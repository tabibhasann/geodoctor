# CHANGELOG

All notable changes to geodoctor are documented here.
This project follows [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-06-16

### Added
- Topology checks: `polygon_overlaps`, `polygon_gaps` (registered and active in the CLI)
- Composite GitHub Action (`.github/actions/geodoctor`) for running `geodoctor check` in CI
- `.pre-commit-hooks.yaml` so `geodoctor-check` can be installed as a pre-commit hook
- `geodoctor diff` command for comparing two datasets
- `--ci` flag on `geodoctor check` for compact CI output
- HTML report `output` flag now writes a file when provided
- `geodoctor rules` table now shows a Fix column
- `geodoctor init` generates per-field `nullable` flags from a real dataset
- Badges (CI, PyPI, license) in README

### Fixed
- Topology module is now registered into the runtime check registry (was dead code in 0.1.0)
- Strict mode (`--strict`) now promotes warnings without losing the original issues
- Progress bar total is now accurate to active rules only
- `out_of_bounds` only runs when the layer is in a geographic CRS
- `null_geometry` is now controllable by `geometry.allow_empty`
- Geometry defaults inverted to match the documented `geodoctor.yml` example (strict-by-default)
- `expected_crs` defaults to `EPSG:4326`
- `Issue` `feature_ids` no longer truncated to 50 when rendering JSON (truncation kept in `to_dict` output only)
- `mypy` is no longer `|| true` in CI (warnings now block)

### Changed
- `GeometryConfig` defaults are now: `allow_invalid=False`, `allow_empty=False`, `allow_duplicates=False`, `single_geometry_type=True`, `min_area_m2=1.0`
- `CRSConfig.expected` defaults to `EPSG:4326`
- Dropped duplicate `[project.optional-dependencies] dev` (kept PEP 735 `[dependency-groups] dev`)

## [0.1.0] - 2025-05-31

### Added
- Initial release
- Geometry checks: invalid, empty, null, duplicate, mixed types, sliver polygons, out of bounds
- CRS checks: missing, unexpected
- Schema checks: missing required, wrong type, null in non-nullable, out of range, not allowed, non-unique, regex, whitespace
- Structure checks: empty layer, long field names, unsafe identifiers
- CLI: `check`, `fix`, `init`, `rules`, `version` commands
- Config: `geodoctor.yml` with pydantic validation
- Renderers: text (rich), JSON, HTML (Jinja2)
- Auto-fixes: make_valid, drop_empty_null, dedupe, reproject, explode, strip_whitespace
