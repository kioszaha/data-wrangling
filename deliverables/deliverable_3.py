import pandas as pd

from utils.file_explorer import AirbnbListings, file_explorer


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
