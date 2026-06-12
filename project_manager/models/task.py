from __future__ import annotations

from datetime import date
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from project_manager.models.user import User


class EmptyTitleError(ValueError):
    """Raised when a task title is empty or contains only whitespace."""


class EmptyContributorError(ValueError):
    """Raised when a contributor name is empty or contains only whitespace."""


class ContributorNotFoundError(ValueError):
    """Raised when a contributor is not found on the task."""


class Task:
    """Represents a project task with rich metadata, status, and contributors."""

    _id_counter = 1

    def __init__(
        self,
        title: str,
        completed: bool = False,
        description: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
        contributors: list[User | str] | None = None,
        id: int | None = None,
    ) -> None:
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")

        stripped_title = title.strip()
        if not stripped_title:
            raise EmptyTitleError("Task title cannot be empty or contain only whitespace.")

        if not isinstance(completed, bool):
            raise TypeError(f"completed must be a bool, got {type(completed).__name__}")

        self._id: int = id if id is not None else self._generate_id()
        self._title: str = stripped_title
        self._completed: bool = completed
        self._description: str = self._validate_optional_string(description)
        self._due_date: str | None = self._parse_due_date(due_date)
        self._priority: str = self._validate_optional_string(priority, default="normal")
        self._assigned_to: str = self._validate_optional_string(assigned_to)
        self._contributors: list[User] = []

        if contributors is not None:
            self._validate_contributors(contributors)

    @classmethod
    def _generate_id(cls) -> int:
        id_ = cls._id_counter
        cls._id_counter += 1
        return id_

    @property
    def id(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return (f"<Task id={self._id} title={self._title!r} completed={self._completed} "
                f"assigned_to={self._assigned_to!r}>")

    def __str__(self) -> str:
        status = "Done" if self._completed else "Pending"
        assigned = self._assigned_to or "unassigned"
        return f"{self._title} ({status}, assigned to {assigned})"

    @property
    def title(self) -> str:
        return self._title

    @property
    def completed(self) -> bool:
        return self._completed

    @property
    def description(self) -> str:
        return self._description

    @property
    def due_date(self) -> str | None:
        return self._due_date

    @property
    def priority(self) -> str:
        return self._priority

    @property
    def assigned_to(self) -> str:
        return self._assigned_to

    @property
    def contributors(self) -> list[User]:
        return self._contributors.copy()

    @property
    def contributor_names(self) -> list[str]:
        return [user.name for user in self._contributors]

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self._completed = True

    def rename(self, new_title: str) -> None:
        """Rename the task title."""
        if not isinstance(new_title, str):
            raise TypeError(f"title must be a string, got {type(new_title).__name__}")

        stripped_title = new_title.strip()
        if not stripped_title:
            raise EmptyTitleError("Task title cannot be empty or contain only whitespace.")

        self._title = stripped_title

    def set_description(self, description: str | None) -> None:
        self._description = self._validate_optional_string(description)

    def set_due_date(self, due_date: str | None) -> None:
        self._due_date = self._parse_due_date(due_date)

    def set_priority(self, priority: str | None) -> None:
        self._priority = self._validate_optional_string(priority, default="normal")

    def set_assigned_to(self, assigned_to: str | None) -> None:
        self._assigned_to = self._validate_optional_string(assigned_to)

    def add_contributor(self, user: User | str) -> None:
        """Add a contributor to the task.

        Args:
            user: The User instance or contributor name to add.

        Raises:
            TypeError: If user is not a User instance or string.
            EmptyContributorError: If the contributor name is empty.
        """
        from project_manager.models.user import User as UserType

        if isinstance(user, str):
            stripped_name = user.strip()
            if not stripped_name:
                raise EmptyContributorError("Contributor name cannot be empty or contain only whitespace.")
            user = UserType(stripped_name)
        elif not isinstance(user, UserType):
            raise TypeError(f"Contributor must be a User instance or name, got {type(user).__name__}")

        if self._find_contributor_index(user.name) is None:
            self._contributors.append(user)

    def remove_contributor(self, user: User | str) -> None:
        """Remove a contributor from the task."""
        if isinstance(user, str):
            stripped_name = user.strip()
            if not stripped_name:
                raise EmptyContributorError("Contributor name cannot be empty or contain only whitespace.")
            index = self._find_contributor_index(stripped_name)
        else:
            from project_manager.models.user import User as UserType
            if not isinstance(user, UserType):
                raise TypeError(f"Contributor must be a User instance or name, got {type(user).__name__}")
            index = self._find_contributor_index(user.name)

        if index is None:
            raise ContributorNotFoundError(f"Contributor '{user}' not found.")

        del self._contributors[index]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the task to a JSON-serializable dictionary."""
        return {
            "id": self._id,
            "title": self._title,
            "completed": self._completed,
            "description": self._description,
            "due_date": self._due_date,
            "priority": self._priority,
            "assigned_to": self._assigned_to,
            "contributors": self.contributor_names,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Reconstruct a Task instance from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        title = data.get("title")
        if title is None:
            raise KeyError("Missing required key: 'title'")

        completed = data.get("completed", False)
        if not isinstance(completed, bool):
            raise TypeError(f"'completed' must be a bool, got {type(completed).__name__}")

        description = data.get("description")
        due_date = data.get("due_date")
        priority = data.get("priority")
        assigned_to = data.get("assigned_to")
        task_id = data.get("id")
        contributors = data.get("contributors")
        if contributors is not None and not isinstance(contributors, list):
            raise TypeError(f"'contributors' must be a list, got {type(contributors).__name__}")

        return cls(
            title=title,
            completed=completed,
            description=description,
            due_date=due_date,
            priority=priority,
            assigned_to=assigned_to,
            contributors=contributors,
            id=task_id,
        )

    def _validate_optional_string(self, value: str | None, default: str = "") -> str:
        if value is None:
            return default
        if not isinstance(value, str):
            raise TypeError(f"Value must be a string, got {type(value).__name__}")
        return value.strip()

    def _parse_due_date(self, due_date: str | None) -> str | None:
        if due_date is None or due_date == "":
            return None
        if not isinstance(due_date, str):
            raise TypeError(f"due_date must be a string, got {type(due_date).__name__}")
        try:
            return date.fromisoformat(due_date.strip()).isoformat()
        except ValueError as exc:
            raise ValueError("due_date must be in YYYY-MM-DD format.") from exc

    def _validate_contributors(self, contributors: list[User | str]) -> None:
        if not isinstance(contributors, list):
            raise TypeError(f"contributors must be a list, got {type(contributors).__name__}")

        for contributor in contributors:
            self.add_contributor(contributor)

    def _find_contributor_index(self, name: str) -> int | None:
        from project_manager.models.user import User as UserType

        normalized_name = name.strip().lower()
        for index, contributor in enumerate(self._contributors):
            if isinstance(contributor, UserType):
                if contributor.name.lower() == normalized_name:
                    return index
            elif isinstance(contributor, str):
                if contributor.lower() == normalized_name:
                    return index
        return None
