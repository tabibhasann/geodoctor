# geodoctor examples

Example configurations and usage patterns for geodoctor.

## Files

- [`basic_check.py`](basic_check.py) — Check a shapefile for common issues
- [`pre-commit.yaml`](pre-commit.yaml) — Use geodoctor as a pre-commit hook
- [`github_action.yml`](github_action.yml) — Run geodoctor in GitHub Actions
- [`config.toml`](config.toml) — Custom rules configuration

## Quick Start

```bash
# Check a shapefile
geodoctor check data/myfile.shp

# Check with verbose output
geodoctor check data/myfile.shp --verbose

# Check all files in a directory
geodoctor check data/ --recursive

# Output JSON report
geodoctor check data/myfile.shp --format json > report.json
```
