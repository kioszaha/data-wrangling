import dotenv

from deliverables.deliverable_3 import main as deliverable_3
from deliverables.deliverable_4 import main as deliverable_4
from utils.sync_data import sync_data

dotenv.load_dotenv()


def main():
    # Load all listings.csv
    sync_data()

    # Deliverable 3
    deliverable_3()

    # Deliverable 4
    deliverable_4()


if __name__ == "__main__":
    main()
