"""Topology checks for gaps and overlaps in polygon layers."""

import geopandas as gpd
from shapely.ops import unary_union

from ..registry import register_check
from ..report import Issue


@register_check(
    "polygon_gaps",
    severity="warning",
    description="Detect gaps (holes) between adjacent polygons",
)
def check_polygon_gaps(gdf: gpd.GeoDataFrame, config) -> list[Issue]:
    """Detect gaps between polygons in a layer.

    Gaps are areas not covered by any polygon but surrounded by polygons.
    Only applies to polygon/multipolygon layers.
    """
    if gdf.empty:
        return []

    geom_types = gdf.geometry.geom_type.unique()
    if not any(gt in ["Polygon", "MultiPolygon"] for gt in geom_types):
        return []

    try:
        # Union all polygons
        unioned = unary_union(gdf.geometry)

        # Check if union has interior rings (holes)
        if unioned.geom_type == "Polygon":
            holes = list(unioned.interiors)
        elif unioned.geom_type == "MultiPolygon":
            holes = []
            for poly in unioned.geoms:
                holes.extend(list(poly.interiors))
        else:
            return []

        if not holes:
            return []

        # Calculate total gap area
        from shapely.geometry import Polygon

        gap_area = sum(Polygon(hole).area for hole in holes)

        return [
            Issue(
                rule_id="polygon_gaps",
                severity="warning",
                message=f"Found {len(holes)} gaps between polygons (total area: {gap_area:.2f} units²)",
                feature_ids=[],
            )
        ]
    except Exception as e:
        return [
            Issue(
                rule_id="polygon_gaps",
                severity="warning",
                message=f"Could not check for gaps: {e}",
                feature_ids=[],
            )
        ]


@register_check(
    "polygon_overlaps",
    severity="warning",
    description="Detect overlapping polygons in a layer",
)
def check_polygon_overlaps(gdf: gpd.GeoDataFrame, config) -> list[Issue]:
    """Detect overlapping polygons in a layer.

    Overlaps occur when two or more polygons share interior area.
    Only applies to polygon/multipolygon layers.
    """
    if gdf.empty or len(gdf) < 2:
        return []

    geom_types = gdf.geometry.geom_type.unique()
    if not any(gt in ["Polygon", "MultiPolygon"] for gt in geom_types):
        return []

    try:
        # Use spatial index for efficient overlap detection
        sindex = gdf.sindex

        overlap_pairs = []
        checked = set()

        for idx, geom in gdf.geometry.items():
            if geom is None or geom.is_empty:
                continue

            # Find potential candidates using spatial index
            candidates = list(sindex.intersection(geom.bounds))

            for candidate_idx in candidates:
                if candidate_idx <= idx:  # Avoid duplicate checks
                    continue

                pair = (idx, candidate_idx)
                if pair in checked:
                    continue
                checked.add(pair)

                other_geom = gdf.geometry.iloc[candidate_idx]
                if other_geom is None or other_geom.is_empty:
                    continue

                # Check for intersection
                if geom.intersects(other_geom):
                    intersection = geom.intersection(other_geom)
                    # Only count if intersection has area (not just touching)
                    if intersection.area > 0:
                        overlap_pairs.append(pair)

        if not overlap_pairs:
            return []

        affected_ids = set()
        for idx1, idx2 in overlap_pairs:
            affected_ids.add(idx1)
            affected_ids.add(idx2)

        return [
            Issue(
                rule_id="polygon_overlaps",
                severity="warning",
                message=f"Found {len(overlap_pairs)} overlapping polygon pairs",
                feature_ids=list(affected_ids),
            )
        ]
    except Exception as e:
        return [
            Issue(
                rule_id="polygon_overlaps",
                severity="warning",
                message=f"Could not check for overlaps: {e}",
                feature_ids=[],
            )
        ]
