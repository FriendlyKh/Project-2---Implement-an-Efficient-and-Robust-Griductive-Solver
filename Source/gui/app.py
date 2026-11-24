# Owner: Person 1
"""
gui.app — Web Application Entry Point (Flask)
==============================================

Provides a modern web-based graphical interface for Griductive Solver.

Endpoints:
* ``GET  /``               — Main game page.
* ``GET  /api/puzzles``    — List available puzzle JSON files.
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
from typing import Optional

from flask import Flask, jsonify, render_template, request

from gui.controls import GameController


def create_app(controller: Optional[GameController] = None) -> Flask:
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

    @app.route("/api/puzzles", methods=["GET"])
    def list_puzzles():
        """Return available puzzle files."""
        return jsonify({"status": "ok", "puzzles": ctrl.list_available_puzzles()})

    @app.route("/api/state", methods=["GET"])
    def get_state():
        """Retrieve current public game board state."""
        return jsonify(ctrl.get_state())

    @app.route("/api/load", methods=["POST"])
    def load():
        """Load a selected puzzle file."""
        data = request.get_json(silent=True) or {}
        puzzle_path = data.get("puzzle_path", "")
        if not puzzle_path:
            return jsonify({"status": "error", "message": "Missing 'puzzle_path'"}), 400
        try:
            return jsonify(ctrl.load_puzzle(puzzle_path))
        except FileNotFoundError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 404
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/api/restart", methods=["POST"])
    def restart():
        """Restart puzzle to initial state."""
        try:
            return jsonify(ctrl.restart())
        except RuntimeError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/api/verdict", methods=["POST"])
    def verdict():
        """Submit a user verdict."""
        data = request.get_json(silent=True) or {}
        cell_id = data.get("cell_id")
        call = data.get("verdict")  # 'CRIMINAL' or 'INNOCENT'
        try:
            return jsonify(ctrl.submit_verdict(cell_id, call))
        except (ValueError, RuntimeError) as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/api/hint", methods=["GET"])
    def hint():
        """Request a deductive hint."""
        try:
            return jsonify(ctrl.get_hint())
        except RuntimeError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/api/step", methods=["POST"])
    def step():
        """Execute one auto-solve step."""
        try:
            return jsonify(ctrl.auto_solve_step())
        except RuntimeError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/api/auto", methods=["POST"])
    def auto_solve():
        """Execute complete auto-solve."""
        try:
            return jsonify(ctrl.auto_solve_all())
        except RuntimeError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.route("/api/highlight", methods=["POST"])
    def highlight():
        """Compute highlighted cells for a selected revealed clue."""
        data = request.get_json(silent=True) or {}
        cell_id = data.get("cell_id") or data.get("clue_id")
        try:
            return jsonify(ctrl.highlight_clue(cell_id))
        except (ValueError, RuntimeError) as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

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
