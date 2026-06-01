"""Structure checks."""

import geopandas as gpd

from ..config import GeodoctorConfig
from ..registry import register_check
from ..report import Issue


@register_check("empty_layer", severity="warning", description="Layer has zero features")
def check_empty_layer(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if len(gdf) > 0:
        return []

    return [
        Issue(
            rule_id="empty_layer",
            severity="warning",
            message="Layer contains zero features",
        )
    ]


@register_check(
    "shapefile_field_name_too_long",
    severity="warning",
    description="Field name exceeds Shapefile limit of 10 characters",
)
def check_shapefile_field_name_too_long(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    long_fields = [c for c in gdf.columns if len(c) > 10]
    if not long_fields:
        return []

    return [
        Issue(
            rule_id="shapefile_field_name_too_long",
            severity="warning",
            message=f"Fields exceeding 10 char Shapefile limit: {', '.join(long_fields)}",
        )
    ]


@register_check(
    "unsafe_field_name",
    severity="warning",
    description="Field name contains special characters or starts with a digit",
)
def check_unsafe_field_name(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    import re

    bad = [c for c in gdf.columns if c != "geometry" and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", c)]
    if not bad:
        return []

    return [
        Issue(
            rule_id="unsafe_field_name",
            severity="warning",
            message=f"Potentially unsafe field names: {', '.join(bad)}",
        )
    ]
