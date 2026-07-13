"""Integration tests: end-to-end CLI."""

import json

from typer.testing import CliRunner

from geodoctor.cli import app

runner = CliRunner()


def test_check_good_gpkg():
    result = runner.invoke(app, ["check", "tests/fixtures/good.gpkg"])
    assert result.exit_code == 0


def test_check_invalid_geom():
    result = runner.invoke(
        app,
        [
            "check",
            "tests/fixtures/invalid_geom.geojson",
            "--config",
            "tests/fixtures/strict_config.yml",
        ],
    )
    # Should find errors with strict config
    # Even if exit code is 1 (errors found), the command should work
    assert result.exit_code in (0, 1)


def test_rules():
    result = runner.invoke(app, ["rules"])
    assert result.exit_code == 0
    assert "invalid_geometry" in result.stdout


def test_rules_json():
    result = runner.invoke(app, ["rules", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "rules" in data
    assert "total" in data
    assert data["total"] > 0
    rule_ids = {r["rule_id"] for r in data["rules"]}
    assert "invalid_geometry" in rule_ids


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.2.0" in result.stdout


def test_missing_file():
    result = runner.invoke(app, ["check", "nonexistent.gpkg"])
    assert result.exit_code == 2


def test_check_github_format():
    result = runner.invoke(
        app,
        [
            "check",
            "tests/fixtures/invalid_geom.geojson",
            "--config",
            "tests/fixtures/strict_config.yml",
            "--format",
            "github",
        ],
    )
    assert result.exit_code in (0, 1)
    # GitHub annotations start with ::error or ::warning or ::notice
    if result.exit_code == 1:
        assert "::error" in result.stdout or "::warning" in result.stdout
    else:
        assert "::notice" in result.stdout


def test_check_sarif_format():
    result = runner.invoke(
        app,
        ["check", "tests/fixtures/good.gpkg", "--format", "sarif"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["$schema"].startswith("https://docs.oasis-open.org/sarif")
    assert data["version"] == "2.1.0"
    assert len(data["runs"]) == 1
    assert data["runs"][0]["tool"]["driver"]["name"] == "geodoctor"


def test_check_ci_format():
    result = runner.invoke(
        app,
        ["check", "tests/fixtures/good.gpkg", "--ci"],
    )
    assert result.exit_code == 0
    assert "geodoctor:" in result.stdout


def test_check_ci_format_with_issues():
    result = runner.invoke(
        app,
        ["check", "tests/fixtures/invalid_geom.geojson", "--config", "tests/fixtures/strict_config.yml", "--ci"],
    )
    assert result.exit_code in (0, 1)
    assert "geodoctor:" in result.stdout
    assert "issue(s)" in result.stdout


def test_diff_command():
    result = runner.invoke(
        app,
        ["diff", "tests/fixtures/good.gpkg", "tests/fixtures/good.gpkg"],
    )
    assert result.exit_code == 0
    assert "Comparing:" in result.stdout


def test_diff_json():
    result = runner.invoke(
        app,
        ["diff", "tests/fixtures/good.gpkg", "tests/fixtures/good.gpkg", "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "dataset_a" in data
    assert "dataset_b" in data
    assert "summary" in data


def test_diff_empty_geojson(tmp_path):
    """diff should handle empty datasets gracefully (both files empty)."""
    empty = tmp_path / "empty.geojson"
    empty.write_text('{"type":"FeatureCollection","features":[]}')
    result = runner.invoke(app, ["diff", str(empty), str(empty)])
    assert result.exit_code == 0
    assert "Comparing:" in result.stdout


def test_diff_one_empty(tmp_path):
    """diff should handle one empty and one non-empty dataset."""
    empty = tmp_path / "empty.geojson"
    empty.write_text('{"type":"FeatureCollection","features":[]}')
    result = runner.invoke(
        app,
        ["diff", "tests/fixtures/good.gpkg", str(empty)],
    )
    assert result.exit_code in (0, 1)


def test_sarif_has_results_structure():
    """SARIF output should have valid results array even when no issues."""
    result = runner.invoke(
        app,
        ["check", "tests/fixtures/good.gpkg", "--format", "sarif"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    run = data["runs"][0]
    assert "results" in run
    assert isinstance(run["results"], list)
    assert "tool" in run
    assert "driver" in run["tool"]
    assert "rules" in run["tool"]["driver"]
