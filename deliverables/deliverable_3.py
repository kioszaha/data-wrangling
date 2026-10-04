"""
Combine the nine monthly Airbnb snapshots into one dataset (Deliverable 3)

Reads the raw listings_YYYYMMDD.csv files from .data/ and writes combined_listings.csv
plus a per-column summary.md to .output/. The four plots from last week's R Markdown
workflow are reproduced at the end via rpy2, which is the one step here with an external
runtime dependency. See docs/design_principles.md for what this stage does.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Any

import pandas as pd
from rich import print

from config import (
    COMBINED_LISTINGS_FILE,
    OUTPUT_DIR,
    PREVIOUS_WEEKS_PLOTS_PDF,
    SUMMARY_FILE,
)
from utils.file_explorer import AirbnbListings, file_explorer


def combine_datasets(airbnb_listings: AirbnbListings) -> pd.DataFrame:
    """Returns a concated dataframe consisting of all the listings

    Args:
        airbnb_listings (AirbnbListings): The Airbnb listings as loaded by the file explorer

    Returns:
        pd.DataFrame: The final combined dataframe
    """

    return pd.concat(
        [airbnb_listing.dataframe for airbnb_listing in airbnb_listings.listings],
        ignore_index=True,
    )


def summarise_column(series: pd.Series) -> dict[str, Any]:
    """Produce summary statistics for a single column.

    Numeric columns report min, max, mean, and standard deviation. Non-numeric
    columns report each category and its count. Every column reports its
    number of missing values.

    Args:
        series (pd.Series): The column to summarise

    Returns:
        dict: The column's summary statistics
    """
    summary: dict[str, Any] = {"missing": int(series.isna().sum())}

    if pd.api.types.is_datetime64_any_dtype(series):
        summary.update(
            {
                "min": series.min(),
                "max": series.max(),
                "mean": series.mean(),
            }
        )
    elif pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(
        series
    ):
        summary.update(
            {
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
                "mean": round(float(series.mean()), 2),
                "std": round(float(series.std()), 2),
            }
        )
    else:
        val_counts = series.value_counts()
        summary["unique_categories"] = len(val_counts)
        top_cats = ", ".join([f"{k} ({v})" for k, v in val_counts.head(3).items()])
        summary["top_categories"] = top_cats or "None"
    return summary


def summarise_dataset(df: pd.DataFrame, exclude: list) -> pd.DataFrame:
    """Produce summary statistics for every column in a dataframe

    Args:
        df (pd.DataFrame): The dataframe to summarise

    Returns:
        pd.DataFrame: A dataframe of summary statistics
    """
    if not exclude:
        exclude = []

    summaries = {
        col: summarise_column(df[col]) for col in df.columns if col not in exclude
    }

    summary_df = pd.DataFrame(summaries).T

    return summary_df

def previous_weeks_plots(Input):

    df = pd.read_csv(Input)
    chch = df[df["neighbourhood_group"] == "Christchurch City"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    chch["price"].plot(
    kind="hist", 
    bins=range(0, 2010, 10),
    title="House Prices in Christchurch City",
    xlabel="Price",
    ylabel="Number of Houses")

    chch_plot = OUTPUT_DIR / "chch_price_plot.png"
    plt.savefig(chch_plot, dpi=300, bbox_inches="tight")
    plt.close()

    df["price"].plot(
        kind="hist", 
        bins=range(0, 2010, 10),
        title="House Prices in New Zealand",
        xlabel="Price",
        ylabel="Number of Houses")

    nz_plot = OUTPUT_DIR / "nz_price_plot.png"
    plt.savefig(nz_plot, dpi=300, bbox_inches="tight")
    plt.close()

    df["last_review"] = pd.to_datetime(df["last_review"], format="%Y-%m-%d", errors="coerce")
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")

    df["days_since_review"] = (df["published_date"] - df["last_review"]).dt.days

    df["days_since_review"].plot(
        kind="hist",
        bins=range(0, 1025, 25),
        title="Difference Between Last Review and Publish Date in Days",
        xlim=(0, 1000),
        xlabel="Days",
        ylabel="Count")

    review_plot = OUTPUT_DIR / "days_since_review_plot.png"
    plt.savefig(review_plot, dpi=300, bbox_inches="tight")
    plt.close()

    threshold = df['number_of_reviews'].quantile(0.9)

    top_10 = df[df['number_of_reviews'] >= threshold]

    chch_top_10_count = len(top_10[top_10['neighbourhood_group'] == "Christchurch City"])
    print("Top 10 Percent of Properties in Christchurch by Number of Reviews: ", chch_top_10_count)



def main() -> None:
    # Obtain the AirbnbListings object
    airbnb_listings = file_explorer("airbnb")

    # Task 2: Load one dataset into Python or R
    june_listings = airbnb_listings.by_month(6)

    # Task 3: Filter by Christchurch only
    june_listings.filter_christchurch()

    # Task 4: Add a column for the month + year
    june_listings.prepare()

    # Task 5: Do the same for all the other datasets, and concatenate them
    airbnb_listings.filter_christchurch_all()
    airbnb_listings.prepare_all()
    combined_dataset = combine_datasets(airbnb_listings)

    # Task 6: Summary statistics + missing values per column
    summary_df = summarise_dataset(
        combined_dataset,
        exclude=[
            "id",
            "host_id",
            "license",
            "published_month",
            "published_year",
            "longitude",
            "latitude",
        ],
    )
    summary_df.to_markdown(SUMMARY_FILE)
    print(f"➡️ [blue] Saved summary to [bold]{SUMMARY_FILE}[/bold][/blue]")

    # Task 7: Store the concatenated dataset in a new file
    combined_dataset_output_path = OUTPUT_DIR / "combined_listings.csv"
    combined_dataset.to_csv(combined_dataset_output_path, index=False)
    print(
        f"➡️ [blue] Saved combined dataset to [bold]{combined_dataset_output_path}[/bold][/blue]"
    )

    # Task 8: Reproduce workflow and plots from last weeks no code software

    previous_weeks_plots_R(COMBINED_LISTINGS_FILE.name, PREVIOUS_WEEKS_PLOTS_PDF.name)
