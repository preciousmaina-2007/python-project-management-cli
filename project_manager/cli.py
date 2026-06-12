from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from rich.console import Console
from rich.table import Table

from project_manager.services.manager import (
    ContributorNotFoundError,
    DuplicateProjectError,
    DuplicateTaskError,
    DuplicateUserError,
    Manager,
    ProjectNotFoundError,
    TaskAlreadyCompletedError,
    TaskNotFoundError,
    UserNotFoundError,
)
from project_manager.services.storage import Storage
from project_manager.models.user import InvalidEmailError


class CLI:
    """Command-line interface for the project management system."""

    def __init__(self, manager: Manager, console: Console | None = None) -> None:
        self._manager = manager
        self._console = console or Console()

    def run(self, args: Sequence[str] | None = None) -> int:
        """Parse arguments and execute the requested command.

        Args:
            args: Command-line arguments. Uses sys.argv by default.

        Returns:
            Exit code (0 for success, 1 for error).
        """
        parser = self._build_parser()
        parsed_args = parser.parse_args(args)

        if not hasattr(parsed_args, "func"):
            parser.print_help()
            return 1

        if getattr(parsed_args, "debug", False):
            logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        try:
            parsed_args.func(parsed_args)
            return 0
        except InvalidEmailError as exc:
            self._console.print(f"[red]Email validation error:[/red] {exc}. Provide an address like 'name@example.com'.")
            return 1
        except (
            DuplicateUserError,
            UserNotFoundError,
            DuplicateProjectError,
            ProjectNotFoundError,
            DuplicateTaskError,
            TaskNotFoundError,
            TaskAlreadyCompletedError,
            ContributorNotFoundError,
            ValueError,
            TypeError,
        ) as exc:
            self._console.print(f"[red]Error:[/red] {exc}")
            return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build the argument parser with all subcommands."""
        parser = argparse.ArgumentParser(
            prog="project_manager",
            description="Command Line Project Management System",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging for CLI operations",
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        self._build_user_commands(subparsers)
        self._build_project_commands(subparsers)
        self._build_task_commands(subparsers)
        self._build_contributor_commands(subparsers)
        self._build_data_commands(subparsers)

        return parser

    def _build_user_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add user-related subcommands."""
        user_parser = subparsers.add_parser("add-user", help="Add a new user")
        user_parser.add_argument(
            "--name",
            required=True,
            help="Name of the user to create",
        )
        user_parser.add_argument(
            "--email",
            help="Optional email address for the user",
        )
        user_parser.set_defaults(func=self._handle_add_user)

        list_users_parser = subparsers.add_parser("list-users", help="List all users")
        list_users_parser.set_defaults(func=self._handle_list_users)

        remove_user_parser = subparsers.add_parser("remove-user", help="Remove a user")
        remove_user_parser.add_argument(
            "--name",
            required=True,
            help="Name of the user to remove",
        )
        remove_user_parser.set_defaults(func=self._handle_remove_user)

        update_user_parser = subparsers.add_parser("update-user", help="Rename an existing user")
        update_user_parser.add_argument(
            "--name",
            required=True,
            help="Current name of the user",
        )
        update_user_parser.add_argument(
            "--new-name",
            required=True,
            help="New name for the user",
        )
        update_user_parser.set_defaults(func=self._handle_update_user)

    def _build_project_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add project-related subcommands."""
        add_project_parser = subparsers.add_parser("add-project", help="Add a new project")
        add_project_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        add_project_parser.add_argument(
            "--title",
            required=True,
            help="Title of the project",
        )
        add_project_parser.add_argument(
            "--description",
            help="Optional description for the project",
        )
        add_project_parser.add_argument(
            "--due-date",
            help="Optional due date in YYYY-MM-DD format",
        )
        add_project_parser.add_argument(
            "--status",
            choices=["planned", "active", "completed"],
            default="planned",
            help="Project status",
        )
        add_project_parser.set_defaults(func=self._handle_add_project)

        update_project_parser = subparsers.add_parser("update-project", help="Update project metadata")
        update_project_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        update_project_parser.add_argument(
            "--title",
            required=True,
            help="Current title of the project",
        )
        update_project_parser.add_argument(
            "--new-title",
            help="New title for the project",
        )
        update_project_parser.add_argument(
            "--description",
            help="New description for the project",
        )
        update_project_parser.add_argument(
            "--status",
            choices=["planned", "active", "completed"],
            help="New project status",
        )
        update_project_parser.set_defaults(func=self._handle_update_project)

        show_project_parser = subparsers.add_parser("show-project", help="Show detailed project information")
        show_project_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        show_project_parser.add_argument(
            "--title",
            required=True,
            help="Title of the project",
        )
        show_project_parser.set_defaults(func=self._handle_show_project)

        list_projects_parser = subparsers.add_parser(
            "list-projects", help="List all projects for a user"
        )
        list_projects_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user",
        )
        list_projects_parser.set_defaults(func=self._handle_list_projects)

        search_projects_parser = subparsers.add_parser(
            "search-projects", help="Search projects for a user"
        )
        search_projects_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user",
        )
        search_projects_parser.add_argument(
            "--query",
            required=True,
            help="Keyword or text to search in project titles or descriptions",
        )
        search_projects_parser.set_defaults(func=self._handle_search_projects)

        project_summary_parser = subparsers.add_parser("project-summary", help="Show summary for a project")
        project_summary_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        project_summary_parser.add_argument(
            "--title",
            required=True,
            help="Title of the project",
        )
        project_summary_parser.set_defaults(func=self._handle_project_summary)

        remove_project_parser = subparsers.add_parser("remove-project", help="Remove a project")
        remove_project_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        remove_project_parser.add_argument(
            "--title",
            required=True,
            help="Title of the project to remove",
        )
        remove_project_parser.set_defaults(func=self._handle_remove_project)

    def _build_task_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add task-related subcommands."""
        add_task_parser = subparsers.add_parser("add-task", help="Add a new task")
        add_task_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        add_task_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        add_task_parser.add_argument(
            "--title",
            required=True,
            help="Title of the task",
        )
        add_task_parser.add_argument(
            "--description",
            help="Optional task description",
        )
        add_task_parser.add_argument(
            "--due-date",
            help="Optional due date in YYYY-MM-DD format",
        )
        add_task_parser.add_argument(
            "--priority",
            choices=["low", "normal", "high"],
            default="normal",
            help="Task priority",
        )
        add_task_parser.add_argument(
            "--assigned-to",
            help="Optional single assignee for the task",
        )
        add_task_parser.set_defaults(func=self._handle_add_task)

        update_task_parser = subparsers.add_parser("update-task", help="Update task metadata")
        update_task_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        update_task_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        update_task_parser.add_argument(
            "--task",
            required=True,
            help="Current title of the task",
        )
        update_task_parser.add_argument(
            "--new-title",
            help="New title for the task",
        )
        update_task_parser.add_argument(
            "--description",
            help="New description for the task",
        )
        update_task_parser.add_argument(
            "--due-date",
            help="New due date in YYYY-MM-DD format",
        )
        update_task_parser.add_argument(
            "--priority",
            choices=["low", "normal", "high"],
            help="New task priority",
        )
        update_task_parser.add_argument(
            "--assigned-to",
            help="New assignee for the task",
        )
        update_task_parser.set_defaults(func=self._handle_update_task)

        show_task_parser = subparsers.add_parser("show-task", help="Show detailed task information")
        show_task_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        show_task_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        show_task_parser.add_argument(
            "--task",
            required=True,
            help="Title of the task",
        )
        show_task_parser.set_defaults(func=self._handle_show_task)

        search_tasks_parser = subparsers.add_parser("search-tasks", help="Search tasks inside a project")
        search_tasks_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        search_tasks_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        search_tasks_parser.add_argument(
            "--query",
            required=True,
            help="Keyword or text to search in task titles or descriptions",
        )
        search_tasks_parser.set_defaults(func=self._handle_search_tasks)

        list_tasks_parser = subparsers.add_parser("list-tasks", help="List all tasks in a project")
        list_tasks_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        list_tasks_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        list_tasks_parser.add_argument(
            "--status",
            choices=["pending", "completed"],
            help="Filter tasks by status",
        )
        list_tasks_parser.add_argument(
            "--assigned-to",
            help="Filter tasks by assignee",
        )
        list_tasks_parser.set_defaults(func=self._handle_list_tasks)

        complete_task_parser = subparsers.add_parser("complete-task", help="Mark a task as completed")
        complete_task_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        complete_task_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        complete_task_parser.add_argument(
            "--task",
            required=True,
            help="Title of the task to complete",
        )
        complete_task_parser.set_defaults(func=self._handle_complete_task)

        remove_task_parser = subparsers.add_parser("remove-task", help="Remove a task")
        remove_task_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        remove_task_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        remove_task_parser.add_argument(
            "--task",
            required=True,
            help="Title of the task to remove",
        )
        remove_task_parser.set_defaults(func=self._handle_remove_task)

    def _build_contributor_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add contributor-related subcommands."""
        add_contributor_parser = subparsers.add_parser("add-contributor", help="Add a contributor to a task")
        add_contributor_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        add_contributor_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        add_contributor_parser.add_argument(
            "--task",
            required=True,
            help="Title of the task",
        )
        add_contributor_parser.add_argument(
            "--contributor",
            required=True,
            help="Name of the contributor to add",
        )
        add_contributor_parser.set_defaults(func=self._handle_add_contributor)

        remove_contributor_parser = subparsers.add_parser(
            "remove-contributor", help="Remove a contributor from a task"
        )
        remove_contributor_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user who owns the project",
        )
        remove_contributor_parser.add_argument(
            "--project",
            required=True,
            help="Title of the project",
        )
        remove_contributor_parser.add_argument(
            "--task",
            required=True,
            help="Title of the task",
        )
        remove_contributor_parser.add_argument(
            "--contributor",
            required=True,
            help="Name of the contributor to remove",
        )
        remove_contributor_parser.set_defaults(func=self._handle_remove_contributor)

    def _build_data_commands(self, subparsers: argparse._SubParsersAction) -> None:
        """Add data persistence-related subcommands."""
        export_parser = subparsers.add_parser("export-data", help="Export the current data file")
        export_parser.add_argument(
            "--output",
            required=True,
            help="Path to export JSON data to",
        )
        export_parser.set_defaults(func=self._handle_export_data)

        import_parser = subparsers.add_parser("import-data", help="Import data from a JSON file")
        import_parser.add_argument(
            "--input",
            required=True,
            help="Path to JSON file containing data to import",
        )
        import_parser.set_defaults(func=self._handle_import_data)

        summary_parser = subparsers.add_parser("user-summary", help="Show summary for a user")
        summary_parser.add_argument(
            "--user",
            required=True,
            help="Name of the user",
        )
        summary_parser.set_defaults(func=self._handle_user_summary)

    def _handle_add_user(self, args: argparse.Namespace) -> None:
        user = self._manager.add_user(args.name, args.email)
        self._console.print(f"User '{user.name}' added successfully.")

    def _handle_list_users(self, args: argparse.Namespace) -> None:
        users = self._manager.list_users()
        if not users:
            self._console.print("[yellow]No users found in the system.[/yellow]")
            return
        table = Table(title="System Users")
        table.add_column("User Name", style="cyan", no_wrap=True)
        table.add_column("Email", style="green")
        for user in users:
            table.add_row(user.name, user.email or "None")
        self._console.print(table)

    def _handle_remove_user(self, args: argparse.Namespace) -> None:
        self._manager.remove_user(args.name)
        self._console.print(f"User '{args.name}' removed successfully.")

    def _handle_add_project(self, args: argparse.Namespace) -> None:
        project = self._manager.add_project(
            args.user,
            args.title,
            description=args.description,
            status=args.status,
            due_date=args.due_date,
        )
        self._console.print(f"Project '{project.title}' created for user '{args.user}'.")

    def _handle_update_project(self, args: argparse.Namespace) -> None:
        project = self._manager.update_project(
            args.user,
            args.title,
            new_title=args.new_title,
            description=args.description,
            status=args.status,
        )
        self._console.print(f"Project '{project.title}' updated for user '{args.user}'.")

    def _handle_show_project(self, args: argparse.Namespace) -> None:
        project = self._manager.show_project(args.user, args.title)
        table = Table(title=f"Project Details: {project.title}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Title", project.title)
        table.add_row("Description", project.description or "None")
        table.add_row("Status", project.status.title())
        table.add_row("Due Date", project.due_date or "None")
        table.add_row("Total Tasks", str(len(project.tasks)))
        self._console.print(table)

    def _handle_list_projects(self, args: argparse.Namespace) -> None:
        projects = self._manager.list_projects(args.user)
        if not projects:
            self._console.print(f"[yellow]No projects found for user '{args.user}'.[/yellow]")
            return
        table = Table(title=f"Projects for {args.user}")
        table.add_column("Project Title", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Total Tasks", style="cyan")
        for project in projects:
            table.add_row(project.title, project.status.title(), str(len(project.tasks)))
        self._console.print(table)

    def _handle_remove_project(self, args: argparse.Namespace) -> None:
        self._manager.remove_project(args.user, args.title)
        self._console.print(f"Project '{args.title}' removed from user '{args.user}'.")

    def _handle_search_projects(self, args: argparse.Namespace) -> None:
        projects = self._manager.search_projects(args.user, args.query)
        if not projects:
            self._console.print(
                f"[yellow]No projects found matching '{args.query}' for user '{args.user}'.[/yellow]"
            )
            return
        table = Table(title=f"Search results for {args.user}")
        table.add_column("Project Title", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Total Tasks", style="cyan")
        for project in projects:
            table.add_row(project.title, project.status.title(), str(len(project.tasks)))
        self._console.print(table)

    def _handle_add_task(self, args: argparse.Namespace) -> None:
        task = self._manager.add_task(
            args.user,
            args.project,
            args.title,
            description=args.description,
            due_date=args.due_date,
            priority=args.priority,
            assigned_to=args.assigned_to,
        )
        self._console.print(f"Task '{task.title}' added to project '{args.project}'.")

    def _handle_update_task(self, args: argparse.Namespace) -> None:
        task = self._manager.update_task(
            args.user,
            args.project,
            args.task,
            new_title=args.new_title,
            description=args.description,
            due_date=args.due_date,
            priority=args.priority,
            assigned_to=args.assigned_to,
        )
        self._console.print(f"Task '{task.title}' updated in project '{args.project}'.")

    def _handle_show_task(self, args: argparse.Namespace) -> None:
        task = self._manager.show_task(args.user, args.project, args.task)
        table = Table(title=f"Task Details: {task.title}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Title", task.title)
        table.add_row("Description", task.description or "None")
        table.add_row("Due Date", task.due_date or "None")
        table.add_row("Priority", task.priority.title())
        table.add_row("Assigned To", task.assigned_to or "None")
        table.add_row("Status", "Done" if task.completed else "Pending")
        table.add_row("Contributors", ", ".join(task.contributor_names) if task.contributor_names else "None")
        self._console.print(table)

    def _handle_search_tasks(self, args: argparse.Namespace) -> None:
        tasks = self._manager.search_tasks(args.user, args.project, args.query)
        if not tasks:
            self._console.print(
                f"[yellow]No tasks found matching '{args.query}' in project '{args.project}'.[/yellow]"
            )
            return
        table = Table(title=f"Task Search Results for {args.project}")
        table.add_column("Task Title", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Assigned", style="cyan")
        for task in tasks:
            table.add_row(
                task.title,
                "Done" if task.completed else "Pending",
                task.assigned_to or "None",
            )
        self._console.print(table)

    def _handle_list_tasks(self, args: argparse.Namespace) -> None:
        tasks = self._manager.list_tasks(args.user, args.project, status=args.status, assigned_to=args.assigned_to)
        if not tasks:
            self._console.print(f"[yellow]No tasks found inside project '{args.project}'.[/yellow]")
            return
        table = Table(title=f"Tasks in {args.project} ({args.user})")
        table.add_column("Task Title", style="blue")
        table.add_column("Status", style="bold")
        table.add_column("Assigned", style="cyan")
        table.add_column("Contributors", style="yellow")
        for task in tasks:
            status = "[green]Done[/green]" if task.completed else "[yellow]Pending[/yellow]"
            assigned_to = task.assigned_to or "None"
            contributors = ", ".join(task.contributor_names) if task.contributor_names else "None"
            table.add_row(task.title, status, assigned_to, contributors)
        self._console.print(table)

    def _handle_complete_task(self, args: argparse.Namespace) -> None:
        self._manager.complete_task(args.user, args.project, args.task)
        self._console.print(f"Task '{args.task}' marked as completed.")

    def _handle_remove_task(self, args: argparse.Namespace) -> None:
        self._manager.remove_task(args.user, args.project, args.task)
        self._console.print(f"Task '{args.task}' removed from project '{args.project}'.")

    def _handle_add_contributor(self, args: argparse.Namespace) -> None:
        self._manager.add_contributor(args.user, args.project, args.task, args.contributor)
        self._console.print(f"Added contributor '{args.contributor}' to task '{args.task}'.")

    def _handle_remove_contributor(self, args: argparse.Namespace) -> None:
        self._manager.remove_contributor(args.user, args.project, args.task, args.contributor)
        self._console.print(f"Removed contributor '{args.contributor}' from task '{args.task}'.")

    def _handle_export_data(self, args: argparse.Namespace) -> None:
        output_path = Path(args.output)
        self._manager.export_data(output_path)
        self._console.print(f"Data exported to '{output_path}'.")

    def _handle_import_data(self, args: argparse.Namespace) -> None:
        input_path = Path(args.input)
        self._manager.import_data(input_path)
        self._console.print(f"Data imported from '{input_path}'.")

    def _handle_update_user(self, args: argparse.Namespace) -> None:
        user = self._manager.rename_user(args.name, args.new_name)
        self._console.print(f"User '{args.name}' renamed to '{user.name}'.")

    def _handle_project_summary(self, args: argparse.Namespace) -> None:
        summary = self._manager.project_summary(args.user, args.title)
        table = Table(title=f"Project Summary: {summary['project']}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("User", summary["user"])
        table.add_row("Description", summary["description"] or "None")
        table.add_row("Status", summary["status"].title())
        table.add_row("Tasks", str(summary["tasks"]))
        table.add_row("Completed Tasks", str(summary["completed_tasks"]))
        table.add_row("Pending Tasks", str(summary["pending_tasks"]))
        table.add_row("Contributors", ", ".join(summary["contributors"]) if summary["contributors"] else "None")
        self._console.print(table)

    def _handle_user_summary(self, args: argparse.Namespace) -> None:
        summary = self._manager.user_summary(args.user)
        table = Table(title=f"Summary for {summary['user']}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Projects", str(summary["projects"]))
        table.add_row("Tasks", str(summary["tasks"]))
        table.add_row("Completed Tasks", str(summary["completed_tasks"]))
        self._console.print(table)


def main() -> int:
    """Global execution driver for the CLI application."""
    db_path = Path("data/projects.json")
    storage = Storage(db_path)
    manager = Manager(storage)
    cli = CLI(manager)
    return cli.run(sys.argv[1:])