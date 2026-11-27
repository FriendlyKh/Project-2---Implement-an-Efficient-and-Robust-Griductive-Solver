# Owner: Person 2 & QA
"""tests.test_cnf_encoder — Unit tests for CNF Encoding & Semantic Evaluators."""

import unittest
from logic.variable_map import VariableMap
from logic.cnf_encoder import CNFEncoder
from logic.semantic_evaluator import SemanticEvaluator
from models.cell import Cell
from models.grid import Grid
from models.clue import (
    AtLeastClue,
    AtMostClue,
    CompareClue,
    DifferentClue,
    ExactlyClue,
    FactClue,
    ParityClue,
    Region,
    SameClue,
)
from solver.dpll import DPLL


def _create_sample_grid() -> Grid:
    """Helper to create a small 3x3 grid with cells for testing."""
    grid = Grid(size=3)
    for col in ["A", "B", "C"]:
        for row in [1, 2, 3]:
            cell_id = f"{col}{row}"
            grid.add_cell(Cell(row=row, col=col, character_name=f"Char_{cell_id}", profession="Resident"))
    return grid


class TestVariableMap(unittest.TestCase):
    """Tests deterministic mapping between character names and SAT variables."""

    def test_variable_allocation(self):
        vm = VariableMap()
        var_a = vm.register("Alice", "A1")
        var_b = vm.register("Bob", "B1")
        self.assertEqual(var_a, 1)
        self.assertEqual(var_b, 2)
        self.assertEqual(vm.get_var("A1"), 1)
        self.assertEqual(vm.get_character(1), "Alice")
        self.assertEqual(vm.get_cell_id(2), "B1")


class TestCNFEncoder(unittest.TestCase):
    """Tests clause generation for all required clue templates and extensions."""

    def setUp(self):
        self.grid = _create_sample_grid()
        self.vm = VariableMap()
        self.vm.register_all(
            [{"name": c.character_name, "cell": c.cell_id} for c in self.grid.get_all_cells()]
        )
        self.encoder = CNFEncoder(self.grid, self.vm)

    def test_encode_fact(self):
        clue = FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True)
        self.assertEqual(self.encoder.encode_clue(clue), [[self.vm.get_var("A1")]])

    def test_encode_same(self):
        clue = SameClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1")
        a, b = self.vm.get_var("A1"), self.vm.get_var("B1")
        self.assertEqual(self.encoder.encode_clue(clue), [[-a, b], [a, -b]])

    def test_encode_different(self):
        clue = DifferentClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1")
        a, b = self.vm.get_var("A1"), self.vm.get_var("B1")
        self.assertEqual(self.encoder.encode_clue(clue), [[a, b], [-a, -b]])

    def test_encode_exactly_k_and_extensions(self):
        clue = ExactlyClue(region=Region("cells", ["A1", "B1", "C1"]), k=1)
        clauses = self.encoder.encode_clue(clue)
        sat, model = DPLL().solve(clauses, self.encoder.total_vars)
        self.assertTrue(sat)
        assert model is not None
        self.assertEqual(sum(model[self.vm.get_var(cid)] for cid in ("A1", "B1", "C1")), 1)

        parity = ParityClue(region=Region("row", 1), parity="odd")
        p_clauses = self.encoder.encode_clue(parity)
        sat_p, model_p = DPLL().solve(p_clauses, self.encoder.total_vars)
        self.assertTrue(sat_p)
        assert model_p is not None
        self.assertEqual(sum(model_p[self.vm.get_var(cid)] for cid in ("A1", "B1", "C1")) % 2, 1)

        cmp_clue = CompareClue(region=Region("row", 1), region_b=Region("row", 2), operator=">")
        c_clauses = self.encoder.encode_clue(cmp_clue)
        sat_c, model_c = DPLL().solve(c_clauses, self.encoder.total_vars)
        self.assertTrue(sat_c)
        assert model_c is not None
        r1 = sum(model_c[self.vm.get_var(cid)] for cid in ("A1", "B1", "C1"))
        r2 = sum(model_c[self.vm.get_var(cid)] for cid in ("A2", "B2", "C2"))
        self.assertGreater(r1, r2)


class TestSemanticEvaluator(unittest.TestCase):
    """Tests direct ground-truth evaluation without SAT solver."""

    def setUp(self):
        self.grid = _create_sample_grid()
        self.assignment = {c.cell_id: (c.cell_id in ("A1", "B2")) for c in self.grid.get_all_cells()}

    def test_eval_fact_and_duplicate_descriptions(self):
        evaluator = SemanticEvaluator(self.grid)
        c1 = FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True, description="Same desc")
        c2 = FactClue(region=Region("cells", ["B1"]), target_cell="B1", is_criminal=True, description="Same desc")
        self.assertTrue(evaluator.evaluate(c1, self.assignment))
        self.assertFalse(evaluator.evaluate(c2, self.assignment))
        results = evaluator.evaluate_all([c1, c2], self.assignment)
        self.assertEqual(len(results), 2)
        self.assertEqual(list(results.values()), [True, False])


if __name__ == "__main__":
    unittest.main()
