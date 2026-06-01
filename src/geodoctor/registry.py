"""Check registry with decorator-based registration."""

from typing import Any, Callable

from .report import Issue, Severity

CHECKS: dict[str, dict[str, Any]] = {}
FIXES: dict[str, Callable] = {}


def register_check(
    rule_id: str,
    severity: Severity = "error",
    description: str = "",
    fix_id: str | None = None,
) -> Callable:
    """Decorator to register a check function."""

    def deco(fn: Callable) -> Callable:
        CHECKS[rule_id] = {
            "fn": fn,
            "severity": severity,
            "description": description,
            "fix_id": fix_id,
        }
        return fn

    return deco


def register_fix(fix_id: str) -> Callable:
    """Decorator to register a fix function."""

    def deco(fn: Callable) -> Callable:
        FIXES[fix_id] = fn
        return fn

    return deco
