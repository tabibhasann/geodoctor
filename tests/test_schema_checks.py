"""Tests for schema checks."""

import geopandas as gpd

from geodoctor.checks.schema import (
    check_missing_required_field,
    check_non_unique_values,
    check_null_in_non_nullable,
    check_value_not_allowed,
)
from geodoctor.config import FieldSpec, GeodoctorConfig, SchemaConfig


class TestMissingRequiredField:
    def test_field_present(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=gpd.points_from_xy([0], [0]),
            crs="EPSG:4326",
        )
        config = GeodoctorConfig(schema_config=SchemaConfig(fields={"name": FieldSpec(required=True)}))
        issues = check_missing_required_field(gdf, config)
        assert len(issues) == 0

    def test_field_missing(self):
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([0], [0]), crs="EPSG:4326")
        config = GeodoctorConfig(schema_config=SchemaConfig(fields={"name": FieldSpec(required=True)}))
        issues = check_missing_required_field(gdf, config)
        assert len(issues) > 0
        assert issues[0].rule_id == "missing_required_field"


class TestNullInNonNullable:
    def test_null_present(self):
        gdf = gpd.GeoDataFrame(
            {"name": [None, "B"]},
            geometry=gpd.points_from_xy([0, 1], [0, 1]),
            crs="EPSG:4326",
        )
        config = GeodoctorConfig(schema_config=SchemaConfig(fields={"name": FieldSpec(nullable=False)}))
        issues = check_null_in_non_nullable(gdf, config)
        assert len(issues) > 0
        assert issues[0].rule_id == "null_in_non_nullable"


class TestValueNotAllowed:
    def test_invalid_value(self):
        gdf = gpd.GeoDataFrame(
            {"category": ["residential", "unknown"]},
            geometry=gpd.points_from_xy([0, 1], [0, 1]),
            crs="EPSG:4326",
        )
        config = GeodoctorConfig(
            schema_config=SchemaConfig(fields={"category": FieldSpec(allowed=["residential", "commercial"])})
        )
        issues = check_value_not_allowed(gdf, config)
        assert len(issues) > 0
        assert issues[0].rule_id == "value_not_allowed"


class TestNonUniqueValues:
    def test_duplicates(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1, 1, 2]},
            geometry=gpd.points_from_xy([0, 1, 2], [0, 1, 2]),
            crs="EPSG:4326",
        )
        config = GeodoctorConfig(schema_config=SchemaConfig(fields={"id": FieldSpec(unique=True)}))
        issues = check_non_unique_values(gdf, config)
        assert len(issues) > 0
