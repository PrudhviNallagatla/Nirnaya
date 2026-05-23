# nirnaya/output/reporter.py
"""Rich-based terminal reporter for Nirnaya layout verification audits.

Renders clear, beautiful visual alerts for contract states, severe
ABI violations, and suggested structural code mitigations.
"""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from nirnaya.core.models import Violation


class TerminalReporter:
    """Encapsulates formatting structures to render clean terminal diagnostics."""

    def __init__(self, use_color: bool = True):
        self.console = Console(color_system="auto" if use_color else None)

    def print_success(self, message: str) -> None:
        """Prints a clean, green validation success confirmation check line."""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def print_warning(self, message: str) -> None:
        """Prints an orange warning message banner block."""
        self.console.print(f"[bold yellow]![/bold yellow] {message}")

    def print_error(self, message: str) -> None:
        """Prints a red error warning marker."""
        self.console.print(f"[bold red]✗[/bold red] {message}")

    def report_violations(self, header_path: str, violations: List[Violation]) -> None:
        """Formats and presents detected layout drift anomalies as clear, scannable data."""
        if not violations:
            self.print_success(
                f"All contracts verified for: [cyan]{header_path}[/cyan]"
            )
            return

        self.console.print("\n" + "─" * 80)
        self.console.print("[bold red]ABI CONTRACT VIOLATIONS DETECTED[/bold red]")
        self.console.print(f"Target Header: [cyan]{header_path}[/cyan]\n")

        table = Table(box=None, padding=(0, 2, 1, 0), show_header=True)
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Category", style="dim", width=20)
        table.add_column("Details")

        for v in violations:
            # Color severity tokens dynamically
            if v.severity == "breaking":
                sev_text = Text("BREAKING", style="red")
            elif v.severity == "warning":
                sev_text = Text("WARNING", style="yellow")
            else:
                sev_text = Text("INFO", style="blue")

            # Format primary structural analysis breakdown
            details_text = Text()
            details_text.append(f"Entity: {v.entity_name}\n", style="bold white")
            details_text.append(f"{v.description}\n", style="italic")

            if v.old_value or v.new_value:
                details_text.append("  └─ Baseline State: ", style="dim")
                details_text.append(f"{v.old_value}\n", style="red")
                details_text.append("  └─ Modified State: ", style="dim")
                details_text.append(f"{v.new_value}\n", style="green")

            if v.suggested_fix:
                details_text.append(
                    f"  💡 Suggested Fix: {v.suggested_fix}", style="cyan"
                )

            table.add_row(sev_text, v.category, details_text)

        self.console.print(table)

        breaking_count = sum(1 for v in violations if v.severity == "breaking")
        self.console.print(
            Panel(
                f"[bold red]Audit Status: FAILED[/bold red]\n"
                f"Discovered [bold]{len(violations)}[/bold] total anomalies. "
                f"([bold red]{breaking_count} breaking layout shifts[/bold red])",
                border_style="red",
                expand=False,
            )
        )
        self.console.print("─" * 80 + "\n")
