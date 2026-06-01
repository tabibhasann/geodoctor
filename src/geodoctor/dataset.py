"""Dataset loading utilities via pyogrio/geopandas."""

import geopandas as gpd


def load_dataset(path: str, layer: str | None = None):
    """Load a vector dataset and return list of (layer_name, GeoDataFrame) pairs."""
    import os.path

    ext = os.path.splitext(path)[1].lower()

    # Single-layer formats
    if ext in (".geojson", ".json", ".fgb"):
        gdf = gpd.read_file(path)
        return [(layer or "default", gdf)]

    # Multi-layer formats
    try:
        layers = gpd.list_layers(path)
    except Exception:
        gdf = gpd.read_file(path)
        return [(layer or "default", gdf)]

    results = []
    for _, row in layers.iterrows():
        layer_name = row["name"]
        if layer and layer_name != layer:
            continue
        try:
            gdf = gpd.read_file(path, layer=layer_name)
            results.append((layer_name, gdf))
        except Exception:
            continue

    return results if results else _fallback_load(path)


def _fallback_load(path: str):
    """Fallback: try reading as a single layer."""
    gdf = gpd.read_file(path)
    return [("default", gdf)]
