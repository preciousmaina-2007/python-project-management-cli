"""Storage utilities for JSON persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "database.json"


def _default_db() -> Dict[str, Any]:
    return {"users": {}, "projects": {}, "tasks": {}}


def load_data() -> Dict[str, Any]:
    """Load JSON data from :data:`~project_tracker.utils.storage.DATA_PATH`.

    Returns a dict with keys: users, projects, tasks.

    If the file does not exist, it is created.
    If the JSON is malformed, a safe empty DB is returned.
    """

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text(json.dumps(_default_db(), indent=2), encoding="utf-8")
        return _default_db()

    try:
        raw = DATA_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return _default_db()
        data.setdefault("users", {})
        data.setdefault("projects", {})
        data.setdefault("tasks", {})
        return data
    except (json.JSONDecodeError, OSError):
        # Safe fallback on malformed JSON or read failure.
        return _default_db()


def save_data(data: Dict[str, Any]) -> None:
    """Persist JSON data to :data:`~project_tracker.utils.storage.DATA_PATH`."""

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    to_save = {
        "users": data.get("users", {}),
        "projects": data.get("projects", {}),
        "tasks": data.get("tasks", {}),
    }
    DATA_PATH.write_text(json.dumps(to_save, indent=2), encoding="utf-8")

