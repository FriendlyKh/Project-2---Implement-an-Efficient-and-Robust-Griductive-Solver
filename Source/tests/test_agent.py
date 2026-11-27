# Owner: Person 4 & QA
"""tests.test_agent — Unit tests for the Deductive Logic Agent & Entailment."""

import unittest

from agent.entailment import EntailmentChecker
from agent.hint import HintProvider
from agent.logic_agent import LogicAgent
from config import PUZZLE_DIR
from engine.game_engine import GameEngine
from engine.puzzle_loader import load_puzzle
from engine.verdict import Verdict
from logic.knowledge_base import KnowledgeBase
from logic.variable_map import VariableMap
from models.cell import Cell
from models.clue import CompareClue, DifferentClue, ExactlyClue, FactClue, Region
from models.grid import Grid
from models.puzzle import Puzzle


def _build_2x2_kb() -> tuple[Grid, KnowledgeBase]:
    grid = Grid(size=2)
    for row, col, name in [(1, "A", "Alice"), (1, "B", "Bob"), (2, "A", "Clara"), (2, "B", "David")]:
        grid.add_cell(Cell(row=row, col=col, character_name=name, profession="Guard"))
    vmap = VariableMap()
    vmap.register_all([{"name": c.character_name, "cell": c.cell_id} for c in grid.get_all_cells()])
    return grid, KnowledgeBase(grid=grid, variable_map=vmap)


class TestEntailmentChecker(unittest.TestCase):
    """Tests entailment verification using DPLL."""

    def test_forced_criminal(self):
        _, kb = _build_2x2_kb()
        kb.add_clue(FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True))
        checker = EntailmentChecker()
        self.assertEqual(checker.check_cell(kb, "A1"), Verdict.CRIMINAL)

    def test_forced_innocent(self):
        _, kb = _build_2x2_kb()
        kb.add_clue(FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True))
        kb.add_clue(DifferentClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1"))
        checker = EntailmentChecker()
        self.assertEqual(checker.check_cell(kb, "B1"), Verdict.INNOCENT)

    def test_unknown(self):
        _, kb = _build_2x2_kb()
        kb.add_clue(FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True))
        checker = EntailmentChecker()
        self.assertEqual(checker.check_cell(kb, "A2"), Verdict.UNKNOWN)

    def test_inconsistent(self):
        _, kb = _build_2x2_kb()
        kb.add_clue(FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True))
        kb.add_clue(FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=False))
        checker = EntailmentChecker()
        self.assertEqual(checker.check_cell(kb, "B1"), Verdict.INCONSISTENT)


class TestLogicAgent(unittest.TestCase):
    """Tests no-guess deduction loop, hint provider, and uniqueness check."""

    def test_no_guess_guarantee(self):
        # Under-constrained 2x2 puzzle: only A1 revealed with no forcing clue -> must deadlock without guessing
        grid = Grid(size=2)
        for row, col, name in [(1, "A", "Alice"), (1, "B", "Bob"), (2, "A", "Clara"), (2, "B", "David")]:
            clue = ExactlyClue(region=Region("row", 2), k=1, description="Row 2 has 1 criminal") if (row, col) == (1, "A") else None
            grid.add_cell(Cell(row=row, col=col, character_name=name, profession="Guard", clue=clue))
        puzzle = Puzzle(grid=grid, solution={"A1": True, "B1": False, "A2": True, "B2": False}, initially_revealed=["A1"])
        engine = GameEngine(puzzle)
        agent = LogicAgent()

        trace = agent.solve(engine)
        self.assertFalse(engine.is_solved())
        self.assertEqual(agent.terminal_state, "UNKNOWN")
        self.assertEqual(len(trace.steps), 0)
        self.assertEqual(engine.get_unresolved_cells(), ["B1", "A2", "B2"])

    def test_inconsistent_detection(self):
        grid = Grid(size=2)
        c_a1 = FactClue(region=Region("cells", ["B1"]), target_cell="B1", is_criminal=True)
        c_a2 = FactClue(region=Region("cells", ["B1"]), target_cell="B1", is_criminal=False)
        grid.add_cell(Cell(row=1, col="A", character_name="Alice", profession="Guard", clue=c_a1))
        grid.add_cell(Cell(row=1, col="B", character_name="Bob", profession="Guard"))
        grid.add_cell(Cell(row=2, col="A", character_name="Clara", profession="Guard", clue=c_a2))
        grid.add_cell(Cell(row=2, col="B", character_name="David", profession="Guard"))
        puzzle = Puzzle(grid=grid, solution={"A1": False, "B1": True, "A2": False, "B2": False}, initially_revealed=["A1", "A2"])
        engine = GameEngine(puzzle)
        agent = LogicAgent()

        agent.solve(engine)
        self.assertEqual(agent.terminal_state, "INCONSISTENT")

    def test_uniqueness_check(self):
        agent = LogicAgent()
        # All repository puzzles should have a unique full-clue-set solution
        for path in sorted(PUZZLE_DIR.rglob("*.json")):
            puzzle = load_puzzle(path)
            self.assertTrue(agent.check_uniqueness(puzzle), f"Expected unique solution for {path.name}")

        # Ambiguous 2x2 puzzle -> False
        grid, _ = _build_2x2_kb()
        ambiguous = Puzzle(grid=grid, solution={"A1": True, "B1": False, "A2": False, "B2": False}, initially_revealed=["A1"])
        self.assertFalse(agent.check_uniqueness(ambiguous))

    def test_hint_provider_supports_compare_region_b(self):
        grid, kb = _build_2x2_kb()
        # Row 1 has 0 criminals, Row 1 == Row 2 -> Row 2 (region_b) must all be INNOCENT
        kb.add_verdict("A1", False)
        kb.add_verdict("B1", False)
        cmp_clue = CompareClue(
            region=Region("row", 1),
            region_b=Region("row", 2),
            operator="==",
            description="Row 1 equals Row 2.",
        )
        kb.add_clue(cmp_clue)
        unresolved = [grid.get_cell_by_id("A2"), grid.get_cell_by_id("B2")]
        hint = HintProvider().get_hint(kb, unresolved, [cmp_clue])
        self.assertEqual(hint, ("A2", Verdict.INNOCENT, "Row 1 equals Row 2."))


if __name__ == "__main__":
    unittest.main()
