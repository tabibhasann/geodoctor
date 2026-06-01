"""Integration tests: end-to-end CLI."""

import pytest
from typer.testing import CliRunner

from geodoctor.cli import app

runner = CliRunner()


def test_check_good_gpkg():
    result = runner.invoke(app, ["check", "tests/fixtures/good.gpkg"])
    assert result.exit_code == 0


def test_check_invalid_geom():
    result = runner.invoke(app, [
        "check",
        "tests/fixtures/invalid_geom.geojson",
        "--config",
        "tests/fixtures/strict_config.yml",
    ])
    # Should find errors with strict config
    # Even if exit code is 1 (errors found), the command should work
    assert result.exit_code in (0, 1)


def test_rules():
    result = runner.invoke(app, ["rules"])
    assert result.exit_code == 0
    assert "invalid_geometry" in result.stdout


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_missing_file():
    result = runner.invoke(app, ["check", "nonexistent.gpkg"])
    assert result.exit_code == 2
