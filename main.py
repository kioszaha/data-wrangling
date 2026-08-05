import dotenv

from deliverables.deliverable_3 import main as deliverable_3
from utils.sync_data import sync_data

dotenv.load_dotenv()


def main():
    # Load all listings.csv
    sync_data()

    deliverable_3()


if __name__ == "__main__":
    main()
