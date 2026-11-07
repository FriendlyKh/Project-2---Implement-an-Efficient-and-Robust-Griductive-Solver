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

from typing import Any, Dict, Optional

from agent.hint import HintProvider
from agent.logic_agent import LogicAgent
from engine.game_engine import GameEngine
from engine.puzzle_loader import load_puzzle
from engine.verdict import Verdict


class GameController:
    """Coordinates player UI actions with the GameEngine and LogicAgent."""

    def __init__(self, engine: Optional[GameEngine] = None) -> None:
        """Initialise controller."""
        self.engine = engine
        self.agent = LogicAgent()
        self.hinter = HintProvider()
        self.current_puzzle_path: Optional[str] = None

    def load_puzzle(self, filepath: str) -> Dict[str, Any]:
        """Load a new puzzle from disk and reset the game state.

        Args:
            filepath: Path to the puzzle JSON file.

        Returns:
            Dictionary with load status and initial board state.
        """
        # TODO: Implement puzzle loading and GameEngine initialisation
        raise NotImplementedError("TODO: Implement GameController.load_puzzle()")

    def restart(self) -> Dict[str, Any]:
        """Reset the current puzzle back to its initial state."""
        # TODO: Implement restart
        raise NotImplementedError("TODO: Implement GameController.restart()")

    def submit_verdict(self, cell_id: str, verdict_str: str) -> Dict[str, Any]:
        """Handle a user's manual verdict call on a cell.

        Must validate using the LogicAgent/EntailmentChecker:
        - If logically forced and matches truth: ACCEPTED
        - If neither verdict is forced: NOT_PROVABLE
        - If opposite verdict is forced: CONTRADICTED

        Args:
            cell_id: Cell identifier (e.g. ``'B2'``).
            verdict_str: ``'CRIMINAL'`` or ``'INNOCENT'``.

        Returns:
            Dictionary with result status, feedback message, and updated board state.
        """
        # TODO: Implement manual verdict submission logic
        raise NotImplementedError("TODO: Implement GameController.submit_verdict()")

    def get_hint(self) -> Dict[str, Any]:
        """Query the HintProvider for one forced character and relevant clue."""
        # TODO: Implement hint retrieval
        raise NotImplementedError("TODO: Implement GameController.get_hint()")

    def auto_solve_step(self) -> Dict[str, Any]:
        """Execute one step of the automated solver."""
        # TODO: Implement single auto-solve step
        raise NotImplementedError("TODO: Implement GameController.auto_solve_step()")

    def auto_solve_all(self) -> Dict[str, Any]:
        """Run the automated solver until completion or deadlock."""
        # TODO: Implement full auto-solve
        raise NotImplementedError("TODO: Implement GameController.auto_solve_all()")
