"""pytest.raises-based error path tests for geodoctor.

Tests that verify exceptions are raised where appropriate:
invalid CRS, corrupt files, invalid YAML, invalid parameters,
and edge cases that should fail hard rather than silently.
"""

from pathlib import Path

import geopandas as gpd
import pytest
from pydantic import ValidationError
from pyogrio.errors import DataSourceError
from pyproj.exceptions import CRSError
from shapely.geometry import Point
from yaml.parser import ParserError

from geodoctor.config import GeodoctorConfig, load_config
from geodoctor.dataset import load_dataset
from geodoctor.fixes.geometry import fix_explode_multipart, fix_reproject
from geodoctor.report import Issue, Report


@pytest.fixture
def valid_gdf() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[Point(0, 0), Point(1, 1)],
        crs="EPSG:4326",
    )


@pytest.fixture
def tmp_geojson(valid_gdf: gpd.GeoDataFrame, tmp_path: Path) -> Path:
    p = tmp_path / "test.geojson"
    valid_gdf.to_file(p, driver="GeoJSON")
    return p


class TestFixReprojectRaises:
    """fix_reproject should raise on invalid CRS."""

    def test_reproject_invalid_crs(self, valid_gdf: gpd.GeoDataFrame) -> None:
        with pytest.raises(CRSError):
            fix_reproject(valid_gdf, "NOT_A_CRS")

    def test_reproject_empty_crs_string(self, valid_gdf: gpd.GeoDataFrame) -> None:
        with pytest.raises(CRSError):
            fix_reproject(valid_gdf, "")

    def test_reproject_no_crs_on_gdf(self) -> None:
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(0, 0)],
        )
        with pytest.raises(ValueError):
            fix_reproject(gdf, "EPSG:3857")


class TestLoadDatasetRaises:
    """load_dataset should raise on corrupt or nonexistent files."""

    def test_load_nonexistent_file(self) -> None:
        with pytest.raises((DataSourceError, FileNotFoundError)):
            load_dataset("/nonexistent/path/to/file.geojson")

    def test_load_corrupt_geojson(self, tmp_path: Path) -> None:
        p = tmp_path / "corrupt.geojson"
        p.write_text("{not valid geojson}")
        with pytest.raises(DataSourceError):
            load_dataset(str(p))

    def test_load_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.geojson"
        p.write_text("")
        with pytest.raises(DataSourceError):
            load_dataset(str(p))


class TestLoadConfigRaises:
    """load_config should raise on invalid YAML."""

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yml"
        p.write_text("not: [valid: yaml: {{{")
        with pytest.raises((ParserError, ValueError)):
            load_config(str(p))

    def test_load_yaml_wrong_type(self, tmp_path: Path) -> None:
        p = tmp_path / "wrong.yml"
        p.write_text("- just\n- a\n- list")
        with pytest.raises((ValidationError, ValueError, TypeError)):
            load_config(str(p))


class TestReportRaises:
    """Report dataclass edge cases that should raise."""

    def test_issue_accepts_any_severity_string(self) -> None:
        # Issue is a plain dataclass, not pydantic — severity is a Literal type hint only
        issue = Issue(rule_id="test", severity="not_a_severity", message="msg")
        assert issue.severity == "not_a_severity"

    def test_report_promoted_with_no_issues(self) -> None:
        report = Report()
        promoted = report.promoted()
        assert len(promoted.issues) == 0


class TestFixExplodeRaises:
    """fix_explode_multipart edge cases."""

    def test_explode_no_geometry_column(self) -> None:
        import pandas as pd

        df = pd.DataFrame({"name": ["A"]})
        with pytest.raises((ValueError, AttributeError)):
            fix_explode_multipart(gpd.GeoDataFrame(df))


class TestValidateCorruptData:
    """validate() should raise on corrupt data files."""

    def test_validate_corrupt_geojson_raises(self, tmp_path: Path) -> None:
        from geodoctor.engine import validate

        p = tmp_path / "corrupt.geojson"
        p.write_text("{not valid}")
        # validate raises DataSourceError for corrupt files
        with pytest.raises(DataSourceError):
            validate(str(p))

    def test_validate_empty_geojson_file_raises(self, tmp_path: Path) -> None:
        from geodoctor.engine import validate

        p = tmp_path / "empty.geojson"
        p.write_text("")
        with pytest.raises(DataSourceError):
            validate(str(p))


class TestConfigValidationRaises:
    """Config model validation should raise on invalid types."""

    def test_field_spec_invalid_type(self) -> None:
        from geodoctor.config import FieldSpec

        # Pydantic should validate types
        with pytest.raises(ValidationError):
            FieldSpec(type=123)  # type: ignore[arg-type]

    def test_geodoctor_config_invalid_severity_override(self) -> None:
        with pytest.raises(ValidationError):
            GeodoctorConfig(severity_overrides={"test": 123})  # type: ignore[dict-item]
