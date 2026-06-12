from __future__ import annotations

from typing import Any
from datetime import date

from .task import Task


class DuplicateTaskError(ValueError):
    """Raised when attempting to add a task with a title that already exists in the project."""


class TaskNotFoundError(ValueError):
    """Raised when a requested task is not found in the project."""


class EmptyProjectTitleError(ValueError):
    """Raised when a project title is empty or contains only whitespace."""


class InvalidProjectStatusError(ValueError):
    """Raised when a project status is not supported."""


class Project:
    """Represents a project that owns a collection of tasks and metadata."""

    VALID_STATUSES = {"planned", "active", "completed"}
    _id_counter = 1

    def __init__(
        self,
        title: str,
        description: str | None = None,
        status: str | None = None,
        due_date: str | None = None,
        tasks: list[Task] | None = None,
        id: int | None = None,
    ) -> None:
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")
        stripped_title = title.strip()
        if not stripped_title:
            raise EmptyProjectTitleError("Project title cannot be empty or contain only whitespace.")

        self._id: int = id if id is not None else self._generate_id()
        self._title: str = stripped_title
        self._description: str = self._validate_optional_string(description)
        self._status: str = self._validate_status(status)
        self._due_date: str | None = self._parse_due_date(due_date)
        self._tasks: list[Task] = []

        if tasks is not None:
            if not isinstance(tasks, list):
                raise TypeError(f"tasks must be a list of Task instances, got {type(tasks).__name__}")
            for task in tasks:
                self.add_task(task)

    @classmethod
    def _generate_id(cls) -> int:
        id_ = cls._id_counter
        cls._id_counter += 1
        return id_

    @property
    def id(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return f"<Project id={self._id} title={self._title!r} status={self._status!r}>"

    def __str__(self) -> str:
        return f"{self._title} [{self._status}]"

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> str:
        return self._status

    @property
    def due_date(self) -> str | None:
        return self._due_date

    @property
    def tasks(self) -> list[Task]:
        return self._tasks.copy()

    def rename(self, new_title: str) -> None:
        """Rename the project title."""
        if not isinstance(new_title, str):
            raise TypeError(f"title must be a string, got {type(new_title).__name__}")
        stripped_title = new_title.strip()
        if not stripped_title:
            raise EmptyProjectTitleError("Project title cannot be empty or contain only whitespace.")
        self._title = stripped_title

    def set_description(self, description: str | None) -> None:
        self._description = self._validate_optional_string(description)

    def set_status(self, status: str | None) -> None:
        self._status = self._validate_status(status)

    def add_task(self, task: Task) -> None:
        """Add a task to the project.

        Args:
            task: The Task instance to add.

        Raises:
            TypeError: If task is not a Task instance.
            DuplicateTaskError: If a task with the same title already exists.
        """
        if not isinstance(task, Task):
            raise TypeError(f"task must be a Task instance, got {type(task).__name__}")

        if self._find_task_index(task.title) is not None:
            raise DuplicateTaskError(
                f"Task with title '{task.title}' already exists in project '{self._title}'."
            )

        self._tasks.append(task)

    def get_task(self, title: str) -> Task:
        """Retrieve a task by title.

        Args:
            title: The title of the task to retrieve.

        Returns:
            The matching Task instance.

        Raises:
            TypeError: If title is not a string.
            TaskNotFoundError: If no task with the given title exists.
        """
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")

        index = self._find_task_index(title)
        if index is None:
            raise TaskNotFoundError(
                f"Task with title '{title.strip()}' not found in project '{self._title}'."
            )

        return self._tasks[index]

    def remove_task(self, title: str) -> None:
        """Remove a task by title.

        Args:
            title: The title of the task to remove.

        Raises:
            TypeError: If title is not a string.
            TaskNotFoundError: If no task with the given title exists.
        """
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")

        index = self._find_task_index(title)
        if index is None:
            raise TaskNotFoundError(
                f"Task with title '{title.strip()}' not found in project '{self._title}'."
            )

        del self._tasks[index]

    def list_tasks(self) -> list[Task]:
        """Return a list of all tasks in the project."""
        return self._tasks.copy()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the project to a JSON-serializable dictionary."""
        return {
            "id": self._id,
            "title": self._title,
            "description": self._description,
            "status": self._status,
            "due_date": self._due_date,
            "tasks": [task.to_dict() for task in self._tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        """Reconstruct a Project instance from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        title = data.get("title")
        if title is None:
            raise KeyError("Missing required key: 'title'")

        description = data.get("description")
        status = data.get("status")
        due_date = data.get("due_date")
        project_id = data.get("id")
        tasks_data = data.get("tasks", [])
        if not isinstance(tasks_data, list):
            raise TypeError(f"'tasks' must be a list, got {type(tasks_data).__name__}")

        tasks: list[Task] = []
        for task_data in tasks_data:
            if not isinstance(task_data, dict):
                raise TypeError(f"Each task must be a dict, got {type(task_data).__name__}")
            tasks.append(Task.from_dict(task_data))

        return cls(title=title, description=description, status=status, due_date=due_date, tasks=tasks, id=project_id)

    def set_due_date(self, due_date: str | None) -> None:
        self._due_date = self._parse_due_date(due_date)

    def _parse_due_date(self, due_date: str | None) -> str | None:
        if due_date is None or due_date == "":
            return None
        if not isinstance(due_date, str):
            raise TypeError(f"due_date must be a string, got {type(due_date).__name__}")
        try:
            return date.fromisoformat(due_date.strip()).isoformat()
        except ValueError as exc:
            raise ValueError("due_date must be in YYYY-MM-DD format.") from exc

    def _find_task_index(self, title: str) -> int | None:
        """Find the index of a task by title, case-insensitive."""
        normalized = title.strip().lower()
        for index, task in enumerate(self._tasks):
            if task.title.lower() == normalized:
                return index
        return None

    @staticmethod
    def _validate_optional_string(value: str | None, default: str = "") -> str:
        if value is None:
            return default
        if not isinstance(value, str):
            raise TypeError(f"Value must be a string, got {type(value).__name__}")
        return value.strip()

    @classmethod
    def _validate_status(cls, status: str | None) -> str:
        normalized_status = cls._validate_optional_string(status, default="planned").lower()
        if normalized_status not in cls.VALID_STATUSES:
            raise InvalidProjectStatusError(
                f"Project status must be one of {sorted(cls.VALID_STATUSES)}, got '{status}'."
            )
        return normalized_status
