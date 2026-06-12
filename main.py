import sys

from project_manager.cli import main


def run_application() -> None:
    """Application entry point. Delegates execution to the CLI layer."""
    sys.exit(main())


if __name__ == "__main__":
    run_application()