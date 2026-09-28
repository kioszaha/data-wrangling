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
