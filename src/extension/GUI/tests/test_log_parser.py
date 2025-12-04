"""Unit tests for the LogParser module."""

import pytest
from src.extension.GUI.log_parser import LogParser, ParseResult


class TestLogParser:
    """Tests for LogParser class."""

    @pytest.fixture
    def parser(self):
        """Create a LogParser instance."""
        return LogParser()

    # ==================== Phase Detection Tests ====================
    class TestPhaseDetection:
        """Tests for phase detection."""

        @pytest.fixture
        def parser(self):
            return LogParser()

        def test_detect_identify_phase_active(self, parser):
            """Should detect Agent 1 identifying phase."""
            result = parser.parse("🔍 Agent 1: Identifying test scenarios...")
            assert result.phase_update == ("identify", "active")

        def test_detect_identify_alternative(self, parser):
            """Should detect alternative identify trigger."""
            result = parser.parse("Identifying test scenarios for module")
            assert result.phase_update == ("identify", "active")

        def test_detect_implement_phase(self, parser):
            """Should detect Agent 2 generating phase."""
            result = parser.parse("🧪 Agent 2: Generating PyTest test code...")
            assert result.phase_update is not None
            # First match for "identify completed", second for "implement active"

        def test_detect_verify_phase(self, parser):
            """Should detect iteration/running tests phase."""
            result = parser.parse("--- Iteration 1 ---")
            assert result.phase_update is not None

        def test_detect_completion(self, parser):
            """Should detect pipeline completion."""
            result = parser.parse("✅ Pipeline Complete!")
            assert result.phase_update == ("verify", "completed")

        def test_no_phase_for_random_line(self, parser):
            """Should return None for unrelated lines."""
            result = parser.parse("Some random log message")
            assert result.phase_update is None

    # ==================== Coverage Tests ====================
    class TestCoverageExtraction:
        """Tests for coverage extraction."""

        @pytest.fixture
        def parser(self):
            return LogParser()

        def test_extract_coverage_standard(self, parser):
            """Should extract standard coverage format."""
            result = parser.parse("   Coverage: 95.2%")
            assert result.coverage == "95.2"

        def test_extract_coverage_measured(self, parser):
            """Should extract 'measured' coverage format."""
            result = parser.parse("   Actual coverage measured: 87.5%")
            assert result.coverage == "87.5"

        def test_extract_coverage_integer(self, parser):
            """Should extract integer coverage."""
            result = parser.parse("Coverage: 100%")
            assert result.coverage == "100"

        def test_no_coverage_in_unrelated_line(self, parser):
            """Should return None for lines without coverage."""
            result = parser.parse("Running tests...")
            assert result.coverage is None

    # ==================== Tests Extraction Tests ====================
    class TestTestsExtraction:
        """Tests for test results extraction."""

        @pytest.fixture
        def parser(self):
            return LogParser()

        def test_extract_tests_passed(self, parser):
            """Should extract test pass/fail counts."""
            result = parser.parse("   Tests: 15/20 passed")
            assert result.tests == ("15", "20", 5)

        def test_extract_tests_all_passed(self, parser):
            """Should handle all tests passing."""
            result = parser.parse("Tests: 10/10 passed")
            assert result.tests == ("10", "10", 0)

        def test_extract_tests_case_insensitive(self, parser):
            """Should be case insensitive."""
            result = parser.parse("tests: 5/8 PASSED")
            assert result.tests == ("5", "8", 3)

    # ==================== Scenarios Tests ====================
    class TestScenariosExtraction:
        """Tests for scenarios extraction."""

        @pytest.fixture
        def parser(self):
            return LogParser()

        def test_extract_identified_scenarios(self, parser):
            """Should extract identified scenarios count."""
            result = parser.parse("   Identified 45 scenarios (45 unique)")
            assert result.scenarios == "45"

        def test_extract_scenarios_summary(self, parser):
            """Should extract scenarios from summary."""
            result = parser.parse("   Scenarios: 30")
            assert result.scenarios == "30"

    # ==================== Security Tests ====================
    class TestSecurityExtraction:
        """Tests for security issues extraction."""

        @pytest.fixture
        def parser(self):
            return LogParser()

        def test_extract_security_issues_found(self, parser):
            """Should extract security issues count."""
            result = parser.parse("   🔒 Security issues found: 3")
            assert result.security_issues == "3"

        def test_extract_minor_security(self, parser):
            """Should extract minor security issues."""
            result = parser.parse("   ℹ️  Minor security issues (low/medium): 2")
            assert result.security_severity == "2"

        def test_extract_severe_none(self, parser):
            """Should detect no severe issues."""
            result = parser.parse("   Severe security issues: None")
            assert result.security_severity == "none"

        def test_extract_severe_count(self, parser):
            """Should extract severe issue count."""
            result = parser.parse("   Severe security issues: 1")
            assert result.security_severity == "1"

    # ==================== Integration Tests ====================
    class TestIntegration:
        """Integration tests for full line parsing."""

        @pytest.fixture
        def parser(self):
            return LogParser()

        def test_parse_empty_line(self, parser):
            """Should handle empty lines gracefully."""
            result = parser.parse("")
            assert result == ParseResult()

        def test_parse_multiple_values(self, parser):
            """Should extract multiple values from rich line."""
            # Note: actual pipeline output doesn't have multiple on one line,
            # but parser should handle it
            result = parser.parse("Coverage: 90% and Security issues found: 2")
            assert result.coverage == "90"
            assert result.security_issues == "2"


# ==================== ParseResult Tests ====================
class TestParseResult:
    """Tests for ParseResult dataclass."""

    def test_default_values(self):
        """Should have None defaults."""
        result = ParseResult()
        assert result.phase_update is None
        assert result.coverage is None
        assert result.tests is None
        assert result.scenarios is None
        assert result.security_issues is None
        assert result.security_severity is None

    def test_equality(self):
        """Should support equality comparison."""
        r1 = ParseResult(coverage="90")
        r2 = ParseResult(coverage="90")
        assert r1 == r2
