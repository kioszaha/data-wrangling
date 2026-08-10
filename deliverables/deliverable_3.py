import pandas as pd
from rich import print

from config import OUTPUT_DIR
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


def summarise_column(series: pd.Series) -> dict:
    """Produce summary statistics for a single column.

    Numeric columns report min, max, mean, and standard deviation. Non-numeric
    columns report each category and its count. Every column reports its
    number of missing values.

    Args:
        series (pd.Series): The column to summarise

    Returns:
        dict: The column's summary statistics
    """
    summary = {"missing": series.isna().sum()}

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
                "min": round(series.min(), 2),
                "max": round(series.max(), 2),
                "mean": round(series.mean(), 2),
                "std": round(series.std(), 2),
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


def main():
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
    summary_output_path = OUTPUT_DIR / "summary.md"
    summary_df.to_markdown(summary_output_path)
    print(f"➡️ [blue] Saved summary to [bold]{summary_output_path}[/bold][/blue]")

    # Task 7: Store the concatenated dataset in a new file
    combined_dataset_output_path = OUTPUT_DIR / "combined_listings.csv"
    combined_dataset.to_csv(combined_dataset_output_path, index=False)
    print(
        f"➡️ [blue] Saved combined dataset to [bold]{combined_dataset_output_path}[/bold][/blue]"
    )
