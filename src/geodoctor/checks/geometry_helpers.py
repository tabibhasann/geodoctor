"""Helper functions for geometry checks."""

from __future__ import annotations

import geopandas as gpd


def _geodesic_area(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Compute geodesic area in m² for each feature."""
    from pyproj import Geod

    geod = Geod(ellps="WGS84")

    def _area(geom):
        if geom is None or geom.is_empty:
            return 0.0
        try:
            area_m2, _ = geod.geometry_area_perimeter(geom)
            return abs(area_m2)
        except Exception:
            return geom.area  # fallback to planar

    return gdf.geometry.apply(_area)


def _signed_area_2x(ring) -> tuple[float, float, float]:
    """Return (abs_area, perim, signed_area) using shapely 2.x signed area."""
    coords = list(ring.coords)
    s = 0.0
    n = len(coords) - 1
    for i in range(n):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        s += (x2 - x1) * (y2 + y1)
    signed = -s / 2.0
    return abs(signed), abs(s) / 2.0, signed
