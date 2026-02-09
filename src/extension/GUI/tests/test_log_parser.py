"""Unit tests for LogParser module."""

import pytest
from src.extension.GUI.log_parser import LogParser, ParseResult


class TestLogParser:
    """Tests for LogParser."""

    @pytest.fixture
    def parser(self):
        return LogParser()

    def test_phase_detection(self, parser):
        """Should detect all phase transitions."""
        cases = [
            ("Agent 1: Identifying", ("identify", "active")),
            ("Agent 2: Generating PyTest", ("implement", "active")),
            ("--- Iteration 1 ---", ("verify", "active")),
            ("Pipeline Complete!", ("verify", "completed")),
            ("Random text", None),
        ]
        for line, expected in cases:
            assert parser.parse(line).phase_update == expected

    def test_coverage_extraction(self, parser):
        """Should extract coverage from various formats."""
        assert parser.parse("Coverage: 95.2%").coverage == "95.2"
        assert parser.parse("coverage measured: 87.5%").coverage == "87.5"
        assert parser.parse("No coverage here").coverage is None

    def test_tests_extraction(self, parser):
        """Should extract test pass/fail counts."""
        result = parser.parse("Tests: 15/20 passed")
        assert result.tests == ("15", "20", 5)

        result = parser.parse("tests: 10/10 PASSED")
        assert result.tests == ("10", "10", 0)

    def test_scenarios_extraction(self, parser):
        """Should extract scenario counts."""
        assert parser.parse("Identified 45 scenarios").scenarios == "45"
        assert parser.parse("Scenarios: 30").scenarios == "30"

    def test_security_extraction(self, parser):
        """Should extract security issue info."""
        assert parser.parse("Security issues found: 3").security_issues == "3"
        assert parser.parse("Severe security issues: None").security_severity == "none"


class TestParseResult:
    """Tests for ParseResult dataclass."""

    def test_defaults_and_equality(self):
        """Should have None defaults and support equality."""
        result = ParseResult()
        assert all(v is None for v in [result.phase_update, result.coverage, result.tests])
        assert ParseResult(coverage="90") == ParseResult(coverage="90")
