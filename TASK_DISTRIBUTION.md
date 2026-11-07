# 📋 Project 2: Task Distribution & Team Collaboration Framework

**Course:** CSC14003 — Introduction to Artificial Intelligence  
**Institution:** Faculty of Information Technology, University of Science, VNU-HCM  
**Project:** Griductive Solver (No-Guess Propositional Logic & DPLL SAT Solver)  
**Team Structure:** 4 Members  
**Duration:** 3 Weeks  

---

## 1. Executive Summary & Grading Breakdown

The 100-point grading scheme defined in the project specification maps directly to individual team responsibilities to ensure accountability and fair contribution evaluation.

| Person | Role Title | Core Technical Modules | Course Deliverables | Point Weight |
|---|---|---|---|---|
| **Person 1** | **Game Engine & UI Architect** | `models/`, `engine/`, `gui/` | Reimplement the Game (10 pts)<br>Demonstration Video Lead (10 pts) | **20 pts** |
| **Person 2** | **Knowledge & Logic Engineer** | `logic/`, extensions | CNF Encoding & Clue Language (10 pts)<br>Report: CNF Formulations (7.5 pts) | **17.5 pts** |
| **Person 3** | **SAT Solver & Benchmarking Specialist** | `solver/`, `experiments/` | DPLL SAT Solver (10 pts)<br>Experiments & Benchmark Suite (10 pts) | **20 pts** |
| **Person 4** | **Deductive Agent & Algorithm Lead** | `agent/`, entailment | Deductive Logic Agent (20 pts)<br>Report: Agent & Uniqueness (7.5 pts) | **27.5 pts** |
| **All Members** | **Full Team** | Integration, Testing, Docs | Final Technical Report (15 pts remaining) | **15 pts** |
| **Total** | | | | **100 pts** |

---

## 2. Individual Work Breakdown & Acceptance Criteria

### 👤 Person 1: Game Engine & GUI Architect
* **Primary Scope:** Data modeling, game state isolation, interactive user interface, and video production.
* **Grading Target:** Section 4.1 (10 pts) + Section 4.7 (10 pts).

#### Tasks & Milestones
- [ ] **Task 1.1 — Data Models (`Source/models/`)**
  - Implement `Cell` dataclass (`row`, `col`, `character_name`, `profession`, `status`, `clue`, `is_revealed`).
  - Implement `Grid` class with spatial queries: `get_cell(col, row)`, `get_row(n)`, `get_column(letter)`, 8-neighborhood calculation (excluding self), and explicit region resolution.
  - Implement `Puzzle` class and JSON serialization/deserialization.
  - *Acceptance Criteria:* Passes `test_game_engine.py` model assertions; coordinates match $A1 \dots N \times N$.
- [ ] **Task 1.2 — Game Engine & Security Boundary (`Source/engine/`)**
  - Implement `GameEngine` holding the complete ground-truth solution and hidden clues.
  - Implement `get_public_state()`: returns **only** revealed cards and proven statuses (strictly no hidden data leak).
  - Implement `submit_verdict(cell_id, verdict)`:
    - If valid and proved: accepts verdict, flips card, and exposes the clue.
    - If unprovable: rejects verdict and returns `NOT_PROVABLE`.
    - If contradictory: rejects verdict and returns `CONTRADICTED`.
  - Implement `is_solved()` check.
- [ ] **Task 1.3 — Graphical User Interface (`Source/gui/`)**
  - Implement responsive web GUI using Flask (`gui/app.py`) or desktop GUI.
  - Visual coordinate grid (columns lettered $A \dots$, rows numbered $1 \dots$).
  - Character cards with avatars, professions, status badges, and 3D card-flip animations.
  - Clue selection highlighting: clicking a clue highlights all cells referenced or counted by that clue (`gui/clue_highlight.py`).
  - Controls: `Load Puzzle`, `Restart`, `💡 Hint`, `Step`, and `⚡ Auto Solve`.
- [ ] **Task 1.4 — Video Demonstration (5–10 minutes)**
  - Script, record, and edit the demonstration video covering:
    - Manual gameplay with valid and invalid verdict attempts.
    - Automated solver execution and step-by-step card reveals.
    - Visual clue highlighting and hint feature presentation.
  - Upload to Google Drive with public viewing permissions (tested in incognito mode).

---

### 👤 Person 2: Knowledge & Logic Engineer
* **Primary Scope:** Variable mapping, conversion of structured clue templates to CNF, semantic evaluators, and clue extensions.
* **Grading Target:** Section 4.2 (10 pts) + Section 4.6 (CNF Derivations).

#### Tasks & Milestones
- [ ] **Task 2.1 — Deterministic Variable Mapping (`Source/logic/variable_map.py`)**
  - Assign unique integer variables $1 \dots N^2$ deterministically to characters ordered alphabetically or by cell ID.
  - Provide bidirectional lookup: `get_var(character_name) -> int` and `get_character(var) -> str`.
  - Maintain clean separation between primary variables $C_i$ and auxiliary encoding variables.
- [ ] **Task 2.2 — Core Clue CNF Encoders (`Source/logic/cnf_encoder.py`)**
  - `FACT`: Unit clause $C_i$ or $\neg C_i$.
  - `SAME`: Equivalence $C_i \leftrightarrow C_j \implies (\neg C_i \lor C_j) \land (C_i \lor \neg C_j)$.
  - `DIFFERENT`: XOR $C_i \oplus C_j \implies (C_i \lor C_j) \land (\neg C_i \lor \neg C_j)$.
  - `EXACTLY k`: Direct combinatorial cardinality encoding:
    - At least $k$: $\bigvee_{S \subseteq R, |S|=|R|-k+1} \bigvee_{i \in S} C_i$.
    - At most $k$: $\bigwedge_{S \subseteq R, |S|=k+1} \bigvee_{i \in S} \neg C_i$.
  - `AT_LEAST k`: Combinatorial encoding for lower bound.
  - `AT_MOST k`: Combinatorial encoding for upper bound.
- [ ] **Task 2.3 — Two Distinct Clue Extensions**
  - *Extension 1 — Parity Clue (`PARITY`):* Encodes whether the number of criminals in a region is odd or even.
  - *Extension 2 — Regional Comparison Clue (`COMPARE`):* Encodes criminal count comparisons between two regions (e.g., $\sum_{i \in R_1} C_i > \sum_{j \in R_2} C_j$).
- [ ] **Task 2.4 — Semantic Evaluators (`Source/logic/semantic_evaluator.py`)**
  - Direct truth functions for each clue template given a complete model dictionary without calling the SAT solver.
  - Used for independent verification and puzzle validation.
- [ ] **Task 2.5 — Report Contribution**
  - Write complete mathematical derivations for at least one binary clue and one counting clue.

---

### 👤 Person 3: SAT Solver & Benchmarking Specialist
* **Primary Scope:** DPLL algorithm implementation, unit propagation, conflict detection, backtrack search, and benchmark evaluation suite.
* **Grading Target:** Section 4.3 (10 pts) + Section 4.5 (10 pts).

#### Tasks & Milestones
- [ ] **Task 3.1 — DPLL SAT Solver Core (`Source/solver/dpll.py`)**
  - **Unit Propagation:** Iteratively identify single-literal clauses, assign them, and simplify the clause database.
  - **Conflict Detection:** Detect empty clauses ($\emptyset$), triggering backtracking.
  - **Deterministic Variable Selection:** Select unassigned variables deterministically (e.g., smallest variable index or Maximum Occurrences in clauses of Minimum Size — MOM's heuristic).
  - **Recursive Branching & Backtracking:** Try assigning $V = \text{True}$; on contradiction, backtrack and try $V = \text{False}$.
  - Support assumption literals for temporary entailment queries without rebuilding clauses.
- [ ] **Task 3.2 — Performance Instrumentation (`Source/solver/stats.py`)**
  - Record:
    - Number of decisions (branching choices).
    - Number of unit propagations.
    - Number of backtracks.
    - Solver wall-clock runtime (microsecond precision).
- [ ] **Task 3.3 — Experiment Runner (`Source/experiments/runner.py`)**
  - Automated batch execution over test puzzles:
    - $3 \times 3$ standard puzzles (`puzzles/3x3/`)
    - $4 \times 4$ puzzles (`puzzles/4x4/`)
    - $5 \times 5$ stress-test puzzle (`puzzles/5x5/`)
  - Capture and export all metrics: Primary Vars, Aux Vars, Clause Count, SAT Calls, Decisions, Propagations, Backtracks, Deduction Steps, and Total Runtime.
  - Export to CSV (`experiments/results/summary.csv`) and console formatted table (`tabulate`).
- [ ] **Task 3.4 — Report Contribution**
  - Generate performance comparison tables and charts for the final report. Analyze scaling characteristics and bottlenecks.

---

### 👤 Person 4: Deductive Agent & Algorithm Lead
* **Primary Scope:** Proof-by-refutation entailment engine, autonomous no-guess deduction loop, deduction trace logger, hint generator, and puzzle uniqueness verification.
* **Grading Target:** Section 4.4 (20 pts).

#### Tasks & Milestones
- [ ] **Task 4.1 — Entailment Engine (`Source/agent/entailment.py`)**
  - Implement two-SAT-query entailment testing for candidate variable $C_i$:
    1. Query $KB_t \land \neg C_i$ with DPLL:
       - If **UNSAT** $\implies KB_t \models C_i \implies \mathbf{CRIMINAL}$.
    2. Query $KB_t \land C_i$ with DPLL:
       - If **UNSAT** $\implies KB_t \models \neg C_i \implies \mathbf{INNOCENT}$.
    3. If both SAT $\implies \mathbf{UNKNOWN}$ (do not guess!).
    4. If both UNSAT $\implies \mathbf{INCONSISTENT}$ (puzzle error).
- [ ] **Task 4.2 — No-Guess Deduction Loop (`Source/agent/logic_agent.py`)**
  - Scan all unresolved cells in deterministic row-major order ($A1, B1, \dots$).
  - For each cell, check entailment. Stop at the first forced verdict.
  - Submit forced verdict to `GameEngine`, receive new clue, update Knowledge Base $KB_{t+1}$, and repeat.
  - Terminate when all cards are resolved or when a deadlock is detected (no forced verdict $\implies$ return failure).
- [ ] **Task 4.3 — Deduction Trace Logging (`Source/agent/trace.py`)**
  - Record each step $t$: Step Number, Active Clue IDs, SAT Queries Executed, Forced Verdict, and Newly Revealed Clue.
  - Provide tabular export for CLI and GUI display.
- [ ] **Task 4.4 — Hint Engine (`Source/agent/hint.py`)**
  - Scan public knowledge state and identify one currently forced character without inspecting hidden data.
  - Identify the active clue(s) that justify this deduction.
- [ ] **Task 4.5 — Full Clue Set Uniqueness Verification**
  - Implement blocking-clause model check on the complete puzzle clue set:
    1. Encode all clues into CNF formula $\Phi$.
    2. Find model $M_1$. If UNSAT $\implies$ invalid puzzle.
    3. Add blocking clause $\neg M_1 = \bigvee_{l \in M_1} \neg l$ and solve again.
    4. If UNSAT $\implies$ unique solution; if SAT $\implies$ ambiguous puzzle.
- [ ] **Task 4.6 — Report Contribution**
  - Document the deduction loop pseudocode, entailment algorithm, and uniqueness proof.

---

## 3. Contribution Percentage Tracking Matrix

As mandated by Section 4.6 of the specification:
$$\text{Individual Score} = \text{Group Score} \times \text{Completion Percentage}$$

Every member's contribution will be logged and signed off before report submission:

| Member Name | Student ID | Assigned Modules | Self-Assessment (%) | Peer-Review (%) | Agreed Final (%) |
|---|---|---|:---:|:---:|:---:|
| **Member 1** | `22120xxx` | `models/`, `engine/`, `gui/`, Video | 100% | 100% | **100%** |
| **Member 2** | `22120xxx` | `logic/`, CNF, Extensions | 100% | 100% | **100%** |
| **Member 3** | `22120xxx` | `solver/`, `experiments/` | 100% | 100% | **100%** |
| **Member 4** | `22120xxx` | `agent/`, Entailment, Trace | 100% | 100% | **100%** |

---

## 4. Git Collaboration Workflow & Rules

### Branching Convention
* `main`: Protected production branch. Clean, compiling, tested code only.
* `develop`: Integration branch. Merged via Pull Requests with at least 1 approval.
* Feature branches:
  * `feat/p1-engine-gui` (Person 1)
  * `feat/p2-cnf-encoder` (Person 2)
  * `feat/p3-dpll-solver` (Person 3)
  * `feat/p4-logic-agent` (Person 4)

### Commit Message Format
Follow Conventional Commits:
* `feat(logic): implement combinatorial encoding for EXACTLY k`
* `fix(solver): resolve infinite loop in backtracking on empty clause`
* `test(agent): add test cases for proof by contradiction`
* `docs(readme): update experiment run instructions`

### Interface Contracts
To work in parallel without blocking each other:
1. **Person 3 (Solver)** does not need Person 2's encoder to test DPLL: use DIMACS CNF lists like `[[1, 2], [-1, 2]]`.
2. **Person 2 (Logic)** does not need Person 3's solver: use `semantic_evaluator.py` to test clause truth against known truth assignments.
3. **Person 4 (Agent)** mocks `solver.solve(...)` until Person 3 delivers the DPLL solver.
4. **Person 1 (GUI)** mocks `ctrl.auto_solve_step()` with predefined steps until Person 4 finishes the deduction loop.
