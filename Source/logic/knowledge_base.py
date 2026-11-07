# Owner: Person 2
"""
logic.knowledge_base — Knowledge Base Management
==================================================

The :class:`KnowledgeBase` (KB) accumulates CNF clauses derived from
revealed clues and proven verdicts.  At any point in the game the KB
represents everything the solver currently knows.

The KB is **monotonic**: clauses are only added, never removed.

Structure of KB at time *t*:

.. math::

    KB_t = \\bigcup_{\\text{clue } c \\in \\text{revealed}} \\text{CNF}(c)
           \\;\\cup\\;
           \\bigcup_{\\text{cell } i \\in \\text{proved}} \\{[\\pm x_i]\\}
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from logic.cnf_encoder import CNF, CNFEncoder, Clause
from logic.variable_map import VariableMap
from models.clue import Clue
from models.grid import Grid


class KnowledgeBase:
    """Manages the active set of CNF clauses for the solver.

    Attributes:
        grid: Reference to the puzzle grid.
        variable_map: The variable mapping in use.
        encoder: The :class:`CNFEncoder` for converting clues.
        _clauses: All accumulated CNF clauses.
        _clue_origins: Maps clause index → originating clue (for tracing).
        _verdict_clauses: Unit clauses from proven verdicts.
    """

    def __init__(self, grid: Grid, variable_map: VariableMap) -> None:
        self.grid = grid
        self.variable_map = variable_map
        self.encoder = CNFEncoder(grid, variable_map)
        self._clauses: List[Clause] = []
        self._clue_origins: Dict[int, Clue] = {}
        self._verdict_clauses: List[Clause] = []

    # ------------------------------------------------------------------
    # Adding knowledge
    # ------------------------------------------------------------------

    def add_clue(self, clue: Clue) -> int:
        """Encode *clue* into CNF and add the resulting clauses to the KB.

        Args:
            clue: The :class:`Clue` to add.

        Returns:
            Number of new clauses added.
        """
        # TODO: Implement
        #   1. Call self.encoder.encode_clue(clue)
        #   2. Append new clauses to self._clauses
        #   3. Record origin in self._clue_origins
        #   4. Return count of new clauses
        raise NotImplementedError("TODO: Implement KnowledgeBase.add_clue()")

    def add_verdict(self, cell_id: str, is_criminal: bool) -> None:
        """Add a unit clause asserting the proven verdict for *cell_id*.

        If ``is_criminal`` is ``True``, adds ``[+x]``; otherwise ``[-x]``.

        Args:
            cell_id: The cell whose verdict is proven.
            is_criminal: ``True`` for CRIMINAL, ``False`` for INNOCENT.
        """
        # TODO: Implement
        #   1. Look up variable via self.variable_map
        #   2. Create unit clause [+var] or [-var]
        #   3. Append to both self._clauses and self._verdict_clauses
        raise NotImplementedError("TODO: Implement KnowledgeBase.add_verdict()")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_clauses(self) -> List[Clause]:
        """Return a copy of all active CNF clauses.

        Returns:
            List of clauses (each clause is a list of signed ints).
        """
        # TODO: Return a shallow copy of self._clauses
        raise NotImplementedError("TODO: Implement KnowledgeBase.get_clauses()")

    def get_stats(self) -> Dict[str, int]:
        """Return statistics about the current KB.

        Returns:
            Dictionary with keys:
            * ``num_vars``: total variables (original + auxiliary)
            * ``num_clauses``: total clauses
            * ``num_clue_clauses``: clauses from clues
            * ``num_verdict_clauses``: unit clauses from verdicts
            * ``num_aux_vars``: auxiliary variables introduced
        """
        # TODO: Compute and return stats
        raise NotImplementedError("TODO: Implement KnowledgeBase.get_stats()")

    def __repr__(self) -> str:
        return (
            f"KnowledgeBase(clauses={len(self._clauses)}, "
            f"verdicts={len(self._verdict_clauses)})"
        )
