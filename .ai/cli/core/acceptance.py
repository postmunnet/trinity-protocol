"""Phase 1.5 — executable acceptance (R11).

Spec ref: docs/migration/08_PHASE2_MEMORY_CLI_ALPHA.md (R11 schema)
          .ai/shims/rrr/SHIM.md (rrr executes acceptance gate)

Replaces the free-form `THINK/03_ACCEPTANCE.md` (aspirational prose)
with `THINK/03_ACCEPTANCE.yaml` (parseable + executable). `ai rrr`
loads the YAML, runs each command in a subprocess with a per-item
timeout, compares the result against `expect_*` fields, and aggregates
into an `AcceptanceReport`.

Schema:

```yaml
session: <session-id>          # optional, advisory
ritual: rrr-input
acceptance:
  - id: A1
    description: "..."
    command: "test -s some/file"
    expect_exit: 0                 # default 0
    expect_stdout_contains: "..."  # optional substring match
    expect_stdout_strip: "..."     # optional exact match after .strip()
    timeout_seconds: 60            # default 60
    required: true                 # default true
```
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class AcceptanceItem:
    id: str
    description: str
    command: str
    expect_exit: Optional[int] = None
    expect_stdout_contains: Optional[str] = None
    expect_stdout_strip: Optional[str] = None
    timeout_seconds: int = 60
    required: bool = True


@dataclass
class AcceptanceResult:
    item: AcceptanceItem
    passed: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    failure_reasons: List[str] = field(default_factory=list)
    timed_out: bool = False


@dataclass
class AcceptanceReport:
    items: List[AcceptanceResult] = field(default_factory=list)
    yaml_path: Optional[Path] = None

    @property
    def ok(self) -> bool:
        return all(r.passed for r in self.items if r.item.required)

    @property
    def required_failures(self) -> List[AcceptanceResult]:
        return [r for r in self.items if r.item.required and not r.passed]


def load_acceptance(yaml_path: Path) -> List[AcceptanceItem]:
    if not yaml_path.exists():
        raise FileNotFoundError(f"acceptance yaml not found: {yaml_path}")
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    items_raw = raw.get("acceptance") or []
    items: List[AcceptanceItem] = []
    for entry in items_raw:
        if "id" not in entry or "command" not in entry:
            raise ValueError(
                f"acceptance entry missing id/command: {entry!r}"
            )
        # R24 — preserve explicit-vs-default for expect_exit so the runner
        # can drop the strict exit check when the caller relied on a stdout
        # check (e.g. `grep -c` exits 1 on no match even though stdout is
        # the correct '0'). Only fall back to strict exit==0 when the
        # caller did NOT specify a stdout check either.
        expect_exit_value: Optional[int]
        if "expect_exit" in entry:
            expect_exit_value = int(entry["expect_exit"])
        else:
            expect_exit_value = None
        items.append(
            AcceptanceItem(
                id=entry["id"],
                description=entry.get("description", ""),
                command=entry["command"],
                expect_exit=expect_exit_value,
                expect_stdout_contains=entry.get("expect_stdout_contains"),
                expect_stdout_strip=entry.get("expect_stdout_strip"),
                timeout_seconds=int(entry.get("timeout_seconds", 60)),
                required=bool(entry.get("required", True)),
            )
        )
    return items


def run_acceptance(
    item: AcceptanceItem, cwd: Path
) -> AcceptanceResult:
    failures: List[str] = []
    timed_out = False
    try:
        proc = subprocess.run(
            item.command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=item.timeout_seconds,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = None
        stdout = (e.stdout or b"").decode("utf-8", errors="replace") if isinstance(e.stdout, (bytes, bytearray)) else (e.stdout or "")
        stderr = (e.stderr or b"").decode("utf-8", errors="replace") if isinstance(e.stderr, (bytes, bytearray)) else (e.stderr or "")
        failures.append(f"timed out after {item.timeout_seconds}s")
    except (OSError, ValueError) as e:
        exit_code = -1
        stdout, stderr = "", str(e)
        failures.append(f"subprocess error: {e}")

    # R24 — compute effective expect_exit: if caller specified it, honor
    # it; if implicit, only enforce strict 0 when there is no stdout check
    # to back-stop correctness. This avoids false negatives from idioms
    # like `grep -c` / `wc -l` that exit non-zero on empty matches even
    # though stdout is correct.
    has_stdout_check = (
        item.expect_stdout_contains is not None
        or item.expect_stdout_strip is not None
    )
    if item.expect_exit is not None:
        effective_expect_exit: Optional[int] = item.expect_exit
    elif has_stdout_check:
        effective_expect_exit = None
    else:
        effective_expect_exit = 0

    if (
        not timed_out
        and effective_expect_exit is not None
        and exit_code != effective_expect_exit
    ):
        failures.append(
            f"exit_code {exit_code} != expected {effective_expect_exit}"
        )
    if item.expect_stdout_contains is not None:
        if item.expect_stdout_contains not in stdout:
            failures.append(
                f"stdout missing expected substring "
                f"{item.expect_stdout_contains!r}"
            )
    if item.expect_stdout_strip is not None:
        if stdout.strip() != item.expect_stdout_strip:
            failures.append(
                f"stdout.strip() {stdout.strip()!r} != "
                f"expected {item.expect_stdout_strip!r}"
            )

    return AcceptanceResult(
        item=item,
        passed=not failures,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        failure_reasons=failures,
        timed_out=timed_out,
    )


def run_all(
    items: List[AcceptanceItem], cwd: Path
) -> AcceptanceReport:
    report = AcceptanceReport()
    for item in items:
        report.items.append(run_acceptance(item, cwd))
    return report
