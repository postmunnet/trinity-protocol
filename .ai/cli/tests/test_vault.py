from pathlib import Path
import importlib.util


def _load_vault_module():
    here = Path(__file__).resolve()
    mod_path = here.parent.parent / "core" / "vault.py"
    spec = importlib.util.spec_from_file_location("vault_mod", mod_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_local_vault_set_get_list_delete(tmp_path: Path):
    mod = _load_vault_module()
    ai_root = tmp_path / ".ai"
    ai_root.mkdir()
    v = mod.LocalVault(ai_root)

    # Set & get
    v.set_secret("API_TOKEN", "s3cr3t")
    assert v.get_secret("API_TOKEN") == "s3cr3t"

    # List contains the key
    keys = v.list_keys()
    assert "API_TOKEN" in keys

    # Delete and ensure gone
    assert v.delete_secret("API_TOKEN") is True
    assert v.get_secret("API_TOKEN") is None
