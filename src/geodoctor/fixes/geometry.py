"""Auto-fix functions for geometry issues."""

import geopandas as gpd
from shapely import is_valid, make_valid


def fix_make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Repair invalid geometries with shapely.make_valid."""
    gdf = gdf.copy()
    for idx, geom in gdf.geometry.items():
        if geom is not None and not is_valid(geom):
            try:
                gdf.at[idx, "geometry"] = make_valid(geom)
            except Exception:
                pass
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
    """Strip leading/trailing whitespace from string columns."""
    gdf = gdf.copy()
    for col in gdf.select_dtypes(include=["object"]).columns:
        if col == "geometry":
            continue
        gdf[col] = gdf[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
    return gdf


FIX_MAP = {
    "make_valid": fix_make_valid,
    "drop_empty_null": fix_drop_empty_null,
    "dedupe_geometry": fix_dedupe_geometry,
    "reproject": None,  # handled specially (needs CRS arg)
    "explode_multipart": fix_explode_multipart,
    "strip_whitespace": fix_strip_whitespace,
}
