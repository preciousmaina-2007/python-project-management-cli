import pytest
from project_manager.models.task import Task
from project_manager.models.project import (
    Project,
    DuplicateTaskError,
    TaskNotFoundError,
    EmptyProjectTitleError,
)

def test_project_creation_and_tasks():
    """Verify projects initialize with text formatting and optional tasks."""
    task = Task(title="Task 1")
    project = Project(title="  Alpha Project  ", tasks=[task])
    
    assert project.title == "Alpha Project"
    assert len(project.tasks) == 1

def test_project_empty_title_raises_error():
    """Verify empty project names are caught immediately."""
    with pytest.raises(EmptyProjectTitleError):
        Project(title="   ")

def test_project_task_operations():
    """Verify CRUD updates for tasks within a project instance."""
    project = Project(title="Beta Project")
    task = Task(title="Unique Task")
    
    project.add_task(task)
    assert project.get_task("Unique Task").title == "Unique Task"
    
    assert project.get_task("unique task").title == "Unique Task"
    
    duplicate_task = Task(title="UNIQUE TASK")
    with pytest.raises(DuplicateTaskError):
        project.add_task(duplicate_task)

    project.remove_task("unique task")
    assert len(project.list_tasks()) == 0
    
    with pytest.raises(TaskNotFoundError):
        project.get_task("Unique Task")


def test_project_has_id_and_repr():
    project = Project(title="Alpha")
    assert isinstance(project.id, int)
    assert "Alpha" in repr(project)
