from __future__ import annotations
import json
import os
import datetime
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union

def iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def atomic_write_json(path: Path, obj: Dict[str, Any]) -> str:
    """Atomically write JSON and return its SHA256 hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(obj, indent=2, ensure_ascii=False)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return digest

@dataclass
class RunHeader:
    run_id: str
    assignment_id: str
    goal: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=iso_now)
    status: str = "READY"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SetupCheckpoint:
    sub_phase: str
    checkpoint_index: int
    last_ok_phase: Optional[str] = None
    failed_phase: Optional[str] = None
    sandbox_id: Optional[str] = None
    updated_at: str = field(default_factory=iso_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AttemptLog:
    attempt_id: int
    started_at: str = field(default_factory=iso_now)
    completed_at: Optional[str] = None
    status: str = "BUSY"
    sub_phase: str = "EXECUTION"
    output_summary: Optional[str] = None
    diff_ref: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Verdict:
    candidate_verdict: str  # PASS, FAIL_RETRY, FAIL_HARD
    reason_code: str
    retry_scope: Optional[str] = None # EXECUTION, REBUILD_SETUP, HUMAN_GATE
    retry_hint: Optional[Dict[str, Any]] = None
    evidence_refs: List[str] = field(default_factory=list)
    voted_at: str = field(default_factory=iso_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TerminalFreeze:
    outcome: str  # DONE, DEAD, NEEDS_HUMAN
    code: str     # VERIFIER_PASS, TIMEOUT, etc.
    by: str       # verifier, harness, policy, human
    completion_status: str  # FULL, PARTIAL, NONE
    artifact_integrity_hash: Optional[str] = None
    artifact_hash_scope: List[str] = field(default_factory=list)
    frozen_at: str = field(default_factory=iso_now)
    retro: Optional[Dict[str, Any]] = None
    memory: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ArtifactManager:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_file = run_dir / "run.json"
        self.setup_file = run_dir / "setup.json"
        self.verdict_file = run_dir / "verdict.json"
        self.terminal_file = run_dir / "terminal.json"
        self.events_file = run_dir / "events.ndjson"

    def write_run_header(self, header: RunHeader) -> str:
        return atomic_write_json(self.run_file, header.to_dict())

    def write_setup_checkpoint(self, checkpoint: SetupCheckpoint) -> str:
        return atomic_write_json(self.setup_file, checkpoint.to_dict())

    def write_verdict(self, verdict: Verdict) -> str:
        return atomic_write_json(self.verdict_file, verdict.to_dict())

    def write_terminal_freeze(self, freeze: TerminalFreeze) -> str:
        # Before writing, we should ideally compute the hash of other artifacts
        # For v0.1, we'll just write it and let the caller provide the hash if needed
        return atomic_write_json(self.terminal_file, freeze.to_dict())

    def log_event(self, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        event = {
            "ts": iso_now(),
            "type": event_type,
            "details": details or {}
        }
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with self.events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
