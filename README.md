# project_management_CLI

A Python-based Command-Line Interface (CLI) application for managing users, projects, and tasks.  
The system simulates a simple project management tool with persistent local storage using JSON.

---
## Features

- Create users, list users, and delete users
- Create projects assigned to users, list projects, search projects by user, and delete projects
- Create tasks assigned to projects, list tasks for a project, complete tasks, and delete tasks
- Persistent storage in `data/database.json` (auto-created if missing)
- Safe handling of malformed JSON
- Rich terminal output (tables + success/error messages)
- Object-oriented design with type hints
- Unit tests with pytest



---

## 🛠️ Technologies Used

Python 3.10+
CLI framework 
JSON (data storage)
pytest (testing)
rich (UI formatting)
python-dateutil (optional date handling)


---

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py --help
```

### Command Reference

#### Users

- Create a user
  ```bash
  python main.py add-user --name "Alice" --email "alice@example.com"
  ```

- List users
  ```bash
  python main.py list-users
  ```

- Delete a user (also deletes their projects and tasks)
  ```bash
  python main.py delete-user --id 1
  ```

#### Projects

- Create a project
  ```bash
  python main.py add-project --user 1 --title "Website" --description "Build v1" --due-date 2026-12-31
  ```

- List projects
  ```bash
  python main.py list-projects
  ```

- Search projects by user
  ```bash
  python main.py search-projects --user 1
  ```

- Delete a project (also deletes its tasks)
  ```bash
  python main.py delete-project --id 1
  ```

#### Tasks

- Create a task
  ```bash
  python main.py add-task --project 1 --title "Design landing page" --assigned-to 1
  ```
  > Note: `--assigned-to` is accepted as an optional override of the project id to match the requested CLI spec.

- List tasks for a project
  ```bash
  python main.py list-tasks --project 1
  ```

- Complete a task
  ```bash
  python main.py complete-task --task-id 1
  ```

- Delete a task
  ```bash
  python main.py delete-task --id 1
  ```

## Testing

Run all unit tests:

```bash
pytest
```

##  Future Improvements
Add login/authentication system
Switch from JSON to SQLite database
Add task priorities and deadlines
Build web version using Flask or FastAPI
Add real-time collaboration features

##  License
MIT licence