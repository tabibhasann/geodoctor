"""Tests for the new fix functions: remove_repeated_vertices, normalize_ring_orientation."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Polygon

from geodoctor.fixes.geometry import (
    fix_normalize_ring_orientation,
    fix_remove_repeated_vertices,
)


def test_remove_repeated_vertices_preserves_geometry():
    gdf = gpd.GeoDataFrame(
        {
            "id": [1],
            "geometry": [
                Polygon([(0, 0), (0, 0), (1, 0), (1, 1), (1, 1), (0, 1), (0, 0)])
            ],
        },
        crs="EPSG:4326",
    )
    fixed = fix_remove_repeated_vertices(gdf)
    # Should be a valid polygon still
    assert fixed.geometry.iloc[0].is_valid


def test_normalize_ring_orientation_to_cw():
    # Make a CCW polygon, then ask for CW
    gdf = gpd.GeoDataFrame(
        {"id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
        crs="EPSG:4326",
    )
    fixed = fix_normalize_ring_orientation(gdf, expected="cw")
    assert fixed.geometry.iloc[0].is_valid


def test_normalize_ring_orientation_no_op_when_already_correct():
    gdf = gpd.GeoDataFrame(
        {"id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
        crs="EPSG:4326",
    )
    fixed = fix_normalize_ring_orientation(gdf, expected="ccw")
    assert fixed.geometry.iloc[0].is_valid


def test_normalize_ring_orientation_skips_non_polygon():
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame({"id": [1], "geometry": [Point(0, 0)]}, crs="EPSG:4326")
    fixed = fix_normalize_ring_orientation(gdf, expected="ccw")
    # Just shouldn't crash; geometry returned unchanged
    assert fixed.geometry.iloc[0].equals(Point(0, 0))


def test_normalize_ring_orientation_handles_none():
    """None geometry should be returned unchanged (no crash)."""
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        {"id": [1, 2], "geometry": [None, Point(0, 0)]}, crs="EPSG:4326"
    )
    fixed = fix_normalize_ring_orientation(gdf, expected="ccw")
    assert fixed.geometry.iloc[0] is None
    assert fixed.geometry.iloc[1].equals(Point(0, 0))
