"""Console, JSON, and HTML renderers for reports."""

import json
from pathlib import Path

from ..report import Report, Issue


def render_console(report: Report) -> str:
    """Render a report to a rich console table."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    console = Console(record=True)
    total = len(report.issues)

    if total == 0:
        console.print(Panel("[green bold]✓ All checks passed![/]", title="geodoctor"))
        return console.export_text()

    sev_colors = {"error": "red", "warning": "yellow", "info": "blue"}
    errors = len(report.errors)
    warnings = len(report.warnings)
    infos = len(report.infos)

    summary = Text()
    summary.append(f"{total} issue(s) found: ", style="bold")
    if errors:
        summary.append(f"{errors} error(s)  ", style="red")
    if warnings:
        summary.append(f"{warnings} warning(s)  ", style="yellow")
    if infos:
        summary.append(f"{infos} info(s)", style="blue")

    console.print(Panel(summary, title="geodoctor"))

    table = Table(title="Issues")
    table.add_column("Rule", style="cyan", no_wrap=True)
    table.add_column("Severity")
    table.add_column("Message")
    table.add_column("Affected", justify="right")
    table.add_column("Fix", justify="center")

    for issue in report.issues:
        color = sev_colors.get(issue.severity, "white")
        table.add_row(
            issue.rule_id,
            f"[{color}]{issue.severity}[/]",
            issue.message,
            str(len(issue.feature_ids)) if issue.feature_ids else "N/A",
            "✓" if issue.fix_available else "",
        )

    console.print(table)
    return console.export_text()


def render_json(report: Report) -> str:
    """Render a report as JSON."""
    return json.dumps(
        {
            "summary": {
                "total_issues": len(report.issues),
                "errors": len(report.errors),
                "warnings": len(report.warnings),
                "infos": len(report.infos),
            },
            "issues": [i.to_dict() for i in report.issues],
        },
        indent=2,
    )


def render_html(report: Report, output_path: str | None = None) -> str:
    """Render a report as HTML using Jinja2."""
    from jinja2 import Template

    template = Template(_HTML_TEMPLATE)
    html = template.render(
        report=report,
        errors=report.errors,
        warnings=report.warnings,
        infos=report.infos,
    )
    if output_path:
        Path(output_path).write_text(html)
    return html


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>geodoctor Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
        .summary span { margin-right: 1.5rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f0f0f0; }
        .error { color: #d32f2f; font-weight: bold; }
        .warning { color: #f57c00; font-weight: bold; }
        .info { color: #1976d2; }
        .fix { color: #388e3c; }
    </style>
</head>
<body>
    <h1>geodoctor Report</h1>
    <div class="summary">
        <span class="error">{{ report.errors|length }} error(s)</span>
        <span class="warning">{{ report.warnings|length }} warning(s)</span>
        <span class="info">{{ report.infos|length }} info(s)</span>
    </div>
    <table>
        <tr><th>Rule</th><th>Severity</th><th>Message</th><th>Affected</th><th>Fix Available</th></tr>
        {% for issue in report.issues %}
        <tr>
            <td>{{ issue.rule_id }}</td>
            <td class="{{ issue.severity }}">{{ issue.severity }}</td>
            <td>{{ issue.message }}</td>
            <td>{{ issue.feature_ids|length }}</td>
            <td class="fix">{% if issue.fix_available %}✓{% endif %}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>"""
