"""Round-trip tests: `geodoctor fix` should produce a dataset that passes `check`."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import Polygon

from geodoctor import validate
from geodoctor.fixes.geometry import (
    fix_dedupe_geometry,
    fix_drop_empty_null,
    fix_make_valid,
    fix_strip_whitespace,
)


def test_make_valid_repairs_invalid_polygon():
    # A bowtie is a self-intersecting polygon
    gdf = gpd.GeoDataFrame(
        {"id": [1], "geometry": [Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])]},
        crs="EPSG:4326",
    )
    assert not gdf.geometry.iloc[0].is_valid
    fixed = fix_make_valid(gdf)
    assert fixed.geometry.iloc[0].is_valid


def test_drop_empty_null():
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2, 3],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                None,
                Polygon(),
            ],
        },
        crs="EPSG:4326",
    )
    fixed = fix_drop_empty_null(gdf)
    assert len(fixed) == 1
    assert fixed.iloc[0]["id"] == 1


def test_dedupe_geometry():
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    gdf = gpd.GeoDataFrame({"id": [1, 2, 3], "geometry": [poly, poly, poly]}, crs="EPSG:4326")
    fixed = fix_dedupe_geometry(gdf)
    assert len(fixed) == 1


def test_strip_whitespace():
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2],
            "name": ["  Alice  ", "Bob "],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
            ],
        },
        crs="EPSG:4326",
    )
    fixed = fix_strip_whitespace(gdf)
    assert fixed["name"].iloc[0] == "Alice"
    assert fixed["name"].iloc[1] == "Bob"


def test_validate_then_fix_round_trip(tmp_path):
    """Take a dataset with issues, apply fixes, then re-validate."""
    path_in = tmp_path / "broken.gpkg"
    path_out = tmp_path / "clean.gpkg"

    # Two identical invalid-ish polygons + a row with whitespace
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2, 3],
            "name": ["  alpha  ", "beta", "gamma"],
            "geometry": [poly, poly, poly],
        },
        crs="EPSG:4326",
    )
    gdf.to_file(path_in, driver="GPKG")

    # Validate original
    before = validate(str(path_in))
    before_rule_ids = {i.rule_id for i in before.issues}
    # Should find duplicate_geometry + whitespace
    assert "duplicate_geometry" in before_rule_ids

    # Apply fixes by chaining helpers
    gdf_fixed = gpd.read_file(path_in)
    gdf_fixed = fix_dedupe_geometry(gdf_fixed)
    gdf_fixed = fix_strip_whitespace(gdf_fixed)
    gdf_fixed.to_file(path_out, driver="GPKG")

    after = validate(str(path_out))
    after_rule_ids = {i.rule_id for i in after.issues}
    # No more duplicate_geometry
    assert "duplicate_geometry" not in after_rule_ids
