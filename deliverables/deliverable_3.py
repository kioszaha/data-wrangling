"""
Combine the nine monthly Airbnb snapshots into one dataset (Deliverable 3)

Reads the raw listings_YYYYMMDD.csv files from .data/ and writes combined_listings.csv
plus a per-column summary.md to .output/. The four plots from last week's R Markdown
workflow are reproduced at the end via rpy2, which is the one step here with an external
runtime dependency. See docs/design_principles.md for what this stage does.
"""

from typing import Any

import pandas as pd
from rich import print

from config import OUTPUT_DIR
from deliverables.deliverable_4 import COMBINED_LISTINGS_FILE
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


def previous_weeks_plots_R(input_csv: str, output_pdf: str) -> None:

    try:
        from rpy2 import robjects

    except ValueError as e:
        if "r_home is None. Try python -m rpy2.situation" == str(e):
            print(
                "[red bold]R was not found on your system. Skipping generating plots."
            )
            return
        print(
            "[red bold]An error occurred importing robjects. Skipping generating plots."
        )
        return

    robjects.globalenv["input_csv"] = str(OUTPUT_DIR / input_csv)
    robjects.globalenv["output_pdf"] = str(OUTPUT_DIR / output_pdf)

    r_code = """
    
    library(dplyr)
    library(readr)
    library(ggplot2)

    pdf(output_pdf)

    dataset = read.csv(input_csv)

    chch_data_one = dataset %>%
      filter(neighbourhood_group == "Christchurch City")

    print(
      ggplot(chch_data_one, aes(x = price)) +
        geom_histogram(binwidth = 10, colour = "white") +
        labs(
          title = "House Prices in Christchurch City",
          x = "Price",
          y = "Number of Houses"
        ) +
        lims(x = c(0,2000)) + theme_bw()
    )

    print(
      ggplot(dataset, aes(x = price)) +
        geom_histogram(binwidth = 10, colour = "white") +
        labs(title = "House Prices in New Zealand", x = "Price", y = "Number of Houses") +
        lims(x = c(0,2000)) + theme_bw()
    )

    dataset$last_review <- as.Date(dataset$last_review, format = "%Y-%m-%d")
    dataset$days_since_june19 <- as.Date(paste(dataset$published_year, dataset$published_month, "01", sep="-")) - dataset$last_review
    dataset$days_since_june19 <- as.numeric(dataset$days_since_june19)

    print(
      ggplot(dataset, aes(x = days_since_june19)) +
        geom_histogram(colour = "white", binwidth = 25) +
        labs(
          title = "Difference Between Last Review and Publish Date in Days",
          x = "Days", y = "Count"
        ) +
        lims(x = c(0, 1000)) + theme_bw()
    )

    threshold <- quantile(dataset$number_of_reviews, 0.9, na.rm = TRUE)

    top_10 <- dataset %>%
      filter(number_of_reviews >= threshold)

    count_top10_chch <- top_10 %>%
      filter(neighbourhood_group == "Christchurch City") %>%
      nrow()

    plot.new()
    text(0.5, 0.6, "Number of Top 10% Properties in Christchurch New Zealand", cex = 1.1)
    text(0.5, 0.4, count_top10_chch, cex = 2.5)

    dev.off()
    """
    robjects.r(r_code)


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
            "published_date",
            "longitude",
            "latitude",
        ],
    )
    summary_output_path = OUTPUT_DIR / "summary.md"
    summary_df.to_markdown(summary_output_path)
    print(f"➡️ [blue] Saved summary to [bold]{summary_output_path}[/bold][/blue]")

    # Task 7: Store the concatenated dataset in a new file
    combined_dataset.to_csv(COMBINED_LISTINGS_FILE, index=False)
    print(
        f"➡️ [blue] Saved combined dataset to [bold]{COMBINED_LISTINGS_FILE}[/bold][/blue]"
    )

    # Task 8: Reproduce workflow and plots from last weeks no code software

    previous_weeks_plots_R("combined_listings.csv", "test_combined_listings_graphs.pdf")
