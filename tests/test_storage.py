import json
from pathlib import Path
import pytest

from project_manager.services.storage import Storage, DatabaseCorruptionError
from project_manager.models.user import User
from project_manager.models.project import Project
from project_manager.models.task import Task


def test_1_database_created_automatically(tmp_path: Path):
    """Test 1: Deleting the file or starting fresh creates database automatically."""
    db_file = tmp_path / "database.json"
    
    assert not db_file.exists()
    storage = Storage(db_file)
    assert db_file.exists()
    
    users = storage.load_users()
    assert users == []


def test_2_add_save_and_reload_user(tmp_path: Path):
    """Test 2: Save a user, reload it, and verify the data matches."""
    db_file = tmp_path / "database.json"
    storage = Storage(db_file)
    
    original_user = User(name="Emmanuel", email="emmanuel@example.com")
    storage.save_users([original_user])
    
    reloaded_storage = Storage(db_file)
    loaded_users = reloaded_storage.load_users()
    
    assert len(loaded_users) == 1
    assert loaded_users[0].name == original_user.name
    assert loaded_users[0].email == original_user.email


def test_3_nested_reconstruction(tmp_path: Path):
    """Test 3: Verify deep structures reconstruct into Objects, not dicts."""
    db_file = tmp_path / "database.json"
    storage = Storage(db_file)
    
    task = Task(title="Build CLI", completed=False, contributors=["Emmanuel"])
    project = Project(title="Python Tool", tasks=[task])
    user = User(name="Emmanuel", projects=[project])
    
    storage.save_users([user])
    
    loaded_users = storage.load_users()
    loaded_user = loaded_users[0]
    
    assert isinstance(loaded_user, User)
    
    loaded_project = loaded_user.projects[0]
    assert isinstance(loaded_project, Project)
    
    loaded_task = loaded_project.tasks[0]
    assert isinstance(loaded_task, Task)
    
    assert loaded_task.title == "Build CLI"
    assert any(contributor.name == "Emmanuel" for contributor in loaded_task.contributors)


def test_4_corrupt_json_raises_custom_exception(tmp_path: Path):
    """Test 4: Corrupt JSON triggers custom application exception, not raw traceback."""
    db_file = tmp_path / "database.json"
    storage = Storage(db_file)
    
    with open(db_file, "w", encoding="utf-8") as f:
        f.write("{ invalid")
        
    with pytest.raises(DatabaseCorruptionError) as exc_info:
        storage.load_users()
        
    assert "contains malformed JSON" in str(exc_info.value)
