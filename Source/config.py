# Owner: Team Lead
"""
Griductive Solver — Configuration Constants
============================================

Central configuration for grid sizes, file paths, and application-wide
constants.  Import from here so magic numbers don't leak into the codebase.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
PUZZLE_DIR = PROJECT_ROOT / "puzzles"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

# ---------------------------------------------------------------------------
# Grid constraints
# ---------------------------------------------------------------------------
MIN_GRID_SIZE = 3
MAX_GRID_SIZE = 6
VALID_COLUMNS = list("ABCDEF")  # Column letters A–F (up to 6×6)

# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------
MAX_SOLVER_TIMEOUT_SECONDS = 60  # Per SAT call
