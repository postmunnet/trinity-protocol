import typer
from pathlib import Path
from rich.console import Console
from ..core.vault import LocalVault

app = typer.Typer()
console = Console()


def _vault() -> LocalVault:
    return LocalVault(Path.cwd() / ".ai")


@app.callback()
def callback():
    """Local Secrets Vault (demo-grade for v0.5)."""
    pass


@app.command()
def set(key: str, value: str):
    v = _vault()
    v.set_secret(key, value)
    console.print(f"[green]Stored secret:[/green] {key}")


@app.command()
def get(key: str):
    v = _vault()
    val = v.get_secret(key)
    if val is None:
        console.print(f"[yellow]Not found:[/yellow] {key}")
        raise typer.Exit(1)
    print(val)


@app.command()
def delete(key: str):
    v = _vault()
    ok = v.delete_secret(key)
    console.print("[green]Deleted[/green]" if ok else "[yellow]Not found[/yellow]")


@app.command()
def list():  # noqa: A003
    v = _vault()
    keys = v.list_keys()
    if not keys:
        console.print("[dim]No secrets stored[/dim]")
        return
    for k in keys:
        print(k)

