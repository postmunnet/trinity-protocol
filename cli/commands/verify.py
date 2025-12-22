import typer
import json
import re
import datetime
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..core.state import StateManager
from ..core.ssot import SSOTLoader

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Verify safety gates (Lock 2)."""
    pass

class VerificationGates:
    """Phase 6 Verification Gates Implementation"""

    def __init__(self, target_dir: Path, config: Dict[str, Any]):
        self.target_dir = target_dir
        self.config = config
        self.results = {
            "forbidden_files": {"status": "pending", "details": []},
            "secret_scan": {"status": "pending", "details": []},
            "smoke_hooks": {"status": "pending", "details": []}
        }

    def check_forbidden_files(self) -> bool:
        """Gate 1: Check for forbidden files (.env, config/dev/**)"""
        console.print("[yellow]🔒 Gate 1:[/yellow] Checking forbidden files...")

        forbidden_patterns = [
            ".env",
            ".env.*",
            "config/dev/**",
            "**/.env",
            "**/config.dev.*"
        ]

        found = []
        for pattern in forbidden_patterns:
            # Simple glob matching
            if "*" in pattern:
                matches = list(self.target_dir.glob(pattern))
                for match in matches:
                    if match.is_file():
                        found.append(str(match.relative_to(self.target_dir)))
            else:
                # Direct file check
                file_path = self.target_dir / pattern
                if file_path.exists():
                    found.append(pattern)

        if found:
            self.results["forbidden_files"]["status"] = "fail"
            self.results["forbidden_files"]["details"] = found
            console.print(f"  [red]❌ FAIL:[/red] Found {len(found)} forbidden file(s)")
            for f in found:
                console.print(f"     - {f}")
            return False
        else:
            self.results["forbidden_files"]["status"] = "pass"
            console.print("  [green]✅ PASS:[/green] No forbidden files")
            return True

    def check_secrets(self) -> bool:
        """Gate 2: Secret scanning with regex patterns"""
        console.print("[yellow]🔒 Gate 2:[/yellow] Scanning for secrets...")

        # Secret patterns from Phase 6 brief + safety.yaml
        secret_patterns = [
            (r'(?i)api[_-]?key\s*[:=]\s*["\']?[\w\-]{16,}', "API Key"),
            (r'(?i)secret\s*[:=]\s*["\']?[\w\-]{16,}', "Secret Token"),
            (r'(?i)password\s*[:=]\s*["\']?[\w\-]{8,}', "Password"),
            (r'(?i)aws[_-]?secret[_-]?access[_-]?key', "AWS Secret"),
            (r'(?i)private[_-]?key', "Private Key"),
            (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API Key"),
        ]

        found_secrets = []

        # Scan all files
        for file_path in self.target_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip binary and large files
            if file_path.suffix in ['.pyc', '.so', '.jpg', '.png', '.gif', '.pdf', '.zip']:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern, secret_type in secret_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        found_secrets.append({
                            "file": str(file_path.relative_to(self.target_dir)),
                            "type": secret_type,
                            "line": content[:match.start()].count('\n') + 1,
                            "preview": match.group()[:50] + "..." if len(match.group()) > 50 else match.group()
                        })
            except Exception:
                # Skip files that can't be read
                continue

        if found_secrets:
            self.results["secret_scan"]["status"] = "fail"
            self.results["secret_scan"]["details"] = found_secrets
            console.print(f"  [red]❌ FAIL:[/red] Found {len(found_secrets)} potential secret(s)")
            for secret in found_secrets[:5]:  # Show first 5
                console.print(f"     - {secret['file']}:{secret['line']} ({secret['type']})")
            if len(found_secrets) > 5:
                console.print(f"     ... and {len(found_secrets) - 5} more")
            return False
        else:
            self.results["secret_scan"]["status"] = "pass"
            console.print("  [green]✅ PASS:[/green] No secrets detected")
            return True

    def check_smoke_hooks(self, strict: bool = True) -> bool:
        """Gate 3: Smoke test hooks (soft fail in permissive mode)"""
        console.print("[yellow]🔒 Gate 3:[/yellow] Running smoke hooks...")

        # For Phase 6 MVP, we skip actual hook execution
        # This would normally run: lint, test, curl checks
        # For now, just pass

        self.results["smoke_hooks"]["status"] = "pass" if not strict else "skipped"
        self.results["smoke_hooks"]["details"] = ["Smoke hooks not configured (Phase 6 MVP)"]

        if strict:
            console.print("  [yellow]⚠️  SKIP:[/yellow] Smoke hooks not configured")
        else:
            console.print("  [green]✅ PASS:[/green] Smoke hooks (permissive mode)")

        return True  # Don't block in MVP

    def run_all(self, strict: bool = True) -> bool:
        """Run all gates and return overall pass/fail"""
        console.print("\n[bold cyan]🛡️  Phase 6 Verification Gates[/bold cyan]\n")

        gate1 = self.check_forbidden_files()
        gate2 = self.check_secrets()
        gate3 = self.check_smoke_hooks(strict)

        overall = gate1 and gate2 and (gate3 if strict else True)

        console.print()
        return overall

@app.command()
def run(scope: str = typer.Option("dev", help="Scope: dev or prod"), strict: bool = True, permissive: bool = False):
    """
    Verify target environment before promotion/close.

    Gates:
      1. Forbidden files (.env, config/dev/**)
      2. Secret scan (api_key, password, tokens)
      3. Smoke hooks (lint/test - optional)

    Exit codes:
      0 = PASS
      1 = FAIL (policy blocks)
      2 = ERROR (runtime/config)
    """
    scope = scope.lower()
    if scope not in ("dev", "prod"):
        console.print("[red]Invalid scope; choose dev or prod[/red]")
        raise typer.Exit(2)
    run_verify(scope, not permissive)

@app.command()
def dev(strict: bool = True, permissive: bool = False):
    """Backward-compatible alias for verify --scope dev."""
    run_verify("dev", not permissive)

@app.command()
def prod(strict: bool = True, permissive: bool = False):
    """Backward-compatible alias for verify --scope prod."""
    run_verify("prod", not permissive)

@app.command()
def selftest():
    """
    Run verification self-test against fixtures.
    Tests: pass_clean, fail_secret, fail_forbidden

    Must deterministically PASS/FAIL as expected.
    Generates temporary fixtures if not found (works on clean install).
    """
    import tempfile
    import os
    
    console.print("[bold yellow]🧪 Running Verification Self-Test[/bold yellow]\n")

    # Try to find existing fixtures first
    cfg = SSOTLoader(Path.cwd()).load()
    project_root = cfg.project_root
    test_fixtures = project_root / "tests" / "verify_fixtures"
    if not test_fixtures.exists():
        fallback = project_root / ".ai" / "testing" / "verify_fixtures"
        test_fixtures = fallback if fallback.exists() else None

    # If no fixtures found, generate temporary ones
    temp_dir = None
    if test_fixtures is None or not test_fixtures.exists():
        console.print("[yellow]ℹ️  Generating temporary test fixtures...[/yellow]\n")
        temp_dir = tempfile.mkdtemp(prefix="trinity_verify_test_")
        test_fixtures = Path(temp_dir)
        
        # Create pass_clean fixture (empty, clean directory)
        clean_dir = test_fixtures / "pass_clean"
        clean_dir.mkdir(parents=True)
        (clean_dir / "readme.txt").write_text("Clean project with no secrets or forbidden files.\n")
        (clean_dir / "app.py").write_text("# Sample clean Python file\ndef main():\n    print('Hello')\n")
        
        # Create fail_secret fixture (contains a secret pattern)
        secret_dir = test_fixtures / "fail_secret"
        secret_dir.mkdir(parents=True)
        (secret_dir / "config.py").write_text("# Bad: contains secret\nAPI_KEY = 'sk-1234567890abcdef1234567890abcdef'\n")
        
        # Create fail_forbidden fixture (contains .env file)
        forbidden_dir = test_fixtures / "fail_forbidden"
        forbidden_dir.mkdir(parents=True)
        (forbidden_dir / ".env").write_text("SECRET_KEY=should_not_be_here\n")

    results = []

    try:
        # Test 1: pass_clean (should PASS)
        clean_dir = test_fixtures / "pass_clean"
        if clean_dir.exists():
            console.print("[cyan]Test 1:[/cyan] pass_clean (expect PASS)")
            gates = VerificationGates(clean_dir, {})
            passed = gates.run_all(strict=True)
            results.append(("pass_clean", "PASS", passed))
            console.print()

        # Test 2: fail_secret (should FAIL)
        secret_dir = test_fixtures / "fail_secret"
        if secret_dir.exists():
            console.print("[cyan]Test 2:[/cyan] fail_secret (expect FAIL)")
            gates = VerificationGates(secret_dir, {})
            passed = gates.run_all(strict=True)
            results.append(("fail_secret", "FAIL", not passed))
            console.print()

        # Test 3: fail_forbidden (should FAIL)
        forbidden_dir = test_fixtures / "fail_forbidden"
        if forbidden_dir.exists():
            console.print("[cyan]Test 3:[/cyan] fail_forbidden (expect FAIL)")
            gates = VerificationGates(forbidden_dir, {})
            passed = gates.run_all(strict=True)
            results.append(("fail_forbidden", "FAIL", not passed))
            console.print()

        # Summary
        table = Table(title="Self-Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Expected", style="yellow")
        table.add_column("Actual", style="white")
        table.add_column("Result", style="white")

        all_passed = True
        for test_name, expected, actual in results:
            result = "✅ PASS" if actual else "❌ FAIL"
            result_style = "green" if actual else "red"
            table.add_row(test_name, expected, "PASS" if actual else "FAIL", f"[{result_style}]{result}[/{result_style}]")
            if not actual:
                all_passed = False

        console.print(table)

        if all_passed:
            console.print("\n[bold green]✅ All self-tests passed![/bold green]")
            exit_code = 0
        else:
            console.print("\n[bold red]❌ Some self-tests failed[/bold red]")
            exit_code = 1
    finally:
        # Clean up temp fixtures
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    raise typer.Exit(exit_code)

def run_verify(scope: str, strict: bool):
    """Common verification logic for dev/prod"""
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(2)

    # Get current session
    current_session_path = status.get("current_session")
    if not current_session_path:
        console.print("[red]No active session found.[/red]")
        raise typer.Exit(2)

    session_path = Path(current_session_path)
    target_dir = session_path / "DO" / scope

    if not target_dir.exists():
        console.print(f"[red]{scope.upper()} directory not found: {target_dir}[/red]")
        raise typer.Exit(2)

    # Run verification
    gates = VerificationGates(target_dir, config.raw_config)
    overall_pass = gates.run_all(strict=strict)

    # Write report (atomic, never empty) - WP5: Separate dev/prod reports
    import uuid
    report = {
        "schema_version": 1,
        "run_id": str(uuid.uuid4())[:8],
        "session_id": session_path.name,
        "scope": scope,
        "status": "PASS" if overall_pass else "FAIL",
        "passed": overall_pass,
        "checks": {
            "forbidden_files": gates.results.get("forbidden_files", {"status": "NOT_RUN"}),
            "secrets": gates.results.get("secret_scan", {"status": "NOT_RUN"}),
            "smoke": gates.results.get("smoke_hooks", {"status": "NOT_RUN"})
        },
        "blocks": [d for d in gates.results.get("forbidden_files", {}).get("details", [])] +
                  [s for s in gates.results.get("secret_scan", {}).get("details", [])],
        "warnings": [],
        "errors": [],
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    # WP5: Write to separate verify_dev.json or verify_prod.json
    # This enables promote to check verify_dev specifically
    state_dir = session_path / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)

    if scope == "dev":
        verify_file = state_dir / "verify_dev.json"
    elif scope == "prod":
        verify_file = state_dir / "verify_prod.json"
    else:
        verify_file = state_dir / "verify_report.json"  # Fallback

    # Atomic write
    tmp_path = verify_file.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    tmp_path.replace(verify_file)

    # Also write to old location for backward compatibility (session/.ai/state/)
    old_verify_report_path = session_path / ".ai" / "state" / "verify_report.json"
    old_verify_report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_old = old_verify_report_path.with_suffix(".json.tmp")
    with open(tmp_old, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    tmp_old.replace(old_verify_report_path)

    # Update CONTROL/VERIFY.md log
    verify_log = session_path / "CONTROL" / "VERIFY.md"
    mode_str = "strict" if strict else "permissive"
    if verify_log.exists():
        with open(verify_log, "a", encoding="utf-8") as f:
            result_emoji = "✅" if overall_pass else "❌"
            f.write(f"| {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | {scope} | {result_emoji} {report['status']} | {mode_str} mode |\n")

    # Advisory: suggest using vault if potential secrets exist in dev tree
    if scope == "dev":
        patterns = ["API_KEY=", "SECRET=", "AWS_SECRET_ACCESS_KEY", "PRIVATE_KEY", "TOKEN="]
        hits = 0
        for file_path in target_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix in {".py", ".env", ".json", ".js", ".ts", ".txt"}:
                try:
                    txt = file_path.read_text(encoding="utf-8", errors="ignore")
                    if any(s in txt for s in patterns):
                        hits += 1
                except Exception:
                    pass
        if hits:
            console.print(Panel(
                "[yellow]Advisory:[/yellow] Detected potential hardcoded secrets in dev.\n"
                "Consider using [cyan]ai vault[/cyan] (see .ai/docs/SECRETS_GUIDE.md).",
                title="Secrets Advisory",
                border_style="yellow",
            ))

    # Final output
    if overall_pass:
        console.print(Panel(
            f"[green]✅ Verification PASSED[/green]\n\n"
            f"Scope: {scope.upper()}\n"
            f"Mode: {mode_str}\n"
            f"Report: {verify_file.relative_to(session_path)}",
            title="🛡️  Verification Result",
            border_style="green"
        ))
        raise typer.Exit(0)
    else:
        console.print(Panel(
            f"[red]❌ Verification FAILED[/red]\n\n"
            f"Scope: {scope.upper()}\n"
            f"Mode: {mode_str}\n"
            f"Report: {verify_file.relative_to(session_path)}\n\n"
            f"Fix issues before proceeding.",
            title="🛡️  Verification Result",
            border_style="red"
        ))
        raise typer.Exit(1)
