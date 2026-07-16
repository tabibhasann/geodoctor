# geodoctor 🩺

**A fast, opinionated linter for geospatial data — like `ruff`, but for maps.** Point it at any vector dataset (Shapefile, GeoJSON, GeoPackage, etc.) and get instant feedback on data quality — invalid geometries, broken CRS, schema violations, topology problems, and more. Auto-fixes what it safely can. Built for CI/CD pipelines.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/tabibhasann/geodoctor/actions/workflows/ci.yml/badge.svg)](https://github.com/tabibhasann/geodoctor/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen)](https://github.com/tabibhasann/geodoctor/actions)
[![Tests](https://img.shields.io/badge/tests-163%20passed-brightgreen)](https://github.com/tabibhasann/geodoctor/actions)

> **Pre-release:** `geodoctor` is not yet published to PyPI. Install from a checkout; PyPI commands below describe the intended release interface.


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

geodoctor combines CI-first design, safe auto-fixes, GitHub annotations,
pre-commit hooks, and broad vector-format support in one focused CLI.

**Configurable by design.** Every check can be enabled or disabled. Disable rules that don't apply to your data.

## Quickstart

```bash
git clone https://github.com/tabibhasann/geodoctor.git
cd geodoctor
python -m pip install -e .

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
- uses: tabibhasann/geodoctor@v0.2.0
  with:
    path: "data/*.gpkg"
    config: "geodoctor.yml"
```

Or run directly for GitHub annotations:

```yaml
- name: Check geodata
  run: |
    pip install "git+https://github.com/tabibhasann/geodoctor.git@v0.2.0"
    geodoctor check data/*.gpkg --format github --strict
```

Annotations appear inline on PR diffs — just like `ruff check`.

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/tabibhasann/geodoctor
    rev: v0.2.0
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

## Alternatives

| Tool | Type | Scope | CLI | CI/CD | Pre-commit | Auto-fix |
|------|------|-------|-----|-------|------------|----------|
| **geodoctor** | Linter | 25 checks across 5 categories (geometry, CRS, schema, structure, topology) | Yes | GitHub Action | Yes | 8 fixes |
| [goodtables](https://github.com/frictionlessdata/frictionless-py) | Validator | Tabular data validation (CSV/Excel) | Yes | Yes | No | No |
| [geojsonlint](https://github.com/JasonSanford/geojsonlint.com) | Linter | GeoJSON RFC 7946 compliance | CLI + web | No | No | No |
| [QGIS Validator](https://docs.qgis.org) | Desktop | Interactive geometry checking | No | No | No | Manual |
| [ogrinfo](https://gdal.org/programs/ogrinfo.html) | CLI | Format inspection + basic validation | Yes | No | No | No |

**Why geodoctor?** It's the only tool that combines CLI linting, CI integration, pre-commit hooks, and auto-fixes for geospatial data quality — purpose-built for the "shift-left" workflow.

## Roadmap

**What works now:**
- 25 checks across 5 categories (geometry, CRS, schema, structure, topology)
- 8 auto-fixes (make valid, drop empty/null, dedupe, reproject, explode multipart, strip whitespace, remove repeated vertices, normalize ring orientation)
- `check`, `fix`, `init`, `rules`, `diff` commands
- Text, JSON, HTML, GitHub annotations, and CI output formats
- `--strict` mode (promote warnings to errors)
- `--ci` flag for compact CI output
- Configurable rules via `geodoctor.yml`
- Progress indicators for large datasets

**Planned:**
- GeoParquet support
- Format-aware checks for raster datasets
- SARIF output for GitHub security tab

## Examples

### Validate a shapefile

```bash
geodoctor check data/cities.shp --strict
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
- uses: tabibhasann/geodoctor@v0.2.0
  with:
    path: data/boundaries.gpkg
    strict: true
```

### Pre-commit hook

```yaml
repos:
  - repo: https://github.com/tabibhasann/geodoctor
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
| `geodoctor check --strict` | Strict mode for CI (fail on warnings) |
| `geodoctor check --format json` | JSON output for CI integration |
| `geodoctor check --format github` | GitHub annotations output |
| `geodoctor fix <file> -o <output>` | Auto-fix common issues |
| `geodoctor init <file>` | Generate a starter geodoctor.yml |
| `geodoctor rules` | List all available checks |
| `geodoctor diff <a> <b>` | Compare two datasets |
| `geodoctor version` | Print version |

### Python API

```python
from geodoctor import validate, load_config

# Validate a file with defaults
report = validate('data.geojson')
print(report.has_errors, len(report.warnings), len(report.errors))

# Validate with a config
config = load_config('geodoctor.yml')
report = validate('data.shp', config=config)

# Access issues by severity
for issue in report.errors:
    print(f"  {issue.rule_id}: {issue.message}")
```

### GitHub Action

```yaml
- uses: tabibhasann/geodoctor@v0.2.0
  with:
    path: ./data
    strict: true
```

### Pre-commit Hook

```yaml
repos:
  - repo: https://github.com/tabibhasann/geodoctor
    rev: v0.2.0
    hooks:
      - id: geodoctor
```


## CLI Reference

```bash
geodoctor --help     # Show all available commands and options
geodoctor version    # Print the installed version
geodoctor check data.gpkg --strict --format json
geodoctor fix data.gpkg -o clean.gpkg --fixes make_valid,drop_empty_null
geodoctor init data.gpkg -o geodoctor.yml
geodoctor rules --json
geodoctor diff old.gpkg new.gpkg --format json
```

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).

---

⭐ Star [tabibhasann/geodoctor](https://github.com/tabibhasann/geodoctor) on GitHub if this helped you.
