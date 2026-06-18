"""Console, JSON, and HTML renderers for reports."""

import json
from pathlib import Path

from ..report import Report


def render_console(report: Report) -> str:
    """Render a report to a rich console table."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console(record=True, file=open("/dev/null", "w"))
    total = len(report.issues)

    if total == 0:
        console.print(Panel("[green bold]✓ All checks passed![/]", title="geodoctor"))
        text = console.export_text()
        console.file.close()
        return text

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
    text = console.export_text()
    console.file.close()
    return text


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
    from jinja2 import Environment, FileSystemLoader

    # Load template from templates directory
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")

    html = template.render(
        report=report,
        errors=report.errors,
        warnings=report.warnings,
        infos=report.infos,
    )

    if output_path:
        Path(output_path).write_text(html)

    return html
