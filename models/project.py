"""Project model module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Project:
    """Represents a project.

    Attributes:
        id: Unique project ID.
        title: Project title.
        description: Project description.
        due_date: Due date as an ISO-8601 date string (YYYY-MM-DD).
        tasks: List of task IDs attached to the project.
    """

    _id_counter: int = 1

    id: int = field(init=False)
    title: str = ""
    description: str = ""
    due_date: str = ""
    tasks: List[int] = field(default_factory=list)

    def __init__(
        self,
        title: str,
        description: str,
        due_date: str,
        tasks: Optional[List[int]] = None,
        id: Optional[int] = None,
    ) -> None:
        if id is not None:
            self.id = int(id)
            Project._id_counter = max(Project._id_counter, self.id + 1)
        else:
            self.id = Project._id_counter
            Project._id_counter += 1

        self.title = title
        self.description = description
        self.due_date = self._validate_due_date(due_date)
        self.tasks = list(tasks or [])

    @staticmethod
    def _validate_due_date(value: str) -> str:
        """Validate due_date as YYYY-MM-DD."""

        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("due-date must be in YYYY-MM-DD format") from exc
        return value

    def add_task(self, task_id: int) -> None:
        """Add a task ID to this project's task list."""

        if task_id not in self.tasks:
            self.tasks.append(task_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize project to dict."""

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "tasks": list(self.tasks),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create project from dict."""

        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            description=str(data.get("description", "")),
            due_date=str(data["due_date"]),
            tasks=list(data.get("tasks", [])),
        )

    def __str__(self) -> str:
        return f"Project(id={self.id}, title={self.title}, due_date={self.due_date})"

