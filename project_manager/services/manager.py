from __future__ import annotations

import json
import logging
from pathlib import Path

from project_manager.models.project import (
    DuplicateTaskError,
    EmptyProjectTitleError,
    Project,
    TaskNotFoundError,
)
from project_manager.models.task import (
    EmptyContributorError,
    EmptyTitleError,
    Task,
)
from project_manager.models.user import (
    DuplicateProjectError,
    EmptyUserNameError,
    ProjectNotFoundError,
    User,
)
from project_manager.services.storage import (
    DatabaseCorruptionError,
    InvalidDatabaseStructureError,
    InvalidInputError,
    Storage,
)

_logger = logging.getLogger(__name__)


class DuplicateUserError(ValueError):
    """Raised when attempting to add a user that already exists."""


class UserNotFoundError(ValueError):
    """Raised when a requested user is not found."""


class DuplicateTaskTitleError(ValueError):
    """Raised when attempting to add a task with a duplicate title."""


class TaskAlreadyCompletedError(ValueError):
    """Raised when attempting to complete an already completed task."""


class ContributorNotFoundError(ValueError):
    """Raised when a requested contributor is not found on a task."""


class Manager:
    """Orchestrates all business logic for the project management system."""

    def __init__(self, storage: Storage) -> None:
        if not isinstance(storage, Storage):
            raise TypeError(f"storage must be a Storage instance, got {type(storage).__name__}")
        self._storage: Storage = storage
        self._users: list[User] = []
        self._load_data()

    def add_user(self, name: str, email: str | None = None) -> User:
        """Add a new user to the system.

        Args:
            name: The name of the user to add.
            email: Optional email address for the user.

        Returns:
            The newly created User instance.

        Raises:
            TypeError: If name or email are invalid types.
            EmptyUserNameError: If name is empty or whitespace-only.
            DuplicateUserError: If a user with the same name already exists.
        """
        normalized_name = self._normalize_name(name)
        if self._find_user_index(normalized_name) is not None:
            raise DuplicateUserError(f"User '{normalized_name}' already exists.")
        user = User(name=normalized_name, email=email)
        self._users.append(user)
        self._save_data()
        return user

    def get_user(self, name: str) -> User:
        """Retrieve a user by name.

        Args:
            name: The name of the user to retrieve.

        Returns:
            The matching User instance.

        Raises:
            TypeError: If name is not a string.
            EmptyUserNameError: If name is empty or whitespace-only.
            UserNotFoundError: If the user does not exist.
        """
        normalized_name = self._normalize_name(name)
        index = self._find_user_index(normalized_name)
        if index is None:
            raise UserNotFoundError(f"User '{normalized_name}' not found.")
        return self._users[index]

    def list_users(self) -> list[User]:
        """Return a list of all users in the system.

        Returns:
            A shallow copy of the user list.
        """
        return self._users.copy()

    def remove_user(self, name: str) -> None:
        """Remove a user from the system.

        Args:
            name: The name of the user to remove.

        Raises:
            TypeError: If name is not a string.
            EmptyUserNameError: If name is empty or whitespace-only.
            UserNotFoundError: If the user does not exist.
        """
        normalized_name = self._normalize_name(name)
        index = self._find_user_index(normalized_name)
        if index is None:
            raise UserNotFoundError(f"User '{normalized_name}' not found.")
        del self._users[index]
        self._save_data()

    def rename_user(self, name: str, new_name: str) -> User:
        """Rename an existing user."""
        user = self.get_user(name)
        normalized_new_name = self._normalize_name(new_name)
        if self._find_user_index(normalized_new_name) is not None:
            raise DuplicateUserError(f"User '{normalized_new_name}' already exists.")
        user.rename(normalized_new_name)
        self._save_data()
        return user

    def add_project(
        self,
        user_name: str,
        project_title: str,
        description: str | None = None,
        status: str | None = None,
        due_date: str | None = None,
    ) -> Project:
        """Add a new project to a user.

        Args:
            user_name: The name of the user who owns the project.
            project_title: The title of the project to add.
            description: Optional project description.
            status: Optional project status.

        Returns:
            The newly created Project instance.
        """
        user = self.get_user(user_name)
        normalized_title = self._normalize_title(project_title)
        project = Project(title=normalized_title, description=description, status=status, due_date=due_date)
        user.add_project(project)
        self._save_data()
        return project

    def get_project(self, user_name: str, project_title: str) -> Project:
        """Retrieve a project from a user."""
        user = self.get_user(user_name)
        return user.get_project(project_title)

    def list_projects(self, user_name: str) -> list[Project]:
        """Return a list of all projects for a user."""
        user = self.get_user(user_name)
        return user.list_projects()

    def search_projects(self, user_name: str, query: str) -> list[Project]:
        """Search for projects by title or description under a specific user."""
        user = self.get_user(user_name)
        normalized_query = self._normalize_title(query).lower()
        return [
            project
            for project in user.list_projects()
            if normalized_query in project.title.lower()
            or normalized_query in project.description.lower()
        ]

    def remove_project(self, user_name: str, project_title: str) -> None:
        """Remove a project from a user."""
        user = self.get_user(user_name)
        user.remove_project(project_title)
        self._save_data()

    def update_project(
        self,
        user_name: str,
        project_title: str,
        new_title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Project:
        """Update project metadata."""
        user = self.get_user(user_name)
        project = user.get_project(project_title)

        if new_title is not None and new_title.strip().lower() != project.title.lower():
            normalized_new_title = self._normalize_title(new_title)
            if user._find_project_index(normalized_new_title) is not None:
                raise DuplicateProjectError(
                    f"Project with title '{normalized_new_title}' already exists for user '{user.name}'."
                )
            project.rename(normalized_new_title)

        if description is not None:
            project.set_description(description)

        if status is not None:
            project.set_status(status)

        self._save_data()
        return project

    def add_task(
        self,
        user_name: str,
        project_title: str,
        task_title: str,
        description: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
    ) -> Task:
        """Add a new task to a project."""
        project = self.get_project(user_name, project_title)
        normalized_task_title = self._normalize_title(task_title)
        task = Task(
            title=normalized_task_title,
            description=description,
            due_date=due_date,
            priority=priority,
            assigned_to=assigned_to,
        )
        project.add_task(task)
        self._save_data()
        return task

    def list_tasks(
        self,
        user_name: str,
        project_title: str,
        status: str | None = None,
        assigned_to: str | None = None,
    ) -> list[Task]:
        """Return a list of all tasks in a project, optionally filtered."""
        project = self.get_project(user_name, project_title)
        tasks = project.list_tasks()

        if status is not None:
            normalized_status = status.strip().lower()
            if normalized_status == "completed":
                tasks = [task for task in tasks if task.completed]
            elif normalized_status == "pending":
                tasks = [task for task in tasks if not task.completed]
            else:
                raise ValueError("Status filter must be 'pending' or 'completed'.")

        if assigned_to is not None:
            normalized_assignee = assigned_to.strip().lower()
            tasks = [
                task for task in tasks if task.assigned_to.lower() == normalized_assignee
            ]

        return tasks

    def complete_task(self, user_name: str, project_title: str, task_title: str) -> None:
        """Mark a task as completed."""
        task = self._get_task(user_name, project_title, task_title)
        if task.completed:
            raise TaskAlreadyCompletedError(
                f"Task '{task.title}' is already completed."
            )
        task.mark_complete()
        self._save_data()

    def search_tasks(
        self,
        user_name: str,
        project_title: str,
        query: str,
    ) -> list[Task]:
        """Search tasks by keyword in title or description."""
        project = self.get_project(user_name, project_title)
        normalized_query = self._normalize_title(query).lower()
        return [
            task
            for task in project.list_tasks()
            if normalized_query in task.title.lower()
            or normalized_query in task.description.lower()
        ]

    def update_task(
        self,
        user_name: str,
        project_title: str,
        task_title: str,
        new_title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
    ) -> Task:
        """Update task metadata and rename if needed."""
        project = self.get_project(user_name, project_title)
        task = project.get_task(task_title)

        if new_title is not None and new_title.strip().lower() != task.title.lower():
            normalized_new_title = self._normalize_title(new_title)
            if project._find_task_index(normalized_new_title) is not None:
                raise DuplicateTaskError(
                    f"Task with title '{normalized_new_title}' already exists in project '{project.title}'."
                )
            task.rename(normalized_new_title)

        if description is not None:
            task.set_description(description)
        if due_date is not None:
            task.set_due_date(due_date)
        if priority is not None:
            task.set_priority(priority)
        if assigned_to is not None:
            task.set_assigned_to(assigned_to)

        self._save_data()
        return task

    def show_project(self, user_name: str, project_title: str) -> Project:
        """Return detailed project information."""
        return self.get_project(user_name, project_title)

    def show_task(self, user_name: str, project_title: str, task_title: str) -> Task:
        """Return detailed task information."""
        return self._get_task(user_name, project_title, task_title)

    def user_summary(self, user_name: str) -> dict[str, object]:
        """Generate a summary of the user with projects and task counts."""
        user = self.get_user(user_name)
        projects = user.list_projects()
        task_count = sum(len(project.tasks) for project in projects)
        completed_tasks = sum(
            1 for project in projects for task in project.tasks if task.completed
        )
        return {
            "user": user.name,
            "projects": len(projects),
            "tasks": task_count,
            "completed_tasks": completed_tasks,
        }

    def project_summary(self, user_name: str, project_title: str) -> dict[str, object]:
        """Generate a summary of a project."""
        project = self.get_project(user_name, project_title)
        tasks = project.list_tasks()
        completed_tasks = sum(1 for task in tasks if task.completed)
        contributors = sorted({contributor.name for task in tasks for contributor in task.contributors})
        return {
            "user": user_name,
            "project": project.title,
            "description": project.description,
            "status": project.status,
            "tasks": len(tasks),
            "completed_tasks": completed_tasks,
            "pending_tasks": len(tasks) - completed_tasks,
            "contributors": contributors,
        }

    def export_data(self, output_path: Path) -> None:
        """Export the current database to another JSON file."""
        if not isinstance(output_path, Path):
            raise TypeError(f"output_path must be a Path instance, got {type(output_path).__name__}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump({"users": [user.to_dict() for user in self._users]}, file, indent=4, ensure_ascii=False)
            file.write("\n")

    def import_data(self, input_path: Path) -> None:
        """Import data from a JSON file and replace the current database."""
        if not isinstance(input_path, Path):
            raise TypeError(f"input_path must be a Path instance, got {type(input_path).__name__}")
        if not input_path.exists():
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

        with input_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._storage.validate_database_structure(data)
        users: list[User] = []
        for user_data in data["users"]:
            if not isinstance(user_data, dict):
                raise InvalidDatabaseStructureError(
                    f"Each user entry must be a dictionary, got {type(user_data).__name__}."
                )
            users.append(User.from_dict(user_data))

        self._users = users
        self._save_data()

    def _load_data(self) -> None:
        """Load all users from persistent storage."""
        _logger.debug("Loading users from storage.")
        try:
            self._users = self._storage.load_users()
            _logger.debug("Loaded %d users.", len(self._users))
        except (
            DatabaseCorruptionError,
            InvalidDatabaseStructureError,
            InvalidInputError,
        ):
            self._users = []
            _logger.exception("Failed to load users from storage.")
            raise

    def _save_data(self) -> None:
        """Persist all users to storage."""
        _logger.debug("Saving %d users to storage.", len(self._users))
        self._storage.save_users(self._users)

    def _find_user_index(self, name: str) -> int | None:
        """Find the index of a user by normalized name.

        Args:
            name: The pre-normalized name to search for.

        Returns:
            The index of the matching user, or None if not found.
        """
        for index, user in enumerate(self._users):
            if user.name.lower() == name.lower():
                return index
        return None

    def _get_task(self, user_name: str, project_title: str, task_title: str) -> Task:
        """Retrieve a task from a project owned by a user.

        Args:
            user_name: The name of the user.
            project_title: The title of the project.
            task_title: The title of the task.

        Returns:
            The matching Task instance.

        Raises:
            TypeError: If inputs are not strings.
            EmptyUserNameError: If user_name is empty or whitespace-only.
            EmptyProjectTitleError: If project_title is empty or whitespace-only.
            EmptyTitleError: If task_title is empty or whitespace-only.
            UserNotFoundError: If the user does not exist.
            ProjectNotFoundError: If the project does not exist for the user.
            TaskNotFoundError: If the task does not exist in the project.
        """
        project = self.get_project(user_name, project_title)
        return project.get_task(task_title)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a name by stripping whitespace and validating.

        Args:
            name: The raw name input.

        Returns:
            The stripped name.

        Raises:
            TypeError: If name is not a string.
            EmptyUserNameError: If name is empty after stripping.
        """
        if not isinstance(name, str):
            raise TypeError(f"name must be a string, got {type(name).__name__}")
        stripped = name.strip()
        if not stripped:
            raise EmptyUserNameError("Name cannot be empty or contain only whitespace.")
        return stripped


    def remove_task(self, user_name: str, project_title: str, task_title: str) -> None:
        """Remove a task from a project."""
        project = self.get_project(user_name, project_title)
        project.remove_task(task_title)
        self._save_data()

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize a title by stripping whitespace and validating."""
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")
        stripped = title.strip()
        if not stripped:
            raise EmptyTitleError("Title cannot be empty or contain only whitespace.")
        return stripped

    def _get_or_create_user(self, name: str) -> User:
        """Return an existing User instance or create a new one."""
        normalized_name = self._normalize_name(name)
        try:
            return self.get_user(normalized_name)
        except UserNotFoundError:
            return User(name=normalized_name)

    def add_contributor(
        self,
        user_name: str,
        project_title: str,
        task_title: str,
        contributor_name: str,
    ) -> None:
        """Add a contributor to a task.

        Args:
            user_name: The name of the user who owns the project.
            project_title: The title of the project.
            task_title: The title of the task.
            contributor_name: The name of the contributor to add.

        Raises:
            TypeError: If inputs are not strings.
            EmptyUserNameError: If user_name is empty or whitespace-only.
            EmptyProjectTitleError: If project_title is empty or whitespace-only.
            EmptyTitleError: If task_title is empty or whitespace-only.
            EmptyContributorError: If contributor_name is empty or whitespace-only.
            UserNotFoundError: If the user does not exist.
            ProjectNotFoundError: If the project does not exist for the user.
            TaskNotFoundError: If the task does not exist in the project.
        """
        task = self._get_task(user_name, project_title, task_title)
        contributor_user = self._get_or_create_user(contributor_name)
        task.add_contributor(contributor_user)
        self._save_data()

    def add_task_contributor(
        self,
        user_name: str,
        project_title: str,
        task_title: str,
        contributor_name: str,
    ) -> None:
        """Add a contributor to an existing project task."""
        task = self._get_task(user_name, project_title, task_title)
        contributor_user = self._get_or_create_user(contributor_name)
        task.add_contributor(contributor_user)
        self._save_data()

    def remove_contributor(
        self,
        user_name: str,
        project_title: str,
        task_title: str,
        contributor_name: str,
    ) -> None:
        """Remove a contributor from a task.

        Args:
            user_name: The name of the user who owns the project.
            project_title: The title of the project.
            task_title: The title of the task.
            contributor_name: The name of the contributor to remove.

        Raises:
            TypeError: If inputs are not strings.
            EmptyUserNameError: If user_name is empty or whitespace-only.
            EmptyProjectTitleError: If project_title is empty or whitespace-only.
            EmptyTitleError: If task_title is empty or whitespace-only.
            EmptyContributorError: If contributor_name is empty or whitespace-only.
            UserNotFoundError: If the user does not exist.
            ProjectNotFoundError: If the project does not exist for the user.
            TaskNotFoundError: If the task does not exist in the project.
            ContributorNotFoundError: If the contributor is not found on the task.
        """
        task = self._get_task(user_name, project_title, task_title)
        normalized_contributor = self._normalize_name(contributor_name)
        try:
            task.remove_contributor(normalized_contributor)
        except ValueError as exc:
            raise ContributorNotFoundError(str(exc)) from exc
        self._save_data()


    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize a title by stripping whitespace and validating.

        Args:
            title: The raw title input.

        Returns:
            The stripped title.

        Raises:
            TypeError: If title is not a string.
            EmptyTitleError: If title is empty after stripping.
        """
        if not isinstance(title, str):
            raise TypeError(f"title must be a string, got {type(title).__name__}")
        stripped = title.strip()
        if not stripped:
            raise EmptyTitleError("Title cannot be empty or contain only whitespace.")
        return stripped