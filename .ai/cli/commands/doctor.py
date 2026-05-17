"""ai doctor — runtime sanity checks for the CLI contract.

The `commands` subcommand walks the `doctor_survey` block in
`.ai/cli/COMMAND_MANIFEST.yaml`, invokes each survey entry via
`python3 -m cli.main ...`, and reports PASS/FAIL per entry.

Exists because the ritual language (sss / vvv / nnn / gogogo / ddd / rrr)
and the executable CLI surface have drifted in the past. The manifest
is the source of truth; this command is the runtime verifier.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

import typer
import yaml
from rich.console import Console
from rich.table import Table


app = typer.Typer(help="Runtime sanity checks for the Trinity CLI contract.")
console = Console()


def _find_repo_root(start: Path) -> Path:
    """Walk upward until we find the .ai/cli/COMMAND_MANIFEST.yaml marker."""
    here = start.resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".ai" / "cli" / "COMMAND_MANIFEST.yaml").exists():
            return candidate
    return here


def _load_manifest(repo_root: Path) -> dict:
    path = repo_root / ".ai" / "cli" / "COMMAND_MANIFEST.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Command manifest not found at {path}. "
            "Cannot verify CLI contract."
        )
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _run_cli(repo_root: Path, argv: List[str], timeout: float = 20.0) -> int:
    """Invoke `python3 -m cli.main <argv>` from inside the .ai/ directory.

    The kernel CLI expects to be run with `.ai/` as cwd (where `cli`
    package is importable). Returns the exit code; on timeout/oserror
    returns -1.
    """
    cli_root = repo_root / ".ai"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", *argv],
            cwd=str(cli_root),
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode
    except (subprocess.TimeoutExpired, OSError):
        return -1


@app.callback()
def callback():
    """Trinity doctor — runtime CLI contract checks."""
    return


@app.command()
def commands(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Print full survey table even when all PASS."
    ),
):
    """Walk the COMMAND_MANIFEST survey and report PASS/FAIL per entry.

    Exit 0 if every survey entry exits cleanly; exit 1 otherwise.
    Useful as a CI / pre-flight check to catch ritual ↔ command drift
    before agents trip over it at runtime.
    """
    repo_root = _find_repo_root(Path.cwd())
    try:
        manifest = _load_manifest(repo_root)
    except FileNotFoundError as e:
        console.print(f"[red]ERROR:[/red] {e}")
        raise typer.Exit(code=2)

    survey = manifest.get("doctor_survey") or []
    if not survey:
        console.print(
            "[yellow]WARN:[/yellow] manifest has no `doctor_survey` block — nothing to check."
        )
        raise typer.Exit(code=0)

    table = Table(title="CLI Command Contract Check", show_lines=False)
    table.add_column("Result", style="bold", no_wrap=True)
    table.add_column("Command", style="cyan")
    table.add_column("Exit", justify="right")

    failures: List[str] = []
    for entry in survey:
        # Survey entries are lists of argv tokens; tolerate a string form.
        if isinstance(entry, str):
            argv = entry.split()
        else:
            argv = [str(t) for t in entry]

        rc = _run_cli(repo_root, argv)
        if rc == 0:
            verdict = "[green]PASS[/green]"
        else:
            verdict = "[red]FAIL[/red]"
            failures.append(" ".join(argv))
        table.add_row(verdict, "ai " + " ".join(argv), str(rc))

    if failures or verbose:
        console.print(table)
    else:
        console.print(
            f"[green]✓[/green] CLI contract OK — {len(survey)} survey entries all PASS."
        )

    if failures:
        console.print(
            f"\n[red]✗ {len(failures)} command(s) failed:[/red] " + ", ".join(failures)
        )
        console.print(
            "\nLikely cause: drift between .ai/cli/COMMAND_MANIFEST.yaml "
            "and the registered Typer apps in .ai/cli/main.py. "
            "Update one or the other so they agree."
        )
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)
