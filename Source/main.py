# Owner: Team Lead
"""
Griductive Solver — Entry Point
================================

Launches the solver in one of several modes:

* Interactive CLI menu (default, or with ``--puzzle`` pre-loaded)
* Load & auto-solve a single puzzle (``--auto``)
* Start the Flask-based GUI (``--gui``)
* Run batch experiments (``--experiment``)

Usage::
    python main.py
    python main.py --puzzle puzzles/3x3/puzzle_01.json
    python main.py --auto   puzzles/3x3/puzzle_01.json
    python main.py --gui
    python main.py --experiment puzzles/
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Ensure ``Source/`` is importable whether invoked from ``Source/`` or repo root
_SOURCE_DIR = Path(__file__).resolve().parent
if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))

# Configure UTF-8 output on Windows consoles / redirected streams
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

try:
    from colorama import Fore, Style, init as _colorama_init

    _colorama_init(autoreset=True)
except ImportError:  # pragma: no cover - graceful fallback without colorama

    class _NoColor:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
        BRIGHT = DIM = RESET_ALL = ""

    Fore = Style = _NoColor()  # type: ignore[assignment]

from tabulate import tabulate

from agent.entailment import EntailmentChecker
from agent.hint import HintProvider
from agent.logic_agent import LogicAgent
from config import (
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    MAX_SOLVER_TIMEOUT_SECONDS,
    PROJECT_ROOT,
    PUZZLE_DIR,
    RESULTS_DIR,
)
from engine.game_engine import GameEngine
from engine.puzzle_loader import load_puzzle
from engine.verdict import Verdict
from gui.clue_highlight import ClueHighlighter
from solver.dpll import DPLL


# ---------------------------------------------------------------------------
# Argument Parsing & Path Resolution
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="griductive-solver",
        description="No-guess grid-deduction puzzle solver (CSC14003 Project 2)",
    )
    parser.add_argument(
        "--puzzle",
        type=str,
        default=None,
        help="Path to a puzzle JSON file to load interactively.",
    )
    parser.add_argument(
        "--auto",
        type=str,
        default=None,
        metavar="PUZZLE",
        help="Auto-solve the given puzzle and print the deduction trace.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Flask-based web GUI.",
    )
    parser.add_argument(
        "--experiment",
        type=str,
        default=None,
        metavar="DIR",
        help="Run the solver on every puzzle under DIR and print stats.",
    )
    return parser.parse_args()


def _resolve_puzzle_path(filepath: str) -> Path:
    """Resolve a puzzle file path relative to CWD, Source/, Source/puzzles/, or repo root."""
    raw = Path(filepath)
    candidates = [
        raw,
        PROJECT_ROOT / raw,
        PUZZLE_DIR / raw,
        PROJECT_ROOT.parent / raw,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"Puzzle file not found: {filepath}")


def _resolve_target_dir(dir_path: str) -> Path:
    """Resolve an experiment directory (or single puzzle file) path."""
    raw = Path(dir_path)
    candidates = [
        raw,
        PROJECT_ROOT / raw,
        PROJECT_ROOT.parent / raw,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"Experiment path not found: {dir_path}")


def _list_available_puzzles() -> List[Tuple[Path, str]]:
    """Discover all puzzle JSON files under ``PUZZLE_DIR`` sorted by relative path."""
    if not PUZZLE_DIR.exists():
        return []
    files = sorted(
        PUZZLE_DIR.rglob("*.json"),
        key=lambda p: str(p.relative_to(PUZZLE_DIR)).replace("\\", "/"),
    )
    catalog: List[Tuple[Path, str]] = []
    for path in files:
        rel = str(path.relative_to(PUZZLE_DIR)).replace("\\", "/")
        catalog.append((path, rel))
    return catalog


def _format_puzzle_name(path: Path) -> str:
    """Return a concise display label for *path*."""
    try:
        return str(path.relative_to(PUZZLE_DIR)).replace("\\", "/")
    except ValueError:
        try:
            return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        except ValueError:
            return path.name


# ---------------------------------------------------------------------------
# Firewall-Safe CLI Board & Clue Display
# ---------------------------------------------------------------------------


def _format_cell_cli(cell_data: dict, highlighted: bool = False) -> str:
    """Format a single public cell dictionary for CLI tabular rendering.

    Strictly uses public fields from ``GameEngine.get_public_state()``.
    """
    cid = cell_data["id"]
    name = cell_data["name"]
    prof = cell_data["profession"]
    is_rev = bool(cell_data["is_revealed"])
    status = cell_data["status"] if is_rev else None

    marker = f"{Fore.YELLOW}*{Style.RESET_ALL}" if highlighted else " "
    header = f"{marker}[{cid}] {name} ({prof})"

    if is_rev and status == "CRIMINAL":
        badge = f"{Fore.RED}{Style.BRIGHT}CRIMINAL{Style.RESET_ALL}"
    elif is_rev and status == "INNOCENT":
        badge = f"{Fore.GREEN}{Style.BRIGHT}INNOCENT{Style.RESET_ALL}"
    else:
        badge = f"{Style.DIM}? UNKNOWN{Style.RESET_ALL}"

    return f"{header}\n  {badge}"


def _print_public_board(
    engine: GameEngine,
    puzzle_label: Optional[str] = None,
    highlighted_cells: Optional[Set[str]] = None,
    highlight_source: Optional[str] = None,
) -> None:
    """Render the public grid state and revealed clues to stdout.

    Never accesses ``engine.puzzle.solution`` or unrevealed clues.
    """
    state = engine.get_public_state()
    columns: List[str] = state["columns"]
    rows: List[int] = state["rows"]
    cells_by_id = {c["id"]: c for c in state["cells"]}
    highlights = {c.strip().upper() for c in (highlighted_cells or set())}

    resolved_count = len(state["verdicts"])
    total_cells = len(state["cells"])
    solved_tag = (
        f" {Fore.GREEN}{Style.BRIGHT}[SOLVED]{Style.RESET_ALL}"
        if state["is_solved"]
        else ""
    )

    title = f"Puzzle: {puzzle_label}" if puzzle_label else "Current Board"
    print(
        f"\n{Fore.CYAN}{Style.BRIGHT}{title}{Style.RESET_ALL} "
        f"— Progress: {resolved_count}/{total_cells} resolved{solved_tag}"
    )
    if highlight_source and highlights:
        print(
            f"{Fore.YELLOW}Highlighted clue ({highlight_source}) -> "
            f"Cells: {', '.join(sorted(highlights))} (*){Style.RESET_ALL}"
        )

    headers = ["Row \\ Col"] + [f"Col {col}" for col in columns]
    table_rows = []
    for r in rows:
        row_cells = [f"Row {r}"]
        for col in columns:
            cid = f"{col}{r}"
            cell_dict = cells_by_id[cid]
            row_cells.append(_format_cell_cli(cell_dict, highlighted=(cid in highlights)))
        table_rows.append(row_cells)

    print(tabulate(table_rows, headers=headers, tablefmt="grid"))

    revealed_clues = [
        c for c in state["cells"] if c["is_revealed"] and c.get("clue_text")
    ]
    print(f"\n{Fore.CYAN}Revealed Clues ({len(revealed_clues)}):{Style.RESET_ALL}")
    if not revealed_clues:
        print("  (No clues revealed yet)")
    else:
        for c in revealed_clues:
            active_mark = (
                f"{Fore.YELLOW}*{Style.RESET_ALL} "
                if highlight_source == c["id"]
                else "  "
            )
            print(
                f"{active_mark}[{c['id']}] {c['name']}: \"{c['clue_text']}\""
            )


# ---------------------------------------------------------------------------
# Execution Modes
# ---------------------------------------------------------------------------


def _run_auto_solve(puzzle_path: str) -> None:
    """Load a puzzle and run the deductive LogicAgent to auto-solve it."""
    resolved = _resolve_puzzle_path(puzzle_path)
    label = _format_puzzle_name(resolved)
    print(f"[Auto-Solve] Loading puzzle from: {resolved}")

    puzzle = load_puzzle(resolved)
    engine = GameEngine(puzzle)

    initially_rev = ", ".join(engine.puzzle.initially_revealed) or "none"
    print(
        f"[Auto-Solve] Grid: {puzzle.grid.size}x{puzzle.grid.size} | "
        f"Initially revealed: {initially_rev}"
    )
    _print_public_board(engine, puzzle_label=label)

    solver = DPLL(timeout_seconds=float(MAX_SOLVER_TIMEOUT_SECONDS))
    agent = LogicAgent(solver=solver)

    start_time = time.perf_counter()
    trace = agent.solve(engine)
    elapsed = time.perf_counter() - start_time

    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== Deduction Trace ==={Style.RESET_ALL}")
    print(trace.format_table())

    _print_public_board(engine, puzzle_label=label)

    kb_stats = engine.build_public_kb().get_stats()
    stats = solver.stats
    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== Solver & Knowledge Base Summary ==={Style.RESET_ALL}")
    print(
        f"  Primary Vars : {puzzle.grid.size * puzzle.grid.size} | "
        f"Aux Vars: {kb_stats['num_aux_vars']} | "
        f"Active Clauses: {kb_stats['num_clauses']}"
    )
    print(
        f"  SAT Calls    : {stats.sat_calls} | "
        f"Decisions: {stats.decisions} | "
        f"Propagations: {stats.propagations} | "
        f"Backtracks: {stats.backtracks} | "
        f"Conflicts: {stats.conflicts}"
    )
    print(f"  Total Time   : {elapsed:.6f}s (DPLL time: {stats.runtime_seconds:.6f}s)")

    if engine.is_solved():
        print(
            f"\n{Fore.GREEN}{Style.BRIGHT}[SUCCESS] Puzzle solved completely in "
            f"{len(trace.steps)} deductive step(s) with zero guessing!{Style.RESET_ALL}"
        )
    else:
        unresolved = ", ".join(engine.get_unresolved_cells())
        print(
            f"\n{Fore.YELLOW}{Style.BRIGHT}[DEADLOCK] Solver stopped after "
            f"{len(trace.steps)} step(s) without guessing. "
            f"Unresolved cells: {unresolved}{Style.RESET_ALL}"
        )


def _run_gui(puzzle_path: Optional[str] = None) -> None:
    """Launch the Flask web GUI (optionally pre-loading *puzzle_path*)."""
    from gui.app import create_app, launch_gui
    from gui.controls import GameController

    if puzzle_path:
        resolved = _resolve_puzzle_path(puzzle_path)
        ctrl = GameController()
        ctrl.load_puzzle(str(resolved))
        app = create_app(ctrl)
        print(
            f"\n[GUI] Pre-loaded puzzle: {_format_puzzle_name(resolved)}\n"
            f"[GUI] Starting Griductive web interface at http://{FLASK_HOST}:{FLASK_PORT}"
        )
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    else:
        print("[GUI] Starting Flask server...")
        launch_gui(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)


def _run_experiments(puzzle_dir: str) -> None:
    """Run batch experiments across all puzzles in a directory."""
    from experiments.runner import ExperimentRunner

    target = _resolve_target_dir(puzzle_dir)
    print(f"[Experiments] Scanning puzzles in: {target}")

    runner = ExperimentRunner(timeout_sec=float(MAX_SOLVER_TIMEOUT_SECONDS))
    results = runner.run_all(target)
    runner.print_table(results)

    csv_path = runner.export_csv(results, RESULTS_DIR / "summary.csv")
    print(f"\n[Experiments] Results exported to: {csv_path}")


# ---------------------------------------------------------------------------
# Interactive CLI Menu
# ---------------------------------------------------------------------------


def _prompt_puzzle_selection() -> Optional[Path]:
    """Display available puzzles and prompt the user for an index or file path."""
    catalog = _list_available_puzzles()
    if catalog:
        print(f"\n{Fore.CYAN}Available Puzzles:{Style.RESET_ALL}")
        for idx, (_, rel_label) in enumerate(catalog, start=1):
            print(f"  {idx}. {rel_label}")
    raw = input("\nEnter puzzle number or JSON file path (Enter to cancel): ").strip()
    if not raw:
        return None
    if raw.isdigit() and catalog:
        choice_idx = int(raw)
        if 1 <= choice_idx <= len(catalog):
            return catalog[choice_idx - 1][0]
        print(f"{Fore.RED}[!] Invalid selection number: {raw}{Style.RESET_ALL}")
        return None
    return _resolve_puzzle_path(raw)


def _parse_cli_verdict(raw: str) -> Optional[Verdict]:
    """Parse user input ('C'/'CRIMINAL' or 'I'/'INNOCENT') into a Verdict."""
    norm = raw.strip().upper()
    if norm in ("C", "CRIMINAL", "1"):
        return Verdict.CRIMINAL
    if norm in ("I", "INNOCENT", "2"):
        return Verdict.INNOCENT
    return None


def _run_cli_menu(initial_puzzle_path: Optional[str] = None) -> None:
    """Interactive command-line menu loop."""
    engine: Optional[GameEngine] = None
    current_path: Optional[Path] = None
    current_label: Optional[str] = None
    cli_agent: Optional[LogicAgent] = None
    highlighted_cells: Set[str] = set()
    highlight_source: Optional[str] = None

    def _load_into_session(path: Path) -> None:
        nonlocal engine, current_path, current_label, cli_agent, highlighted_cells, highlight_source
        puzzle = load_puzzle(path)
        engine = GameEngine(puzzle)
        current_path = path
        current_label = _format_puzzle_name(path)
        cli_agent = LogicAgent(
            solver=DPLL(timeout_seconds=float(MAX_SOLVER_TIMEOUT_SECONDS))
        )
        highlighted_cells = set()
        highlight_source = None
        revealed = ", ".join(engine.puzzle.initially_revealed) or "none"
        print(
            f"\n{Fore.GREEN}[Loaded]{Style.RESET_ALL} {current_label} "
            f"({puzzle.grid.size}x{puzzle.grid.size}) — Initially revealed: {revealed}"
        )
        _print_public_board(engine, puzzle_label=current_label)

    if initial_puzzle_path is not None:
        resolved_init = _resolve_puzzle_path(initial_puzzle_path)
        _load_into_session(resolved_init)

    while True:
        print("\n" + "=" * 58)
        print(f"  {Fore.CYAN}{Style.BRIGHT}Griductive Solver — Interactive CLI{Style.RESET_ALL}")
        print("=" * 58)
        if engine is not None and current_label is not None:
            res_cnt = len(engine.verdicts)
            tot_cnt = len(engine.puzzle.solution)
            status_note = "SOLVED" if engine.is_solved() else f"{res_cnt}/{tot_cnt} resolved"
            print(f"  Active Puzzle: {current_label} ({status_note})")
        else:
            print("  Active Puzzle: (none loaded)")
        print("-" * 58)
        print("  1. Load puzzle")
        print("  2. Show grid & revealed clues")
        print("  3. Highlight cells referenced by a revealed clue")
        print("  4. Submit verdict for a character")
        print("  5. Request logical hint")
        print("  6. Step solver (deduce 1 character)")
        print("  7. Auto-solve puzzle (no guessing)")
        print("  8. Restart current puzzle")
        print("  9. Run batch experiments")
        print("  0. Quit")
        print("-" * 58)

        try:
            choice = input("Select an option [0-9]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Griductive Solver. Goodbye!")
            break

        if choice == "0" or choice.lower() in ("q", "quit", "exit"):
            print("Exiting Griductive Solver. Goodbye!")
            break

        elif choice == "1":
            try:
                selected = _prompt_puzzle_selection()
                if selected is not None:
                    _load_into_session(selected)
            except (FileNotFoundError, ValueError) as exc:
                print(f"{Fore.RED}[Error] {exc}{Style.RESET_ALL}")

        elif choice == "2":
            if engine is None:
                print(f"{Fore.YELLOW}[!] Please load a puzzle first (option 1).{Style.RESET_ALL}")
                continue
            _print_public_board(
                engine,
                puzzle_label=current_label,
                highlighted_cells=highlighted_cells,
                highlight_source=highlight_source,
            )

        elif choice == "3":
            if engine is None:
                print(f"{Fore.YELLOW}[!] Please load a puzzle first (option 1).{Style.RESET_ALL}")
                continue
            cid = input(
                "Enter revealed cell ID to highlight its clue (Enter to clear): "
            ).strip().upper()
            if not cid:
                highlighted_cells = set()
                highlight_source = None
                print("Cleared clue highlight.")
            elif cid not in engine.revealed_cells:
                print(
                    f"{Fore.RED}[!] Cell {cid} is not revealed; hidden clues cannot be inspected.{Style.RESET_ALL}"
                )
                continue
            else:
                cell = engine.puzzle.grid.get_cell_by_id(cid)
                if cell is None or cell.clue is None:
                    highlighted_cells = set()
                    highlight_source = None
                    print(f"Cell {cid} carries no clue.")
                else:
                    highlighted_cells = ClueHighlighter.get_referenced_cells(
                        cell.clue, engine.puzzle.grid
                    )
                    highlight_source = cid
            _print_public_board(
                engine,
                puzzle_label=current_label,
                highlighted_cells=highlighted_cells,
                highlight_source=highlight_source,
            )

        elif choice == "4":
            if engine is None:
                print(f"{Fore.YELLOW}[!] Please load a puzzle first (option 1).{Style.RESET_ALL}")
                continue
            if engine.is_solved():
                print(f"{Fore.GREEN}Puzzle is already completely solved!{Style.RESET_ALL}")
                continue

            cid = input(
                f"Enter unresolved cell ID ({', '.join(engine.get_unresolved_cells())}): "
            ).strip().upper()
            if not cid:
                continue
            raw_verdict = input("Verdict — [C]riminal or [I]nnocent: ").strip()
            verdict = _parse_cli_verdict(raw_verdict)
            if verdict is None:
                print(
                    f"{Fore.RED}[!] Invalid verdict {raw_verdict!r}; enter C (CRIMINAL) or I (INNOCENT).{Style.RESET_ALL}"
                )
                continue

            try:
                outcome = engine.submit_verdict(cid, verdict)
            except ValueError as exc:
                print(f"{Fore.RED}[!] {exc}{Style.RESET_ALL}")
                continue

            cell = engine.puzzle.grid.get_cell_by_id(cid)
            char_name = cell.character_name if cell else cid

            if outcome == Verdict.ACCEPTED:
                clue_desc = cell.clue.description if (cell and cell.clue) else None
                print(
                    f"{Fore.GREEN}{Style.BRIGHT}[ACCEPTED]{Style.RESET_ALL} "
                    f"{char_name} ({cid}) is proven {verdict.name}!"
                )
                if clue_desc:
                    print(f'  Newly revealed clue: "{clue_desc}"')
                _print_public_board(
                    engine,
                    puzzle_label=current_label,
                    highlighted_cells=highlighted_cells,
                    highlight_source=highlight_source,
                )
                if engine.is_solved():
                    print(
                        f"\n{Fore.GREEN}{Style.BRIGHT}Congratulations! Puzzle solved with zero guessing!{Style.RESET_ALL}"
                    )
            elif outcome == Verdict.NOT_PROVABLE:
                print(
                    f"{Fore.YELLOW}[NOT PROVABLE]{Style.RESET_ALL} "
                    f"{char_name} ({cid}) cannot yet be logically proven {verdict.name} "
                    "from public clues. Guessing is not allowed!"
                )
            elif outcome == Verdict.CONTRADICTED:
                print(
                    f"{Fore.RED}[CONTRADICTED]{Style.RESET_ALL} "
                    f"Calling {char_name} ({cid}) {verdict.name} contradicts the solution. "
                    "Card remains face-down."
                )
            else:
                print(
                    f"{Fore.RED}[{outcome.name}]{Style.RESET_ALL} "
                    f"Knowledge base inconsistency detected at {cid}."
                )

        elif choice == "5":
            if engine is None:
                print(f"{Fore.YELLOW}[!] Please load a puzzle first (option 1).{Style.RESET_ALL}")
                continue
            if engine.is_solved():
                print(f"{Fore.GREEN}Puzzle is already solved!{Style.RESET_ALL}")
                continue

            kb = engine.build_public_kb()
            unresolved_cells = [
                c
                for c in engine.puzzle.grid.get_all_cells()
                if c.cell_id not in engine.verdicts
            ]
            active_clues = [clue for _, clue in engine.get_revealed_clues()]
            hinter = HintProvider(
                EntailmentChecker(
                    DPLL(timeout_seconds=float(MAX_SOLVER_TIMEOUT_SECONDS))
                )
            )
            hint = hinter.get_hint(kb, unresolved_cells, active_clues)

            if hint is None:
                print(
                    f"{Fore.YELLOW}[Hint] No unresolved character is currently forced "
                    "from revealed clues (deadlock / ambiguous state).{Style.RESET_ALL}"
                )
            else:
                target_cid, forced_verdict, clue_desc = hint
                target_cell = engine.puzzle.grid.get_cell_by_id(target_cid)
                char_name = target_cell.character_name if target_cell else target_cid

                # Locate a supporting revealed clue for board highlighting
                src_cid: Optional[str] = None
                refs: Set[str] = {target_cid}
                for rev_cid, rev_clue in engine.get_revealed_clues():
                    cand_refs = ClueHighlighter.get_referenced_cells(
                        rev_clue, engine.puzzle.grid
                    )
                    if target_cid in cand_refs:
                        src_cid = rev_cid
                        refs = cand_refs | {target_cid}
                        if not clue_desc:
                            clue_desc = rev_clue.description
                        break

                highlighted_cells = refs
                highlight_source = src_cid
                print(
                    f"\n{Fore.CYAN}{Style.BRIGHT}[Hint]{Style.RESET_ALL} "
                    f"{char_name} ({target_cid}) can be logically proven "
                    f"{Style.BRIGHT}{forced_verdict.name}{Style.RESET_ALL}."
                )
                if clue_desc:
                    origin = f" ({src_cid})" if src_cid else ""
                    print(f'  Relevant clue{origin}: "{clue_desc}"')

        elif choice == "6":
            if engine is None or cli_agent is None:
                print(f"{Fore.YELLOW}[!] Please load a puzzle first (option 1).{Style.RESET_ALL}")
                continue
            if engine.is_solved():
                print(f"{Fore.GREEN}Puzzle is already solved!{Style.RESET_ALL}")
                continue

            kb = engine.build_public_kb()
            step = cli_agent.step(engine, kb)
            if step is None:
                print(
                    f"{Fore.YELLOW}[Deadlock] No unresolved character can be deduced "
                    "without guessing.{Style.RESET_ALL}"
                )
            else:
                cli_agent.trace.add_step(step)
                print(
                    f"{Fore.GREEN}[Step {step.step_number}]{Style.RESET_ALL} "
                    f"Deduced {step.character_name} ({step.cell_id}) = "
                    f"{Style.BRIGHT}{step.verdict.name}{Style.RESET_ALL} "
                    f"({step.sat_queries_count} SAT queries)."
                )
                if step.newly_revealed_clue:
                    print(f'  Newly revealed clue: "{step.newly_revealed_clue}"')
                _print_public_board(
                    engine,
                    puzzle_label=current_label,
                    highlighted_cells=highlighted_cells,
                    highlight_source=highlight_source,
                )
                if engine.is_solved():
                    print(
                        f"\n{Fore.GREEN}{Style.BRIGHT}Puzzle solved completely with zero guessing!{Style.RESET_ALL}"
                    )

        elif choice == "7":
            if engine is None:
                print(f"{Fore.YELLOW}[!] Please load a puzzle first (option 1).{Style.RESET_ALL}")
                continue
            if engine.is_solved():
                print(f"{Fore.GREEN}Puzzle is already solved!{Style.RESET_ALL}")
                continue

            solver = DPLL(timeout_seconds=float(MAX_SOLVER_TIMEOUT_SECONDS))
            auto_agent = LogicAgent(solver=solver)
            trace = auto_agent.solve(engine)

            # Append newly executed auto-solve steps into session trace
            if cli_agent is not None:
                for step in trace.steps:
                    step.step_number = len(cli_agent.trace.steps) + 1
                    cli_agent.trace.add_step(step)

            print(f"\n{Fore.CYAN}{Style.BRIGHT}=== Deduction Trace ==={Style.RESET_ALL}")
            print(trace.format_table())
            _print_public_board(engine, puzzle_label=current_label)

            if engine.is_solved():
                print(
                    f"\n{Fore.GREEN}{Style.BRIGHT}Auto-solve complete! Solved in "
                    f"{len(trace.steps)} step(s) with zero guessing.{Style.RESET_ALL}"
                )
            else:
                remaining = ", ".join(engine.get_unresolved_cells())
                print(
                    f"\n{Fore.YELLOW}[Deadlock] Stopped after {len(trace.steps)} step(s). "
                    f"Unresolved cells: {remaining}{Style.RESET_ALL}"
                )

        elif choice == "8":
            if current_path is None:
                print(f"{Fore.YELLOW}[!] No puzzle loaded to restart.{Style.RESET_ALL}")
                continue
            _load_into_session(current_path)

        elif choice == "9":
            raw_dir = input(
                f"Enter puzzle directory [default: {PUZZLE_DIR}]: "
            ).strip()
            target_dir = raw_dir if raw_dir else str(PUZZLE_DIR)
            try:
                _run_experiments(target_dir)
            except (FileNotFoundError, ValueError) as exc:
                print(f"{Fore.RED}[Error] {exc}{Style.RESET_ALL}")

        else:
            print(f"{Fore.YELLOW}[!] Unknown option {choice!r}. Choose 0-9.{Style.RESET_ALL}")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Dispatch to the appropriate mode based on CLI arguments."""
    args = _parse_args()

    try:
        if args.gui:
            _run_gui(puzzle_path=args.puzzle)
        elif args.auto:
            _run_auto_solve(args.auto)
        elif args.experiment:
            _run_experiments(args.experiment)
        elif args.puzzle:
            _run_cli_menu(initial_puzzle_path=args.puzzle)
        else:
            _run_cli_menu()
    except (FileNotFoundError, ValueError) as exc:
        print(f"{Fore.RED}[Error] {exc}{Style.RESET_ALL}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
