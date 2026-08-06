import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from config import DATA_DIR


@dataclass
class AirbnbListing:
    """An induvidual Airbnb listing object

    Attributes:
        path (Path): Storage location of the original .csv file
        date (datetime.date): Date that the dataset was published
        dataframe (pd.DataFrame | None): A Pandas dataframe with the contents of the .csv file. Subject to modification
    """

    path: Path
    date: datetime.date
    dataframe: pd.DataFrame | None = field(default=None, init=False)

    def load(self, force=False) -> pd.DataFrame:
        """Load the .csv path as a Pandas Dataframe

        Args:
            force (bool, optional): Forces an overwrite of the data, even if it's already loaded. Defaults to False.

        Returns:
            pd.DataFrame: A loaded Pandas Dataframe of the original. csv file
        """
        if self.dataframe is None or force:
            self.dataframe = pd.read_csv(self.path)
        return self.dataframe

    def filter_christchurch(self) -> None:
        """Loads the dataframe if necessary, then mutates the DataFrame
        in place to filter by Christchurch City"""
        self.load()
        self.dataframe = self.dataframe[
            self.dataframe["neighbourhood_group"] == "Christchurch City"
        ]

    def prepare(self) -> None:
        """Loads the dataframe if necessary, then mutates the DataFrame
        in place to add month and year columns based on the publish date of the dataset"""
        self.load()
        self.dataframe["month"] = self.date.month
        self.dataframe["year"] = self.date.year


class AirbnbListings:
    """This class is used to explore the Airbnb listings data"""

    _FILENAME_RE = re.compile(r"listings_(\d{8})\.csv")

    def __init__(self, airbnb_dir: Path):
        """Create a Listings object

        Args:
            airbnb_dir (Path): Airbnb data directory
        """

        listings: list[AirbnbListing] = []
        self._month_map: dict[int, int] = {}

        for i, listing_path in enumerate(airbnb_dir.rglob("*.csv")):
            date = self._FILENAME_RE.search(listing_path.name)

            if not date:
                raise ValueError(
                    f"Could not extract date from filename: {listing_path.name}"
                )

            date = datetime.datetime.strptime(date.group(1), "%Y%m%d").date()

            listings.append(AirbnbListing(listing_path, date))
            self._month_map[date.month] = i

        self.listings = listings

    def filter_christchurch_all(self) -> None:
        """Executes Listing.filter_christchurch() for every listing"""
        for listing in self.listings:
            listing.filter_christchurch()

    def prepare_all(self) -> None:
        """Executes Listing.prepare() for every listing"""
        for listing in self.listings:
            listing.prepare()

    def by_month(self, month: int, load: bool = True) -> AirbnbListing:
        """Load a listings.csv file as a Pandas dataframe by the numerical month of the data

        Args:
            month (int): Month as a number, e.g 7 = July
            load (bool, optional): Calls listing.load() if unloaded. Defaults to True.

        Returns:
            Listing: Listing object as requested
        """
        if month not in self._month_map:
            raise ValueError(f"There is no listings file matching the month: {month}")

        requested_listing = self.listings[self._month_map[month]]
        if load:
            requested_listing.load()

        return requested_listing


def _airbnb_listings() -> AirbnbListings:
    """Utility funciton that builds the AirbnbListings object

    Raises:
        FileNotFoundError: Where there is no Airbnb directory, can be fixed by running sync_data() online

    Returns:
        AirbnbListings: The final AirbnbListings object
    """
    airbnb_dir = DATA_DIR / "airbnb"
    if not airbnb_dir.exists():
        raise FileNotFoundError(
            f"Directory not found: {airbnb_dir}\n Did you run sync_data()?"
        )
    return AirbnbListings(airbnb_dir)


def file_explorer(dataset: str) -> AirbnbListings:
    """Return a relevant data object based on what dataset you would like to explore

    Args:
        dataset (str): String key dataset. Options: "airbnb"

    Raises:
        ValueError: Where the dataset supplied is invalid

    Returns:
        AirbnbListings: Where the dataset is Airbnb
    """
    _BUILDERS = {
        "airbnb": _airbnb_listings,
    }
    try:
        return _BUILDERS[dataset]()
    except KeyError:
        raise ValueError(
            f"Unknown dataset: {dataset}. Valid datasets: {', '.join(_BUILDERS.keys())}"
        ) from None
