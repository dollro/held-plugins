#!/usr/bin/env python
"""Django's command-line utility. Run from the repo root: python backend/manage.py <cmd>."""

import os
import sys
from pathlib import Path


def main() -> None:
    # The repo root must be importable so that `backend.*` and `realtime.*` resolve.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
