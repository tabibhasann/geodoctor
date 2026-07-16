"""Tests for HTML report generation."""

import tempfile
from pathlib import Path

from geodoctor.renderers.console import render_html as generate_html_report
from geodoctor.report import Issue, Report


class TestGenerateHtmlReport:
    def test_empty_report(self):
        """Test HTML generation for empty report."""
        report = Report(issues=[], total_features=0)
        html = generate_html_report(report)

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "0" in html  # Should show zero issues

    def test_report_with_issues(self):
        """Test HTML generation for report with issues."""
        issues = [
            Issue(
                rule_id="invalid_geometry",
                severity="error",
                message="Geometry is invalid",
                feature_ids=[1, 2],
            ),
            Issue(
                rule_id="missing_crs",
                severity="warning",
                message="CRS is not defined",
                feature_ids=[],
            ),
        ]

        report = Report(issues=issues, total_features=100)
        html = generate_html_report(report)

        assert "invalid_geometry" in html
        assert "missing_crs" in html
        assert "Geometry is invalid" in html
        assert "CRS is not defined" in html
        assert "error" in html
        assert "warning" in html

    def test_report_summary_statistics(self):
        """Test that summary statistics are included."""
        issues = [
            Issue(rule_id="test1", severity="error", message="Error 1", feature_ids=[1]),
            Issue(rule_id="test2", severity="error", message="Error 2", feature_ids=[2]),
            Issue(rule_id="test3", severity="warning", message="Warning 1", feature_ids=[]),
        ]

        report = Report(issues=issues, total_features=50)
        html = generate_html_report(report)

        # Should show counts
        assert "2" in html  # 2 errors
        assert "1" in html  # 1 warning
        assert "50" in html  # total features

    def test_report_with_details(self):
        """Test that issue details are included."""
        issues = [
            Issue(
                rule_id="invalid_geometry",
                severity="error",
                message="Geometry is invalid",
                feature_ids=[1],
            ),
        ]

        report = Report(issues=issues, total_features=10)
        html = generate_html_report(report)

        assert "invalid_geometry" in html

    def test_report_save_to_file(self):
        """Test saving HTML report to file."""
        issues = [
            Issue(
                rule_id="test",
                severity="info",
                message="Test message",
                feature_ids=[],
            ),
        ]

        report = Report(issues=issues, total_features=5)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)

        try:
            generate_html_report(report, output_path=output_path)

            # Check file was created
            assert output_path.exists()

            # Check file content
            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "test" in content
            assert "Test message" in content
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_report_html_valid_structure(self):
        """Test that generated HTML has valid structure."""
        report = Report(issues=[], total_features=0)
        html = generate_html_report(report)

        # Check for required HTML elements
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert "<title>" in html
        assert "</title>" in html

    def test_report_includes_metadata(self):
        """Test that report includes metadata like feature count."""
        report = Report(issues=[], total_features=100)
        html = generate_html_report(report)

        # Should mention total features
        assert "100" in html

    def test_report_css_included(self):
        """Test that CSS styles are included."""
        report = Report(issues=[], total_features=0)
        html = generate_html_report(report)

        # Should have style tag or link to CSS
        assert "<style>" in html or "<link" in html

    def test_report_severity_color_coding(self):
        """Test that different severities have different styling."""
        issues = [
            Issue(rule_id="error1", severity="error", message="Error", feature_ids=[]),
            Issue(rule_id="warning1", severity="warning", message="Warning", feature_ids=[]),
            Issue(rule_id="info1", severity="info", message="Info", feature_ids=[]),
        ]

        report = Report(issues=issues, total_features=10)
        html = generate_html_report(report)

        # All severities should be present
        assert "error" in html.lower()
        assert "warning" in html.lower()
        assert "info" in html.lower()

    def test_report_large_number_of_issues(self):
        """Test report with many issues."""
        # Create 100 issues
        issues = [
            Issue(
                rule_id=f"rule_{i}",
                severity="error",
                message=f"Issue {i}",
                feature_ids=[i],
            )
            for i in range(100)
        ]

        report = Report(issues=issues, total_features=1000)
        html = generate_html_report(report)

        # Should handle large number of issues
        assert len(html) > 1000  # Should be substantial
        assert "100" in html  # Should show count

    def test_report_with_unicode(self):
        """Test report with unicode characters."""
        issues = [
            Issue(
                rule_id="unicode_test",
                severity="error",
                message="Invalid geometry: 中文测试 🚫",
                feature_ids=[1],
            ),
        ]

        report = Report(issues=issues, total_features=10)
        html = generate_html_report(report)

        # Should handle unicode properly
        assert "unicode_test" in html
        assert "Invalid geometry" in html

    def test_report_escapes_untrusted_issue_fields(self):
        """Dataset-derived issue content must not become executable HTML."""
        issue = Issue(
            rule_id='<img src=x onerror="alert(1)">',
            severity='error" onclick="alert(2)',  # type: ignore[arg-type]
            layer="<svg onload=alert(3)>",
            message="<script>alert(4)</script>",
            feature_ids=[1],
        )

        html = generate_html_report(Report(issues=[issue], total_features=1))

        assert "<img src=x" not in html
        assert "<svg onload" not in html
        assert "<script>alert(4)</script>" not in html
        assert "&lt;img src=x" in html
        assert "&lt;svg onload=alert(3)&gt;" in html
        assert "&lt;script&gt;alert(4)&lt;/script&gt;" in html
        assert 'class="error&#34; onclick=&#34;alert(2)"' in html
