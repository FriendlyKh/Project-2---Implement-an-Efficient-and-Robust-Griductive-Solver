# Owner: Person 4
"""
agent.trace — Deduction Trace & Logging
=========================================

Records every step of the deduction loop for auditing, reporting, and
visualization.  According to the project specification (Section 4.4), the
deduction trace must record:

* The step number
* Active clue identifiers at that step
* SAT queries executed
* Forced verdict derived
* Newly revealed clue (and the cell that was flipped)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from engine.verdict import Verdict


@dataclass
class TraceStep:
    """A single recorded step in the deduction process.

    Attributes:
        step_number: 1-based sequential step index.
        cell_id: Identifier of the cell deduced (e.g. ``'B2'``).
        character_name: Name of the deduced character.
        verdict: Entailed status (``Verdict.CRIMINAL`` or ``Verdict.INNOCENT``).
        active_clue_ids: List of clue identifiers/descriptions active at this step.
        sat_queries_count: Number of SAT solver calls made in this step.
        newly_revealed_clue: Natural-language or string description of newly revealed clue.
        notes: Optional extra details (e.g. proof justification).
    """

    step_number: int
    cell_id: str
    character_name: str
    verdict: Verdict
    active_clue_ids: List[str] = field(default_factory=list)
    sat_queries_count: int = 0
    newly_revealed_clue: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert step record to dictionary representation."""
        return {
            "step": self.step_number,
            "cell": self.cell_id,
            "name": self.character_name,
            "verdict": self.verdict.name if hasattr(self.verdict, "name") else str(self.verdict),
            "active_clues": self.active_clue_ids,
            "sat_queries": self.sat_queries_count,
            "revealed_clue": self.newly_revealed_clue,
            "notes": self.notes,
        }


class DeductionTrace:
    """Complete log of all deduction steps during puzzle resolution.

    Attributes:
        steps: List of sequential :class:`TraceStep` instances.
        total_sat_calls: Aggregate count of SAT calls across all steps.
    """

    def __init__(self) -> None:
        """Initialise an empty trace."""
        self.steps: List[TraceStep] = []
        self.total_sat_calls: int = 0

    def add_step(self, step: TraceStep) -> None:
        """Append a completed step to the trace.

        Args:
            step: The :class:`TraceStep` to record.
        """
        self.steps.append(step)
        self.total_sat_calls += step.sat_queries_count

    def to_dict(self) -> List[Dict[str, Any]]:
        """Export full trace to a list of dictionaries (for JSON output)."""
        return [step.to_dict() for step in self.steps]

    def format_table(self) -> str:
        """Render trace as a formatted text table suitable for CLI display or reports.

        Returns:
            A formatted multi-line string.
        """
        # TODO: Implement clean tabular formatting (e.g. using tabulate or manual columns)
        # Columns: Step | Cell | Character | Verdict | Queries | Newly Revealed Clue
        raise NotImplementedError("TODO: Implement DeductionTrace.format_table()")
