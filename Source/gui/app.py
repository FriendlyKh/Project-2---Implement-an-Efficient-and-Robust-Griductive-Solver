# Owner: Person 1
"""
gui.app — Web Application Entry Point (Flask)
==============================================

Provides a modern web-based graphical interface for Griductive Solver.

Endpoints:
* ``GET  /``               — Main game page.
* ``GET  /api/state``      — Current public board state.
* ``POST /api/load``       — Load a puzzle JSON file.
* ``POST /api/restart``    — Restart the current puzzle.
* ``POST /api/verdict``    — Call a character CRIMINAL or INNOCENT.
* ``GET  /api/hint``       — Get a logical hint.
* ``POST /api/step``       — Advance solver by one step.
* ``POST /api/auto``       — Run solver to completion.
* ``POST /api/highlight``  — Get highlighted cell IDs for a selected clue.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request

from gui.controls import GameController


def create_app(controller: GameController | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        controller: Optional pre-configured GameController instance.

    Returns:
        Configured Flask application.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    ctrl = controller or GameController()

    @app.route("/")
    def index():
        """Render main interactive interface."""
        return render_template("index.html")

    @app.route("/api/state", methods=["GET"])
    def get_state():
        """Retrieve current public game board state."""
        # TODO: Return serialized public state via ctrl.board_view
        return jsonify({"status": "ok", "message": "TODO: implement state endpoint"})

    @app.route("/api/load", methods=["POST"])
    def load():
        """Load a selected puzzle file."""
        data = request.get_json() or {}
        puzzle_path = data.get("puzzle_path", "")
        # TODO: Call ctrl.load_puzzle(puzzle_path)
        return jsonify({"status": "ok", "message": f"TODO: load {puzzle_path}"})

    @app.route("/api/restart", methods=["POST"])
    def restart():
        """Restart puzzle to initial state."""
        # TODO: Call ctrl.restart()
        return jsonify({"status": "ok", "message": "TODO: restart"})

    @app.route("/api/verdict", methods=["POST"])
    def verdict():
        """Submit a user verdict."""
        data = request.get_json() or {}
        cell_id = data.get("cell_id")
        call = data.get("verdict")  # 'CRIMINAL' or 'INNOCENT'
        # TODO: Call ctrl.submit_verdict(cell_id, call)
        return jsonify({"status": "ok", "message": f"TODO: submit {call} for {cell_id}"})

    @app.route("/api/hint", methods=["GET"])
    def hint():
        """Request a hint."""
        # TODO: Call ctrl.get_hint()
        return jsonify({"status": "ok", "message": "TODO: hint"})

    @app.route("/api/step", methods=["POST"])
    def step():
        """Execute one auto-solve step."""
        # TODO: Call ctrl.auto_solve_step()
        return jsonify({"status": "ok", "message": "TODO: step"})

    @app.route("/api/auto", methods=["POST"])
    def auto_solve():
        """Execute complete auto-solve."""
        # TODO: Call ctrl.auto_solve_all()
        return jsonify({"status": "ok", "message": "TODO: auto"})

    @app.route("/api/highlight", methods=["POST"])
    def highlight():
        """Compute highlighted cells for a selected clue."""
        data = request.get_json() or {}
        clue_id = data.get("clue_id")
        # TODO: Use ClueHighlighter to return list of cell IDs
        return jsonify({"cells": []})

    return app


def launch_gui(host: str = "127.0.0.1", port: int = 5000, debug: bool = True) -> None:
    """Start the GUI web server.

    Args:
        host: Interface to bind.
        port: Port number.
        debug: Run in debug mode.
    """
    app = create_app()
    print(f"\n[GUI] Starting Griductive web interface at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
