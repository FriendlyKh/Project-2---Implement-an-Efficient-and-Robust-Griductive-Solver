# Owner: Person 1
"""
models.cell — Cell Data Model
==============================

Represents a single cell on the N×N puzzle grid.  Each cell contains a
character who is either a CRIMINAL or INNOCENT (hidden from the solver
until revealed).  Cells may carry a clue that the character provides once
their card is flipped.

Example cell IDs: ``"A1"``, ``"B3"``, ``"C2"`` (column letter + row number).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.clue import Clue

VALID_STATUSES = ("CRIMINAL", "INNOCENT")
_CELL_ID_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


@dataclass
class Cell:
    """A single cell on the puzzle grid.

    Attributes:
        row: 1-based row index (e.g. 1, 2, 3).
        col: Column letter (e.g. ``'A'``, ``'B'``, ``'C'``).
        character_name: Display name of the character in this cell.
        profession: Thematic profession/role of the character.
        status: ``'CRIMINAL'``, ``'INNOCENT'``, or ``None`` if not yet
            determined by the solver.
        clue: The :class:`Clue` this character carries (may be ``None``
            if the character has no clue or the clue is not yet revealed).
        is_revealed: Whether the cell's card has been flipped (clue visible).
    """

    row: int
    col: str
    character_name: str
    profession: str
    status: Optional[str] = None
    clue: Optional["Clue"] = None
    is_revealed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.row, int) or isinstance(self.row, bool) or self.row < 1:
            raise ValueError(f"Row must be a positive integer, got {self.row!r}")
        if not isinstance(self.col, str) or not self.col.strip().isalpha():
            raise ValueError(f"Column must be an alphabetic string, got {self.col!r}")
        self.col = self.col.strip().upper()
        if self.status is not None and self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid cell status {self.status!r}; expected one of {VALID_STATUSES} or None"
            )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def cell_id(self) -> str:
        """Return the canonical cell identifier, e.g. ``'A1'``, ``'B2'``.

        The format is **column letter** followed by **row number**.
        """
        return f"{self.col}{self.row}"

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def reveal(self) -> None:
        """Mark the cell as revealed (card flipped)."""
        self.is_revealed = True

    def set_verdict(self, verdict: str) -> None:
        """Set the cell's status to *verdict* (``'CRIMINAL'`` or ``'INNOCENT'``).

        Args:
            verdict: One of ``'CRIMINAL'`` or ``'INNOCENT'``.

        Raises:
            ValueError: If *verdict* is not a valid status string.
        """
        if verdict not in VALID_STATUSES:
            raise ValueError(
                f"Invalid verdict {verdict!r}; must be one of {VALID_STATUSES}"
            )
        self.status = verdict

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the cell to a JSON-compatible dictionary."""
        return {
            "cell": self.cell_id,
            "row": self.row,
            "col": self.col,
            "character_name": self.character_name,
            "profession": self.profession,
            "status": self.status,
            "clue": self.clue.to_dict() if self.clue is not None else None,
            "is_revealed": self.is_revealed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cell":
        """Deserialize a cell from a dictionary.

        Supports both full ``Cell.to_dict()`` dictionaries (``row``, ``col``,
        ``character_name``) and puzzle JSON character entries (``cell``, ``name``).

        Args:
            data: Dictionary with keys matching Cell fields.

        Returns:
            A new :class:`Cell` instance.
        """
        from models.clue import Clue

        if not isinstance(data, dict):
            raise ValueError("Cell data must be a dictionary")

        if "row" in data and "col" in data:
            row = int(data["row"])
            col = str(data["col"]).strip().upper()
        elif "cell" in data:
            match = _CELL_ID_RE.match(str(data["cell"]).strip())
            if not match:
                raise ValueError(f"Invalid cell identifier: {data['cell']!r}")
            col = match.group(1).upper()
            row = int(match.group(2))
        else:
            raise ValueError("Cell data must include either ('row', 'col') or 'cell'")

        if "character_name" in data:
            character_name = str(data["character_name"])
        elif "name" in data:
            character_name = str(data["name"])
        else:
            raise ValueError("Cell data must include 'character_name' or 'name'")

        profession = str(data.get("profession", ""))
        status = data.get("status")
        if isinstance(status, str):
            status = status.strip().upper()

        raw_clue = data.get("clue")
        if raw_clue is None:
            clue = None
        elif isinstance(raw_clue, Clue):
            clue = raw_clue
        elif isinstance(raw_clue, dict):
            clue = Clue.from_dict(raw_clue)
        else:
            raise ValueError(f"Invalid clue field in cell data: {raw_clue!r}")

        is_revealed = bool(data.get("is_revealed", False))

        return cls(
            row=row,
            col=col,
            character_name=character_name,
            profession=profession,
            status=status,
            clue=clue,
            is_revealed=is_revealed,
        )

    def __repr__(self) -> str:
        status_str = self.status or "?"
        return (
            f"Cell({self.cell_id}, {self.character_name!r}, "
            f"status={status_str}, revealed={self.is_revealed})"
        )
