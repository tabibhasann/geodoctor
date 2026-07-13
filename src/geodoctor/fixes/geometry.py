"""Auto-fix functions for geometry issues."""

import contextlib

import geopandas as gpd
from shapely import is_valid, make_valid
from shapely.geometry import Polygon


def fix_make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Repair invalid geometries with shapely.make_valid."""
    gdf = gdf.copy()
    for idx, geom in gdf.geometry.items():
        if geom is not None and not is_valid(geom):
            with contextlib.suppress(Exception):
                gdf.at[idx, "geometry"] = make_valid(geom)
    return gdf


def fix_drop_empty_null(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Remove features with empty or null geometry."""
    mask = gdf.geometry.apply(lambda g: g is not None and not g.is_empty)
    return gdf[mask].copy()


def fix_dedupe_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Remove duplicate geometries (keep first)."""
    wkb = gdf.geometry.apply(lambda g: g.wkb if g is not None else None)
    return gdf[~wkb.duplicated()].copy()


def fix_reproject(gdf: gpd.GeoDataFrame, target_crs: str) -> gpd.GeoDataFrame:
    """Reproject to the expected CRS."""
    return gdf.to_crs(target_crs)


def fix_explode_multipart(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Explode multipart geometries to single-part."""
    return gdf.explode(index_parts=False).reset_index(drop=True)


def fix_strip_whitespace(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Strip leading/trailing whitespace from string columns.

    Nulls and non-strings are preserved as-is.
    """
    gdf = gdf.copy()
    for col in gdf.select_dtypes(include=["object", "string"]).columns:
        if col == "geometry":
            continue
        gdf[col] = gdf[col].apply(lambda v: v.strip() if isinstance(v, str) and not pd_isna(v) else v)
    return gdf


def pd_isna(v) -> bool:
    """Null-safe check that handles NaN, None, and pd.NA uniformly."""
    if v is None:
        return True
    try:
        import pandas as pd

        return bool(pd.isna(v))
    except Exception:
        return False


def fix_remove_repeated_vertices(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Remove consecutive identical vertices from every geometry."""
    from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon

    gdf = gdf.copy()

    def _dedup_coords(coords):
        if len(coords) < 2:
            return coords
        result = [coords[0]]
        for c in coords[1:]:
            if c != result[-1]:
                result.append(c)
        return result

    def _clean(geom):
        if geom is None or geom.is_empty:
            return geom
        try:
            if geom.geom_type == "Point":
                return geom
            if geom.geom_type == "LineString":
                pts = _dedup_coords(list(geom.coords))
                return LineString(pts) if len(pts) >= 2 else geom
            if geom.geom_type == "MultiLineString":
                lines = []
                for line in geom.geoms:
                    pts = _dedup_coords(list(line.coords))
                    if len(pts) >= 2:
                        lines.append(LineString(pts))
                return MultiLineString(lines) if lines else geom
            if geom.geom_type == "Polygon":
                ext = _dedup_coords(list(geom.exterior.coords))
                ints = [_dedup_coords(list(r.coords)) for r in geom.interiors]
                return Polygon(exterior=ext, interiors=ints) if len(ext) >= 4 else geom
            if geom.geom_type == "MultiPolygon":
                polys = []
                for poly in geom.geoms:
                    ext = _dedup_coords(list(poly.exterior.coords))
                    if len(ext) < 4:
                        continue
                    ints = [_dedup_coords(list(r.coords)) for r in poly.interiors]
                    polys.append(Polygon(exterior=ext, interiors=ints))
                return MultiPolygon(polys) if polys else geom
        except Exception:
            return geom
        return geom

    gdf["geometry"] = gdf.geometry.apply(_clean)
    return gdf


def fix_normalize_ring_orientation(gdf: gpd.GeoDataFrame, expected: str = "ccw") -> gpd.GeoDataFrame:
    """Orient polygon exterior rings to match `expected` ('cw' or 'ccw')."""
    from shapely.geometry import MultiPolygon

    target_ccw = expected.lower().startswith("ccw")
    gdf = gdf.copy()

    def _orient(geom):
        if geom is None or geom.is_empty:
            return geom
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            return geom
        try:
            fixed = make_valid(geom)
            if fixed.geom_type == "Polygon":
                polys = [fixed]
            elif fixed.geom_type == "MultiPolygon":
                polys = list(fixed.geoms)
            else:
                return geom
            new = [_flip(p) if _is_ccw(p.exterior) != target_ccw else p for p in polys]
            return MultiPolygon(new) if len(new) > 1 else new[0]
        except Exception:
            return geom

    def _flip(poly: Polygon) -> Polygon:
        from shapely.geometry import Polygon as ShapelyPolygon

        ext = list(poly.exterior.coords)[::-1]
        ints = [list(i.coords)[::-1] for i in poly.interiors]
        return ShapelyPolygon(exterior=ext, interiors=ints)

    def _is_ccw(ring) -> bool:
        coords = list(ring.coords)
        s = 0.0
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            s += (x2 - x1) * (y2 + y1)
        return -s / 2.0 >= 0

    gdf["geometry"] = gdf.geometry.apply(_orient)
    return gdf


FIX_MAP = {
    "make_valid": fix_make_valid,
    "drop_empty_null": fix_drop_empty_null,
    "dedupe_geometry": fix_dedupe_geometry,
    "reproject": None,  # handled specially (needs CRS arg)
    "explode_multipart": fix_explode_multipart,
    "strip_whitespace": fix_strip_whitespace,
    "remove_repeated_vertices": fix_remove_repeated_vertices,
    "normalize_ring_orientation": fix_normalize_ring_orientation,
}

__all__ = list(FIX_MAP.keys()) + [
    "fix_make_valid",
    "fix_drop_empty_null",
    "fix_dedupe_geometry",
    "fix_reproject",
    "fix_explode_multipart",
    "fix_strip_whitespace",
    "fix_remove_repeated_vertices",
    "fix_normalize_ring_orientation",
    "FIX_MAP",
]
