import json
import subprocess
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_cli_in_tmp(tmp_path: Path, args: list[str]) -> subprocess.CompletedProcess:
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    db_file = data_dir / "projects.json"
    if not db_file.exists():
        db_file.write_text(json.dumps({"users": []}))
    repo = _repo_root()
    proc = subprocess.run([sys.executable, str(repo / "main.py")] + args, cwd=tmp_path, capture_output=True, text=True)
    return proc


def test_cli_add_and_list_users(tmp_path: Path):
    proc = run_cli_in_tmp(tmp_path, ["add-user", "--name", "CliUser", "--email", "cli@example.com"])
    assert proc.returncode == 0

    proc = run_cli_in_tmp(tmp_path, ["list-users"])
    assert proc.returncode == 0
    assert "CliUser" in proc.stdout


def test_cli_project_task_flow(tmp_path: Path):
    # Add user
    proc = run_cli_in_tmp(tmp_path, ["add-user", "--name", "FlowUser"])
    assert proc.returncode == 0

    # Add project
    proc = run_cli_in_tmp(tmp_path, ["add-project", "--user", "FlowUser", "--title", "Flow Project"])
    assert proc.returncode == 0

    # Add task
    proc = run_cli_in_tmp(tmp_path, ["add-task", "--user", "FlowUser", "--project", "Flow Project", "--title", "Flow Task"])
    assert proc.returncode == 0

    # Show task
    proc = run_cli_in_tmp(tmp_path, ["show-task", "--user", "FlowUser", "--project", "Flow Project", "--task", "Flow Task"])
    assert proc.returncode == 0
    assert "Flow Task" in proc.stdout
