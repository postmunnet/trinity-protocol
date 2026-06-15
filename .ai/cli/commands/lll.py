"""ai lll — Look / List: situational awareness snapshot.

Spec ref: .ai/shims/lll/SHIM.md (canonical contract)
          docs/specs/07_SHIM_SPEC.md §3.2

Read-only. Surfaces what is *currently true* so the next short code
(`vvv`/`nnn`/etc.) starts from a correct baseline.

Surfaces:
  1. Git state            — branch, dirty file count, ahead/behind
  2. Trinity session      — active session id, current graph_state,
                            last transition timestamp
  3. Recent audit events  — last 5 entries from events.ndjson
  4. Open work            — files in active session's THINK/ +
                            SANDBOX/<seat>/ (count only, no contents)
  5. Memory hint          — top 3 hits from memory-cli search using
                            the active session's name as the query

Read-only events still append per Decision D9: a `lll.invoked` event
goes to the audit chain so the snapshot itself is auditable.

`--json` returns the structured envelope; default is a Markdown
panel for terminal humans.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.audit import get_chain_for_project
from ..core.next_action import compute as compute_next, render_one_line
from ..core.runtime_home import read_engine_source_sha
from ..core.project_resolver import resolve_current_project
from ..core.project_signal import collect_project_signal
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.tools_registry import call as call_tool

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    json_out: bool = typer.Option(
        False, "--json", help="Return the structured snapshot as JSON"
    ),
    audit_n: int = typer.Option(
        5, "--audit-n", help="Number of recent audit events to surface"
    ),
):
    """Run lll snapshot: read-only, no state mutation."""
    if ctx.invoked_subcommand is not None:
        return
    code = _run(json_out=json_out, audit_n=audit_n)
    raise typer.Exit(code=code)


def _run(json_out: bool, audit_n: int) -> int:
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    project_root = config.project_root

    snapshot = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "project_root": str(project_root),
        "project_binding": _project_binding(),
        "project_signal": collect_project_signal(project_root),
        "git": _git_state(project_root),
        "session": _session_state(config),
        "audit_recent": _recent_audit(project_root, audit_n),
        "open_work": None,
        "memory_hints": [],
        "stale_sessions": _stale_sessions(config),
        "runtime_drift": None,
        "doc_drift": _doc_drift(project_root),
    }

    sess = snapshot["session"]
    if sess.get("session_path"):
        spath = Path(sess["session_path"])
        snapshot["open_work"] = _open_work(spath)
        snapshot["runtime_drift"] = _runtime_drift(spath)
        # Q24.10 step 5 — session-scope evidence-adoption KPI (no fleet
        # aggregation). kpi_scope is carried so the number is never read as
        # global (lesson Q24.9).
        try:
            from ..core.aaa_analyzer import compute_kpi, _session_events
            kpi = compute_kpi(_session_events(project_root, spath.name))
            snapshot["evidence_kpi"] = {
                **kpi,
                "kpi_scope": {
                    "level": "session",
                    "session_id": spath.name,
                    "project": project_root.name,
                    "source": "audit_events",
                },
            }
        except Exception:
            snapshot["evidence_kpi"] = None
        # Build a richer memory-cli search query: the operator's Q1 Goal
        # answer is far more topical than the slug alone. Falls back to
        # the slug when THINK/01_PROMPT.md is missing or unparseable
        # (early sessions, retroactive stitched sessions).
        slug = sess.get("session_id") or ""
        prompt_q = _extract_prompt_query(spath)
        if prompt_q:
            query = f"{prompt_q} {slug}".strip()
        else:
            query = slug
        snapshot["memory_hints"] = _memory_hints(project_root, query)

    # D9: read-only events still append.
    chain = get_chain_for_project(project_root)
    chain.append(
        "lll.invoked",
        {
            "session_id": sess.get("session_id"),
            "graph_state": sess.get("graph_state"),
            "decided_by": "human",
            "audit_n": audit_n,
            "memory_hint_count": len(snapshot["memory_hints"]),
        },
    )

    if json_out:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return 0

    _render_human(snapshot)
    # Layer 5a — next-action footer (skip when no session)
    sess = snapshot.get("session") or {}
    if sess.get("active"):
        action = compute_next(
            project_root,
            session_path=Path(sess["session_path"]),
            graph_state=sess.get("graph_state"),
        )
    else:
        action = compute_next(project_root, session_path=None)
    console.print(render_one_line(action))
    return 0


# ─────────── git ───────────


def _project_binding() -> Optional[Dict[str, Any]]:
    try:
        resolved = resolve_current_project(allow_fallback=False)
    except Exception:
        return None
    return {
        "project_id": resolved.project_id,
        "project_slug": resolved.project_slug,
        "project_name": resolved.project_name,
        "root_path": str(resolved.root_path),
        "memory_db_path": str(resolved.memory_db_path),
        "source": resolved.source,
        "registered": resolved.registered,
        "binding_path": str(resolved.binding_path) if resolved.binding_path else None,
        "registry_path": str(resolved.registry_path) if resolved.registry_path else None,
    }


def _git_state(project_root: Path) -> Dict[str, Any]:
    def _git(*args: str) -> str:
        try:
            r = subprocess.run(
                ["git", *args],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            return r.stdout.strip()
        except Exception:
            return ""

    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or None
    if not branch:
        return {"available": False}

    dirty = _git("status", "--porcelain")
    dirty_count = len([l for l in dirty.splitlines() if l.strip()])

    # ahead/behind upstream — gracefully None if no upstream
    upstream = _git("rev-parse", "--abbrev-ref", "@{upstream}")
    ahead_behind: Dict[str, Optional[int]] = {"ahead": None, "behind": None}
    if upstream:
        counts = _git("rev-list", "--left-right", "--count", "@{upstream}...HEAD")
        if counts:
            try:
                behind, ahead = (int(x) for x in counts.split())
                ahead_behind = {"ahead": ahead, "behind": behind}
            except ValueError:
                pass

    head_short = _git("rev-parse", "--short", "HEAD") or None

    return {
        "available": True,
        "branch": branch,
        "head": head_short,
        "dirty_count": dirty_count,
        "upstream": upstream or None,
        **ahead_behind,
    }


# ─────────── session ───────────


def _session_state(config) -> Dict[str, Any]:
    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if not cur:
        return {
            "active": False,
            "session_id": None,
            "session_path": None,
            "graph_state": None,
            "last_transition_ts": None,
        }
    spath = Path(cur)
    sid = spath.name

    # last_transition_ts: scan audit chain backwards for the latest
    # graph.transition event for this session.
    last_ts = None
    chain = get_chain_for_project(config.project_root)
    for ev in chain.iter_events_reversed():
        if ev.get("type") != "graph.transition":
            continue
        det = ev.get("details") or {}
        if det.get("session_id") == sid:
            last_ts = ev.get("ts")
            break

    # graph_state from same scan (fall back to status.json if any)
    graph_state: Optional[str] = status.get("graph_state")
    if not graph_state:
        for ev in chain.iter_events_reversed():
            if ev.get("type") != "graph.transition":
                continue
            det = ev.get("details") or {}
            if det.get("session_id") == sid:
                graph_state = det.get("to_state")
                break

    return {
        "active": True,
        "session_id": sid,
        "session_path": str(spath),
        "graph_state": graph_state,
        "last_transition_ts": last_ts,
    }


# ─────────── audit ───────────


def _recent_audit(project_root: Path, n: int) -> List[Dict[str, Any]]:
    chain = get_chain_for_project(project_root)
    out: List[Dict[str, Any]] = []
    for ev in chain.iter_events_reversed():
        out.append({
            "ts": ev.get("ts"),
            "type": ev.get("type"),
            "session_id": (ev.get("details") or {}).get("session_id"),
            "decided_by": (ev.get("details") or {}).get("decided_by"),
        })
        if len(out) >= n:
            break
    return out


# ─────────── open work ───────────


def _open_work(session_path: Path) -> Dict[str, Any]:
    def _count(p: Path) -> int:
        if not p.exists() or not p.is_dir():
            return 0
        return sum(1 for x in p.rglob("*") if x.is_file())

    return {
        "think_files": _count(session_path / "THINK"),
        "sandbox_files": _count(session_path / "SANDBOX"),
        "do_dev_files": _count(session_path / "DO" / "dev"),
    }


# ─────────── stale sessions ───────────


def _doc_drift(project_root: Path) -> Optional[Dict[str, Any]]:
    """Read-only standing fact-drift summary (advisory). Returns None when clean
    or on any failure — kept cheap + fail-soft so it never slows or breaks lll.
    Surfaces the doc-drift guard proactively so any agent sees it at session
    start, not only when blocked at rrr. See docs/DOC_DRIFT_GUARD.md."""
    try:
        from ..core.fact_drift import compare
        rep = compare(project_root)
        drifted = [r.fact_id for r in rep.results if r.drifted]
        return {"drift_count": len(drifted), "drifted": drifted} if drifted else None
    except Exception:
        return None


def _runtime_drift(session_path: Path) -> Optional[Dict[str, Any]]:
    """Read-only: compare the pinned engine hash (stamped at sss in CONTROL/
    META.json) against the live engine source_sha. Returns None when not
    applicable (no pin, source-mode, unreadable) — fail-soft, never raises.
    """
    try:
        pinned = json.loads(
            (session_path / "CONTROL" / "META.json").read_text(encoding="utf-8")
        ).get("runtime_pinned_hash")
        live = read_engine_source_sha(session_path)
        if not pinned or not live:
            return None
        return {"pinned": pinned, "live": live, "drifted": pinned != live}
    except (OSError, ValueError, TypeError):
        return None


def _stale_sessions(config) -> List[str]:
    """Sessions sitting in `sessions/` root that are neither current
    nor reserved subdirs. Surfaces ghost folders left by retroactive
    rrr / aborted sessions so the operator can recover them.
    """
    paths_cfg = (config.raw_config or {}).get("paths", {})
    sessions_template = paths_cfg.get("sessions", "${ai_root}/sessions")
    sessions_resolved = (
        sessions_template
        .replace("${ai_root}", str(config.ai_root))
        .replace("${project_root}", str(config.project_root))
    )
    sessions_root = Path(sessions_resolved)
    if not sessions_root.exists():
        return []

    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    cur_name = Path(cur).name if cur else None

    reserved = {"active", "archive"}
    out: List[str] = []
    for entry in sorted(sessions_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name in reserved:
            continue
        if entry.name == cur_name:
            continue
        out.append(entry.name)
    return out


# ─────────── memory ───────────


def _memory_hints(project_root: Path, query: str) -> List[Dict[str, Any]]:
    if not query:
        return []
    for variant in _memory_query_variants(query):
        results = _memory_hints_once(project_root, variant)
        if results:
            return results
    return []


def _memory_hints_once(project_root: Path, query: str) -> List[Dict[str, Any]]:
    inv = call_tool(
        project_root,
        "memory-cli",
        f"search {json.dumps(query)} --limit=3",
        timeout_seconds=10,
    )
    if not inv.ok or not inv.envelope:
        return []
    data = inv.envelope.get("data") or {}
    return data.get("results") or []


_MEMORY_STOPWORDS = {
    "the", "and", "for", "from", "with", "into", "that", "this",
    "task", "session", "fix", "feat", "ops", "pm", "am",
}


def _memory_query_variants(query: str) -> List[str]:
    """Return bounded fallback queries for memory-cli search.

    memory-cli FTS can behave like a strict multi-term search. Long
    session prompts such as "fix workflow bugs from lll-to-close audit"
    may return no rows even though shorter topical probes would. Keep the
    original query first for precision, then progressively shorten.
    """
    original = " ".join(query.split())
    variants: List[str] = []
    if original:
        variants.append(original)

    tokens: List[str] = []
    for raw in re.split(r"[^0-9A-Za-zก-๙]+", original.lower()):
        tok = raw.strip()
        if len(tok) < 3 or tok.isdigit() or tok in _MEMORY_STOPWORDS:
            continue
        if tok not in tokens:
            tokens.append(tok)

    if tokens:
        variants.append(" ".join(tokens[:6]))
    if len(tokens) >= 3:
        variants.append(" ".join(tokens[:3]))
    variants.extend(tokens[:3])

    out: List[str] = []
    seen = set()
    for v in variants:
        if v and v not in seen:
            out.append(v)
            seen.add(v)
    return out[:6]


_PROMPT_QUERY_MAX = 200


def _extract_prompt_query(session_path: Path) -> Optional[str]:
    """Extract the Q1 (Goal) answer from THINK/01_PROMPT.md to enrich
    memory-cli search beyond the bare session-id slug.

    Tolerant parser:
      1. Locate the '## Q1 — Goal' (or '## Q1') section header.
      2. Prefer text after a '**Answer:**' marker inside that section.
      3. Fallback: first non-empty paragraph of the section.
      4. Trim to <=200 chars (shell argv ceiling).
      5. Return None on any failure — caller falls back to slug.
    """
    prompt = session_path / "THINK" / "01_PROMPT.md"
    if not prompt.exists():
        return None
    try:
        text = prompt.read_text(encoding="utf-8")
    except OSError:
        return None

    # Find the Q1 section. Accept either "## Q1 — Goal" or just "## Q1".
    m = re.search(r"^##\s+Q1(?:\s+[—-]\s+Goal)?\s*$", text, re.MULTILINE)
    if not m:
        return None
    q1_start = m.end()
    # Section ends at the next "## " heading or EOF.
    next_h = re.search(r"^##\s+", text[q1_start:], re.MULTILINE)
    q1_block = text[q1_start : q1_start + (next_h.start() if next_h else len(text))]

    # Prefer text after '**Answer:**' marker.
    am = re.search(r"\*\*Answer:\*\*\s*", q1_block)
    body = q1_block[am.end():] if am else q1_block

    # Take the first non-empty paragraph (until blank line).
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not paragraphs:
        return None
    first = paragraphs[0]
    # Collapse internal whitespace + clip.
    flat = " ".join(first.split())
    if not flat:
        return None
    return flat[:_PROMPT_QUERY_MAX]


# ─────────── human render ───────────


def _render_human(snap: Dict[str, Any]) -> None:
    git = snap["git"]
    sess = snap["session"]

    # Header — git
    if git.get("available"):
        head_line = f"branch [bold]{git['branch']}[/bold] @ {git['head']}"
        if git.get("upstream"):
            head_line += (
                f" · upstream {git['upstream']} "
                f"(ahead {git['ahead']}, behind {git['behind']})"
            )
        head_line += f" · dirty: {git['dirty_count']} file(s)"
    else:
        head_line = "[dim]not a git repo[/dim]"

    # Session
    if sess.get("active"):
        sess_line = (
            f"[bold]{sess['session_id']}[/bold] · "
            f"graph_state={sess.get('graph_state') or '?'}"
        )
        if sess.get("last_transition_ts"):
            sess_line += f" · last transition {sess['last_transition_ts']}"
    else:
        sess_line = "[dim]no active session — `ai session new <task>`[/dim]"

    project = snap.get("project_binding")
    project_line = None
    if project:
        project_line = (
            f"[bold]{project['project_slug']}[/bold] · "
            f"source={project['source']} · memory={project['memory_db_path']}"
        )

    # Open work
    open_line = "—"
    if snap.get("open_work"):
        ow = snap["open_work"]
        open_line = (
            f"THINK={ow['think_files']} · "
            f"SANDBOX={ow['sandbox_files']} · "
            f"DO/dev={ow['do_dev_files']}"
        )

    # Audit recent
    audit_table = Table(show_header=True, header_style="cyan")
    audit_table.add_column("ts", overflow="fold")
    audit_table.add_column("type")
    audit_table.add_column("decided_by")
    audit_table.add_column("session", overflow="fold")
    for ev in snap["audit_recent"]:
        audit_table.add_row(
            str(ev.get("ts") or "?"),
            str(ev.get("type") or "?"),
            str(ev.get("decided_by") or ""),
            str(ev.get("session_id") or ""),
        )

    body = (
        f"[cyan]git[/cyan]      {head_line}\n"
        + (f"[cyan]project[/cyan]  {project_line}\n" if project_line else "")
        + f"[cyan]session[/cyan]  {sess_line}\n"
        + f"[cyan]open[/cyan]     {open_line}"
    )
    console.print(Panel(body, title="🔍 lll — snapshot", border_style="cyan"))

    if snap["audit_recent"]:
        console.print(audit_table)

    _render_project_signal(snap.get("project_signal") or {})

    if snap.get("stale_sessions"):
        body = []
        for name in snap["stale_sessions"]:
            body.append(
                f"  • [bold]{name}[/bold]\n"
                f"      recover: ai rrr --retroactive --session {name}"
            )
        console.print(
            Panel(
                f"[yellow]{len(snap['stale_sessions'])} stale session(s) "
                f"in sessions/ root — neither current nor archived:[/yellow]\n"
                + "\n".join(body),
                title="⚠️  stale sessions",
                border_style="yellow",
            )
        )

    drift = snap.get("runtime_drift")
    if drift and drift.get("drifted"):
        console.print(
            Panel(
                f"[yellow]engine drifted mid-session[/yellow] (may be benign)\n"
                f"  pinned @ sss: [dim]{drift['pinned']}[/dim]\n"
                f"  live now:     [dim]{drift['live']}[/dim]",
                title="⚠️  runtime drift",
                border_style="yellow",
            )
        )

    dd = snap.get("doc_drift")
    if dd and dd.get("drift_count"):
        console.print(
            Panel(
                f"[yellow]{dd['drift_count']} fact(s) drift vs docs[/yellow]: "
                f"{', '.join(dd['drifted'])}\n"
                f"  run [bold]ai doc-drift --facts[/bold] · docs/DOC_DRIFT_GUARD.md",
                title="⚠️  doc drift",
                border_style="yellow",
            )
        )

    if snap["memory_hints"]:
        body = []
        for h in snap["memory_hints"]:
            title = h.get("title") or h.get("id")
            when = h.get("created_at") or "?"
            body.append(
                f"[bold]{title}[/bold]  [dim]{when}[/dim]\n"
                f"  id: {h.get('id')}"
            )
        console.print(
            Panel(
                "\n\n".join(body),
                title=f"💡 {len(snap['memory_hints'])} memory hint(s)",
                border_style="green",
            )
        )

    # Q24.10 step 5 — evidence-adoption KPI footer (session scope, labelled).
    kpi = snap.get("evidence_kpi")
    if kpi:
        sc = kpi["kpi_scope"]
        console.print(
            f"[cyan]evidence[/cyan]  adoption={kpi['evidence_command_adoption_rate']} · "
            f"structural={kpi['structural_pass_rate']} · "
            f"high-risk-no-evidence={kpi['high_risk_without_evidence_count']} "
            f"[dim](scope: {sc['level']} {sc['session_id']} · n={kpi['steps_measured']})[/dim]"
        )


def _render_project_signal(signal: Dict[str, Any]) -> None:
    if not signal.get("available"):
        return

    def _lines(key: str, title: str, limit: int = 3) -> List[str]:
        rows = signal.get(key) or []
        out = []
        for row in rows[:limit]:
            src = row.get("source") or "?"
            line = row.get("line") or "?"
            out.append(f"[bold]{title}[/bold] {row.get('text')} [dim]({src}:{line})[/dim]")
        return out

    body: List[str] = []
    body.extend(_lines("deploy_risk", "Deploy"))
    body.extend(_lines("carryover", "Carryover"))
    body.extend(_lines("pending", "Pending"))
    body.extend(_lines("regression_watch", "Watch"))
    body.extend(_lines("next_actions", "Next"))
    if not body:
        return
    console.print(
        Panel(
            "\n".join(body),
            title="📌 Project Signal",
            border_style="magenta",
        )
    )
