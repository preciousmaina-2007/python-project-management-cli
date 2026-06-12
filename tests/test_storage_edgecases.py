import json
from pathlib import Path

import pytest

from project_manager.services.storage import Storage, DatabaseCorruptionError


def test_load_users_malformed_json_raises(tmp_path: Path):
    db = tmp_path / "db.json"
    db.parent.mkdir(parents=True, exist_ok=True)
    with open(db, "w", encoding="utf-8") as f:
        f.write("{ invalid json }")

    storage = Storage(db)
    with pytest.raises(DatabaseCorruptionError):
        storage.load_users()


def test_validate_database_structure_accepts_minimal(tmp_path: Path):
    db = tmp_path / "db.json"
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_text(json.dumps({"users": []}))
    storage = Storage(db)
    # Should not raise
    storage.validate_database_structure({"users": []})
