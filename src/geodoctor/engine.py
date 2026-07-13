"""High-level programmatic API for geodoctor.

This module is what library users import:

    from geodoctor import validate
    report = validate("path/to/data.gpkg")
    if report.has_errors:
        ...

The CLI (``geodoctor.cli:app``) wraps this same engine; this module
exists so the library surface is stable and doesn't pull in typer/rich.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from . import checks  # noqa: F401  -- side effect: registers all @register_check decorators
from .config import GeodoctorConfig, load_config
from .dataset import load_dataset
from .registry import CHECKS
from .report import Issue, Report


def _is_rule_active(rule_id: str, config: GeodoctorConfig) -> bool:
    """Mirror of ``cli._is_rule_active`` kept here so the engine has no CLI dep."""
    geom = config.geometry
    if rule_id == "invalid_geometry":
        return not geom.allow_invalid
    if rule_id in {"empty_geometry", "null_geometry"}:
        if rule_id == "null_geometry":
            return not config.geometry.allow_null
        return not config.geometry.allow_empty
    if rule_id == "duplicate_geometry":
        return not geom.allow_duplicates
    if rule_id == "mixed_geometry_types":
        return geom.single_geometry_type
    if rule_id == "sliver_polygon":
        return geom.min_area_m2 > 0
    if rule_id == "out_of_bounds":
        return config.crs.expected in (None, "EPSG:4326", "4326")
    if rule_id == "missing_crs":
        return config.crs.require
    return True


def validate(
    path: str | Path,
    config: GeodoctorConfig | None = None,
    layer: str | None = None,
    rule_ids: Iterable[str] | None = None,
) -> Report:
    """Run registered checks against ``path`` and return a :class:`Report`.

    Args:
        path: Path to a vector dataset readable by geopandas/pyogrio.
        config: Optional configuration. If ``None``, defaults from
            :func:`load_config` are used.
        layer: Optional layer name (for multi-layer formats like GPKG).
        rule_ids: Optional subset of rule ids to run. Defaults to all
            active rules.

    Returns:
        A :class:`Report` instance (also accessible via the lazy import
        ``from geodoctor import Report``).
    """
    if config is None:
        config = load_config()

    active = (
        [r for r in rule_ids if r in CHECKS]
        if rule_ids is not None
        else [r for r in CHECKS if _is_rule_active(r, config)]
    )

    report = Report()
    path = Path(path)
    if not path.exists():
        report.issues.append(
            Issue(
                rule_id="io",
                severity="error",
                message=f"file not found: {path}",
            )
        )
        return report

    for layer_name, gdf in load_dataset(str(path), layer=layer):
        report.layers_checked += 1
        report.total_features += len(gdf)
        for rule_id in active:
            check_info = CHECKS[rule_id]
            severity = config.effective_severity(rule_id, check_info["severity"])
            try:
                issues = check_info["fn"](gdf, config)
            except Exception as exc:  # noqa: BLE001
                issues = [
                    Issue(
                        rule_id=rule_id,
                        severity=severity,
                        message=f"Check failed: {exc}",
                        layer=layer_name,
                    )
                ]
            for issue in issues:
                issue.severity = severity
                issue.layer = layer_name
                report.issues.append(issue)

    return report
