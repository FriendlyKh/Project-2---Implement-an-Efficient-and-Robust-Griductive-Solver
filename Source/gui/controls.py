# Owner: Person 1
"""
gui.controls — UI Controller Actions
======================================

Implements the user interaction and gameplay commands required by Section 4.1:

* **Load**: Load a puzzle file (from JSON).
* **Restart**: Reset puzzle to initial public state.
* **Submit Verdict**: User calls a character CRIMINAL or INNOCENT.
    - If proved and correct: accepted, flipped, revealed.
    - If rejected: reports NOT_PROVABLE or CONTRADICTED without revealing hidden clue.
* **Hint**: Identify a character whose verdict can be proved next.
* **Auto Solve**: Invoke the LogicAgent to automatically solve step-by-step.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from agent.hint import HintProvider
from agent.logic_agent import LogicAgent
from config import PROJECT_ROOT, PUZZLE_DIR
from engine.game_engine import GameEngine
from engine.puzzle_loader import load_puzzle
from engine.verdict import Verdict
from gui.board_view import BoardView
from gui.clue_highlight import ClueHighlighter
from models.puzzle import Puzzle


class GameController:
    """Coordinates player UI actions with the GameEngine and LogicAgent."""

    def __init__(self, engine: Optional[GameEngine] = None) -> None:
        """Initialise controller."""
        self.engine: Optional[GameEngine] = engine
        self.board_view: Optional[BoardView] = BoardView(engine) if engine else None
        self.agent = LogicAgent()
        self.hinter = HintProvider()
        self.current_puzzle_path: Optional[str] = None
        self.highlighted_cells: Set[str] = set()
        self.highlight_source: Optional[str] = None
        self.trace_log: List[Dict[str, Any]] = []
        self._step_counter: int = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_engine(self) -> GameEngine:
        if self.engine is None or self.board_view is None:
            raise RuntimeError("No puzzle is currently loaded. Please load a puzzle first.")
        return self.engine

    @staticmethod
    def _resolve_puzzle_path(filepath: str) -> Path:
        raw = Path(filepath)
        candidates = [
            raw,
            PROJECT_ROOT / raw,
            PUZZLE_DIR / raw,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        raise FileNotFoundError(f"Puzzle file not found: {filepath}")

    def list_available_puzzles(self) -> List[Dict[str, Any]]:
        """Discover all available puzzle JSON files under ``Source/puzzles/``."""
        puzzles: List[Dict[str, Any]] = []
        if not PUZZLE_DIR.exists():
            return puzzles

        for path in sorted(
            PUZZLE_DIR.rglob("*.json"),
            key=lambda p: str(p.relative_to(PUZZLE_DIR)).replace("\\", "/"),
        ):
            rel_to_source = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            folder = path.parent.name
            stem = path.stem.replace("_", " ").title()
            label = f"{folder.replace('x', '×')} — {stem}"
            puzzles.append({"path": rel_to_source, "label": label})
        return puzzles

    def get_state(self) -> Dict[str, Any]:
        """Return current public board state and trace."""
        if self.engine is None or self.board_view is None:
            return {
                "status": "ok",
                "loaded": False,
                "puzzle_path": None,
                "board": None,
                "highlight_source": None,
                "trace": [],
            }
        return {
            "status": "ok",
            "loaded": True,
            "puzzle_path": self.current_puzzle_path,
            "board": self.board_view.get_public_board_state(self.highlighted_cells),
            "highlight_source": self.highlight_source,
            "trace": list(self.trace_log),
        }

    def _append_trace(
        self,
        kind: str,
        message: str,
        cell_id: Optional[str] = None,
        verdict: Optional[str] = None,
        clue_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        entry: Dict[str, Any] = {
            "step": self._step_counter,
            "kind": kind,
            "cell_id": cell_id,
            "verdict": verdict,
            "clue_text": clue_text,
            "message": message,
        }
        self.trace_log.append(entry)
        return entry

    def _find_supporting_clue(
        self, engine: GameEngine, target_cell_id: str
    ) -> Tuple[Optional[str], Optional[str], Set[str]]:
        """Find a revealed clue whose referenced cells include *target_cell_id*."""
        for clue_cell_id, clue in engine.get_revealed_clues():
            refs = ClueHighlighter.get_referenced_cells(clue, engine.puzzle.grid)
            if target_cell_id in refs:
                return clue_cell_id, clue.description, refs | {target_cell_id}
        # Fallback to first revealed clue if deduction is indirect across multiple clues
        revealed = engine.get_revealed_clues()
        if revealed:
            clue_cell_id, clue = revealed[0]
            refs = ClueHighlighter.get_referenced_cells(clue, engine.puzzle.grid)
            return clue_cell_id, clue.description, refs | {target_cell_id}
        return None, None, {target_cell_id}

    def _find_first_forced_cell(
        self, engine: GameEngine
    ) -> Optional[Tuple[str, Verdict]]:
        """Scan unresolved cells in deterministic row-major order and return the
        first cell whose status is logically entailed by the public KB.
        """
        for cid in engine.get_unresolved_cells():
            entailed = engine.check_public_entailment(cid)
            if entailed in (Verdict.CRIMINAL, Verdict.INNOCENT):
                return cid, entailed
        return None

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------

    def load_puzzle(self, filepath: str) -> Dict[str, Any]:
        """Load a new puzzle from disk and reset the game state.

        Args:
            filepath: Path to the puzzle JSON file.

        Returns:
            Dictionary with load status and initial public board state.
        """
        resolved = self._resolve_puzzle_path(filepath)
        puzzle = load_puzzle(resolved)
        self.engine = GameEngine(puzzle)
        self.board_view = BoardView(self.engine)
        self.current_puzzle_path = filepath
        self.highlighted_cells = set()
        self.highlight_source = None
        self.trace_log = []
        self._step_counter = 0

        revealed = ", ".join(self.engine.puzzle.initially_revealed) or "none"
        msg = (
            f"Loaded {puzzle.grid.size}×{puzzle.grid.size} puzzle "
            f"({resolved.name}). Initially revealed: {revealed}."
        )
        self._append_trace("info", msg)

        return {
            "status": "ok",
            "loaded": True,
            "message": msg,
            "puzzle_path": filepath,
            "board": self.board_view.get_public_board_state(),
            "trace": list(self.trace_log),
        }

    def restart(self) -> Dict[str, Any]:
        """Reset the current puzzle back to its initial state."""
        engine = self._require_engine()
        if self.current_puzzle_path:
            return self.load_puzzle(self.current_puzzle_path)

        fresh_puzzle = Puzzle.from_dict(engine.puzzle.to_dict())
        self.engine = GameEngine(fresh_puzzle)
        self.board_view = BoardView(self.engine)
        self.highlighted_cells = set()
        self.highlight_source = None
        self.trace_log = []
        self._step_counter = 0

        msg = "Puzzle restarted to initial state."
        self._append_trace("info", msg)
        return {
            "status": "ok",
            "loaded": True,
            "message": msg,
            "puzzle_path": self.current_puzzle_path,
            "board": self.board_view.get_public_board_state(),
            "trace": list(self.trace_log),
        }

    def submit_verdict(self, cell_id: str, verdict_str: str) -> Dict[str, Any]:
        """Handle a user's manual verdict call on a cell.

        Validates against the authoritative GameEngine:
        - If logically forced and matches truth: ACCEPTED (card flips & reveals clue)
        - If neither verdict is forced: NOT_PROVABLE (no card reveal)
        - If contradicts truth: CONTRADICTED (no card reveal)

        Args:
            cell_id: Cell identifier (e.g. ``'B2'``).
            verdict_str: ``'CRIMINAL'`` or ``'INNOCENT'``.

        Returns:
            Dictionary with result status, feedback message, and updated board state.
        """
        engine = self._require_engine()
        assert self.board_view is not None

        if not cell_id:
            raise ValueError("Missing 'cell_id'")
        cid = str(cell_id).strip().upper()
        norm_verdict = str(verdict_str or "").strip().upper()
        if norm_verdict == "CRIMINAL":
            verdict = Verdict.CRIMINAL
        elif norm_verdict == "INNOCENT":
            verdict = Verdict.INNOCENT
        else:
            raise ValueError(
                f"Invalid verdict {verdict_str!r}; expected 'CRIMINAL' or 'INNOCENT'"
            )

        cell = engine.puzzle.grid.get_cell_by_id(cid)
        if cell is None:
            raise ValueError(f"Unknown cell ID: {cid}")

        outcome = engine.submit_verdict(cid, verdict)

        if outcome == Verdict.ACCEPTED:
            self._step_counter += 1
            revealed_clue = cell.clue.description if cell.clue is not None else None
            msg = f"[Step {self._step_counter}] ACCEPTED: {cell.character_name} ({cid}) is {verdict.name}."
            if revealed_clue:
                msg += f' Revealed clue: "{revealed_clue}"'
            self._append_trace(
                "accepted",
                msg,
                cell_id=cid,
                verdict=verdict.name,
                clue_text=revealed_clue,
            )
            if engine.is_solved():
                self._append_trace("solved", "🎉 Puzzle solved completely with zero guessing!")
        elif outcome == Verdict.NOT_PROVABLE:
            revealed_clue = None
            msg = (
                f"NOT PROVABLE: {cell.character_name} ({cid}) cannot yet be logically "
                f"proven {verdict.name} from revealed clues. No guessing allowed!"
            )
            self._append_trace("warning", msg, cell_id=cid, verdict="NOT_PROVABLE")
        elif outcome == Verdict.CONTRADICTED:
            revealed_clue = None
            msg = (
                f"CONTRADICTED: Calling {cell.character_name} ({cid}) {verdict.name} "
                f"contradicts the truth. Card remains hidden."
            )
            self._append_trace("error", msg, cell_id=cid, verdict="CONTRADICTED")
        else:
            revealed_clue = None
            msg = f"INCONSISTENT: Knowledge base contradiction detected at {cid}."
            self._append_trace("error", msg, cell_id=cid, verdict=outcome.name)

        return {
            "status": "ok",
            "result": outcome.name,
            "cell_id": cid,
            "verdict": verdict.name,
            "revealed_clue": revealed_clue,
            "message": msg,
            "is_solved": engine.is_solved(),
            "board": self.board_view.get_public_board_state(self.highlighted_cells),
            "trace": list(self.trace_log),
        }

    def get_hint(self) -> Dict[str, Any]:
        """Query the HintProvider for one forced character and relevant clue."""
        engine = self._require_engine()
        assert self.board_view is not None

        if engine.is_solved():
            return {
                "status": "ok",
                "hint": None,
                "message": "Puzzle is already solved!",
                "board": self.board_view.get_public_board_state(self.highlighted_cells),
            }

        kb = engine.build_public_kb()
        unresolved_cells = [
            cell
            for cell in engine.puzzle.grid.get_all_cells()
            if cell.cell_id not in engine.verdicts
        ]
        active_clues = [clue for _, clue in engine.get_revealed_clues()]

        hint_tuple: Optional[Tuple[str, Verdict, Optional[str]]] = None
        used_provider = False
        try:
            hint_tuple = self.hinter.get_hint(kb, unresolved_cells, active_clues)
            used_provider = True
        except NotImplementedError:
            used_provider = False

        if not used_provider:
            forced = self._find_first_forced_cell(engine)
            if forced is not None:
                cid, entailed = forced
                _, clue_desc, _ = self._find_supporting_clue(engine, cid)
                hint_tuple = (cid, entailed, clue_desc)

        if hint_tuple is None:
            msg = "No character is currently logically forced from the revealed clues (deadlock / ambiguous state)."
            self._append_trace("warning", f"💡 Hint: {msg}")
            return {
                "status": "ok",
                "hint": None,
                "message": msg,
                "board": self.board_view.get_public_board_state(self.highlighted_cells),
                "trace": list(self.trace_log),
            }

        target_cid, forced_verdict, explanation = hint_tuple
        target_cell = engine.puzzle.grid.get_cell_by_id(target_cid)
        clue_cell_id, fallback_clue_desc, highlight_set = self._find_supporting_clue(
            engine, target_cid
        )
        clue_desc = explanation or fallback_clue_desc

        self.highlighted_cells = set(highlight_set)
        self.highlight_source = clue_cell_id

        char_name = target_cell.character_name if target_cell else target_cid
        msg = f"💡 Hint: {char_name} ({target_cid}) can be proven {forced_verdict.name}."
        if clue_desc:
            msg += f' Relevant clue ({clue_cell_id}): "{clue_desc}"'
        self._append_trace("hint", msg, cell_id=target_cid, verdict=forced_verdict.name, clue_text=clue_desc)

        return {
            "status": "ok",
            "hint": {
                "cell_id": target_cid,
                "character_name": char_name,
                "verdict": forced_verdict.name,
                "clue_cell_id": clue_cell_id,
                "clue_text": clue_desc,
                "highlight_cells": sorted(highlight_set),
            },
            "message": msg,
            "board": self.board_view.get_public_board_state(self.highlighted_cells),
            "trace": list(self.trace_log),
        }

    def auto_solve_step(self) -> Dict[str, Any]:
        """Execute one step of the automated no-guess solver."""
        engine = self._require_engine()
        assert self.board_view is not None

        if engine.is_solved():
            return {
                "status": "ok",
                "done": True,
                "deadlock": False,
                "step": None,
                "message": "Puzzle is already solved!",
                "board": self.board_view.get_public_board_state(self.highlighted_cells),
                "trace": list(self.trace_log),
            }

        kb = engine.build_public_kb()
        agent_step = None
        used_agent = False
        try:
            agent_step = self.agent.step(engine, kb)
            used_agent = True
        except NotImplementedError:
            used_agent = False

        if used_agent:
            if agent_step is None:
                msg = "Deadlock: no unresolved character can be deduced without guessing."
                self._append_trace("warning", msg)
                return {
                    "status": "ok",
                    "done": False,
                    "deadlock": True,
                    "step": None,
                    "message": msg,
                    "board": self.board_view.get_public_board_state(self.highlighted_cells),
                    "trace": list(self.trace_log),
                }
            self._step_counter += 1
            step_data = agent_step.to_dict()
            cid = step_data["cell"]
            verdict_name = step_data["verdict"]
            clue_text = step_data.get("revealed_clue")
            msg = (
                f"[Step {self._step_counter}] Auto-deduced {step_data['name']} ({cid}) = "
                f"{verdict_name}."
            )
            if clue_text:
                msg += f' Revealed clue: "{clue_text}"'
            self._append_trace(
                "auto", msg, cell_id=cid, verdict=verdict_name, clue_text=clue_text
            )
            if engine.is_solved():
                self._append_trace("solved", "🎉 Puzzle solved completely with zero guessing!")
            return {
                "status": "ok",
                "done": engine.is_solved(),
                "deadlock": False,
                "step": step_data,
                "message": msg,
                "board": self.board_view.get_public_board_state(self.highlighted_cells),
                "trace": list(self.trace_log),
            }

        # Fallback: pure public-KB entailment deduction (strictly no guessing)
        forced = self._find_first_forced_cell(engine)
        if forced is None:
            msg = "Deadlock: no unresolved character is logically forced from revealed clues (stopped without guessing)."
            self._append_trace("warning", msg)
            return {
                "status": "ok",
                "done": False,
                "deadlock": True,
                "step": None,
                "message": msg,
                "board": self.board_view.get_public_board_state(self.highlighted_cells),
                "trace": list(self.trace_log),
            }

        cid, entailed = forced
        outcome = engine.submit_verdict(cid, entailed)
        if outcome != Verdict.ACCEPTED:
            msg = f"Engine rejected deduced verdict {entailed.name} for {cid}: {outcome.name}."
            self._append_trace("error", msg, cell_id=cid, verdict=outcome.name)
            return {
                "status": "ok",
                "done": False,
                "deadlock": True,
                "step": None,
                "message": msg,
                "board": self.board_view.get_public_board_state(self.highlighted_cells),
                "trace": list(self.trace_log),
            }

        self._step_counter += 1
        cell = engine.puzzle.grid.get_cell_by_id(cid)
        char_name = cell.character_name if cell else cid
        revealed_clue = cell.clue.description if (cell and cell.clue) else None

        msg = f"[Step {self._step_counter}] Auto-deduced {char_name} ({cid}) = {entailed.name}."
        if revealed_clue:
            msg += f' Revealed clue: "{revealed_clue}"'
        self._append_trace(
            "auto", msg, cell_id=cid, verdict=entailed.name, clue_text=revealed_clue
        )
        if engine.is_solved():
            self._append_trace("solved", "🎉 Puzzle solved completely with zero guessing!")

        step_payload = {
            "step": self._step_counter,
            "cell": cid,
            "name": char_name,
            "verdict": entailed.name,
            "revealed_clue": revealed_clue,
        }
        return {
            "status": "ok",
            "done": engine.is_solved(),
            "deadlock": False,
            "step": step_payload,
            "message": msg,
            "board": self.board_view.get_public_board_state(self.highlighted_cells),
            "trace": list(self.trace_log),
        }

    def auto_solve_all(self) -> Dict[str, Any]:
        """Run the automated solver until completion or deadlock."""
        engine = self._require_engine()
        assert self.board_view is not None

        steps: List[Dict[str, Any]] = []
        deadlock = False

        max_iters = len(engine.puzzle.solution) + 1
        for _ in range(max_iters):
            if engine.is_solved():
                break
            res = self.auto_solve_step()
            if res.get("step") is not None:
                steps.append(res["step"])
            if res.get("deadlock"):
                deadlock = True
                break

        solved = engine.is_solved()
        if solved:
            msg = f"Auto-solve complete! Solved in {len(steps)} deductive step(s) with zero guessing."
        elif deadlock:
            remaining = len(engine.get_unresolved_cells())
            msg = (
                f"Auto-solve stopped after {len(steps)} step(s): "
                f"{remaining} character(s) cannot be deduced without guessing (deadlock)."
            )
        else:
            msg = f"Auto-solve finished ({len(steps)} step(s))."

        return {
            "status": "ok",
            "solved": solved,
            "deadlock": deadlock,
            "steps": steps,
            "message": msg,
            "board": self.board_view.get_public_board_state(self.highlighted_cells),
            "trace": list(self.trace_log),
        }

    def highlight_clue(self, cell_id: Optional[str]) -> Dict[str, Any]:
        """Compute and activate highlighted cells for the revealed clue at *cell_id*.

        Passing ``None`` or an empty string clears the current highlight.
        """
        engine = self._require_engine()
        assert self.board_view is not None

        if not cell_id:
            self.highlighted_cells = set()
            self.highlight_source = None
            return {
                "status": "ok",
                "source_cell": None,
                "cells": [],
                "clue_text": None,
                "board": self.board_view.get_public_board_state(),
            }

        cid = str(cell_id).strip().upper()
        if cid not in engine.revealed_cells:
            raise ValueError(f"Cell {cid} is not revealed; hidden clues cannot be highlighted.")

        cell = engine.puzzle.grid.get_cell_by_id(cid)
        if cell is None or cell.clue is None:
            self.highlighted_cells = set()
            self.highlight_source = None
            return {
                "status": "ok",
                "source_cell": cid,
                "cells": [],
                "clue_text": None,
                "board": self.board_view.get_public_board_state(),
            }

        referenced = ClueHighlighter.get_referenced_cells(cell.clue, engine.puzzle.grid)
        self.highlighted_cells = set(referenced)
        self.highlight_source = cid

        return {
            "status": "ok",
            "source_cell": cid,
            "cells": sorted(referenced),
            "clue_text": cell.clue.description,
            "board": self.board_view.get_public_board_state(self.highlighted_cells),
        }
