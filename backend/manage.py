#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Ensure project root is in sys.path for importing 'simulation' package
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        # pyrefly: ignore [missing-import]
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    if len(sys.argv) > 1 and sys.argv[1] == "runserver" and os.environ.get("RUN_MAIN") != "true":
        print("\033[38;5;117m\033[1m╭" + "─" * 60 + "╮")
        print("│  ✨ IDR Backend Server Active ✨      │")
        print("│  💖 Base URL:  http://127.0.0.1:8000/api/v1/               │")
        print("│  🚀 Swagger:   http://127.0.0.1:8000/api/docs/             │")
        print("╰" + "─" * 60 + "╯\033[0m\n")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
