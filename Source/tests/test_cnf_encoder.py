# Owner: Person 2 & QA
"""tests.test_cnf_encoder — Unit tests for CNF Encoding & Semantic Evaluators."""

import unittest
from logic.variable_map import VariableMap
from logic.cnf_encoder import CNFEncoder
from logic.semantic_evaluator import SemanticEvaluator
from models.cell import Cell
from models.grid import Grid
from models.clue import FactClue, SameClue, DifferentClue, ExactlyClue, AtLeastClue, AtMostClue, Region


def _create_sample_grid() -> Grid:
    """Helper to create a small 3x3 grid with mock cells for testing."""
    grid = Grid(size=3)
    try:
        for col in ["A", "B", "C"]:
            for row in [1, 2, 3]:
                cell_id = f"{col}{row}"
                grid.add_cell(Cell(row=row, col=col, character_name=f"Char_{cell_id}", profession="Resident"))
    except NotImplementedError:
        pass
    return grid


class TestVariableMap(unittest.TestCase):
    """Tests deterministic mapping between character names and SAT variables."""

    @unittest.skip("Stub: waiting for Person 2 to implement VariableMap.register()")
    def test_variable_allocation(self):
        vm = VariableMap()
        var_a = vm.register("Alice", "A1")
        var_b = vm.register("Bob", "B1")
        self.assertEqual(var_a, 1)
        self.assertEqual(var_b, 2)
        self.assertEqual(vm.get_var("A1"), 1)
        self.assertEqual(vm.get_character(1), "Alice")


class TestCNFEncoder(unittest.TestCase):
    """Tests clause generation for all required clue templates."""

    def setUp(self):
        self.grid = _create_sample_grid()
        self.vm = VariableMap()

    @unittest.skip("Stub: waiting for Person 2 to implement FactClue encoding")
    def test_encode_fact(self):
        encoder = CNFEncoder(self.grid, self.vm)
        clue = FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True)

    @unittest.skip("Stub: waiting for Person 2 to implement SameClue encoding")
    def test_encode_same(self):
        encoder = CNFEncoder(self.grid, self.vm)
        clue = SameClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1")

    @unittest.skip("Stub: waiting for Person 2 to implement DifferentClue encoding")
    def test_encode_different(self):
        encoder = CNFEncoder(self.grid, self.vm)
        clue = DifferentClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1")

    @unittest.skip("Stub: waiting for Person 2 to implement ExactlyClue encoding")
    def test_encode_exactly_k(self):
        encoder = CNFEncoder(self.grid, self.vm)
        clue = ExactlyClue(region=Region("cells", ["A1", "B1", "C1"]), k=1)


class TestSemanticEvaluator(unittest.TestCase):
    """Tests direct ground-truth evaluation without SAT solver."""

    def setUp(self):
        self.grid = _create_sample_grid()

    @unittest.skip("Stub: waiting for Person 2 to implement SemanticEvaluator")
    def test_eval_fact(self):
        evaluator = SemanticEvaluator(self.grid)


if __name__ == "__main__":
    unittest.main()
