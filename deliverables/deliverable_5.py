"""
Deliverable 5: attach SA2 area codes to the Airbnb listings (Koordinates Query API),
join with the bond data, and answer the questions in the brief.

Run order: main()  ->  join_datasets()  ->  the four analysis functions.
"""

import json
import os
import sqlite3
import time
from collections.abc import Mapping
from multiprocessing import Pool
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests
from rich import print
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)

from config import (
    AIRBNB_BONDS_DB_FILE,
    AREA_CODE_CACHE_FILE,
    CLEANED_BONDS_FILE,
    CLEANED_LISTINGS_FILE,
    CLEANED_LISTINGS_WITH_AREA_CODE_FILE,
    COUNTS_BY_AREA_CSV,
    COUNTS_BY_AREA_PNG,
    GAP_BY_AREA_CSV,
    GAP_BY_AREA_PNG,
    JOINED_LISTINGS_BONDS_FILE,
    SA2_DICTIONARY_FILE,
)

API_KEY = os.environ.get("KOORDINATES_API_KEY")
LAYER_ID = 98970
AREA_FIELD = "SA22019_V1_00"
API_URL = "https://koordinates.com/services/query/v1/vector.json"
MIN_LISTINGS = 10  # ignore tiny areas when ranking the price gap
CHRISTCHURCH_CENTRAL_AREA_CODE = 326600
MAX_MISSING_RATIO = 0.05  # abort geocoding if more than this share stays unresolved
MAX_ATTEMPTS = 3  # retries per coordinate, so a rate-limit blip doesn't leave a hole
GEOCODE_WORKERS = 8  # parallel lookups; the API is the bottleneck, not the CPU
NIGHTS_PER_WEEK = 7  # converts the weekly Median Rent to a comparable nightly rate


# ---------------------------------------------------------------- area codes
def get_area_code(coords: tuple[float, float]) -> str | None:
    """Fetch the area code for a latitude/longitude pair from Koordinates."""
    if not API_KEY:
        print(
            "[red]Koordinates API key was not found. Make sure the "
            "KOORDINATES_API_KEY variable is set.[/red]"
        )
        return
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
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            layer = response.json()["vectorQuery"]["layers"][str(LAYER_ID)]
            features = layer["features"] if isinstance(layer, dict) else layer
            if not features:
                return None
            return features[0]["properties"].get(AREA_FIELD)
        except requests.RequestException as e:
            time.sleep(2**attempt)
            print(f"[red]Error for ({lat}, {lon}): {e}[/red]")
    return None


def load_area_code_cache(cache_file: Path) -> pd.DataFrame:
    """Load the coordinate-to-area-code lookup built by previous runs."""
    if not cache_file.exists():
        return pd.DataFrame(columns=["latitude", "longitude", "area_code"])
    cache = pd.read_csv(cache_file)
    if "area_code" not in cache.columns:
        return pd.DataFrame(columns=["latitude", "longitude", "area_code"])
    return (
        cache[["latitude", "longitude", "area_code"]]
        .dropna(subset=["area_code"])
        .drop_duplicates()
    )


def save_area_code_cache(cache_file: Path, lookup: pd.DataFrame) -> None:
    """Persist the full coordinate-to-area-code lookup for future runs.

    The cache only ever grows: it is input-agnostic, so running the pipeline
    with a different (e.g. single-month) listing file never loses the
    coordinates resolved by earlier runs.
    """
    lookup.to_csv(cache_file, index=False)


def fetch_coodinates(input_file: Path, output_file: Path) -> None:
    """Fetch missing coordinates from Koordinates and store them in a cache.

    Raises:
        FileNotFoundError: Input file is not found.
        RuntimeError: Over 5% of coordinates are missing.
    """
    print("[bold green]Mapping Airbnb coordinates to area codes...")
    if not input_file.exists():
        raise FileNotFoundError(
            f"{input_file} does not exist. Did you run the previous deliverables?"
        )

    df = pd.read_csv(input_file)
    cache_file = AREA_CODE_CACHE_FILE
    if not cache_file.exists() and output_file.exists():
        # One-time migration from the old cache layout, where the lookup was
        # only stored inside the enriched listings file.
        save_area_code_cache(cache_file, load_area_code_cache(output_file))
    cached_lookup = load_area_code_cache(cache_file)

    # Find unique coordinates in input
    unique_coords = df[["latitude", "longitude"]].drop_duplicates()

    # Exclude coordinates that are already cached
    if not cached_lookup.empty:
        merged = unique_coords.merge(
            cached_lookup[["latitude", "longitude"]],
            on=["latitude", "longitude"],
            how="left",
            indicator=True,
        )
        coords_to_query = merged[merged["_merge"] == "left_only"][
            ["latitude", "longitude"]
        ]
    else:
        coords_to_query = unique_coords.copy()

    coord_list = list(coords_to_query.itertuples(index=False, name=None))
    start = time.time()

    # Fetch missing coordinates (if any)
    new_codes = []
    if coord_list:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            MofNCompleteColumn(),
            refresh_per_second=1,
        ) as progress:
            task = progress.add_task(
                f"[bold blue]Querying area codes for {len(coord_list)} missing locations[/bold blue]",
                total=len(coord_list),
            )

            with Pool(processes=GEOCODE_WORKERS) as pool:
                for result in pool.imap(get_area_code, coord_list, chunksize=20):
                    new_codes.append(result)
                    progress.update(task, advance=1)
        print(
            f"[green]Fetched {len(new_codes)} new area codes in {time.time() - start:.1f} seconds[/green]"
        )
    else:
        print(
            "[green]All coordinates already mapped in destination file. Skipping pool execution.[/green]"
        )

    # Combine new fetched results with previously cached results
    new_lookup = coords_to_query.copy()
    new_lookup["area_code"] = pd.to_numeric(
        pd.Series(new_codes, index=new_lookup.index), errors="coerce"
    )

    lookup = pd.concat([cached_lookup, new_lookup], ignore_index=True).drop_duplicates(
        subset=["latitude", "longitude"], keep="last"
    )

    # Merge full lookup back into original dataframe
    df = df.merge(lookup, on=["latitude", "longitude"], how="left")

    missing = df["area_code"].isna().sum()
    print(f"[green]Missing area codes: {missing} ({missing / len(df):.2%})")
    if missing / len(df) > MAX_MISSING_RATIO:
        # Don't cache a bad run: an invalid key or rate limiting gives mostly blanks
        raise RuntimeError(
            f"Over {MAX_MISSING_RATIO:.0%} of area codes are missing - check the API key "
            "and rate limits, then rerun. Nothing was saved."
        )

    df["area_code"] = df["area_code"].astype("Int64")
    save_area_code_cache(cache_file, lookup)
    df.to_csv(output_file, index=False)
    print(f"➡️ [blue]Saved enriched Airbnb data to [bold]{output_file}[/bold][/blue]")


# ---------------------------------------------------------------- join
def month_to_quarter_start(row: pd.Series) -> str:
    """Convert an Airbnb publication month into its quarter start date."""
    month = int(row["published_month"])
    year = int(
        row["published_year"]
    )  # int() so a float year never gives "2025.0-01-01"
    if month in [1, 2, 3]:
        return f"{year}-01-01"
    elif month in [4, 5, 6]:
        return f"{year}-04-01"
    elif month in [7, 8, 9]:
        return f"{year}-07-01"
    else:
        return f"{year}-10-01"


def load_location_names(dictionary_file: Path) -> dict[int, str]:
    """Load the SA2 area-code-to-name dictionary."""
    with dictionary_file.open(encoding="utf-8") as file:
        dictionary = json.load(file)
    return {
        int(area_code): str(area_name) for area_code, area_name in dictionary.items()
    }


def add_location_names(
    table: pd.DataFrame, location_names: Mapping[int, str]
) -> pd.DataFrame:
    """Add location names to a copy of an area-indexed result table for display."""
    display_table = table.copy()
    display_table.insert(
        0,
        "location_name",
        [
            location_names.get(int(area_code), "Unknown")
            for area_code in display_table.index
        ],
    )
    return display_table


def load_bonds_all(bonds_file: Path) -> pd.DataFrame:
    """Load bond records for all dwelling types and bedroom counts."""
    bonds = pd.read_csv(bonds_file)
    bonds["TimeFrame"] = pd.to_datetime(bonds["TimeFrame"]).dt.strftime("%Y-%m-%d")
    # One row per area and quarter: all dwelling types, all bed counts,
    # excluding the New Zealand-wide total (-99)
    return bonds[
        (bonds["Dwelling Type"] == "ALL")
        & (bonds["Number Of Beds"] == "ALL")
        & (bonds["Location Id"] != -99)
    ].copy()


def join_datasets(
    listings_file: Path, bonds_file: Path, output_file: Path
) -> pd.DataFrame:
    """Join Airbnb listings and bond data by area code and quarter."""
    print("[bold cyan]Joining the Airbnb and bond datasets...")
    listings = pd.read_csv(listings_file)
    bonds_all = load_bonds_all(bonds_file)

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
    print(f"[cyan]Listings rows: {len(listings)}")
    print(f"[cyan]Bonds rows (ALL/ALL only): {len(bonds_all)}")
    print(
        f"[cyan]Joined rows: {len(joined)}  ({unmatched} listings had no matching bond row)"
    )

    joined.to_csv(output_file, index=False)
    print(f"➡️ [blue]Saved joined data to [bold]{output_file}[/bold][/blue]")
    return joined


# ---------------------------------------------------------------- questions
def median_price_christchurch_central(
    listings_file: Path, location_names: Mapping[int, str]
) -> float:
    """Calculate the median Airbnb price in Christchurch Central."""
    print("[bold magenta]Calculating the Christchurch Central median Airbnb price...")
    # Use all listings in the area, not just those that matched a bond row
    listings = pd.read_csv(listings_file)
    cc = listings[listings["area_code"] == CHRISTCHURCH_CENTRAL_AREA_CODE]
    median_price = cc["price"].median()

    location_name = location_names.get(
        CHRISTCHURCH_CENTRAL_AREA_CODE, "Christchurch Central"
    )
    print(f"[magenta]Number of listing rows in {location_name}: {len(cc)}")
    print(f"[magenta]Median Airbnb price in {location_name}: ${median_price:.2f}")
    return median_price


def biggest_rental_gap(
    joined_file: Path, location_names: Mapping[int, str]
) -> pd.DataFrame:
    """Calculate and save short-term versus long-term rental price gaps."""
    print("[bold red]Calculating short-term versus long-term rental price gaps...")
    output_file = GAP_BY_AREA_CSV
    plot_file = GAP_BY_AREA_PNG
    joined = pd.read_csv(joined_file)

    # Convert weekly median rent to a nightly rate for a fair comparison
    joined["long_term_daily_rate"] = joined["Median Rent"] / NIGHTS_PER_WEEK
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

    print(
        f"[red]Top 10 areas with the largest gap (areas with >= {MIN_LISTINGS} listings):"
    )
    print(add_location_names(gap_by_area.head(10).round(1), location_names))
    gap_by_area.to_csv(output_file)

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
    fig.savefig(plot_file, dpi=150)
    plt.close(fig)

    return gap_by_area


def compare_property_counts(
    listings_file: Path,
    bonds_file: Path,
    location_names: Mapping[int, str],
) -> pd.DataFrame:
    """Compare average Airbnb and active long-term rental counts by area."""
    output_file = COUNTS_BY_AREA_CSV
    plot_file = COUNTS_BY_AREA_PNG
    listings = pd.read_csv(listings_file)
    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)
    bonds_all = load_bonds_all(bonds_file)

    # Both sides as an average count per quarter. Active Bonds is the stock of
    # tenancies in force; Total Bonds is only NEW bonds lodged in the quarter
    # (a flow), so summing it would measure turnover, not how many properties.
    airbnb_counts = (
        listings.groupby(["area_code", "TimeFrame"])["id"]
        .nunique()
        .groupby("area_code")
        .mean()
        .rename("airbnb_listings")
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

    print("[bold yellow]Comparing Airbnb and long-term rental property counts...")
    print("[yellow]Top 10 areas by number of Airbnb listings (average per quarter):")
    print(add_location_names(comparison.head(10), location_names))
    comparison.to_csv(output_file)

    top15 = comparison.head(15)
    fig, ax = plt.subplots(figsize=(8, 5))
    pos = range(len(top15))
    ax.barh(
        [i + 0.2 for i in pos],
        top15["airbnb_listings"],
        height=0.4,
        label="Airbnb listings",
    )
    ax.barh(
        [i - 0.2 for i in pos],
        top15["active_rentals"],
        height=0.4,
        label="Active long-term rentals",
    )
    ax.set_yticks(list(pos))
    ax.set_yticklabels(top15.index.astype(str))
    ax.invert_yaxis()
    ax.set_xlabel("Average count per quarter")
    ax.set_title("Airbnb vs long-term rentals by area")
    ax.legend()
    plt.tight_layout()
    fig.savefig(plot_file, dpi=150)
    plt.close(fig)
    return comparison


def compare_bed_counts(
    listings_file: Path,
    bonds_file: Path,
    location_names: Mapping[int, str],
) -> pd.DataFrame:
    """Compare Airbnb units with estimated long-term rental beds by area."""
    print("[bold yellow]Comparing Airbnb units and long-term rental beds...")
    listings = pd.read_csv(listings_file)
    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)
    bonds = pd.read_csv(bonds_file)

    # The Airbnb data has no bedroom count, so each listing is one unit and the
    # comparison below is Airbnb units vs long-term rental BEDS - not like for like.
    airbnb_units = (
        listings.groupby(["area_code", "TimeFrame"])["id"]
        .nunique()
        .groupby("area_code")
        .mean()
        .rename("airbnb_units")
    )

    # Only Dwelling Type == ALL, otherwise every rental is counted once per
    # dwelling type as well as once in the ALL row. Bed counts ALL/5+/missing
    # have no numeric value and are excluded.
    bonds_valid = (
        bonds[(bonds["Dwelling Type"] == "ALL") & (bonds["Location Id"] != -99)]
        .dropna(subset=["beds_num"])
        .copy()
    )
    bonds_valid["beds_in_rentals"] = (
        bonds_valid["beds_num"] * bonds_valid["Active Bonds"]
    )

    beds_per_quarter = bonds_valid.groupby(["Location Id", "TimeFrame"])[
        "beds_in_rentals"
    ].sum()
    long_term_beds = (
        beds_per_quarter.groupby("Location Id").mean().rename("long_term_beds")
    )
    long_term_beds.index.name = "area_code"

    comparison = pd.concat([airbnb_units, long_term_beds], axis=1).dropna().round(1)
    comparison = comparison.sort_values("airbnb_units", ascending=False)

    print(
        "[yellow]Top 10 areas: Airbnb units vs long-term rental beds (average per quarter):"
    )
    print(add_location_names(comparison.head(10), location_names))
    return comparison


# ---------------------------------------------------------------- SQLite
def sqlite_join(
    listings_file: Path,
    bonds_file: Path,
    location_names: Mapping[int, str],
) -> pd.DataFrame:
    """Store both datasets in SQLite and return their SQL join."""
    print("[bold blue]Running the SQLite join...")
    database_file = AIRBNB_BONDS_DB_FILE
    listings = pd.read_csv(listings_file)
    listings["TimeFrame"] = listings.apply(month_to_quarter_start, axis=1)
    bonds_all = load_bonds_all(bonds_file)

    con = sqlite3.connect(database_file)
    listings.to_sql("listings", con, if_exists="replace", index=False)
    bonds_all.to_sql("bonds", con, if_exists="replace", index=False)

    joined = pd.read_sql_query(
        """
        SELECT l.*, b."Median Rent", b."Total Bonds", b."Active Bonds"
        FROM listings AS l
        INNER JOIN bonds AS b
            ON l.area_code = b."Location Id" AND l.TimeFrame = b.TimeFrame
    """,
        con,
    )
    print(f"[blue]SQL join returned {len(joined)} rows")

    # SQLite has no MEDIAN(), so take the middle row(s) of the sorted prices
    median = pd.read_sql_query(
        f"""
        SELECT AVG(price) AS median_price FROM (
            SELECT price FROM listings WHERE area_code = {CHRISTCHURCH_CENTRAL_AREA_CODE}
            ORDER BY price
            LIMIT 2 - (SELECT COUNT(*) FROM listings WHERE area_code = {CHRISTCHURCH_CENTRAL_AREA_CODE}) % 2
            OFFSET (SELECT (COUNT(*) - 1) / 2 FROM listings WHERE area_code = {CHRISTCHURCH_CENTRAL_AREA_CODE})
        )
    """,
        con,
    )
    location_name = location_names.get(
        CHRISTCHURCH_CENTRAL_AREA_CODE, "Christchurch Central"
    )
    print(f"[blue]Median price in {location_name} (SQL):", median.iloc[0, 0])
    con.close()
    return joined


def main() -> None:
    """Run the complete deliverable-5 data preparation and analysis pipeline."""

    cleaned_listings_with_area_code_file = CLEANED_LISTINGS_WITH_AREA_CODE_FILE
    cleaned_bonds_file = CLEANED_BONDS_FILE
    joined_listings_bonds_file = JOINED_LISTINGS_BONDS_FILE
    location_names = load_location_names(SA2_DICTIONARY_FILE)

    fetch_coodinates(
        CLEANED_LISTINGS_FILE,
        cleaned_listings_with_area_code_file,
    )
    join_datasets(
        cleaned_listings_with_area_code_file,
        cleaned_bonds_file,
        joined_listings_bonds_file,
    )
    median_price_christchurch_central(
        cleaned_listings_with_area_code_file,
        location_names,
    )
    biggest_rental_gap(joined_listings_bonds_file, location_names)
    compare_property_counts(
        cleaned_listings_with_area_code_file,
        cleaned_bonds_file,
        location_names,
    )
    compare_bed_counts(
        cleaned_listings_with_area_code_file,
        cleaned_bonds_file,
        location_names,
    )
    sqlite_join(
        cleaned_listings_with_area_code_file,
        cleaned_bonds_file,
        location_names,
    )
