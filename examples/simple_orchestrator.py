#!/usr/bin/env python3
"""
Trinity Protocol v0.5 — Reference Orchestrator

Demonstrates chaining Trinity CLI commands programmatically to complete a full
workflow: session → snapshot → sandbox apply → verify → promote → close.

Usage:
  python .ai/examples/simple_orchestrator.py --task "Fix Auth Bug" \
      --patch sessions/examples/2025-12-22_sandbox_demo/SANDBOX/codex/patch.diff

  python .ai/examples/simple_orchestrator.py --quick "Small Fix"
"""
from __future__ import annotations
import subprocess
import shlex
import sys
import json
from dataclasses import dataclass
from pathlib import Path


CLI = str((Path(".ai") / "cli" / "ai").resolve())


@dataclass
class CommandResult:
    code: int
    out: str
    err: str


def run_ai_command(cmd: str) -> CommandResult:
    """Run a Trinity CLI command via the ai wrapper (uses venv if on PATH).

    Returns CommandResult with exit code and captured output.
    """
    full_cmd = cmd if cmd.startswith(CLI) else f"{CLI} {cmd}"
    proc = subprocess.Popen(
        shlex.split(full_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    out, err = proc.communicate()
    return CommandResult(proc.returncode, out.strip(), err.strip())


def create_session(name: str) -> str:
    print(f"├── [1/7] Creating session... ", end="", flush=True)
    res = run_ai_command(f"session new \"{name}\"")
    if res.code != 0:
        print("❌")
        print(res.err or res.out)
        raise SystemExit(1)
    # retrieve session path
    path_res = run_ai_command("status path")
    if path_res.code != 0 or not path_res.out:
        print("❌")
        print(path_res.err or path_res.out)
        raise SystemExit(1)
    print("✅")
    return path_res.out


def _copy_patch_to_session(patch_path: str, session_path: str) -> bool:
    src = Path(patch_path)
    if not src.exists():
        return False
    dst = Path(session_path) / "SANDBOX" / "codex" / "patch.diff"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def run_full_workflow(task_name: str, patch_path: str | None = None) -> bool:
    print(f"🚀 Starting Trinity Workflow: {task_name}")
    session_path = create_session(task_name)

    print("├── [2/7] Running snapshot... ", end="", flush=True)
    snap = run_ai_command("snapshot run")
    if snap.code != 0:
        print("❌\n" + (snap.err or snap.out))
        return False
    print("✅")

    print("├── [3/7] Applying patch... ", end="", flush=True)
    applied = False
    if patch_path:
        _copy_patch_to_session(patch_path, session_path)
        dry = run_ai_command("sandbox apply codex --dry-run")
        if dry.code != 0:
            print("❌\n" + (dry.err or dry.out))
            return False
        app = run_ai_command("sandbox apply codex")
        if app.code != 0:
            print("❌\n" + (app.err or app.out))
            return False
        applied = True
    print("✅" if applied else "⚠️  (skipped)")

    print("├── [4/7] Verifying dev... ", end="", flush=True)
    vdev = run_ai_command("verify dev")
    if vdev.code != 0:
        print("❌\n" + (vdev.err or vdev.out))
        return False
    print("✅")

    print("├── [5/7] Promoting to prod... ", end="", flush=True)
    prom = run_ai_command("promote run") if "promote run" in (CLI,) else run_ai_command("promote")
    if prom.code != 0:
        print("❌\n" + (prom.err or prom.out))
        return False
    print("✅")

    print("├── [6/7] Verifying prod... ", end="", flush=True)
    vprod = run_ai_command("verify prod")
    if vprod.code != 0:
        print("❌\n" + (vprod.err or vprod.out))
        return False
    print("✅")

    print("└── [7/7] Closing session... ", end="", flush=True)
    close = run_ai_command("close run")
    if close.code != 0:
        print("❌\n" + (close.err or close.out))
        return False
    print("✅")

    print("✅ Workflow complete! Session archived.")
    return True


def run_quick_workflow(task_name: str) -> bool:
    """Quick path without patch apply/debate (direct edit or empty change)."""
    return run_full_workflow(task_name, patch_path=None)


def _parse_args(argv: list[str]) -> dict:
    import argparse
    p = argparse.ArgumentParser(description="Trinity v0.5 Reference Orchestrator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--task", help="Task name for full workflow")
    g.add_argument("--quick", help="Task name for quick workflow (no patch)")
    p.add_argument("--patch", help="Path to unified diff to apply", default=None)
    return vars(p.parse_args(argv))


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    if args.get("task"):
        ok = run_full_workflow(args["task"], args.get("patch"))
        sys.exit(0 if ok else 1)
    else:
        ok = run_quick_workflow(args["quick"])  # type: ignore[arg-type]
        sys.exit(0 if ok else 1)

