# Owner: Person 4
"""agent — Deductive logic agent, entailment, hints, and tracing."""

from agent.logic_agent import LogicAgent
from agent.entailment import EntailmentChecker
from agent.hint import HintProvider
from agent.trace import DeductionTrace

__all__ = ["LogicAgent", "EntailmentChecker", "HintProvider", "DeductionTrace"]
