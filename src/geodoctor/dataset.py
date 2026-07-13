"""Dataset loading utilities via pyogrio/geopandas."""

import os.path

import geopandas as gpd


def load_dataset(path: str, layer: str | None = None):
    """Load a vector dataset and return list of (layer_name, GeoDataFrame) pairs."""
    ext = os.path.splitext(path)[1].lower()

    # Single-layer formats
    if ext in (".geojson", ".json", ".fgb"):
        gdf = gpd.read_file(path)
        gdf._source_path = path
        return [(layer or "default", gdf)]

    # GeoParquet
    if ext in (".parquet", ".geoparquet"):
        try:
            gdf = gpd.read_parquet(path)
        except ImportError as exc:
            raise ImportError(
                "GeoParquet support requires pyarrow. Install with: pip install pyarrow"
            ) from exc
        gdf._source_path = path
        return [(layer or "default", gdf)]

    # Multi-layer formats
    try:
        layers = gpd.list_layers(path)
    except Exception:
        gdf = gpd.read_file(path)
        gdf._source_path = path
        return [(layer or "default", gdf)]

    results = []
    for _, row in layers.iterrows():
        layer_name = row["name"]
        if layer and layer_name != layer:
            continue
        try:
            gdf = gpd.read_file(path, layer=layer_name)
            gdf._source_path = path
            results.append((layer_name, gdf))
        except Exception:
            continue

    return results if results else _fallback_load(path)


def _fallback_load(path: str):
    """Fallback: try reading as a single layer."""
    gdf = gpd.read_file(path)
    gdf._source_path = path
    return [("default", gdf)]
