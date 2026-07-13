"""Fix command implementation — applies auto-fixes to a dataset."""

from __future__ import annotations

from pathlib import Path

import typer

from ..config import load_config
from ..dataset import load_dataset
from ..fixes.geometry import FIX_MAP, fix_reproject


def run_fix(
    path: str,
    output_path: str,
    config_path: str | None,
    fixes: str,
) -> None:
    """Apply auto-fixes to a dataset."""
    config = load_config(config_path)

    if not Path(path).exists():
        typer.echo(f"Error: file not found: {path}", err=True)
        raise typer.Exit(2)

    fix_list = [f.strip() for f in fixes.split(",")]

    layers = load_dataset(path)
    ext = Path(output_path).suffix.lower()
    driver_map = {
        ".gpkg": "GPKG",
        ".geojson": "GeoJSON",
        ".json": "GeoJSON",
        ".shp": "ESRI Shapefile",
        ".fgb": "FlatGeobuf",
    }
    driver = driver_map.get(ext)

    if len(layers) > 1 and driver != "GPKG":
        typer.echo(
            "Error: multi-layer inputs require a GeoPackage output "
            "so each fixed layer can be preserved.",
            err=True,
        )
        raise typer.Exit(2)

    changes: list[str] = []
    for layer_name, gdf in layers:
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
                changes.append(
                    f"Applied {fix_id} to {layer_name} ({old_len} → {len(gdf)} features)"
                )

        if driver == "ESRI Shapefile" and ext == ".shp":
            gdf.to_file(output_path)
        elif driver == "GPKG":
            gdf.to_file(output_path, driver=driver, layer=layer_name)
        else:
            gdf.to_file(output_path, driver=driver)

    typer.echo("Fixes applied:")
    for c in changes:
        typer.echo(f"  • {c}")
    typer.echo(f"\nOutput written to: {output_path}")
