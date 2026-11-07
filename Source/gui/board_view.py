# Owner: Person 1
"""
gui.board_view — Grid & Board State Presentation
==================================================

Formats and serializes the current public state of the Griductive board for
rendering in the graphical interface.

Handles:
* Row and column coordinate labels (A..Z, 1..N)
* Visible cards: flipped (revealed status & clue) vs face-down
* Character avatars, display names, and professions
* Cell state highlighting (selected clue, candidate focus)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from engine.game_engine import GameEngine
from models.grid import Grid


class BoardView:
    """Prepares board data structures for frontend display."""

    def __init__(self, engine: GameEngine) -> None:
        """Initialise board view for an active *engine* instance.

        Args:
            engine: The authoritative GameEngine instance.
        """
        self.engine = engine

    def get_public_board_state(
        self, highlighted_cells: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """Generate a complete dictionary representing the public board view.

        CRITICAL: Never leak hidden status or unrevealed clues into this view!

        Args:
            highlighted_cells: Set of cell IDs to mark with a visual highlight
                (e.g. from an active clue).

        Returns:
            Dictionary containing:
            * ``size``: N
            * ``columns``: ['A', 'B', ...]
            * ``rows``: [1, 2, ...]
            * ``cells``: 2D array or list of cell objects with:
                - ``id``: "A1"
                - ``name``: character name
                - ``profession``: character profession
                - ``is_revealed``: bool
                - ``status``: CRIMINAL / INNOCENT / None
                - ``clue_text``: Natural-language text if revealed, else None
                - ``is_highlighted``: bool
        """
        # TODO: Implement public board state serialization
        raise NotImplementedError("TODO: Implement BoardView.get_public_board_state()")
