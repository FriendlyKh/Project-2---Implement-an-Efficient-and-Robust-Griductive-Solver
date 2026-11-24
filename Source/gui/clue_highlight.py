# Owner: Person 1
"""
gui.clue_highlight — Visual Clue Highlighting
================================================

Determines which grid cells should be visually highlighted when a user clicks
or hovers over a revealed clue.

Section 4.1 Requirement:
"Allow a revealed clue to be selected and visually highlight the
characters/cells referenced or counted by that clue."
"""

from __future__ import annotations

from typing import Set

from models.clue import (
    Clue,
    CompareClue,
    DifferentClue,
    FactClue,
    SameClue,
)
from models.grid import Grid


class ClueHighlighter:
    """Computes sets of cell IDs referenced by a clue."""

    @staticmethod
    def get_referenced_cells(clue: Clue, grid: Grid) -> Set[str]:
        """Compute all cell IDs affected or counted by *clue*.

        Args:
            clue: The revealed :class:`~models.clue.Clue` selected by the user.
            grid: The puzzle :class:`~models.grid.Grid`.

        Returns:
            A set of valid cell IDs (e.g. ``{'A1', 'A2', 'A3'}``).
        """
        if clue is None:
            return set()

        referenced: Set[str] = set()

        if isinstance(clue, FactClue):
            cell = grid.get_cell_by_id(clue.target_cell)
            if cell is not None:
                referenced.add(cell.cell_id)
            return referenced

        if isinstance(clue, (SameClue, DifferentClue)):
            for cid in (clue.cell_a, clue.cell_b):
                cell = grid.get_cell_by_id(cid)
                if cell is not None:
                    referenced.add(cell.cell_id)
            return referenced

        if isinstance(clue, CompareClue):
            if clue.region is not None:
                referenced.update(c.cell_id for c in grid.get_region(clue.region))
            if clue.region_b is not None:
                referenced.update(c.cell_id for c in grid.get_region(clue.region_b))
            return referenced

        # Counting clues (EXACTLY, AT_LEAST, AT_MOST), ParityClue, and any
        # generic region-based clue.
        if clue.region is not None:
            referenced.update(c.cell_id for c in grid.get_region(clue.region))

        return referenced
