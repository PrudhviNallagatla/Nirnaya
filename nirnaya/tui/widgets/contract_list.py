# nirnaya/tui/widgets/contract_list.py
"""Interactive contract tracking ledger sidebar.

Provides a structured file registry sidebar with real-time status highlights 
and visual warning badges for tracked C++ headers.
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Static


class ContractItem(ListItem):
    """An individual row entry representing a tracked contract's validation status."""

    def __init__(self, header_path: str, status: str):
        # Store the tracking handle as the node identifier
        super().__init__(name=header_path)
        self.header_path = header_path
        self.status = status

    def compose(self) -> ComposeResult:
        """Appends color-coded status badges next to the header file name."""
        short_name = Path(self.header_path).name
        
        if self.status == "pass":
            badge = "[bold green]✓ PASS[/bold green]"
        elif self.status == "fail":
            badge = "[bold red]✗ FAIL[/bold red]"
        elif self.status == "missing":
            badge = "[bold red]! NONE[/bold red]"
        else:
            badge = "[bold yellow]! ERRR[/bold yellow]"

        yield Static(f"{badge}  {short_name}")


class ContractListView(ListView):
    """A managed list view container displaying all registered interface headers."""

    def populate_records(self, tracked_items: list[tuple[str, str]]) -> None:
        """Clears old listings and redraws the sidebar with updated statuses."""
        self.clear()
        for path, status in tracked_items:
            self.append(ContractItem(path, status))