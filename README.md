# geodoctor 🩺

**The first comprehensive linter for geospatial data.** Point it at any vector dataset (Shapefile, GeoJSON, GeoPackage, etc.) and get instant feedback on data quality — invalid geometries, broken CRS, schema violations, topology problems, and more. Auto-fixes what it safely can. Built for CI/CD pipelines.

[![PyPI version](https://img.shields.io/pypi/v/geodoctor.svg)](https://pypi.org/project/geodoctor/)
[![Python](https://img.shields.io/pypi/pyversions/geodoctor.svg)](https://pypi.org/project/geodoctor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/tabibhasann/geodoctor/actions/workflows/ci.yml/badge.svg)](https://github.com/tabibhasann/geodoctor/actions/workflows/ci.yml)
[![Downloads](https://img.shields.io/pypi/dm/geodoctor.svg)](https://pypi.org/project/geodoctor/)

## Why geodoctor?

Geospatial data is notoriously error-prone. Invalid geometries break spatial operations, missing CRS causes projection errors, schema violations cause downstream failures. **geodoctor catches these problems before they reach production.**

- ✅ **25 automated checks** across 5 categories (geometry, CRS, schema, structure, topology)
- ✅ **8 auto-fixes** for common problems (make valid, drop empty/null geometries, dedupe, reproject, explode multipart, strip whitespace, remove repeated vertices, normalize ring orientation)
- ✅ **CI/CD ready** — GitHub Actions integration, exit codes, JSON output
- ✅ **Progress indicators** for large datasets
- ✅ **Rich HTML reports** with detailed issue breakdown
- ✅ **Configurable rules** — enable/disable checks, set severity levels

**Zero false positives.** Every check is configurable. Disable rules that don't apply to your data.

## Quickstart

```bash
pip install geodoctor

# Check a dataset
geodoctor check data.gpkg

# Generate a config from your data
geodoctor init data.gpkg

# Auto-fix issues
geodoctor fix data.gpkg -o clean.gpkg

# List available checks
geodoctor rules
```

## What it checks

| Category | Rules |
|----------|-------|
| **Geometry** | invalid, empty, null, duplicate, mixed types, sliver polygons, out-of-bounds coordinates, repeated vertices, zero-length segments, ring orientation |
| **CRS** | missing, unexpected |
| **Schema** | missing fields, wrong types, null in non-nullable, out of range, invalid enum, non-unique, regex mismatch |
| **Structure** | empty layer, long field names, unsafe identifiers |
| **Topology** | polygon gaps, polygon overlaps |

## CI integration

```yaml
# GitHub Actions
- uses: tabibhasann/geodoctor@v0
  with:
    path: "data/*.gpkg"
    config: "geodoctor.yml"
```

## Configuration

```yaml
# geodoctor.yml
crs:
  expected: "EPSG:4326"
  require: true
geometry:
  allow_invalid: false
  allow_empty: false
  single_geometry_type: true
schema:
  fields:
    id: { type: int, required: true, unique: true, nullable: false }
    name: { type: str, required: true }
    population: { type: int, min: 0 }
severity_overrides:
  duplicate_geometry: warning
```

## License

MIT — see [LICENSE](LICENSE).
