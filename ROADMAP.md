# Roadmap

`geodoctor` should be the dependable CI linter for geospatial datasets: clear checks, safe fixes, and no surprising data changes.

## Now

- Keep the current 25 checks and 8 fixes stable.
- `geodoctor diff` command for comparing two datasets (added in 0.2.0).
- Improve fixture coverage for GeoPackage, Shapefile, and GeoJSON edge cases.
- Keep CLI, JSON, and HTML report output consistent.

## Next

- Add more topology diagnostics for administrative boundaries and parcels.
- Add config presets for common data-quality profiles.
- Add SARIF output format for GitHub security tab.
- Add documentation examples for large-file workflows.

## Later

- Explore raster-adjacent checks only if vector linting remains focused.
- Add optional map previews for issue clusters.
- Add plugin hooks for domain-specific checks.

