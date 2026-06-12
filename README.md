# Project Management CLI Tool

A lightweight, extensible Python CLI application for managing users, projects, tasks, and contributors — with JSON-backed persistence and a terminal-first workflow.

## Features

- User management with `add-user`, `list-users`, and `remove-user`
- Project management with `add-project`, `list-projects`, `remove-project`, and `search-projects`
- Task management with `add-task`, `list-tasks`, `complete-task`, and `remove-task`
- Contributor tracking with `add-contributor` and `remove-contributor`
- Local JSON persistence under `data/projects.json`
- Pretty console output via `rich`
- Debug mode via global `--debug` flag

## Tech Stack

- **Language:** Python 3.10+
- **CLI Framework:** Click / Typer
- **Output:** Rich
- **Storage:** JSON (local file)
- **Testing:** pytest

## Prerequisites

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation

### Local Setup

1. **Clone repository**

```
git clone https://github.com/favourkendi-dev/project-management-cli.git
cd project-management-cli
```

2. **Install dependencies**

```
python3 -m pip install -r requirements.txt
```

3. **Run the application**

```
python3 main.py --help
```

## Usage

The entrypoint is `main.py`. Enable debug logging with the global `--debug` flag.

### Users

```
# Add a user
python3 main.py add-user --name "Alex" --email "alex123@gmail.com"

# List all users
python3 main.py list-users

# Remove a user
python3 main.py remove-user --name "Alex"
```

### Projects

```
# Create a project
python3 main.py add-project --user "Alex" --title "CLI Tool" --due-date "2026-06-30"

# List projects
python3 main.py list-projects --user "Alex"

# Search projects
python3 main.py search-projects --user "Alex" --query "cli"

# Remove a project
python3 main.py remove-project --user "Alex" --title "CLI Tool"
```

### Tasks

```
# Add a task
python3 main.py add-task --user "Alex" --project "CLI Tool" --title "Implement add-task"

# List tasks
python3 main.py list-tasks --user "Alex" --project "CLI Tool"

# Complete a task
python3 main.py complete-task --user "Alex" --project "CLI Tool" --task "Implement add-task"

# Remove a task
python3 main.py remove-task --user "Alex" --project "CLI Tool" --task "Implement add-task"
```

### Contributors

```
# Add a contributor
python3 main.py add-contributor --user "Alex" --project "CLI Tool" --task "Implement add-task" --contributor "Jordan"

# Remove a contributor
python3 main.py remove-contributor --user "Alex" --project "CLI Tool" --task "Implement add-task" --contributor "Jordan"
```

## Project Structure

project_management_cli/
├── main.py                  # Application entry point
├── project_manager/
│   ├── cli.py               # CLI interface logic
│   ├── models/              # User, Project, and Task classes
│   └── services/            # Manager business logic & Storage persistence
├── data/
│   └── projects.json        # Local JSON storage (auto-created)
└── tests/                   # Unit tests for models, services, and CLI

## Testing

```
# Run all tests
pytest

# Run quietly with path context
PYTHONPATH=. pytest -q

# Run a specific test file
pytest tests/test_cli.py -v
```

## Storage

- Data is persisted locally in `data/projects.json`
- The file is created automatically if it does not exist
- Export/import the file directly for backup or sharing

## Troubleshooting

**Import errors when running tests:**

```
PYTHONPATH=. pytest -q
```

**`data/projects.json` not found:**

The file is created automatically on first run. If issues persist, ensure the `data/` directory exists at the project root.

## Contributing

1. Create a feature branch: `git checkout -b feature/description`
2. Make changes with descriptive commits
3. Push: `git push origin feature/description`
4. Open a Pull Request
5. Await code review & approval

## License

MIT License