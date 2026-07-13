"""Console, JSON, and HTML renderers for reports."""

import json
from io import StringIO
from pathlib import Path

from ..report import Report


def render_console(report: Report) -> str:
    """Render a report to a rich console table."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console(record=True, file=StringIO())
    total = len(report.issues)

    if total == 0:
        console.print(Panel("[green bold]✓ All checks passed![/]", title="geodoctor"))
        text = console.export_text()
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


def render_sarif(report: Report, run_path: str = "") -> str:
    """Render a report as SARIF 2.1.0 JSON for security tooling integration."""
    sarif_level = {"error": "error", "warning": "warning", "info": "note"}

    results = []
    for issue in report.issues:
        results.append({
            "ruleId": issue.rule_id,
            "level": sarif_level.get(issue.severity, "warning"),
            "message": {"text": issue.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": run_path,
                        },
                        "region": {
                            "startLine": 1,
                        },
                    },
                    "logicalLocations": [
                        {
                            "name": issue.layer,
                            "kind": "layer",
                        },
                    ] if issue.layer else [],
                }
            ],
            "partialFingerprints": {
                "primaryLocationLineHash": issue.rule_id,
            },
        })

    sarif = {
        "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/cs01/schemas/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "geodoctor",
                        "informationUri": "https://github.com/tabibhasann/geodoctor",
                        "rules": [
                            {
                                "id": rule_id,
                                "name": rule_id,
                                "shortDescription": {"text": info.get("description", "")},
                                "defaultConfiguration": {
                                    "level": sarif_level.get(info.get("severity", "warning"), "warning"),
                                },
                            }
                            for rule_id, info in _get_all_rules().items()
                        ],
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(sarif, indent=2)


def _get_all_rules() -> dict:
    """Get all registered rules (lazy import to avoid circular deps)."""
    from ..registry import CHECKS

    return {rid: {"description": info["description"], "severity": info["severity"]} for rid, info in CHECKS.items()}


def render_ci(report: Report) -> str:
    """Render a compact CI-friendly summary (one line per issue, no colors)."""
    lines = []
    total = len(report.issues)
    if total == 0:
        return "geodoctor: 0 issues found. All checks passed."

    errors = len(report.errors)
    warnings = len(report.warnings)
    infos = len(report.infos)
    lines.append(f"geodoctor: {total} issue(s) — {errors} error(s), {warnings} warning(s), {infos} info(s)")
    for issue in report.issues:
        loc = f"[{issue.layer}]" if issue.layer else ""
        affected = f" ({len(issue.feature_ids)} affected)" if issue.feature_ids else ""
        lines.append(f"  {issue.severity.upper():7s} {issue.rule_id:30s} {loc} {issue.message}{affected}")
    return "\n".join(lines)
