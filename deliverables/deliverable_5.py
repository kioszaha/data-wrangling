"""
Deliverable 5: attach SA2 area codes to the Airbnb listings (Koordinates Query API),
join with the bond data, and answer the questions in the brief.

Run order: main()  ->  join_datasets()  ->  the four analysis functions.
"""

import os
import sqlite3
import time
from multiprocessing import Pool

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv

from config import OUTPUT_DIR

load_dotenv()  # so the key is found even when this file is run on its own
API_KEY = os.getenv("KOORDINATES_API_KEY")
LAYER_ID = 123515
AREA_FIELD = "SA22026_V1_00"
URL = "https://koordinates.com/services/query/v1/vector.json"
MIN_LISTINGS = 10  # ignore tiny areas when ranking the price gap


# ---------------------------------------------------------------- area codes
def get_area_code(coords):
    lat, lon = coords
    params = {
        "key": API_KEY,
        "layer": LAYER_ID,
        "x": lon,
        "y": lat,
        "max_results": 1,
        "radius": 100,
        "geometry": "false",
        "with_field_names": "true",
    }
    for attempt in range(3):  # retry so a rate-limit blip doesn't leave a hole
        try:
            response = requests.get(URL, params=params, timeout=10)
            response.raise_for_status()
            layer = response.json()["vectorQuery"]["layers"][str(LAYER_ID)]
            features = layer["features"] if isinstance(layer, dict) else layer
            if not features:
                return None
            return features[0]["properties"].get(AREA_FIELD)
        except Exception as e:
            last_error = e
            time.sleep(2**attempt)
    print(f"Error for ({lat}, {lon}): {last_error}")
    return None


def main():
    input_path = OUTPUT_DIR / "cleaned_listings.csv"
    output_path = OUTPUT_DIR / "cleaned_listings_with_area_code.csv"

    if output_path.exists():
        print(f"{output_path} already exists, skipping geocoding.")
        return

    df = pd.read_csv(input_path)

    # Listings repeat across monthly snapshots, so query each distinct point once
    unique_coords = df[["latitude", "longitude"]].drop_duplicates()
    coord_list = list(unique_coords.itertuples(index=False, name=None))
    print(f"Querying area codes for {len(coord_list)} distinct locations "
          f"({len(df)} listing rows)...")
    start = time.time()

    with Pool(processes=8) as pool:
        codes = pool.map(get_area_code, coord_list, chunksize=20)

    print(f"Done in {time.time() - start:.1f} seconds")

    lookup = unique_coords.copy()
    lookup["area_code"] = pd.to_numeric(pd.Series(codes, index=lookup.index), errors="coerce")
    df = df.merge(lookup, on=["latitude", "longitude"], how="left")

    missing = df["area_code"].isna().sum()
    print(f"Missing area codes: {missing} ({missing / len(df):.2%})")
    if missing / len(df) > 0.05:
        # Don't cache a bad run: an invalid key or rate limiting gives mostly blanks
        raise RuntimeError("Over 5% of area codes are missing - check the API key "
                           "and rate limits, then rerun. Nothing was saved.")

    df["area_code"] = df["area_code"].astype("Int64")
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")


# ---------------------------------------------------------------- join
def month_to_quarter_start(row):
    month = int(row["published_month"])
    year = int(row["published_year"])  # int() so a float year never gives "2025.0-01-01"
    if month in [1, 2, 3]:
        return f"{year}-01-01"
    elif month in [4, 5, 6]:
        return f"{year}-04-01"
    elif month in [7, 8, 9]:
        return f"{year}-07-01"
    else:
        return f"{year}-10-01"


def load_bonds_all():
    bonds = pd.read_csv(OUTPUT_DIR / "cleaned_bonds.csv")
    bonds["TimeFrame"] = pd.to_datetime(bonds["TimeFrame"]).dt.strftime("%Y-%m-%d")
    # One row per area and quarter: all dwelling types, all bed counts,
    # excluding the New Zealand-wide total (-99)
    return bonds[
        (bonds["Dwelling Type"] == "ALL")
        & (bonds["Number Of Beds"] == "ALL")
        & (bonds["Location Id"] != -99)
    ].copy()


def join_datasets():
    listings = pd.read_csv(OUTPUT_DIR / "cleaned_listings_with_area_code.csv")
    bonds_all = load_bonds_all()

    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)

    # Inner join: we only want listings that have a matching area and quarter
    # of bond data, since the price comparison needs both sides.
    joined = listings.merge(
        bonds_all,
        left_on=["area_code", "TimeFrame"],
        right_on=["Location Id", "TimeFrame"],
        how="inner",
    )

    unmatched = len(listings) - len(joined)
    print(f"Listings rows: {len(listings)}")
    print(f"Bonds rows (ALL/ALL only): {len(bonds_all)}")
    print(f"Joined rows: {len(joined)}  ({unmatched} listings had no matching bond row)")

    joined.to_csv(OUTPUT_DIR / "joined_listings_bonds.csv", index=False)
    print(f"Saved to {OUTPUT_DIR / 'joined_listings_bonds.csv'}")
    return joined


# ---------------------------------------------------------------- questions
def median_price_christchurch_central():
    # Use all listings in the area, not just those that matched a bond row
    listings = pd.read_csv(OUTPUT_DIR / "cleaned_listings_with_area_code.csv")
    cc = listings[listings["area_code"] == 326600]
    median_price = cc["price"].median()

    print(f"Number of listing rows in Christchurch Central: {len(cc)}")
    print(f"Median Airbnb price in Christchurch Central: ${median_price:.2f}")
    return median_price


def biggest_rental_gap():
    joined = pd.read_csv(OUTPUT_DIR / "joined_listings_bonds.csv")

    # Convert weekly median rent to a nightly rate for a fair comparison
    joined["long_term_daily_rate"] = joined["Median Rent"] / 7
    joined["price_gap"] = joined["price"] - joined["long_term_daily_rate"]

    gap_by_area = (
        joined.groupby("area_code")
        .agg(
            median_gap=("price_gap", "median"),
            avg_gap=("price_gap", "mean"),
            median_short_term_price=("price", "median"),
            median_long_term_daily_rate=("long_term_daily_rate", "median"),
            listing_count=("price_gap", "count"),
        )
        .query("listing_count >= @MIN_LISTINGS")
        .sort_values("median_gap", ascending=False)
    )

    print(f"Top 10 areas with the largest gap (areas with >= {MIN_LISTINGS} listings):")
    print(gap_by_area.head(10).round(1))
    gap_by_area.to_csv(OUTPUT_DIR / "gap_by_area.csv")

    # Distribution of the gap in the top 10 areas (extreme values trimmed for display)
    top = gap_by_area.head(10).index
    plot_df = joined[joined["area_code"].isin(top)]
    lo, hi = plot_df["price_gap"].quantile([0.01, 0.99])
    plot_df = plot_df[plot_df["price_gap"].between(lo, hi)]
    labels = [str(a) for a in top]
    data = [plot_df.loc[plot_df["area_code"] == a, "price_gap"] for a in top]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot(data, tick_labels=labels, showfliers=False)
    ax.set_xlabel("SA2 area code")
    ax.set_ylabel("Airbnb price minus rent, $ per night")
    ax.set_title("Short- vs long-term price gap (top 10 areas by median gap)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "gap_by_area.png", dpi=150)
    plt.close(fig)

    return gap_by_area


def compare_property_counts():
    listings = pd.read_csv(OUTPUT_DIR / "cleaned_listings_with_area_code.csv")
    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)
    bonds_all = load_bonds_all()

    # Both sides as an average count per quarter. Active Bonds is the stock of
    # tenancies in force; Total Bonds is only NEW bonds lodged in the quarter
    # (a flow), so summing it would measure turnover, not how many properties.
    airbnb_counts = (
        listings.groupby(["area_code", "TimeFrame"])["id"].nunique()
        .groupby("area_code").mean().rename("airbnb_listings")
    )
    rental_counts = (
        bonds_all.groupby("Location Id")["Active Bonds"].mean().rename("active_rentals")
    )
    rental_counts.index.name = "area_code"

    comparison = pd.concat([airbnb_counts, rental_counts], axis=1).dropna().round(1)
    comparison["airbnb_per_100_rentals"] = (
        comparison["airbnb_listings"] / comparison["active_rentals"] * 100
    ).round(1)
    comparison = comparison.sort_values("airbnb_listings", ascending=False)

    print("Top 10 areas by number of Airbnb listings (average per quarter):")
    print(comparison.head(10))
    comparison.to_csv(OUTPUT_DIR / "counts_by_area.csv")

    top15 = comparison.head(15)
    fig, ax = plt.subplots(figsize=(8, 5))
    pos = range(len(top15))
    ax.barh([i + 0.2 for i in pos], top15["airbnb_listings"], height=0.4, label="Airbnb listings")
    ax.barh([i - 0.2 for i in pos], top15["active_rentals"], height=0.4, label="Active long-term rentals")
    ax.set_yticks(list(pos))
    ax.set_yticklabels(top15.index.astype(str))
    ax.invert_yaxis()
    ax.set_xlabel("Average count per quarter")
    ax.set_title("Airbnb vs long-term rentals by area")
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "counts_by_area.png", dpi=150)
    plt.close(fig)
    return comparison


def compare_bed_counts():
    listings = pd.read_csv(OUTPUT_DIR / "cleaned_listings_with_area_code.csv")
    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)
    bonds = pd.read_csv(OUTPUT_DIR / "cleaned_bonds.csv")

    # The Airbnb data has no bedroom count, so each listing is one unit and the
    # comparison below is Airbnb units vs long-term rental BEDS - not like for like.
    airbnb_units = (
        listings.groupby(["area_code", "TimeFrame"])["id"].nunique()
        .groupby("area_code").mean().rename("airbnb_units")
    )

    # Only Dwelling Type == ALL, otherwise every rental is counted once per
    # dwelling type as well as once in the ALL row. Bed counts ALL/5+/missing
    # have no numeric value and are excluded.
    bonds_valid = bonds[
        (bonds["Dwelling Type"] == "ALL") & (bonds["Location Id"] != -99)
    ].dropna(subset=["beds_num"]).copy()
    bonds_valid["beds_in_rentals"] = bonds_valid["beds_num"] * bonds_valid["Active Bonds"]

    beds_per_quarter = bonds_valid.groupby(["Location Id", "TimeFrame"])["beds_in_rentals"].sum()
    long_term_beds = beds_per_quarter.groupby("Location Id").mean().rename("long_term_beds")
    long_term_beds.index.name = "area_code"

    comparison = pd.concat([airbnb_units, long_term_beds], axis=1).dropna().round(1)
    comparison = comparison.sort_values("airbnb_units", ascending=False)

    print("Top 10 areas: Airbnb units vs long-term rental beds (average per quarter):")
    print(comparison.head(10))
    return comparison


# ---------------------------------------------------------------- SQLite 
def sqlite_join():
    listings = pd.read_csv(OUTPUT_DIR / "cleaned_listings_with_area_code.csv")
    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)
    bonds_all = load_bonds_all()

    con = sqlite3.connect(OUTPUT_DIR / "airbnb_bonds.db")
    listings.to_sql("listings", con, if_exists="replace", index=False)
    bonds_all.to_sql("bonds", con, if_exists="replace", index=False)

    joined = pd.read_sql_query("""
        SELECT l.*, b."Median Rent", b."Total Bonds", b."Active Bonds"
        FROM listings AS l
        INNER JOIN bonds AS b
            ON l.area_code = b."Location Id" AND l.TimeFrame = b.TimeFrame
    """, con)
    print(f"SQL join returned {len(joined)} rows")

    # SQLite has no MEDIAN(), so take the middle row(s) of the sorted prices
    median = pd.read_sql_query("""
        SELECT AVG(price) AS median_price FROM (
            SELECT price FROM listings WHERE area_code = 326600
            ORDER BY price
            LIMIT 2 - (SELECT COUNT(*) FROM listings WHERE area_code = 326600) % 2
            OFFSET (SELECT (COUNT(*) - 1) / 2 FROM listings WHERE area_code = 326600)
        )
    """, con)
    print("Median price in Christchurch Central (SQL):", median.iloc[0, 0])
    con.close()
    return joined



if __name__ == "__main__":
    main()
    join_datasets()
    median_price_christchurch_central()
    biggest_rental_gap()
    compare_property_counts()
    compare_bed_counts()
    sqlite_join()