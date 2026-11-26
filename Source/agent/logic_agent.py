# Owner: Person 4
"""
agent.logic_agent — Deductive Logic Agent
===========================================

Autonomous agent that solves Griductive puzzles using purely deductive reasoning.

Requirements (Section 4.4):
* Classifies unresolved characters as CRIMINAL, INNOCENT, or UNKNOWN.
* Never guesses: only submits forced verdicts.
* Follows the deduction loop:
    1. Scan unsolved characters deterministically (row-major order).
    2. Check entailment via DPLL SAT calls (KB ∧ ¬Ci / KB ∧ Ci).
    3. Submit forced verdict to GameEngine and reveal the character's card.
    4. Incorporate newly revealed clue into KB and repeat.
* Records each step in a :class:`~agent.trace.DeductionTrace`.
* Provides a uniqueness check for the full clue set.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from agent.entailment import EntailmentChecker
from agent.trace import DeductionTrace, TraceStep
from engine.game_engine import GameEngine
from engine.verdict import Verdict
from logic.knowledge_base import KnowledgeBase
from logic.variable_map import VariableMap
from logic.cnf_encoder import CNFEncoder
from models.clue import Clue
from models.puzzle import Puzzle
from solver.dpll import DPLL

class LogicAgent:
    """Automatic no-guess deduction agent.

    Attributes:
        solver: The DPLL SAT solver instance.
        entailment: Entailment checker built upon the solver.
        trace: Deduction trace recording all steps.
    """

    def __init__(self, solver: Optional[DPLL] = None) -> None:
        """Initialise the agent with an optional SAT solver."""
        self.solver = solver or DPLL()
        self.entailment = EntailmentChecker(self.solver)
        self.trace = DeductionTrace()

    def solve(self, engine: GameEngine) -> DeductionTrace:
        """Execute the deduction loop to solve the puzzle held by *engine*.

        Algorithm:
        1. Query public state from *engine* (revealed clues, proved verdicts).
        2. Initialise KnowledgeBase with public clues and verdicts.
        3. Loop:
            a. For all unsolved cells in row-major order:
                 check if cell's status is forced (CRIMINAL or INNOCENT).
            b. If a forced verdict is found:
                 - submit verdict to *engine*
                 - if accepted, retrieve newly revealed clue
                 - add newly revealed clue and unit clause to KB
                 - record step in trace
            c. If no unresolved cell is forced:
                 - Puzzle cannot be solved without guessing (deadlock / UNKNOWN).
                 - Break loop.
            d. If all cells are resolved:
                 - Puzzle solved successfully!
                 - Break loop.
        4. Return the recorded trace.

        Args:
            engine: The :class:`~engine.game_engine.GameEngine` instance.

        Returns:
            The completed :class:`~agent.trace.DeductionTrace`.
        """
        # TODO: Implement the deduction loop:
        #   kb = KnowledgeBase(variable_map=..., encoder=...)
        #   while not engine.is_solved():
        #       ...
        kb = engine.build_public_kb()

        while not engine.is_solved():
            step = self.step(engine, kb)

            #no unresolved cell is forced
            if step is None:
                break

            self.trace.add_step(step)

        return self.trace
    
    def step(self, engine: GameEngine, kb: KnowledgeBase) -> Optional[TraceStep]:
        """Perform a single step of deduction.

        Finds the first forced character in row-major order, submits the
        verdict to *engine*, updates *kb*, and returns the trace record.

        Args:
            engine: The game engine.
            kb: The active knowledge base.

        Returns:
            The :class:`~agent.trace.TraceStep` if a deduction was made,
            or ``None`` if no character could be forced.
        """
        # TODO: Implement single-step deduction
        unresolved_cells = engine.get_public_state()['unresolved_cells']
        queries_before = self.solver.stats.sat_calls 

        for cell_id in unresolved_cells:
            verdict = self.entailment.check_cell(kb, cell_id)


            if verdict not in (Verdict.INNOCENT, Verdict.CRIMINAL):
                continue

            active = [
                f"{cid}: {clue.description or clue.clue_type}"
                for cid, clue in engine.get_revealed_clues()
            ]
            result = engine.submit_verdict(cell_id, verdict)

            if result != Verdict.ACCEPTED:
                raise RuntimeError(
                    f"KB entails {verdict.name} for {cell_id} but engine returned {result.name}"
                )

            clue = engine.reveal_card(cell_id)

            if clue is not None:
                kb.add_clue(clue)

            kb.add_verdict(cell_id, verdict == verdict.CRIMINAL)

            cell = kb.grid.get_cell_by_id(cell_id)

            return TraceStep(
                step_number=len(self.trace.steps) + 1,
                cell_id=cell_id,
                character_name= cell.character_name if cell else 'NotFound',
                verdict=verdict,
                active_clue_ids=active,
                sat_queries_count=self.solver.stats.sat_calls - queries_before,
                newly_revealed_clue=clue.description if clue is not None else None,
                notes=None,
            )
        #no unresolved cell is forced
        return None
              

    def check_uniqueness(self, puzzle: Puzzle) -> bool:
        """Verify whether the complete set of all clues guarantees a UNIQUE solution.

        According to Section 4.4:
        "Provide a separate uniqueness check for the complete clue set."

        Algorithm:
        1. Encode ALL clues in the puzzle into a full CNF formula.
        2. Run DPLL to find a first model M1.
        3. If UNSAT -> No solution exists (invalid puzzle).
        4. Block M1 by adding clause ¬M1 = (¬l1 ∨ ¬l2 ∨ ... ∨ ¬ln).
        5. Solve again.
        6. If UNSAT -> Exactly ONE unique model exists (VALID).
        7. If SAT -> Multiple models exist (AMBIGUOUS puzzle).

        Args:
            puzzle: The puzzle to evaluate with all hidden clues revealed.

        Returns:
            ``True`` if exactly one solution exists, ``False`` otherwise.
        """
        # TODO: Implement uniqueness check via blocking clause technique
        grid = puzzle.grid
        cells = grid.get_all_cells()

        vmap = VariableMap()
        vmap.register_all([{"name": c.character_name, "cell": c.cell_id} for c in cells])
        encoder = CNFEncoder(grid, vmap)

        clauses = []
        for cell in cells:
            if cell.clue is not None:
                clauses.extend(encoder.encode_clue(cell.clue))
        num_vars = encoder.total_vars          # gồm cả biến phụ

        solver = DPLL()

        sat, model = solver.solve(clauses, num_vars)
        if not sat:
            return False          

        cell_vars = [vmap.get_var(c.cell_id) for c in cells]
        blocking = [-v if model.get(v, False) else v for v in cell_vars]

        sat2, _ = solver.solve(clauses + [blocking], num_vars)
        return not sat2

