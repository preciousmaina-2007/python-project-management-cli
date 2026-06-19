import json
from pathlib import Path

from project_tracker.utils import storage


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    db_file = tmp_path / "database.json"
    monkeypatch.setattr(storage, "DATA_PATH", db_file)

    data = storage.load_data()
    assert data["users"] == {}

    data["users"]["1"] = {"id": 1, "name": "A", "email": "a@example.com", "projects": []}
    storage.save_data(data)

    loaded = storage.load_data()
    assert loaded["users"]["1"]["email"] == "a@example.com"


def test_load_malformed_json(tmp_path, monkeypatch):
    db_file = tmp_path / "database.json"
    monkeypatch.setattr(storage, "DATA_PATH", db_file)

    db_file.write_text("{ bad json", encoding="utf-8")
    loaded = storage.load_data()
    assert loaded == {"users": {}, "projects": {}, "tasks": {}}

