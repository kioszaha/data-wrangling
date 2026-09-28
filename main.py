"""
Run the whole data-wrangling pipeline in order.

Run order: sync_data() -> deliverable_3() -> deliverable_4() -> deliverable_5().
Each stage reads only what the stages before it wrote, so the order is also
the dependency chain. See docs/design_principles.md for what each stage does.
"""

import dotenv

from deliverables.deliverable_3 import main as deliverable_3
from deliverables.deliverable_4 import main as deliverable_4
from deliverables.deliverable_5 import main as deliverable_5
from utils.sync_data import sync_data

dotenv.load_dotenv()


def main() -> None:
    # Load all listings.csv
    sync_data()

    # Deliverable 3
    deliverable_3()

    # Deliverable 4
    deliverable_4()

    # Deliverable 5
    deliverable_5()


if __name__ == "__main__":
    main()
