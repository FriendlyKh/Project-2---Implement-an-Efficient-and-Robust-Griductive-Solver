# Owner: Person 1
"""
engine.verdict — Verdict Enumeration
======================================

Enumerates every possible classification outcome for a character cell.
"""

from __future__ import annotations

from enum import Enum, auto


class Verdict(Enum):
    """Possible verdicts for a character.

    Values:
        CRIMINAL:
            The knowledge base *entails* that this character is a criminal
            (KB ∧ ¬C_i is UNSAT).
        INNOCENT:
            The knowledge base *entails* that this character is innocent
            (KB ∧ C_i is UNSAT).
        UNKNOWN:
            Neither CRIMINAL nor INNOCENT can be proven from the current
            knowledge base — more clues are needed.
        NOT_PROVABLE:
            Neither verdict is currently logically forced by the public KB
            (guessing is not allowed).
        CONTRADICTED:
            The opposite verdict is currently logically forced by the public KB
            (or the submission contradicts the hidden solution).
        INCONSISTENT:
            The knowledge base itself is inconsistent (both KB ∧ C_i and
            KB ∧ ¬C_i are UNSAT).  This should never happen in a valid
            puzzle.
    """

    CRIMINAL = auto()
    INNOCENT = auto()
    UNKNOWN = auto()
    NOT_PROVABLE = auto()
    CONTRADICTED = auto()
    INCONSISTENT = auto()

    # Accepted by the engine when the verdict is logically provable
    ACCEPTED = auto()
