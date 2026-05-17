"""Pytest config for Trinity CLI tests.

Resolves two cwd-sensitive concerns at once:

1. ``test_basic.py`` uses paths like ``.ai/state/status.json`` and assumes
   the cwd is the repo root.
2. ``test_session_naming.py`` uses ``from cli.core.session_naming import ...``
   which requires ``.ai/`` to be on ``sys.path``.

This conftest pins both regardless of the cwd pytest is invoked from
(repo root *or* ``.ai/``).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# conftest is at <repo>/.ai/cli/tests/conftest.py
TESTS_DIR = Path(__file__).resolve().parent
AI_DIR = TESTS_DIR.parent.parent          # <repo>/.ai
REPO_ROOT = AI_DIR.parent                  # <repo>

# Ensure `from cli.core...` works no matter where pytest started.
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

# Pin cwd to repo root so legacy tests using `.ai/...` paths resolve.
os.chdir(REPO_ROOT)
