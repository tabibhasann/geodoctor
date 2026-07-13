# Architecture

```
geodoctor
├── src/geodoctor/
│   ├── cli.py                 # Typer CLI entry point: check, fix, init, rules, diff, version
│   ├── engine.py              # validate() — runs registered checks on a dataset
│   ├── registry.py            # CHECKS/FIXES registries with @register_check, @register_fix decorators
│   ├── config.py              # GeodoctorConfig — loads geodoctor.yml, severity overrides
│   ├── dataset.py             # load_dataset() — geopandas loader (GeoJSON, FGB, GPKG, GeoParquet)
│   ├── rules/
│   │   ├── geometry.py        # Geometry validation checks (invalid, self-intersect, etc.)
│   │   ├── attributes.py      # Attribute checks (null, duplicate, type mismatch)
│   │   └── metadata.py        # Metadata/crs checks
│   ├── fixes/
│   │   └── geometry.py        # Auto-fix functions for geometry issues
│   └── renderers/
│       ├── console.py         # Rich table, JSON, HTML, SARIF, CI, GitHub renderers
│       └── __init__.py
├── tests/
│   ├── test_cli.py            # CLI integration tests (check, rules, diff, formats)
│   ├── fixtures/              # Test datasets (good.gpkg, invalid_geom.geojson, etc.)
│   └── test_engine.py         # Engine unit tests
├── .pre-commit-hooks.yaml     # Pre-commit hook integration
└── pyproject.toml
```

## Data Flow

```
User CLI input
    │
    ▼
cli.py (Typer)
    │
    ├──► check / diff / fix / rules / init
    │       │
    │       ▼
    │    engine.validate(path, config, layer, rule_ids)
    │       │
    │       ├──► dataset.load_dataset()  ← geopandas (GeoJSON/FGB/GPKG/Parquet)
    │       │
    │       ├──► registry.CHECKS         ← iterate active rules
    │       │       │
    │       │       └──► rule_fn(gdf, config) → issues[]
    │       │
    │       └──► Report(issues)
    │               │
    │               ▼
    │           renderers.console
    │               ├── render_console()  ← Rich table
    │               ├── render_json()     ← JSON
    │               ├── render_html()     ← HTML
    │               ├── render_sarif()    ← SARIF 2.1.0
    │               ├── render_ci()       ← compact CI
    │               └── render_github()   ← GitHub Actions format
    │
    └──► Output (stdout / file)
```

## Key Design Decisions

- **Registry pattern**: Rules are registered via decorators, making it trivial to add new checks.
- **Config-driven**: `geodoctor.yml` controls which rules are active and their severities.
- **Multiple output formats**: SARIF for security tools, CI for compact output, GitHub for PR annotations.
- **GeoParquet support**: Dataset loader detects `.parquet`/`.geoparquet` and uses `gpd.read_parquet`.
- **Diff command**: Runs checks on two datasets and shows the difference in issues.
