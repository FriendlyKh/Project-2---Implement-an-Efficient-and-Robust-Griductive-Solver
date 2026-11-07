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

from typing import List, Set

from models.clue import Clue
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
            A set of cell IDs (e.g. ``{'A1', 'A2', 'A3'}``).
        """
        # TODO: Implement region extraction based on clue type:
        #   - FactClue: [clue.target_cell]
        #   - SameClue / DifferentClue: [clue.cell_a, clue.cell_b]
        #   - CountingClue (EXACTLY, AT_LEAST, AT_MOST):
        #       Extract cells from clue.region (row, col, neighbors, explicit list)
        #   - Extension clues (Compare, Parity, etc.):
        #       Extract all cells from participating regions
        raise NotImplementedError("TODO: Implement ClueHighlighter.get_referenced_cells()")
