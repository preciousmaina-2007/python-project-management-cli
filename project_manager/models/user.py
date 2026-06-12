from __future__ import annotations

from typing import Any
from project_manager.utils.validation import is_valid_email

from .project import Project


class EmptyUserNameError(ValueError):
    """Raised when a user name is empty or contains only whitespace."""


class DuplicateProjectError(ValueError):
    """Raised when attempting to add a project with a title that already exists."""


class ProjectNotFoundError(ValueError):
    """Raised when a requested project is not found."""


class InvalidEmailError(ValueError):
    """Raised when an email address does not match expected format."""


class Person:
    """A named entity with optional email and a stable identifier."""

    _id_counter = 1

    def __init__(self, name: str, email: str | None = None, id: int | None = None) -> None:
        if not isinstance(name, str):
            raise TypeError(f"name must be a string, got {type(name).__name__}")
        stripped_name = name.strip()
        if not stripped_name:
            raise EmptyUserNameError("User name cannot be empty or contain only whitespace.")

        self._id: int = id if id is not None else self._generate_id()
        self._name: str = stripped_name
        self._email: str = self._validate_optional_string(email)

        if self._email and not is_valid_email(self._email):
            raise InvalidEmailError(f"Invalid email address: '{email}'")

    @classmethod
    def _generate_id(cls) -> int:
        id_ = cls._id_counter
        cls._id_counter += 1
        return id_

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    def __repr__(self) -> str:
        return f"<Person id={self._id} name={self._name!r} email={self._email!r}>"

    def __str__(self) -> str:
        return f"{self._name} ({self._email or 'no email'})"

    @staticmethod
    def _validate_optional_string(value: str | None, default: str = "") -> str:
        if value is None:
            return default
        if not isinstance(value, str):
            raise TypeError(f"Value must be a string, got {type(value).__name__}")
        return value.strip()


class User(Person):
    """Represents a user that owns a collection of projects."""

    def __init__(self, name: str, email: str | None = None, projects: list[Project] | None = None, id: int | None = None) -> None:
        super().__init__(name, email=email, id=id)
        self._projects: list[Project] = []
        if projects is not None:
            if not isinstance(projects, list):
                raise TypeError(f"projects must be a list of Project instances, got {type(projects).__name__}")
            for project in projects:
                self.add_project(project)

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def projects(self) -> list[Project]:
        return self._projects.copy()

    def add_project(self, project: Project) -> None:
        """Add a project to the user.

        Args:
            project: The Project instance to add.

        Raises:
            TypeError: If project is not a Project instance.
            DuplicateProjectError: If a project with the same title already exists.
        """
        if not isinstance(project, Project):
            raise TypeError(f"project must be a Project instance, got {type(project).__name__}")
        if self._find_project_index(project.title) is not None:
            raise DuplicateProjectError(
                f"Project with title '{project.title}' already exists for user '{self._name}'."
            )
        self._projects.append(project)

    def rename(self, new_name: str) -> None:
        """Rename the user."""
        if not isinstance(new_name, str):
            raise TypeError(f"name must be a string, got {type(new_name).__name__}")
        stripped_name = new_name.strip()
        if not stripped_name:
            raise EmptyUserNameError("User name cannot be empty or contain only whitespace.")
        self._name = stripped_name

    def get_project(self, title: str) -> Project:
        """Retrieve a project by title.

        Args:
            title: The title of the project to retrieve.

        Returns:
            The matching Project instance.

        Raises:
            TypeError: If title is not a string.
            ProjectNotFoundError: If no project with the given title exists.
        """
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")
        index = self._find_project_index(title)
        if index is None:
            raise ProjectNotFoundError(
                f"Project with title '{title.strip()}' not found for user '{self._name}'."
            )
        return self._projects[index]

    def remove_project(self, title: str) -> None:
        """Remove a project by title.

        Args:
            title: The title of the project to remove.

        Raises:
            TypeError: If title is not a string.
            ProjectNotFoundError: If no project with the given title exists.
        """
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")
        index = self._find_project_index(title)
        if index is None:
            raise ProjectNotFoundError(
                f"Project with title '{title.strip()}' not found for user '{self._name}'."
            )
        del self._projects[index]

    def list_projects(self) -> list[Project]:
        """Return a list of all projects owned by the user.

        Returns:
            A shallow copy of the project list.
        """
        return self._projects.copy()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the user to a JSON-serializable dictionary."""
        return {
            "id": self._id,
            "name": self._name,
            "email": self._email,
            "projects": [project.to_dict() for project in self._projects],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Reconstruct a User instance from a dictionary.

        Args:
            data: A dictionary containing user data.

        Returns:
            A new User instance.

        Raises:
            KeyError: If required keys are missing.
            TypeError: If values have incorrect types.
            EmptyUserNameError: If the user name is empty after stripping.
            EmptyProjectTitleError: If a project title is empty after stripping.
            DuplicateTaskError: If a duplicate task title is encountered.
            TaskNotFoundError: If a task reference is invalid during reconstruction.
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        name = data.get("name")
        if name is None:
            raise KeyError("Missing required key: 'name'")

        email = data.get("email")
        projects_data = data.get("projects", [])
        if not isinstance(projects_data, list):
            raise TypeError(f"'projects' must be a list, got {type(projects_data).__name__}")

        projects: list[Project] = []
        for project_data in projects_data:
            if not isinstance(project_data, dict):
                raise TypeError(f"Each project must be a dict, got {type(project_data).__name__}")
            projects.append(Project.from_dict(project_data))

        user_id = data.get("id")
        return cls(name=name, email=email, projects=projects, id=user_id)

    def _find_project_index(self, title: str) -> int | None:
        """Find the index of a project by title, case-insensitive.

        Args:
            title: The title to search for.

        Returns:
            The index of the matching project, or None if not found.
        """
        normalized = title.strip().lower()
        for index, project in enumerate(self._projects):
            if project.title.lower() == normalized:
                return index
        return None