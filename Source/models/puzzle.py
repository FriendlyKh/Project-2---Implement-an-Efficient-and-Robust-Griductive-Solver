# Owner: Person 1
"""
models.puzzle — Puzzle Data Model
===================================

A :class:`Puzzle` bundles the visible :class:`~models.grid.Grid` with the
**hidden solution** (which cells are criminals) and the list of cells that
start face-up (initially revealed).

The hidden solution is a ``dict[str, bool]`` mapping each cell ID to
``True`` (CRIMINAL) or ``False`` (INNOCENT).  The solver never peeks at
the solution directly — it is used only by the
:class:`~engine.game_engine.GameEngine` to validate verdicts and reveal
clues.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from models.cell import Cell
from models.clue import Clue
from models.grid import Grid


class Puzzle:
    """Complete puzzle definition (grid + hidden solution + metadata).

    Attributes:
        grid: The :class:`Grid` containing all character cells.
        solution: Mapping ``cell_id → is_criminal`` (hidden from solver).
        initially_revealed: List of cell IDs whose cards start face-up.
    """

    def __init__(
        self,
        grid: Grid,
        solution: Dict[str, bool],
        initially_revealed: List[str],
    ) -> None:
        self.grid = grid
        self.solution = {k.strip().upper(): bool(v) for k, v in solution.items()}
        self.initially_revealed = [cid.strip().upper() for cid in initially_revealed]

    # ------------------------------------------------------------------
    # Serialisation / Deserialisation
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Puzzle":
        """Construct a :class:`Puzzle` from a validated dictionary.

        Cells on the constructed :class:`Grid` start with ``status=None``
        and ``is_revealed=False`` so that ground-truth statuses remain
        strictly isolated inside ``Puzzle.solution`` until revealed by the
        :class:`~engine.game_engine.GameEngine`.

        Args:
            data: Dictionary conforming to the puzzle JSON schema.

        Returns:
            A fully initialised :class:`Puzzle`.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise ValueError("Puzzle data must be a JSON object")

        for key in ("size", "characters", "initially_revealed"):
            if key not in data:
                raise ValueError(f"Puzzle data missing required field: {key!r}")

        size = data["size"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 1:
            raise ValueError(f"Puzzle 'size' must be a positive integer, got {size!r}")

        characters = data["characters"]
        if not isinstance(characters, list) or len(characters) != size * size:
            raise ValueError(
                f"Puzzle 'characters' must be a list of {size * size} entries"
            )

        grid = Grid(size=size)
        solution: Dict[str, bool] = {}

        for entry in characters:
            if not isinstance(entry, dict):
                raise ValueError("Each character entry must be a dictionary")
            for req in ("cell", "name", "profession", "status", "clue"):
                if req not in entry:
                    raise ValueError(f"Character entry missing required key {req!r}: {entry!r}")

            raw_status = str(entry["status"]).strip().upper()
            if raw_status not in ("CRIMINAL", "INNOCENT"):
                raise ValueError(
                    f"Invalid status {entry['status']!r} for cell {entry['cell']!r}"
                )

            raw_clue = entry.get("clue")
            clue = Clue.from_dict(raw_clue) if raw_clue is not None else None

            # Create Cell without exposing ground-truth status on the Grid
            cell = Cell.from_dict(
                {
                    "cell": entry["cell"],
                    "name": entry["name"],
                    "profession": entry["profession"],
                    "status": None,
                    "clue": clue,
                    "is_revealed": False,
                }
            )
            grid.add_cell(cell)
            solution[cell.cell_id] = raw_status == "CRIMINAL"

        raw_revealed = data["initially_revealed"]
        if not isinstance(raw_revealed, list):
            raise ValueError("Puzzle 'initially_revealed' must be a list of cell IDs")

        initially_revealed: List[str] = []
        for raw_cid in raw_revealed:
            cid = str(raw_cid).strip().upper()
            if cid not in solution:
                raise ValueError(
                    f"Initially revealed cell {raw_cid!r} is not in the puzzle grid"
                )
            if cid not in initially_revealed:
                initially_revealed.append(cid)

        return cls(grid=grid, solution=solution, initially_revealed=initially_revealed)

    @classmethod
    def from_json(cls, filepath: str | Path) -> "Puzzle":
        """Load a puzzle from a JSON file.

        The expected JSON schema is documented in ``README.md``.

        Args:
            filepath: Path to the puzzle ``.json`` file.

        Returns:
            A fully initialised :class:`Puzzle`.

        Raises:
            FileNotFoundError: If *filepath* does not exist.
            ValueError: If the JSON structure is invalid.
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Puzzle file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in puzzle file {path}: {exc}") from exc

        return cls.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the puzzle to a JSON-compatible dictionary."""
        characters: List[Dict[str, Any]] = []
        for cell in self.grid.get_all_cells():
            is_crim = self.solution[cell.cell_id]
            characters.append(
                {
                    "cell": cell.cell_id,
                    "name": cell.character_name,
                    "profession": cell.profession,
                    "status": "CRIMINAL" if is_crim else "INNOCENT",
                    "clue": cell.clue.to_dict() if cell.clue is not None else None,
                }
            )
        return {
            "size": self.grid.size,
            "characters": characters,
            "initially_revealed": list(self.initially_revealed),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_criminals(self) -> List[str]:
        """Return cell IDs of all criminals (from the hidden solution) in row-major order."""
        return [
            cell.cell_id
            for cell in self.grid.get_all_cells()
            if self.solution.get(cell.cell_id, False)
        ]

    def get_innocents(self) -> List[str]:
        """Return cell IDs of all innocents (from the hidden solution) in row-major order."""
        return [
            cell.cell_id
            for cell in self.grid.get_all_cells()
            if not self.solution.get(cell.cell_id, True)
        ]

    def __repr__(self) -> str:
        return (
            f"Puzzle(size={self.grid.size}, "
            f"revealed={len(self.initially_revealed)})"
        )
