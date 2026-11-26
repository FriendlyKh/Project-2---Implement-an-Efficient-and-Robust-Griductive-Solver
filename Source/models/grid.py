# Owner: Person 1
"""
models.grid — Grid / Board Data Model
=======================================

The :class:`Grid` holds an N×N matrix of :class:`~models.cell.Cell` objects
and provides convenience accessors for rows, columns, neighbours, and
arbitrary regions.

Coordinate system
-----------------
* **Columns** are letters: ``A``, ``B``, ``C``, …
* **Rows** are 1-based integers: ``1``, ``2``, ``3``, …
* A cell ID is *column + row*, e.g. ``"B2"``.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from models.cell import Cell
from models.clue import Region

_CELL_ID_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _parse_cell_id(cell_id: str) -> Optional[Tuple[str, int]]:
    """Parse a canonical cell ID (e.g. ``'B2'``) into ``('B', 2)``."""
    if not isinstance(cell_id, str):
        return None
    match = _CELL_ID_RE.match(cell_id.strip())
    if not match:
        return None
    return match.group(1).upper(), int(match.group(2))


class Grid:
    """N×N grid of :class:`Cell` objects.

    Attributes:
        size: Side length of the square grid (e.g. 3 for a 3×3 grid).
        cells: Internal mapping from cell ID (e.g. ``'A1'``) to :class:`Cell`.
    """

    def __init__(self, size: int) -> None:
        """Initialise an empty grid.

        Args:
            size: Side length (must be ≥ 1).

        Raises:
            ValueError: If *size* is not a positive integer.
        """
        if not isinstance(size, int) or isinstance(size, bool) or size < 1:
            raise ValueError(f"Grid size must be a positive integer, got {size!r}")
        self.size: int = size
        self.cells: Dict[str, Cell] = {}

    @property
    def valid_columns(self) -> List[str]:
        """Return valid column letters for this grid (``A`` .. N-th letter)."""
        return [chr(ord("A") + i) for i in range(self.size)]

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def add_cell(self, cell: Cell) -> None:
        """Register *cell* in the grid.

        Args:
            cell: The :class:`Cell` to add.

        Raises:
            ValueError: If the cell coordinates are out of bounds or a cell
                with the same ID already exists.
        """
        col_idx = ord(cell.col) - ord("A") if len(cell.col) == 1 else -1
        if col_idx < 0 or col_idx >= self.size:
            raise ValueError(
                f"Column {cell.col!r} out of bounds for {self.size}×{self.size} grid"
            )
        if cell.row < 1 or cell.row > self.size:
            raise ValueError(
                f"Row {cell.row} out of bounds for {self.size}×{self.size} grid"
            )
        if cell.cell_id in self.cells:
            raise ValueError(f"Duplicate cell ID: {cell.cell_id!r}")
        self.cells[cell.cell_id] = cell

    def get_cell(self, col: str, row: int) -> Optional[Cell]:
        """Return the cell at column *col*, row *row*, or ``None``.

        Args:
            col: Column letter (e.g. ``'A'``).
            row: 1-based row number.
        """
        if not isinstance(col, str) or not col.strip():
            return None
        return self.cells.get(f"{col.strip().upper()}{row}")

    def get_cell_by_id(self, cell_id: str) -> Optional[Cell]:
        """Return the cell with the given *cell_id*, or ``None``.

        Args:
            cell_id: Canonical cell identifier (e.g. ``'B2'``).
        """
        parsed = _parse_cell_id(cell_id)
        if parsed is None:
            return None
        col, row = parsed
        return self.get_cell(col, row)

    # ------------------------------------------------------------------
    # Region queries
    # ------------------------------------------------------------------

    def get_row(self, row_num: int) -> List[Cell]:
        """Return all cells in *row_num* (1-based), ordered by column.

        Args:
            row_num: The row number.
        """
        return sorted(
            (c for c in self.cells.values() if c.row == row_num),
            key=lambda c: c.col,
        )

    def get_column(self, col_letter: str) -> List[Cell]:
        """Return all cells in the given column, ordered by row.

        Args:
            col_letter: The column letter (e.g. ``'A'``).
        """
        target_col = str(col_letter).strip().upper()
        return sorted(
            (c for c in self.cells.values() if c.col == target_col),
            key=lambda c: c.row,
        )

    def get_neighbors(self, col: str, row: int) -> List[Cell]:
        """Return the (up to 8) orthogonal + diagonal neighbours of (*col*, *row*).

        Excludes the center cell itself. Returned in deterministic row-major order.

        Args:
            col: Column letter.
            row: Row number.
        """
        col_norm = str(col).strip().upper()
        if len(col_norm) != 1 or not col_norm.isalpha():
            return []
        col_idx = ord(col_norm) - ord("A")
        neighbors: List[Cell] = []

        for dr in (-1, 0, 1):
            nr = row + dr
            if nr < 1 or nr > self.size:
                continue
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nc = col_idx + dc
                if nc < 0 or nc >= self.size:
                    continue
                cell = self.get_cell(chr(ord("A") + nc), nr)
                if cell is not None:
                    neighbors.append(cell)

        return neighbors


    def get_region(self, region: Region) -> List[Cell]:
        """Resolve a :class:`Region` specification into a list of cells.

        Supports region types: ``'row'``, ``'column'`` (or ``'col'``),
        ``'cells'``, ``'neighbors'`` (or ``'neighbours'``), and ``'all'``.

        Args:
            region: A :class:`Region` describing the desired cells.

        Returns:
            List of :class:`Cell` objects in the region.

        Raises:
            ValueError: If the region type is unknown or references invalid cells.
        """
        rtype = region.region_type.strip().lower()

        if rtype == "row":
            if region.value is None:
                raise ValueError("Row region requires a row number value")
            return self.get_row(int(region.value))

        if rtype in ("column", "col"):
            if region.value is None:
                raise ValueError("Column region requires a column letter value")
            return self.get_column(str(region.value))

        if rtype == "cells":
            if not isinstance(region.value, list):
                raise ValueError("Explicit 'cells' region requires a list of cell IDs")
            seen: set[str] = set()
            result: List[Cell] = []
            for raw_id in region.value:
                cell = self.get_cell_by_id(str(raw_id))
                if cell is None:
                    raise ValueError(f"Cell {raw_id!r} not found in grid")
                if cell.cell_id not in seen:
                    seen.add(cell.cell_id)
                    result.append(cell)
            return result

        if rtype in ("neighbors", "neighbours"):
            if not isinstance(region.value, str):
                raise ValueError("Neighbors region requires a center cell ID string")
            parsed = _parse_cell_id(region.value)
            if parsed is None:
                raise ValueError(f"Invalid center cell ID for neighbors: {region.value!r}")
            return self.get_neighbors(parsed[0], parsed[1])

        if rtype == "all":
            return self.get_all_cells()

        raise ValueError(f"Unknown region type: {region.region_type!r}")

    def get_all_cells(self) -> List[Cell]:
        """Return all cells in the grid, in row-major order.

        Row-major order: A1, B1, C1, A2, B2, C2, …
        """
        return sorted(self.cells.values(), key=lambda c: (c.row, c.col))

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Grid(size={self.size}, cells={len(self.cells)})"
