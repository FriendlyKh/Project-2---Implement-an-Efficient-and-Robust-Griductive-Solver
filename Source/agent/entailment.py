# Owner: Person 4
"""
agent.entailment — Entailment Checker
=======================================

Determines whether the knowledge base **entails** that a given character
is CRIMINAL, INNOCENT, or neither (UNKNOWN).

Algorithm
---------
For character variable *C_i*:

1. **Test CRIMINAL**: Solve ``KB ∧ ¬C_i``.
   - If UNSAT → KB entails ``C_i`` (character is CRIMINAL).
2. **Test INNOCENT**: Solve ``KB ∧ C_i``.
   - If UNSAT → KB entails ``¬C_i`` (character is INNOCENT).
3. **Combine results**:
   - Both UNSAT → INCONSISTENT (should never happen in valid puzzles).
   - Only step 1 UNSAT → CRIMINAL.
   - Only step 2 UNSAT → INNOCENT.
   - Both SAT → UNKNOWN (insufficient information).
"""

from __future__ import annotations

from typing import Tuple

from engine.verdict import Verdict
from logic.knowledge_base import KnowledgeBase
from solver.dpll import DPLL
from solver.stats import SolverStats


class EntailmentChecker:
    """Checks whether the KB entails a verdict for a specific variable.

    Attributes:
        solver: The :class:`~solver.dpll.DPLL` solver instance.
        stats: Aggregated solver statistics across all entailment checks.
    """

    def __init__(self, solver: DPLL | None = None) -> None:
        """Initialise the checker.

        Args:
            solver: A DPLL solver instance.  If ``None``, a new one is
                created.
        """
        self.solver = solver or DPLL()
        self.stats = SolverStats()

    def check(self, kb: KnowledgeBase, variable: int) -> Verdict:
        """Determine the entailed verdict for *variable* given *kb*.

        Performs two SAT calls:
        * ``KB ∧ ¬variable``  (assumptions=[``-variable``])
        * ``KB ∧ variable``   (assumptions=[``+variable``])

        Args:
            kb: The current knowledge base.
            variable: Positive integer SAT variable to check.

        Returns:
            One of ``Verdict.CRIMINAL``, ``Verdict.INNOCENT``,
            ``Verdict.UNKNOWN``, or ``Verdict.INCONSISTENT``.
        """
        # TODO: Implement the two-SAT-call entailment procedure
        #   1. clauses = kb.get_clauses()
        #   2. num_vars = kb.encoder.total_vars
        #   3. Test KB ∧ ¬variable:
        #        sat_neg, _ = self.solver.solve(clauses, num_vars, assumptions=[-variable])
        #   4. Test KB ∧ variable:
        #        sat_pos, _ = self.solver.solve(clauses, num_vars, assumptions=[variable])
        #   5. Combine:
        #        if not sat_neg and not sat_pos: return INCONSISTENT
        #        if not sat_neg: return CRIMINAL
        #        if not sat_pos: return INNOCENT
        #        return UNKNOWN
        raise NotImplementedError("TODO: Implement EntailmentChecker.check()")

    def check_cell(
        self, kb: KnowledgeBase, cell_id: str
    ) -> Verdict:
        """Convenience: check entailment for a cell by its ID.

        Args:
            kb: The knowledge base.
            cell_id: Cell identifier (e.g. ``'B2'``).

        Returns:
            Entailed verdict.
        """
        # TODO: Look up variable from kb.variable_map and delegate to check()
        raise NotImplementedError("TODO: Implement EntailmentChecker.check_cell()")
