"""Project Tracker CLI.

Run:
    python main.py --help
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

from rich.prompt import Prompt

from models.project import Project
from models.task import Task
from models.user import User
from utils.display import error, show_projects, show_tasks, show_users, success
from utils.storage import load_data, save_data


def _get_user(data: Dict[str, Any], user_id: int) -> Dict[str, Any] | None:
    return data.get("users", {}).get(str(user_id))


def _get_project(data: Dict[str, Any], project_id: int) -> Dict[str, Any] | None:
    return data.get("projects", {}).get(str(project_id))


def _get_task(data: Dict[str, Any], task_id: int) -> Dict[str, Any] | None:
    return data.get("tasks", {}).get(str(task_id))


def cmd_add_user(args: argparse.Namespace) -> int:
    data = load_data()
    user = User(name=args.name, email=args.email)
    data["users"][str(user.id)] = user.to_dict()
    save_data(data)
    success(f"User created with ID {user.id}")
    return 0


def cmd_list_users(_args: argparse.Namespace) -> int:
    data = load_data()
    show_users(data.get("users", {}).values())
    return 0


def cmd_delete_user(args: argparse.Namespace) -> int:
    data = load_data()
    if _get_user(data, args.id) is None:
        error("User not found")
        return 1

    # Delete projects and tasks belonging to the user.
    user = User.from_dict(_get_user(data, args.id))  # type: ignore[arg-type]
    for pid in list(user.projects):
        cmd_delete_project(argparse.Namespace(id=pid), _silent=True, _data_override=data)

    data["users"].pop(str(args.id), None)
    save_data(data)
    success(f"User {args.id} deleted")
    return 0


def cmd_add_project(args: argparse.Namespace) -> int:
    data = load_data()
    user_dict = _get_user(data, args.user)
    if user_dict is None:
        error("User not found")
        return 1

    project = Project(title=args.title, description=args.description, due_date=args.due_date)
    data["projects"][str(project.id)] = project.to_dict() | {"user_id": int(args.user)}

    user = User.from_dict(user_dict)
    user.add_project(project.id)
    data["users"][str(user.id)] = user.to_dict()

    save_data(data)
    success(f"Project created with ID {project.id}")
    return 0


def cmd_list_projects(_args: argparse.Namespace) -> int:
    data = load_data()
    projects = []
    for pid, p in data.get("projects", {}).items():
        p_copy = dict(p)
        p_copy["id"] = int(pid) if "id" not in p_copy else p_copy["id"]
        projects.append(p_copy)
    show_projects(projects)
    return 0


def cmd_search_projects(args: argparse.Namespace) -> int:
    data = load_data()
    user = _get_user(data, args.user)
    if user is None:
        error("User not found")
        return 1

    user_obj = User.from_dict(user)
    results: List[dict] = []
    for pid in user_obj.projects:
        p = _get_project(data, pid)
        if p is None:
            continue
        p_copy = dict(p)
        p_copy["id"] = int(pid)
        results.append(p_copy | {"user_id": p_copy.get("user_id", args.user)})
    show_projects(results)
    return 0


def cmd_delete_project(args: argparse.Namespace, _silent: bool = False, _data_override: Dict[str, Any] | None = None) -> int:
    data = _data_override if _data_override is not None else load_data()

    if _get_project(data, args.id) is None:
        if not _silent:
            error("Project not found")
        return 1

    project_dict = _get_project(data, args.id)
    assert project_dict is not None

    # Delete tasks linked to this project.
    for tid, task in list(data.get("tasks", {}).items()):
        if int(task.get("assigned_to", -1)) == int(args.id):
            data["tasks"].pop(str(tid), None)

    # Remove from owning user's projects list.
    user_id = int(project_dict.get("user_id"))
    user_dict = _get_user(data, user_id)
    if user_dict is not None:
        u = User.from_dict(user_dict)
        if args.id in u.projects:
            u.projects.remove(args.id)
            data["users"][str(u.id)] = u.to_dict()

    data["projects"].pop(str(args.id), None)
    if _data_override is None:
        save_data(data)
    return 0


def cmd_add_task(args: argparse.Namespace) -> int:
    data = load_data()
    project = _get_project(data, args.project)
    if project is None:
        error("Project not found")
        return 1

    task = Task(title=args.title, assigned_to=int(args.project))
    data["tasks"][str(task.id)] = task.to_dict()

    proj_obj = Project.from_dict(project)
    proj_obj.add_task(task.id)

    # preserve stored user_id wrapper if present
    user_id = int(project.get("user_id", -1))
    stored = proj_obj.to_dict() | {"user_id": user_id}
    data["projects"][str(args.project)] = stored

    save_data(data)
    success(f"Task created with ID {task.id}")
    return 0


def cmd_list_tasks(args: argparse.Namespace) -> int:
    data = load_data()
    project = _get_project(data, args.project)
    if project is None:
        error("Project not found")
        return 1

    tasks: List[dict] = []
    for t in data.get("tasks", {}).values():
        if int(t.get("assigned_to", -1)) == int(args.project):
            tasks.append(t)

    show_tasks(tasks)
    return 0


def cmd_complete_task(args: argparse.Namespace) -> int:
    data = load_data()
    task = _get_task(data, args.task_id)
    if task is None:
        error("Task not found")
        return 1

    t_obj = Task.from_dict(task)
    t_obj.complete()
    data["tasks"][str(t_obj.id)] = t_obj.to_dict()

    save_data(data)
    success(f"Task {t_obj.id} marked as completed")
    return 0


def cmd_delete_task(args: argparse.Namespace) -> int:
    data = load_data()
    task = _get_task(data, args.id)
    if task is None:
        error("Task not found")
        return 1

    project_id = int(task.get("assigned_to"))
    # remove from project's task list
    project = _get_project(data, project_id)
    if project is not None:
        p_obj = Project.from_dict(project)
        if args.id in p_obj.tasks:
            p_obj.tasks.remove(args.id)
            data["projects"][str(project_id)] = p_obj.to_dict() | {"user_id": int(project.get("user_id", -1))}

    data["tasks"].pop(str(args.id), None)
    save_data(data)
    success(f"Task {args.id} deleted")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # User
    p = sub.add_parser("add-user", help="Create a user")
    p.add_argument("--name", required=True)
    p.add_argument("--email", required=True)
    p.set_defaults(func=cmd_add_user)

    p = sub.add_parser("list-users", help="List users")
    p.set_defaults(func=cmd_list_users)

    p = sub.add_parser("delete-user", help="Delete a user")
    p.add_argument("--id", type=int, required=True)
    p.set_defaults(func=cmd_delete_user)

    # Project
    p = sub.add_parser("add-project", help="Create a project")
    p.add_argument("--user", type=int, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--due-date", required=True)
    p.set_defaults(func=cmd_add_project)

    p = sub.add_parser("list-projects", help="List projects")
    p.set_defaults(func=cmd_list_projects)

    p = sub.add_parser("search-projects", help="Search projects by user")
    p.add_argument("--user", type=int, required=True)
    p.set_defaults(func=cmd_search_projects)

    p = sub.add_parser("delete-project", help="Delete a project")
    p.add_argument("--id", type=int, required=True)
    p.set_defaults(func=lambda a: cmd_delete_project(a))

    # Task
    p = sub.add_parser("add-task", help="Create a task")
    p.add_argument("--project", type=int, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--assigned-to", type=int, required=False)
    # Note: CLI spec says --assigned-to; but model uses assigned_to=project id.
    # We'll accept --assigned-to as optional override of project id.
    p.set_defaults(func=cmd_add_task)

    p = sub.add_parser("list-tasks", help="List tasks for a project")
    p.add_argument("--project", type=int, required=True)
    p.set_defaults(func=cmd_list_tasks)

    p = sub.add_parser("complete-task", help="Mark a task as completed")
    p.add_argument("--task-id", type=int, required=True)
    p.set_defaults(func=cmd_complete_task)

    p = sub.add_parser("delete-task", help="Delete a task")
    p.add_argument("--id", type=int, required=True)
    p.set_defaults(func=cmd_delete_task)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Handle the slight mismatch in requested CLI args for add-task.
    if hasattr(args, "assigned_to") and args.assigned_to is not None:
        # If assigned-to provided, treat it as project id override.
        args.project = int(args.assigned_to)

    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

