import typer
import json
import datetime
import hashlib
import re
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from ..core.next_action import compute as compute_next, render_one_line
from ..core.state import StateManager, SessionLocalState
from ..core.ssot import SSOTLoader
from ..core.audit import get_chain_for_project
from ..core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    load_pack,
)
from ..core.presentation_renderer import write_close_pack
from ..core.session_archive import archive_session
from ..core import manifest as manifest_module

app = typer.Typer(invoke_without_command=True)
console = Console()

@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Force-close even if gates fail"),
    with_synthesis: bool = typer.Option(
        False,
        "--with-synthesis",
        help="After CLOSE_PACK.md is written, invoke the presentation_synthesizer agent.",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport. Verifies HMAC before archive.",
    ),
):
    """Close and archive session.

    Bare `ai close` is the canonical ritual command. `ai close run`
    remains a backward-compatible subcommand.
    """
    if ctx.invoked_subcommand is not None:
        return
    _run_impl(
        force=force,
        with_synthesis=with_synthesis,
        hmac_envelope_file=hmac_envelope_file,
    )

@app.command()
def run(
    force: bool = False,
    with_synthesis: bool = typer.Option(
        False,
        "--with-synthesis",
        help="After CLOSE_PACK.md is written, invoke the "
        "presentation_synthesizer agent to draft a 3-layer synthesis "
        "(convergence / dissent / founder decisions). Output is saved "
        "to PRESENTATION_SYNTH.md inside the session dir (travels into "
        "the archive). Fail-soft: close completes normally if agent "
        "fails. Skipped under --force.",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport. When present, kernel "
        "verifies HMAC before archiving the session; on failure emits "
        "close.hmac_rejected and exits 79.",
    ),
):
    """
    Close current session and archive.

    Phase 6 Requirement: Prod verify must PASS before close.
    Exit codes:
      0 = Success
      1 = Gate failed (verification not passed)
      2 = Error
    """
    _run_impl(
        force=force,
        with_synthesis=with_synthesis,
        hmac_envelope_file=hmac_envelope_file,
    )


def _run_impl(
    *,
    force: bool = False,
    with_synthesis: bool = False,
    hmac_envelope_file: Optional[Path] = None,
) -> None:
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(2)

    # Get current session
    current_session_path = status.get("current_session")
    if not current_session_path:
        console.print("[red]No active session to close. Run `ai session new <task>` to start one.[/red]")
        raise typer.Exit(1)

    session_path = Path(current_session_path)
    if not session_path.exists():
        console.print(f"[red]Session path not found: {session_path}[/red]")
        raise typer.Exit(1)

    if hmac_envelope_file is not None:
        from ..core.hmac_gate import enforce_hmac_or_exit
        chain_for_hmac = get_chain_for_project(config.project_root)
        enforce_hmac_or_exit(
            hmac_envelope_file=hmac_envelope_file,
            chain=chain_for_hmac,
            ritual="close",
            session_id=session_path.name,
        )

    # RC v1.1-rc Article XII.5 — load the close pack so the empirical
    # ratification trail anchors the audit-event vocabulary. The pack
    # declares CONCEPTUAL states (DONE/FAILED/ABORTED → SEALED); the
    # physical graph uses DONE only. Pre-existing pack/graph naming
    # divergence — out of scope for this session (`.ai/rituals/**` is in
    # forbidden_paths). Like gogogo/ddd/rrr, we load the pack to anchor
    # event vocabulary but do not call assert_transition_allowed with the
    # physical pair.
    close_pack = load_pack(
        "close",
        rituals_root=config.project_root / ".ai" / "rituals",
    )

    # Emit pack-declared close.invoked as the first ritual-side audit
    # event — before any state mutation (Article XX).
    get_chain_for_project(config.project_root).append(
        "close.invoked",
        {
            "session_id": session_path.name,
            "decided_by": "kernel",
            "force": force,
        },
    )

    # Gate 1: the standard graph must be terminal before archive. Prod
    # verification alone is not enough; close is the ritual after rrr.
    if not force:
        sls = SessionLocalState(session_path)
        graph_state = sls.graph_state(default=sls.current_state())
        if graph_state not in {"DONE", "DEAD"}:
            action = render_one_line(
                compute_next(
                    config.project_root,
                    session_path=session_path,
                    graph_state=graph_state,
                )
            )
            console.print("[bold red]🚨 GATE LOCK:[/bold red] Session graph is not terminal")
            console.print(f"   graph_state={graph_state!r}; close requires DONE or DEAD")
            console.print(f"   {action}")
            raise typer.Exit(1)

    # Gate 2: Prod verify must PASS (prefer session-local, fallback to legacy)
    if not force:
        sls = SessionLocalState(session_path)
        if not sls.prod_verified():
            # fallback legacy
            legacy = session_path / ".ai" / "state" / "verify_report.json"
            ok = False
            if legacy.exists():
                try:
                    with legacy.open("r", encoding="utf-8") as f:
                        r = json.load(f)
                    ok = r.get("scope") == "prod" and r.get("passed") is True
                except Exception:
                    ok = False
            if not ok:
                console.print("[bold red]🚨 GATE LOCK:[/bold red] Prod verification not passed")
                console.print("   Run [yellow]ai verify prod[/yellow] first or use --force")
                raise typer.Exit(1)

    # Part 2 (capture wiring): open a capture for close's pre-archive
    # work. MUST exit the with-block BEFORE archive_session — archive
    # moves session_dir to .ai/sessions/archive/ and the capture's
    # __exit__ would otherwise try to write to a path that no longer
    # exists. Trade-off: session.closed + close.completed events emitted
    # after capture exits, so they lack capture_id; that is acceptable
    # since the close-capture row itself records all pre-archive
    # evidence.
    from ..core.recordproxy import capture as _rp_capture
    with _rp_capture(
        session_path,
        ritual="close",
        role="KERNEL",
        kind="ritual_invocation",
    ) as cap:
        cap.input("close_params.json", {"force": force, "with_synthesis": with_synthesis})
        _close_pre_archive(session_path, config, cap)
        if with_synthesis and not force:
            _invoke_presentation_synthesizer(session_path, config.project_root)
    archive_path, last_event_hash = _close_archive_and_emit(
        session_path, config, status, state_mgr, force
    )
    archive_dir = archive_path.parent
    archive_name = archive_path.name
    console.print(f"   [green]✓[/green] Archived to: {archive_path}")

    # KI-2026-05-16-002 fix — route post-close terminal footer through
    # the shared next_action formatter. After archive, current_session
    # is cleared → compute(session_path=None) returns the canonical
    # "ai session new <task-slug>" recommendation; render_one_line
    # gives operator + parallel agents the same text that `ai next`
    # would print for the same state.
    post_close_action = compute_next(config.project_root, session_path=None)
    next_line = render_one_line(post_close_action)
    summary = (
        f"[green]✅ Session Closed Successfully[/green]\n\n"
        f"Session: {session_path.name}\n"
        f"Archived: {archive_path}\n\n"
        f"[bold]Summary:[/bold]\n"
        f"• Prod verification: PASSED\n"
        f"• State: DONE\n"
        f"• Archive location: {archive_dir}\n\n"
        f"{next_line}"
    )
    console.print(Panel(summary, title="🏁 Session Closed", border_style="green"))
    return


def _invoke_presentation_synthesizer(session_path: Path, project_root: Path) -> Optional[Path]:
    """Subprocess-invoke presentation_synthesizer agent.

    Saves stdout to <session>/PRESENTATION_SYNTH.md alongside CLOSE_PACK.md.
    Returns the written path on success, None on any failure (fail-soft).
    """
    import subprocess as _sub
    try:
        proc = _sub.run(
            [
                "bash",
                str(project_root / ".ai" / "cli" / "agent"),
                "presentation_synthesizer",
                "draft",
                "--session-path",
                str(session_path),
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            console.print(
                f"[yellow]⚠ presentation_synthesizer failed "
                f"(exit={proc.returncode}); skipping synthesis[/yellow]"
            )
            return None
        target = session_path / "PRESENTATION_SYNTH.md"
        target.write_text(proc.stdout, encoding="utf-8")
        console.print(f"   [dim]presentation synthesis: {target.name}[/dim]")
        return target
    except Exception as exc:
        console.print(
            f"[yellow]⚠ presentation_synthesizer invocation failed: {exc}[/yellow]"
        )
        return None


def _close_pre_archive(session_path: Path, config, cap) -> None:
    # Update metadata
    meta_file = session_path / "CONTROL" / "META.json"
    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta = json.load(f)
        meta["status"] = "closed"
        meta["closed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta["workflow"]["closed"] = True
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)

    # Update session-local state to DONE
    try:
        sls = SessionLocalState(session_path)
        # move to DONE if VERIFIED or already DONE
        cur = sls.current_state()
        if cur != "DONE":
            # allow VERIFIED -> DONE; if other states, still attempt per force flag
            try:
                sls.set_state("DONE")
            except Exception:
                pass
    except Exception:
        pass

    # Phase 13 wiring — render CLOSE_PACK.md so it travels with the
    # archive. Fail-soft: close MUST NOT abort if the renderer trips
    # (would block a legitimate archive on a cosmetic concern).
    try:
        close_pack_path = write_close_pack(session_path)
        console.print(f"   [dim]close pack: {close_pack_path.name}[/dim]")
        cap.output("close_pack.md.path", str(close_pack_path))
    except Exception as exc:
        console.print(f"[yellow]⚠ close pack render failed: {exc}[/yellow]")

    # TRINITY_SESSION_CLOSE_SPEC_V1 §2-§5 — build final manifest, emit
    # close.manifest_built, and (COLD only) external audit. Done BEFORE
    # archive_session so the manifest lands inside the session dir and
    # follows it into the archive.
    try:
        tier = manifest_module.resolve_tier(session_path)
    except Exception as e:
        console.print(f"[yellow]⚠ tier resolution failed: {e}; defaulting to WARM[/yellow]")
        tier = "WARM"

    final_manifest: dict = {}
    manifest_path = session_path / "CONTROL" / "final_manifest.yaml"
    try:
        final_manifest = manifest_module.build_final_manifest(
            session_path, tier, graph_state_final="DONE"
        )
        # Write as YAML if available, JSON otherwise. The on-disk file
        # location is .yaml per Close Spec §2.
        try:
            import yaml  # type: ignore
            manifest_path.write_text(
                yaml.safe_dump(final_manifest, sort_keys=True, default_flow_style=False),
                encoding="utf-8",
            )
        except Exception:
            # PyYAML missing — emit JSON with a .yaml extension as a graceful
            # fallback. The manifest body is YAML-compatible JSON.
            manifest_path.write_text(
                json.dumps(final_manifest, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        get_chain_for_project(config.project_root).append(
            "close.manifest_built",
            {
                "session_id": session_path.name,
                "path": str(manifest_path.relative_to(config.project_root)),
                "sha256": final_manifest["manifest_sha256"],
                "capture_count": len(
                    final_manifest.get("captures", {}).get("capture_ids", [])
                ),
                "last_seq": final_manifest.get("audit", {}).get("last_seq"),
                "tier": tier,
            },
        )
    except Exception as e:
        # Manifest is additive; if it fails, log + proceed (existing close
        # behavior preserved). COLD external audit failure escalates below.
        console.print(f"[yellow]⚠ manifest build failed: {e}[/yellow]")
        final_manifest = {}

    # COLD-tier: emit external audit per Close Spec §3.
    # Failure here raises NEEDS_HUMAN (Article XIII) — close MUST NOT silently
    # complete a COLD session without external audit.
    if tier == "COLD" and final_manifest:
        try:
            audit_root = config.project_root / "audit" / "external"
            legacy_ndjson = config.project_root / ".ai" / "audit" / "events.ndjson"
            external_path = manifest_module.write_external_audit(
                session_path,
                final_manifest,
                audit_root=audit_root,
                legacy_ndjson=legacy_ndjson if legacy_ndjson.is_file() else None,
            )
            get_chain_for_project(config.project_root).append(
                "close.external_audit_emitted",
                {
                    "session_id": session_path.name,
                    "path": str(external_path.relative_to(config.project_root)),
                    "sha256": manifest_module._sha256_file(external_path),
                    "tier": "COLD",
                },
            )
        except Exception as e:
            console.print(
                f"[bold red]🚨 COLD external audit emission failed:[/bold red] {e}"
            )
            console.print("   Per TRINITY_SESSION_CLOSE_SPEC_V1 §5, escalating NEEDS_HUMAN (exit 3)")
            get_chain_for_project(config.project_root).append(
                "close.external_audit_emitted",
                {
                    "session_id": session_path.name,
                    "status": "FAILED",
                    "error": str(e)[:500],
                    "tier": "COLD",
                },
            )
            raise typer.Exit(3)

    # Part 2 (capture wiring): record the manifest + tier as capture
    # output before the with-block exits in run(). Archive + post-archive
    # audit events happen OUTSIDE the capture (see _close_archive_and_emit
    # in run()) because archive_session moves the session_dir.
    if final_manifest:
        cap.output("final_manifest.yaml", final_manifest)
    cap.validation("close_tier.txt", tier)

    # Vendor-harness conversation transcripts — must run INSIDE the cap
    # block (so capture_items are recorded before __exit__) and BEFORE
    # archive (per memory feedback_close_capture_before_archive). The
    # umbrella tolerates per-handler failure so close never breaks on
    # additive observability.
    _snapshot_conversation_transcripts(session_path, config, cap)


def _slugify_project_root(project_root: Path) -> str:
    """Mirror Claude Code's slug scheme: collapse non-alphanumeric runs to '-'.

    The dir name ``-home-user-projects-example-trinity-v2`` for project
    root ``/home/user/projects/example/trinity_v2`` is the empirical
    encoding (both ``/`` and ``_`` collapse to ``-``).
    """
    return re.sub(r"[^A-Za-z0-9]+", "-", str(project_root))


def _jsonl_cwd_matches_project(jsonl_path: Path, project_root: Path) -> bool:
    """Open the JSONL and confirm at least one record has ``cwd`` rooted in
    ``project_root``.

    Slug encoding is lossy (``_`` and ``/`` both collapse to ``-``), so two
    distinct projects whose paths only differ in those characters share the
    same slug prefix and would otherwise be indistinguishable on disk.
    Claude Code records the actual cwd inside each JSONL record as ground
    truth; we verify it before accepting a candidate.

    Reads up to ~32 lines so cost stays bounded for large transcripts.
    Returns False on any I/O / parse failure (safe-fallback rejects the
    candidate).
    """
    try:
        project_str = str(project_root.resolve())
    except Exception:
        return False
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 32:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                cwd = rec.get("cwd")
                if isinstance(cwd, str) and cwd:
                    return cwd == project_str or cwd.startswith(project_str + "/")
    except OSError:
        return False
    return False


def _snapshot_claude_transcript(session_path: Path, config, cap) -> None:
    """Snapshot the Claude Code conversation transcript into CAPTURE.

    Claude Code persists each conversation as a JSONL file under
    ``~/.claude/projects/<slug>/<uuid>.jsonl`` where ``<slug>`` is the
    project's absolute path with non-alphanumeric runs collapsed to ``-``.

    Discovery is 2-tier to defend against slug collisions (the slug encoder
    is lossy — ``foo_bar`` and ``foo/bar`` produce the same suffix, so a
    sibling project ``trinity_v2_backup`` would share ``-trinity-v2``'s
    prefix and snapshot the wrong transcript):

    1. **Slug match with separator awareness** — accept ``<slug>``
       (canonical cwd) and ``<slug>-...`` (subdir cwd, where ``-`` is the
       slug separator) but reject ``<slug><not-dash>...`` (sibling project
       sharing a prefix).
    2. **Cwd verify** — open each candidate JSONL and require at least one
       record whose ``cwd`` field starts with ``project_root``. This is the
       ground truth Claude Code records per-message; lossy slug encoding
       cannot fake it.

    The transcript is recorded as a ``runtime`` capture_item — it documents
    HOW the session unfolded (operator prompts + AI replies + tool calls)
    rather than ritual input/output. CAS dedupes by SHA-256, so a long
    conversation that spans multiple Trinity sessions stores one blob
    referenced by many ``runtime`` capture_items.

    Silent no-op when Claude Code is not the active harness (no slug dir,
    no JSONL, or none of the JSONLs verify against this project_root).
    """
    slug = _slugify_project_root(config.project_root)
    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.is_dir():
        return  # Claude Code never used on this machine
    # Separator-aware slug match: canonical OR <slug>-<suffix> where the
    # leading '-' is the encoder's separator (subdir cwds). Rejects
    # sibling-project dirs whose slug shares a prefix without the
    # separator (e.g. `_backup` -> `-backup` joined to `-trinity-v2`).
    slug_sep = slug + "-"
    candidate_dirs = [
        d for d in claude_projects.iterdir()
        if d.is_dir() and (d.name == slug or d.name.startswith(slug_sep))
    ]
    if not candidate_dirs:
        return
    # cwd-verify each JSONL: lossy slug encoding can collide subdir vs
    # sibling-project, so consult the in-file cwd ground truth.
    verified_jsonls = []
    for d in candidate_dirs:
        for jsonl in d.glob("*.jsonl"):
            if _jsonl_cwd_matches_project(jsonl, config.project_root):
                verified_jsonls.append(jsonl)
    if not verified_jsonls:
        return
    latest = max(verified_jsonls, key=lambda p: p.stat().st_mtime)
    # CAS by SHA — write_blob dedupes; size_bytes recorded in capture_items.
    cap.runtime("claude_code_transcript.jsonl", latest.read_bytes())


def _codex_jsonl_cwd_matches_project(jsonl_path: Path, project_root: Path) -> bool:
    """Codex stores cwd inside the first record (type='session_meta') as
    ``payload.cwd``. Verify it against project_root.

    Reads up to the first 4 non-empty records — session_meta is canonically
    the file's leading record but we tolerate a small amount of header noise.
    """
    try:
        project_str = str(project_root.resolve())
    except Exception:
        return False
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            checked = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                checked += 1
                if checked > 4:
                    break
                try:
                    rec = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if rec.get("type") != "session_meta":
                    continue
                cwd = (rec.get("payload") or {}).get("cwd")
                if isinstance(cwd, str) and cwd:
                    return cwd == project_str or cwd.startswith(project_str + "/")
                return False
    except OSError:
        return False
    return False


def _snapshot_codex_transcript(session_path: Path, config, cap) -> None:
    """Snapshot the latest Codex CLI rollout JSONL for this project.

    Codex stores conversations as
    ``~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-<timestamp>-<uuid>.jsonl``.
    Each file's first record is ``type='session_meta'`` whose payload
    carries the launch ``cwd``; we use that as ground truth for project
    ownership (no slug-style collision risk).

    Performance: instead of opening every rollout (potentially thousands
    over time), we sort all rollout JSONLs by mtime descending and check
    in order, stopping at the first whose ``session_meta.cwd`` matches
    this project_root. That's typically the in-flight Codex session.

    Silent no-op when Codex CLI is not installed / no matching rollout.
    """
    codex_sessions = Path.home() / ".codex" / "sessions"
    if not codex_sessions.is_dir():
        return
    rollouts = list(codex_sessions.rglob("rollout-*.jsonl"))
    if not rollouts:
        return
    # Newest first; stop at first project-matching rollout.
    rollouts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for rollout in rollouts:
        if _codex_jsonl_cwd_matches_project(rollout, config.project_root):
            cap.runtime("codex_cli_transcript.jsonl", rollout.read_bytes())
            return


def _snapshot_gemini_transcript(session_path: Path, config, cap) -> None:
    """Snapshot the latest Gemini CLI chat JSON for this project.

    Gemini stores conversations as
    ``~/.gemini/tmp/<projectHash>/chats/session-<timestamp>-<uuid>.json``
    where ``projectHash = sha256(absolute_project_path)``. The hash is
    deterministic and exact — no slug collision risk, no cwd-verify
    needed (the hash IS the verification).

    Silent no-op when Gemini CLI hasn't been used on this project (the
    ``<projectHash>`` dir simply won't exist).
    """
    try:
        project_str = str(config.project_root.resolve())
    except Exception:
        return
    project_hash = hashlib.sha256(project_str.encode()).hexdigest()
    chats_dir = Path.home() / ".gemini" / "tmp" / project_hash / "chats"
    if not chats_dir.is_dir():
        return
    chats = list(chats_dir.glob("session-*.json"))
    if not chats:
        return
    latest = max(chats, key=lambda p: p.stat().st_mtime)
    cap.runtime("gemini_cli_transcript.json", latest.read_bytes())


def _snapshot_conversation_transcripts(session_path: Path, config, cap) -> None:
    """Umbrella: run all vendor-harness transcript snapshots, tolerating
    per-handler failure.

    Each handler is silent-no-op when its harness wasn't used on this
    project. If a handler raises (e.g. permission denied on a transcript
    file, or malformed JSONL), the failure is logged and the umbrella
    moves on — transcript capture is additive observability and MUST NOT
    block close.

    The order is fixed (Claude → Codex → Gemini) so audit trails are
    reproducible across sessions; CAS dedupes by SHA so re-snapshotting
    an unchanged transcript is free.
    """
    handlers = (
        ("claude", _snapshot_claude_transcript),
        ("codex", _snapshot_codex_transcript),
        ("gemini", _snapshot_gemini_transcript),
    )
    for name, handler in handlers:
        try:
            handler(session_path, config, cap)
        except Exception as e:
            console.print(
                f"[yellow]⚠ {name} transcript snapshot skipped: {e}[/yellow]"
            )


def _close_archive_and_emit(session_path: Path, config, status, state_mgr, force: bool):
    """Archive the session and emit session.closed + close.completed.
    Runs OUTSIDE the close capture because archive_session moves the
    session_dir (and with it the capture.sqlite); the capture must be
    finalized before this function is called."""
    console.print(f"[yellow]📦 Archiving session...[/yellow]")
    archive_path = archive_session(session_path, config)
    archive_name = archive_path.name

    try:
        chain = get_chain_for_project(config.project_root)
        global_event = chain.append("session.closed", {
            "session_id": session_path.name,
            "archive_path": str(archive_path.relative_to(config.project_root)),
            "force": force,
        })
        chain.append("close.completed", {
            "session_id": session_path.name,
            "decided_by": "kernel",
            "archive_path": str(archive_path.relative_to(config.project_root)),
        })
        last_event_hash = global_event["hash"]
    except Exception as e:
        console.print(f"[yellow]⚠ audit chain append failed: {e}[/yellow]")
        last_event_hash = None

    status["system"]["status"] = "idle"
    status["current_session"] = None
    status["system"]["active_capsules"] = max(0, status["system"].get("active_capsules", 1) - 1)
    status["last_closed"] = {
        "session": archive_name,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if last_event_hash:
        status["last_event_hash"] = last_event_hash
    state_mgr.save_status(status)

    return archive_path, last_event_hash
