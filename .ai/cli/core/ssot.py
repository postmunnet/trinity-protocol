from __future__ import annotations
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class SSOTConfig:
    project_root: Path
    ai_root: Path
    state_path: Path
    ssot_path: Path
    raw_config: Dict[str, Any]

class SSOTLoader:
    def __init__(self, project_root: Optional[Path] = None):
        # Auto-detect project root if not provided
        cwd = Path.cwd() if project_root is None else project_root
        self.project_root = self._detect_project_root(cwd)
        self.ai_root = self.project_root / ".ai"
        self.ssot_path = self.ai_root / "ssot.yaml"

    def _detect_project_root(self, start: Path) -> Path:
        """
        Detect the project root by locating a directory that contains .ai/ssot.yaml.
        - If invoked from inside .ai/, use its parent.
        - Otherwise, walk upwards until found; fallback to start if not found.
        """
        # If currently inside the .ai directory, project root is parent
        if start.name == ".ai" and (start / "ssot.yaml").exists():
            return start.parent

        # Walk upwards to find a folder that has .ai/ssot.yaml
        cur = start
        for _ in range(10):  # avoid runaway; 10 levels is plenty for typical repos
            ai_dir = cur / ".ai"
            if (ai_dir / "ssot.yaml").exists():
                return cur
            if cur.parent == cur:
                break
            cur = cur.parent

        # Fallback to starting directory
        return start

    def load(self) -> SSOTConfig:
        if not self.ssot_path.exists():
            raise FileNotFoundError(f"SSOT not found: {self.ssot_path}")
        
        with self.ssot_path.open("r", encoding="utf-8") as f:
            try:
                # Use safe_load for security
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid yaml in SSOT: {e}")

        # Basic validation (MVP)
        self._validate_config(config)

        # Resolve paths
        paths = config.get("paths", {})
        # Note: In a real implementation we'd do environment variable substitution here
        # For now, we manually map specific known paths or rely on defaults
        
        # Determine strict state path location from config or default
        state_str = paths.get("state", "${ai_root}/state")
        # simple substitution
        state_str = state_str.replace("${ai_root}", str(self.ai_root))
        state_str = state_str.replace("${project_root}", str(self.project_root))
        
        state_path = Path(state_str)
        
        return SSOTConfig(
            project_root=self.project_root,
            ai_root=self.ai_root,
            state_path=state_path,
            ssot_path=self.ssot_path,
            raw_config=config
        )

    def _validate_config(self, cfg: Dict[str, Any]) -> None:
        if not isinstance(cfg, dict):
            raise ValueError("SSOT must be a mapping")
        if "version" not in cfg:
            raise ValueError("SSOT missing 'version'")
        if "paths" not in cfg or not isinstance(cfg["paths"], dict):
            raise ValueError("SSOT missing 'paths' section")
        # Deploy section validation (optional)
        deploy = cfg.get("deploy", {})
        if deploy and not isinstance(deploy, dict):
            raise ValueError("'deploy' must be a mapping")
        for env in ("dev", "prod"):
            d = deploy.get(env)
            if not d:
                continue
            if not isinstance(d, dict):
                raise ValueError(f"deploy.{env} must be a mapping")
            dtype = d.get("type", "local_copy")
            if dtype not in ("local_copy", "rsync", "scp"):
                raise ValueError(f"deploy.{env}.type unsupported: {dtype}")
            if dtype == "local_copy":
                if "path" not in d:
                    raise ValueError(f"deploy.{env}.path required for local_copy")
            if dtype in ("rsync", "scp"):
                if not d.get("host") or not d.get("path"):
                    raise ValueError(f"deploy.{env}.host and .path required for {dtype}")
