"""Tests for report dataclasses and severity logic."""

from geodoctor.report import Issue, Report


class TestIssue:
    def test_to_dict_basic(self):
        issue = Issue(
            rule_id="invalid_geom",
            severity="error",
            message="Self-intersecting polygon",
            layer="roads",
            feature_ids=[1, 2, 3],
        )
        d = issue.to_dict()
        assert d["rule_id"] == "invalid_geom"
        assert d["severity"] == "error"
        assert d["layer"] == "roads"
        assert d["total_affected"] == 3
        assert d["fix_available"] is False

    def test_to_dict_truncates_feature_ids(self):
        issue = Issue(
            rule_id="test",
            severity="warning",
            message="test",
            feature_ids=list(range(100)),
        )
        d = issue.to_dict()
        assert len(d["feature_ids"]) == 50
        assert d["total_affected"] == 100

    def test_defaults(self):
        issue = Issue(rule_id="r", severity="error", message="m")
        assert issue.layer == ""
        assert issue.feature_ids == []
        assert issue.count == 0
        assert issue.fix_available is False


class TestReport:
    def test_empty_report(self):
        r = Report()
        assert r.errors == []
        assert r.warnings == []
        assert r.infos == []
        assert r.has_errors is False

    def test_has_errors(self):
        r = Report(issues=[Issue("r", "error", "m")])
        assert r.has_errors is True
        assert len(r.errors) == 1
        assert len(r.warnings) == 0

    def test_has_warnings_only(self):
        r = Report(issues=[Issue("r", "warning", "m")])
        assert r.has_errors is False
        assert len(r.warnings) == 1

    def test_promoted_promotes_warnings_to_errors(self):
        r = Report(
            issues=[
                Issue("r1", "warning", "m1"),
                Issue("r2", "error", "m2"),
                Issue("r3", "info", "m3"),
            ],
            layers_checked=2,
            total_features=100,
        )
        promoted = r.promoted()
        assert len(promoted.issues) == 2
        assert all(i.severity == "error" for i in promoted.issues)
        assert promoted.layers_checked == 2
        assert promoted.total_features == 100

    def test_promoted_drops_info(self):
        r = Report(issues=[Issue("r", "info", "m")])
        promoted = r.promoted()
        assert len(promoted.issues) == 0
