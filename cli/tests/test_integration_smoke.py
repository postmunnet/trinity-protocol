from pathlib import Path
import json
import textwrap
import importlib.util
import os


def _load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_integration_smoke(tmp_path: Path):
    # Simulate a session structure
    session = tmp_path / "2025-12-21_smoke"
    dev = session / "DO" / "dev"
    sandbox_codex = session / "SANDBOX" / "codex"
    state_dir = session / ".state"
    dev.mkdir(parents=True)
    sandbox_codex.mkdir(parents=True)
    state_dir.mkdir(parents=True)

    (dev / "foo.txt").write_text("hello\n", encoding="utf-8")
    patch = textwrap.dedent(
        """
        --- a/foo.txt
        +++ b/foo.txt
        @@ -1,1 +1,1 @@
        -hello
        +world
        """
    ).lstrip()
    (sandbox_codex / "patch.diff").write_text(patch, encoding="utf-8")

    patch_mod = _load_mod(Path(__file__).parent.parent / "core" / "patch.py", "patch_mod")
    fs_mod = _load_mod(Path(__file__).parent.parent / "core" / "fs.py", "fs_mod")
    state_mod = _load_mod(Path(__file__).parent.parent / "core" / "state.py", "state_mod")

    # Validate scope
    patch_mod.validate_scope(patch, dev)

    # Apply into temp and atomically replace dev
    tmp = session / "DO" / "dev_tmp"
    fs_mod.safe_copy_tree(dev, tmp)
    patch_mod.apply_unified_diff(patch, tmp)
    fs_mod.atomic_replace(tmp, dev)

    # Confirm change
    assert (dev / "foo.txt").read_text(encoding="utf-8").strip() == "world"

    # Update state: INIT -> EDITING -> VERIFIED -> DONE
    sls = state_mod.SessionLocalState(session)
    assert sls.current_state() == "INIT"
    sls.set_state("EDITING")

    # Write verify reports (dev/prod PASS)
    state_mod.atomic_write_json(state_dir / "verify_dev.json", {
        "version": "1.0", "scope": "dev", "passed": True, "checks": {}
    })
    state_mod.atomic_write_json(state_dir / "verify_prod.json", {
        "version": "1.0", "scope": "prod", "passed": True, "checks": {}
    })

    sls.set_state("VERIFIED")
    sls.set_state("DONE")
    assert sls.current_state() == "DONE"

    # Append event log
    with (state_dir / "events.ndjson").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "smoke", "ok": True}) + "\n")
    assert (state_dir / "events.ndjson").stat().st_size > 0

