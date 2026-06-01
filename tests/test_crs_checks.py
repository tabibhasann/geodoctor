"""Tests for CRS checks."""

import geopandas as gpd
import pytest

from geodoctor.config import CRSConfig, GeodoctorConfig
from geodoctor.checks.crs import check_missing_crs, check_unexpected_crs


class TestMissingCRS:
    def test_with_crs(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]), crs="EPSG:4326")
        issues = check_missing_crs(gdf, GeodoctorConfig())
        assert len(issues) == 0

    def test_without_crs(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]))
        config = GeodoctorConfig(crs=CRSConfig(require=True))
        issues = check_missing_crs(gdf, config)
        assert len(issues) > 0
        assert issues[0].rule_id == "missing_crs"


class TestUnexpectedCRS:
    def test_matching_crs(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]), crs="EPSG:4326")
        config = GeodoctorConfig(crs=CRSConfig(expected="EPSG:4326"))
        issues = check_unexpected_crs(gdf, config)
        assert len(issues) == 0

    def test_wrong_crs(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]), crs="EPSG:3857")
        config = GeodoctorConfig(crs=CRSConfig(expected="EPSG:4326"))
        issues = check_unexpected_crs(gdf, config)
        assert len(issues) > 0
        assert issues[0].rule_id == "unexpected_crs"
