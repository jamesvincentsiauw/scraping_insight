"""
Persist and load benchmark results as JSON files.

Each run is stored as a timestamped JSON file in the results/ directory.
The dashboard reads all files and aggregates them for historical trending.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

sys_path_hack = os.path.join(os.path.dirname(__file__), "..")
import sys

sys.path.insert(0, sys_path_hack)

from config import RESULTS_DIR


def _ensure_results_dir() -> Path:
    path = Path(RESULTS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_run(results: list[dict]) -> str:
    """Save a list of ScrapeResult dicts to a timestamped JSON file."""
    results_dir = _ensure_results_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = results_dir / f"run_{ts}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    return str(filename)


def load_all_runs() -> list[dict]:
    """Load and merge all run files from the results directory."""
    results_dir = _ensure_results_dir()
    all_results: list[dict] = []
    for path in sorted(results_dir.glob("run_*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
                all_results.extend(data)
        except (json.JSONDecodeError, OSError):
            continue
    return all_results


def load_latest_run() -> list[dict]:
    """Load only the most recent run file."""
    results_dir = _ensure_results_dir()
    files = sorted(results_dir.glob("run_*.json"))
    if not files:
        return []
    with open(files[-1]) as f:
        return json.load(f)


def list_runs() -> list[str]:
    """Return sorted list of run file names."""
    results_dir = _ensure_results_dir()
    return [p.name for p in sorted(results_dir.glob("run_*.json"))]
