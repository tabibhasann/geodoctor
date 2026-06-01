"""CRS-related checks."""

import geopandas as gpd

from ..config import GeodoctorConfig
from ..registry import register_check
from ..report import Issue


@register_check("missing_crs", severity="error", description="Layer has no CRS defined")
def check_missing_crs(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if not config.crs.require:
        return []

    if gdf.crs is not None:
        return []

    return [
        Issue(
            rule_id="missing_crs",
            severity="error",
            message="CRS is not defined",
            feature_ids=list(gdf.index),
        )
    ]


@register_check(
    "unexpected_crs",
    severity="error",
    description="CRS does not match expected value",
    fix_id="reproject",
)
def check_unexpected_crs(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    expected = config.crs.expected
    if not expected or gdf.crs is None:
        return []

    if gdf.crs.to_string() == expected or gdf.crs.to_epsg() == _parse_epsg(expected):
        return []

    return [
        Issue(
            rule_id="unexpected_crs",
            severity="error",
            message=f"CRS is {gdf.crs.to_string()}, expected {expected}",
            feature_ids=list(gdf.index),
            fix_available=True,
        )
    ]


def _parse_epsg(expected: str) -> int | None:
    """Extract EPSG code from a string like 'EPSG:4326'."""
    try:
        return int(expected.replace("EPSG:", "").strip())
    except (ValueError, AttributeError):
        return None
