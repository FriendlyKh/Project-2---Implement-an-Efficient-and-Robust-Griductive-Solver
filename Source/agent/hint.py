# Owner: Person 4
"""
agent.hint — Hint System
========================

Provides hint suggestions without peeking at the hidden solution.

Requirements (Section 4.1 & 4.4):
* Hint must identify a character whose verdict is currently logically forced.
* Must NOT read the hidden solution from the GameEngine.
* Can also identify a relevant revealed clue that helps prove the verdict.
"""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

from agent.entailment import EntailmentChecker
from engine.verdict import Verdict
from logic.knowledge_base import KnowledgeBase
from models.cell import Cell
from models.clue import Clue, CompareClue, DifferentClue, FactClue, SameClue
from models.grid import Grid


def _get_clue_referenced_ids(clue: Clue, grid: Grid) -> Set[str]:
    """Return all cell IDs referenced or counted by *clue*."""
    if isinstance(clue, FactClue):
        return {clue.target_cell} if clue.target_cell else set()
    if isinstance(clue, (SameClue, DifferentClue)):
        return {cid for cid in (clue.cell_a, clue.cell_b) if cid}
    if isinstance(clue, CompareClue):
        ids = {c.cell_id for c in grid.get_region(clue.region)} if clue.region else set()
        if clue.region_b is not None:
            ids.update(c.cell_id for c in grid.get_region(clue.region_b))
        return ids
    return {c.cell_id for c in grid.get_region(clue.region)} if clue.region else set()


class HintProvider:
    """Computes hints by purely deductive reasoning over the public Knowledge Base."""

    def __init__(self, entailment_checker: Optional[EntailmentChecker] = None) -> None:
        """Initialise the hint provider.

        Args:
            entailment_checker: Checker used to test provability.
        """
        self.checker = entailment_checker or EntailmentChecker()

    def get_hint(
        self,
        kb: KnowledgeBase,
        unresolved_cells: List[Cell],
        active_clues: Optional[List[Clue]] = None,
    ) -> Optional[Tuple[str, Verdict, Optional[str]]]:
        """Find one cell whose verdict is currently forced by the public KB.

        Args:
            kb: The current public knowledge base.
            unresolved_cells: List of cells whose status is still unknown.
            active_clues: List of currently revealed clues (optional, to identify
                which clue helps prove the candidate).

        Returns:
            A tuple ``(cell_id, forced_verdict, explanation_or_clue_desc)``,
            or ``None`` if no character is currently forced (deadlock / ambiguous).
        """
        for cell in sorted(unresolved_cells, key=lambda c: (c.row, c.col)):
            verdict = self.checker.check_cell(kb, cell.cell_id)

            if verdict == Verdict.INCONSISTENT:
                return None

            if verdict in (Verdict.CRIMINAL, Verdict.INNOCENT):
                explanation = None
                if active_clues is not None:
                    for clue in active_clues:
                        if cell.cell_id in _get_clue_referenced_ids(clue, kb.grid):
                            explanation = clue.description or f"{clue.clue_type} clue"
                            break
                return (cell.cell_id, verdict, explanation)
        return None
