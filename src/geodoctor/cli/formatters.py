"""Output formatting helpers for CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from ..renderers.console import render_ci as _render_ci
from ..renderers.console import render_console
from ..renderers.console import render_html as _render_html
from ..renderers.console import render_json as _render_json
from ..renderers.console import render_sarif as _render_sarif
from ..report import Report


def emit_report(
    report: Report,
    fmt: str,
    path: str,
    output: str | None,
) -> None:
    """Render and emit a report in the requested format."""
    if fmt == "json":
        text = _render_json(report)
    elif fmt == "html":
        text = _render_html(report, output)
    elif fmt == "github":
        lines = []
        for issue in report.issues:
            level = "error" if issue.severity == "error" else "warning"
            loc = f"file={path}"
            if issue.layer:
                loc += f",layer={issue.layer}"
            lines.append(f"::{level} {loc}::{issue.rule_id}: {issue.message}")
        text = "\n".join(lines) if lines else "::notice ::All checks passed"
    elif fmt == "sarif":
        text = _render_sarif(report, run_path=path)
    elif fmt == "ci":
        text = _render_ci(report)
    else:
        text = render_console(report)

    if output and fmt != "html":
        Path(output).write_text(text)
    elif not output:
        typer.echo(text)
