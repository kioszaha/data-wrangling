import os
import time
from multiprocessing import Pool
import requests
import pandas as pd
from config import OUTPUT_DIR

API_KEY = os.getenv("KOORDINATES_API_KEY")
LAYER_ID = 123515


def get_area_code(coords):
    lat, lon = coords
    url = "https://koordinates.com/services/query/v1/vector.json"
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
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        features = data["vectorQuery"]["layers"][str(LAYER_ID)]["features"]
        if not features:
            return None
        return features[0]["properties"].get("SA22026_V1_00")
    except Exception as e:
        print(f"Error for ({lat}, {lon}): {e}")
        return None


def main():
    input_path = OUTPUT_DIR / "cleaned_listings.csv"
    output_path = OUTPUT_DIR / "cleaned_listings_with_area_code.csv"

    df = pd.read_csv(input_path)
    coords = list(zip(df["latitude"], df["longitude"]))

    print(f"Querying area codes for {len(coords)} listings...")
    start = time.time()

    with Pool(processes=8) as pool:
        area_codes = pool.map(get_area_code, coords)

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f} seconds")

    df["area_code"] = area_codes

    missing = df["area_code"].isna().sum()
    print(f"Missing area codes: {missing} ({missing / len(df):.2%})")

    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

def month_to_quarter_start(row):
    month = row["published_month"]
    year = row["published_year"]
    if month in [1, 2, 3]:
        return f"{year}-01-01"
    elif month in [4, 5, 6]:
        return f"{year}-04-01"
    elif month in [7, 8, 9]:
        return f"{year}-07-01"
    else:
        return f"{year}-10-01"


def join_datasets():
    listings = pd.read_csv(OUTPUT_DIR / "cleaned_listings_with_area_code.csv")
    bonds = pd.read_csv(OUTPUT_DIR / "cleaned_bonds.csv")

    # Keep only the aggregate rows (all dwelling types, all bed counts combined)
    bonds_all = bonds[
        (bonds["Dwelling Type"] == "ALL") & (bonds["Number Of Beds"] == "ALL")
    ].copy()

    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)

    joined = listings.merge(
        bonds_all,
        left_on=["area_code", "TimeFrame"],
        right_on=["Location Id", "TimeFrame"],
        how="inner",
    )

    print(f"Listings rows: {len(listings)}")
    print(f"Bonds rows (ALL/ALL only): {len(bonds_all)}")
    print(f"Joined rows: {len(joined)}")

    joined.to_csv(OUTPUT_DIR / "joined_listings_bonds.csv", index=False)
    print(f"Saved to {OUTPUT_DIR / 'joined_listings_bonds.csv'}")

    return joined

def median_price_christchurch_central():
    joined = pd.read_csv(OUTPUT_DIR / "joined_listings_bonds.csv")

    cc = joined[joined["area_code"] == 326600]
    median_price = cc["price"].median()

    print(f"Number of listings in Christchurch Central: {len(cc)}")
    print(f"Median Airbnb price in Christchurch Central: ${median_price:.2f}")

    return median_price

def biggest_rental_gap():
    joined = pd.read_csv(OUTPUT_DIR / "joined_listings_bonds.csv")

    # Convert weekly median rent to a daily rate for fair comparison
    joined["long_term_daily_rate"] = joined["Median Rent"] / 7
    joined["price_gap"] = joined["price"] - joined["long_term_daily_rate"]

    # Average gap per area_code
    gap_by_area = (
        joined.groupby("area_code")
        .agg(
            avg_gap=("price_gap", "mean"),
            avg_short_term_price=("price", "mean"),
            avg_long_term_daily_rate=("long_term_daily_rate", "mean"),
            listing_count=("price_gap", "count"),
        )
        .sort_values("avg_gap", ascending=False)
    )

    print("Top 10 areas with the largest gap (short-term - long-term daily rate):")
    print(gap_by_area.head(10))

    return gap_by_area

if __name__ == "__main__":
    main()