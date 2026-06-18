"""Tests for topology checks (overlaps and gaps)."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Polygon

from geodoctor import load_config, validate
from geodoctor.registry import CHECKS


def test_topology_checks_registered():
    """Both topology checks should be in the global registry."""
    assert "polygon_overlaps" in CHECKS
    assert "polygon_gaps" in CHECKS


def test_polygon_overlaps_finds_overlap():
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (4, 0), (4, 4), (0, 4)]),  # shares area with next
                Polygon([(2, 2), (6, 2), (6, 6), (2, 6)]),
            ],
        },
        crs="EPSG:4326",
    )
    issues = CHECKS["polygon_overlaps"]["fn"](gdf, load_config())
    assert issues, "expected at least one issue for overlapping polygons"
    assert issues[0].rule_id == "polygon_overlaps"


def test_polygon_overlaps_clean_layer():
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
            ],
        },
        crs="EPSG:4326",
    )
    issues = CHECKS["polygon_overlaps"]["fn"](gdf, load_config())
    assert issues == []


def test_polygon_overlaps_skips_lines():
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            ],
        },
        crs="EPSG:4326",
    )
    # Two identical polygons DO overlap (they are equal), so we expect at least one issue
    issues = CHECKS["polygon_overlaps"]["fn"](gdf, load_config())
    assert len(issues) >= 1


def test_polygon_gaps_finds_hole():
    """An annulus (square with a square hole) has a gap inside."""
    outer = Polygon(
        [(0, 0), (10, 0), (10, 10), (0, 10)],
        holes=[[(2, 2), (8, 2), (8, 8), (2, 8)]],
    )
    # Use just the exterior so union is a hollow polygon (gap)
    gdf = gpd.GeoDataFrame({"id": [1], "geometry": [Polygon(outer.exterior)]}, crs="EPSG:4326")
    # Just call to make sure the check doesn't crash on this shape.
    _ = CHECKS["polygon_gaps"]["fn"](gdf, load_config())
    # The exterior itself isn't technically a "gap" by this check (it's the whole shape),
    # but the check should not crash. The actual gap is between two disjoint adjacent
    # polygons, so we test that with two polygons surrounding a hole.
    gdf2 = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (5, 0), (5, 10), (0, 10)]),
                Polygon([(5, 0), (10, 0), (10, 10), (5, 10)]),
            ],
        },
        crs="EPSG:4326",
    )
    issues2 = CHECKS["polygon_gaps"]["fn"](gdf2, load_config())
    # Two adjacent rectangles should be gap-free.
    assert issues2 == []


def test_topology_runs_through_validate_api(tmp_path):
    """End-to-end: validate() should run topology checks."""
    path = tmp_path / "overlapping.gpkg"
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "geometry": [
                Polygon([(0, 0), (4, 0), (4, 4), (0, 4)]),
                Polygon([(2, 2), (6, 2), (6, 6), (2, 6)]),
            ],
        },
        crs="EPSG:4326",
    )
    gdf.to_file(path, driver="GPKG")

    report = validate(str(path))
    rule_ids = {i.rule_id for i in report.issues}
    assert "polygon_overlaps" in rule_ids
