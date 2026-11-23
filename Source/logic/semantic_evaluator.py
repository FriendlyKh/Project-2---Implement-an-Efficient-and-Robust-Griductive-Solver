# Owner: Person 2
"""
logic.semantic_evaluator — Direct Truth Evaluator
===================================================

Given a **complete assignment** (every character classified as CRIMINAL or
INNOCENT), directly evaluates whether each clue template is satisfied.

This is used for:
* Validating puzzle consistency (do all clues agree with the hidden solution?).
* Debugging the CNF encoder (compare CNF-based result against direct evaluation).
* Post-solve verification.

Unlike the SAT solver path, this evaluator does **not** use propositional
logic or CNF — it evaluates clue semantics directly.
"""

from __future__ import annotations

from typing import Dict, List

from models.clue import (
    AtLeastClue,
    AtMostClue,
    Clue,
    CompareClue,
    DifferentClue,
    ExactlyClue,
    FactClue,
    ParityClue,
    SameClue,
)
from models.grid import Grid
from models.clue import Region


class SemanticEvaluator:
    """Evaluates clues directly against a complete truth assignment.

    Attributes:
        grid: The puzzle grid.
    """

    def __init__(self, grid: Grid) -> None:
        self.grid = grid

    def evaluate(
        self, clue: Clue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate whether *clue* is satisfied under *assignment*.

        Args:
            clue: The clue to evaluate.
            assignment: Mapping ``cell_id → is_criminal`` for **every** cell.

        Returns:
            ``True`` if the clue is satisfied, ``False`` otherwise.

        Raises:
            ValueError: If the clue type is unknown.
        """
        # TODO: Implement dispatch to per-type evaluators
        _dict = {
            "FACT": self._eval_fact,
            "SAME": self._eval_same,
            "DIFFERENT": self._eval_different,
            "EXACTLY": self._eval_exactly,
            "AT_LEAST": self._eval_at_least,
            "AT_MOST": self._eval_at_most,
            "PARITY": self._eval_parity,
            "COMPARE": self._eval_compare
        }

        handler = _dict.get(clue.clue_type.upper())
        if handler is None:
            raise ValueError("Unknown clue type.")
        return handler(clue, assignment)

    def evaluate_all(
        self, clues: List[Clue], assignment: Dict[str, bool]
    ) -> Dict[str, bool]:
        """Evaluate a list of clues and return per-clue results.

        Args:
            clues: List of clues to evaluate.
            assignment: Complete truth assignment.

        Returns:
            Dictionary mapping clue description → satisfied (bool).
        """
        # TODO: Iterate over clues and call evaluate()
        _dict = {}

        for clue in clues:
            _dict[clue.description] = self.evaluate(clue, assignment)

        return _dict

    # ------------------------------------------------------------------
    # Per-type evaluators
    # ------------------------------------------------------------------

    def _eval_fact(self, clue: FactClue, assignment: Dict[str, bool]) -> bool:
        """Evaluate a FACT clue."""
        # TODO: Check assignment[clue.target_cell] == clue.is_criminal
        return assignment[clue.target_cell] == clue.is_criminal

    def _eval_same(self, clue: SameClue, assignment: Dict[str, bool]) -> bool:
        """Evaluate a SAME clue."""
        # TODO: Check assignment[cell_a] == assignment[cell_b]
        return assignment[clue.cell_a] == assignment[clue.cell_b]

    def _eval_different(
        self, clue: DifferentClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate a DIFFERENT clue."""
        # TODO: Check assignment[cell_a] != assignment[cell_b]
        return assignment[clue.cell_a] != assignment[clue.cell_b]

    def _count_criminals(self, region: Region, assignment: Dict[str, bool]) -> int:
        k = 0

        for cell in self.grid.get_region(region):
            if assignment[cell.cell_id]:
                k += 1

        return k
    
    def _eval_exactly(
        self, clue: ExactlyClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate an EXACTLY clue."""
        # TODO: Count criminals in region and check == k
        k = self._count_criminals(clue.region, assignment)
        return k == clue.k

    def _eval_at_least(
        self, clue: AtLeastClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate an AT_LEAST clue."""
        # TODO: Count criminals in region and check >= k
        k = self._count_criminals(clue.region, assignment)
        return k >= clue.k

    def _eval_at_most(
        self, clue: AtMostClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate an AT_MOST clue."""
        # TODO: Count criminals in region and check <= k
        k = self._count_criminals(clue.region, assignment)
        return k <= clue.k

    def _eval_parity(
        self, clue: ParityClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate a PARITY clue."""
        # TODO: Count criminals in region and check parity
        if clue.parity not in ("even", "odd"):
            raise ValueError("Unknown parity.")
        
        k = self._count_criminals(clue.region, assignment)
        check = "even" if k % 2 == 0 else "odd"
        return check == clue.parity

    def _eval_compare(
        self, clue: CompareClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate a COMPARE clue."""
        # TODO: Count criminals in both regions and compare
        if clue.region_b is None:
            raise ValueError("CompareClue requires region_b.")
        
        k1 = self._count_criminals(clue.region, assignment)
        k2 = self._count_criminals(clue.region_b, assignment)

        res = {
            '>': k1 > k2,
            '<': k1 < k2,
            '>=': k1 >= k2,
            '<=': k1 <= k2,
            '==': k1 == k2,
            '!=': k1 != k2
        }

        if clue.operator not in res:
            raise ValueError("Unknown comparison operator.")
        return res[clue.operator]
