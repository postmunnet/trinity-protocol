"""Schema version constants for RecordProxy v1 artifacts.

Design §16 invariant: No schema_version = invalid system artifact.
Writers may advance. Readers must remember.
Raw capture artifacts are immutable.
"""

CAPTURE_SCHEMA_VERSION = "trinity.capture.v1"
AUDIT_EVENT_SCHEMA_VERSION = "trinity.audit_event.v1"
CAPTURE_ITEM_SCHEMA_VERSION = "trinity.capture_item.v1"

CAPTURE_STATUS = (
    "CAPTURING",
    "COMPLETED",
    "FAILED_PARTIAL",
    "RECONCILED",
    "ORPHANED_INVOCATION",
    "ARCHIVED",
)

CAPTURE_ITEM_KIND = (
    "input",
    "output",
    "validation",
    "runtime",
    "model",
    "env",
    "git_state",
)

REDACTION_MODE_DEFAULT = "REDACTED"
REDACTION_MODE_BREAK_GLASS = "RAW_BREAK_GLASS"
