"""ai doctor — runtime sanity checks for the CLI contract.

The `commands` subcommand walks the `doctor_survey` block in
`.ai/cli/COMMAND_MANIFEST.yaml`, invokes each survey entry via
`python3 -m cli.main ...`, and reports PASS/FAIL per entry.

Exists because the ritual language (sss / vvv / nnn / gogogo / ddd / rrr)
and the executable CLI surface have drifted in the past. The manifest
is the source of truth; this command is the runtime verifier.
"""
from __future__ import annotations

import json
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
    """Find the dir holding .ai/cli/COMMAND_MANIFEST.yaml.

    Preference: cwd ancestors (operator PWD wins). Fallback: the kernel source
    root, derived from this file's location — needed for THIN projects whose cwd
    has no local .ai/cli (the kernel resolves from the central runtime). Mirrors
    sss._find_git_root.
    """
    here = start.resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".ai" / "cli" / "COMMAND_MANIFEST.yaml").exists():
            return candidate
    # fallback: kernel source root (.ai/cli/commands/doctor.py -> core/trinity_v2)
    kernel_root = Path(__file__).resolve().parents[3]
    if (kernel_root / ".ai" / "cli" / "COMMAND_MANIFEST.yaml").exists():
        return kernel_root
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
    """Invoke `python3 -m cli.main <argv>` against the CALLER'S project.

    Importability comes from PYTHONPATH=<kernel .ai> (the same contract the
    thin-client `.ai/ai` shim uses); the working directory stays the
    operator's project so every probe exercises the command exactly as the
    operator would run it. Before 2026-06-10 probes ran with cwd=<kernel
    .ai>, which made state-reading commands (audit verify-chain/replay)
    inspect the KERNEL's own (intentionally absent) audit chain on thin
    clients — a false FAIL that pointed at the wrong chain.
    Returns the exit code; on timeout/oserror returns -1.
    """
    import os

    cli_root = repo_root / ".ai"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cli_root) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    try:
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", *argv],
            cwd=str(Path.cwd()),
            env=env,
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


# Durable-state siblings whose state lives under central_root/state/<name> (R12).
_CENTRAL_SIBLINGS = [
    "task-cli", "brain-cli", "notify-cli", "tg-bot",
    "judge-cli", "seo-genie-cli", "image-cli", "wordpress-cli",
]


@app.command()
def resources(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
):
    """Report where each kernel-fallback-eligible .ai resource resolves from.

    For the cwd project, each resource is shown as project (project-local
    file present), kernel (thin client — kernel-shipped default in use), or
    missing (neither exists). Read-only; prints no fallback notes itself.
    """
    import json as _json

    from ..core.kernel_resource import FALLBACK_RESOURCES, resolve_ai_resource

    project_root = Path.cwd()
    rows = []
    for label, rel in FALLBACK_RESOURCES:
        path, source = resolve_ai_resource(
            project_root, rel, label=label, quiet=True
        )
        rows.append({
            "resource": label,
            "rel": f".ai/{rel}",
            "source": source,
            "path": str(path) if path else None,
        })
    if json_out:
        typer.echo(_json.dumps({"project_root": str(project_root), "resources": rows}, indent=2))
        return
    from rich.console import Console
    from rich.table import Table

    table = Table(title=f"resource resolution · {project_root}")
    table.add_column("resource")
    table.add_column("source")
    table.add_column("path")
    for r in rows:
        style = {"project": "green", "kernel": "yellow", "missing": "red"}[r["source"]]
        table.add_row(r["resource"], f"[{style}]{r['source']}[/{style}]", r["path"] or "—")
    Console().print(table)
    # ssot.yaml is intentionally NOT fallback-eligible (project identity,
    # retro-0056); surface its presence for completeness.
    ssot = project_root / ".ai" / "ssot.yaml"
    Console().print(
        f"ssot.yaml (identity, no fallback): "
        f"{'present' if ssot.exists() else '[red]MISSING[/red]'}"
    )


@app.command()
def central(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
):
    """Check central_root health (R12): durable state location + integrity.

    Read-only (passive core — never migrates). Verifies central_root holds
    memory/, the task-cli db, the registry, and the durable siblings' state, and
    detects split data still living under runtime_root (run `ai migrate-state
    --apply` to consolidate).
    """
    # Imported lazily so `ai doctor commands` has no central-resolver dependency.
    from ..core.runtime_home import resolve_central_home, resolve_runtime_home

    central_root = resolve_central_home()
    checks = {
        "central_root_exists": central_root.exists(),
        "memory": (central_root / "memory").exists(),
        "task_db": (central_root / "state" / "task-cli" / "tasks.db").exists(),
        "registry": (central_root / "registry" / "projects.json").exists(),
    }
    sibling_state = {s: (central_root / "state" / s).exists() for s in _CENTRAL_SIBLINGS}

    # split-data detection: durable state still under runtime_root (non-strict —
    # an unconfigured runtime simply yields no split).
    runtime_root = resolve_runtime_home(strict=False)
    split = {}
    if runtime_root is not None:
        split = {
            "memory_under_runtime": (runtime_root / "memory").exists(),
            "task_under_runtime": (runtime_root / "state" / "task-cli").exists(),
        }
    has_split = any(split.values())

    if json_out:
        console.print_json(json.dumps({
            "ok": True,
            "central_root": str(central_root),
            "runtime_root": str(runtime_root) if runtime_root else None,
            "checks": checks,
            "sibling_state": sibling_state,
            "split": split,
            "has_split_durable_data": has_split,
        }))
        raise typer.Exit(code=0)

    console.print(f"[bold]central-root health[/bold] · {central_root}")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Status", justify="center")
    rows = {**checks, **{f"state/{s}": sibling_state[s] for s in _CENTRAL_SIBLINGS}}
    for k, v in rows.items():
        table.add_row(k, "[green]✓[/green]" if v else "[yellow]·[/yellow]")
    console.print(table)
    if has_split:
        console.print(
            "[yellow]⚠ split durable data under runtime_root — "
            "run `ai migrate-state --apply` to consolidate.[/yellow]"
        )
    else:
        console.print("[green]✓ no split durable data[/green]")
    raise typer.Exit(code=0)
