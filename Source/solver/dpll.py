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

import time
from typing import Dict, List, Optional, Tuple

from solver.stats import SolverStats

# Type aliases
Literal = int
Clause = List[Literal]
CNF = List[Clause]
Assignment = Dict[int, bool]

VALID_HEURISTICS = ("mom", "smallest")


class DPLL:
    """DPLL SAT solver.

    Attributes:
        stats: :class:`SolverStats` tracking performance metrics.
        heuristic: Deterministic variable selection heuristic (``'mom'`` or
            ``'smallest'``).
        use_pure_literal: Whether to enable pure literal elimination.
        timeout_seconds: Optional per-``solve`` wall-clock timeout in seconds.
    """

    def __init__(
        self,
        heuristic: str = "mom",
        use_pure_literal: bool = False,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        norm_heuristic = str(heuristic).strip().lower()
        if norm_heuristic not in VALID_HEURISTICS:
            raise ValueError(
                f"Unknown heuristic {heuristic!r}; expected one of {VALID_HEURISTICS}"
            )
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {timeout_seconds!r}"
            )
        self.stats = SolverStats()
        self.heuristic: str = norm_heuristic
        self.use_pure_literal: bool = bool(use_pure_literal)
        self.timeout_seconds: Optional[float] = timeout_seconds
        self._deadline: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(
        self,
        clauses: CNF,
        num_vars: int,
        assumptions: Optional[List[Literal]] = None,
        timeout_seconds: Optional[float] = None,
    ) -> Tuple[bool, Optional[Assignment]]:
        """Determine whether *clauses* is satisfiable.

        Args:
            clauses: List of clauses (each a list of signed ints).
            num_vars: Total number of variables (1 .. num_vars).
            assumptions: Optional list of literals to assume TRUE before
                solving.  Useful for entailment checks (``KB ∧ ¬C_i``).
            timeout_seconds: Optional per-call timeout override (seconds).

        Returns:
            A tuple ``(is_sat, assignment)``:
            * ``(True, {1: True, 2: False, …})`` if satisfiable.
            * ``(False, None)`` if unsatisfiable.

        Raises:
            ValueError: If any literal is ``0`` or ``num_vars < 0``.
            TimeoutError: If the solver exceeds the configured timeout.
        """
        if num_vars < 0:
            raise ValueError(f"num_vars must be non-negative, got {num_vars!r}")

        effective_timeout = (
            timeout_seconds if timeout_seconds is not None else self.timeout_seconds
        )
        if effective_timeout is not None and effective_timeout <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {effective_timeout!r}"
            )

        self.stats.record_sat_call()
        self.stats.start_timer()
        self._deadline = (
            time.perf_counter() + effective_timeout
            if effective_timeout is not None
            else None
        )

        try:
            working_clauses, max_seen_var = self._prepare_clauses(clauses, assumptions)
            effective_num_vars = max(num_vars, max_seen_var)

            is_sat, assignment = self._dpll_recursive(
                working_clauses, {}, effective_num_vars
            )
            if not is_sat or assignment is None:
                return False, None

            # Complete the model deterministically for all variables 1..effective_num_vars
            complete_assignment: Assignment = {
                v: assignment.get(v, False) for v in range(1, effective_num_vars + 1)
            }
            return True, complete_assignment
        finally:
            self._deadline = None
            self.stats.stop_timer()

    # ------------------------------------------------------------------
    # Core DPLL routines
    # ------------------------------------------------------------------

    def _prepare_clauses(
        self,
        clauses: CNF,
        assumptions: Optional[List[Literal]],
    ) -> Tuple[CNF, int]:
        """Copy, validate, deduplicate clauses and append assumption unit clauses.

        Does not mutate the caller's ``clauses`` or ``assumptions``.
        """
        working: CNF = []
        max_var = 0

        for clause in clauses:
            seen: set[int] = set()
            deduped: Clause = []
            tautology = False
            for lit in clause:
                if lit == 0:
                    raise ValueError("DIMACS literals must be non-zero integers")
                var = abs(lit)
                if var > max_var:
                    max_var = var
                if -lit in seen:
                    tautology = True
                    break
                if lit not in seen:
                    seen.add(lit)
                    deduped.append(lit)
            if not tautology:
                working.append(deduped)

        if assumptions:
            for lit in assumptions:
                if lit == 0:
                    raise ValueError("Assumption literals must be non-zero integers")
                var = abs(lit)
                if var > max_var:
                    max_var = var
                working.append([lit])

        return working, max_var

    def _check_timeout(self) -> None:
        """Raise TimeoutError if the active solve deadline has elapsed."""
        if self._deadline is not None and time.perf_counter() > self._deadline:
            raise TimeoutError("DPLL solver exceeded timeout")

    def _dpll_recursive(
        self,
        clauses: CNF,
        assignment: Assignment,
        num_vars: int,
    ) -> Tuple[bool, Optional[Assignment]]:
        """Recursive DPLL procedure.

        Steps:
        1. Unit propagation.
        2. Optional pure literal elimination.
        3. Check for empty clause (conflict) → backtrack.
        4. Check if all clauses satisfied → return SAT.
        5. Choose branching variable.
        6. Try variable = TRUE; recurse.
        7. If conflict, try variable = FALSE; recurse.
        8. If both fail → UNSAT.

        Args:
            clauses: Current clause set.
            assignment: Current partial assignment.
            num_vars: Total variable count.

        Returns:
            ``(is_sat, assignment_or_None)``
        """
        self._check_timeout()

        # 1. Unit propagation
        clauses, assignment, conflict = self.unit_propagation(clauses, assignment)
        if conflict:
            return False, None

        # 2. Optional pure literal elimination
        if self.use_pure_literal and clauses:
            clauses, assignment = self._pure_literal_elimination(clauses, assignment)

        # 3. Check for empty clause (conflict)
        if self._has_empty_clause(clauses):
            self.stats.record_conflict()
            return False, None

        # 4. Check if all clauses satisfied
        if self._all_clauses_satisfied(clauses, assignment):
            return True, assignment

        # 5. Choose branching variable deterministically
        var = self.choose_variable(clauses, assignment, num_vars)
        if var is None:
            self.stats.record_conflict()
            return False, None

        # 6. Branch: try variable = TRUE
        self.stats.record_decision()
        true_assignment = dict(assignment)
        true_assignment[var] = True
        sat, result = self._dpll_recursive(
            self._simplify(clauses, var),
            true_assignment,
            num_vars,
        )
        if sat:
            return True, result

        # 7. Backtrack: try variable = FALSE
        self.stats.record_backtrack()
        false_assignment = dict(assignment)
        false_assignment[var] = False
        sat, result = self._dpll_recursive(
            self._simplify(clauses, -var),
            false_assignment,
            num_vars,
        )
        if sat:
            return True, result

        # 8. Both branches failed → UNSAT
        return False, None

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
        working = clauses

        # If caller supplied a pre-populated assignment alongside unsimplified
        # clauses, apply only bindings that still appear in working clauses.
        if assignment and working:
            pending_lits: List[Literal] = []
            seen_vars: set[int] = set()
            for clause in working:
                if len(clause) == 0:
                    self.stats.record_conflict()
                    return working, assignment, True
                for lit in clause:
                    var = abs(lit)
                    if var in assignment and var not in seen_vars:
                        seen_vars.add(var)
                        pending_lits.append(var if assignment[var] else -var)
            for lit in pending_lits:
                working = self._simplify(working, lit)
                if self._has_empty_clause(working):
                    self.stats.record_conflict()
                    return working, assignment, True

        while True:
            unit_lit: Optional[Literal] = None
            for clause in working:
                if len(clause) == 0:
                    self.stats.record_conflict()
                    return working, assignment, True
                if len(clause) == 1 and unit_lit is None:
                    unit_lit = clause[0]

            if unit_lit is None:
                return working, assignment, False

            var = abs(unit_lit)
            val = unit_lit > 0

            if var in assignment:
                if assignment[var] != val:
                    self.stats.record_conflict()
                    return working, assignment, True
            else:
                assignment[var] = val
                self.stats.record_propagation()

            working = self._simplify(working, unit_lit)

    def _pure_literal_elimination(
        self,
        clauses: CNF,
        assignment: Assignment,
    ) -> Tuple[CNF, Assignment]:
        """Assign pure literals (variables appearing with only one polarity)."""
        working = clauses
        while working:
            pos_vars: set[int] = set()
            neg_vars: set[int] = set()
            for clause in working:
                for lit in clause:
                    if lit > 0:
                        pos_vars.add(lit)
                    else:
                        neg_vars.add(-lit)

            pure_pos = sorted(pos_vars - neg_vars)
            pure_neg = sorted(neg_vars - pos_vars)
            if not pure_pos and not pure_neg:
                break

            for var in pure_pos:
                if var not in assignment:
                    assignment[var] = True
                    self.stats.record_propagation()
                    working = self._simplify(working, var)
            for var in pure_neg:
                if var not in assignment:
                    assignment[var] = False
                    self.stats.record_propagation()
                    working = self._simplify(working, -var)

        return working, assignment

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
            Simplified clause set (never mutates input clause lists).
        """
        neg = -literal
        simplified: CNF = []
        for clause in clauses:
            if literal in clause:
                continue
            if neg in clause:
                simplified.append([lit for lit in clause if lit != neg])
            else:
                simplified.append(clause)
        return simplified

    def choose_variable(
        self,
        clauses: CNF,
        assignment: Assignment,
        num_vars: int,
    ) -> Optional[int]:
        """Choose the next unassigned variable to branch on.

        Supports two deterministic strategies:
        * ``'mom'`` (default): Maximum Occurrences in clauses of Minimum Size,
          breaking ties by smallest variable index.
        * ``'smallest'``: Smallest unassigned variable index in ``1..num_vars``.

        Args:
            clauses: Current clause set.
            assignment: Current partial assignment.
            num_vars: Total variable count.

        Returns:
            A positive integer variable, or ``None`` if all assigned.
        """
        if self.heuristic == "mom" and clauses:
            min_len: Optional[int] = None
            for clause in clauses:
                clen = len(clause)
                if clen > 0 and (min_len is None or clen < min_len):
                    min_len = clen

            if min_len is not None:
                pos_counts: Dict[int, int] = {}
                neg_counts: Dict[int, int] = {}
                for clause in clauses:
                    if len(clause) != min_len:
                        continue
                    for lit in clause:
                        var = abs(lit)
                        if var in assignment:
                            continue
                        if lit > 0:
                            pos_counts[var] = pos_counts.get(var, 0) + 1
                        else:
                            neg_counts[var] = neg_counts.get(var, 0) + 1

                candidates = set(pos_counts.keys()) | set(neg_counts.keys())
                if candidates:
                    # MOM score: (f+(v) + f-(v)) * 2^2 + f+(v) * f-(v)
                    # Tie-break deterministically by smallest variable index.
                    return min(
                        candidates,
                        key=lambda v: (
                            -(
                                (pos_counts.get(v, 0) + neg_counts.get(v, 0)) * 4
                                + pos_counts.get(v, 0) * neg_counts.get(v, 0)
                            ),
                            v,
                        ),
                    )

        # Smallest unassigned variable in 1..num_vars
        for var in range(1, num_vars + 1):
            if var not in assignment:
                return var

        # Fallback if clauses reference a variable > num_vars
        extra_vars = sorted(
            {
                abs(lit)
                for clause in clauses
                for lit in clause
                if abs(lit) not in assignment
            }
        )
        return extra_vars[0] if extra_vars else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _has_empty_clause(self, clauses: CNF) -> bool:
        """Return ``True`` if any clause in *clauses* is empty."""
        return any(len(clause) == 0 for clause in clauses)

    def _all_clauses_satisfied(
        self, clauses: CNF, assignment: Assignment
    ) -> bool:
        """Return ``True`` if all clauses are satisfied by *assignment*."""
        for clause in clauses:
            satisfied = False
            for lit in clause:
                var = abs(lit)
                if var in assignment and assignment[var] == (lit > 0):
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True

    def reset_stats(self) -> None:
        """Reset the statistics tracker in-place."""
        self.stats.reset()
