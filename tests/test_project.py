from project_tracker.models.project import Project


def test_project_creation_and_add_task():
    p = Project(title="Proj", description="Desc", due_date="2026-01-01")
    assert p.tasks == []
    p.add_task(5)
    p.add_task(5)
    assert p.tasks == [5]


def test_due_date_validation():
    try:
        Project(title="Proj", description="Desc", due_date="01-01-2026")
    except ValueError as e:
        assert "YYYY-MM-DD" in str(e)
    else:
        assert False, "Expected ValueError"

