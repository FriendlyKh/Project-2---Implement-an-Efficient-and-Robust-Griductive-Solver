# Owner: Person 2
"""
logic.variable_map — Propositional Variable Mapping
=====================================================

Provides a deterministic, bijective mapping between character names (or
cell IDs) and positive integer propositional variables used in the
DIMACS-style CNF representation.

Convention
----------
* Variable ``i`` (positive int) represents *"character i is a CRIMINAL"*.
* Literal ``+i`` → character is criminal.
* Literal ``-i`` → character is innocent.

The mapping is **deterministic**: given the same set of characters, the
same variable numbers are always assigned (sorted alphabetically by
cell ID).
"""

from __future__ import annotations

from typing import Dict, List, Optional


class VariableMap:
    """Bijective mapping between character/cell identifiers and SAT variable
    integers.

    Usage::

        vmap = VariableMap()
        vmap.register("Alice", "A1")
        var = vmap.get_var("A1")     # → 1
        name = vmap.get_character(1) # → "Alice"
        cell = vmap.get_cell_id(1)   # → "A1"

    Attributes:
        _char_to_var: Mapping character_name → variable int.
        _cell_to_var: Mapping cell_id → variable int.
        _var_to_char: Reverse mapping variable int → character_name.
        _var_to_cell: Reverse mapping variable int → cell_id.
        _next_var: Next variable number to assign.
    """

    def __init__(self) -> None:
        self._char_to_var: Dict[str, int] = {}
        self._cell_to_var: Dict[str, int] = {}
        self._var_to_char: Dict[int, str] = {}
        self._var_to_cell: Dict[int, str] = {}
        self._next_var: int = 1

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, character_name: str, cell_id: str) -> int:
        """Register a character and assign it the next variable number.

        Args:
            character_name: Display name (e.g. ``'Alice'``).
            cell_id: Grid cell (e.g. ``'A1'``).

        Returns:
            The assigned positive integer variable.

        Raises:
            ValueError: If the character or cell is already registered.
        """
        # TODO: Implement registration
        #   1. Check for duplicates
        #   2. Assign self._next_var
        #   3. Update all four maps
        #   4. Increment self._next_var
        if character_name in self._char_to_var:
            raise ValueError("The character is already registered!")

        if cell_id in self._cell_to_var:
            raise ValueError("The cell is already registered!")

        var = self._next_var
        self._char_to_var[character_name] = var
        self._cell_to_var[cell_id] = var
        self._var_to_char[var] = character_name
        self._var_to_cell[var] = cell_id

        self._next_var += 1
        return var

    def register_all(
        self, characters: List[Dict[str, str]]
    ) -> None:
        """Bulk-register characters from a list of dicts.

        Each dict must have keys ``'name'`` and ``'cell'``.
        Characters are sorted by cell ID before assignment to ensure
        determinism.

        Args:
            characters: List of ``{"name": "Alice", "cell": "A1", …}`` dicts.
        """
        # TODO: Sort by cell_id, then call register() for each
        characters = sorted(characters, key=lambda x: x['cell'])

        for char in characters:
            self.register(char['name'], char['cell'])

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_var(self, cell_id: str) -> int:
        """Return the variable number for the given *cell_id*.

        Args:
            cell_id: Cell identifier (e.g. ``'B2'``).

        Returns:
            Positive integer variable.

        Raises:
            KeyError: If *cell_id* is not registered.
        """
        # TODO: Implement lookup
        if cell_id in self._cell_to_var:
            return self._cell_to_var[cell_id]
        raise KeyError("Cell not registered!")

    def get_var_by_name(self, character_name: str) -> int:
        """Return the variable number for the given *character_name*.

        Args:
            character_name: Character display name.

        Returns:
            Positive integer variable.

        Raises:
            KeyError: If *character_name* is not registered.
        """
        # TODO: Implement lookup
        if character_name in self._char_to_var:
            return self._char_to_var[character_name]
        raise KeyError("Character not registered!")

    def get_character(self, var: int) -> str:
        """Return the character name for variable *var*.

        Args:
            var: Positive integer variable.

        Returns:
            Character display name.

        Raises:
            KeyError: If *var* is not registered.
        """
        # TODO: Implement reverse lookup
        if var in self._var_to_char:
            return self._var_to_char[var]
        raise KeyError("Variable not registered!")

    def get_cell_id(self, var: int) -> str:
        """Return the cell ID for variable *var*.

        Args:
            var: Positive integer variable.

        Returns:
            Cell identifier string.

        Raises:
            KeyError: If *var* is not registered.
        """
        # TODO: Implement reverse lookup
        if var in self._var_to_cell:
            return self._var_to_cell[var]
        raise KeyError("Variable not registered!")

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    @property
    def num_vars(self) -> int:
        """Total number of registered variables."""
        return self._next_var - 1

    def __repr__(self) -> str:
        return f"VariableMap(num_vars={self.num_vars})"
