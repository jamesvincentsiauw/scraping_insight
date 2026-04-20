"""
Persist and load benchmark results, grouped by target label.

Folder structure after a run:
    results/
    ├── httpbin-get/
    │   ├── run_20260420_123456.json
    │   └── run_20260421_094532.json
    ├── sae-advanced-tech/
    │   └── run_20260420_123456.json
    └── ...

Each per-target file contains results from all vendors for that target in
that run — sorted by vendor name for easy side-by-side comparison:
    {
      "run_id":  "20260420_123456",
      "label":   "httpbin-get",
      "url":     "https://httpbin.org/get",
      "results": [ {vendor, success, response_time_ms, ...}, ... ]
    }

load_all_runs() and load_latest_run() still return a flat list[dict] so the
dashboard and PDF exporter need no changes.

Legacy flat run_*.json files in the results root are still loaded for
backwards compatibility.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import RESULTS_DIR


def _results_root() -> Path:
    path = Path(RESULTS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── Save ─────────────────────────────────────────────────────────────────────

def save_run(results: list[dict]) -> str:
    """
    Save results grouped into per-target subfolders.
    Returns the results root directory path.
    """
    root = _results_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Group by label (fall back to a slug of the URL if label is missing)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        label = r.get("label") or _url_to_label(r.get("url", "unknown"))
        grouped[label].append(r)

    for label, vendor_results in grouped.items():
        # Sanitise label for use as a directory name
        safe_label = _safe_dirname(label)
        target_dir = root / safe_label
        target_dir.mkdir(exist_ok=True)

        # Sort vendors alphabetically so diffs are stable
        vendor_results.sort(key=lambda x: x.get("vendor", ""))

        payload = {
            "run_id": ts,
            "label": label,
            "url": vendor_results[0].get("url", ""),
            "results": vendor_results,
        }
        out_file = target_dir / f"run_{ts}.json"
        with open(out_file, "w") as f:
            json.dump(payload, f, indent=2)

    return str(root)


# ── Load ──────────────────────────────────────────────────────────────────────

def _iter_target_files(root: Path):
    """Yield all per-target run files (new format) under root."""
    for target_dir in sorted(root.iterdir()):
        if target_dir.is_dir():
            for run_file in sorted(target_dir.glob("run_*.json")):
                yield run_file


def _flatten(data: dict | list) -> list[dict]:
    """Normalise both old flat list format and new grouped dict format."""
    if isinstance(data, list):
        return data  # legacy flat format
    # New format: data["results"] is the list of per-vendor dicts
    label = data.get("label", "")
    url = data.get("url", "")
    rows = []
    for r in data.get("results", []):
        row = dict(r)
        row.setdefault("label", label)
        row.setdefault("url", url)
        rows.append(row)
    return rows


def load_all_runs() -> list[dict]:
    """Load every result (all targets, all runs) as a flat list."""
    root = _results_root()
    all_results: list[dict] = []

    # New per-target folder structure
    for path in _iter_target_files(root):
        try:
            with open(path) as f:
                all_results.extend(_flatten(json.load(f)))
        except (json.JSONDecodeError, OSError):
            continue

    # Legacy flat files in root
    for path in sorted(root.glob("run_*.json")):
        try:
            with open(path) as f:
                all_results.extend(_flatten(json.load(f)))
        except (json.JSONDecodeError, OSError):
            continue

    return all_results


def load_latest_run() -> list[dict]:
    """Load only the most recent run (by timestamp) across all target folders."""
    root = _results_root()

    # Collect all run files with their timestamps
    candidates: list[tuple[str, Path]] = []

    for path in _iter_target_files(root):
        # Extract timestamp from filename: run_YYYYMMDD_HHMMSS.json
        ts = path.stem.replace("run_", "")
        candidates.append((ts, path))

    for path in sorted(root.glob("run_*.json")):
        ts = path.stem.replace("run_", "")
        candidates.append((ts, path))

    if not candidates:
        return []

    latest_ts = max(ts for ts, _ in candidates)
    results: list[dict] = []
    for ts, path in candidates:
        if ts == latest_ts:
            try:
                with open(path) as f:
                    results.extend(_flatten(json.load(f)))
            except (json.JSONDecodeError, OSError):
                continue

    return results


def list_runs() -> list[str]:
    """Return sorted list of unique run IDs across all target folders."""
    root = _results_root()
    run_ids: set[str] = set()

    for path in _iter_target_files(root):
        run_ids.add(path.stem.replace("run_", ""))

    for path in root.glob("run_*.json"):
        run_ids.add(path.stem.replace("run_", ""))

    return sorted(run_ids)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_dirname(name: str) -> str:
    """Convert a label to a safe directory name."""
    import re
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name).strip("_") or "unknown"


def _url_to_label(url: str) -> str:
    """Derive a short label from a URL when no label is available."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    slug = parts[-1] if parts else parsed.netloc
    return slug[:40] or "unknown"
