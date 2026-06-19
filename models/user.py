"""User model module."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, ClassVar, Dict, List, Optional

from .person import Person


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class User(Person):
    """Represents a user in the system.

    Attributes:
        id: Unique user identifier.
        name: Display name.
        email: Email address with validation.
        projects: List of project IDs owned by the user.
    """

    _id_counter: ClassVar[int] = 1

    id: int = field(init=False)
    _email: str = field(init=False, repr=False)
    projects: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.id = User._id_counter
        User._id_counter += 1

    def __init__(self, name: str, email: str, projects: Optional[List[int]] = None, id: Optional[int] = None):
        # Keep dataclass-like behavior while enforcing the required OOP rules.
        super().__init__(name=name)
        if id is not None:
            self.id = id
            User._id_counter = max(User._id_counter, id + 1)
        else:
            self.id = User._id_counter
            User._id_counter += 1

        self.projects = list(projects or [])
        self.email = email

    @property
    def email(self) -> str:
        """Get validated email."""

        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Set email after validation."""

        if not isinstance(value, str) or not EMAIL_RE.match(value):
            raise ValueError("Invalid email address")
        self._email = value

    def add_project(self, project_id: int) -> None:
        """Add a project ID to the user's project list."""

        if project_id not in self.projects:
            self.projects.append(project_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user to a JSON-friendly dict."""

        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "projects": list(self.projects),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create a user from a dict."""

        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            email=str(data["email"]),
            projects=list(data.get("projects", [])),
        )

    def __str__(self) -> str:
        return f"User(id={self.id}, name={self.name}, email={self.email})"

