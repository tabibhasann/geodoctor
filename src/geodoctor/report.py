"""Issue report dataclasses and severity definitions."""

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["error", "warning", "info"]


@dataclass
class Issue:
    rule_id: str
    severity: Severity
    message: str
    layer: str = ""
    feature_ids: list[int] = field(default_factory=list)
    count: int = 0
    fix_available: bool = False

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "layer": self.layer,
            "feature_ids": self.feature_ids[:50],
            "total_affected": len(self.feature_ids),
            "fix_available": self.fix_available,
        }


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)
    layers_checked: int = 0
    total_features: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "info"]

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def promoted_errors(self) -> list[Issue]:
        """Return issues with warnings promoted to error (strict mode)."""
        return [
            Issue(
                rule_id=i.rule_id,
                severity="error",
                message=i.message,
                layer=i.layer,
                feature_ids=i.feature_ids,
                count=i.count,
                fix_available=i.fix_available,
            )
            for i in self.issues
            if i.severity != "info"
        ]
