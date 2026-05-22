# nirnaya/tui/widgets/violation_panel.py
"""Interactive contract violation display widget.

Formats and presents layout deviations, type alterations, and recommended 
refactoring tips inside a structured, scrollable canvas view.
"""

from typing import List
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Container
from textual.widgets import Static

from nirnaya.core.models import Violation


class ViolationItem(Container):
    """An isolated card layout presenting a single detected contract violation."""

    def __init__(self, violation: Violation):
        super().__init__()
        self.violation = violation

    def compose(self) -> ComposeResult:
        """Draws the detailed fields for an individual layout violation card."""
        v = self.violation
        
        # Select matching status colors based on threat level
        sev_color = "red" if v.severity == "breaking" else "yellow"
        
        header_text = f"[{sev_color}][bold]{v.severity.upper()}[/bold][/{sev_color}] | [cyan]{v.category.upper()}[/cyan] | [white][bold]{v.entity_name}[/bold][/white]"
        yield Static(header_text, classes="violation-card-header")
        yield Static(f"[italic]{v.description}[/italic]", classes="violation-card-desc")
        
        # Render internal property states side-by-side if they drifted
        if v.old_value or v.new_value:
            drift_text = (
                f"  [red]Expected Profile Baseline :[/red] {v.old_value}\n"
                f"  [green]Incoming Code Modification :[/green] {v.new_value}"
            )
            yield Static(drift_text, classes="violation-card-drift")
            
        if v.suggested_fix:
            yield Static(f" 💡 [dim cyan]Suggested Fix: {v.suggested_fix}[/dim cyan]", classes="violation-card-fix")


class ViolationDisplayPanel(VerticalScroll):
    """A scrollable container presenting a list of structural layout violations."""

    CSS = """
    ViolationDisplayPanel {
        background: #1e1e1e;
        padding: 1;
    }
    
    ViolationItem {
        background: #282828;
        margin-bottom: 1;
        padding: 1;
        border-left: solid 4 red;
        height: auto;
    }
    
    .violation-card-header {
        margin-bottom: 1;
    }
    
    .violation-card-desc {
        color: #dcdcdc;
        margin-bottom: 1;
        padding-left: 2;
    }
    
    .violation-card-drift {
        background: #1a1a1a;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    .violation-card-fix {
        margin-top: 1;
        padding-left: 2;
    }
    
    .clean-contract-msg {
        color: #00ff00;
        text-align: center;
        margin-top: 5;
        bold: true;
    }
    """

    def render_violations(self, header_name: str, violations: List[Violation]) -> None:
        """Clears the previous panel content and draws the new violation list cards."""
        # Clean current sub-elements
        self.query("*").remove()
        
        if not violations:
            self.mount(Static(f"✓ Public interface contract intact for:\n[cyan]{header_name}[/cyan]", classes="clean-contract-msg"))
            return

        for violation in violations:
            self.mount(ViolationItem(violation))