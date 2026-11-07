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
from pathlib import Path
from typing import List

from models.puzzle import Puzzle


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
        # TODO: Implement loading
        #   1. Read JSON
        #   2. Validate structure via validate()
        #   3. Delegate to Puzzle.from_json() or build Puzzle directly
        raise NotImplementedError("TODO: Implement PuzzleLoader.load()")

    @staticmethod
    def load_all(directory: str | Path) -> List[Puzzle]:
        """Recursively load all ``.json`` puzzle files under *directory*.

        Args:
            directory: Root directory to scan.

        Returns:
            List of :class:`Puzzle` objects, sorted by filename.
        """
        # TODO: Glob for .json files and load each
        raise NotImplementedError("TODO: Implement PuzzleLoader.load_all()")

    @staticmethod
    def validate(data: dict) -> bool:
        """Validate the raw JSON dictionary against the expected schema.

        Checks:
        * ``'size'`` is a positive integer.
        * ``'characters'`` is a non-empty list with the correct count
          (size × size).
        * Each character has required fields: ``cell``, ``name``,
          ``profession``, ``status``, ``clue``.
        * ``'initially_revealed'`` cell IDs are valid.

        Args:
            data: The parsed JSON dictionary.

        Returns:
            ``True`` if valid.

        Raises:
            ValueError: With a descriptive message if validation fails.
        """
        # TODO: Implement validation checks
        raise NotImplementedError("TODO: Implement PuzzleLoader.validate()")
