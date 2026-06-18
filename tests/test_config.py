"""Tests for the config system."""

from __future__ import annotations

from pathlib import Path

from geodoctor.config import (
    CRSConfig,
    FieldSpec,
    GeodoctorConfig,
    GeometryConfig,
    load_config,
)


def test_geometry_defaults_match_readme():
    """The default config should match the documented 'strict' example."""
    g = GeometryConfig()
    assert g.allow_invalid is False
    assert g.allow_empty is False
    assert g.allow_duplicates is False
    assert g.single_geometry_type is True
    assert g.min_area_m2 == 1.0


def test_crs_defaults_to_epsg4326():
    c = CRSConfig()
    assert c.expected == "EPSG:4326"
    assert c.require is True


def test_field_spec_defaults():
    f = FieldSpec()
    assert f.type == "str"
    assert f.required is False
    assert f.nullable is True


def test_effective_severity_override():
    cfg = GeodoctorConfig(severity_overrides={"invalid_geometry": "warning"})
    assert cfg.effective_severity("invalid_geometry", "error") == "warning"
    assert cfg.effective_severity("other_rule", "error") == "error"


def test_load_config_missing_file_uses_defaults(tmp_path: Path):
    cfg = load_config(str(tmp_path / "nonexistent.yml"))
    assert cfg.geometry.allow_invalid is False
    assert cfg.crs.expected == "EPSG:4326"


def test_load_config_remaps_schema_key(tmp_path: Path):
    p = tmp_path / "geodoctor.yml"
    p.write_text(
        """
crs:
  expected: EPSG:3857
  require: true
geometry:
  allow_invalid: true
schema:
  fields:
    name:
      type: str
      required: true
      max_length: 50
"""
    )
    cfg = load_config(str(p))
    assert cfg.crs.expected == "EPSG:3857"
    assert cfg.geometry.allow_invalid is True
    assert "name" in cfg.schema_config.fields
    assert cfg.schema_config.fields["name"].max_length == 50


def test_load_config_empty_file(tmp_path: Path):
    p = tmp_path / "geodoctor.yml"
    p.write_text("")
    cfg = load_config(str(p))
    assert isinstance(cfg, GeodoctorConfig)


def test_load_config_with_severity_overrides(tmp_path: Path):
    p = tmp_path / "geodoctor.yml"
    p.write_text(
        """
severity_overrides:
  duplicate_geometry: warning
  invalid_geometry: info
"""
    )
    cfg = load_config(str(p))
    assert cfg.severity_overrides["duplicate_geometry"] == "warning"
    assert cfg.effective_severity("invalid_geometry", "error") == "info"
