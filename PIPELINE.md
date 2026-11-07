# ⚙️ Griductive Solver: Engineering & Deduction Pipeline

This document outlines the two core pipelines in the project:
1. **The Deduction Pipeline**: How clues, propositional logic, and DPLL interact to solve a puzzle with zero guessing.
2. **The Software Quality & CI/CD Pipeline**: Automated verification, unit testing, and benchmark generation.

---

## 1. 🧩 The Griductive Deduction Pipeline

The deduction loop operates strictly under the **Open World Assumption** from the agent's perspective: an unrevealed card carries unknown truth until logically forced by public clues.

### Architecture & Security Boundary (The Firewall)

```mermaid
flowchart TD
    subgraph ENGINE["🔒 GameEngine (Authoritative Ground Truth)"]
        PUZZLE[("Loaded Puzzle<br>(Grid + Hidden Statuses)")]
        STATE[Current Board State]
        VERIFIER{Verdict Validation}
    end

    subgraph FIREWALL["🛡️ Firewall (State Isolation)"]
        direction TB
        PUBLIC_DATA["Public State Only:<br>• Revealed Cards<br>• Proven Verdicts<br>• Face-Up Clues"]
    end

    subgraph AGENT["🤖 LogicAgent (Pure Deduction)"]
        KB["Knowledge Base (KB_t)"]
        ENCODER["CNF Encoder<br>(Combinatorial Encoding)"]
        CHECKER["Entailment Checker<br>(KB ∧ ¬C_i / KB ∧ C_i)"]
        DPLL["DPLL SAT Solver<br>(Unit Prop + Backtracking)"]
        TRACE["Deduction Trace Logger"]
    end

    PUZZLE --> STATE
    STATE -->|Extract Public View| PUBLIC_DATA
    PUBLIC_DATA -->|Initialize| KB
    KB --> ENCODER
    ENCODER --> CHECKER
    CHECKER <--> DPLL
    CHECKER -->|Forced Verdict Found| TRACE
    TRACE -->|Submit Verdict| VERIFIER
    VERIFIER -->|If Accepted: Flip Card| STATE
```

---

### Step-by-Step Deduction Protocol

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Auto-Solve
    participant Agent as LogicAgent
    participant KB as KnowledgeBase
    participant Solver as DPLL Solver
    participant Engine as GameEngine

    User->>Agent: solve() or step()
    Agent->>Engine: get_public_state()
    Engine-->>Agent: revealed_clues, proven_statuses
    Agent->>KB: update(revealed_clues, proven_statuses)

    loop For each unresolved character C_i in row-major order
        Agent->>Solver: solve(KB ∧ ¬C_i) [Test CRIMINAL]
        Solver-->>Agent: Result (SAT or UNSAT)
        
        alt KB ∧ ¬C_i is UNSAT
            Note over Agent: C_i is forced CRIMINAL!
            Agent->>Engine: submit_verdict(C_i, CRIMINAL)
            Engine-->>Agent: ACCEPTED + newly_revealed_clue
            Agent->>KB: add_clue(new_clue) & add_unit_clause(C_i)
        else KB ∧ ¬C_i is SAT
            Agent->>Solver: solve(KB ∧ C_i) [Test INNOCENT]
            Solver-->>Agent: Result (SAT or UNSAT)
            alt KB ∧ C_i is UNSAT
                Note over Agent: C_i is forced INNOCENT!
                Agent->>Engine: submit_verdict(C_i, INNOCENT)
                Engine-->>Agent: ACCEPTED + newly_revealed_clue
                Agent->>KB: add_clue(new_clue) & add_unit_clause(¬C_i)
            else Both SAT
                Note over Agent: Status UNKNOWN. Continue to next cell.
            end
        end
    end
    Note over Agent: If no cell was forced in full pass: STOP (Deadlock / Unknown).
```

---

## 2. 🔬 Logical Entailment Mathematics

For any unresolved character $i$ at deduction step $t$:

$$\text{KB}_t \models C_i \iff \text{KB}_t \land \neg C_i \text{ is } \mathbf{UNSAT} \implies \text{Verdict: } \mathbf{CRIMINAL}$$

$$\text{KB}_t \models \neg C_i \iff \text{KB}_t \land C_i \text{ is } \mathbf{UNSAT} \implies \text{Verdict: } \mathbf{INNOCENT}$$

$$\text{Both } \text{KB}_t \land \neg C_i \text{ and } \text{KB}_t \land C_i \text{ are SAT} \implies \text{Verdict: } \mathbf{UNKNOWN} \text{ (Never Guess)}$$

$$\text{Both } \text{KB}_t \land \neg C_i \text{ and } \text{KB}_t \land C_i \text{ are UNSAT} \implies \text{Verdict: } \mathbf{INCONSISTENT}$$

---

## 3. 🧪 Software Quality & CI/CD Pipeline

We enforce a strict 4-stage pipeline for all code contributions:

```mermaid
flowchart LR
    STAGE1["1. Syntax & Compiling<br>compileall"]
    STAGE2["2. Unit Tests<br>pytest tests/"]
    STAGE3["3. Solver Benchmarks<br>experiments/runner.py"]
    STAGE4["4. Export & Report<br>CSV / Stats"]

    STAGE1 --> STAGE2 --> STAGE3 --> STAGE4
```

### Stage 1: Syntax & Bytecode Compilation
Ensures no syntax errors, broken imports, or missing packages:
```bash
python3 -m compileall Source/
```

### Stage 2: Unit Testing Suite
Runs all test modules with verbose output:
```bash
pytest Source/tests/ -v
```

### Stage 3: Benchmark Suite (3×3, 4×4, 5×5)
Runs the experiment runner across all puzzle sizes and collects metrics:
```bash
python3 Source/main.py --experiment Source/puzzles/
```

### Stage 4: Automated Verification Script
Run the automated pipeline script in one step:
```bash
./scripts/pipeline.sh
```
