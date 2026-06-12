import pytest
from project_manager.models.task import (
    Task,
    EmptyTitleError,
    EmptyContributorError,
    ContributorNotFoundError,
)

def test_task_creation_and_properties():
    """Verify task properties are correctly set up on initialization."""
    task = Task(title=" Write Docs ", completed=False, contributors=["Alice"])
    assert task.title == "Write Docs"
    assert task.completed is False
    assert len(task.contributors) == 1
    assert task.contributors[0].name == "Alice"

def test_task_invalid_types_raise_error():
    """Verify improper input types raise a TypeError."""
    with pytest.raises(TypeError):
        Task(title=123)  
    with pytest.raises(TypeError):
        Task(title="Valid", completed="NotABool") 

def test_task_empty_title_raises_error():
    """Verify empty or space-only titles reject construction."""
    with pytest.raises(EmptyTitleError):
        Task(title="")
    with pytest.raises(EmptyTitleError):
        Task(title="   ")

def test_task_mutations():
    """Verify completion markers and contributor management functions properly."""
    task = Task(title="Fix Bug")
    assert not task.completed
    
    task.mark_complete()
    assert task.completed

    task.add_contributor("Bob")
    assert task.contributors[0].name == "Bob"
    
    task.add_contributor("Bob")
    assert len(task.contributors) == 1

    task.remove_contributor("Bob")
    assert all(contributor.name != "Bob" for contributor in task.contributors)


def test_task_has_id_and_repr():
    task = Task(title="Fix Issue")
    assert isinstance(task.id, int)
    assert "Fix Issue" in repr(task)


def test_task_invalid_contributor_actions():
    """Verify safety limits for contributor assignments."""
    task = Task(title="Task")
    with pytest.raises(EmptyContributorError):
        task.add_contributor("  ")
    with pytest.raises(ContributorNotFoundError):
        task.remove_contributor("Fake User")
