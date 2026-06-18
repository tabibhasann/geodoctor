"""Tests for the public programmatic API (engine + __init__)."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Point

from geodoctor import Issue, Report, load_config, validate
from geodoctor.engine import validate as engine_validate


def test_public_api_imports():
    """All public names from geodoctor should be importable."""
    assert callable(validate)
    assert callable(load_config)
    assert Report is not None
    assert Issue is not None


def test_validate_returns_report(tmp_path):
    path = tmp_path / "points.gpkg"
    gdf = gpd.GeoDataFrame({"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326")
    gdf.to_file(path, driver="GPKG")
    report = validate(str(path))
    assert isinstance(report, Report)
    assert report.layers_checked == 1
    assert report.total_features == 2


def test_validate_missing_file(tmp_path):
    report = validate(str(tmp_path / "nope.gpkg"))
    assert report.has_errors
    assert any("not found" in i.message for i in report.issues)


def test_validate_rule_ids_subset(tmp_path):
    path = tmp_path / "points.gpkg"
    gdf = gpd.GeoDataFrame({"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326")
    gdf.to_file(path, driver="GPKG")
    report = engine_validate(str(path), rule_ids=["missing_crs"])
    assert all(i.rule_id == "missing_crs" for i in report.issues)


def test_validate_with_custom_config(tmp_path):
    path = tmp_path / "points.gpkg"
    gdf = gpd.GeoDataFrame({"id": [1, 2], "geometry": [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326")
    gdf.to_file(path, driver="GPKG")
    cfg = load_config()
    cfg.crs.require = False
    report = engine_validate(str(path), config=cfg)
    rule_ids = {i.rule_id for i in report.issues}
    assert "missing_crs" not in rule_ids
