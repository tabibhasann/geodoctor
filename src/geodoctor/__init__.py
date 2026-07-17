"""geodoctor: a linter for geospatial data."""

from __future__ import annotations

from typing import TYPE_CHECKING

__version__ = "0.3.0"

__all__ = [
    "__version__",
    "validate",
    "load_config",
    "Report",
    "Issue",
    "GeodoctorConfig",
]

if TYPE_CHECKING:  # pragma: no cover
    from .config import GeodoctorConfig, load_config
    from .engine import validate
    from .report import Issue, Report


def __getattr__(name: str):  # noqa: PLR0911
    """Lazy attribute access for the public API.

    Importing this module must not eagerly import the entire CLI/renderer stack
    (those pull in rich/typer/yaml/jinja2). Heavy modules are loaded on demand.
    """
    if name in {"validate", "Report", "Issue"}:
        from .engine import validate as _validate
        from .report import Issue, Report

        return {"validate": _validate, "Report": Report, "Issue": Issue}[name]
    if name == "load_config":
        from .config import load_config
        return load_config
    raise AttributeError(f"module 'geodoctor' has no attribute {name!r}")
