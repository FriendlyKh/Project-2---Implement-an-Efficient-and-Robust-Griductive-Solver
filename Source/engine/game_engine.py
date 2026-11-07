# Owner: Person 1
"""
engine.game_engine — Game Engine
==================================

The :class:`GameEngine` is the **authority** on the puzzle.  It:

* Holds the hidden solution (the ground truth).
* Manages the pool of unrevealed clues.
* Validates submitted verdicts against both the hidden solution and
  logical provability.
* Reveals a character's clue when their card is flipped.
* Tracks whether the puzzle is fully solved.

The solver / agent never accesses the solution directly — it interacts
with the engine through its public API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from engine.verdict import Verdict
from models.clue import Clue
from models.puzzle import Puzzle


class GameEngine:
    """Owns the puzzle and mediates between the agent and the hidden solution.

    Attributes:
        puzzle: The :class:`~models.puzzle.Puzzle` being played.
        revealed_cells: Set of cell IDs whose cards have been flipped.
        verdicts: Mapping ``cell_id → Verdict`` for submitted verdicts.
    """

    def __init__(self, puzzle: Puzzle) -> None:
        """Initialise the engine with a loaded *puzzle*.

        Initially, only the cells in ``puzzle.initially_revealed`` are
        face-up; all others are hidden.
        """
        self.puzzle = puzzle
        self.revealed_cells: set[str] = set(puzzle.initially_revealed)
        self.verdicts: Dict[str, Verdict] = {}

        # TODO: Mark initially-revealed cells as revealed in the grid
        #   for cell_id in puzzle.initially_revealed:
        #       cell = puzzle.grid.get_cell_by_id(cell_id)
        #       cell.reveal()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_verdict(self, cell_id: str, verdict: Verdict) -> Verdict:
        """Submit a verdict for character at *cell_id*.

        The engine checks:
        1. Does the verdict match the hidden solution?
           - No → return ``Verdict.CONTRADICTED``
        2. Is the verdict logically provable from revealed clues?
           - No → return ``Verdict.NOT_PROVABLE``
        3. Otherwise → accept the verdict, reveal the cell's clue, and
           return ``Verdict.ACCEPTED``.

        Args:
            cell_id: The cell to classify.
            verdict: ``Verdict.CRIMINAL`` or ``Verdict.INNOCENT``.

        Returns:
            Outcome of the submission.
        """
        # TODO: Implement verdict validation
        #   1. Check cell_id is valid and not already resolved
        #   2. Compare verdict against self.puzzle.solution[cell_id]
        #   3. If correct, check provability (optional for scaffold)
        #   4. Record verdict, reveal clue, return result
        raise NotImplementedError("TODO: Implement GameEngine.submit_verdict()")

    def reveal_card(self, cell_id: str) -> Optional[Clue]:
        """Flip the card at *cell_id* and return its clue.

        After revealing, the clue is available in the cell object and
        should be added to the knowledge base by the agent.

        Args:
            cell_id: The cell whose card to flip.

        Returns:
            The :class:`Clue` carried by the character, or ``None`` if
            the character has no clue.
        """
        # TODO: Implement card reveal
        #   1. Mark cell as revealed
        #   2. Add cell_id to self.revealed_cells
        #   3. Return the cell's clue
        raise NotImplementedError("TODO: Implement GameEngine.reveal_card()")

    def is_solved(self) -> bool:
        """Return ``True`` if every character has a correct verdict.

        The puzzle is solved when all cells have been classified as
        either CRIMINAL or INNOCENT, and all verdicts match the hidden
        solution.
        """
        # TODO: Check that all cells have verdicts matching solution
        raise NotImplementedError("TODO: Implement GameEngine.is_solved()")

    def get_public_state(self) -> Dict[str, Any]:
        """Return the publicly visible game state (no hidden info).

        The returned dictionary contains:
        * ``grid_size``: int
        * ``cells``: list of dicts (only revealed info)
        * ``verdicts``: dict of submitted verdicts
        * ``is_solved``: bool

        This is safe to send to the GUI or agent.
        """
        # TODO: Build and return public state dict
        raise NotImplementedError("TODO: Implement GameEngine.get_public_state()")

    def get_unrevealed_cells(self) -> List[str]:
        """Return cell IDs that have not been revealed yet."""
        # TODO: Return cells not in self.revealed_cells
        raise NotImplementedError("TODO: Implement GameEngine.get_unrevealed_cells()")

    def get_unresolved_cells(self) -> List[str]:
        """Return cell IDs that do not yet have a submitted verdict."""
        # TODO: Return cells not in self.verdicts
        raise NotImplementedError("TODO: Implement GameEngine.get_unresolved_cells()")

    def __repr__(self) -> str:
        total = len(self.puzzle.solution)
        resolved = len(self.verdicts)
        return f"GameEngine(resolved={resolved}/{total})"
