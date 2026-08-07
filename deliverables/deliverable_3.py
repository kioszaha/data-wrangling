import pandas as pd

from utils.file_explorer import AirbnbListings, file_explorer

from config import DATA_DIR

def combine_datasets(airbnb_listings: AirbnbListings) -> pd.DataFrame:
    """Returns a concated dataframe consisting of all the listings

    Args:
        airbnb_listings (AirbnbListings): The Airbnb listings as loaded by the file explorer

    Returns:
        pd.DataFrame: The final combined dataframe
    """

    return pd.concat(
        [airbnb_listing.dataframe for airbnb_listing in airbnb_listings.listings]
    )

def summarize_column(series: pd.Series) -> dict:
    """Produce summary statistics for a single column.

    Numeric columns report min, max, mean, and standard deviation. Non-numeric
    columns report each category and its count. Every column reports its
    number of missing values.

    Args:
        series (pd.Series): The column to summarize

    Returns:
        dict: The column's summary statistics
    """
    summary = {"missing": series.isna().sum()}

    if pd.api.types.is_numeric_dtype(series):
        summary.update(
            {
                "min": series.min(),
                "max": series.max(),
                "mean": series.mean(),
                "std": series.std(),
            }
        )
    else:
        summary["categories"] = series.value_counts()

    return summary


def summarize_dataset(df: pd.DataFrame) -> dict[str, dict]:
    """Produce summary statistics for every column in a dataframe

    Args:
        df (pd.DataFrame): The dataframe to summarize

    Returns:
        dict[str, dict]: A mapping of column name to its summary statistics
    """
    return {column: summarize_column(df[column]) for column in df.columns}

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
    summary = summarize_dataset(combined_dataset)
    for column, stats in summary.items():
        print(f"\n=== {column} ===")
        for stat_name, value in stats.items():
            print(f"{stat_name}: {value}")

    # Task 7: Store the concatenated dataset in a new file
    output_path = DATA_DIR / "combined_listings.csv"
    combined_dataset.to_csv(output_path, index=False)
    print(f"\nSaved combined dataset to {output_path}")