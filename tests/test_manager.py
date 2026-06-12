import pytest
from pathlib import Path
from project_manager.services.storage import Storage
from project_manager.services.manager import (
    Manager,
    DuplicateUserError,
    UserNotFoundError,
    TaskAlreadyCompletedError,
)
from project_manager.models.user import User, DuplicateProjectError, ProjectNotFoundError
from project_manager.models.project import Project, DuplicateTaskError, TaskNotFoundError
from project_manager.models.task import Task, ContributorNotFoundError


@pytest.fixture
def db_setup(tmp_path: Path):
    """Fixture to provide a reusable database path and storage instance."""
    db_file = tmp_path / "database.json"
    storage = Storage(db_file)
    return db_file, storage


@pytest.fixture
def manager(db_setup) -> Manager:
    """Fixture to provide a clean Manager instance linked to a temporary database."""
    _, storage = db_setup
    return Manager(storage)


def test_add_user(manager: Manager):
    """Verify adding users works and prevents duplicates."""
    user = manager.add_user("Emmanuel", "emmanuel@example.com")
    assert user.name == "Emmanuel"
    assert user.email == "emmanuel@example.com"
    assert len(manager.list_users()) == 1
    
    with pytest.raises(DuplicateUserError):
        manager.add_user("emmanuel")


def test_remove_user(manager: Manager):
    """Verify removing users mutates state cleanly."""
    manager.add_user("Emmanuel")
    manager.remove_user("Emmanuel")
    assert len(manager.list_users()) == 0
    
    with pytest.raises(UserNotFoundError):
        manager.remove_user("NonExistent")


def test_add_project(manager: Manager):
    """Verify projects are added correctly to specific users."""
    manager.add_user("Emmanuel")
    project = manager.add_project("Emmanuel", "CLI Tool")
    assert project.title == "CLI Tool"
    assert len(manager.list_projects("Emmanuel")) == 1
    
    with pytest.raises(DuplicateProjectError):
        manager.add_project("Emmanuel", "cli tool")


def test_search_projects(manager: Manager):
    """Verify project search returns matching titles for a user."""
    manager.add_user("Emmanuel")
    manager.add_project("Emmanuel", "CLI Tool")
    manager.add_project("Emmanuel", "Core Engine")
    results = manager.search_projects("Emmanuel", "cli")
    assert len(results) == 1
    assert results[0].title == "CLI Tool"

    no_results = manager.search_projects("Emmanuel", "missing")
    assert no_results == []


def test_remove_project(manager: Manager):
    """Verify projects are cleanly deleted from user profiles."""
    manager.add_user("Emmanuel")
    manager.add_project("Emmanuel", "CLI Tool")
    manager.remove_project("Emmanuel", "CLI Tool")
    assert len(manager.list_projects("Emmanuel")) == 0
    
    with pytest.raises(ProjectNotFoundError):
        manager.remove_project("Emmanuel", "CLI Tool")


def test_add_task(manager: Manager):
    """Verify tasks register safely within parent projects."""
    manager.add_user("Emmanuel")
    manager.add_project("Emmanuel", "CLI Tool")
    task = manager.add_task("Emmanuel", "CLI Tool", "Write Tests")
    assert task.title == "Write Tests"
    assert not task.completed
    
    with pytest.raises(DuplicateTaskError):
        manager.add_task("Emmanuel", "CLI Tool", "Write Tests")


def test_complete_task(manager: Manager):
    """Verify tasks flip completion bits and handle multi-completion rejections."""
    manager.add_user("Emmanuel")
    manager.add_project("Emmanuel", "CLI Tool")
    manager.add_task("Emmanuel", "CLI Tool", "Write Tests")
    
    manager.complete_task("Emmanuel", "CLI Tool", "Write Tests")
    tasks = manager.list_tasks("Emmanuel", "CLI Tool")
    
    target_task = next(t for t in tasks if t.title == "Write Tests")
    assert target_task.completed is True
    
    with pytest.raises(TaskAlreadyCompletedError):
        manager.complete_task("Emmanuel", "CLI Tool", "Write Tests")


def test_remove_task(manager: Manager):
    """Verify task removal from project scopes via Manager proxies."""
    manager.add_user("Emmanuel")
    project = manager.add_project("Emmanuel", "CLI Tool")
    manager.add_task("Emmanuel", "CLI Tool", "Write Tests")
    
    project.remove_task("Write Tests")
    assert len(project.list_tasks()) == 0


def test_add_contributor(manager: Manager):
    """Verify contributor registration on nested tasks."""
    manager.add_user("Emmanuel")
    manager.add_project("Emmanuel", "CLI Tool")
    manager.add_task("Emmanuel", "CLI Tool", "Write Tests")
    
    manager.add_task_contributor("Emmanuel", "CLI Tool", "Write Tests", "Annette")
    tasks = manager.list_tasks("Emmanuel", "CLI Tool")
    target_task = next(t for t in tasks if t.title == "Write Tests")
    assert any(contributor.name == "Annette" for contributor in target_task.contributors)


def test_remove_contributor(manager: Manager):
    """Verify tracking removals for assigned task contributors."""
    manager.add_user("Emmanuel")
    project = manager.add_project("Emmanuel", "CLI Tool")
    manager.add_task("Emmanuel", "CLI Tool", "Write Tests")
    manager.add_task_contributor("Emmanuel", "CLI Tool", "Write Tests", "Annette")
    
    task = project.get_task("Write Tests")
    task.remove_contributor("Annette")
    assert all(contributor.name != "Annette" for contributor in task.contributors)


def test_persistence_roundtrip(db_setup):
    """Verify disk synchronization across multiple separate manager sessions."""
    db_file, storage = db_setup
    
    manager_1 = Manager(storage)
    manager_1.add_user("Emmanuel")
    manager_1.add_project("Emmanuel", "CLI Tool")
    manager_1.add_task("Emmanuel", "CLI Tool", "Write Tests")
    manager_1.add_task_contributor("Emmanuel", "CLI Tool", "Write Tests", "Annette")
    
    fresh_storage = Storage(db_file)
    manager_2 = Manager(fresh_storage)
    
    assert len(manager_2.list_users()) == 1
    recovered_project = manager_2.get_project("Emmanuel", "CLI Tool")
    recovered_task = recovered_project.get_task("Write Tests")
    
    assert recovered_task.title == "Write Tests"
    assert any(contributor.name == "Annette" for contributor in recovered_task.contributors)
