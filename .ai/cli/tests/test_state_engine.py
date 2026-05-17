from pathlib import Path
import json
import os
import time
import importlib.util


def _load_state_module():
    here = Path(__file__).resolve()
    mod_path = here.parent.parent / "core" / "state.py"
    spec = importlib.util.spec_from_file_location("state_mod", mod_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_atomic_write_json_nonzero(tmp_path: Path):
    mod = _load_state_module()
    p = tmp_path / "state.json"
    for i in range(3):
        mod.atomic_write_json(p, {"i": i})
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["i"] == i
        assert p.stat().st_size > 0


def test_lock_acquire_release(tmp_path: Path):
    mod = _load_state_module()
    lock = tmp_path / "LOCK"
    mod.acquire_lock(lock, timeout=2)
    assert lock.exists()
    # Second acquire should block then raise
    t0 = time.time()
    try:
        mod.acquire_lock(lock, timeout=1)
        assert False, "expected LockError"
    except mod.LockError:
        pass
    finally:
        mod.release_lock(lock)
    assert lock.exists() is False


def test_stale_lock_cleanup(tmp_path: Path):
    mod = _load_state_module()
    lock = tmp_path / "LOCK"
    mod.acquire_lock(lock, timeout=2)
    # Make it stale by backdating mtime
    old = time.time() - 100
    os.utime(lock, (old, old))
    assert mod.is_lock_stale(lock, timeout=1) is True
    mod.cleanup_stale_lock(lock, timeout=1)
    assert not lock.exists()


def test_session_local_state_transitions(tmp_path: Path):
    mod = _load_state_module()
    session = tmp_path / "session"
    (session / ".state").mkdir(parents=True)
    sls = mod.SessionLocalState(session)
    assert sls.current_state() == "INIT"
    sls.set_state("EDITING")
    assert sls.current_state() == "EDITING"
    sls.set_state("VERIFIED")
    assert sls.current_state() == "VERIFIED"
    sls.set_state("DONE")
    assert sls.current_state() == "DONE"
    # Illegal transition
    try:
        sls.set_state("EDITING")
        assert False, "invalid transition not rejected"
    except mod.LockError:
        pass
