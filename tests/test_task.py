from project_tracker.models.task import Task


def test_task_creation_and_completion():
    t = Task(title="Task", assigned_to=3)
    assert t.status == "pending"
    t.complete()
    assert t.status == "completed"

