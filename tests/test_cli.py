import pytest
from pathlib import Path
from rich.console import Console
from project_manager.services.storage import Storage
from project_manager.services.manager import Manager
from project_manager.cli import CLI

@pytest.fixture
def cli_engine(tmp_path: Path):
    db_file = tmp_path / "cli_db.json"
    storage = Storage(db_file)
    manager = Manager(storage)
    console = Console(record=True, width=120)
    return CLI(manager, console), console

def test_cli_e2e_user_and_project_flow(cli_engine):
    cli, console = cli_engine
    
    assert cli.run(["add-user", "--name", "Emmanuel", "--email", "emmanuel@example.com"]) == 0
    assert "User 'Emmanuel' added successfully" in console.export_text()
    
    assert cli.run(["add-project", "--user", "Emmanuel", "--title", "Core Engine"]) == 0
    assert "Project 'Core Engine' created" in console.export_text()

    assert cli.run(["add-task", "--user", "Emmanuel", "--project", "Core Engine", "--title", "CLI Layout"]) == 0
    assert "Task 'CLI Layout' added" in console.export_text()
    
    assert cli.run(["search-projects", "--user", "Emmanuel", "--query", "core"]) == 0
    assert "Core Engine" in console.export_text()

    assert cli.run(["add-user", "--name", "Emmanuel"]) == 1
    assert "Error:" in console.export_text()
