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

VALID_COMPARE_OPERATORS = (">", "<", ">=", "<=", "==", "!=")
VALID_PARITIES = ("odd", "even")


# =========================================================================
# Region specification helper
# =========================================================================

@dataclass
class Region:
    """Specification for a region of the grid.

    A region can be:
    * ``{"type": "row",       "value": 1}``            → all cells in row 1
    * ``{"type": "column",    "value": "A"}``          → all cells in column A
    * ``{"type": "cells",     "value": ["A1","B2"]}``  → explicit list of cell IDs
    * ``{"type": "neighbors", "value": "B2"}``         → 8-neighborhood of B2
    * ``{"type": "all"}``                              → the entire grid

    Attributes:
        region_type: One of ``'row'``, ``'column'``, ``'cells'``, ``'neighbors'``, ``'all'``.
        value: The row number, column letter, list of cell IDs, center cell ID, or ``None``.
    """

    region_type: str
    value: Optional[Union[int, str, List[str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"type": self.region_type}
        if self.value is not None:
            d["value"] = list(self.value) if isinstance(self.value, list) else self.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Region":
        if not isinstance(data, dict) or "type" not in data:
            raise ValueError(f"Region dictionary must contain 'type', got {data!r}")
        return cls(region_type=str(data["type"]), value=data.get("value"))

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

    clue_type: str = ""
    region: Region = field(default_factory=lambda: Region("all"))
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the clue to a JSON-compatible dictionary."""
        return {
            "type": self.clue_type,
            "region": self.region.to_dict(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clue":
        """Factory: dispatch to the correct subclass based on ``data['type']``.

        Args:
            data: Dictionary with at least a ``'type'`` key.

        Returns:
            An instance of the appropriate :class:`Clue` subclass.

        Raises:
            ValueError: If ``'type'`` is missing or unknown.
        """
        if not isinstance(data, dict) or "type" not in data:
            raise ValueError(f"Clue dictionary must contain 'type', got {data!r}")
        clue_type = str(data["type"]).strip().upper()
        subclass = _CLUE_REGISTRY.get(clue_type)
        if subclass is None:
            raise ValueError(f"Unknown clue type: {data['type']!r}")
        return subclass.from_dict(data)


def _parse_region(data: Dict[str, Any], default: Optional[Region] = None) -> Region:
    """Helper to parse ``data['region']`` or fall back to *default*."""
    raw = data.get("region")
    if raw is None:
        if default is not None:
            return default
        raise ValueError(f"Clue dictionary missing required 'region': {data!r}")
    if isinstance(raw, Region):
        return raw
    return Region.from_dict(raw)


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
        if self.target_cell:
            self.target_cell = self.target_cell.strip().upper()

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["target_cell"] = self.target_cell
        d["is_criminal"] = self.is_criminal
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactClue":
        if "target_cell" not in data or "is_criminal" not in data:
            raise ValueError(f"FactClue requires 'target_cell' and 'is_criminal': {data!r}")
        target = str(data["target_cell"]).strip().upper()
        region = _parse_region(data, default=Region("cells", [target]))
        return cls(
            clue_type="FACT",
            region=region,
            description=str(data.get("description", "")),
            target_cell=target,
            is_criminal=bool(data["is_criminal"]),
        )


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
        if self.cell_a:
            self.cell_a = self.cell_a.strip().upper()
        if self.cell_b:
            self.cell_b = self.cell_b.strip().upper()

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["cell_a"] = self.cell_a
        d["cell_b"] = self.cell_b
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SameClue":
        if "cell_a" not in data or "cell_b" not in data:
            raise ValueError(f"SameClue requires 'cell_a' and 'cell_b': {data!r}")
        cell_a = str(data["cell_a"]).strip().upper()
        cell_b = str(data["cell_b"]).strip().upper()
        region = _parse_region(data, default=Region("cells", [cell_a, cell_b]))
        return cls(
            clue_type="SAME",
            region=region,
            description=str(data.get("description", "")),
            cell_a=cell_a,
            cell_b=cell_b,
        )


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
        if self.cell_a:
            self.cell_a = self.cell_a.strip().upper()
        if self.cell_b:
            self.cell_b = self.cell_b.strip().upper()

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["cell_a"] = self.cell_a
        d["cell_b"] = self.cell_b
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DifferentClue":
        if "cell_a" not in data or "cell_b" not in data:
            raise ValueError(f"DifferentClue requires 'cell_a' and 'cell_b': {data!r}")
        cell_a = str(data["cell_a"]).strip().upper()
        cell_b = str(data["cell_b"]).strip().upper()
        region = _parse_region(data, default=Region("cells", [cell_a, cell_b]))
        return cls(
            clue_type="DIFFERENT",
            region=region,
            description=str(data.get("description", "")),
            cell_a=cell_a,
            cell_b=cell_b,
        )


@dataclass
class ExactlyClue(Clue):
    """Asserts that exactly *k* characters in the region are criminals.

    Attributes:
        k: The exact number of criminals required.
    """

    k: int = 0

    def __post_init__(self) -> None:
        self.clue_type = "EXACTLY"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["k"] = self.k
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExactlyClue":
        if "k" not in data:
            raise ValueError(f"ExactlyClue requires 'k': {data!r}")
        return cls(
            clue_type="EXACTLY",
            region=_parse_region(data),
            description=str(data.get("description", "")),
            k=int(data["k"]),
        )


@dataclass
class AtLeastClue(Clue):
    """Asserts that at least *k* characters in the region are criminals.

    Attributes:
        k: The minimum number of criminals.
    """

    k: int = 0

    def __post_init__(self) -> None:
        self.clue_type = "AT_LEAST"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["k"] = self.k
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AtLeastClue":
        if "k" not in data:
            raise ValueError(f"AtLeastClue requires 'k': {data!r}")
        return cls(
            clue_type="AT_LEAST",
            region=_parse_region(data),
            description=str(data.get("description", "")),
            k=int(data["k"]),
        )


@dataclass
class AtMostClue(Clue):
    """Asserts that at most *k* characters in the region are criminals.

    Attributes:
        k: The maximum number of criminals.
    """

    k: int = 0

    def __post_init__(self) -> None:
        self.clue_type = "AT_MOST"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["k"] = self.k
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AtMostClue":
        if "k" not in data:
            raise ValueError(f"AtMostClue requires 'k': {data!r}")
        return cls(
            clue_type="AT_MOST",
            region=_parse_region(data),
            description=str(data.get("description", "")),
            k=int(data["k"]),
        )


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
        self.parity = str(self.parity).strip().lower()
        if self.parity not in VALID_PARITIES:
            raise ValueError(f"Invalid parity {self.parity!r}; must be 'odd' or 'even'")

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["parity"] = self.parity
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParityClue":
        if "parity" not in data:
            raise ValueError(f"ParityClue requires 'parity': {data!r}")
        return cls(
            clue_type="PARITY",
            region=_parse_region(data),
            description=str(data.get("description", "")),
            parity=str(data["parity"]).strip().lower(),
        )


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
        self.operator = str(self.operator).strip()
        if self.operator not in VALID_COMPARE_OPERATORS:
            raise ValueError(
                f"Invalid comparison operator {self.operator!r}; "
                f"must be one of {VALID_COMPARE_OPERATORS}"
            )

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["operator"] = self.operator
        d["region_b"] = self.region_b.to_dict() if self.region_b is not None else None
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompareClue":
        raw_b = data.get("region_b")
        if raw_b is None:
            region_b = None
        elif isinstance(raw_b, Region):
            region_b = raw_b
        else:
            region_b = Region.from_dict(raw_b)
        return cls(
            clue_type="COMPARE",
            region=_parse_region(data),
            description=str(data.get("description", "")),
            region_b=region_b,
            operator=str(data.get("operator", ">")),
        )


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
