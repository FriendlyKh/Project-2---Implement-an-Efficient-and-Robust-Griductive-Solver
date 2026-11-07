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

from typing import Dict, List, Optional, Tuple

from agent.entailment import EntailmentChecker
from engine.verdict import Verdict
from logic.knowledge_base import KnowledgeBase
from models.cell import Cell
from models.clue import Clue


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
        # TODO: Implement hint finder:
        #   1. Iterate through unresolved cells deterministically (e.g. row-major order)
        #   2. For each cell, check entailment:
        #        verdict = self.checker.check_cell(kb, cell.cell_id)
        #   3. If verdict in (Verdict.CRIMINAL, Verdict.INNOCENT):
        #        Find an active clue that references this cell (if active_clues given)
        #        return (cell.cell_id, verdict, relevant_clue_description)
        #   4. If loop completes with no forced cells, return None.
        raise NotImplementedError("TODO: Implement HintProvider.get_hint()")
