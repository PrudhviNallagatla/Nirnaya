# nirnaya/cli.py
"""Typer developer command-line portal entrypoint for Nirnaya.

Exposes native commands to scaffold workspace projects, track contract states,
and assert ABI preservation metrics inside CI pipelines.
"""

from pathlib import Path
from typing import List, Optional
import typer

from nirnaya import __version__
from nirnaya.storage.git import GitWorkspace
from nirnaya.storage.vault import StorageVault
from nirnaya.context.compile_commands import CompileCommandsReader
from nirnaya.core.parser import HeaderParser
from nirnaya.core.diff import BlueprintDiffEngine
from nirnaya.output.reporter import TerminalReporter
from nirnaya.context.discovery import HeaderDiscovery

app = typer.Typer(
    name="nirnaya",
    help="C++ interface contract verification engine tracking ABI layout drift.",
    no_args_is_help=True,
)


def _get_vault_or_exit(reporter: TerminalReporter) -> StorageVault:
    """Helper utility to resolve workspace storage boundaries securely."""
    git_ctx = GitWorkspace()
    root = git_ctx.find_repo_root()
    if not root:
        reporter.print_error(
            "Nirnaya must be initialized inside a valid active Git repository workspace."
        )
        raise typer.Exit(code=2)

    vault = StorageVault(root)
    if not vault.vault_dir.exists():
        reporter.print_error(
            "No active .nirnaya vault metadata vault discovered. Run 'nirnaya init' first."
        )
        raise typer.Exit(code=2)
    return vault


@app.command()
def init(
    headers: Optional[List[str]] = typer.Argument(
        None, help="Target C++ interface headers to bind under tracking constraint."
    ),
    project_name: str = typer.Option(
        "mylib",
        "--name",
        "-n",
        help="Human-readable reference name tag for the project asset.",
    ),
):
    """Initializes a local .nirnaya vault and sets up baseline golden snapshots."""
    reporter = TerminalReporter()
    git_ctx = GitWorkspace()
    root = git_ctx.find_repo_root()

    if not root:
        reporter.print_error(
            "Could not find a valid Git root repository container boundary."
        )
        raise typer.Exit(code=2)

    vault = StorageVault.initialize(root, project_name)
    reporter.print_success(
        f"Initialized storage vault registry inside [cyan]{vault.vault_dir}[/cyan]"
    )

    # AUTOMATED CHECK ENHANCEMENT: If no file arguments are provided, run our auto-crawl
    if not headers:
        reporter.print_warning(
            "No explicit target headers provided. Running automated workspace discovery crawl..."
        )
        discoverer = HeaderDiscovery(root)
        discovered_paths = discoverer.discover_public_headers()
        # Translate absolute system paths to clean relative strings for the config file
        headers = [
            str(git_ctx.get_relative_path(p).as_posix()) for p in discovered_paths
        ]

    if not headers:
        reporter.print_warning(
            "Crawl complete: No C++ header files found in this workspace layout."
        )
        raise typer.Exit(code=0)

    # Process all tracked or newly discovered headers
    vault.track_headers(headers)
    parser = HeaderParser()
    cmd_reader = CompileCommandsReader()

    # Validate existence first, then track only the confirmed ones
    valid_headers = []
    for h in headers:
        h_path = (root / h).resolve()
        if not h_path.exists():
            reporter.print_warning(
                f"Header target file reference not found on disk: {h}"
            )
        else:
            valid_headers.append(h)

    if not valid_headers:
        reporter.print_warning("No valid header files found to track.")
        raise typer.Exit(code=0)

    vault.track_headers(valid_headers)  # only registers confirmed files
    parser = HeaderParser()
    cmd_reader = CompileCommandsReader()

    for h in valid_headers:
        h_path = (root / h).resolve()
        flags = cmd_reader.get_flags_for_header(str(h_path))
        try:
            blueprint = parser.parse_header(str(h_path), compiler_flags=flags)
            vault.save_blueprint(blueprint)
            reporter.print_success(
                f"Captured immutable baseline profile snapshot for: [cyan]{h}[/cyan]"
            )
        except Exception as e:
            reporter.print_error(f"Failed parsing target layout configuration {h}: {e}")

    reporter.print_success(
        f"Tracked and cataloged [bold]{len(valid_headers)}[/bold] interface contracts."
    )


@app.command()
def check(
    header: Optional[str] = typer.Argument(
        None, help="Check an isolated file layout definition specifically."
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Mutes rich text coloring escape sequences completely.",
    ),
):
    """Audits active C++ header layouts against local working tree drift anomalies."""
    reporter = TerminalReporter(use_color=not no_color)
    vault = _get_vault_or_exit(reporter)

    headers_to_check = [header] if header else vault.get_tracked_headers()
    if not headers_to_check:
        reporter.print_warning(
            "No trackable contract configurations found. Register targets with 'nirnaya init <files>'"
        )
        raise typer.Exit(code=0)

    parser = HeaderParser()
    cmd_reader = CompileCommandsReader()
    global_violations_found = False
    git_ctx = GitWorkspace()
    root = git_ctx.find_repo_root()

    if not root:
        reporter.print_error(
            "Could not find a valid Git root repository container boundary."
        )
        raise typer.Exit(code=2)

    for h in headers_to_check:
        h_path = (root / h).resolve()  # anchored to git root, not CWD
        if not h_path.exists():
            reporter.print_error(
                f"Tracked element link severed. File missing from layout: {h}"
            )
            global_violations_found = True
            continue

        try:
            old_blueprint = vault.load_blueprint(h)
        except FileNotFoundError:
            reporter.print_error(
                f"Missing historical baseline configuration trace for tracked asset: {h}"
            )
            global_violations_found = True
            continue

        flags = cmd_reader.get_flags_for_header(str(h_path))
        new_blueprint = parser.parse_header(str(h_path), compiler_flags=flags)

        violations = BlueprintDiffEngine.diff_blueprints(old_blueprint, new_blueprint)
        reporter.report_violations(h, violations)

        if any(v.severity == "breaking" for v in violations):
            global_violations_found = True

    if global_violations_found:
        raise typer.Exit(code=1)

    reporter.print_success(
        "All public interface layout commitments verified perfectly."
    )


@app.command()
def update(
    header: str = typer.Argument(
        ..., help="Target header contract baseline to explicitly increment."
    )
):
    """Acknowledges incoming structural modifications, updating the active baseline snapshot."""
    reporter = TerminalReporter()
    vault = _get_vault_or_exit(reporter)

    h_path = Path(header).resolve()
    if not h_path.exists():
        reporter.print_error(
            f"Cannot refresh target contract. File missing from disk path location: {header}"
        )
        raise typer.Exit(code=2)

    parser = HeaderParser()
    cmd_reader = CompileCommandsReader()
    flags = cmd_reader.get_flags_for_header(str(h_path))

    try:
        new_blueprint = parser.parse_header(str(h_path), compiler_flags=flags)
        vault.save_blueprint(new_blueprint)
        reporter.print_success(
            f"Golden contract layout boundary incremented for: [cyan]{header}[/cyan]"
        )
    except Exception as e:
        reporter.print_error(f"Failed rewriting validation snapshot record block: {e}")
        raise typer.Exit(code=2)


@app.command(name="version")
def version_cmd():
    """Displays the active system build installation index details for Nirnaya."""
    typer.echo(f"Nirnaya Contract Engine — v{__version__}")


@app.command()
def show():
    """Launches the interactive TUI dashboard panel layout to monitor system assets."""
    reporter = TerminalReporter()
    try:
        from nirnaya.tui.app import ContractDashboard

        # Fire up the application context runner
        dashboard = ContractDashboard()
        dashboard.run()
    except Exception as e:
        reporter.print_error(f"Failed to launch terminal graphics layout engine: {e}")
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
