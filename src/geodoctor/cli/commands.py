"""Init and rules command implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from ..dataset import load_dataset
from ..registry import CHECKS


def run_init(path: str, output: str) -> None:
    """Generate a starter geodoctor.yml from a dataset."""
    import yaml

    for _layer_name, gdf in load_dataset(path):
        config: dict[str, Any] = {
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


def run_rules(json_output: bool) -> None:
    """List all available checks."""
    if json_output:
        import json as _json

        rules_list = []
        for rule_id, info in CHECKS.items():
            rules_list.append({
                "rule_id": rule_id,
                "severity": info["severity"],
                "description": info["description"],
                "fix_available": bool(info.get("fix_id")),
                "fix_id": info.get("fix_id"),
            })
        typer.echo(_json.dumps({"rules": rules_list, "total": len(rules_list)}, indent=2))
        return

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
