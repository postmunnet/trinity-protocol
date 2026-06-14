from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Iterable


class TemplateLoader:
    """Lightweight template loader with {{VAR}} substitution.

    Sources templates from `<ai_root>/templates` by default.
    """

    def __init__(self, templates_root: Path):
        self.templates_root = templates_root

    @classmethod
    def from_ssot(cls, ssot_config) -> "TemplateLoader":
        # Resolve templates root from SSOT
        paths = ssot_config.raw_config.get("paths", {})
        tpl = paths.get("templates", str(ssot_config.ai_root / "templates"))
        tpl_path = Path(str(tpl).replace("${ai_root}", str(ssot_config.ai_root)).replace("${project_root}", str(ssot_config.project_root)))
        # Thin-client fallback (mirrors sss._find_git_root / doctor, retro-0055):
        # a thin-linked project strips its vendored `.ai/templates`, so the
        # SSOT-resolved project-local path is absent. Fall back to the kernel's
        # own `.ai/templates` (this file lives at <kernel>/.ai/cli/core/, so
        # parents[2] is the kernel `.ai`) so scaffolding still works.
        if not tpl_path.is_dir():
            kernel_templates = Path(__file__).resolve().parents[2] / "templates"
            if kernel_templates.is_dir():
                tpl_path = kernel_templates
        return cls(tpl_path)

    def load(self, rel_path: str) -> str:
        p = self.templates_root / rel_path
        with p.open("r", encoding="utf-8") as f:
            return f.read()

    def render(self, content: str, variables: Dict[str, str]) -> str:
        rendered = content
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

    def write_rendered(self, rel_path: str, dst: Path, variables: Dict[str, str]) -> None:
        content = self.load(rel_path)
        rendered = self.render(content, variables)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("w", encoding="utf-8") as f:
            f.write(rendered)

    def copy_structure(
        self,
        src_rel_dir: str,
        dst_dir: Path,
        variables: Optional[Dict[str, str]] = None,
        exclude: Optional[Iterable[str]] = None,
    ) -> None:
        """Copy a template directory to destination, rendering text files.

        - Performs naive text render on all files (safe for md/json/txt).
        - Exclude any relative paths present in `exclude`.
        """
        variables = variables or {}
        exclude = set(exclude or [])
        src_dir = self.templates_root / src_rel_dir
        # Fail loud: a missing src_dir would otherwise make rglob() yield
        # nothing, silently producing a half-scaffolded session (the thin-client
        # bug this guards against — see retro on TemplateLoader fallback).
        if not src_dir.is_dir():
            raise FileNotFoundError(
                f"template source directory not found: {src_dir} "
                f"(templates_root={self.templates_root}, src_rel_dir={src_rel_dir!r})"
            )
        for p in src_dir.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(self.templates_root)
            # Skip excluded exact paths (relative to templates root)
            if str(rel) in exclude:
                continue
            # Also skip if any exclude entry is a top-level name match
            if any(str(rel).startswith(ex + "/") for ex in exclude):
                continue
            target = dst_dir / rel.relative_to(src_rel_dir)
            content = p.read_text(encoding="utf-8")
            rendered = self.render(content, variables)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding="utf-8")

