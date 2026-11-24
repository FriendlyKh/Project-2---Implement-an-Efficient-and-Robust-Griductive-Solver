# Owner: Person 1
"""
engine.puzzle_loader — Puzzle Loader
======================================

Loads and validates puzzle definitions from JSON files.

JSON schema (see ``README.md`` for full specification)::

    {
      "size": 3,
      "characters": [ … ],
      "initially_revealed": ["A1", "C3"]
    }
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from models.clue import Clue
from models.puzzle import Puzzle

_CELL_ID_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


class PuzzleLoader:
    """Loads :class:`~models.puzzle.Puzzle` objects from JSON files.

    This is a stateless utility class; all methods are class-level.
    """

    @staticmethod
    def load(filepath: str | Path) -> Puzzle:
        """Load a single puzzle from *filepath*.

        Args:
            filepath: Path to the ``.json`` puzzle file.

        Returns:
            A fully constructed :class:`Puzzle`.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the JSON is invalid or fails validation.
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Puzzle file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in puzzle file {path}: {exc}") from exc

        PuzzleLoader.validate(data)
        return Puzzle.from_dict(data)

    @staticmethod
    def load_all(directory: str | Path) -> List[Puzzle]:
        """Recursively load all ``.json`` puzzle files under *directory*.

        Args:
            directory: Root directory to scan.

        Returns:
            List of :class:`Puzzle` objects, sorted by relative path / filename.

        Raises:
            FileNotFoundError: If *directory* does not exist.
        """
        root = Path(directory)
        if not root.exists():
            raise FileNotFoundError(f"Puzzle directory not found: {root}")

        json_files = sorted(
            root.rglob("*.json"),
            key=lambda p: str(p.relative_to(root)).replace("\\", "/"),
        )
        return [PuzzleLoader.load(path) for path in json_files]

    @staticmethod
    def validate(data: Dict[str, Any]) -> bool:
        """Validate the raw JSON dictionary against the expected schema.

        Checks:
        * ``'size'`` is a positive integer.
        * ``'characters'`` is a non-empty list with the correct count
          (size × size).
        * Each character has required fields: ``cell``, ``name``,
          ``profession``, ``status``, ``clue``.
        * Cell IDs are unique and within the ``A1 .. N×N`` coordinate range.
        * ``'initially_revealed'`` cell IDs are valid.

        Args:
            data: The parsed JSON dictionary.

        Returns:
            ``True`` if valid.

        Raises:
            ValueError: With a descriptive message if validation fails.
        """
        if not isinstance(data, dict):
            raise ValueError("Puzzle JSON root must be an object/dictionary")

        size = data.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size < 1:
            raise ValueError(f"Puzzle 'size' must be a positive integer, got {size!r}")

        characters = data.get("characters")
        expected_count = size * size
        if not isinstance(characters, list) or len(characters) != expected_count:
            actual = len(characters) if isinstance(characters, list) else type(characters).__name__
            raise ValueError(
                f"Puzzle 'characters' must be a list of {expected_count} entries, got {actual}"
            )

        valid_cols = {chr(ord("A") + i) for i in range(size)}
        seen_cells: set[str] = set()
        required_keys = ("cell", "name", "profession", "status", "clue")

        for idx, char in enumerate(characters):
            if not isinstance(char, dict):
                raise ValueError(f"Character at index {idx} must be a dictionary")
            for key in required_keys:
                if key not in char:
                    raise ValueError(
                        f"Character at index {idx} missing required field {key!r}"
                    )

            raw_cell = str(char["cell"]).strip()
            match = _CELL_ID_RE.match(raw_cell)
            if not match:
                raise ValueError(f"Invalid cell coordinate {char['cell']!r} at index {idx}")
            col, row = match.group(1).upper(), int(match.group(2))
            if col not in valid_cols or row < 1 or row > size:
                raise ValueError(
                    f"Cell coordinate {raw_cell!r} out of bounds for {size}×{size} grid"
                )
            cell_id = f"{col}{row}"
            if cell_id in seen_cells:
                raise ValueError(f"Duplicate cell coordinate {cell_id!r}")
            seen_cells.add(cell_id)

            status = str(char["status"]).strip().upper()
            if status not in ("CRIMINAL", "INNOCENT"):
                raise ValueError(
                    f"Invalid status {char['status']!r} for cell {cell_id}; "
                    "must be 'CRIMINAL' or 'INNOCENT'"
                )

            if char["clue"] is not None:
                Clue.from_dict(char["clue"])

        initially_revealed = data.get("initially_revealed")
        if not isinstance(initially_revealed, list):
            raise ValueError("Puzzle 'initially_revealed' must be a list of cell IDs")

        for raw_cid in initially_revealed:
            cid = str(raw_cid).strip().upper()
            if cid not in seen_cells:
                raise ValueError(
                    f"Initially revealed cell {raw_cid!r} does not exist in puzzle characters"
                )

        return True


def load_puzzle(filepath: str | Path) -> Puzzle:
    """Convenience function wrapping :meth:`PuzzleLoader.load`."""
    return PuzzleLoader.load(filepath)
