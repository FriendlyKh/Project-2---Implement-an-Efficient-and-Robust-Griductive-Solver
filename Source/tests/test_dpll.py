# Owner: Person 3 & QA
"""tests.test_dpll — Unit and integration tests for DPLL, SolverStats, and ExperimentRunner."""

from __future__ import annotations

import copy
import csv
import json
import random
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

from agent.entailment import EntailmentChecker
from config import PUZZLE_DIR
from engine.puzzle_loader import PuzzleLoader
from engine.verdict import Verdict
from experiments.runner import CSV_FIELDNAMES, ExperimentResult, ExperimentRunner
from logic.knowledge_base import KnowledgeBase
from logic.semantic_evaluator import SemanticEvaluator
from logic.variable_map import VariableMap
from models.cell import Cell
from models.clue import DifferentClue, ExactlyClue, FactClue, Region, SameClue
from models.grid import Grid
from solver.dpll import CNF, DPLL
from solver.stats import SolverStats


def _verify_model(clauses: CNF, assignment: Dict[int, bool]) -> bool:
    """Independently check whether *assignment* satisfies every clause in *clauses*."""
    for clause in clauses:
        if not any(
            assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)]
            for lit in clause
        ):
            return False
    return True


def _bruteforce_is_sat(clauses: CNF, num_vars: int) -> bool:
    """Exact truth-table SAT check for small formulas (used as test oracle)."""
    for mask in range(1 << num_vars):
        assignment = {v: bool((mask >> (v - 1)) & 1) for v in range(1, num_vars + 1)}
        if _verify_model(clauses, assignment):
            return True
    return False


def _pigeonhole_cnf(pigeons: int, holes: int) -> tuple[CNF, int]:
    """Build PHP(pigeons, holes) CNF: UNSAT whenever pigeons > holes."""
    # Variable p(i, j) = i * holes + j + 1 for i in 0..pigeons-1, j in 0..holes-1
    clauses: CNF = []
    # Every pigeon must be in at least one hole
    for i in range(pigeons):
        clauses.append([i * holes + j + 1 for j in range(holes)])
    # No hole can hold two pigeons
    for j in range(holes):
        for i1 in range(pigeons):
            for i2 in range(i1 + 1, pigeons):
                clauses.append([-(i1 * holes + j + 1), -(i2 * holes + j + 1)])
    return clauses, pigeons * holes


class TestSolverStats(unittest.TestCase):
    """Tests performance instrumentation in SolverStats."""

    def test_counters_and_serialization(self):
        stats = SolverStats()
        self.assertEqual(stats.decisions, 0)
        self.assertEqual(stats.propagations, 0)
        self.assertEqual(stats.backtracks, 0)
        self.assertEqual(stats.conflicts, 0)
        self.assertEqual(stats.sat_calls, 0)
        self.assertEqual(stats.runtime_seconds, 0.0)

        stats.start_timer()
        stats.record_sat_call()
        stats.record_decision()
        stats.record_propagation()
        stats.record_propagation()
        stats.record_conflict()
        stats.record_backtrack()
        stats.stop_timer()
        # Stopping twice should be a safe no-op
        elapsed = stats.runtime_seconds
        stats.stop_timer()
        self.assertEqual(stats.runtime_seconds, elapsed)
        self.assertGreaterEqual(stats.runtime_seconds, 0.0)

        data = stats.to_dict()
        self.assertEqual(data["sat_calls"], 1)
        self.assertEqual(data["decisions"], 1)
        self.assertEqual(data["propagations"], 2)
        self.assertEqual(data["conflicts"], 1)
        self.assertEqual(data["backtracks"], 1)
        self.assertIn("runtime_seconds", data)

    def test_merge_and_inplace_reset(self):
        s1 = SolverStats(decisions=2, propagations=5, backtracks=1, conflicts=1, sat_calls=3)
        s2 = SolverStats(decisions=4, propagations=7, backtracks=2, conflicts=3, sat_calls=5)
        s1.merge(s2)
        self.assertEqual(s1.decisions, 6)
        self.assertEqual(s1.propagations, 12)
        self.assertEqual(s1.backtracks, 3)
        self.assertEqual(s1.conflicts, 4)
        self.assertEqual(s1.sat_calls, 8)

        solver = DPLL()
        ref = solver.stats
        solver.solve([[1, 2], [-1, 2]], num_vars=2)
        self.assertGreater(ref.sat_calls, 0)
        solver.reset_stats()
        self.assertIs(solver.stats, ref)
        self.assertEqual(ref.sat_calls, 0)
        self.assertEqual(ref.decisions, 0)
        self.assertEqual(ref.propagations, 0)
        self.assertEqual(ref.backtracks, 0)


class TestDPLLSolver(unittest.TestCase):
    """Tests DPLL SAT solving, unit propagation, backtracking, assumptions, and heuristics."""

    def test_simple_sat(self):
        solver = DPLL()
        # (x1 ∨ x2) ∧ (¬x1 ∨ x2) -> satisfied by x2=True
        clauses = [[1, 2], [-1, 2]]
        sat, assignment = solver.solve(clauses, num_vars=2)
        self.assertTrue(sat)
        self.assertIsNotNone(assignment)
        assert assignment is not None
        self.assertTrue(assignment[2])
        self.assertTrue(_verify_model(clauses, assignment))
        self.assertEqual(solver.stats.sat_calls, 1)

    def test_simple_unsat(self):
        solver = DPLL()
        # (x1) ∧ (¬x1) -> UNSAT
        clauses = [[1], [-1]]
        sat, assignment = solver.solve(clauses, num_vars=1)
        self.assertFalse(sat)
        self.assertIsNone(assignment)
        self.assertEqual(solver.stats.sat_calls, 1)
        self.assertGreaterEqual(solver.stats.conflicts, 1)

    def test_empty_formula_and_empty_clause(self):
        solver = DPLL()
        sat, assignment = solver.solve([], num_vars=3)
        self.assertTrue(sat)
        self.assertEqual(assignment, {1: False, 2: False, 3: False})

        sat_empty, assign_empty = solver.solve([[]], num_vars=2)
        self.assertFalse(sat_empty)
        self.assertIsNone(assign_empty)

        sat_mixed, assign_mixed = solver.solve([[1], []], num_vars=1)
        self.assertFalse(sat_mixed)
        self.assertIsNone(assign_mixed)

    def test_tautology_and_duplicate_literals(self):
        solver = DPLL()
        clauses = [[1, -1], [2, 2], [-2, 3, 3]]
        sat, assignment = solver.solve(clauses, num_vars=3)
        self.assertTrue(sat)
        assert assignment is not None
        self.assertTrue(assignment[2])
        self.assertTrue(assignment[3])
        self.assertEqual(solver.stats.decisions, 0)
        self.assertEqual(solver.stats.propagations, 2)

    def test_unit_propagation(self):
        solver = DPLL()
        # (x1) ∧ (¬x1 ∨ x2) ∧ (¬x2 ∨ x3) ∧ (¬x3 ∨ x4)
        clauses = [[1], [-1, 2], [-2, 3], [-3, 4]]
        sat, assignment = solver.solve(clauses, num_vars=4)
        self.assertTrue(sat)
        self.assertEqual(assignment, {1: True, 2: True, 3: True, 4: True})
        self.assertEqual(solver.stats.decisions, 0)
        self.assertEqual(solver.stats.backtracks, 0)
        self.assertEqual(solver.stats.propagations, 4)

    def test_unit_propagation_direct_with_partial_assignment(self):
        solver = DPLL()
        clauses = [[1, 2], [-1, 3], [-2, 4]]
        assignment = {1: False}
        simplified, updated, conflict = solver.unit_propagation(clauses, assignment)
        self.assertFalse(conflict)
        self.assertEqual(simplified, [])
        self.assertEqual(updated, {1: False, 2: True, 4: True})

    def test_backtracking_required_sat(self):
        # Choosing x1=True forces x2=True and x2=False (conflict!), so solver MUST backtrack to x1=False
        solver = DPLL(heuristic="smallest")
        clauses = [[-1, 2], [-1, -2], [1, 3]]
        sat, assignment = solver.solve(clauses, num_vars=3)
        self.assertTrue(sat)
        assert assignment is not None
        self.assertFalse(assignment[1])
        self.assertTrue(assignment[3])
        self.assertTrue(_verify_model(clauses, assignment))
        self.assertGreaterEqual(solver.stats.decisions, 1)
        self.assertGreaterEqual(solver.stats.backtracks, 1)
        self.assertGreaterEqual(solver.stats.conflicts, 1)

    def test_pigeonhole_unsat_backtracking(self):
        # PHP(4, 3): 4 pigeons into 3 holes — non-trivial UNSAT
        clauses, num_vars = _pigeonhole_cnf(4, 3)
        for heuristic in ("mom", "smallest"):
            solver = DPLL(heuristic=heuristic)
            sat, assignment = solver.solve(clauses, num_vars=num_vars)
            self.assertFalse(sat)
            self.assertIsNone(assignment)
            self.assertGreater(solver.stats.decisions, 0)
            self.assertGreater(solver.stats.backtracks, 0)
            self.assertGreater(solver.stats.conflicts, 0)

    def test_assumptions_and_input_immutability(self):
        # Formula: x1 -> x2, x2 -> x3, x1 is True -> x3 is entailed True
        original_clauses = [[1], [-1, 2], [-2, 3]]
        snapshot = copy.deepcopy(original_clauses)
        assumptions_neg = [-3]
        assumptions_pos = [3]

        solver = DPLL()
        sat_neg, assign_neg = solver.solve(
            original_clauses, num_vars=3, assumptions=assumptions_neg
        )
        sat_pos, assign_pos = solver.solve(
            original_clauses, num_vars=3, assumptions=assumptions_pos
        )

        self.assertFalse(sat_neg)
        self.assertIsNone(assign_neg)
        self.assertTrue(sat_pos)
        assert assign_pos is not None
        self.assertTrue(assign_pos[3])

        # Verify zero mutation of caller inputs
        self.assertEqual(original_clauses, snapshot)
        self.assertEqual(assumptions_neg, [-3])
        self.assertEqual(assumptions_pos, [3])

        # Contradictory assumptions -> UNSAT
        sat_contra, _ = solver.solve([], num_vars=2, assumptions=[1, -1])
        self.assertFalse(sat_contra)

    def test_random_3sat_matches_bruteforce_oracle(self):
        rng = random.Random(42)
        num_vars = 5
        for _ in range(30):
            num_clauses = rng.randint(15, 28)
            clauses: CNF = []
            for _ in range(num_clauses):
                chosen = rng.sample(range(1, num_vars + 1), 3)
                clauses.append([v if rng.choice((True, False)) else -v for v in chosen])

            expected_sat = _bruteforce_is_sat(clauses, num_vars)
            for heuristic in ("mom", "smallest"):
                for pure_lit in (False, True):
                    solver = DPLL(heuristic=heuristic, use_pure_literal=pure_lit)
                    sat, assignment = solver.solve(clauses, num_vars)
                    self.assertEqual(
                        sat,
                        expected_sat,
                        f"Mismatch for heuristic={heuristic}, pure_lit={pure_lit}",
                    )
                    if sat:
                        self.assertIsNotNone(assignment)
                        assert assignment is not None
                        self.assertTrue(_verify_model(clauses, assignment))
                    else:
                        self.assertIsNone(assignment)

    def test_determinism(self):
        clauses, num_vars = _pigeonhole_cnf(4, 3)
        s1 = DPLL(heuristic="mom")
        s2 = DPLL(heuristic="mom")
        s1.solve(clauses, num_vars)
        s2.solve(clauses, num_vars)
        self.assertEqual(s1.stats.decisions, s2.stats.decisions)
        self.assertEqual(s1.stats.propagations, s2.stats.propagations)
        self.assertEqual(s1.stats.backtracks, s2.stats.backtracks)
        self.assertEqual(s1.stats.conflicts, s2.stats.conflicts)

    def test_invalid_inputs_and_timeout(self):
        with self.assertRaises(ValueError):
            DPLL(heuristic="random")
        with self.assertRaises(ValueError):
            DPLL(timeout_seconds=0)

        solver = DPLL()
        with self.assertRaises(ValueError):
            solver.solve([[0, 1]], num_vars=1)
        with self.assertRaises(ValueError):
            solver.solve([[1]], num_vars=1, assumptions=[0])
        with self.assertRaises(ValueError):
            solver.solve([[1]], num_vars=-1)

        # Tiny timeout on hard PHP(7, 6) must raise TimeoutError and stop timer cleanly
        hard_clauses, hard_vars = _pigeonhole_cnf(7, 6)
        timed_solver = DPLL(heuristic="smallest", timeout_seconds=1e-5)
        with self.assertRaises(TimeoutError):
            timed_solver.solve(hard_clauses, hard_vars)
        self.assertIsNone(timed_solver.stats._start_time)
        self.assertGreater(timed_solver.stats.runtime_seconds, 0.0)

    def test_entailment_checker_integration(self):
        grid = Grid(size=2)
        for row in (1, 2):
            for col in ("A", "B"):
                grid.add_cell(Cell(row=row, col=col, character_name=f"P_{col}{row}", profession="Guard"))

        vmap = VariableMap()
        vmap.register_all(
            [{"name": c.character_name, "cell": c.cell_id} for c in grid.get_all_cells()]
        )
        kb = KnowledgeBase(grid=grid, variable_map=vmap)
        kb.add_clue(FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=True))
        kb.add_clue(DifferentClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1"))

        solver = DPLL()
        checker = EntailmentChecker(solver)
        self.assertEqual(checker.check_cell(kb, "A1"), Verdict.CRIMINAL)
        self.assertEqual(checker.check_cell(kb, "B1"), Verdict.INNOCENT)
        self.assertEqual(checker.check_cell(kb, "A2"), Verdict.UNKNOWN)
        self.assertEqual(checker.stats.sat_calls, 6)

        # Introduce contradiction -> INCONSISTENT
        kb.add_clue(FactClue(region=Region("cells", ["B1"]), target_cell="B1", is_criminal=True))
        self.assertEqual(checker.check_cell(kb, "A2"), Verdict.INCONSISTENT)


class TestExperimentRunner(unittest.TestCase):
    """Tests batch puzzle benchmarking, metrics capture, and report exports."""

    def test_run_single_puzzle(self):
        runner = ExperimentRunner(timeout_sec=30.0)
        res = runner.run_puzzle(PUZZLE_DIR / "3x3" / "puzzle_02.json")

        self.assertIsInstance(res, ExperimentResult)
        self.assertEqual(res.puzzle_name, "3x3/puzzle_02.json")
        self.assertEqual(res.grid_size, 3)
        self.assertEqual(res.primary_vars, 9)
        self.assertGreater(res.aux_vars, 0)
        self.assertGreater(res.total_clauses, 0)
        self.assertGreater(res.sat_calls, 0)
        self.assertGreater(res.propagations, 0)
        self.assertEqual(res.deduction_steps, 7)
        self.assertGreaterEqual(res.runtime_sec, 0.0)
        self.assertTrue(res.solved)
        self.assertEqual(res.status_message, "SUCCESS")

    def test_run_all_repository_puzzles_solve_and_unique(self):
        runner = ExperimentRunner(timeout_sec=30.0)
        results = runner.run_all(PUZZLE_DIR)

        self.assertGreaterEqual(len(results), 5)
        sizes = {r.grid_size for r in results}
        self.assertTrue({3, 4, 5}.issubset(sizes))

        for res in results:
            self.assertTrue(
                res.solved,
                f"Expected {res.puzzle_name} to solve cleanly, got {res.status_message}",
            )
            self.assertEqual(res.primary_vars, res.grid_size * res.grid_size)
            self.assertGreater(res.sat_calls, 0)
            self.assertGreater(res.deduction_steps, 0)

        # Verify every puzzle in Source/puzzles is semantically consistent and uniquely solvable
        for path in sorted(PUZZLE_DIR.rglob("*.json")):
            puzzle = PuzzleLoader.load(path)
            evaluator = SemanticEvaluator(puzzle.grid)
            for cell in puzzle.grid.get_all_cells():
                if cell.clue is not None:
                    self.assertTrue(
                        evaluator.evaluate(cell.clue, puzzle.solution),
                        f"Clue contradiction in {path} at {cell.cell_id}: {cell.clue.description}",
                    )

            vmap = VariableMap()
            vmap.register_all(
                [{"name": c.character_name, "cell": c.cell_id} for c in puzzle.grid.get_all_cells()]
            )
            kb = KnowledgeBase(puzzle.grid, vmap)
            for cell in puzzle.grid.get_all_cells():
                if cell.clue is not None:
                    kb.add_clue(cell.clue)
            for cid in puzzle.initially_revealed:
                kb.add_verdict(cid, puzzle.solution[cid])

            solver = DPLL()
            clauses = kb.get_clauses()
            sat1, model1 = solver.solve(clauses, kb.encoder.total_vars)
            self.assertTrue(sat1, f"Full clue set UNSAT in {path}")
            assert model1 is not None
            blocking = [(-v if model1[v] else v) for v in range(1, vmap.num_vars + 1)]
            sat2, _ = solver.solve(clauses + [blocking], kb.encoder.total_vars)
            self.assertFalse(sat2, f"Puzzle {path} has multiple solutions (not unique)")

    def test_exports_and_heuristic_comparison(self):
        runner = ExperimentRunner(timeout_sec=30.0)
        results = runner.run_all(PUZZLE_DIR / "3x3")
        self.assertGreaterEqual(len(results), 2)

        table_str = runner.format_table(results)
        self.assertIn("3x3/puzzle_01.json", table_str)
        self.assertIn("SOLVED", table_str)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = runner.export_csv(results, tmp / "summary.csv")
            json_path = runner.export_json(results, tmp / "summary.json")
            tex_path = runner.export_latex(results, tmp / "summary.tex")

            self.assertTrue(csv_path.is_file())
            with csv_path.open("r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                self.assertEqual(reader.fieldnames, CSV_FIELDNAMES)
                rows = list(reader)
                self.assertEqual(len(rows), len(results))

            loaded_json = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(loaded_json), len(results))

            tex_text = tex_path.read_text(encoding="utf-8")
            self.assertIn("\\begin{tabular}", tex_text)

        comparison = runner.compare_heuristics(PUZZLE_DIR / "3x3")
        self.assertIn("mom", comparison)
        self.assertIn("smallest", comparison)
        self.assertEqual(len(comparison["mom"]), len(comparison["smallest"]))

    def test_error_handling(self):
        runner = ExperimentRunner()
        with self.assertRaises(FileNotFoundError):
            runner.run_all(Path("nonexistent_puzzles_dir_xyz"))

        bad_res = runner.run_puzzle(Path("nonexistent_puzzle_xyz.json"))
        self.assertFalse(bad_res.solved)
        self.assertTrue(bad_res.status_message.startswith("LOAD_ERROR:"))


if __name__ == "__main__":
    unittest.main()
