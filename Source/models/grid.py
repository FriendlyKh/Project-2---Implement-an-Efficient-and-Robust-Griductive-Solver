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

from typing import Dict, List, Optional

from models.cell import Cell
from models.clue import Region


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
        """
        self.size: int = size
        self.cells: Dict[str, Cell] = {}

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def add_cell(self, cell: Cell) -> None:
        """Register *cell* in the grid.

        Args:
            cell: The :class:`Cell` to add.

        Raises:
            ValueError: If a cell with the same ID already exists.
        """
        # TODO: Validate and store the cell in self.cells
        raise NotImplementedError("TODO: Implement Grid.add_cell()")

    def get_cell(self, col: str, row: int) -> Optional[Cell]:
        """Return the cell at column *col*, row *row*, or ``None``.

        Args:
            col: Column letter (e.g. ``'A'``).
            row: 1-based row number.
        """
        # TODO: Look up and return the cell from self.cells
        raise NotImplementedError("TODO: Implement Grid.get_cell()")

    def get_cell_by_id(self, cell_id: str) -> Optional[Cell]:
        """Return the cell with the given *cell_id*, or ``None``.

        Args:
            cell_id: Canonical cell identifier (e.g. ``'B2'``).
        """
        # TODO: Parse cell_id and delegate to get_cell
        raise NotImplementedError("TODO: Implement Grid.get_cell_by_id()")

    # ------------------------------------------------------------------
    # Region queries
    # ------------------------------------------------------------------

    def get_row(self, row_num: int) -> List[Cell]:
        """Return all cells in *row_num* (1-based), ordered by column.

        Args:
            row_num: The row number.
        """
        # TODO: Filter self.cells by row and return sorted by column
        raise NotImplementedError("TODO: Implement Grid.get_row()")

    def get_column(self, col_letter: str) -> List[Cell]:
        """Return all cells in the given column, ordered by row.

        Args:
            col_letter: The column letter (e.g. ``'A'``).
        """
        # TODO: Filter self.cells by column and return sorted by row
        raise NotImplementedError("TODO: Implement Grid.get_column()")

    def get_neighbors(self, col: str, row: int) -> List[Cell]:
        """Return the (up to 8) orthogonal + diagonal neighbours of (*col*, *row*).

        Args:
            col: Column letter.
            row: Row number.
        """
        # TODO: Compute neighbouring positions and return valid cells
        raise NotImplementedError("TODO: Implement Grid.get_neighbors()")

    def get_region(self, region: Region) -> List[Cell]:
        """Resolve a :class:`Region` specification into a list of cells.

        Supports region types: ``'row'``, ``'column'``, ``'cells'``, ``'all'``.

        Args:
            region: A :class:`Region` describing the desired cells.

        Returns:
            List of :class:`Cell` objects in the region.
        """
        # TODO: Dispatch based on region.region_type
        raise NotImplementedError("TODO: Implement Grid.get_region()")

    def get_all_cells(self) -> List[Cell]:
        """Return all cells in the grid, in row-major order.

        Row-major order: A1, B1, C1, A2, B2, C2, …
        """
        # TODO: Return cells sorted by (row, col)
        raise NotImplementedError("TODO: Implement Grid.get_all_cells()")

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Grid(size={self.size}, cells={len(self.cells)})"
