# Owner: Person 3
"""
solver.stats — Solver Statistics Tracker
==========================================

Tracks performance metrics for each SAT solver invocation:

* Number of decisions (branching choices)
* Number of unit propagations
* Number of backtracks
* Total runtime (wall-clock seconds)

Used by the experiment runner and deduction trace logger.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SolverStats:
    """Accumulated statistics for a solver run.

    Attributes:
        decisions: Number of branching decisions made.
        propagations: Number of unit propagations performed.
        backtracks: Number of backtrack operations.
        conflicts: Number of conflicts detected.
        runtime_seconds: Wall-clock time in seconds.
        sat_calls: Number of separate SAT queries made.
    """

    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    conflicts: int = 0
    runtime_seconds: float = 0.0
    sat_calls: int = 0

    # Internal timer (not serialised)
    _start_time: float = field(default=0.0, repr=False)

    def start_timer(self) -> None:
        """Begin timing a solver call."""
        self._start_time = time.perf_counter()

    def stop_timer(self) -> None:
        """Stop the timer and accumulate elapsed time."""
        if self._start_time > 0:
            self.runtime_seconds += time.perf_counter() - self._start_time
            self._start_time = 0.0

    def record_decision(self) -> None:
        """Increment the decision counter."""
        self.decisions += 1

    def record_propagation(self) -> None:
        """Increment the propagation counter."""
        self.propagations += 1

    def record_backtrack(self) -> None:
        """Increment the backtrack counter."""
        self.backtracks += 1

    def record_conflict(self) -> None:
        """Increment the conflict counter."""
        self.conflicts += 1

    def record_sat_call(self) -> None:
        """Increment the SAT call counter."""
        self.sat_calls += 1

    def merge(self, other: "SolverStats") -> None:
        """Merge *other*'s counters into this instance.

        Args:
            other: Another :class:`SolverStats` to combine.
        """
        self.decisions += other.decisions
        self.propagations += other.propagations
        self.backtracks += other.backtracks
        self.conflicts += other.conflicts
        self.runtime_seconds += other.runtime_seconds
        self.sat_calls += other.sat_calls

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "decisions": self.decisions,
            "propagations": self.propagations,
            "backtracks": self.backtracks,
            "conflicts": self.conflicts,
            "runtime_seconds": round(self.runtime_seconds, 6),
            "sat_calls": self.sat_calls,
        }

    def __repr__(self) -> str:
        return (
            f"SolverStats(decisions={self.decisions}, "
            f"propagations={self.propagations}, "
            f"backtracks={self.backtracks}, "
            f"runtime={self.runtime_seconds:.4f}s)"
        )
