import pytest

from pathlib import Path
from project_manager.services.storage import Storage
from project_manager.services.manager import Manager
from project_manager.models.user import InvalidEmailError


def test_add_user_with_invalid_email_raises(tmp_path: Path):
    db_file = tmp_path / "db.json"
    storage = Storage(db_file)
    manager = Manager(storage)

    with pytest.raises(InvalidEmailError):
        manager.add_user("Alex", "not-an-email")


def test_add_user_with_valid_email(tmp_path: Path):
    db_file = tmp_path / "db.json"
    storage = Storage(db_file)
    manager = Manager(storage)

    user = manager.add_user("Alex", "alex@example.com")
    assert user.email == "alex@example.com"
