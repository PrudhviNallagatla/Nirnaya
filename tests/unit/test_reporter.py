"""Unit tests for the terminal reporter output formatting."""

from nirnaya.core.models import Violation
from nirnaya.output.reporter import TerminalReporter


def test_reporter_handles_empty_and_mixed_violations(capsys):
    reporter = TerminalReporter(use_color=False)

    reporter.report_violations("include/api.h", [])
    empty_output = capsys.readouterr().out
    assert "All contracts verified for:" in empty_output

    reporter.report_violations(
        "include/api.h",
        [
            Violation(
                severity="warning",
                category="enum_value",
                entity_name="Mode::C",
                description="New enum constant 'C' added.",
            ),
            Violation(
                severity="info",
                category="type_alias",
                entity_name="Alias",
                description="New type alias 'Alias' added.",
            ),
            Violation(
                severity="breaking",
                category="struct_layout",
                entity_name="Packet::id",
                description="Field member 'id' memory offset drifted.",
                old_value="bit 0",
                new_value="bit 16",
            ),
        ],
    )
    violation_output = capsys.readouterr().out

    assert "ABI CONTRACT VIOLATIONS DETECTED" in violation_output
    assert "WARNING" in violation_output
    assert "INFO" in violation_output
