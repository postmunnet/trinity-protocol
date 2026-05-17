from pathlib import Path
import textwrap
import json
import importlib.util


def _load_patch_module():
    here = Path(__file__).resolve()
    mod_path = here.parent.parent / "core" / "patch.py"
    spec = importlib.util.spec_from_file_location("patch_mod", mod_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_apply_valid_patch_modify(tmp_path: Path):
    mod = _load_patch_module()
    root = tmp_path / "dev"
    root.mkdir()
    (root / "foo.txt").write_text("hello\n", encoding="utf-8")
    diff = textwrap.dedent(
        """
        --- a/foo.txt
        +++ b/foo.txt
        @@ -1,1 +1,1 @@
        -hello
        +world
        """
    ).lstrip()
    res = mod.apply_unified_diff(diff, root)
    assert res["applied"] is True
    assert (root / "foo.txt").read_text(encoding="utf-8").strip() == "world"


def test_apply_create_file(tmp_path: Path):
    mod = _load_patch_module()
    root = tmp_path / "dev"
    root.mkdir()
    diff = textwrap.dedent(
        """
        --- /dev/null
        +++ b/new.txt
        @@ -0,0 +1,1 @@
        +new line
        """
    ).lstrip()
    res = mod.apply_unified_diff(diff, root)
    assert (root / "new.txt").exists()
    assert (root / "new.txt").read_text(encoding="utf-8").strip() == "new line"


def test_reject_binary_patch(tmp_path: Path):
    mod = _load_patch_module()
    root = tmp_path / "dev"
    root.mkdir()
    diff = "GIT binary patch\nxyz\n"
    try:
        mod.apply_unified_diff(diff, root)
        assert False, "expected PatchError"
    except mod.PatchError:
        pass


def test_scope_guard_outside(tmp_path: Path):
    mod = _load_patch_module()
    root = tmp_path / "dev"
    root.mkdir()
    diff = textwrap.dedent(
        """
        --- a/../../etc/passwd
        +++ b/../../etc/passwd
        @@ -1,1 +1,1 @@
        -x
        +y
        """
    ).lstrip()
    try:
        mod.validate_scope(diff, root)
        assert False, "expected PatchError"
    except mod.PatchError:
        pass


def test_dry_run(tmp_path: Path):
    mod = _load_patch_module()
    root = tmp_path / "dev"
    root.mkdir()
    (root / "foo.txt").write_text("hello\n", encoding="utf-8")
    diff = textwrap.dedent(
        """
        --- a/foo.txt
        +++ b/foo.txt
        @@ -1,1 +1,1 @@
        -hello
        +world
        """
    ).lstrip()
    res = mod.apply_unified_diff(diff, root, dry_run=True)
    assert res["applied"] is False
    assert (root / "foo.txt").read_text(encoding="utf-8").strip() == "hello"

