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

_PROFESSION_AVATARS: Dict[str, str] = {
    "detective": "🕵️",
    "doctor": "🩺",
    "guard": "🛡️",
    "lawyer": "⚖️",
    "scientist": "🔬",
    "teacher": "📚",
    "architect": "📐",
    "chef": "👨‍🍳",
    "cook": "🍳",
    "journalist": "📰",
    "reporter": "🎙️",
    "judge": "👨‍⚖️",
    "engineer": "⚙️",
    "pilot": "✈️",
    "mechanic": "🔧",
    "baker": "🥐",
    "surgeon": "🏥",
    "captain": "⚓",
    "florist": "💐",
    "clerk": "📋",
    "farmer": "🌾",
    "painter": "🎨",
    "astronaut": "🚀",
    "nurse": "💉",
    "artist": "🎭",
    "driver": "🚗",
    "singer": "🎤",
    "poet": "🪶",
    "author": "📖",
    "writer": "✍️",
    "tailor": "🧵",
    "actor": "🎬",
    "mason": "🧱",
    "miner": "⛏️",
    "spy": "🕶️",
}


def get_profession_avatar(profession: str) -> str:
    """Return a thematic avatar icon for *profession*."""
    return _PROFESSION_AVATARS.get(profession.strip().lower(), "👤")


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
            * ``cells``: list of cell objects in row-major order with:
                - ``id``: "A1"
                - ``row``: 1
                - ``col``: "A"
                - ``name``: character name
                - ``profession``: character profession
                - ``avatar``: profession emoji/avatar
                - ``is_revealed``: bool
                - ``status``: CRIMINAL / INNOCENT / None
                - ``clue_text``: Natural-language text if revealed, else None
                - ``clue_type``: Clue type tag if revealed, else None
                - ``is_highlighted``: bool
            * ``verdicts``: dict of proven verdicts
            * ``resolved_count``: number of resolved characters
            * ``total_cells``: total grid cells
            * ``is_solved``: bool
        """
        public = self.engine.get_public_state()
        highlighted = {cid.strip().upper() for cid in (highlighted_cells or set())}

        formatted_cells: List[Dict[str, Any]] = []
        for cell in public["cells"]:
            cid = cell["id"]
            is_rev = bool(cell["is_revealed"])
            clue_obj = cell.get("clue") if is_rev else None
            formatted_cells.append(
                {
                    "id": cid,
                    "row": cell["row"],
                    "col": cell["col"],
                    "name": cell["name"],
                    "profession": cell["profession"],
                    "avatar": get_profession_avatar(cell["profession"]),
                    "is_revealed": is_rev,
                    "status": cell["status"] if is_rev else None,
                    "clue_text": cell["clue_text"] if is_rev else None,
                    "clue_type": clue_obj.get("type") if isinstance(clue_obj, dict) else None,
                    "is_highlighted": cid in highlighted,
                }
            )

        return {
            "size": public["grid_size"],
            "columns": public["columns"],
            "rows": public["rows"],
            "cells": formatted_cells,
            "verdicts": public["verdicts"],
            "resolved_count": len(public["verdicts"]),
            "total_cells": len(formatted_cells),
            "is_solved": public["is_solved"],
        }
