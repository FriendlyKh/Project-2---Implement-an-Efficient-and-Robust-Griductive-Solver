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

from dataclasses import dataclass, field
from typing import Optional

# Forward reference — avoids circular import at runtime.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.clue import Clue


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
        # TODO: Implement reveal logic — set is_revealed and make clue visible
        raise NotImplementedError("TODO: Implement Cell.reveal()")

    def set_verdict(self, verdict: str) -> None:
        """Set the cell's status to *verdict* (``'CRIMINAL'`` or ``'INNOCENT'``).

        Args:
            verdict: One of ``'CRIMINAL'`` or ``'INNOCENT'``.

        Raises:
            ValueError: If *verdict* is not a valid status string.
        """
        # TODO: Validate and set self.status
        raise NotImplementedError("TODO: Implement Cell.set_verdict()")

    def to_dict(self) -> dict:
        """Serialize the cell to a JSON-compatible dictionary."""
        # TODO: Implement serialization
        raise NotImplementedError("TODO: Implement Cell.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "Cell":
        """Deserialize a cell from a dictionary.

        Args:
            data: Dictionary with keys matching Cell fields.

        Returns:
            A new :class:`Cell` instance.
        """
        # TODO: Implement deserialization
        raise NotImplementedError("TODO: Implement Cell.from_dict()")

    def __repr__(self) -> str:
        status_str = self.status or "?"
        return (
            f"Cell({self.cell_id}, {self.character_name!r}, "
            f"status={status_str}, revealed={self.is_revealed})"
        )
