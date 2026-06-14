"""`ai config` — declare and inspect the Trinity runtime location.

The runtime root is where ALL runtime state lives (siblings + kernel central
homes). Config is mandatory; nothing auto-detects into home.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..core.runtime_home import (
    RuntimeNotConfiguredError,
    resolve_central_home,
    resolve_runtime_home,
    write_runtime_yaml,
)

app = typer.Typer(help="Declare/inspect the Trinity runtime location.")
console = Console()


@app.command("set-runtime")
def set_runtime(
    path: Path = typer.Argument(..., help="Folder to use as the Trinity runtime root (STATE)."),
    instance: Optional[Path] = typer.Option(
        None, "--instance", help="Instance dir to write .ai/runtime.yaml into (default: cwd)."
    ),
    code: Optional[Path] = typer.Option(
        None, "--code", help="CODE root of the central runtime (read by the .ai/ai shim to exec the kernel)."
    ),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    instance_root = (instance or Path.cwd()).expanduser().resolve()
    runtime_root = path.expanduser().resolve()
    runtime_code = code.expanduser().resolve() if code is not None else None
    yaml_path = write_runtime_yaml(instance_root, runtime_root, runtime_code)
    if json_out:
        console.print_json(
            json.dumps(
                {
                    "ok": True,
                    "runtime_root": str(runtime_root),
                    "runtime_code": str(runtime_code) if runtime_code else None,
                    "runtime_yaml": str(yaml_path),
                }
            )
        )
    else:
        console.print(f"[green]✓[/green] runtime root set: [bold]{runtime_root}[/bold]")
        if runtime_code:
            console.print(f"  code root: [bold]{runtime_code}[/bold]")
        console.print(f"  declared in: {yaml_path}")


@app.command("show")
def show(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    try:
        root = resolve_runtime_home(strict=True)
    except RuntimeNotConfiguredError as e:
        if json_out:
            console.print_json(json.dumps({"ok": False, "error": {"code": e.code, "message": str(e)}}))
        else:
            console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(code=1)
    if json_out:
        console.print_json(json.dumps({"ok": True, "runtime_root": str(root)}))
    else:
        console.print(f"runtime root: [bold]{root}[/bold]")


@app.command("paths")
def paths(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Report runtime_root + central_root + derived homes, and flag split data.

    central_root (durable: memory/task/registry) is independent of the runtime
    channel — see design §12 Central-Root Doctrine. This is the R12 Phase-1
    observability surface; no data is moved.
    """
    try:
        runtime = resolve_runtime_home(strict=True)
    except RuntimeNotConfiguredError:
        runtime = None
    central = resolve_central_home()

    central_memory = central / "memory"
    central_task = central / "state" / "task-cli"
    central_registry = central / "registry"

    # split-data detection: durable state still living under runtime_root
    split = []
    if runtime is not None:
        if (runtime / "memory").exists():
            split.append(str(runtime / "memory"))
        if (runtime / "state" / "task-cli").exists():
            split.append(str(runtime / "state" / "task-cli"))

    if json_out:
        console.print_json(json.dumps({
            "ok": True,
            "runtime_root": str(runtime) if runtime else None,
            "central_root": str(central),
            "central_memory_home": str(central_memory),
            "central_task_state": str(central_task),
            "central_registry_home": str(central_registry),
            "split_data_under_runtime": split,
        }))
        return

    console.print(f"runtime_root : [bold]{runtime or '(unconfigured)'}[/bold]")
    console.print(f"central_root : [bold]{central}[/bold]")
    console.print(f"  memory     : {central_memory}")
    console.print(f"  task state : {central_task}")
    console.print(f"  registry   : {central_registry}")
    if split:
        console.print(f"[yellow]⚠ split data under runtime_root (migrate to central — R12 Phase 2):[/yellow]")
        for s in split:
            console.print(f"    {s}")
    else:
        console.print("[green]✓ no split durable data under runtime_root[/green]")
