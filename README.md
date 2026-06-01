# geodoctor 🩺

> The linter for geospatial data. Point it at a Shapefile/GeoJSON/GeoPackage and it finds invalid geometries, broken CRS, schema violations, and topology problems — then auto-fixes what it safely can. Runs in CI.

[![PyPI version](https://img.shields.io/pypi/v/geodoctor.svg)](https://pypi.org/project/geodoctor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
| **Geometry** | invalid, empty, null, duplicate, mixed types, sliver polygons, out-of-bounds coordinates |
| **CRS** | missing, unexpected, geographic vs projected |
| **Schema** | missing fields, wrong types, null in non-nullable, out of range, invalid enum, non-unique, regex mismatch |
| **Structure** | empty layer, long field names, unsafe identifiers |

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
