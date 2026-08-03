import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from config import DATA_DIR


@dataclass
class Listing:
    path: Path
    date: datetime.date
    dataframe: pd.DataFrame | None = field(default=None, init=False)

    def load(self) -> pd.DataFrame:
        if self.dataframe is None:
            self.dataframe = pd.read_csv(self.path)
        return self.dataframe


class Listings:
    _FILENAME_RE = re.compile(r"listings_(\d{8})\.csv")

    def __init__(self, airbnb_dir: Path):
        """Create a Listings object

        Args:
            airbnb_dir (Path): Airbnb data directory
        """

        listings: list[Listing] = []
        self._month_map: dict[int, int] = {}

        for i, listing_path in enumerate(airbnb_dir.rglob("*")):
            date_match = self._FILENAME_RE.search(listing_path.name)

            if not date_match:
                raise ValueError(
                    f"Could not extract date from filename: {listing_path.name}"
                )

            date_string = date_match.group(1)

            date = datetime.datetime.strptime(date_string, "%Y%m%d").date()

            listings.append(Listing(listing_path, date))
            self._month_map[date.month] = i

        self.listings = listings

    def by_month(self, month: int, load: bool = True) -> pd.DataFrame:
        """Load a listings.csv file as a Pandas dataframe by the numerical month of the data

        Args:
            month (int): Month as a number, e.g 7 = July
            load (bool, optional): Calls listing.load() if unloaded. Defaults to True.

        Returns:
            pandas.DataFrame: Dataframe with the contents of the relevant listing file
        """
        if month not in self._month_map:
            return ValueError(f"There is no listings file matching the month: {month}")

        requested_listing = self.listings[self._month_map[month]]
        if load:
            requested_listing.load()

        return requested_listing


class FileExplorer:
    def __init__(self):
        """File explorer, used to browse data

        Raises:
            FileNotFoundError: _description_
        """

        airbnb_dir = DATA_DIR / "airbnb"
        if not airbnb_dir.exists():
            raise FileNotFoundError(
                f"Directory not found: {airbnb_dir}\n Did you run sync_data()?"
            )

        self.listings = Listings(airbnb_dir)
