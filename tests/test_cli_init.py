"""Tests for the `init` CLI command and HTML/JSON CLI output paths."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point
from typer.testing import CliRunner

from geodoctor.cli import app

runner = CliRunner()


def test_init_creates_config(tmp_path):
    data_path = tmp_path / "pts.geojson"
    out_path = tmp_path / "geodoctor.yml"
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "name": ["a", "b"]},
        geometry=[Point(0, 0), Point(1, 1)],
        crs="EPSG:4326",
    )
    gdf.to_file(data_path, driver="GeoJSON")

    result = runner.invoke(app, ["init", str(data_path), "--output", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()
    content = out_path.read_text()
    assert "EPSG:4326" in content
    assert "id" in content
    assert "name" in content


def test_check_with_json_format(tmp_path):
    data_path = tmp_path / "pts.geojson"
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326"
    )
    gdf.to_file(data_path, driver="GeoJSON")

    result = runner.invoke(app, ["check", str(data_path), "--format", "json"])
    assert result.exit_code == 0
    assert '"summary"' in result.stdout
    assert '"total_issues"' in result.stdout


def test_check_with_html_format(tmp_path):
    data_path = tmp_path / "pts.geojson"
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326"
    )
    gdf.to_file(data_path, driver="GeoJSON")

    result = runner.invoke(app, ["check", str(data_path), "--format", "html"])
    assert result.exit_code == 0
    assert "<!DOCTYPE html>" in result.stdout


def test_check_with_html_format_writes_file(tmp_path):
    data_path = tmp_path / "pts.geojson"
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326"
    )
    gdf.to_file(data_path, driver="GeoJSON")
    out_path = tmp_path / "report.html"

    result = runner.invoke(app, ["check", str(data_path), "--format", "html", "--output", str(out_path)])
    assert result.exit_code == 0
    assert out_path.exists()
    assert "<!DOCTYPE html>" in out_path.read_text()


def test_check_with_strict_promotes_warnings(tmp_path):
    """A clean dataset should pass; with --strict, no warnings means still clean."""
    data_path = tmp_path / "pts.geojson"
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326"
    )
    gdf.to_file(data_path, driver="GeoJSON")

    result = runner.invoke(app, ["check", str(data_path), "--strict"])
    assert result.exit_code == 0


def test_fix_command_end_to_end(tmp_path):
    """End-to-end test of the fix command."""
    from shapely.geometry import Polygon

    data_path = tmp_path / "dupes.geojson"
    out_path = tmp_path / "deduped.geojson"
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2, 3], "geometry": [poly, poly, poly]}, crs="EPSG:4326"
    )
    gdf.to_file(data_path, driver="GeoJSON")

    result = runner.invoke(
        app, ["fix", str(data_path), "--output", str(out_path), "--fixes", "dedupe_geometry"]
    )
    assert result.exit_code == 0
    assert out_path.exists()
    assert "dedupe_geometry" in result.stdout

    # Verify the result has 1 row
    gdf_out = gpd.read_file(out_path)
    assert len(gdf_out) == 1
