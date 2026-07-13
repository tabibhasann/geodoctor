# geodoctor 🩺

**A fast, opinionated linter for geospatial data — like `ruff`, but for maps.** Point it at any vector dataset (Shapefile, GeoJSON, GeoPackage, etc.) and get instant feedback on data quality — invalid geometries, broken CRS, schema violations, topology problems, and more. Auto-fixes what it safely can. Built for CI/CD pipelines.

[![PyPI version](https://img.shields.io/pypi/v/geodoctor.svg)](https://pypi.org/project/geodoctor/)
[![Python](https://img.shields.io/pypi/pyversions/geodoctor.svg)](https://pypi.org/project/geodoctor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/tabibhasann/geodoctor/actions/workflows/ci.yml/badge.svg)](https://github.com/tabibhasann/geodoctor/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen)](https://github.com/tabibhasann/geodoctor/actions)
[![Tests](https://img.shields.io/badge/tests-160%2B%20passed-brightgreen)](https://github.com/tabibhasann/geodoctor/actions)
[![Downloads](https://img.shields.io/pypi/dm/geodoctor.svg)](https://pypi.org/project/geodoctor/)


**Demo:** Example output and CI integration: see [Examples](#examples) above

## Why geodoctor?

Geospatial data is notoriously error-prone. Invalid geometries break spatial operations, missing CRS causes projection errors, schema violations cause downstream failures. **geodoctor catches these problems before they reach production.**

- ✅ **25 automated checks** across 5 categories (geometry, CRS, schema, structure, topology)
- ✅ **8 auto-fixes** for common problems (make valid, drop empty/null geometries, dedupe, reproject, explode multipart, strip whitespace, remove repeated vertices, normalize ring orientation)
- ✅ **CI/CD ready** — GitHub Actions integration, exit codes, JSON output
- ✅ **Progress indicators** for large datasets
- ✅ **Rich HTML reports** with detailed issue breakdown
- ✅ **Configurable rules** — enable/disable checks, set severity levels

### How it compares

| Tool | Focus | CI-first | Auto-fix | GitHub annotations | Pre-commit | Formats |
|---|---|---|---|---|---|---|
| **geodoctor** | Lint + fix | ✅ | ✅ 8 fixes | ✅ | ✅ | Shapefile, GeoJSON, GPKG, FGB, GeoParquet |
| [geoassert](https://github.com/geoassert/geoassert) | Contract validation | ✅ | ❌ | ✅ | ❌ | GeoParquet, PostGIS, BigQuery |
| [geolint](https://github.com/geolint/geolint) | Full CLI + web UI | ✅ | ✅ | ❌ | ❌ | GPKG, GeoJSON |
| [geojson-validator](https://www.npmjs.com/package/geojson-validator) | GeoJSON only | ❌ | ✅ | ❌ | ❌ | GeoJSON |
| [GeoQA](https://github.com/geoqa/geoqa) | Profiling + reports | ❌ | ✅ | ❌ | ❌ | Shapefile, GeoJSON, GPKG |

geodoctor is the only tool that combines CI-first design, auto-fix, GitHub
annotations, pre-commit hooks, and broad format support in a single `pip install`.

**Configurable by design.** Every check can be enabled or disabled. Disable rules that don't apply to your data.

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

### GitHub Actions

```yaml
- uses: tabibhasann/geodoctor@v0
  with:
    path: "data/*.gpkg"
    config: "geodoctor.yml"
```

Or run directly for GitHub annotations:

```yaml
- name: Check geodata
  run: |
    pip install geodoctor
    geodoctor check data/*.gpkg --format github --strict
```

Annotations appear inline on PR diffs — just like `ruff check`.

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/tabibhasann/geodoctor
    rev: v0.1.0
    hooks:
      - id: geodoctor
        args: ["check", "--strict"]
        files: \.(geojson|gpkg|shp|fgb)$
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

## Roadmap

**What works now:**
- 25 checks across 5 categories (geometry, CRS, schema, structure, topology)
- 8 auto-fixes (make valid, drop empty/null, dedupe, reproject, explode multipart, strip whitespace, remove repeated vertices, normalize ring orientation)
- `check`, `fix`, `init`, `rules` commands
- Text, JSON, HTML, and GitHub annotations output formats
- `--strict` mode (promote warnings to errors)
- Configurable rules via `geodoctor.yml`
- Progress indicators for large datasets

**Planned:**
- GeoParquet support
- `geodoctor check --ci` mode (exit non-zero on warnings, not just errors)
- Format-aware checks for raster datasets
- SARIF output for GitHub security tab
- `geodoctor diff` command (compare two datasets)

## Examples

### Validate a shapefile

```bash
geodoctor check --input data/cities.shp --strict
```

```
✓ CRS check: EPSG:4326 (WGS 84)
✗ Geometry check: 3 invalid geometries found
  → Feature 42: self-intersecting polygon
  → Feature 87: ring not closed
  → Feature 103: duplicate vertices
⚠ Field check: missing required field 'population'
✓ Topology check: no gaps or overlaps

Summary: 1 error, 1 warning, 2 checks passed
```

### Lint a GeoPackage in CI

```yaml
- uses: tabibhasan/geodoctor@v0.2.0
  with:
    input: data/boundaries.gpkg
    strict: true
```

### Pre-commit hook

```yaml
repos:
  - repo: https://github.com/tabibhasan/geodoctor
    rev: v0.2.0
    hooks:
      - id: geodoctor
        args: [--strict]
```

## API

### CLI Commands

| Command | Description |
|---------|-------------|
| `geodoctor check <file>` | Validate a geospatial data file |
| `geodoctor check <dir>` | Validate all files in a directory |
| `geodoctor check --strict` | Strict mode for CI (fail on warnings) |
| `geodoctor check --format json` | JSON output for CI integration |
| `geodoctor fix <file>` | Auto-fix common issues |

### Python API

```python
from geodoctor import check, fix
from geodoctor.rules import CRSRule, GeometryRule

# Validate a file
result = check('data.geojson')
print(result.passed, result.warnings, result.errors)

# Validate with specific rules
result = check('data.shp', rules=[CRSRule(), GeometryRule()])

# Auto-fix
fixed = fix('data.geojson')
```

### GitHub Action

```yaml
- uses: tabibhasann/geodoctor@v1
  with:
    path: ./data
    strict: true
```

### Pre-commit Hook

```yaml
repos:
  - repo: https://github.com/tabibhasann/geodoctor
    rev: v1.0.0
    hooks:
      - id: geodoctor
```


## CLI Reference

\`\`\`bash
geodoctor --help     # Show all available commands and options
geodoctor --version  # Print the installed version
\`\`\`

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).

---

⭐ Star [tabibhasann/geodoctor](https://github.com/tabibhasann/geodoctor) on GitHub if this helped you.
