# Owner: Person 3 & QA
"""tests.test_dpll — Unit tests for the DPLL SAT solver."""

import unittest
from solver.dpll import DPLL


class TestDPLLSolver(unittest.TestCase):
    """Tests SAT solving capabilities and stats recording."""

    def test_simple_sat(self):
        solver = DPLL()
        # (x1 ∨ x2) ∧ (¬x1 ∨ x2) -> satisfied by x2=True
        clauses = [[1, 2], [-1, 2]]
        # TODO: Once implemented, assert sat is True
        # sat, assignment = solver.solve(clauses, num_vars=2)
        # self.assertTrue(sat)

    def test_simple_unsat(self):
        solver = DPLL()
        # (x1) ∧ (¬x1) -> UNSAT
        clauses = [[1], [-1]]
        # TODO: Once implemented, assert sat is False
        # sat, assignment = solver.solve(clauses, num_vars=1)
        # self.assertFalse(sat)

    def test_unit_propagation(self):
        solver = DPLL()
        # (x1) ∧ (¬x1 ∨ x2) -> unit prop sets x1=True, then x2=True
        clauses = [[1], [-1, 2]]
        # TODO: Verify unit propagation step


if __name__ == "__main__":
    unittest.main()
