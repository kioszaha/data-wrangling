"""
Clean the Christchurch Airbnb listings dataset (Deliverable 4)

Using the combined_listening.csv file from Deliverable 3

"""

import pandas as pd

from config import DATA_DIR, OUTPUT_DIR

OUTPUT_PATH = OUTPUT_DIR / "cleaned_listings.csv"


def clean_airbnb_data():
    INPUT_FILE = OUTPUT_DIR / "combined_listings.csv"
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} does not exist. Did you run deliverable_3()?"
        )

    df = pd.read_csv(INPUT_FILE)

    # Dropped columns neightbourhood_group & license & host_name
    df = df.drop(columns=["neighbourhood_group", "license", "host_name"])
    df = df.dropna(subset=["minimum_nights"])

    # Filled in missing values for reviews_per_month and host_name
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)

    df.to_csv(OUTPUT_PATH, index=False)
    return df


def clean_bonds_data():
    BONDS_DATA = DATA_DIR / "Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
    if not BONDS_DATA.exists():
        raise FileNotFoundError(
            f"{BONDS_DATA} does not exist. Did you run sync_data()?"
        )

    bonds_df = pd.read_csv(BONDS_DATA)

    pass


def main():
    clean_airbnb_data()
