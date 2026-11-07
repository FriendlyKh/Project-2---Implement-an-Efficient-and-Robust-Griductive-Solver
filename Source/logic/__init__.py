# Owner: Person 2
"""logic — Propositional logic layer (variable mapping, CNF encoding, KB)."""

from logic.variable_map import VariableMap
from logic.cnf_encoder import CNFEncoder
from logic.knowledge_base import KnowledgeBase
from logic.semantic_evaluator import SemanticEvaluator

__all__ = ["VariableMap", "CNFEncoder", "KnowledgeBase", "SemanticEvaluator"]
