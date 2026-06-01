# Contributing to geodoctor

## Getting started

1. Fork, clone, `pip install -e ".[dev]"`
2. Create a branch
3. Add checks or fixes
4. Run `ruff check src/ tests/ && pytest tests/ -v`
5. Submit PR

## AI-assisted maintenance

This project uses AI for first-pass PR review, test generation, and release-note drafting. All AI output is human-reviewed.

## Adding a new check

1. Create a function in `src/geodoctor/checks/` that takes `(gdf: GeoDataFrame, config: GeodoctorConfig) -> list[Issue]`
2. Decorate with `@register_check("rule_id", severity="error", description="...")`
3. Add tests using small in-memory GeoDataFrames
4. Register any associated fix with `@register_fix("fix_id")`
