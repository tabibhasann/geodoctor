"""Tests for auto-fix functions."""

import geopandas as gpd
from shapely.geometry import MultiPoint, Point, Polygon

from geodoctor.fixes.geometry import (
    fix_dedupe_geometry,
    fix_drop_empty_null,
    fix_explode_multipart,
    fix_make_valid,
    fix_reproject,
    fix_strip_whitespace,
)


class TestFixMakeValid:
    def test_valid_geometry_unchanged(self):
        """Test that valid geometries are not modified."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(2, 2), (3, 2), (3, 3), (2, 3)]),
            ],
        )
        result = fix_make_valid(gdf)
        assert len(result) == 2
        assert all(result.geometry.is_valid)

    def test_invalid_bowtie_fixed(self):
        """Test that invalid bowtie polygon is fixed."""
        # Bowtie polygon (self-intersecting)
        bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[bowtie])

        assert not gdf.geometry[0].is_valid
        result = fix_make_valid(gdf)
        assert result.geometry[0].is_valid

    def test_mixed_valid_invalid(self):
        """Test mixed valid and invalid geometries."""
        valid_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        invalid_poly = Polygon([(2, 2), (3, 3), (3, 2), (2, 3)])  # Bowtie

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[valid_poly, invalid_poly],
        )

        result = fix_make_valid(gdf)
        assert len(result) == 2
        assert all(result.geometry.is_valid)

    def test_empty_dataframe(self):
        """Test with empty dataframe."""
        gdf = gpd.GeoDataFrame({"id": []}, geometry=[])
        result = fix_make_valid(gdf)
        assert len(result) == 0


class TestFixDropEmptyNull:
    def test_drop_null_geometries(self):
        """Test that null geometries are dropped."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[Point(0, 0), None, Point(1, 1)],
        )
        result = fix_drop_empty_null(gdf)
        assert len(result) == 2
        assert list(result["id"]) == [1, 3]

    def test_drop_empty_geometries(self):
        """Test that empty geometries are dropped."""
        from shapely.geometry import Point

        empty_point = Point()  # Empty point

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[Point(0, 0), empty_point, Point(1, 1)],
        )
        result = fix_drop_empty_null(gdf)
        assert len(result) == 2
        assert list(result["id"]) == [1, 3]

    def test_all_valid_kept(self):
        """Test that all valid geometries are kept."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[Point(0, 0), Point(1, 1)],
        )
        result = fix_drop_empty_null(gdf)
        assert len(result) == 2

    def test_all_null_removed(self):
        """Test that all null geometries are removed."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[None, None],
        )
        result = fix_drop_empty_null(gdf)
        assert len(result) == 0


class TestFixDedupeGeometry:
    def test_remove_duplicates(self):
        """Test that duplicate geometries are removed."""
        p1 = Point(0, 0)
        p2 = Point(1, 1)

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[p1, p1, p2],  # First two are duplicates
        )
        result = fix_dedupe_geometry(gdf)
        assert len(result) == 2
        assert list(result["id"]) == [1, 3]  # Keeps first occurrence

    def test_no_duplicates(self):
        """Test that unique geometries are kept."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[Point(0, 0), Point(1, 1)],
        )
        result = fix_dedupe_geometry(gdf)
        assert len(result) == 2

    def test_all_duplicates(self):
        """Test that all duplicates except first are removed."""
        p = Point(0, 0)
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[p, p, p],
        )
        result = fix_dedupe_geometry(gdf)
        assert len(result) == 1
        assert result["id"].iloc[0] == 1

    def test_with_null_geometries(self):
        """Test handling of null geometries."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[Point(0, 0), None, None],
        )
        result = fix_dedupe_geometry(gdf)
        # Should keep first Point and first None
        assert len(result) == 2


class TestFixReproject:
    def test_reproject_4326_to_3857(self):
        """Test reprojection from WGS84 to Web Mercator."""
        gdf = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        result = fix_reproject(gdf, "EPSG:3857")
        assert result.crs.to_epsg() == 3857

    def test_reproject_3857_to_4326(self):
        """Test reprojection from Web Mercator to WGS84."""
        gdf = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[Point(0, 0)],
            crs="EPSG:3857",
        )
        result = fix_reproject(gdf, "EPSG:4326")
        assert result.crs.to_epsg() == 4326

    def test_reproject_preserves_data(self):
        """Test that reprojection preserves attribute data."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2], "name": ["A", "B"]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )
        result = fix_reproject(gdf, "EPSG:3857")
        assert list(result["id"]) == [1, 2]
        assert list(result["name"]) == ["A", "B"]


class TestFixExplodeMultipart:
    def test_explode_multipoint(self):
        """Test exploding MultiPoint to individual Points."""
        mp = MultiPoint([(0, 0), (1, 1), (2, 2)])
        gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[mp])

        result = fix_explode_multipart(gdf)
        assert len(result) == 3
        assert all(result.geometry.geom_type == "Point")

    def test_single_part_unchanged(self):
        """Test that single-part geometries are unchanged."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[Point(0, 0), Point(1, 1)],
        )
        result = fix_explode_multipart(gdf)
        assert len(result) == 2

    def test_mixed_single_and_multi(self):
        """Test mixed single and multipart geometries."""
        p = Point(0, 0)
        mp = MultiPoint([(1, 1), (2, 2)])

        gdf = gpd.GeoDataFrame({"id": [1, 2]}, geometry=[p, mp])
        result = fix_explode_multipart(gdf)
        # Should have 1 point + 2 points from multipoint = 3 total
        assert len(result) == 3


class TestFixStripWhitespace:
    def test_strip_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        gdf = gpd.GeoDataFrame(
            {
                "id": [1, 2],
                "name": ["  Alice  ", "Bob  "],
                "city": ["  NYC", "LA  "],
            },
            geometry=[Point(0, 0), Point(1, 1)],
        )
        result = fix_strip_whitespace(gdf)
        assert result["name"].iloc[0] == "Alice"
        assert result["name"].iloc[1] == "Bob"
        assert result["city"].iloc[0] == "NYC"
        assert result["city"].iloc[1] == "LA"

    def test_preserve_internal_whitespace(self):
        """Test that internal whitespace is preserved."""
        gdf = gpd.GeoDataFrame(
            {"id": [1], "name": ["  New York City  "]},
            geometry=[Point(0, 0)],
        )
        result = fix_strip_whitespace(gdf)
        assert result["name"].iloc[0] == "New York City"

    def test_non_string_columns_unchanged(self):
        """Test that non-string columns are not modified."""
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2], "value": [10, 20]},
            geometry=[Point(0, 0), Point(1, 1)],
        )
        result = fix_strip_whitespace(gdf)
        assert list(result["id"]) == [1, 2]
        assert list(result["value"]) == [10, 20]

    def test_geometry_column_unchanged(self):
        """Test that geometry column is not modified."""
        gdf = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[Point(0, 0)],
        )
        result = fix_strip_whitespace(gdf)
        assert result.geometry.iloc[0].equals(Point(0, 0))

    def test_mixed_types_in_column(self):
        """Test columns with mixed types (strings and None)."""
        import pandas as pd

        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3], "name": ["  Alice  ", None, "  Bob"]},
            geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
        )
        result = fix_strip_whitespace(gdf)
        assert result["name"].iloc[0] == "Alice"
        # pandas coerces None in object columns to NaN — assert null-ness
        assert pd.isna(result["name"].iloc[1])
        assert result["name"].iloc[2] == "Bob"
