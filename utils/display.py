"""Rich-based display helpers."""

from __future__ import annotations

from typing import Iterable

from rich.console import Console
from rich.table import Table


console = Console()


def show_users(users: Iterable[dict]) -> None:
    table = Table(title="Users")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Email")

    for u in users:
        table.add_row(str(u.get("id")), str(u.get("name")), str(u.get("email")))

    console.print(table)


def show_projects(projects: Iterable[dict]) -> None:
    table = Table(title="Projects")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Due Date")
    table.add_column("User ID")

    for p in projects:
        table.add_row(
            str(p.get("id")),
            str(p.get("title")),
            str(p.get("due_date")),
            str(p.get("user_id", "")),
        )

    console.print(table)


def show_tasks(tasks: Iterable[dict]) -> None:
    table = Table(title="Tasks")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Project ID")

    for t in tasks:
        table.add_row(
            str(t.get("id")),
            str(t.get("title")),
            str(t.get("status")),
            str(t.get("assigned_to")),
        )

    console.print(table)


def success(message: str) -> None:
    console.print(f"[bold green]✓ {message}[/bold green]")


def error(message: str) -> None:
    console.print(f"[bold red]✗ {message}[/bold red]")

