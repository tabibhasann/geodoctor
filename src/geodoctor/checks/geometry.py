"""Geometry quality checks."""

import geopandas as gpd
from shapely import is_empty, is_valid
from shapely.validation import explain_validity

from ..config import GeodoctorConfig
from ..registry import register_check
from ..report import Issue
from .geometry_helpers import _geodesic_area, _signed_area_2x


@register_check(
    "invalid_geometry",
    severity="error",
    description="Geometry is invalid (self-intersections, etc.)",
    fix_id="make_valid",
)
def check_invalid_geometry(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if config.geometry.allow_invalid:
        return []

    invalid = gdf[~gdf.geometry.apply(lambda g: is_valid(g) if g is not None else True)]
    if len(invalid) == 0:
        return []

    reasons = []
    for idx in invalid.index[:10]:
        g = invalid.loc[idx].geometry
        if g is not None and not is_valid(g):
            reasons.append(f"FID {idx}: {explain_validity(g)}")

    return [
        Issue(
            rule_id="invalid_geometry",
            severity="error",
            message=f"{len(invalid)} invalid geometries. " + "; ".join(reasons),
            feature_ids=list(invalid.index),
            fix_available=True,
        )
    ]


@register_check("empty_geometry", severity="warning", description="Features with empty geometry")
def check_empty_geometry(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if config.geometry.allow_empty:
        return []

    empty = gdf[gdf.geometry.apply(lambda g: is_empty(g) if g is not None else True)]
    if len(empty) == 0:
        return []

    return [
        Issue(
            rule_id="empty_geometry",
            severity="warning",
            message=f"{len(empty)} empty geometries",
            feature_ids=list(empty.index),
            fix_available=True,
        )
    ]


@register_check(
    "null_geometry",
    severity="error",
    description="Features with null/missing geometry",
)
def check_null_geometry(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if config.geometry.allow_null:
        return []

    nulls = gdf[gdf.geometry.isna()]
    if len(nulls) == 0:
        return []

    return [
        Issue(
            rule_id="null_geometry",
            severity="error",
            message=f"{len(nulls)} features with null geometry",
            feature_ids=list(nulls.index),
        )
    ]


@register_check(
    "duplicate_geometry",
    severity="warning",
    description="Duplicate (identical) geometries",
    fix_id="dedupe_geometry",
)
def check_duplicate_geometry(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if config.geometry.allow_duplicates:
        return []

    wkb = gdf.geometry.apply(lambda g: g.wkb if g is not None else None)
    dupes = wkb[wkb.duplicated()]
    if len(dupes) == 0:
        return []

    return [
        Issue(
            rule_id="duplicate_geometry",
            severity="warning",
            message=f"{len(dupes)} duplicate geometries",
            feature_ids=list(dupes.index),
            fix_available=True,
        )
    ]


@register_check(
    "mixed_geometry_types",
    severity="warning",
    description="Multiple geometry types in a single layer",
)
def check_mixed_geometry_types(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if not config.geometry.single_geometry_type:
        return []

    types = gdf.geometry.apply(lambda g: g.geom_type if g is not None else None).dropna()
    unique_types = types.unique()
    if len(unique_types) <= 1:
        return []

    return [
        Issue(
            rule_id="mixed_geometry_types",
            severity="warning",
            message=f"Mixed geometry types: {list(unique_types)}",
            feature_ids=list(gdf.index),
        )
    ]


@register_check("sliver_polygon", severity="warning", description="Polygons below minimum area threshold")
def check_sliver_polygon(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    min_area = config.geometry.min_area_m2
    if min_area <= 0:
        return []

    geom_types = gdf.geometry.geom_type.dropna().unique()
    if not any(gt in ("Polygon", "MultiPolygon") for gt in geom_types):
        return []

    areas = _geodesic_area(gdf)
    slivers = gdf[areas < min_area]
    if len(slivers) == 0:
        return []

    return [
        Issue(
            rule_id="sliver_polygon",
            severity="warning",
            message=f"{len(slivers)} polygons below {min_area} m²",
            feature_ids=list(slivers.index),
        )
    ]


@register_check("out_of_bounds", severity="error", description="Coordinates outside valid range for geographic CRS")
def check_out_of_bounds(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    if gdf.crs is None or not gdf.crs.is_geographic:
        return []

    bad = []
    for idx, geom in gdf.geometry.items():
        if geom is None:
            continue
        b = geom.bounds
        if b[0] < -180 or b[2] > 180 or b[1] < -90 or b[3] > 90:
            bad.append(idx)

    if not bad:
        return []

    return [
        Issue(
            rule_id="out_of_bounds",
            severity="error",
            message=f"{len(bad)} features have coordinates outside [-180,180],[-90,90]",
            feature_ids=bad,
        )
    ]


@register_check(
    "repeated_vertices",
    severity="info",
    description="Geometries with consecutive identical vertices",
    fix_id="remove_repeated_vertices",
)
def check_repeated_vertices(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    affected: list[int] = []
    for idx, geom in gdf.geometry.items():
        if geom is None or geom.is_empty:
            continue
        try:
            coords = list(geom.coords)
            for i in range(1, len(coords)):
                if coords[i] == coords[i - 1]:
                    affected.append(idx)
                    break
        except Exception:
            continue
    if not affected:
        return []
    return [
        Issue(
            rule_id="repeated_vertices",
            severity="info",
            message=f"{len(affected)} geometries have repeated consecutive vertices",
            feature_ids=affected,
            fix_available=True,
        )
    ]


@register_check(
    "zero_length_segment",
    severity="info",
    description="Line geometries with zero-length segments",
)
def check_zero_length_segment(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    affected: list[int] = []
    for idx, geom in gdf.geometry.items():
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type not in ("LineString", "MultiLineString"):
            continue
        try:
            for line in geom.geoms if geom.geom_type == "MultiLineString" else [geom]:
                coords = list(line.coords)
                for i in range(1, len(coords)):
                    if coords[i] == coords[i - 1]:
                        affected.append(idx)
                        break
                if idx in affected:
                    break
        except Exception:
            continue
    if not affected:
        return []
    return [
        Issue(
            rule_id="zero_length_segment",
            severity="info",
            message=f"{len(affected)} line geometries have zero-length segments",
            feature_ids=affected,
        )
    ]


@register_check(
    "ring_orientation",
    severity="info",
    description="Polygon exterior rings with unexpected orientation",
    fix_id="normalize_ring_orientation",
)
def check_ring_orientation(gdf: gpd.GeoDataFrame, config: GeodoctorConfig) -> list[Issue]:
    expected = config.geometry.expected_ring_orientation
    if expected is None:
        return []

    target_sign = 1.0 if expected.lower().startswith("cw") else -1.0
    affected: list[int] = []
    for idx, geom in gdf.geometry.items():
        if geom is None or geom.is_empty:
            continue
        polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom] if geom.geom_type == "Polygon" else []
        for poly in polys:
            try:
                # Signed area: positive = CCW in shapely 2.x
                _, _, sign = _signed_area_2x(poly.exterior)
                if sign * target_sign < 0:
                    affected.append(idx)
                    break
            except Exception:
                continue
    if not affected:
        return []
    return [
        Issue(
            rule_id="ring_orientation",
            severity="info",
            message=f"{len(affected)} polygons have exterior rings not matching '{expected}'",
            feature_ids=affected,
            fix_available=True,
        )
    ]
