"""
Single source of truth for the project's directory layout.

Deriving every path from BASE_DIR rather than from the current working
directory is what makes the pipeline portable: it behaves identically when run
from the project root, from deliverables/, or from an IDE with a different
working directory. See docs/design_principles.md.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / ".data"
DATA_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = BASE_DIR / ".output"
OUTPUT_DIR.mkdir(exist_ok=True)


BONDS_FILE = DATA_DIR / "bonds" / "Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
CLEANED_LISTINGS_FILE = OUTPUT_DIR / "cleaned_listings.csv"
CLEANED_BONDS_FILE = OUTPUT_DIR / "cleaned_bonds.csv"
COMBINED_LISTINGS_FILE = OUTPUT_DIR / "combined_listings.csv"

SA2_DICTIONARY_FILE = DATA_DIR / "sa2_2026_dictionary.json"

# Deliverable 3
SUMMARY_FILE = OUTPUT_DIR / "summary.md"
PREVIOUS_WEEKS_PLOTS_PDF = OUTPUT_DIR / "test_combined_listings_graphs.pdf"

# Deliverable 5
AREA_CODE_CACHE_FILE = OUTPUT_DIR / "area_code_cache.csv"
CLEANED_LISTINGS_WITH_AREA_CODE_FILE = OUTPUT_DIR / "cleaned_listings_with_area_code.csv"
JOINED_LISTINGS_BONDS_FILE = OUTPUT_DIR / "joined_listings_bonds.csv"
GAP_BY_AREA_CSV = OUTPUT_DIR / "gap_by_area.csv"
GAP_BY_AREA_PNG = OUTPUT_DIR / "gap_by_area.png"
COUNTS_BY_AREA_CSV = OUTPUT_DIR / "counts_by_area.csv"
COUNTS_BY_AREA_PNG = OUTPUT_DIR / "counts_by_area.png"
AIRBNB_BONDS_DB_FILE = OUTPUT_DIR / "airbnb_bonds.db"
