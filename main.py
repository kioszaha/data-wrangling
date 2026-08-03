import dotenv

from utils.file_explorer import FileExplorer
from utils.sync_data import sync_data

dotenv.load_dotenv()


def main():
    sync_data()
    file_explorer = FileExplorer()
    june_listings = file_explorer.listings.by_month(6)


if __name__ == "__main__":
    main()
