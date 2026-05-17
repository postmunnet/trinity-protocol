"""Redaction pipeline (design §12).

Deny-by-default. Raw passthrough only via TRINITY_RECORDPROXY_RAW=1 break-glass.

Invariant: Raw unredacted output must not be written by default.
Redaction happens before evidence is written.
"""

import os
import re
from typing import Tuple

from .schemas import REDACTION_MODE_DEFAULT, REDACTION_MODE_BREAK_GLASS

RAW_BREAK_GLASS_ENV = "TRINITY_RECORDPROXY_RAW"

_REDACTED_MARKER = "[REDACTED]"

# v1 patterns. Each entry: (rule_name, compiled_regex, replacement_template).
# replacement_template uses \g<1> ... groups when needed.
_PATTERNS = [
    (
        "bearer_token",
        re.compile(r"(Authorization\s*:\s*Bearer\s+)([A-Za-z0-9._\-+/=]{6,})", re.IGNORECASE),
        lambda m: f"{m.group(1)}{_REDACTED_MARKER}",
    ),
    (
        "pem_private_key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        lambda m: f"[REDACTED_PRIVATE_KEY:{_REDACTED_MARKER}]",
    ),
    (
        "aws_access_key",
        re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
        lambda m: _REDACTED_MARKER,
    ),
    (
        "aws_secret_key",
        re.compile(r"\b(aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{30,})[\"']?"),
        lambda m: f"{m.group(1)}={_REDACTED_MARKER}",
    ),
    (
        "gcp_service_account",
        re.compile(r'"private_key"\s*:\s*"[^"]+"', re.DOTALL),
        lambda m: f'"private_key": "{_REDACTED_MARKER}"',
    ),
    (
        "github_token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
        lambda m: _REDACTED_MARKER,
    ),
    (
        "slack_token",
        re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),
        lambda m: _REDACTED_MARKER,
    ),
    (
        "generic_api_key_assignment",
        re.compile(
            r"\b(api[_-]?key|apikey|access[_-]?token|secret[_-]?key|password)\s*[:=]\s*[\"']?([A-Za-z0-9._\-/+=]{8,})[\"']?",
            re.IGNORECASE,
        ),
        lambda m: f"{m.group(1)}={_REDACTED_MARKER}",
    ),
    (
        "env_assignment_secret",
        re.compile(
            r"^([A-Z][A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|KEY|CREDENTIAL)[A-Z0-9_]*)\s*=\s*(\S+)",
            re.MULTILINE,
        ),
        lambda m: f"{m.group(1)}={_REDACTED_MARKER}",
    ),
    (
        "db_url_with_credentials",
        re.compile(
            r"(\b(?:postgres|postgresql|mysql|mongodb|redis|amqp)://)([^:/@\s]+):([^@\s]+)@",
            re.IGNORECASE,
        ),
        lambda m: f"{m.group(1)}{m.group(2)}:{_REDACTED_MARKER}@",
    ),
    (
        "session_cookie",
        re.compile(
            r"(Cookie\s*:\s*[^;\n]*?(?:session|sid|jwt|auth)[^=]*=)([^;\n\s]+)",
            re.IGNORECASE,
        ),
        lambda m: f"{m.group(1)}{_REDACTED_MARKER}",
    ),
]


def _is_break_glass_enabled() -> bool:
    """Check the explicit human-gated env flag (design §12)."""
    return os.environ.get(RAW_BREAK_GLASS_ENV) == "1"


def redact(text: str) -> str:
    """Redact secrets from text. Deny-by-default.

    Behavior:
        - Default: applies all v1 patterns; secrets replaced with [REDACTED].
        - TRINITY_RECORDPROXY_RAW=1: returns input unchanged (break-glass).

    Returns redacted string. Use ``redact_with_metadata`` to also get the
    mode tag (REDACTED vs RAW_BREAK_GLASS) for evidence trails.
    """
    out, _ = redact_with_metadata(text)
    return out


def redact_with_metadata(text: str) -> Tuple[str, dict]:
    """Redact and return (redacted_text, metadata).

    metadata shape:
        {
            "mode": "REDACTED" | "RAW_BREAK_GLASS",
            "applied_rules": [rule_name, ...],
            "redacted_count": <int>,
        }
    """
    if _is_break_glass_enabled():
        return text, {
            "mode": REDACTION_MODE_BREAK_GLASS,
            "applied_rules": [],
            "redacted_count": 0,
        }

    applied = []
    total_redacted = 0
    out = text
    for name, pattern, replace in _PATTERNS:
        new_out, n = pattern.subn(replace, out)
        if n > 0:
            applied.append(name)
            total_redacted += n
            out = new_out

    return out, {
        "mode": REDACTION_MODE_DEFAULT,
        "applied_rules": applied,
        "redacted_count": total_redacted,
    }
