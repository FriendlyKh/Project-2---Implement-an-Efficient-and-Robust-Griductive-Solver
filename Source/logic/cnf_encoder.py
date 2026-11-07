# Owner: Person 2
"""
logic.cnf_encoder — CNF Clause Encoder
========================================

Converts each :class:`~models.clue.Clue` into a list of clauses in
**DIMACS-style CNF** format.  Each clause is a list of signed integers
where:

* ``+i`` means variable *i* is TRUE  (character is CRIMINAL)
* ``-i`` means variable *i* is FALSE (character is INNOCENT)

Encoding strategies
-------------------
* **FACT** / **SAME** / **DIFFERENT**: direct propositional encoding.
* **EXACTLY** / **AT_LEAST** / **AT_MOST**: combinatorial (enumerate
  all disallowed subsets) — acceptable for small grids (≤ 6×6).
* **PARITY**: encode parity constraints via XOR → CNF conversion.
* **COMPARE**: encode relative comparisons between two regions.

The encoder tracks **auxiliary variables** if any advanced encoding
requires them (e.g. Tseitin transformation for PARITY).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

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
from logic.variable_map import VariableMap

# Type alias: a clause is a list of signed ints, a CNF is a list of clauses.
Clause = List[int]
CNF = List[Clause]


class CNFEncoder:
    """Encodes clues into CNF clauses.

    Attributes:
        grid: The puzzle grid (needed to resolve regions to cell lists).
        variable_map: The variable map for character → integer lookup.
        _aux_var_count: Number of auxiliary variables introduced so far.
        _next_aux_var: Next auxiliary variable number (starts after
            ``variable_map.num_vars``).
    """

    def __init__(self, grid: Grid, variable_map: VariableMap) -> None:
        self.grid = grid
        self.variable_map = variable_map
        self._aux_var_count: int = 0
        self._next_aux_var: int = variable_map.num_vars + 1

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def encode_clue(self, clue: Clue) -> CNF:
        """Encode a single :class:`Clue` into CNF clauses.

        Dispatches to the appropriate ``encode_*`` method based on
        ``clue.clue_type``.

        Args:
            clue: The clue to encode.

        Returns:
            A list of clauses (each clause is a list of signed ints).

        Raises:
            ValueError: If the clue type is unknown.
        """
        # TODO: Implement dispatch to specific encoder methods
        #   dispatch = {
        #       "FACT": self.encode_fact,
        #       "SAME": self.encode_same,
        #       ...
        #   }
        raise NotImplementedError("TODO: Implement CNFEncoder.encode_clue()")

    # ------------------------------------------------------------------
    # Per-clue-type encoders
    # ------------------------------------------------------------------

    def encode_fact(self, clue: FactClue) -> CNF:
        """Encode a FACT clue as a single unit clause.

        If the fact says "X is CRIMINAL", emit ``[[+x]]``.
        If "X is INNOCENT", emit ``[[-x]]``.

        Args:
            clue: The :class:`FactClue` to encode.

        Returns:
            CNF with a single unit clause.
        """
        # TODO: Implement FACT encoding
        raise NotImplementedError("TODO: Implement encode_fact()")

    def encode_same(self, clue: SameClue) -> CNF:
        """Encode a SAME clue: two characters share status.

        Equivalent to ``(A ↔ B)`` which expands to:
        * ``(¬A ∨ B)`` and ``(A ∨ ¬B)``

        Args:
            clue: The :class:`SameClue` to encode.

        Returns:
            CNF clauses encoding the biconditional.
        """
        # TODO: Implement SAME encoding
        raise NotImplementedError("TODO: Implement encode_same()")

    def encode_different(self, clue: DifferentClue) -> CNF:
        """Encode a DIFFERENT clue: two characters have different statuses.

        Equivalent to ``(A ⊕ B)`` which expands to:
        * ``(A ∨ B)`` and ``(¬A ∨ ¬B)``

        Args:
            clue: The :class:`DifferentClue` to encode.

        Returns:
            CNF clauses encoding the exclusive-or.
        """
        # TODO: Implement DIFFERENT encoding
        raise NotImplementedError("TODO: Implement encode_different()")

    def encode_exactly(self, clue: ExactlyClue) -> CNF:
        """Encode an EXACTLY-k clue: exactly *k* criminals in a region.

        Uses combinatorial encoding:
        * At-least-k (forbid all combinations of n-k+1 innocents)
        * At-most-k  (forbid all combinations of k+1 criminals)

        Args:
            clue: The :class:`ExactlyClue` to encode.

        Returns:
            CNF clauses.
        """
        # TODO: Implement EXACTLY encoding using combinations
        raise NotImplementedError("TODO: Implement encode_exactly()")

    def encode_at_least(self, clue: AtLeastClue) -> CNF:
        """Encode an AT_LEAST-k clue.

        Forbid every combination of (n - k + 1) characters all being
        innocent.

        Args:
            clue: The :class:`AtLeastClue` to encode.

        Returns:
            CNF clauses.
        """
        # TODO: Implement AT_LEAST encoding
        raise NotImplementedError("TODO: Implement encode_at_least()")

    def encode_at_most(self, clue: AtMostClue) -> CNF:
        """Encode an AT_MOST-k clue.

        Forbid every combination of (k + 1) characters all being
        criminal.

        Args:
            clue: The :class:`AtMostClue` to encode.

        Returns:
            CNF clauses.
        """
        # TODO: Implement AT_MOST encoding
        raise NotImplementedError("TODO: Implement encode_at_most()")

    def encode_parity(self, clue: ParityClue) -> CNF:
        """Encode a PARITY clue (extension): odd/even criminals in a region.

        Strategy: use XOR-chain → CNF conversion (Tseitin).

        Args:
            clue: The :class:`ParityClue` to encode.

        Returns:
            CNF clauses (may introduce auxiliary variables).
        """
        # TODO: Implement PARITY encoding
        #   Hint: XOR of n variables can be encoded with O(n) auxiliary vars
        raise NotImplementedError("TODO: Implement encode_parity()")

    def encode_compare(self, clue: CompareClue) -> CNF:
        """Encode a COMPARE clue (extension): compare counts across regions.

        Strategy: enumerate feasible count-pairs and encode as
        disjunction of EXACTLY constraints.

        Args:
            clue: The :class:`CompareClue` to encode.

        Returns:
            CNF clauses.
        """
        # TODO: Implement COMPARE encoding
        raise NotImplementedError("TODO: Implement encode_compare()")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_vars_for_region(self, clue: Clue) -> List[int]:
        """Resolve the clue's region to a list of SAT variable integers.

        Args:
            clue: A clue whose ``region`` field specifies cells.

        Returns:
            Sorted list of positive integer variables.
        """
        # TODO: Use self.grid.get_region() and self.variable_map
        raise NotImplementedError("TODO: Implement _get_vars_for_region()")

    def _new_aux_var(self) -> int:
        """Allocate and return a fresh auxiliary variable."""
        var = self._next_aux_var
        self._next_aux_var += 1
        self._aux_var_count += 1
        return var

    @property
    def aux_var_count(self) -> int:
        """Number of auxiliary variables introduced during encoding."""
        return self._aux_var_count

    @property
    def total_vars(self) -> int:
        """Total variables: original + auxiliary."""
        return self.variable_map.num_vars + self._aux_var_count
