"""Generate test fixture datasets."""

import geopandas as gpd
from shapely.geometry import Point, Polygon


def good_gpkg(path: str) -> None:
    """A perfectly valid dataset."""
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Site A", "Site B", "Site C"],
            "population": [100, 200, 300],
            "category": ["residential", "commercial", "industrial"],
        },
        geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
        crs="EPSG:4326",
    )
    gdf.to_file(path, driver="GPKG")


def invalid_geom_geojson(path: str) -> None:
    """A dataset with a self-intersecting polygon (bowtie)."""

    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[Polygon([(0, 0), (1, 1), (0, 1), (1, 0)])],  # bowtie
        crs="EPSG:4326",
    )
    gdf.to_file(path, driver="GeoJSON")


def missing_crs_geojson(path: str) -> None:
    """A dataset without a CRS."""
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[Point(0, 0)],
    )
    gdf.to_file(path, driver="GeoJSON")


def bad_schema_gpkg(path: str) -> None:
    """A dataset with schema violations."""
    gdf = gpd.GeoDataFrame(
        {
            "id": [1, 2, 3],
            "name": [None, "Site B", "Site C"],  # null in non-nullable
            "population": [100, -1, 999999],  # negative, too large
            "category": ["residential", "unknown", "industrial"],  # invalid
        },
        geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
        crs="EPSG:4326",
    )
    gdf.to_file(path, driver="GPKG")


if __name__ == "__main__":
    import sys

    good_gpkg(sys.argv[1])
