"""Unit tests for PipelineRunner module."""

from unittest.mock import Mock, patch

import pytest

from src.extension.GUI.pipeline_runner import PipelineRunner


class TestPipelineRunner:
    """Tests for PipelineRunner class."""

    @pytest.fixture
    def runner(self, tmp_path):
        """Create a PipelineRunner with mock script."""
        script = tmp_path / "script.py"
        script.write_text("print('test')")
        return PipelineRunner(script, Mock(), Mock())

    def test_init_state(self, runner):
        """Should initialize with correct state."""
        assert runner.process is None
        assert runner.is_running is False

    def test_start_validation(self, runner, tmp_path):
        """start() should validate paths and running state."""
        # Already running
        runner.is_running = True
        assert runner.start("/any") is False

        # Invalid paths
        runner.is_running = False
        assert runner.start("/nonexistent") is False

    def test_start_success(self, runner, tmp_path):
        """start() should set is_running on valid paths."""
        target = tmp_path / "target"
        target.mkdir()
        with patch.object(runner, "_run"):
            assert runner.start(str(target)) is True
            assert runner.is_running is True

    def test_stop(self, runner):
        """stop() should terminate process and set is_running."""
        runner.is_running = True
        runner.process = Mock()

        runner.stop()

        assert runner.is_running is False
        runner.process.terminate.assert_called_once()


class TestSendInput:
    """Tests for send_input method."""

    @pytest.fixture
    def active_runner(self, tmp_path):
        """Runner with active process."""
        script = tmp_path / "script.py"
        script.touch()
        runner = PipelineRunner(script, Mock(), Mock())
        runner.is_running = True
        runner.process = Mock()
        runner.process.stdin = Mock()
        return runner

    def test_send_input_validation(self, tmp_path):
        """send_input() should return False for invalid states."""
        script = tmp_path / "script.py"
        script.touch()
        runner = PipelineRunner(script, Mock(), Mock())

        # Not running
        assert runner.send_input("test") is False

        # No process
        runner.is_running = True
        runner.process = None
        assert runner.send_input("test") is False

    def test_send_input_success(self, active_runner):
        """send_input() should write and flush on success."""
        assert active_runner.send_input("cmd") is True
        active_runner.process.stdin.write.assert_called_with("cmd\n")
        active_runner.process.stdin.flush.assert_called_once()

    def test_send_input_handles_errors(self, active_runner):
        """send_input() should handle pipe errors gracefully."""
        active_runner.process.stdin.write.side_effect = BrokenPipeError()
        assert active_runner.send_input("test") is False
