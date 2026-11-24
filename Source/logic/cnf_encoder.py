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
import itertools

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
from models.clue import Region
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
        dispatch = {
            "FACT": self.encode_fact,
            "SAME": self.encode_same,
            "DIFFERENT": self.encode_different,
            "EXACTLY": self.encode_exactly,
            "AT_LEAST": self.encode_at_least,
            "AT_MOST": self.encode_at_most,
            "PARITY": self.encode_parity,
            "COMPARE": self.encode_compare
        }

        handler = dispatch.get(clue.clue_type.upper())
        if handler is None:
            raise ValueError("Unknown clue type.")
        return handler(clue)

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
        x = self.variable_map.get_var(clue.target_cell)
        return [[x]] if clue.is_criminal else [[-x]]

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
        a = self.variable_map.get_var(clue.cell_a)
        b = self.variable_map.get_var(clue.cell_b)
        return [[-a, b], [a, -b]]
    
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
        a = self.variable_map.get_var(clue.cell_a)
        b = self.variable_map.get_var(clue.cell_b)
        return [[a, b], [-a, -b]]

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
        return self.encode_at_most(clue) + self.encode_at_least(clue)

    def _encode_at_least_vars(self, variables: list[int], k: int) -> CNF:
        n = len(variables)

        if k <= 0:
            return []

        if k > n:
            return [[]]
        return [list(comb) for comb in itertools.combinations(variables, n - k + 1)]
    
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
        variables = self._get_vars_for_region(clue)
        return self._encode_at_least_vars(variables, clue.k)

    def _encode_at_most_vars(self, variables: list[int], k: int) -> CNF:
        n = len(variables)

        if k >= n:
            return []

        if k < 0:
            return [[]]
        return [[-v for v in comb] for comb in itertools.combinations(variables, k + 1)]

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
        variables = self._get_vars_for_region(clue)
        return self._encode_at_most_vars(variables, clue.k)

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
        if clue.parity not in ("even", "odd"):
            raise ValueError("Unknown parity.")

        variables = self._get_vars_for_region(clue)
        if not variables:
            return [] if clue.parity == "even" else [[]]

        clauses: CNF = []
        prev = variables[0]

        for x in variables[1:]:
            aux = self._new_aux_var()
            clauses.extend([
                [-aux, prev, x],
                [-aux, -prev, -x],
                [aux, -prev, x],
                [aux, prev, -x]
            ])
            prev = aux

        clauses.append([prev] if clue.parity == "odd" else [-prev])
        return clauses

    def _vars_for_region(self, region: Region) -> List[int]:
        cells = self.grid.get_region(region)
        return sorted(self.variable_map.get_var(cell.cell_id) for cell in cells)
    
    def _encode_exactly_vars(self, variables: List[int], k: int) -> CNF:
        return (
            self._encode_at_least_vars(variables, k)
            + self._encode_at_most_vars(variables, k)
        )

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
        if clue.region_b is None:
            raise ValueError("CompareClue requires region_b.")
        
        ops = {
            ">":  lambda a, b: a > b,
            "<":  lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }
        if clue.operator not in ops:
            raise ValueError("Unknown comparison operator")
        cmp_fn = ops[clue.operator]
        vars_a = self._vars_for_region(clue.region)
        vars_b = self._vars_for_region(clue.region_b)
        pairs = [
            (ka, kb)
            for ka in range(len(vars_a) + 1)
            for kb in range(len(vars_b) + 1)
            if cmp_fn(ka, kb)
        ]

        if not pairs:
            return [[]]
        
        clauses: CNF = []
        selectors: List[int] = []

        for ka, kb in pairs:
            s = self._new_aux_var()
            selectors.append(s)
            pair_clauses = (
                self._encode_exactly_vars(vars_a, ka)
                + self._encode_exactly_vars(vars_b, kb)
            )
            for clause in pair_clauses:
                clauses.append([-s] + clause)

        clauses.append(selectors)
        return clauses

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
        cells = self.grid.get_region(clue.region)
        return sorted(self.variable_map.get_var(cell.cell_id) for cell in cells)

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
