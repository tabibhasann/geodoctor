"""Tests for the check/fix registry."""

from geodoctor.registry import CHECKS, FIXES, register_check, register_fix


class TestRegisterCheck:
    def setup_method(self):
        self._saved_checks = dict(CHECKS)
        CHECKS.clear()

    def teardown_method(self):
        CHECKS.clear()
        CHECKS.update(self._saved_checks)

    def test_register_basic(self):
        @register_check("test_rule", severity="warning", description="test")
        def my_check(gdf):
            return []

        assert "test_rule" in CHECKS
        assert CHECKS["test_rule"]["severity"] == "warning"
        assert CHECKS["test_rule"]["description"] == "test"
        assert CHECKS["test_rule"]["fix_id"] is None

    def test_register_with_fix_id(self):
        @register_check("rule_with_fix", fix_id="fix_1")
        def my_check(gdf):
            return []

        assert CHECKS["rule_with_fix"]["fix_id"] == "fix_1"

    def test_returns_original_function(self):
        @register_check("test")
        def my_check(gdf):
            return ["issue"]

        assert my_check(gdf=None) == ["issue"]


class TestRegisterFix:
    def setup_method(self):
        self._saved_fixes = dict(FIXES)
        FIXES.clear()

    def teardown_method(self):
        FIXES.clear()
        FIXES.update(self._saved_fixes)

    def test_register_basic(self):
        @register_fix("my_fix")
        def my_fix(gdf):
            return gdf

        assert "my_fix" in FIXES
        assert FIXES["my_fix"] is my_fix

    def test_returns_original_function(self):
        @register_fix("my_fix")
        def my_fix(gdf):
            return "fixed"

        assert my_fix(gdf=None) == "fixed"
