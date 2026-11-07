# Owner: Person 1
"""
models.clue — Clue Class Hierarchy
====================================

Each character on the grid carries a **clue** — a propositional-logic
statement about the number or identity of criminals in some *region* of
the grid.

Clue types
----------
* **FACT**      — Directly states whether a specific character is criminal or innocent.
* **SAME**      — Two specific characters share the same status.
* **DIFFERENT** — Two specific characters have different statuses.
* **EXACTLY**   — Exactly *k* criminals in a region.
* **AT_LEAST**  — At least *k* criminals in a region.
* **AT_MOST**   — At most *k* criminals in a region.

Extension clue types
--------------------
* **PARITY**    — The number of criminals in a region is odd or even.
* **COMPARE**   — Compares criminal counts between two regions (e.g. region A
  has more criminals than region B).

All clue objects support ``to_dict()`` / ``from_dict()`` for JSON round-tripping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


# =========================================================================
# Region specification helper
# =========================================================================

@dataclass
class Region:
    """Specification for a region of the grid.

    A region can be:
    * ``{"type": "row",    "value": 1}``     → all cells in row 1
    * ``{"type": "column", "value": "A"}``   → all cells in column A
    * ``{"type": "cells",  "value": ["A1","B2"]}`` → explicit list of cell IDs
    * ``{"type": "all"}``                    → the entire grid

    Attributes:
        region_type: One of ``'row'``, ``'column'``, ``'cells'``, ``'all'``.
        value: The row number, column letter, list of cell IDs, or ``None``.
    """

    region_type: str
    value: Optional[Union[int, str, List[str]]] = None

    def to_dict(self) -> dict:
        d: Dict[str, Any] = {"type": self.region_type}
        if self.value is not None:
            d["value"] = self.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        return cls(region_type=data["type"], value=data.get("value"))

    def __repr__(self) -> str:
        if self.value is not None:
            return f"Region({self.region_type}, {self.value})"
        return f"Region({self.region_type})"


# =========================================================================
# Base Clue
# =========================================================================

@dataclass
class Clue:
    """Abstract base class for all clue types.

    Attributes:
        clue_type: String tag identifying the concrete clue type.
        region: The :class:`Region` this clue refers to.
        description: Human-readable text describing the clue.
    """

    clue_type: str
    region: Region
    description: str = ""

    def to_dict(self) -> dict:
        """Serialize the clue to a JSON-compatible dictionary."""
        # TODO: Implement base serialization; subclasses should call super().to_dict()
        raise NotImplementedError("TODO: Implement Clue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "Clue":
        """Factory: dispatch to the correct subclass based on ``data['type']``.

        Args:
            data: Dictionary with at least a ``'type'`` key.

        Returns:
            An instance of the appropriate :class:`Clue` subclass.
        """
        # TODO: Implement dispatch logic using _CLUE_REGISTRY
        raise NotImplementedError("TODO: Implement Clue.from_dict() dispatch")


# =========================================================================
# Concrete clue subclasses
# =========================================================================

@dataclass
class FactClue(Clue):
    """Directly states whether a specific character is CRIMINAL or INNOCENT.

    Attributes:
        target_cell: Cell ID of the character this fact is about (e.g. ``'B2'``).
        is_criminal: ``True`` if the fact asserts CRIMINAL, ``False`` for INNOCENT.
    """

    target_cell: str = ""
    is_criminal: bool = True

    def __post_init__(self) -> None:
        self.clue_type = "FACT"

    def to_dict(self) -> dict:
        # TODO: Implement FactClue serialization
        raise NotImplementedError("TODO: Implement FactClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "FactClue":
        # TODO: Implement FactClue deserialization
        raise NotImplementedError("TODO: Implement FactClue.from_dict()")


@dataclass
class SameClue(Clue):
    """Asserts that two characters share the same status.

    Attributes:
        cell_a: Cell ID of the first character.
        cell_b: Cell ID of the second character.
    """

    cell_a: str = ""
    cell_b: str = ""

    def __post_init__(self) -> None:
        self.clue_type = "SAME"

    def to_dict(self) -> dict:
        # TODO: Implement SameClue serialization
        raise NotImplementedError("TODO: Implement SameClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "SameClue":
        # TODO: Implement SameClue deserialization
        raise NotImplementedError("TODO: Implement SameClue.from_dict()")


@dataclass
class DifferentClue(Clue):
    """Asserts that two characters have different statuses.

    Attributes:
        cell_a: Cell ID of the first character.
        cell_b: Cell ID of the second character.
    """

    cell_a: str = ""
    cell_b: str = ""

    def __post_init__(self) -> None:
        self.clue_type = "DIFFERENT"

    def to_dict(self) -> dict:
        # TODO: Implement DifferentClue serialization
        raise NotImplementedError("TODO: Implement DifferentClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "DifferentClue":
        # TODO: Implement DifferentClue deserialization
        raise NotImplementedError("TODO: Implement DifferentClue.from_dict()")


@dataclass
class ExactlyClue(Clue):
    """Asserts that exactly *k* characters in the region are criminals.

    Attributes:
        k: The exact number of criminals required.
    """

    k: int = 0

    def __post_init__(self) -> None:
        self.clue_type = "EXACTLY"

    def to_dict(self) -> dict:
        # TODO: Implement ExactlyClue serialization
        raise NotImplementedError("TODO: Implement ExactlyClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "ExactlyClue":
        # TODO: Implement ExactlyClue deserialization
        raise NotImplementedError("TODO: Implement ExactlyClue.from_dict()")


@dataclass
class AtLeastClue(Clue):
    """Asserts that at least *k* characters in the region are criminals.

    Attributes:
        k: The minimum number of criminals.
    """

    k: int = 0

    def __post_init__(self) -> None:
        self.clue_type = "AT_LEAST"

    def to_dict(self) -> dict:
        # TODO: Implement AtLeastClue serialization
        raise NotImplementedError("TODO: Implement AtLeastClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "AtLeastClue":
        # TODO: Implement AtLeastClue deserialization
        raise NotImplementedError("TODO: Implement AtLeastClue.from_dict()")


@dataclass
class AtMostClue(Clue):
    """Asserts that at most *k* characters in the region are criminals.

    Attributes:
        k: The maximum number of criminals.
    """

    k: int = 0

    def __post_init__(self) -> None:
        self.clue_type = "AT_MOST"

    def to_dict(self) -> dict:
        # TODO: Implement AtMostClue serialization
        raise NotImplementedError("TODO: Implement AtMostClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "AtMostClue":
        # TODO: Implement AtMostClue deserialization
        raise NotImplementedError("TODO: Implement AtMostClue.from_dict()")


# =========================================================================
# Extension clue types
# =========================================================================

@dataclass
class ParityClue(Clue):
    """Asserts that the number of criminals in the region has a given parity.

    This is an **extension** clue type.

    Attributes:
        parity: ``'odd'`` or ``'even'``.
    """

    parity: str = "even"  # 'odd' or 'even'

    def __post_init__(self) -> None:
        self.clue_type = "PARITY"

    def to_dict(self) -> dict:
        # TODO: Implement ParityClue serialization
        raise NotImplementedError("TODO: Implement ParityClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "ParityClue":
        # TODO: Implement ParityClue deserialization
        raise NotImplementedError("TODO: Implement ParityClue.from_dict()")


@dataclass
class CompareClue(Clue):
    """Compares the number of criminals between two regions.

    This is an **extension** clue type.

    Attributes:
        region_b: The second region to compare against ``self.region``.
        operator: Comparison operator — one of ``'>'``, ``'<'``, ``'>='``,
            ``'<='``, ``'=='``, ``'!='``.
    """

    region_b: Optional[Region] = None
    operator: str = ">"  # '>', '<', '>=', '<=', '==', '!='

    def __post_init__(self) -> None:
        self.clue_type = "COMPARE"

    def to_dict(self) -> dict:
        # TODO: Implement CompareClue serialization
        raise NotImplementedError("TODO: Implement CompareClue.to_dict()")

    @classmethod
    def from_dict(cls, data: dict) -> "CompareClue":
        # TODO: Implement CompareClue deserialization
        raise NotImplementedError("TODO: Implement CompareClue.from_dict()")


# =========================================================================
# Registry for from_dict dispatch
# =========================================================================

_CLUE_REGISTRY: Dict[str, type] = {
    "FACT": FactClue,
    "SAME": SameClue,
    "DIFFERENT": DifferentClue,
    "EXACTLY": ExactlyClue,
    "AT_LEAST": AtLeastClue,
    "AT_MOST": AtMostClue,
    "PARITY": ParityClue,
    "COMPARE": CompareClue,
}
