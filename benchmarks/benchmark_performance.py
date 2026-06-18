"""Performance benchmarks for geodoctor.

Measures validation speed for different dataset sizes against the real
public API (`geodoctor.validate`).

Run with:    python benchmarks/benchmark_performance.py
"""

import statistics
import tempfile
import time
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, Polygon

from geodoctor import validate


class BenchmarkResult:
    """Container for a single timed benchmark."""

    def __init__(self, name: str, times: list[float], features: int):
        self.name = name
        self.times = times
        self.features = features
        self.mean = statistics.mean(times)
        self.median = statistics.median(times)
        self.throughput = features / self.mean if self.mean > 0 else float("inf")

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.features} features):\n"
            f"  Mean:   {self.mean * 1000:8.2f} ms\n"
            f"  Median: {self.median * 1000:8.2f} ms\n"
            f"  Rate:   {self.throughput:10.0f} features/sec"
        )


def _make_polygon_gdf(n: int) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "id": range(n),
            "name": [f"feature_{i}" for i in range(n)],
            "value": [i * 10 for i in range(n)],
            "geometry": [
                Polygon([(i, i), (i + 1, i), (i + 1, i + 1), (i, i + 1)])
                for i in range(n)
            ],
        },
        crs="EPSG:4326",
    )


def _make_point_gdf(n: int) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "id": range(n),
            "name": [f"pt_{i}" for i in range(n)],
            "value": [i for i in range(n)],
            "geometry": [Point(i, i) for i in range(n)],
        },
        crs="EPSG:4326",
    )


def benchmark_full_validation():
    print("\n" + "=" * 60)
    print("FULL VALIDATION BENCHMARK")
    print("=" * 60)

    for size in (100, 500, 1000, 5000):
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
            path = Path(f.name)
        try:
            _make_polygon_gdf(size).to_file(path, driver="GeoJSON")
            times = []
            for _ in range(5):
                t0 = time.perf_counter()
                validate(str(path))
                times.append(time.perf_counter() - t0)
            print(BenchmarkResult("validate()", times, size))
            print()
        finally:
            path.unlink(missing_ok=True)


def benchmark_geometry_only():
    print("\n" + "=" * 60)
    print("GEOMETRY-ONLY BENCHMARK")
    print("=" * 60)

    for size in (100, 1000, 5000):
        gdf = _make_polygon_gdf(size)
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            validate("__memory__", rule_ids=["invalid_geometry"])  # type: ignore[arg-type]
            times.append(time.perf_counter() - t0)
        # Avoid the noop above: do an in-memory path that actually runs checks
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
            path = Path(f.name)
        try:
            gdf.to_file(path, driver="GeoJSON")
            times = []
            for _ in range(5):
                t0 = time.perf_counter()
                validate(str(path), rule_ids=["invalid_geometry", "duplicate_geometry"])
                times.append(time.perf_counter() - t0)
            print(BenchmarkResult("geometry rules", times, size))
            print()
        finally:
            path.unlink(missing_ok=True)


def benchmark_crs_only():
    print("\n" + "=" * 60)
    print("CRS-ONLY BENCHMARK")
    print("=" * 60)

    for size in (100, 1000, 5000):
        gdf = _make_point_gdf(size)
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
            path = Path(f.name)
        try:
            gdf.to_file(path, driver="GeoJSON")
            times = []
            for _ in range(20):
                t0 = time.perf_counter()
                validate(str(path), rule_ids=["missing_crs", "unexpected_crs"])
                times.append(time.perf_counter() - t0)
            print(BenchmarkResult("crs rules", times, size))
            print()
        finally:
            path.unlink(missing_ok=True)


def run_all_benchmarks() -> None:
    print("\n" + "=" * 60)
    print("GEODOCTOR PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    benchmark_geometry_only()
    benchmark_crs_only()
    benchmark_full_validation()
    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print(f"Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    run_all_benchmarks()
