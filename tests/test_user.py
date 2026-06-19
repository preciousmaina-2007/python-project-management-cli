from project_tracker.models.user import User
import pytest


def test_user_creation():
    u = User(name="Alice", email="alice@example.com")
    assert u.id >= 1
    assert u.name == "Alice"
    assert u.email == "alice@example.com"
    assert u.projects == []


def test_email_validation():
    with pytest.raises(ValueError):
        User(name="Bad", email="not-an-email")


def test_add_project():
    u = User(name="Bob", email="bob@example.com")
    u.add_project(10)
    u.add_project(10)
    assert u.projects == [10]

