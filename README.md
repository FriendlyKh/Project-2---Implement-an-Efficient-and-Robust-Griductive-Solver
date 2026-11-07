# 🕵️‍♂️ Griductive Solver — Project 2

> **Course:** CSC14003 — Introduction to Artificial Intelligence  
> **Faculty of Information Technology, University of Science, VNU-HCM**  
> **Team:** 4 Members | **Duration:** ~3 Weeks  

A robust, no-guess grid-deduction puzzle solver using propositional logic, combinatorial CNF encoding, an engineered DPLL SAT solver, and a proof-by-refutation deductive agent.

---

## 🌟 Interactive Visual Explainer ("The Evolution of Trust" Style)

Inspired by Nicky Case’s [*The Evolution of Trust*](https://ncase.me/trust/), we built an interactive, bite-sized web journey explaining:
- Griductive puzzle rules & card flipping
- The **"NO GUESSING"** golden rule
- Propositional logic variables ($C_i$) & Conjunctive Normal Form (CNF)
- The **DPLL SAT solver** (Unit Propagation & Backtracking)
- **Proof-by-Refutation Entailment**: $\text{KB}_t \models C_i \iff \text{KB}_t \land \neg C_i \text{ is UNSAT}$
- Autonomous deduction loops & firewall architecture

👉 **Launch Explainer:** Open [`docs/explainer.html`](file:///home/nguyen-dinh-ngoc-khoa/PycharmProjects/Project-2---Implement-an-Efficient-and-Robust-Griductive-Solver/docs/explainer.html) in any browser:
```bash
xdg-open docs/explainer.html    # Linux
# or open docs/explainer.html   # macOS
```

---

## 📚 Essential Project Documentation

| Document | Purpose |
|---|---|
| [**`TASK_DISTRIBUTION.md`**](file:///home/nguyen-dinh-ngoc-khoa/PycharmProjects/Project-2---Implement-an-Efficient-and-Robust-Griductive-Solver/TASK_DISTRIBUTION.md) | **4-person task breakdown**, acceptance criteria, contribution matrix, and rubric points |
| [**`PIPELINE.md`**](file:///home/nguyen-dinh-ngoc-khoa/PycharmProjects/Project-2---Implement-an-Efficient-and-Robust-Griductive-Solver/PIPELINE.md) | **Deduction pipeline & CI/CD workflow**, Mermaid architecture diagrams, and entailment math |
| [**`Source/README.md`**](file:///home/nguyen-dinh-ngoc-khoa/PycharmProjects/Project-2---Implement-an-Efficient-and-Robust-Griductive-Solver/Source/README.md) | Developer guide, code structure, puzzle JSON schema, and execution commands |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd Source
pip install -r requirements.txt
```

### 2. Run Modes
```bash
# 1. Interactive CLI Menu
python main.py

# 2. Automated Solver (No Guessing)
python main.py --auto puzzles/3x3/puzzle_01.json

# 3. Interactive Web GUI (Flask)
python main.py --gui
# Access in browser at: http://127.0.0.1:5000

# 4. Batch Experiments & Benchmarks (3×3, 4×4, 5×5)
python main.py --experiment puzzles/

# 5. Run Automated Pipeline Check (compiles, validates JSON, runs tests)
../scripts/pipeline.sh
```

---

## 👥 4-Person Team Distribution & Grading Rubric

| Member | Title & Focus | Assigned Modules | Rubric Deliverables | Points |
|---|---|---|---|:---:|
| **Person 1** | **Game Engine & UI Architect** | `models/`, `engine/`, `gui/` | **Reimplement Game (10 pts)** + **Demo Video (10 pts)**<br>• Game state isolation & public view<br>• Web GUI with card flipping & clue highlight<br>• 5–10 min video presentation | **20 pts** |
| **Person 2** | **Knowledge & Logic Engineer** | `logic/`, extensions | **CNF Encoding (10 pts)**<br>• Variable mapping ($C_i$)<br>• 6 core templates (`FACT`, `SAME`, `DIFF`, `EXACTLY`, `AT_LEAST`, `AT_MOST`)<br>• 2 clue extensions (`PARITY`, `COMPARE`)<br>• Direct semantic evaluators | **10 pts** |
| **Person 3** | **SAT Solver & Benchmarking Specialist** | `solver/`, `experiments/` | **DPLL Solver (10 pts)** + **Experiments (10 pts)**<br>• DPLL procedure (unit prop, backtrack, stats)<br>• Experiment runner across 3×3, 4×4, 5×5 stress puzzles<br>• Export tables & charts for report | **20 pts** |
| **Person 4** | **Deductive Agent & Algorithm Lead** | `agent/`, entailment | **Deductive Logic Agent (20 pts)**<br>• Entailment checker ($\text{KB}_t \land \neg C_i \vdash \text{UNSAT}$)<br>• Autonomous deduction loop (strictly no guessing)<br>• Full clue set uniqueness check (blocking clauses)<br>• Hint system & deduction trace | **20 pts** |
| **All Team** | **Technical Report & Quality** | Integration & docs | **Report (30 pts)**<br>• Problem formulation, derivations, benchmarks, AI prompt log | **30 pts** |
| **Total** | | | | **100 pts** |

---

## 🏛️ System Architecture: The Strict Firewall

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

## 🔬 Mathematical Proof Protocol (Entailment)

For an unrevealed character $i$ at step $t$:
1. **Test CRIMINAL**: Run DPLL on $\text{KB}_t \land \neg C_i$.
   - If $\text{UNSAT} \implies \text{KB}_t \models C_i \implies \mathbf{CRIMINAL}$.
2. **Test INNOCENT**: Run DPLL on $\text{KB}_t \land C_i$.
   - If $\text{UNSAT} \implies \text{KB}_t \models \neg C_i \implies \mathbf{INNOCENT}$.
3. **If Both SAT**: Status is $\mathbf{UNKNOWN}$ $\implies$ Agent skips and waits for more clues.
4. **If Both UNSAT**: Status is $\mathbf{INCONSISTENT}$ $\implies$ Puzzle contains contradictory clues.

---

## 🛠️ Verification & CI/CD

Run the automated 5-stage verification pipeline anytime:
```bash
./scripts/pipeline.sh
```
This runs:
1. Python environment checks
2. Bytecode compilation (`python3 -m compileall Source/`)
3. Puzzle JSON schema validations (all 3×3, 4×4, 5×5 files)
4. CLI sanity test (`python3 Source/main.py --help`)
5. Unit test suite
