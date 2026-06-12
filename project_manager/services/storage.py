from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from project_manager.models.project import (
    DuplicateTaskError,
    EmptyProjectTitleError,
    Project,
    TaskNotFoundError,
)
from project_manager.models.task import EmptyContributorError, EmptyTitleError, Task
from project_manager.models.user import (
    DuplicateProjectError,
    EmptyUserNameError,
    ProjectNotFoundError,
    User,
)


class DatabaseCorruptionError(Exception):
    """Raised when the database file contains malformed or corrupted data."""


class InvalidDatabaseStructureError(ValueError):
    """Raised when the database structure does not match the expected schema."""


class InvalidInputError(TypeError):
    """Raised when input to save_users does not meet type requirements."""


class Storage:
    """Handles all persistence operations for the project management database."""

    def __init__(self, database_path: Path) -> None:
        if not isinstance(database_path, Path):
            raise TypeError(f"database_path must be a Path instance, got {type(database_path).__name__}")
        self._database_path: Path = database_path
        self._initialize_database()

    @property
    def database_path(self) -> Path:
        return self._database_path

    def load_users(self) -> list[User]:
        """Load and deserialize all users from the database.

        Returns:
            A list of User instances reconstructed from persisted data.

        Raises:
            DatabaseCorruptionError: If the JSON is malformed.
            InvalidDatabaseStructureError: If the database structure is invalid.
            EmptyUserNameError: If a user name is empty during reconstruction.
            EmptyProjectTitleError: If a project title is empty during reconstruction.
            EmptyTitleError: If a task title is empty during reconstruction.
            EmptyContributorError: If a contributor name is empty during reconstruction.
            DuplicateProjectError: If duplicate project titles are encountered.
            DuplicateTaskError: If duplicate task titles are encountered.
            TaskNotFoundError: If a task reference is invalid during reconstruction.
        """
        try:
            with self._database_path.open(mode="r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise DatabaseCorruptionError(
                f"Database file '{self._database_path}' contains malformed JSON."
            ) from exc
        except FileNotFoundError as exc:
            raise DatabaseCorruptionError(
                f"Database file '{self._database_path}' not found."
            ) from exc

        self._validate_database_structure(data)

        users: list[User] = []
        for user_data in data["users"]:
            if not isinstance(user_data, dict):
                raise InvalidDatabaseStructureError(
                    f"Each user entry must be a dictionary, got {type(user_data).__name__}."
                )
            users.append(User.from_dict(user_data))

        return users

    def save_users(self, users: list[User]) -> None:
        """Serialize and persist all users to the database.

        Args:
            users: A list of User instances to persist.

        Raises:
            InvalidInputError: If users is not a list or contains non-User elements.
        """
        if not isinstance(users, list):
            raise InvalidInputError(f"users must be a list, got {type(users).__name__}")
        for item in users:
            if not isinstance(item, User):
                raise InvalidInputError(
                    f"All items in users must be User instances, got {type(item).__name__}."
                )

        data: dict[str, Any] = {
            "users": [user.to_dict() for user in users],
        }

        try:
            with self._database_path.open(mode="w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
                file.write("\n")
        except OSError as exc:
            raise DatabaseCorruptionError(
                f"Failed to write to database file '{self._database_path}': {exc}"
            ) from exc

    def _initialize_database(self) -> None:
        """Ensure the database file and its parent directories exist with valid structure."""
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DatabaseCorruptionError(
                f"Failed to create database directory '{self._database_path.parent}': {exc}"
            ) from exc

        if not self._database_path.exists():
            default_structure: dict[str, Any] = {
                "users": [],
            }
            try:
                with self._database_path.open(mode="w", encoding="utf-8") as file:
                    json.dump(default_structure, file, indent=4, ensure_ascii=False)
                    file.write("\n")
            except OSError as exc:
                raise DatabaseCorruptionError(
                    f"Failed to create database file '{self._database_path}': {exc}"
                ) from exc

    def _validate_database_structure(self, data: Any) -> None:
        """Validate that the loaded data conforms to the expected database schema.

        Args:
            data: The parsed JSON data.

        Raises:
            InvalidDatabaseStructureError: If the structure is invalid.
        """
        if not isinstance(data, dict):
            raise InvalidDatabaseStructureError(
                f"Database root must be a dictionary, got {type(data).__name__}."
            )

        if "users" not in data:
            raise InvalidDatabaseStructureError(
                "Database root is missing required 'users' key."
            )

        if not isinstance(data["users"], list):
            raise InvalidDatabaseStructureError(
                f"'users' must be a list, got {type(data['users']).__name__}."
            )

    def validate_database_structure(self, data: Any) -> None:
        """Public validation for external callers and import operations."""
        self._validate_database_structure(data)
