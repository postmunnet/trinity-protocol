"""Module entry-point: enables `python -m cli.agents.session_bootstrap ...`."""
from cli.agents.session_bootstrap.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
