"""Trinity RecordProxy v1 — evidence transaction layer.

Design ref: session 0002 THINK/DESIGN.md (2026-05-13).

Public surface:
    from cli.core.recordproxy import capture, CaptureStore, AuditWriter, redact

Invariants (design §22):
    - RecordProxy captures the agent.
    - Audit captures the system.
    - Redaction happens before evidence is written.
    - No schema_version = invalid system artifact.
"""

from .record_proxy import capture, new_capture_id
from .capture_store import CaptureStore
from .audit_writer import AuditWriter
from .redaction import redact
from .schemas import (
    CAPTURE_SCHEMA_VERSION,
    AUDIT_EVENT_SCHEMA_VERSION,
    CAPTURE_ITEM_SCHEMA_VERSION,
)

__all__ = [
    "capture",
    "new_capture_id",
    "CaptureStore",
    "AuditWriter",
    "redact",
    "CAPTURE_SCHEMA_VERSION",
    "AUDIT_EVENT_SCHEMA_VERSION",
    "CAPTURE_ITEM_SCHEMA_VERSION",
]
