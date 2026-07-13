"""Check execution engine — runs registered checks against a dataset."""

from __future__ import annotations

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from ..config import GeodoctorConfig
from ..dataset import load_dataset
from ..registry import CHECKS
from ..report import Issue, Report


def is_rule_active(rule_id: str, config: GeodoctorConfig, default_sev: str) -> bool:
    """Check if a rule is active based on config.

    Rules can be disabled via config settings:
    - Geometry rules: check geometry.allow_* flags
    - CRS rules: check crs.require flag
    - Topology rules: active for polygon layers
    - Schema/structure rules: always active (controlled by field presence)
    """
    if rule_id == "invalid_geometry":
        return not config.geometry.allow_invalid
    if rule_id == "empty_geometry":
        return not config.geometry.allow_empty
    if rule_id == "null_geometry":
        return not config.geometry.allow_null
    if rule_id == "duplicate_geometry":
        return not config.geometry.allow_duplicates
    if rule_id == "mixed_geometry_types":
        return config.geometry.single_geometry_type
    if rule_id == "sliver_polygon":
        return config.geometry.min_area_m2 > 0
    if rule_id == "out_of_bounds":
        return config.crs.expected in (None, "EPSG:4326", "4326")
    if rule_id == "missing_crs":
        return config.crs.require
    return True


def run_checks(dataset_path: str, config: GeodoctorConfig, layer: str | None = None) -> Report:
    """Run all registered checks against a dataset."""
    report = Report()

    layers = list(load_dataset(dataset_path, layer=layer))
    active_rule_ids = [
        rid for rid in CHECKS
        if is_rule_active(rid, config, CHECKS[rid]["severity"])
    ]
    total_checks = len(layers) * len(active_rule_ids)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=True,
    ) as progress:
        task = progress.add_task("Running checks...", total=total_checks or 1)

        for layer_name, gdf in layers:
            report.layers_checked += 1
            report.total_features += len(gdf)

            for rule_id in active_rule_ids:
                check_info = CHECKS[rule_id]
                default_sev = check_info["severity"]
                severity = config.effective_severity(rule_id, default_sev)
                try:
                    issues = check_info["fn"](gdf, config)
                    for issue in issues:
                        issue.severity = severity
                        issue.layer = layer_name
                        report.issues.append(issue)
                except Exception as e:
                    report.issues.append(
                        Issue(
                            rule_id=rule_id,
                            severity=severity,
                            message=f"Check failed: {e}",
                            layer=layer_name,
                        )
                    )
                finally:
                    progress.advance(task)

    return report
