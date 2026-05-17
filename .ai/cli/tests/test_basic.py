import json
import os
import pytest

def section(name):
    print(f"\n[BOOTSTRAP] Testing {name}...")

def test_ssot_exists():
    section("SSOT Existence")
    assert os.path.exists(".ai/ssot.yaml"), "SSOT file missing!"

def test_state_initialized():
    section("State Initialization")
    assert os.path.exists(".ai/state/status.json"), "status.json missing!"
    with open(".ai/state/status.json") as f:
        data = json.load(f)
        # R5 — accept idle OR busy; the kernel writes "busy" while a
        # session is active and "idle" between sessions. The original
        # assert flaked any time tests ran during an open session.
        assert data["system"]["status"] in ("idle", "busy"), (
            "System status should be idle|busy"
        )

def test_canaries_exist():
    section("Canary Existence")
    assert os.path.exists(".ai/testing/canaries/canary_with_secrets.py")
