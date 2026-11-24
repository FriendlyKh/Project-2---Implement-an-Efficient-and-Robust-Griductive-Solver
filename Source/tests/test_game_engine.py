# Owner: Person 1 & QA
"""tests.test_game_engine — Unit tests for Models, Game Engine, Puzzle Loader, and GUI."""

from __future__ import annotations

import unittest
from pathlib import Path

from config import PUZZLE_DIR
from engine.game_engine import GameEngine
from engine.puzzle_loader import PuzzleLoader, load_puzzle
from engine.verdict import Verdict
from gui.app import create_app
from gui.board_view import BoardView
from gui.clue_highlight import ClueHighlighter
from gui.controls import GameController
from models.cell import Cell
from models.clue import (
    AtLeastClue,
    AtMostClue,
    Clue,
    CompareClue,
    DifferentClue,
    ExactlyClue,
    FactClue,
    ParityClue,
    Region,
    SameClue,
)
from models.grid import Grid
from models.puzzle import Puzzle


class TestModels(unittest.TestCase):
    """Task 1.1 — Unit tests for Cell, Clue, Grid, and Puzzle models."""

    def test_cell_basics_and_serialization(self):
        clue = FactClue(
            region=Region("cells", ["B2"]),
            description="B2 is Criminal.",
            target_cell="B2",
            is_criminal=True,
        )
        cell = Cell(
            row=1,
            col="a",
            character_name="Alice",
            profession="Detective",
            clue=clue,
        )
        self.assertEqual(cell.cell_id, "A1")
        self.assertEqual(cell.col, "A")
        self.assertFalse(cell.is_revealed)
        self.assertIsNone(cell.status)

        cell.reveal()
        self.assertTrue(cell.is_revealed)

        cell.set_verdict("CRIMINAL")
        self.assertEqual(cell.status, "CRIMINAL")

        with self.assertRaises(ValueError):
            cell.set_verdict("GUILTY")

        serialized = cell.to_dict()
        restored = Cell.from_dict(serialized)
        self.assertEqual(restored.cell_id, "A1")
        self.assertEqual(restored.character_name, "Alice")
        self.assertEqual(restored.profession, "Detective")
        self.assertEqual(restored.status, "CRIMINAL")
        self.assertTrue(restored.is_revealed)
        self.assertIsInstance(restored.clue, FactClue)
        self.assertEqual(restored.clue.target_cell, "B2")
        self.assertTrue(restored.clue.is_criminal)

    def test_all_clue_types_roundtrip(self):
        clues = [
            FactClue(region=Region("cells", ["A1"]), target_cell="A1", is_criminal=False, description="A1 innocent"),
            SameClue(region=Region("cells", ["A1", "B1"]), cell_a="A1", cell_b="B1", description="same"),
            DifferentClue(region=Region("cells", ["A1", "C1"]), cell_a="A1", cell_b="C1", description="diff"),
            ExactlyClue(region=Region("row", 1), k=2, description="exact 2"),
            AtLeastClue(region=Region("column", "B"), k=1, description="at least 1"),
            AtMostClue(region=Region("all"), k=3, description="at most 3"),
            ParityClue(region=Region("row", 2), parity="odd", description="odd"),
            CompareClue(
                region=Region("row", 1),
                region_b=Region("row", 2),
                operator=">",
                description="row1 > row2",
            ),
        ]
        for clue in clues:
            raw = clue.to_dict()
            rebuilt = Clue.from_dict(raw)
            self.assertEqual(type(rebuilt), type(clue))
            self.assertEqual(rebuilt.to_dict(), raw)

        with self.assertRaises(ValueError):
            Clue.from_dict({"type": "UNKNOWN_TYPE", "region": {"type": "all"}})
        with self.assertRaises(ValueError):
            ParityClue(region=Region("row", 1), parity="maybe")
        with self.assertRaises(ValueError):
            CompareClue(region=Region("row", 1), region_b=Region("row", 2), operator="~=")

    def test_grid_spatial_queries(self):
        grid = Grid(size=3)
        for row in range(1, 4):
            for col in ("A", "B", "C"):
                grid.add_cell(Cell(row=row, col=col, character_name=f"Char_{col}{row}", profession="Guard"))

        # Coordinates A1..C3 in row-major order
        all_ids = [c.cell_id for c in grid.get_all_cells()]
        self.assertEqual(all_ids, ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"])

        # get_cell & get_cell_by_id
        self.assertEqual(grid.get_cell("B", 2).cell_id, "B2")
        self.assertEqual(grid.get_cell_by_id("c3").cell_id, "C3")
        self.assertIsNone(grid.get_cell("D", 1))
        self.assertIsNone(grid.get_cell_by_id("invalid"))

        # Rows and columns
        self.assertEqual([c.cell_id for c in grid.get_row(2)], ["A2", "B2", "C2"])
        self.assertEqual([c.cell_id for c in grid.get_column("B")], ["B1", "B2", "B3"])

        # 8-neighborhood (excluding self)
        center_neighbors = [c.cell_id for c in grid.get_neighbors("B", 2)]
        self.assertEqual(center_neighbors, ["A1", "B1", "C1", "A2", "C2", "A3", "B3", "C3"])
        self.assertNotIn("B2", center_neighbors)

        corner_neighbors = [c.cell_id for c in grid.get_neighbors("A", 1)]
        self.assertEqual(corner_neighbors, ["B1", "A2", "B2"])

        edge_neighbors = [c.cell_id for c in grid.get_neighbors("B", 1)]
        self.assertEqual(edge_neighbors, ["A1", "C1", "A2", "B2", "C2"])

        # Region resolution
        self.assertEqual([c.cell_id for c in grid.get_region(Region("row", 1))], ["A1", "B1", "C1"])
        self.assertEqual([c.cell_id for c in grid.get_region(Region("column", "C"))], ["C1", "C2", "C3"])
        self.assertEqual([c.cell_id for c in grid.get_region(Region("cells", ["C3", "A1"]))], ["C3", "A1"])
        self.assertEqual([c.cell_id for c in grid.get_region(Region("neighbors", "A1"))], ["B1", "A2", "B2"])
        self.assertEqual(len(grid.get_region(Region("all"))), 9)

        # Duplicate / out-of-bounds guards
        with self.assertRaises(ValueError):
            grid.add_cell(Cell(row=1, col="A", character_name="Dup", profession="Guard"))
        with self.assertRaises(ValueError):
            grid.add_cell(Cell(row=4, col="A", character_name="OOB", profession="Guard"))

    def test_puzzle_json_roundtrip(self):
        path = PUZZLE_DIR / "3x3" / "puzzle_01.json"
        puzzle = Puzzle.from_json(path)
        self.assertEqual(puzzle.grid.size, 3)
        self.assertEqual(puzzle.initially_revealed, ["A1", "C3"])
        self.assertEqual(puzzle.get_criminals(), ["A1", "A2", "B3"])
        self.assertEqual(len(puzzle.get_innocents()), 6)

        # Grid cells must not leak solution status on load
        for cell in puzzle.grid.get_all_cells():
            self.assertIsNone(cell.status)
            self.assertFalse(cell.is_revealed)

        rebuilt = Puzzle.from_dict(puzzle.to_dict())
        self.assertEqual(rebuilt.solution, puzzle.solution)
        self.assertEqual(rebuilt.initially_revealed, puzzle.initially_revealed)


class TestPuzzleLoader(unittest.TestCase):
    """Task 1.2 — Unit tests for PuzzleLoader validation and batch loading."""

    def test_load_all_repository_puzzles(self):
        puzzles = PuzzleLoader.load_all(PUZZLE_DIR)
        self.assertGreaterEqual(len(puzzles), 5)
        sizes = [p.grid.size for p in puzzles]
        self.assertIn(3, sizes)
        self.assertIn(4, sizes)
        self.assertIn(5, sizes)

    def test_validate_rejects_malformed_data(self):
        with self.assertRaises(ValueError):
            PuzzleLoader.validate({"size": 0, "characters": [], "initially_revealed": []})
        with self.assertRaises(ValueError):
            PuzzleLoader.validate({"size": 3, "characters": [], "initially_revealed": []})
        with self.assertRaises(FileNotFoundError):
            load_puzzle(Path("nonexistent_puzzle_xyz.json"))


class TestGameEngine(unittest.TestCase):
    """Task 1.2 — Tests game engine state isolation and verdict validation."""

    def setUp(self):
        self.puzzle_01 = PuzzleLoader.load(PUZZLE_DIR / "3x3" / "puzzle_01.json")
        self.puzzle_02 = PuzzleLoader.load(PUZZLE_DIR / "3x3" / "puzzle_02.json")

    def test_state_isolation(self):
        """Ensure public state does NOT expose hidden solutions or unrevealed clues."""
        engine = GameEngine(self.puzzle_01)
        state = engine.get_public_state()

        self.assertNotIn("solution", state)
        self.assertEqual(state["grid_size"], 3)
        self.assertFalse(state["is_solved"])

        cells_by_id = {c["id"]: c for c in state["cells"]}
        # Initially revealed cards A1 and C3 show status & clue
        self.assertTrue(cells_by_id["A1"]["is_revealed"])
        self.assertEqual(cells_by_id["A1"]["status"], "CRIMINAL")
        self.assertIsNotNone(cells_by_id["A1"]["clue_text"])

        self.assertTrue(cells_by_id["C3"]["is_revealed"])
        self.assertEqual(cells_by_id["C3"]["status"], "INNOCENT")
        self.assertIsNotNone(cells_by_id["C3"]["clue_text"])

        # All other cards MUST hide both status and clue
        for cid in ("B1", "C1", "A2", "B2", "C2", "A3", "B3"):
            self.assertFalse(cells_by_id[cid]["is_revealed"])
            self.assertIsNone(cells_by_id[cid]["status"])
            self.assertIsNone(cells_by_id[cid]["clue"])
            self.assertIsNone(cells_by_id[cid]["clue_text"])

    def test_verdict_acceptance(self):
        """Proved verdict flips card and exposes clue."""
        engine = GameEngine(self.puzzle_01)
        # C3's revealed clue states: "Henry in B3 is Criminal." -> B3 is provably CRIMINAL
        outcome = engine.submit_verdict("B3", Verdict.CRIMINAL)
        self.assertEqual(outcome, Verdict.ACCEPTED)
        self.assertIn("B3", engine.revealed_cells)
        self.assertEqual(engine.verdicts["B3"], Verdict.CRIMINAL)

        state = engine.get_public_state()
        b3 = next(c for c in state["cells"] if c["id"] == "B3")
        self.assertTrue(b3["is_revealed"])
        self.assertEqual(b3["status"], "CRIMINAL")
        self.assertIn("At least 1 criminal in column B", b3["clue_text"])

    def test_verdict_rejection(self):
        """Unproven verdict returns NOT_PROVABLE; wrong verdict returns CONTRADICTED; neither flips card."""
        engine = GameEngine(self.puzzle_01)

        # A2 is truly CRIMINAL in solution, but NOT provable from initial clues (A1, C3)
        res_guess = engine.submit_verdict("A2", Verdict.CRIMINAL)
        self.assertEqual(res_guess, Verdict.NOT_PROVABLE)
        self.assertNotIn("A2", engine.revealed_cells)
        self.assertNotIn("A2", engine.verdicts)

        # B3 is truly CRIMINAL, so calling it INNOCENT contradicts the solution
        res_wrong = engine.submit_verdict("B3", Verdict.INNOCENT)
        self.assertEqual(res_wrong, Verdict.CONTRADICTED)
        self.assertNotIn("B3", engine.revealed_cells)
        self.assertNotIn("B3", engine.verdicts)

        # Public state still hides both A2 and B3
        cells_by_id = {c["id"]: c for c in engine.get_public_state()["cells"]}
        self.assertIsNone(cells_by_id["A2"]["status"])
        self.assertIsNone(cells_by_id["A2"]["clue_text"])
        self.assertIsNone(cells_by_id["B3"]["status"])
        self.assertIsNone(cells_by_id["B3"]["clue_text"])

    def test_full_no_guess_solve_and_is_solved(self):
        """Puzzle 3x3/puzzle_02.json solves completely via deductive entailment."""
        engine = GameEngine(self.puzzle_02)
        self.assertFalse(engine.is_solved())

        while not engine.is_solved():
            progressed = False
            for cid in engine.get_unresolved_cells():
                verdict = engine.check_public_entailment(cid)
                if verdict in (Verdict.CRIMINAL, Verdict.INNOCENT):
                    self.assertEqual(engine.submit_verdict(cid, verdict), Verdict.ACCEPTED)
                    progressed = True
                    break
            self.assertTrue(progressed, "Expected puzzle_02 to solve without deadlock")

        self.assertTrue(engine.is_solved())
        self.assertEqual(engine.get_unresolved_cells(), [])
        self.assertEqual(engine.get_unrevealed_cells(), [])


class TestGUI(unittest.TestCase):
    """Task 1.3 — Unit tests for ClueHighlighter, BoardView, GameController, and Flask API."""

    def test_clue_highlighter_all_types(self):
        puzzle = PuzzleLoader.load(PUZZLE_DIR / "3x3" / "puzzle_02.json")
        grid = puzzle.grid

        # PARITY on row 1 (A1's clue)
        self.assertEqual(
            ClueHighlighter.get_referenced_cells(grid.get_cell_by_id("A1").clue, grid),
            {"A1", "B1", "C1"},
        )
        # COMPARE row 1 vs row 2 (B1's clue)
        self.assertEqual(
            ClueHighlighter.get_referenced_cells(grid.get_cell_by_id("B1").clue, grid),
            {"A1", "B1", "C1", "A2", "B2", "C2"},
        )
        # EXACTLY on column C (C1's clue)
        self.assertEqual(
            ClueHighlighter.get_referenced_cells(grid.get_cell_by_id("C1").clue, grid),
            {"C1", "C2", "C3"},
        )
        # SAME A2 & A3 (A2's clue)
        self.assertEqual(
            ClueHighlighter.get_referenced_cells(grid.get_cell_by_id("A2").clue, grid),
            {"A2", "A3"},
        )
        # FACT B3 (A3's clue)
        self.assertEqual(
            ClueHighlighter.get_referenced_cells(grid.get_cell_by_id("A3").clue, grid),
            {"B3"},
        )

    def test_board_view_respects_firewall(self):
        puzzle = PuzzleLoader.load(PUZZLE_DIR / "3x3" / "puzzle_01.json")
        engine = GameEngine(puzzle)
        view = BoardView(engine)
        board = view.get_public_board_state(highlighted_cells={"A1", "B1", "C1"})

        self.assertEqual(board["size"], 3)
        self.assertEqual(board["columns"], ["A", "B", "C"])
        self.assertEqual(board["rows"], [1, 2, 3])
        self.assertEqual(board["resolved_count"], 2)
        self.assertEqual(board["total_cells"], 9)

        by_id = {c["id"]: c for c in board["cells"]}
        self.assertTrue(by_id["A1"]["is_highlighted"])
        self.assertTrue(by_id["B1"]["is_highlighted"])
        self.assertFalse(by_id["A2"]["is_highlighted"])
        self.assertIsNone(by_id["B1"]["status"])
        self.assertIsNone(by_id["B1"]["clue_text"])

    def test_flask_endpoints_full_workflow(self):
        ctrl = GameController()
        app = create_app(ctrl)
        client = app.test_client()

        # Index page loads
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Griductive", resp.data)

        # Puzzles list
        resp = client.get("/api/puzzles")
        self.assertEqual(resp.status_code, 200)
        puzzles = resp.get_json()["puzzles"]
        self.assertGreaterEqual(len(puzzles), 5)

        # Load 3x3/puzzle_02.json
        resp = client.post("/api/load", json={"puzzle_path": "puzzles/3x3/puzzle_02.json"})
        self.assertEqual(resp.status_code, 200)
        load_data = resp.get_json()
        self.assertEqual(load_data["status"], "ok")
        self.assertEqual(load_data["board"]["resolved_count"], 2)

        # Highlight revealed clue A1 -> row 1
        resp = client.post("/api/highlight", json={"cell_id": "A1"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["cells"], ["A1", "B1", "C1"])

        # Highlight unrevealed cell B1 must be rejected (security boundary)
        resp = client.post("/api/highlight", json={"cell_id": "B1"})
        self.assertEqual(resp.status_code, 400)

        # Request hint
        resp = client.get("/api/hint")
        self.assertEqual(resp.status_code, 200)
        hint_data = resp.get_json()
        self.assertIsNotNone(hint_data["hint"])
        self.assertEqual(hint_data["hint"]["cell_id"], "B1")
        self.assertEqual(hint_data["hint"]["verdict"], "CRIMINAL")

        # Submit wrong verdict -> CONTRADICTED
        resp = client.post("/api/verdict", json={"cell_id": "B1", "verdict": "INNOCENT"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["result"], "CONTRADICTED")

        # Submit unprovable guess -> NOT_PROVABLE (A2 is innocent in solution, not yet provable)
        resp = client.post("/api/verdict", json={"cell_id": "A2", "verdict": "INNOCENT"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["result"], "NOT_PROVABLE")

        # Submit proved verdict -> ACCEPTED
        resp = client.post("/api/verdict", json={"cell_id": "B1", "verdict": "CRIMINAL"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["result"], "ACCEPTED")

        # Single step
        resp = client.post("/api/step")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.get_json()["step"])

        # Auto solve remaining steps
        resp = client.post("/api/auto")
        self.assertEqual(resp.status_code, 200)
        auto_data = resp.get_json()
        self.assertTrue(auto_data["solved"])
        self.assertTrue(auto_data["board"]["is_solved"])

        # Restart resets back to initial 2 revealed cells
        resp = client.post("/api/restart")
        self.assertEqual(resp.status_code, 200)
        restart_data = resp.get_json()
        self.assertEqual(restart_data["board"]["resolved_count"], 2)
        self.assertFalse(restart_data["board"]["is_solved"])


if __name__ == "__main__":
    unittest.main()
