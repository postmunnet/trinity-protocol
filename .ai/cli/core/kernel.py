from __future__ import annotations
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from .artifacts import ArtifactManager, RunHeader, SetupCheckpoint, AttemptLog, Verdict, TerminalFreeze

class RuntimeState(Enum):
    READY = "READY"
    SETUP = "SETUP"
    BUSY = "BUSY"
    VERIFYING = "VERIFYING"
    GATED = "GATED"
    TERMINAL = "TERMINAL"

class KernelError(Exception):
    pass

class Kernel:
    """
    Trinity V2 Kernel (v0.1)
    Implements the 6-state Finite State Machine for reliable goal execution.
    """
    
    ALLOWED_TRANSITIONS = {
        RuntimeState.READY: {RuntimeState.SETUP},
        RuntimeState.SETUP: {RuntimeState.BUSY, RuntimeState.GATED, RuntimeState.TERMINAL},
        RuntimeState.BUSY: {RuntimeState.VERIFYING, RuntimeState.GATED, RuntimeState.TERMINAL},
        RuntimeState.VERIFYING: {RuntimeState.BUSY, RuntimeState.SETUP, RuntimeState.GATED, RuntimeState.TERMINAL},
        RuntimeState.GATED: {RuntimeState.BUSY, RuntimeState.SETUP, RuntimeState.TERMINAL},
        RuntimeState.TERMINAL: set(),  # No exit from terminal
    }

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.artifacts = ArtifactManager(run_dir)
        self.state: RuntimeState = RuntimeState.READY
        self.runtime_tainted: bool = False

    def transition_to(self, new_state: RuntimeState, reason: Optional[str] = None):
        if new_state not in self.ALLOWED_TRANSITIONS[self.state]:
            raise KernelError(f"Illegal transition: {self.state.value} -> {new_state.value}")
        
        old_state = self.state
        self.state = new_state
        
        self.artifacts.log_event("STATE_TRANSITION", {
            "from": old_state.value,
            "to": new_state.value,
            "reason": reason
        })

    def bootstrap(self, run_id: str, assignment_id: str, goal: str):
        """READY -> SETUP transition."""
        header = RunHeader(run_id=run_id, assignment_id=assignment_id, goal=goal)
        self.artifacts.write_run_header(header)
        self.artifacts.log_event("RUN_CREATED", {"run_id": run_id, "goal": goal})
        self.transition_to(RuntimeState.SETUP)

    def complete_setup(self, sandbox_id: str):
        """SETUP -> BUSY transition."""
        checkpoint = SetupCheckpoint(
            sub_phase="SESSION_BOOTSTRAP",
            checkpoint_index=7,
            last_ok_phase="SESSION_BOOTSTRAP",
            sandbox_id=sandbox_id
        )
        self.artifacts.write_setup_checkpoint(checkpoint)
        self.artifacts.log_event("SETUP_PHASE_COMPLETED", {"phase": "BOOTSTRAP", "sandbox_id": sandbox_id})
        self.transition_to(RuntimeState.BUSY)

    def record_attempt(self, attempt_id: int, status: str = "COMPLETED"):
        """BUSY -> VERIFYING transition."""
        self.artifacts.log_event("ATTEMPT_COMPLETED", {"attempt_id": attempt_id, "status": status})
        self.transition_to(RuntimeState.VERIFYING)

    def record_verdict(self, verdict: Verdict):
        """VERIFYING -> BUSY/SETUP/GATED/TERMINAL transition based on verdict."""
        self.artifacts.write_verdict(verdict)
        self.artifacts.log_event("VERDICT_EMITTED", verdict.to_dict())
        
        if verdict.candidate_verdict == "PASS":
            self.finalize(outcome="DONE", code="VERIFIER_PASS", by="verifier")
        elif verdict.candidate_verdict == "FAIL_HARD":
            self.finalize(outcome="DEAD", code="VERIFY_FAIL_HARD", by="verifier")
        elif verdict.candidate_verdict == "FAIL_RETRY":
            if verdict.retry_scope == "EXECUTION" and not self.runtime_tainted:
                self.transition_to(RuntimeState.BUSY, reason="Retry execution")
            elif verdict.retry_scope == "REBUILD_SETUP" or self.runtime_tainted:
                self.transition_to(RuntimeState.SETUP, reason="Retry setup (tainted or requested)")
            elif verdict.retry_scope == "HUMAN_GATE":
                self.transition_to(RuntimeState.GATED, reason="Human gate requested")
            else:
                # Default fallback
                self.transition_to(RuntimeState.SETUP, reason="Default retry fallback")

    def finalize(self, outcome: str, code: str, by: str, completion_status: str = "FULL"):
        """Transition to TERMINAL and freeze artifacts."""
        freeze = TerminalFreeze(
            outcome=outcome,
            code=code,
            by=by,
            completion_status=completion_status
        )
        self.artifacts.write_terminal_freeze(freeze)
        self.transition_to(RuntimeState.TERMINAL, reason=f"Finalized as {outcome}")
        self.artifacts.log_event("TERMINAL_FROZEN", freeze.to_dict())

    def request_gate(self, reason: str, awaited_actor: str = "human"):
        """Any state -> GATED transition."""
        self.artifacts.log_event("GATE_REQUESTED", {"reason": reason, "awaited": awaited_actor})
        self.transition_to(RuntimeState.GATED, reason=reason)

    def emit_context_built_capture(self, session_dir, ritual: str, context_sources: list, ritual_context=None):
        """Optional kernel self-capture for context.built (RecordProxy v1, design §8).
        Inert by default — only fires when an explicit caller passes session_dir.
        """
        if session_dir is None:
            return None
        from .recordproxy import capture
        with capture(session_dir=session_dir, ritual=ritual, role="KERNEL",
                     kind="kernel_self_capture") as cap:
            cap.input("context_sources.json", {"sources": list(context_sources)})
            if ritual_context is not None:
                cap.input("ritual_context.json", ritual_context)
        return cap.capture_id
