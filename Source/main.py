# Owner: Team Lead
"""
Griductive Solver — Entry Point
================================

Launches the solver in one of several modes:

* Interactive CLI menu (default)
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
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    """Build and return the argument parser."""
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


def _run_cli_menu() -> None:
    """Interactive command-line menu."""
    # TODO: Implement interactive CLI menu
    #   1. Load puzzle
    #   2. Show grid
    #   3. Submit verdict
    #   4. Request hint
    #   5. Auto-solve
    #   6. Quit
    print("=" * 50)
    print("  Griductive Solver — Interactive CLI")
    print("=" * 50)
    print()
    print("  1. Load puzzle")
    print("  2. Show grid")
    print("  3. Submit verdict for a character")
    print("  4. Request hint")
    print("  5. Auto-solve")
    print("  6. Run experiments")
    print("  0. Quit")
    print()
    print("[!] This is a skeleton — menu actions are not yet implemented.")
    raise NotImplementedError("TODO: Implement interactive CLI menu loop")


def _run_auto_solve(puzzle_path: str) -> None:
    """Load a puzzle and run the logic agent to auto-solve it."""
    # TODO: Implement auto-solve flow
    #   1. Load puzzle via PuzzleLoader
    #   2. Create GameEngine
    #   3. Create LogicAgent
    #   4. Call agent.solve_puzzle(engine)
    #   5. Print deduction trace
    print(f"[Auto-Solve] Loading puzzle from: {puzzle_path}")
    raise NotImplementedError("TODO: Implement auto-solve flow")


def _run_gui() -> None:
    """Launch the Flask web GUI."""
    # TODO: Implement GUI launch
    #   1. Import gui.app
    #   2. Start Flask server
    print("[GUI] Starting Flask server…")
    raise NotImplementedError("TODO: Implement GUI launch")


def _run_experiments(puzzle_dir: str) -> None:
    """Run batch experiments across all puzzles in a directory."""
    # TODO: Implement experiment runner
    #   1. Import experiments.runner
    #   2. Call runner.run_all(puzzle_dir)
    #   3. Print results table
    print(f"[Experiments] Scanning puzzles in: {puzzle_dir}")
    raise NotImplementedError("TODO: Implement experiment runner invocation")


def main() -> None:
    """Dispatch to the appropriate mode based on CLI arguments."""
    args = _parse_args()

    if args.gui:
        _run_gui()
    elif args.auto:
        _run_auto_solve(args.auto)
    elif args.experiment:
        _run_experiments(args.experiment)
    elif args.puzzle:
        print(f"[CLI] Loading puzzle: {args.puzzle}")
        # TODO: Load puzzle then enter interactive menu
        raise NotImplementedError("TODO: Load puzzle and enter CLI menu")
    else:
        _run_cli_menu()


if __name__ == "__main__":
    main()
