# CHANGELOG

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
