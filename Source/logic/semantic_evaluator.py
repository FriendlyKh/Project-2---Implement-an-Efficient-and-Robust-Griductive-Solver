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
        raise NotImplementedError("TODO: Implement SemanticEvaluator.evaluate()")

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
        raise NotImplementedError("TODO: Implement SemanticEvaluator.evaluate_all()")

    # ------------------------------------------------------------------
    # Per-type evaluators
    # ------------------------------------------------------------------

    def _eval_fact(self, clue: FactClue, assignment: Dict[str, bool]) -> bool:
        """Evaluate a FACT clue."""
        # TODO: Check assignment[clue.target_cell] == clue.is_criminal
        raise NotImplementedError("TODO: Implement _eval_fact()")

    def _eval_same(self, clue: SameClue, assignment: Dict[str, bool]) -> bool:
        """Evaluate a SAME clue."""
        # TODO: Check assignment[cell_a] == assignment[cell_b]
        raise NotImplementedError("TODO: Implement _eval_same()")

    def _eval_different(
        self, clue: DifferentClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate a DIFFERENT clue."""
        # TODO: Check assignment[cell_a] != assignment[cell_b]
        raise NotImplementedError("TODO: Implement _eval_different()")

    def _eval_exactly(
        self, clue: ExactlyClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate an EXACTLY clue."""
        # TODO: Count criminals in region and check == k
        raise NotImplementedError("TODO: Implement _eval_exactly()")

    def _eval_at_least(
        self, clue: AtLeastClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate an AT_LEAST clue."""
        # TODO: Count criminals in region and check >= k
        raise NotImplementedError("TODO: Implement _eval_at_least()")

    def _eval_at_most(
        self, clue: AtMostClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate an AT_MOST clue."""
        # TODO: Count criminals in region and check <= k
        raise NotImplementedError("TODO: Implement _eval_at_most()")

    def _eval_parity(
        self, clue: ParityClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate a PARITY clue."""
        # TODO: Count criminals in region and check parity
        raise NotImplementedError("TODO: Implement _eval_parity()")

    def _eval_compare(
        self, clue: CompareClue, assignment: Dict[str, bool]
    ) -> bool:
        """Evaluate a COMPARE clue."""
        # TODO: Count criminals in both regions and compare
        raise NotImplementedError("TODO: Implement _eval_compare()")
