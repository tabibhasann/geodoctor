"""CLI entry point — typer-powered command-line interface."""

from __future__ import annotations

from pathlib import Path

import typer

from .. import (
    __version__,
    checks,  # noqa: F401  ensure all submodules register their @register_check
)
from ..config import load_config
from .commands import run_init, run_rules
from .engine import run_checks
from .fixes_cmd import run_fix
from .formatters import emit_report

app = typer.Typer(
    name="geodoctor",
    help="The linter for geospatial data.",
    add_completion=False,
)


@app.command()
def check(
    path: str = typer.Argument(..., help="Path to the dataset"),
    config_path: str = typer.Option(None, "--config", "-c", help="Path to geodoctor.yml"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json, html, github, sarif, ci"),
    layer: str = typer.Option(None, "--layer", "-l", help="Layer name to check"),
    strict: bool = typer.Option(False, "--strict", help="Promote warnings to errors"),
    ci: bool = typer.Option(False, "--ci", help="CI mode: compact output, exit 1 on errors, 0 on warnings only"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Check a geospatial dataset for issues."""
    config = load_config(config_path)

    if not Path(path).exists():
        typer.echo(f"Error: file not found: {path}", err=True)
        raise typer.Exit(2)

    report = run_checks(path, config, layer)
    display_report = report.promoted() if strict else report

    fmt = "ci" if ci else format
    emit_report(display_report, fmt, path, output)

    if display_report.has_errors:
        raise typer.Exit(1)
    raise typer.Exit(0)


@app.command()
def fix(
    path: str = typer.Argument(..., help="Path to the dataset"),
    output_path: str = typer.Option(..., "--output", "-o", help="Output file path"),
    config_path: str = typer.Option(None, "--config", "-c", help="Path to geodoctor.yml"),
    fixes: str = typer.Option(
        "make_valid,drop_empty_null",
        "--fixes",
        help="Comma-separated list of fix IDs to apply",
    ),
):
    """Apply auto-fixes to a dataset."""
    run_fix(path, output_path, config_path, fixes)


@app.command()
def init(
    path: str = typer.Argument(..., help="Path to a dataset to analyze"),
    output: str = typer.Option("geodoctor.yml", "--output", "-o", help="Output config path"),
):
    """Generate a starter geodoctor.yml from a dataset."""
    run_init(path, output)


@app.command()
def rules(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all available checks."""
    run_rules(json_output)


@app.command()
def diff(
    path_a: str = typer.Argument(..., help="Path to the first dataset"),
    path_b: str = typer.Argument(..., help="Path to the second dataset"),
    config_path: str = typer.Option(None, "--config", "-c", help="Path to geodoctor.yml"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json"),
    layer: str = typer.Option(None, "--layer", "-l", help="Layer name to compare"),
):
    """Compare two datasets by running checks on both and showing the difference."""
    config = load_config(config_path)

    for p in (path_a, path_b):
        if not Path(p).exists():
            typer.echo(f"Error: file not found: {p}", err=True)
            raise typer.Exit(2)

    report_a = run_checks(path_a, config, layer)
    report_b = run_checks(path_b, config, layer)

    issues_a = {i.rule_id for i in report_a.issues}
    issues_b = {i.rule_id for i in report_b.issues}

    fixed = issues_a - issues_b
    introduced = issues_b - issues_a
    persisted = issues_a & issues_b

    if format == "json":
        import json as _json

        output = {
            "dataset_a": path_a,
            "dataset_b": path_b,
            "summary": {
                "issues_in_a": len(report_a.issues),
                "issues_in_b": len(report_b.issues),
                "fixed": sorted(fixed),
                "introduced": sorted(introduced),
                "persisted": sorted(persisted),
            },
        }
        typer.echo(_json.dumps(output, indent=2))
    else:
        typer.echo(f"Comparing: {path_a} -> {path_b}\n")
        typer.echo(f"  Issues in A:  {len(report_a.issues)}")
        typer.echo(f"  Issues in B:  {len(report_b.issues)}")
        typer.echo(f"  Fixed:        {len(fixed)}  {sorted(fixed) if fixed else ''}")
        typer.echo(f"  Introduced:   {len(introduced)}  {sorted(introduced) if introduced else ''}")
        typer.echo(f"  Persisted:    {len(persisted)}  {sorted(persisted) if persisted else ''}")

    if introduced:
        raise typer.Exit(1)
    raise typer.Exit(0)


@app.command()
def version():
    """Show version."""
    typer.echo(f"geodoctor {__version__}")


if __name__ == "__main__":
    app()
