"""CLI entry point — typer-powered command-line interface."""

from pathlib import Path

import typer

from . import (
    __version__,
    checks,  # noqa: F401  ensure all submodules register their @register_check
)
from .config import GeodoctorConfig, load_config
from .dataset import load_dataset
from .registry import CHECKS
from .renderers.console import render_console
from .renderers.console import render_html as _render_html
from .renderers.console import render_json as _render_json
from .report import Report

app = typer.Typer(
    name="geodoctor",
    help="The linter for geospatial data.",
    add_completion=False,
)


def _run_checks(dataset_path: str, config: GeodoctorConfig, layer: str | None = None) -> Report:
    """Run all registered checks against a dataset."""
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    report = Report()

    layers = list(load_dataset(dataset_path, layer=layer))
    active_rule_ids = [rid for rid in CHECKS if _is_rule_active(rid, config, CHECKS[rid]["severity"])]
    total_checks = len(layers) * len(active_rule_ids)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
    ) as progress:
        task = progress.add_task("Running checks...", total=total_checks or 1)

        for layer_name, gdf in layers:
            report.layers_checked += 1
            report.total_features += len(gdf)

            for rule_id in active_rule_ids:
                check_info = CHECKS[rule_id]
                default_sev = check_info["severity"]
                severity = config.effective_severity(rule_id, default_sev)
                try:
                    issues = check_info["fn"](gdf, config)
                    for issue in issues:
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
                finally:
                    progress.advance(task)

    return report


def _is_rule_active(rule_id: str, config: GeodoctorConfig, default_sev: str) -> bool:
    """Check if a rule is active based on config.

    Rules can be disabled via config settings:
    - Geometry rules: check geometry.allow_* flags
    - CRS rules: check crs.require flag
    - Topology rules: active for polygon layers
    - Schema/structure rules: always active (controlled by field presence)
    """
    # Geometry checks - respect allow_* flags
    if rule_id == "invalid_geometry":
        return not config.geometry.allow_invalid
    if rule_id == "empty_geometry":
        return not config.geometry.allow_empty
    if rule_id == "null_geometry":
        return not config.geometry.allow_empty
    if rule_id == "duplicate_geometry":
        return not config.geometry.allow_duplicates
    if rule_id == "mixed_geometry_types":
        return config.geometry.single_geometry_type
    if rule_id == "sliver_polygon":
        return config.geometry.min_area_m2 > 0
    if rule_id == "out_of_bounds":
        return config.crs.expected in (None, "EPSG:4326", "4326")

    # CRS checks - respect require flag
    if rule_id == "missing_crs":
        return config.crs.require

    # All other rules (schema, structure, topology) are active by default
    return True


@app.command()
def check(
    path: str = typer.Argument(..., help="Path to the dataset"),
    config_path: str = typer.Option(None, "--config", "-c", help="Path to geodoctor.yml"),
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
    display_report = report.promoted() if strict else report

    if format == "json":
        output_str = _render_json(display_report)
        if output:
            Path(output).write_text(output_str)
        else:
            typer.echo(output_str)
    elif format == "html":
        # render_html writes the file if output is set; otherwise return the string
        output_str = _render_html(display_report, output)
        if not output:
            typer.echo(output_str)
    else:
        output_str = render_console(display_report)
        if output:
            Path(output).write_text(output_str)
        else:
            typer.echo(output_str)

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

    for _layer_name, gdf in load_dataset(path):  # noqa: PERF102  (writes per-layer)
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
            spec: dict = {"type": _dtype_to_str(dtype), "nullable": nullable}
            unique_count = gdf[col].nunique()
            if unique_count == len(gdf) and not nullable:
                spec["unique"] = True
            config["schema"]["fields"][col] = spec  # type: ignore[index]

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
