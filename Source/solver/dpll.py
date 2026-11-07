# Owner: Person 3
"""
solver.dpll — DPLL SAT Solver
================================

A complete implementation of the **Davis–Putnam–Logemann–Loveland (DPLL)**
algorithm for solving propositional satisfiability (SAT) problems in
conjunctive normal form (CNF).

Key components:

1. **Unit propagation** — iteratively assign forced literals.
2. **Pure literal elimination** (optional optimisation).
3. **Conflict detection** — detect empty clauses.
4. **Branching** — choose an unassigned variable (deterministic).
5. **Backtracking** — undo assignments on conflict.

The solver works on DIMACS-style CNF:
* Variables are positive integers ``1 .. num_vars``.
* A literal is a signed int (``+i`` = TRUE, ``-i`` = FALSE).
* A clause is a list of literals (disjunction).
* The formula is a list of clauses (conjunction).

Usage::

    solver = DPLL()
    result, assignment = solver.solve(clauses, num_vars)
    # result: True (SAT) or False (UNSAT)
    # assignment: dict[int, bool] mapping var → value, or None if UNSAT
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from solver.stats import SolverStats

# Type aliases
Literal = int
Clause = List[Literal]
CNF = List[Clause]
Assignment = Dict[int, bool]


class DPLL:
    """DPLL SAT solver.

    Attributes:
        stats: :class:`SolverStats` tracking performance metrics.
    """

    def __init__(self) -> None:
        self.stats = SolverStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(
        self,
        clauses: CNF,
        num_vars: int,
        assumptions: Optional[List[Literal]] = None,
    ) -> Tuple[bool, Optional[Assignment]]:
        """Determine whether *clauses* is satisfiable.

        Args:
            clauses: List of clauses (each a list of signed ints).
            num_vars: Total number of variables (1 .. num_vars).
            assumptions: Optional list of literals to assume TRUE before
                solving.  Useful for entailment checks (``KB ∧ ¬C_i``).

        Returns:
            A tuple ``(is_sat, assignment)``:
            * ``(True, {1: True, 2: False, …})`` if satisfiable.
            * ``(False, None)`` if unsatisfiable.
        """
        # TODO: Implement the top-level DPLL entry point
        #   1. Record SAT call in stats
        #   2. Deep-copy clauses (to avoid mutation)
        #   3. Apply assumptions as unit clauses
        #   4. Call _dpll_recursive(clauses, assignment)
        #   5. Return result
        raise NotImplementedError("TODO: Implement DPLL.solve()")

    # ------------------------------------------------------------------
    # Core DPLL routines
    # ------------------------------------------------------------------

    def _dpll_recursive(
        self,
        clauses: CNF,
        assignment: Assignment,
        num_vars: int,
    ) -> Tuple[bool, Optional[Assignment]]:
        """Recursive DPLL procedure.

        Steps:
        1. Unit propagation.
        2. Check for empty clause (conflict) → backtrack.
        3. Check if all clauses satisfied → return SAT.
        4. Choose branching variable.
        5. Try variable = TRUE; recurse.
        6. If conflict, try variable = FALSE; recurse.
        7. If both fail → UNSAT.

        Args:
            clauses: Current clause set.
            assignment: Current partial assignment.
            num_vars: Total variable count.

        Returns:
            ``(is_sat, assignment_or_None)``
        """
        # TODO: Implement recursive DPLL
        raise NotImplementedError("TODO: Implement DPLL._dpll_recursive()")

    def unit_propagation(
        self,
        clauses: CNF,
        assignment: Assignment,
    ) -> Tuple[CNF, Assignment, bool]:
        """Perform unit propagation until fixpoint or conflict.

        Repeatedly find unit clauses (clauses with exactly one unassigned
        literal) and propagate the forced assignment.

        Args:
            clauses: Current clause set.
            assignment: Current partial assignment (modified in-place).

        Returns:
            A tuple ``(simplified_clauses, updated_assignment, conflict)``:
            * ``conflict`` is ``True`` if an empty clause was derived.
        """
        # TODO: Implement unit propagation
        #   Loop:
        #     1. Find a unit clause (clause with one unresolved literal)
        #     2. Assign the literal's variable accordingly
        #     3. Simplify clauses: remove satisfied clauses, shorten others
        #     4. If empty clause found → return conflict=True
        #     5. If no more unit clauses → return
        raise NotImplementedError("TODO: Implement DPLL.unit_propagation()")

    def _simplify(
        self,
        clauses: CNF,
        literal: Literal,
    ) -> CNF:
        """Simplify *clauses* given that *literal* is TRUE.

        * Remove clauses containing *literal* (they are satisfied).
        * Remove ``-literal`` from remaining clauses (it is FALSE).

        Args:
            clauses: Clause set to simplify.
            literal: The literal that is now TRUE.

        Returns:
            Simplified clause set.
        """
        # TODO: Implement clause simplification
        raise NotImplementedError("TODO: Implement DPLL._simplify()")

    def choose_variable(
        self,
        clauses: CNF,
        assignment: Assignment,
        num_vars: int,
    ) -> Optional[int]:
        """Choose the next unassigned variable to branch on.

        Strategy: pick the smallest unassigned variable (deterministic).

        Args:
            clauses: Current clause set.
            assignment: Current partial assignment.
            num_vars: Total variable count.

        Returns:
            A positive integer variable, or ``None`` if all assigned.
        """
        # TODO: Implement variable selection
        #   Simple strategy: return the smallest var in 1..num_vars
        #   not yet in assignment
        raise NotImplementedError("TODO: Implement DPLL.choose_variable()")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _has_empty_clause(self, clauses: CNF) -> bool:
        """Return ``True`` if any clause in *clauses* is empty."""
        # TODO: Check for empty clauses
        raise NotImplementedError("TODO: Implement DPLL._has_empty_clause()")

    def _all_clauses_satisfied(
        self, clauses: CNF, assignment: Assignment
    ) -> bool:
        """Return ``True`` if all clauses are satisfied by *assignment*."""
        # TODO: Check all clauses
        raise NotImplementedError("TODO: Implement DPLL._all_clauses_satisfied()")

    def reset_stats(self) -> None:
        """Reset the statistics tracker."""
        self.stats = SolverStats()
