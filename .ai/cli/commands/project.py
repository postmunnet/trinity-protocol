from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.project_agent_shim import (
    AgentShimError,
    install_project_agent_shims,
    install_project_trinity_wrapper,
)
from ..core.project_binding import (
    ProjectBinding,
    binding_path_for,
    ensure_project_dirs,
    read_project_binding,
    write_project_binding,
)
from ..core.project_registry import (
    ProjectRegistry,
    default_memory_home,
    default_trinity_home,
    touch_memory_db,
)
from ..core.project_resolver import (
    ProjectResolutionError,
    ResolvedProject,
    resolve_current_project,
)


app = typer.Typer(help="Register and inspect Trinity project bindings.")
console = Console()


@app.command("add")
def add_project(
    path: Path = typer.Argument(..., help="Project path to bind to Trinity."),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Human project name. Defaults to root basename."
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite an existing .trinity/project.yaml binding."
    ),
    json_out: bool = typer.Option(
        False, "--json", help="Print machine-readable JSON output."
    ),
    agent_shim: bool = typer.Option(
        True,
        "--agent-shim/--no-agent-shim",
        help="Install or update the Trinity-managed AGENTS.md block.",
    ),
    wrapper: bool = typer.Option(
        True,
        "--wrapper/--no-wrapper",
        help="Install or update the project-local ./trinity wrapper.",
    ),
) -> None:
    """Register a project and create its local Trinity binding files."""
    root = _detect_project_root(path)
    project_name = name or root.name
    trinity_home = default_trinity_home()
    memory_home = default_memory_home()
    registry = ProjectRegistry.default()
    binding_path = binding_path_for(root)
    if binding_path.exists() and not force:
        raise typer.BadParameter(f"project binding already exists: {binding_path}")

    record = registry.register_project(
        project_name=project_name,
        root_path=root,
        binding_path=binding_path,
        memory_home=memory_home,
    )
    binding = ProjectBinding(
        project_id=record.project_id,
        project_slug=record.project_slug,
        project_name=record.project_name,
        root_path=record.root_path,
        trinity_home=trinity_home,
        memory_home=record.memory_home,
        memory_db_path=record.memory_db_path,
        binding_path=record.binding_path,
        trinity_version=record.trinity_version,
    )
    write_project_binding(binding, force=force)
    ensure_project_dirs(root)
    touch_memory_db(record.memory_db_path)
    agent_shim_paths = []
    if agent_shim:
        try:
            agent_shim_paths = install_project_agent_shims(root, binding)
        except AgentShimError as e:
            raise typer.BadParameter(str(e))
    wrapper_path = install_project_trinity_wrapper(root, binding) if wrapper else None

    payload = _record_payload(record)
    payload["binding_path"] = str(binding.binding_path)
    payload["agent_shim_paths"] = [str(p) for p in agent_shim_paths]
    payload["wrapper_path"] = str(wrapper_path) if wrapper_path else None
    if json_out:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    console.print(
        f"[green]registered[/green] [bold]{record.project_slug}[/bold] "
        f"→ {record.root_path}"
    )
    console.print(f"binding: {binding.binding_path}")
    console.print(f"memory:  {record.memory_db_path}")
    for idx, path in enumerate(agent_shim_paths):
        label = "agents" if idx == 0 else "       "
        console.print(f"{label}:  {path}")
    if wrapper_path:
        console.print(f"wrapper: {wrapper_path}")


@app.command("list")
def list_projects(
    json_out: bool = typer.Option(
        False, "--json", help="Print machine-readable JSON output."
    ),
) -> None:
    """List registered projects."""
    registry = ProjectRegistry.default()
    rows = registry.list_projects()
    if json_out:
        print(json.dumps([_record_payload(r) for r in rows], indent=2, ensure_ascii=False))
        return
    table = Table(title="Trinity Projects")
    table.add_column("slug", style="cyan")
    table.add_column("name")
    table.add_column("root")
    table.add_column("memory db")
    for row in rows:
        table.add_row(
            row.project_slug,
            row.project_name,
            str(row.root_path),
            str(row.memory_db_path),
        )
    console.print(table)


@app.command("current")
def current_project(
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Resolve an explicit registered project."
    ),
    json_out: bool = typer.Option(
        False, "--json", help="Print machine-readable JSON output."
    ),
) -> None:
    """Show the current project identity and memory DB path."""
    try:
        resolved = resolve_current_project(project_ref=project)
    except ProjectResolutionError as e:
        console.print(f"[red]ERROR:[/red] {e}", err=True)
        raise typer.Exit(code=2)
    if json_out:
        print(json.dumps(_resolved_payload(resolved), indent=2, ensure_ascii=False))
        return
    _print_resolved(resolved)


@app.command("doctor")
def doctor_project(
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Check an explicit registered project."
    ),
    json_out: bool = typer.Option(
        False, "--json", help="Print machine-readable JSON output."
    ),
) -> None:
    """Check that registry, local binding, and memory DB path agree."""
    checks = []
    try:
        resolved = resolve_current_project(project_ref=project, allow_fallback=False)
        checks.append(("resolve", True, f"{resolved.project_slug} via {resolved.source}"))
    except ProjectResolutionError as e:
        payload = {"ok": False, "checks": [{"name": "resolve", "ok": False, "detail": str(e)}]}
        if json_out:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            console.print(f"[red]ERROR:[/red] {e}", err=True)
        raise typer.Exit(code=2)

    checks.append(("registered", resolved.registered, str(resolved.registry_path or "")))
    checks.append(("root_exists", resolved.root_path.exists(), str(resolved.root_path)))
    checks.append((
        "binding_exists",
        bool(resolved.binding_path and resolved.binding_path.exists()),
        str(resolved.binding_path or ""),
    ))
    checks.append(("memory_db_exists", resolved.memory_db_path.exists(), str(resolved.memory_db_path)))

    if resolved.binding_path and resolved.binding_path.exists():
        try:
            binding = read_project_binding(resolved.binding_path)
            binding_ok = (
                binding.project_slug == resolved.project_slug
                and binding.root_path == resolved.root_path
                and binding.memory_db_path == resolved.memory_db_path
            )
            checks.append(("binding_matches", binding_ok, str(resolved.binding_path)))
        except Exception as e:
            checks.append(("binding_matches", False, str(e)))

    ok = all(row[1] for row in checks)
    payload = {
        "ok": ok,
        "project": _resolved_payload(resolved),
        "checks": [
            {"name": name, "ok": check_ok, "detail": detail}
            for name, check_ok, detail in checks
        ],
    }
    if json_out:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        table = Table(title="Trinity Project Doctor")
        table.add_column("check")
        table.add_column("result")
        table.add_column("detail")
        for name, check_ok, detail in checks:
            table.add_row(name, "[green]PASS[/green]" if check_ok else "[red]FAIL[/red]", detail)
        console.print(table)
    if not ok:
        raise typer.Exit(code=1)


def _detect_project_root(path: Path) -> Path:
    start = Path(path).expanduser().resolve()
    if not start.exists():
        raise typer.BadParameter(
            f"project path must exist on this machine: {start}. "
            "For a remote host path, run Trinity on that host, mount the path locally, "
            "or add remote-project support first."
        )
    if start.is_file():
        start = start.parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return start
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return start


def _record_payload(record) -> Dict[str, Any]:
    return {
        "project_id": record.project_id,
        "project_slug": record.project_slug,
        "project_name": record.project_name,
        "root_path": str(record.root_path),
        "binding_path": str(record.binding_path),
        "memory_home": str(record.memory_home),
        "memory_db_path": str(record.memory_db_path),
        "trinity_version": record.trinity_version,
        "status": record.status,
        "created_at": record.created_at,
        "last_used_at": record.last_used_at,
    }


def _resolved_payload(project: ResolvedProject) -> Dict[str, Any]:
    return {
        "project_id": project.project_id,
        "project_slug": project.project_slug,
        "project_name": project.project_name,
        "root_path": str(project.root_path),
        "memory_home": str(project.memory_home),
        "memory_db_path": str(project.memory_db_path),
        "trinity_home": str(project.trinity_home),
        "source": project.source,
        "registered": project.registered,
        "binding_path": str(project.binding_path) if project.binding_path else None,
        "registry_path": str(project.registry_path) if project.registry_path else None,
    }


def _print_resolved(project: ResolvedProject) -> None:
    console.print(f"[bold]Project:[/bold] {project.project_slug}")
    console.print(f"[bold]Name:[/bold] {project.project_name}")
    console.print(f"[bold]Source:[/bold] {project.source}")
    console.print(f"[bold]Root:[/bold] {project.root_path}")
    console.print(f"[bold]Binding:[/bold] {project.binding_path or '—'}")
    console.print(f"[bold]Registry:[/bold] {project.registry_path or '—'}")
    console.print(f"[bold]Memory DB:[/bold] {project.memory_db_path}")
