# Owner: Person 1
"""
models.puzzle — Puzzle Data Model
===================================

A :class:`Puzzle` bundles the visible :class:`~models.grid.Grid` with the
**hidden solution** (which cells are criminals) and the list of cells that
start face-up (initially revealed).

The hidden solution is a ``dict[str, bool]`` mapping each cell ID to
``True`` (CRIMINAL) or ``False`` (INNOCENT).  The solver never peeks at
the solution directly — it is used only by the
:class:`~engine.game_engine.GameEngine` to validate verdicts and reveal
clues.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from models.grid import Grid


class Puzzle:
    """Complete puzzle definition (grid + hidden solution + metadata).

    Attributes:
        grid: The :class:`Grid` containing all character cells.
        solution: Mapping ``cell_id → is_criminal`` (hidden from solver).
        initially_revealed: List of cell IDs whose cards start face-up.
    """

    def __init__(
        self,
        grid: Grid,
        solution: Dict[str, bool],
        initially_revealed: List[str],
    ) -> None:
        self.grid = grid
        self.solution = solution
        self.initially_revealed = initially_revealed

    # ------------------------------------------------------------------
    # Serialisation / Deserialisation
    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, filepath: str | Path) -> "Puzzle":
        """Load a puzzle from a JSON file.

        The expected JSON schema is documented in ``README.md``.

        Args:
            filepath: Path to the puzzle ``.json`` file.

        Returns:
            A fully initialised :class:`Puzzle`.

        Raises:
            FileNotFoundError: If *filepath* does not exist.
            ValueError: If the JSON structure is invalid.
        """
        # TODO: Implement JSON loading
        #   1. Read JSON file
        #   2. Parse 'size', 'characters', 'initially_revealed'
        #   3. Build Grid and Cell objects
        #   4. Build solution dict from character statuses
        #   5. Create and return Puzzle
        raise NotImplementedError("TODO: Implement Puzzle.from_json()")

    def to_dict(self) -> dict:
        """Serialize the puzzle to a JSON-compatible dictionary."""
        # TODO: Implement serialization
        raise NotImplementedError("TODO: Implement Puzzle.to_dict()")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_criminals(self) -> List[str]:
        """Return cell IDs of all criminals (from the hidden solution)."""
        # TODO: Filter solution for True values
        raise NotImplementedError("TODO: Implement Puzzle.get_criminals()")

    def get_innocents(self) -> List[str]:
        """Return cell IDs of all innocents (from the hidden solution)."""
        # TODO: Filter solution for False values
        raise NotImplementedError("TODO: Implement Puzzle.get_innocents()")

    def __repr__(self) -> str:
        return (
            f"Puzzle(size={self.grid.size}, "
            f"revealed={len(self.initially_revealed)})"
        )
