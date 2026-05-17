from __future__ import annotations
import re
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any


class PatchError(Exception):
    pass


_HUNK_RE = re.compile(r"^@@ -(?P<o_start>\d+)(,(?P<o_count>\d+))? \+(?P<n_start>\d+)(,(?P<n_count>\d+))? @@")


def _norm_rel_path(p: str) -> str:
    # strip a/ or b/ prefixes if present
    if p.startswith("a/") or p.startswith("b/"):
        p = p[2:]
    return p


def _ensure_safe_rel_path(root: Path, rel_path: str) -> Path:
    if rel_path in ("/dev/null", "dev/null"):
        raise PatchError("/dev/null is not a valid target path here")
    # reject absolute
    if os.path.isabs(rel_path):
        raise PatchError(f"Absolute paths not allowed: {rel_path}")
    # normalize and ensure no backtracking
    rel_norm = Path(rel_path).as_posix()
    if rel_norm.startswith("../") or "/../" in rel_norm:
        raise PatchError(f"Path escapes root: {rel_path}")
    # reject sensitive areas by contract
    top = rel_norm.split("/", 1)[0]
    if top in {"THINK", "CONTROL"} or top.startswith(".state"):
        raise PatchError(f"Patch targets forbidden area: {rel_path}")
    # resolve under root and ensure within
    resolved = (root / rel_norm).resolve()
    if not str(resolved).startswith(str(root.resolve())):
        raise PatchError(f"Path escapes root after resolve: {rel_path}")
    return resolved


def _read_text_lines(p: Path) -> List[str]:
    try:
        return p.read_text(encoding="utf-8").splitlines(keepends=True)
    except FileNotFoundError:
        return []


def _write_text_lines(p: Path, lines: List[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    # Ensure trailing newline for text files
    content = "".join(lines)
    if lines and not content.endswith("\n"):
        content += "\n"
    p.write_text(content, encoding="utf-8")


def _apply_hunks_to_lines(original: List[str], hunks: List[List[Tuple[str, str]]], o_starts: List[int]) -> List[str]:
    new_lines: List[str] = []
    cur = 0  # index into original lines (0-based)
    for hunk, o_start in zip(hunks, o_starts):
        target_index = max(o_start - 1, 0)
        if target_index < cur:
            raise PatchError("Hunks out of order or overlapping")
        # copy unchanged region up to start of this hunk
        new_lines.extend(original[cur:target_index])
        cur = target_index
        # apply hunk operations
        for op, text in hunk:
            if op == ' ':
                # context line must match
                if cur >= len(original) or original[cur] != text:
                    raise PatchError("Context mismatch while applying hunk")
                new_lines.append(original[cur])
                cur += 1
            elif op == '-':
                # deletion must match
                if cur >= len(original) or original[cur] != text:
                    raise PatchError("Deletion mismatch while applying hunk")
                cur += 1
            elif op == '+':
                new_lines.append(text)
            else:
                raise PatchError(f"Unknown hunk operation: {op}")
    # append remainder of file
    new_lines.extend(original[cur:])
    return new_lines


def _parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    if "GIT binary patch" in diff_text or re.search(r"^Binary files ", diff_text, re.M):
        raise PatchError("Binary patches are not allowed")

    lines = diff_text.splitlines(keepends=True)
    i = 0
    patches: List[Dict[str, Any]] = []
    while i < len(lines):
        # skip noise lines like diff --git / index / file mode
        if lines[i].startswith("diff ") or lines[i].startswith("index ") or lines[i].startswith("new file mode") or lines[i].startswith("deleted file mode"):
            i += 1
            continue
        if i + 1 < len(lines) and lines[i].startswith("--- ") and lines[i+1].startswith("+++ "):
            old_path = lines[i][4:].strip()
            new_path = lines[i+1][4:].strip()
            i += 2
            hunks: List[List[Tuple[str, str]]] = []
            o_starts: List[int] = []
            # consume hunks for this file
            while i < len(lines) and lines[i].startswith("@@ "):
                m = _HUNK_RE.match(lines[i].strip())
                if not m:
                    raise PatchError("Invalid hunk header")
                o_start = int(m.group('o_start'))
                o_count = int(m.group('o_count') or '0')
                i += 1
                ops: List[Tuple[str, str]] = []
                # consume hunk lines until next hunk or file header or EOF
                while i < len(lines) and not (lines[i].startswith('@@ ') or lines[i].startswith('--- ')):
                    if lines[i][0] in (' ', '+', '-'):
                        # Store line with its leading indicator removed but keep original newline
                        ops.append((lines[i][0], lines[i][1:]))
                        i += 1
                    else:
                        # end of hunk
                        break
                hunks.append(ops)
                o_starts.append(o_start)
            patches.append({
                'old_path': old_path,
                'new_path': new_path,
                'hunks': hunks,
                'o_starts': o_starts,
            })
        else:
            # skip unrelated line
            i += 1
    if not patches:
        raise PatchError("No file hunks found; require unified diff with ---/+++ headers")
    return patches


def validate_scope(diff_text: str, allowed_root: Path) -> List[Path]:
    patches = _parse_unified_diff(diff_text)
    targets: List[Path] = []
    for p in patches:
        newp = p['new_path']
        oldp = p['old_path']
        # choose path to validate (prefer new unless /dev/null)
        chosen = newp if not newp.endswith("/dev/null") and newp != "/dev/null" else oldp
        chosen = _norm_rel_path(chosen)
        # special-case /dev/null when creating/deleting: will validate later
        if chosen in ("/dev/null", "dev/null"):
            continue
        targets.append(_ensure_safe_rel_path(allowed_root, chosen))
    return targets


def apply_unified_diff(diff_text: str, root_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    patches = _parse_unified_diff(diff_text)
    touched: List[str] = []
    for p in patches:
        old_path = _norm_rel_path(p['old_path'])
        new_path = _norm_rel_path(p['new_path'])
        # Handle create/delete
        creating = old_path in ("/dev/null", "dev/null")
        deleting = new_path in ("/dev/null", "dev/null")
        if creating and deleting:
            raise PatchError("Invalid patch: both old and new are /dev/null")

        if not creating:
            src = _ensure_safe_rel_path(root_dir, old_path)
        else:
            src = None
        if not deleting:
            dst = _ensure_safe_rel_path(root_dir, new_path)
        else:
            dst = None

        if deleting:
            # Remove file
            if not dry_run:
                if dst is None and src and src.exists():
                    src.unlink()
            touched.append(old_path)
            continue

        # Modify or create
        original = _read_text_lines(src) if src else []
        new_lines = _apply_hunks_to_lines(original, p['hunks'], p['o_starts'])
        if not dry_run and dst is not None:
            _write_text_lines(dst, new_lines)
        touched.append(new_path)
    return {"applied": not dry_run, "touched": touched}

