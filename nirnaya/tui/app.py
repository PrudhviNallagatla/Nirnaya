# nirnaya/tui/app.py
"""Main Textual TUI application engine for Nirnaya.

Provides a navigable terminal user interface to explore contract health states,
review layout anomalies, and refresh baseline snapshots interactively.
"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static
from textual.screen import ModalScreen

from nirnaya.storage.git import GitWorkspace
from nirnaya.storage.vault import StorageVault
from nirnaya.core.parser import HeaderParser
from nirnaya.core.diff import BlueprintDiffEngine
from nirnaya.context.compile_commands import CompileCommandsReader

from nirnaya.tui.widgets.contract_list import ContractListView
from nirnaya.tui.widgets.violation_panel import ViolationDisplayPanel


class HelpModal(ModalScreen):
    """A floating pop-up window detailing the interactive key command layout matrix."""

    CSS = """
    HelpModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    
    #help_box {
        width: 50;
        height: auto;
        background: #1f242c;
        border: double #c9d1d9;
        padding: 1 2;
    }
    
    .help-title {
        color: #e6edf3;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    
    .help-row {
        margin-bottom: 1;
    }

    .help-divider {
        color: #9aa4b2;
        text-style: dim;
    }

    .help-footer {
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("NIRNAYA INTERACTIVE HELP", classes="help-title"),
            Static(
                "──────────────────────────────────────────", classes="help-divider"
            ),
            Static(
                "[bold cyan]Arrows / Tab[/bold cyan] : Navigate through the header list",
                classes="help-row",
            ),
            Static(
                "[bold cyan]Enter[/bold cyan]        : Select header file to view details",
                classes="help-row",
            ),
            Static(
                "[bold yellow]r[/bold yellow]            : Recheck workspace and look for layout changes",
                classes="help-row",
            ),
            Static(
                "[bold green]u[/bold green]            : Accept local modifications as new baseline",
                classes="help-row",
            ),
            Static(
                "[bold red]q[/bold red]            : Quit the dashboard session",
                classes="help-row",
            ),
            Static(
                "──────────────────────────────────────────", classes="help-divider"
            ),
            Static(
                "Press [bold magenta]esc[/bold magenta] or [bold magenta]h[/bold magenta] to dismiss this overlay panel.",
                classes="help-row help-footer",
            ),
            id="help_box",
        )

    def action_dismiss_help(self) -> None:
        """Closes the modal when hitting the escape sequence."""
        self.app.pop_screen()

    # Route key bindings inside the modal window context
    BINDINGS = [("escape", "dismiss_help", "Close"), ("h", "dismiss_help", "Close")]


class ContractDashboard(App):
    """An interactive terminal dashboard showing contract tracking health updates."""

    # Custom CSS settings to disable native command palette visual footers
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: #121212;
    }
    
    #workspace_container {
        layout: horizontal;
        height: 1fr;
        width: 100%;
    }
    
    #sidebar {
        width: 35;
        height: 100%;
        background: #1e1e1e;
        border-right: solid #2d3139;
    }
    
    #main_content {
        width: 1fr;
        height: 100%;
        background: #161616;
    }
    
    .header-title {
        background: #1f242c;
        color: #e6edf3;
        text-align: center;
        height: 3;
        content-align: center middle;
        text-style: bold;
        border-bottom: solid #2d3139;
    }
    
    #contract_list_sidebar {
        background: #1e1e1e;
        padding: 1;
    }
    """

    BINDINGS = [
        ("r", "recheck", "Recheck"),
        ("u", "update_current", "Update Baseline"),
        ("h", "show_help", "Help Menu"),
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initializes workspace target references and forces initial focal selection loops."""
        git_ctx = GitWorkspace()
        root = git_ctx.find_repo_root()

        if not root:
            self.exit(result="Fatal: Must be inside a valid Git repository workspace.")
            return

        self.vault = StorageVault(root)
        self.parser = HeaderParser()
        self.cmd_reader = CompileCommandsReader()

        self.action_recheck()

        # FIX: Select and focus the first element automatically so the screen never mounts blank
        sidebar = self.query_one("#contract_list_sidebar", ContractListView)
        sidebar.focus()
        if sidebar.children:
            sidebar.index = 0
            # Force trigger the view loading pipeline manually
            first_name = sidebar.children[0].name
            if first_name:
                self._update_details_pane(first_name)

    def compose(self) -> ComposeResult:
        """Constructs active visual frame layout zones using modular widgets."""
        yield Header(show_clock=True)

        yield Container(
            Vertical(
                Static("Tracked Headers", classes="header-title"),
                ContractListView(id="contract_list_sidebar"),
                id="sidebar",
            ),
            Vertical(
                Static("Layout Drift Diagnostics", classes="header-title"),
                ViolationDisplayPanel(id="violation_display_panel"),
                id="main_content",
            ),
            id="workspace_container",
        )

        yield Footer()

    def action_show_help(self) -> None:
        """Launches the user help floating guide cards layout screen overlay layer."""
        self.push_screen(HelpModal())

    def action_recheck(self) -> None:
        """Re-runs layout parser audit evaluations across tracked contracts in real-time."""
        sidebar = self.query_one("#contract_list_sidebar", ContractListView)
        tracked = self.vault.get_tracked_headers()

        records_payload: list[tuple[str, str]] = []

        for h in tracked:
            h_path = Path(h).resolve()
            if not h_path.exists():
                records_payload.append((h, "missing"))
                continue

            try:
                old_bp = self.vault.load_blueprint(h)
                flags = self.cmd_reader.get_flags_for_header(str(h_path))
                new_bp = self.parser.parse_header(str(h_path), compiler_flags=flags)
                violations = BlueprintDiffEngine.diff_blueprints(old_bp, new_bp)

                status = (
                    "fail"
                    if any(v.severity == "breaking" for v in violations)
                    else "pass"
                )
                records_payload.append((h, status))
            except Exception:
                records_payload.append((h, "error"))

        sidebar.populate_records(records_payload)

    def action_update_current(self) -> None:
        """Updates the active header snapshot baseline and instantly re-renders the panel data view."""
        sidebar = self.query_one("#contract_list_sidebar", ContractListView)
        selected_item = sidebar.highlighted_child

        if selected_item and selected_item.name:
            h = selected_item.name
            h_path = Path(h).resolve()

            if h_path.exists():
                flags = self.cmd_reader.get_flags_for_header(str(h_path))
                new_bp = self.parser.parse_header(str(h_path), compiler_flags=flags)
                self.vault.save_blueprint(new_bp)

                # FIX: Force immediate, live data cascade updates following the update command run
                self.action_recheck()
                self._update_details_pane(h)

    def on_list_view_selected(self, event: ContractListView.Selected) -> None:
        """Directs the selection lookup tracker when manually triggering elements via keys."""
        if event.item and event.item.name:
            self._update_details_pane(event.item.name)

    def _update_details_pane(self, selected_file: str) -> None:
        """Helper utility to sync the detailed violation records down into the card panel canvas."""
        display_panel = self.query_one(
            "#violation_display_panel", ViolationDisplayPanel
        )
        h_path = Path(selected_file).resolve()

        if not h_path.exists():
            return

        try:
            old_bp = self.vault.load_blueprint(selected_file)
            flags = self.cmd_reader.get_flags_for_header(str(h_path))
            new_bp = self.parser.parse_header(str(h_path), compiler_flags=flags)
            violations = BlueprintDiffEngine.diff_blueprints(old_bp, new_bp)

            display_panel.render_violations(selected_file, violations)
        except Exception as e:
            display_panel.mount(
                Static(f"[red]Error analyzing layout properties: {e}[/red]")
            )
