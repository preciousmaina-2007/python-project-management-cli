"""Task model module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Task:
    """Represents a task.

    Attributes:
        id: Unique task ID.
        title: Task title.
        status: Status string (e.g., "pending" or "completed").
        assigned_to: Project ID the task belongs to.
    """

    _id_counter: int = 1

    id: int = field(init=False)
    title: str = ""
    status: str = "pending"
    assigned_to: int = -1

    def __init__(
        self,
        title: str,
        assigned_to: int,
        status: str = "pending",
        id: Optional[int] = None,
    ) -> None:
        if id is not None:
            self.id = int(id)
            Task._id_counter = max(Task._id_counter, self.id + 1)
        else:
            self.id = Task._id_counter
            Task._id_counter += 1

        self.title = title
        self.assigned_to = int(assigned_to)
        self.status = status

    def complete(self) -> None:
        """Mark the task as completed."""

        self.status = "completed"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dict."""

        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "assigned_to": self.assigned_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dict."""

        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            status=str(data.get("status", "pending")),
            assigned_to=int(data["assigned_to"]),
        )

    def __str__(self) -> str:
        return f"Task(id={self.id}, title={self.title}, status={self.status})"

