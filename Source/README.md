# Griductive Solver — Project 2 (CSC14003)

> **Course**: CSC14003 — Introduction to Artificial Intelligence  
> **Faculty of Information Technology, University of Science, VNU-HCM**  
> **Assignment**: Project 2 — Implement an Efficient and Robust Griductive Solver  
> **Duration**: ~3 weeks | **Team Size**: 4 members

---

## 🧭 Visual Interactive Guide

We built an interactive **"Evolution of Trust"**-style web explainer that walks through the entire logic, game mechanics, DPLL solver, entailment engine, and architecture step-by-step with interactive puzzles and animations.

To open it in your browser:
```bash
# Open in your browser (Linux)
xdg-open docs/explainer.html
# or on macOS: open docs/explainer.html
# or on Windows: start docs/explainer.html
```

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
cd Source
pip install -r requirements.txt
```

### 2. Run Modes

- **Interactive CLI Menu**:
  ```bash
  python main.py
  ```
- **Load and Play a Puzzle (CLI)**:
  ```bash
  python main.py --puzzle puzzles/3x3/puzzle_01.json
  ```
- **Automated No-Guess Solving**:
  ```bash
  python main.py --auto puzzles/3x3/puzzle_01.json
  ```
- **Interactive Web GUI (Flask)**:
  ```bash
  python main.py --gui
  # Opens modern interface at http://127.0.0.1:5000
  ```
- **Batch Experiments (3×3, 4×4, 5×5)**:
  ```bash
  python main.py --experiment puzzles/
  ```
- **Run Unit Tests**:
  ```bash
  pytest tests/ -v
  ```

---

## 👥 4-Person Team Distribution & Ownership

Each file in `Source/` has an explicit `# Owner: Person X` annotation. The tasks map directly to the assignment grading rubric:

| Role & Member | Assigned Components | Deliverables & Grading Scope | Key Files |
|---|---|---|---|
| **Person 1**<br>*(Game Modeling & GUI Frontend)* | • Grid, Cell, Clue models<br>• GameEngine & State Isolation<br>• Web GUI & Card Flipping<br>• Clue Highlighting & Controls | **Reimplement the Game (10 pts)**<br>• Playable GUI with coordinates, cards, statuses<br>• State isolation (hidden data never leaked)<br>• Load, Restart, Hint, Auto Solve controls<br>• Video demo presentation lead (10 pts) | `models/`<br>`engine/`<br>`gui/`<br>`tests/test_game_engine.py` |
| **Person 2**<br>*(Logic Formulation & CNF Encoding)* | • Propositional variable mapping<br>• Clue templates to CNF<br>• 2 Clue Extensions (Parity, Compare)<br>• Semantic Evaluators<br>• Knowledge Base state builder | **Automatic CNF Encoding (10 pts)**<br>• Deterministic variable mapping ($C_i$)<br>• 6 core clue templates (FACT, SAME, DIFF, EXACTLY, AT_LEAST, AT_MOST)<br>• ≥2 extensions (e.g. Parity, Region Compare)<br>• Direct semantic evaluators | `logic/variable_map.py`<br>`logic/cnf_encoder.py`<br>`logic/knowledge_base.py`<br>`logic/semantic_evaluator.py`<br>`tests/test_cnf_encoder.py` |
| **Person 3**<br>*(DPLL SAT Solver & Experiments)* | • Core DPLL algorithm<br>• Unit propagation & conflict check<br>• Backtracking & search statistics<br>• Experiment runner & benchmarks | **DPLL Solver (10 pts) & Experiments (10 pts)**<br>• DPLL procedure (unit prop, conflict detection, backtrack)<br>• Metrics tracking (decisions, propagations, backtracks, runtime)<br>• Benchmarking 3×3, 4×4, 5×5 stress puzzles<br>• CSV / LaTeX table generation for report | `solver/dpll.py`<br>`solver/stats.py`<br>`experiments/runner.py`<br>`tests/test_dpll.py` |
| **Person 4**<br>*(Deductive Logic Agent & Entailment)* | • Entailment checking (KB $\models C_i$)<br>• Autonomous deduction loop<br>• Deduction trace logging<br>• Hint system & Uniqueness check | **Deductive Logic Agent (20 pts)**<br>• Entailment: $\text{KB}_t \land \neg C_i$ is UNSAT $\iff C_i$ is CRIMINAL<br>• No-guess deduction loop<br>• Step-by-step deduction trace<br>• Full clue set uniqueness check (blocking clause) | `agent/entailment.py`<br>`agent/logic_agent.py`<br>`agent/hint.py`<br>`agent/trace.py`<br>`tests/test_agent.py` |

---

## 🏛️ System Architecture & Wall of Separation

```
┌────────────────────────────────────────────────────────┐
│                   GameEngine                           │
│  • Holds full ground-truth puzzle & hidden solution    │
│  • Manages unrevealed cards and face-up state          │
│  • Validates submitted verdicts against provability    │
└──────────────────────────▲─────────────────────────────┘
                           │ Public API (Revealed only)
                           │ NEVER leaks hidden status!
═══════════════════════════╪══════════════════════════════
               FIREWALL / STRICT BOUNDARY
═══════════════════════════╪══════════════════════════════
                           │
┌──────────────────────────▼─────────────────────────────┐
│                   LogicAgent                           │
│  • Sees ONLY public KB (revealed clues + verdicts)     │
│  • EntailmentChecker: KB ∧ ¬Ci / KB ∧ Ci via DPLL     │
│  • Derives forced verdicts (CRIMINAL / INNOCENT)       │
│  • Strictly NO GUESSING allowed                        │
└────────────────────────────────────────────────────────┘
```

---

## 📐 Logical Entailment Formulation

For any unresolved character $i$ at step $t$:
- $\text{KB}_t \models C_i \iff \text{KB}_t \land \neg C_i$ is **UNSAT** $\implies$ **CRIMINAL**
- $\text{KB}_t \models \neg C_i \iff \text{KB}_t \land C_i$ is **UNSAT** $\implies$ **INNOCENT**
- Both satisfiable $\implies$ **UNKNOWN** (do not guess; wait for more clues)
- Both unsatisfiable $\implies$ **INCONSISTENT** (invalid puzzle / contradiction)

---

## 📦 Submission Structure (Required)

```
StudentID1_StudentID2_StudentID3_StudentID4/
├── Source/
│   ├── main.py
│   ├── requirements.txt
│   ├── README.md
│   ├── config.py
│   ├── models/
│   ├── engine/
│   ├── logic/
│   ├── solver/
│   ├── agent/
│   ├── gui/
│   ├── experiments/
│   ├── puzzles/
│   └── tests/
└── Report.pdf  (Includes demo video link)
```
