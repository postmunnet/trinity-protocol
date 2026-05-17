from __future__ import annotations
import json
import os
import time
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # avoid runtime import issues in path-loaded tests
    from .ssot import SSOTConfig

class StateManager:
    def __init__(self, config: 'SSOTConfig'):
        self.config = config
        self.status_file = self.config.state_path / "status.json"
        
    def _iso_now(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def load_status(self) -> Dict[str, Any]:
        """Load status, handling missing/corrupt files gracefully."""
        if not self.status_file.exists():
            # Initialize with valid default
            status = {
                "system": {"status": "idle"}, 
                "version": "1.0",
                "initialized_at": self._iso_now()
            }
            self.save_status(status)
            return status

        try:
            with self.status_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Recover by rewriting sane default
            # In Phase 6C we will add audit logging here
            status = {
                "system": {"status": "idle"},
                "error": "recovered_from_corruption", 
                "updated_at": self._iso_now()
            }
            self.save_status(status)
            return status

    def save_status(self, data: Dict[str, Any]) -> None:
        """Atomic write: write to temp and replace.
        
        Prevents 0-byte corruption on crashes.
        """
        p = self.status_file
        p.parent.mkdir(parents=True, exist_ok=True)
        
        # Update timestamp
        if "last_updated" not in data:
            data["last_updated"] = self._iso_now()
        
        tmp = p.with_suffix(p.suffix + ".tmp")  # ← temp file
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # ← force disk write
        
        os.replace(tmp, p)  # ← atomic rename

    # Convenience helpers for PRD v0.4 tracking
    def set_active_environment(self, env: str) -> None:
        data = self.load_status()
        data.setdefault("pipeline", {})["active_environment"] = env
        self.save_status(data)

    def set_last_snapshot_hash(self, digest: str) -> None:
        data = self.load_status()
        data.setdefault("pipeline", {})["last_snapshot_hash"] = digest
        self.save_status(data)

    def set_last_promote_hash(self, digest: str) -> None:
        data = self.load_status()
        data.setdefault("pipeline", {})["last_promote_hash"] = digest
        self.save_status(data)


# --- WP2: Session-Local State Engine helpers ---

class LockError(Exception):
    pass


def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    """Atomically write JSON to `path` using temp file + replace.

    Ensures directory exists and avoids 0-byte files on crash.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _lock_info() -> Dict[str, Any]:
    return {
        "pid": os.getpid(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def is_lock_stale(lock_path: Path, timeout: int) -> bool:
    if not lock_path.exists():
        return False
    try:
        mtime = lock_path.stat().st_mtime
        return (time.time() - mtime) > timeout
    except Exception:
        return True


def acquire_lock(lock_path: Path, timeout: int = 30) -> None:
    """Acquire a file lock using O_EXCL, breaking stale locks after timeout seconds.

    Raises LockError if not acquired within timeout.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(_lock_info(), f)
            return
        except FileExistsError:
            # Break stale lock
            if is_lock_stale(lock_path, timeout):
                try:
                    os.remove(lock_path)
                    continue
                except Exception:
                    pass
            time.sleep(0.2)
    raise LockError(f"Could not acquire lock: {lock_path}")


def release_lock(lock_path: Path) -> None:
    try:
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        # Non-fatal
        pass


def cleanup_stale_lock(lock_path: Path, timeout: int = 30) -> None:
    if is_lock_stale(lock_path, timeout):
        try:
            lock_path.unlink()
        except Exception:
            pass


class SessionLocalState:
    """Minimal session-local state engine using session/.state/*.json files."""

    ALLOWED = {
        ("INIT", "EDITING"),
        ("EDITING", "VERIFIED"),
        ("VERIFIED", "DONE"),
    }

    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.state_dir = session_path / ".state"
        self.session_state_file = self.state_dir / "session_state.json"
        self.verify_dev_file = self.state_dir / "verify_dev.json"
        self.verify_prod_file = self.state_dir / "verify_prod.json"

    def _load(self, p: Path) -> Dict[str, Any]:
        if not p.exists():
            return {}
        try:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def current_state(self) -> str:
        data = self._load(self.session_state_file)
        return data.get("legacy_state") or data.get("state", "INIT")

    def set_state(self, new_state: str) -> None:
        cur = self.current_state()
        if (cur, new_state) not in self.ALLOWED and cur != new_state:
            raise LockError(f"Invalid state transition {cur} -> {new_state}")
        # F5 fix: merge with existing data so created_at is preserved across updates.
        existing = self._load(self.session_state_file)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        obj = dict(existing)
        obj.pop("state", None)
        obj.update({
            "version": "1.0",
            "legacy_state": new_state,
            "updated_at": now,
        })
        # Set created_at on first write only.
        if "created_at" not in obj:
            obj["created_at"] = now
        atomic_write_json(self.session_state_file, obj)

    def dev_verified(self) -> bool:
        data = self._load(self.verify_dev_file)
        return data.get("passed") is True

    def prod_verified(self) -> bool:
        data = self._load(self.verify_prod_file)
        return data.get("passed") is True

    # Phase 1 — Goal Loop graph state (separate from MVP lifecycle ALLOWED).
    # `graph_state` tracks the workflow graph (READY/THINK/SANDBOX/DO/...).
    # Set via Loop.fire(); never edited directly.

    def graph_state(self, default: Optional[str] = None) -> Optional[str]:
        data = self._load(self.session_state_file)
        return data.get("graph_state", default)

    def set_graph_state(self, new_state: str) -> None:
        existing = self._load(self.session_state_file)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        merged = dict(existing)
        if "legacy_state" not in merged and "state" in merged:
            merged["legacy_state"] = merged["state"]
        merged.pop("state", None)
        merged.update({
            "graph_state": new_state,
            "graph_state_updated_at": now,
        })
        if "created_at" not in merged:
            merged["created_at"] = now
        atomic_write_json(self.session_state_file, merged)

    # Phase 6 — Sub-graph stack (multi-graph composition).
    # When a Loop.enter_subgraph(<inner>) call fires, the kernel pushes
    # `{graph, prior_state}` onto this stack and switches the active
    # graph name. exit_subgraph pops the top frame and restores the
    # parent graph + prior_state. The stack persists in
    # session_state.json so a kernel restart resumes correctly.

    def subgraph_stack(self) -> List[Dict[str, Any]]:
        data = self._load(self.session_state_file)
        stack = data.get("subgraph_stack")
        return list(stack) if isinstance(stack, list) else []

    def push_subgraph(
        self, *, outer_graph: str, outer_state: str, inner_graph: str
    ) -> None:
        existing = self._load(self.session_state_file)
        stack = list(existing.get("subgraph_stack") or [])
        stack.append({
            "outer_graph": outer_graph,
            "outer_state": outer_state,
            "inner_graph": inner_graph,
        })
        merged = {
            **existing,
            "subgraph_stack": stack,
            "active_graph": inner_graph,
        }
        atomic_write_json(self.session_state_file, merged)

    def pop_subgraph(self) -> Optional[Dict[str, Any]]:
        """Pop the top frame; reset active_graph to the popped frame's
        `outer_graph` (which is the new top-of-stack's inner_graph if
        any frames remain, or the outermost graph if the stack is now
        empty)."""
        existing = self._load(self.session_state_file)
        stack = list(existing.get("subgraph_stack") or [])
        if not stack:
            return None
        frame = stack.pop()
        merged = {
            **existing,
            "subgraph_stack": stack,
        }
        if stack:
            # Still nested: active = the inner_graph of the new top.
            merged["active_graph"] = stack[-1]["inner_graph"]
        else:
            # Back to the outermost graph (frame.outer_graph).
            merged["active_graph"] = frame["outer_graph"]
        atomic_write_json(self.session_state_file, merged)
        return frame

    def active_graph(self, default: Optional[str] = None) -> Optional[str]:
        data = self._load(self.session_state_file)
        return data.get("active_graph", default)
