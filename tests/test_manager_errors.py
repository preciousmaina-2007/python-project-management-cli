import pytest
from pathlib import Path

from project_manager.services.storage import Storage, InvalidInputError
from project_manager.services.manager import Manager, DuplicateUserError


def test_manager_add_duplicate_user_raises(tmp_path: Path):
    db = tmp_path / "db.json"
    storage = Storage(db)
    manager = Manager(storage)
    manager.add_user("DupUser")
    with pytest.raises(DuplicateUserError):
        manager.add_user("dupuser")


def test_storage_save_users_invalid_input(tmp_path: Path):
    db = tmp_path / "db.json"
    storage = Storage(db)
    with pytest.raises(InvalidInputError):
        storage.save_users("not-a-list")
