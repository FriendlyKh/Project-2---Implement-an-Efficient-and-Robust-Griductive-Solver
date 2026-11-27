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

from models.clue import (
    AtLeastClue,
    AtMostClue,
    Clue,
    CompareClue,
    DifferentClue,
    ExactlyClue,
    FactClue,
    Region,
    SameClue,
)
from models.puzzle import Puzzle

_CELL_ID_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _validate_region(region: Region, size: int, seen_cells: set[str]) -> int:
    """Validate *region* against grid bounds and return the number of cells in it."""
    rtype = region.region_type.strip().lower()
    valid_cols = {chr(ord("A") + i) for i in range(size)}

    if rtype == "row":
        if region.value is None or not isinstance(region.value, int) or isinstance(region.value, bool):
            raise ValueError(f"Row region requires an integer row number, got {region.value!r}")
        if region.value < 1 or region.value > size:
            raise ValueError(f"Row {region.value} out of bounds for {size}×{size} grid")
        return size

    if rtype in ("column", "col"):
        col = str(region.value).strip().upper() if region.value is not None else ""
        if col not in valid_cols:
            raise ValueError(f"Column {region.value!r} out of bounds for {size}×{size} grid")
        return size

    if rtype == "cells":
        if not isinstance(region.value, list) or not region.value:
            raise ValueError("Explicit 'cells' region requires a non-empty list of cell IDs")
        unique_ids = set()
        for raw_id in region.value:
            cid = str(raw_id).strip().upper()
            if cid not in seen_cells:
                raise ValueError(f"Region references unknown cell {raw_id!r}")
            unique_ids.add(cid)
        return len(unique_ids)

    if rtype in ("neighbors", "neighbours"):
        if not isinstance(region.value, str):
            raise ValueError("Neighbors region requires a center cell ID string")
        center = region.value.strip().upper()
        if center not in seen_cells:
            raise ValueError(f"Neighbors center cell {region.value!r} not in grid")
        match = _CELL_ID_RE.match(center)
        assert match is not None
        col_idx = ord(match.group(1)) - ord("A")
        row = int(match.group(2))
        return sum(
            1
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if not (dr == 0 and dc == 0)
            and 1 <= row + dr <= size
            and 0 <= col_idx + dc < size
        )

    if rtype == "all":
        return size * size

    raise ValueError(f"Unknown region type: {region.region_type!r}")


def _validate_clue(clue: Clue, size: int, seen_cells: set[str]) -> None:
    """Validate clue referenced cells, regions, and counting bounds (0 <= k <= |R|)."""
    if isinstance(clue, FactClue):
        if clue.target_cell not in seen_cells:
            raise ValueError(f"FactClue target_cell {clue.target_cell!r} not in grid")
    elif isinstance(clue, (SameClue, DifferentClue)):
        for cid in (clue.cell_a, clue.cell_b):
            if cid not in seen_cells:
                raise ValueError(f"{clue.clue_type} clue references unknown cell {cid!r}")
    elif isinstance(clue, CompareClue):
        _validate_region(clue.region, size, seen_cells)
        if clue.region_b is None:
            raise ValueError("CompareClue requires 'region_b'")
        _validate_region(clue.region_b, size, seen_cells)
    elif isinstance(clue, (ExactlyClue, AtLeastClue, AtMostClue)):
        region_size = _validate_region(clue.region, size, seen_cells)
        if clue.k < 0 or clue.k > region_size:
            raise ValueError(
                f"{clue.clue_type} clue parameter k={clue.k} out of range [0, {region_size}]"
            )
    else:
        _validate_region(clue.region, size, seen_cells)


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
        * Clue parameters and referenced regions are valid for the grid.
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
        parsed_clues: List[Clue] = []
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
                parsed_clues.append(Clue.from_dict(char["clue"]))

        for clue in parsed_clues:
            _validate_clue(clue, size, seen_cells)

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
