# Owner: Person 1
"""
engine.game_engine — Game Engine
==================================

The :class:`GameEngine` is the **authority** on the puzzle.  It:

* Holds the hidden solution (the ground truth).
* Manages the pool of unrevealed clues.
* Validates submitted verdicts against both the hidden solution and
  logical provability.
* Reveals a character's clue when their card is flipped.
* Tracks whether the puzzle is fully solved.

The solver / agent never accesses the solution directly — it interacts
with the engine through its public API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from engine.verdict import Verdict
from logic.knowledge_base import KnowledgeBase
from logic.variable_map import VariableMap
from models.clue import Clue
from models.puzzle import Puzzle


def _cnf_is_sat(clauses: List[List[int]], assumptions: Optional[List[int]] = None) -> bool:
    """Internal lightweight SAT checker used only as fallback when DPLL/Entailment
    from Person 3/4 is not yet implemented.

    Works on standard DIMACS-style CNF clauses with unit propagation and backtracking.
    """
    working: List[List[int]] = [list(c) for c in clauses]
    if assumptions:
        for lit in assumptions:
            working.append([lit])

    def _simplify(formula: List[List[int]], lit: int) -> Optional[List[List[int]]]:
        neg = -lit
        reduced: List[List[int]] = []
        for clause in formula:
            if lit in clause:
                continue
            if neg in clause:
                new_clause = [x for x in clause if x != neg]
                if not new_clause:
                    return None
                reduced.append(new_clause)
            else:
                reduced.append(clause)
        return reduced

    def _solve(formula: List[List[int]]) -> bool:
        # Check empty clause / empty formula
        while True:
            if not formula:
                return True
            unit_lit: Optional[int] = None
            for clause in formula:
                if not clause:
                    return False
                if len(clause) == 1:
                    unit_lit = clause[0]
                    break
            if unit_lit is None:
                break
            simplified = _simplify(formula, unit_lit)
            if simplified is None:
                return False
            formula = simplified

        if not formula:
            return True

        # Deterministic branching on smallest clause's first literal
        branch_clause = min(formula, key=len)
        var = abs(branch_clause[0])
        for branch_lit in (var, -var):
            simplified = _simplify(formula, branch_lit)
            if simplified is not None and _solve(simplified):
                return True
        return False

    return _solve(working)


class GameEngine:
    """Owns the puzzle and mediates between the agent and the hidden solution.

    Attributes:
        puzzle: The :class:`~models.puzzle.Puzzle` being played.
        revealed_cells: Set of cell IDs whose cards have been flipped.
        verdicts: Mapping ``cell_id → Verdict`` for proven/accepted verdicts.
    """

    def __init__(
        self,
        puzzle: Puzzle,
        entailment_checker: Optional[Any] = None,
        require_proof: bool = True,
    ) -> None:
        """Initialise the engine with a loaded *puzzle*.

        Initially, only the cells in ``puzzle.initially_revealed`` are
        face-up (status and clue visible); all other cells remain hidden.

        Args:
            puzzle: The loaded :class:`~models.puzzle.Puzzle`.
            entailment_checker: Optional custom entailment checker exposing
                ``check_cell(kb, cell_id) -> Verdict``.
            require_proof: If ``True`` (default), enforces the No-Guess rule by
                verifying logical entailment before accepting any verdict.
        """
        self.puzzle = puzzle
        self.revealed_cells: set[str] = set()
        self.verdicts: Dict[str, Verdict] = {}
        self._entailment_checker = entailment_checker
        self._require_proof = require_proof

        # Reset every cell on the grid to face-down so no hidden info leaks
        for cell in self.puzzle.grid.get_all_cells():
            cell.is_revealed = False
            cell.status = None

        # Flip initially-revealed cards face-up (both status and clue are public)
        for cell_id in self.puzzle.initially_revealed:
            cid = cell_id.strip().upper()
            cell = self.puzzle.grid.get_cell_by_id(cid)
            if cell is None:
                raise ValueError(f"Initially revealed cell {cell_id!r} not found in grid")
            is_criminal = self.puzzle.solution[cid]
            verdict = Verdict.CRIMINAL if is_criminal else Verdict.INNOCENT
            cell.set_verdict(verdict.name)
            cell.reveal()
            self.revealed_cells.add(cid)
            self.verdicts[cid] = verdict

    # ------------------------------------------------------------------
    # Public knowledge base & entailment verification (Firewall-safe)
    # ------------------------------------------------------------------

    def build_public_kb(self) -> KnowledgeBase:
        """Construct a :class:`~logic.knowledge_base.KnowledgeBase` using
        **strictly public** information (revealed clues and proven verdicts).

        Never reads ``self.puzzle.solution``.
        """
        vmap = VariableMap()
        char_entries = [
            {"name": cell.character_name, "cell": cell.cell_id}
            for cell in self.puzzle.grid.get_all_cells()
        ]
        vmap.register_all(char_entries)

        kb = KnowledgeBase(grid=self.puzzle.grid, variable_map=vmap)
        for cell in self.puzzle.grid.get_all_cells():
            if cell.cell_id in self.revealed_cells and cell.clue is not None:
                kb.add_clue(cell.clue)
        for cell_id, verdict in sorted(self.verdicts.items()):
            if verdict == Verdict.CRIMINAL:
                kb.add_verdict(cell_id, True)
            elif verdict == Verdict.INNOCENT:
                kb.add_verdict(cell_id, False)
        return kb

    def check_public_entailment(self, cell_id: str) -> Verdict:
        """Determine what verdict (if any) is logically entailed for *cell_id*
        from the current public clues and proven verdicts.

        Tries Person 4's :class:`~agent.entailment.EntailmentChecker` first
        and falls back to an internal CNF checker if DPLL/Entailment is still
        a stub.
        """
        cid = cell_id.strip().upper()
        kb = self.build_public_kb()

        checker = self._entailment_checker
        if checker is None:
            try:
                from agent.entailment import EntailmentChecker

                checker = EntailmentChecker()
            except Exception:
                checker = None

        if checker is not None:
            try:
                return checker.check_cell(kb, cid)
            except NotImplementedError:
                pass

        # Fallback: exact proof-by-refutation over Person 2's CNF clauses
        var = kb.variable_map.get_var(cid)
        clauses = kb.get_clauses()
        sat_neg = _cnf_is_sat(clauses, assumptions=[-var])
        sat_pos = _cnf_is_sat(clauses, assumptions=[var])

        if not sat_neg and not sat_pos:
            return Verdict.INCONSISTENT
        if not sat_neg:
            return Verdict.CRIMINAL
        if not sat_pos:
            return Verdict.INNOCENT
        return Verdict.UNKNOWN

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_verdict(self, cell_id: str, verdict: Verdict) -> Verdict:
        """Submit a verdict for character at *cell_id*.

        The engine checks (per specification Section 2.2 & 4.1):
        1. Is a verdict logically forced from revealed clues?
           - Neither verdict forced → return ``Verdict.NOT_PROVABLE`` (without
             revealing the card or leaking the hidden solution).
           - Opposite verdict forced → return ``Verdict.CONTRADICTED`` (without
             revealing the card).
        2. Does the verdict match the hidden solution?
           - No → return ``Verdict.CONTRADICTED`` (without revealing the card).
        3. Otherwise → accept the verdict, reveal the cell's clue, and
           return ``Verdict.ACCEPTED``.

        Args:
            cell_id: The cell to classify (e.g. ``'B1'``).
            verdict: ``Verdict.CRIMINAL`` or ``Verdict.INNOCENT``.

        Returns:
            Outcome of the submission (``Verdict.ACCEPTED``,
            ``Verdict.NOT_PROVABLE``, ``Verdict.CONTRADICTED``, or
            ``Verdict.INCONSISTENT``).

        Raises:
            ValueError: If *cell_id* is invalid, already resolved, or *verdict*
                is not ``Verdict.CRIMINAL`` / ``Verdict.INNOCENT``.
        """
        if verdict not in (Verdict.CRIMINAL, Verdict.INNOCENT):
            raise ValueError(
                f"Submitted verdict must be Verdict.CRIMINAL or Verdict.INNOCENT, got {verdict!r}"
            )

        cid = cell_id.strip().upper()
        cell = self.puzzle.grid.get_cell_by_id(cid)
        if cell is None or cid not in self.puzzle.solution:
            raise ValueError(f"Unknown cell ID: {cell_id!r}")

        if cid in self.verdicts:
            raise ValueError(f"Cell {cid} is already resolved")

        # 1. Logical provability check FIRST (no-guess enforcement; never leak hidden status)
        if self._require_proof:
            entailed = self.check_public_entailment(cid)
            if entailed == Verdict.INCONSISTENT:
                return Verdict.INCONSISTENT
            if entailed == Verdict.UNKNOWN:
                return Verdict.NOT_PROVABLE
            if entailed != verdict:
                return Verdict.CONTRADICTED

        # 2. Ground-truth consistency check (never reveal on contradiction)
        expected = Verdict.CRIMINAL if self.puzzle.solution[cid] else Verdict.INNOCENT
        if verdict != expected:
            return Verdict.CONTRADICTED

        # 3. Accept verdict, flip card, expose clue
        self.verdicts[cid] = verdict
        cell.set_verdict(verdict.name)
        self.reveal_card(cid)
        return Verdict.ACCEPTED

    def reveal_card(self, cell_id: str) -> Optional[Clue]:
        """Flip the card at *cell_id* and return its clue.

        After revealing, the clue is available in the cell object and
        should be added to the knowledge base by the agent.

        Args:
            cell_id: The cell whose card to flip.

        Returns:
            The :class:`Clue` carried by the character, or ``None`` if
            the character has no clue.

        Raises:
            ValueError: If *cell_id* does not exist in the grid.
        """
        cid = cell_id.strip().upper()
        cell = self.puzzle.grid.get_cell_by_id(cid)
        if cell is None:
            raise ValueError(f"Unknown cell ID: {cell_id!r}")
        cell.reveal()
        self.revealed_cells.add(cid)
        return cell.clue

    def is_solved(self) -> bool:
        """Return ``True`` if every character has a correct verdict.

        The puzzle is solved when all cells have been classified as
        either CRIMINAL or INNOCENT, and all verdicts match the hidden
        solution.
        """
        if len(self.verdicts) != len(self.puzzle.solution):
            return False
        for cid, is_criminal in self.puzzle.solution.items():
            expected = Verdict.CRIMINAL if is_criminal else Verdict.INNOCENT
            if self.verdicts.get(cid) != expected:
                return False
        return True

    def get_public_state(self) -> Dict[str, Any]:
        """Return the publicly visible game state (strictly no hidden info).

        The returned dictionary contains:
        * ``grid_size``: int
        * ``columns``: list of column letters (e.g. ``['A', 'B', 'C']``)
        * ``rows``: list of 1-based row numbers (e.g. ``[1, 2, 3]``)
        * ``cells``: list of dicts in row-major order (only revealed info;
          unrevealed cells always have ``status=None``, ``clue=None``,
          ``clue_text=None``)
        * ``verdicts``: dict mapping resolved ``cell_id → 'CRIMINAL'|'INNOCENT'``
        * ``revealed_cells``: list of revealed cell IDs in row-major order
        * ``unresolved_cells``: list of unresolved cell IDs in row-major order
        * ``is_solved``: bool

        This is safe to send to the GUI or agent.
        """
        public_cells: List[Dict[str, Any]] = []
        revealed_ordered: List[str] = []

        for cell in self.puzzle.grid.get_all_cells():
            cid = cell.cell_id
            is_rev = cid in self.revealed_cells
            if is_rev:
                revealed_ordered.append(cid)
                verdict = self.verdicts.get(cid)
                status_str = verdict.name if verdict is not None else cell.status
                clue_dict = cell.clue.to_dict() if cell.clue is not None else None
                clue_text = cell.clue.description if cell.clue is not None else None
            else:
                # Strict Firewall: never expose hidden status or hidden clue
                status_str = None
                clue_dict = None
                clue_text = None

            public_cells.append(
                {
                    "id": cid,
                    "cell_id": cid,
                    "row": cell.row,
                    "col": cell.col,
                    "character_name": cell.character_name,
                    "name": cell.character_name,
                    "profession": cell.profession,
                    "is_revealed": is_rev,
                    "status": status_str,
                    "clue": clue_dict,
                    "clue_text": clue_text,
                }
            )

        return {
            "grid_size": self.puzzle.grid.size,
            "columns": self.puzzle.grid.valid_columns,
            "rows": list(range(1, self.puzzle.grid.size + 1)),
            "cells": public_cells,
            "verdicts": {cid: v.name for cid, v in self.verdicts.items()},
            "revealed_cells": revealed_ordered,
            "unresolved_cells": self.get_unresolved_cells(),
            "is_solved": self.is_solved(),
        }

    def get_revealed_clues(self) -> List[Tuple[str, Clue]]:
        """Return ``(cell_id, clue)`` pairs for all currently revealed clues."""
        result: List[Tuple[str, Clue]] = []
        for cell in self.puzzle.grid.get_all_cells():
            if cell.cell_id in self.revealed_cells and cell.clue is not None:
                result.append((cell.cell_id, cell.clue))
        return result

    def get_unrevealed_cells(self) -> List[str]:
        """Return cell IDs that have not been revealed yet (row-major order)."""
        return [
            cell.cell_id
            for cell in self.puzzle.grid.get_all_cells()
            if cell.cell_id not in self.revealed_cells
        ]

    def get_unresolved_cells(self) -> List[str]:
        """Return cell IDs that do not yet have a submitted verdict (row-major order)."""
        return [
            cell.cell_id
            for cell in self.puzzle.grid.get_all_cells()
            if cell.cell_id not in self.verdicts
        ]

    def __repr__(self) -> str:
        total = len(self.puzzle.solution)
        resolved = len(self.verdicts)
        return f"GameEngine(resolved={resolved}/{total})"
