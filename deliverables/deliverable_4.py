"""
Clean the Christchurch Airbnb listings dataset (Deliverable 4)

Using the combined_listening.csv file from Deliverable 3

"""

import numpy as np
import pandas as pd
from rich import print

from config import DATA_DIR, OUTPUT_DIR


def clean_airbnb_data() -> pd.DataFrame:
    # Make sure the result from deliverable 3 exists
    INPUT_FILE = OUTPUT_DIR / "combined_listings.csv"
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} does not exist. Did you run deliverable_3()?"
        )

    print("[bold purple]Filtering the bonds dataset...")

    df = pd.read_csv(INPUT_FILE)
    initial_rows = len(df)
    print(f"[purple]Initial Airbnb row count: {initial_rows}")

    # Dropped columns neighbourhood_group & license & host_name
    # Dropping these since license and neighbourhood_group are mostly empty/uninformative,
    # and host_name isn't needed for quantitative analysis
    cols_to_drop = [
        col
        for col in ["neighbourhood_group", "license", "host_name"]
        if col in df.columns
    ]
    df = df.drop(columns=cols_to_drop)

    # Make sure latitude and longitude exist for spatial mapping, drop if missing
    geo_nulls = df[["latitude", "longitude"]].isna().any(axis=1).sum()
    df = df.dropna(subset=["latitude", "longitude"]).copy()
    print(
        f"[purple]Missing latitude/longitude dropped {geo_nulls} rows ({(geo_nulls / (geo_nulls + len(df))) * 100:.2f}%)"
    )

    # Drop any rows missing minimum_nights or invalid price values (e.g., <= 0)
    min_nights_nulls = df["minimum_nights"].isna().sum()
    df = df.dropna(subset=["minimum_nights"]).copy()
    print(
        f"[purple]Missing minimum_nights dropped {min_nights_nulls} rows ({(min_nights_nulls / (min_nights_nulls + len(df))) * 100:.2f}%)"
    )

    invalid_prices = (df["price"].isna()) | (df["price"] <= 0)
    invalid_price_count = invalid_prices.sum()
    df = df[~invalid_prices].copy()
    print(
        f"[purple]Missing or invalid price dropped {invalid_price_count} rows ({(invalid_price_count / (invalid_price_count + len(df))) * 100:.2f}%)"
    )

    # Filled in missing values for reviews_per_month (missing means 0 reviews)
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)

    # Convert last_review to datetime format if present
    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(df["last_review"])

    print(
        f"[purple]Final clean Airbnb dataset has {len(df)} rows (retained {(len(df) / initial_rows) * 100:.2f}% of original data)"
    )

    return df


def load_bonds_data() -> pd.DataFrame:

    # Make sure the input data for this deliverable exists
    BONDS_DATA = DATA_DIR / "bonds" / "Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
    if not BONDS_DATA.exists():
        raise FileNotFoundError(
            f"{BONDS_DATA} does not exist. Did you run sync_data()?"
        )

    return pd.read_csv(BONDS_DATA, parse_dates=["TimeFrame"])


def clean_bonds_data(bonds_df: pd.DataFrame) -> pd.DataFrame:
    print("[bold yellow]Filtering the bonds dataset...[/bold yellow]")
    initial_rows = len(bonds_df)

    # Filter the bonds data to be the same timeframe as the airbnb data,
    # Which is 5th October 2025 - 19th June 2026

    start = pd.Timestamp("2025-10-05")
    end = pd.Timestamp("2026-06-19")
    bonds_cleaned = bonds_df[bonds_df["TimeFrame"].between(start, end)].copy()

    # Log how many rows got chopped by date filtering
    rows_lost_timeframe = initial_rows - len(bonds_cleaned)
    print(
        f"[yellow]TimeFrame filter dropped {rows_lost_timeframe} rows ({(rows_lost_timeframe / initial_rows) * 100:.2f}%)"
    )

    # Location Id is a key field, so we need to drop any rows missing it
    location_nulls = bonds_cleaned["Location Id"].isna().sum()
    bonds_cleaned = bonds_cleaned.dropna(subset=["Location Id"]).copy()
    bonds_cleaned["Location Id"] = bonds_cleaned["Location Id"].astype("Int64")
    print(
        f"[yellow]Missing Location Id dropped {location_nulls} rows ({(location_nulls / len(bonds_cleaned)) * 100:.2f}%)"
    )

    # Clean the data
    print(
        f"[yellow]{(len(bonds_cleaned[bonds_cleaned['Number Of Beds'] == '5+']) / len(bonds_cleaned)) * 100:.2f}% of the data has '5+' as Number of Beds"
    )
    print(
        f"[yellow]{(len(bonds_cleaned[bonds_cleaned['Number Of Beds'] == 'ALL']) / len(bonds_cleaned)) * 100:.2f}% of the data has 'ALL' as Number of Beds"
    )
    # Approx 1% of the data has a string '5+' as the Number Of Beds
    # We are going to preserve the 5+ for any potential categorical analysis, but drop it for a numerical column

    # Drop the summary aggregate rows since 'ALL' isn't an actual bed count
    bed_order = ["0", "1", "2", "3", "4", "5", "5+", "6", "7", "8", "9", "15", "ALL"]
    bonds_cleaned["beds_cat"] = pd.Categorical(
        bonds_cleaned["Number Of Beds"], categories=bed_order, ordered=True
    )

    bonds_cleaned["beds_num"] = (
        bonds_cleaned["Number Of Beds"]
        .replace("5+", np.nan)
        .replace("ALL", np.nan)
        .astype(float)
        .astype("Int64")
    )

    # Drop any rows missing core rent stats (Median Rent)
    rent_nulls = bonds_cleaned["Median Rent"].isna().sum()
    bonds_cleaned = bonds_cleaned.dropna(subset=["Median Rent"]).copy()
    print(
        f"[yellow]Missing Median Rent dropped {rent_nulls} rows ({(rent_nulls / len(bonds_cleaned) + rent_nulls) * 100:.2f}%)"
    )

    print(
        f"[yellow]Final clean dataset has {len(bonds_cleaned)} rows (retained {(len(bonds_cleaned) / initial_rows) * 100:.2f}% of original data)"
    )

    return bonds_cleaned


def main():

    CLEANED_AIRBNB_OUTPUT_PATH = OUTPUT_DIR / "cleaned_listings.csv"
    cleaned_airbnb_df = clean_airbnb_data()
    cleaned_airbnb_df.to_csv(CLEANED_AIRBNB_OUTPUT_PATH, index=False)
    print(
        f"➡️ [blue] Saved cleaned Airbnb data to [bold]{CLEANED_AIRBNB_OUTPUT_PATH}[/bold][/blue]"
    )

    CLEANED_BONDS_OUTPUT_PATH = OUTPUT_DIR / "cleaned_bonds.csv"
    bonds_df = load_bonds_data()
    cleaned_bonds_df = clean_bonds_data(bonds_df)
    cleaned_bonds_df.to_csv(CLEANED_BONDS_OUTPUT_PATH, index=False)

    print(
        f"➡️ [blue] Saved cleaned bonds data to [bold]{CLEANED_BONDS_OUTPUT_PATH}[/bold][/blue]"
    )
