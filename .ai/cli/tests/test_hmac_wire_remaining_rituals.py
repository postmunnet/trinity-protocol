"""Source-inspection — verify sss/vvv/nnn/close wire enforce_hmac_or_exit."""
from __future__ import annotations

import inspect

from cli.commands import close as close_mod
from cli.commands import nnn as nnn_mod
from cli.commands import sss as sss_mod
from cli.commands import vvv as vvv_mod


def test_sss_wires_hmac_gate() -> None:
    src = inspect.getsource(sss_mod)
    assert "--hmac-envelope-file" in src
    assert "from ..core.hmac_gate import enforce_hmac_or_exit" in src
    assert 'ritual="sss"' in src


def test_vvv_wires_hmac_gate() -> None:
    src = inspect.getsource(vvv_mod)
    assert "--hmac-envelope-file" in src
    assert "from ..core.hmac_gate import enforce_hmac_or_exit" in src
    assert 'ritual="vvv"' in src


def test_nnn_wires_hmac_gate() -> None:
    src = inspect.getsource(nnn_mod)
    assert "--hmac-envelope-file" in src
    assert "from ..core.hmac_gate import enforce_hmac_or_exit" in src
    assert 'ritual="nnn"' in src


def test_close_wires_hmac_gate() -> None:
    src = inspect.getsource(close_mod)
    assert "--hmac-envelope-file" in src
    assert "from ..core.hmac_gate import enforce_hmac_or_exit" in src
    assert 'ritual="close"' in src
