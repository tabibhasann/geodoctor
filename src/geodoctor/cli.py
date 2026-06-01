"""CLI entry point — typer-powered command-line interface."""

import sys
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .checks import crs, geometry, schema, structure
from .config import GeodoctorConfig, load_config
from .dataset import load_dataset
from .registry import CHECKS
from .report import Report
from .renderers.console import render_console
from .renderers.console import render_json as _render_json
from .renderers.console import render_html as _render_html

app = typer.Typer(
    name="geodoctor",
    help="The linter for geospatial data.",
    add_completion=False,
)


def _run_checks(dataset_path: str, config: GeodoctorConfig, layer: str | None = None) -> Report:
    """Run all registered checks against a dataset."""
    report = Report()

    for layer_name, gdf in load_dataset(dataset_path, layer=layer):
        report.layers_checked += 1
        report.total_features += len(gdf)

        for rule_id, check_info in CHECKS.items():
            default_sev = check_info["severity"]
            severity = config.effective_severity(rule_id, default_sev)
            try:
                issues = check_info["fn"](gdf, config)
                for issue in issues:
                    # Check if this rule is allowed based on config
                    if _is_rule_active(rule_id, config, default_sev):
                        issue.severity = severity
                        issue.layer = layer_name
                        report.issues.append(issue)
            except Exception as e:
                from .report import Issue
                report.issues.append(
                    Issue(
                        rule_id=rule_id,
                        severity=severity,
                        message=f"Check failed: {e}",
                        layer=layer_name,
                    )
                )

    return report


def _is_rule_active(rule_id: str, config: GeodoctorConfig, default_sev: str) -> bool:
    """Check if a rule is active based on config."""
    # If severity is overridden to a non-error/non-warning, it may still be active
    return True  # All checks run by default; config controls severity


@app.command()
def check(
    path: str = typer.Argument(..., help="Path to the dataset"),
    config_path: str = typer.Option(
        None, "--config", "-c", help="Path to geodoctor.yml"
    ),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json, html"),
    layer: str = typer.Option(None, "--layer", "-l", help="Layer name to check"),
    strict: bool = typer.Option(False, "--strict", help="Promote warnings to errors"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Check a geospatial dataset for issues."""
    config = load_config(config_path)

    if not Path(path).exists():
        typer.echo(f"Error: file not found: {path}", err=True)
        raise typer.Exit(2)

    report = _run_checks(path, config, layer)

    if strict:
        from .report import Issue
        report.issues = report.promoted_errors()

    if format == "json":
        output_str = _render_json(report)
    elif format == "html":
        output_str = _render_html(report, output)
    else:
        output_str = render_console(report)

    if output and format != "html":
        Path(output).write_text(output_str)
    elif format != "html":
        typer.echo(output_str)

    if report.has_errors or (strict and report.issues):
        raise typer.Exit(1)
    raise typer.Exit(0)


@app.command()
def fix(
    path: str = typer.Argument(..., help="Path to the dataset"),
    output_path: str = typer.Option(..., "--output", "-o", help="Output file path"),
    config_path: str = typer.Option(
        None, "--config", "-c", help="Path to geodoctor.yml"
    ),
    fixes: str = typer.Option(
        "make_valid,drop_empty_null",
        "--fixes",
        help="Comma-separated list of fix IDs to apply",
    ),
):
    """Apply auto-fixes to a dataset."""
    from .fixes.geometry import FIX_MAP, fix_reproject

    config = load_config(config_path)

    if not Path(path).exists():
        typer.echo(f"Error: file not found: {path}", err=True)
        raise typer.Exit(2)

    fix_list = [f.strip() for f in fixes.split(",")]

    changes = []
    for layer_name, gdf in load_dataset(path):
        for fix_id in fix_list:
            if fix_id == "reproject":
                if config.crs.expected:
                    gdf = fix_reproject(gdf, config.crs.expected)
                    changes.append(f"Reprojected {layer_name} to {config.crs.expected}")
                continue
            fn = FIX_MAP.get(fix_id)
            if fn:
                old_len = len(gdf)
                gdf = fn(gdf)
                changes.append(f"Applied {fix_id} to {layer_name} ({old_len} → {len(gdf)} features)")

        ext = Path(output_path).suffix.lower()
        driver_map = {
            ".gpkg": "GPKG",
            ".geojson": "GeoJSON",
            ".json": "GeoJSON",
            ".shp": "ESRI Shapefile",
            ".fgb": "FlatGeobuf",
        }
        driver = driver_map.get(ext)

        if driver == "ESRI Shapefile" and ext == ".shp":
            # geopandas handles Shapefile via the directory approach
            gdf.to_file(output_path)
        else:
            gdf.to_file(output_path, driver=driver)

    typer.echo("Fixes applied:")
    for c in changes:
        typer.echo(f"  • {c}")
    typer.echo(f"\nOutput written to: {output_path}")


@app.command()
def init(
    path: str = typer.Argument(..., help="Path to a dataset to analyze"),
    output: str = typer.Option("geodoctor.yml", "--output", "-o", help="Output config path"),
):
    """Generate a starter geodoctor.yml from a dataset."""
    import yaml

    for layer_name, gdf in load_dataset(path):
        config = {
            "crs": {
                "expected": gdf.crs.to_string() if gdf.crs else None,
                "require": True,
            },
            "geometry": {
                "allow_invalid": False,
                "allow_empty": False,
                "allow_duplicates": False,
                "single_geometry_type": False,
            },
            "schema": {
                "fields": {},
            },
        }

        for col in gdf.columns:
            if col == "geometry":
                continue
            dtype = str(gdf[col].dtype)
            nullable = bool(gdf[col].isna().any())
            spec = {"type": _dtype_to_str(dtype), "nullable": nullable}
            unique_count = gdf[col].nunique()
            if unique_count == len(gdf) and not nullable:
                spec["unique"] = True
            config["schema"]["fields"][col] = spec

        yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
        Path(output).write_text(yaml_str)
        typer.echo(f"Generated config: {output}")
        return

    typer.echo("No layers found in dataset.", err=True)


def _dtype_to_str(dtype: str) -> str:
    if "int" in dtype:
        return "int"
    elif "float" in dtype:
        return "float"
    elif "bool" in dtype:
        return "bool"
    return "str"


@app.command()
def rules():
    """List all available checks."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Available Checks")
    table.add_column("Rule ID", style="cyan")
    table.add_column("Severity")
    table.add_column("Description")
    table.add_column("Fix", justify="center")

    for rule_id, info in CHECKS.items():
        table.add_row(
            rule_id,
            info["severity"],
            info["description"],
            "✓" if info.get("fix_id") else "",
        )

    console.print(table)


@app.command()
def version():
    """Show version."""
    typer.echo(f"geodoctor {__version__}")


if __name__ == "__main__":
    app()
