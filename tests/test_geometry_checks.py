"""Tests for geometry checks."""

import geopandas as gpd
import pytest

from geodoctor.config import GeometryConfig, GeodoctorConfig
from geodoctor.checks.geometry import (
    check_invalid_geometry,
    check_empty_geometry,
    check_null_geometry,
    check_duplicate_geometry,
    check_mixed_geometry_types,
    check_out_of_bounds,
)


class TestInvalidGeometry:
    def test_valid_data_no_issues(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0, 1], [0, 1]), crs="EPSG:4326")
        config = GeodoctorConfig(geometry=GeometryConfig(allow_invalid=False))
        issues = check_invalid_geometry(gdf, config)
        assert len(issues) == 0

    def test_invalid_bowtie(self):
        from shapely.geometry import Polygon
        gdf = gpd.GeoDataFrame(
            geometry=[Polygon([(0, 0), (1, 1), (0, 1), (1, 0)])],
            crs="EPSG:4326",
        )
        config = GeodoctorConfig(geometry=GeometryConfig(allow_invalid=False))
        issues = check_invalid_geometry(gdf, config)
        assert len(issues) > 0
        assert issues[0].rule_id == "invalid_geometry"


class TestEmptyGeometry:
    def test_no_empty(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]), crs="EPSG:4326")
        config = GeodoctorConfig(geometry=GeometryConfig(allow_empty=False))
        issues = check_empty_geometry(gdf, config)
        assert len(issues) == 0

    def test_with_empty(self):
        from shapely import wkt
        gdf = gpd.GeoDataFrame(
            geometry=[wkt.loads("POINT(0 0)"), wkt.loads("POLYGON EMPTY")],
            crs="EPSG:4326",
        )
        config = GeodoctorConfig(geometry=GeometryConfig(allow_empty=False))
        issues = check_empty_geometry(gdf, config)
        assert len(issues) > 0


class TestNullGeometry:
    def test_nulls(self):
        gdf = gpd.GeoDataFrame(
            {"a": [1, 2]},
            geometry=gpd.points_from_xy([0, 1], [0, 1]),
            crs="EPSG:4326",
        )
        gdf.loc[1, "geometry"] = None
        issues = check_null_geometry(gdf, GeodoctorConfig())
        assert len(issues) > 0
        assert issues[0].rule_id == "null_geometry"


class TestDuplicateGeometry:
    def test_dupes(self):
        geom = gpd.points_from_xy([0, 0], [0, 0])
        gdf = gpd.GeoDataFrame(geometry=geom, crs="EPSG:4326")
        config = GeodoctorConfig(geometry=GeometryConfig(allow_duplicates=False))
        issues = check_duplicate_geometry(gdf, config)
        assert len(issues) > 0


class TestOutOfBounds:
    def test_valid_bounds(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]), crs="EPSG:4326")
        issues = check_out_of_bounds(gdf, GeodoctorConfig())
        assert len(issues) == 0

    def test_out_of_bounds(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([200], [0]), crs="EPSG:4326")
        issues = check_out_of_bounds(gdf, GeodoctorConfig())
        assert len(issues) > 0
