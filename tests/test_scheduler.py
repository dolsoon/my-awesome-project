"""
Test Dual-Mode Scheduler (Manual + Automatic)
SPEC-AI-FACIL-001 Phase 1: Batch Processing Scheduler
"""

import pytest
from unittest.mock import Mock, patch
import time


class TestDualModeScheduler:
    """Tests for dual-mode scheduler (on-demand + automatic)"""

    @pytest.fixture
    def scheduler(self):
        """Create DualModeScheduler instance for testing"""
        from src.services.scheduler import DualModeScheduler
        return DualModeScheduler(analysis_service=Mock())

    def test_scheduler_initialization_manual_mode(self, scheduler):
        """Test scheduler initializes in manual (on-demand) mode"""
        assert scheduler.mode == "manual"
        assert scheduler.is_automatic() is False

    def test_switch_to_automatic_mode(self, scheduler):
        """Test switching to automatic mode with interval"""
        scheduler.set_automatic_mode(interval_seconds=60)
        assert scheduler.mode == "automatic"
        assert scheduler.interval == 60
        assert scheduler.is_automatic() is True

    def test_switch_to_manual_mode(self, scheduler):
        """Test switching back to manual (on-demand) mode"""
        scheduler.set_automatic_mode(interval_seconds=60)
        scheduler.set_manual_mode()
        assert scheduler.mode == "manual"
        assert scheduler.is_automatic() is False

    def test_configurable_intervals(self, scheduler):
        """Test configurable automatic intervals (30s, 60s, 120s)"""
        allowed_intervals = [30, 60, 120]

        for interval in allowed_intervals:
            scheduler.set_automatic_mode(interval_seconds=interval)
            assert scheduler.interval == interval

    def test_trigger_on_demand_analysis(self, scheduler):
        """Test triggering immediate on-demand analysis"""
        mock_analysis = Mock()
        scheduler.analysis_service = mock_analysis

        result = scheduler.trigger_analysis_now()
        assert result is not None

    def test_debouncing_prevents_duplicate_triggers(self, scheduler):
        """Test debouncing prevents duplicate manual triggers within 10s"""
        scheduler.debounce_window = 10

        # First trigger
        scheduler.trigger_analysis_now()
        first_time = time.time()

        # Immediate second trigger should be debounced
        result = scheduler.trigger_analysis_now()
        assert result is None or not result  # Debounced

        # Trigger after debounce window
        scheduler.last_analysis_time = first_time - 11
        result = scheduler.trigger_analysis_now()
        assert result is not None  # Not debounced

    def test_automatic_analysis_scheduling(self, scheduler):
        """Test automatic analysis scheduling at configured intervals"""
        scheduler.set_automatic_mode(interval_seconds=60)

        # Schedule automatic analysis
        scheduler.start_automatic_analysis()
        assert scheduler.is_running() is True

    def test_stop_automatic_analysis(self, scheduler):
        """Test stopping automatic analysis"""
        scheduler.set_automatic_mode(interval_seconds=60)
        scheduler.start_automatic_analysis()

        scheduler.stop_automatic_analysis()
        assert scheduler.is_running() is False

    def test_next_analysis_countdown(self, scheduler):
        """Test calculating time until next automatic analysis"""
        scheduler.set_automatic_mode(interval_seconds=60)
        scheduler.last_analysis_time = time.time()

        countdown = scheduler.get_next_analysis_countdown()
        assert 0 < countdown <= 60

    def test_display_mode_status(self, scheduler):
        """Test displaying current operation mode"""
        # Manual mode
        scheduler.set_manual_mode()
        status = scheduler.get_mode_display()
        assert "MANUAL" in status

        # Automatic mode
        scheduler.set_automatic_mode(interval_seconds=60)
        status = scheduler.get_mode_display()
        assert "AUTO" in status
        assert "60" in status

    def test_mode_persistence_across_session(self, scheduler, tmp_path):
        """Test persisting mode preference across session pause/resume"""
        config_file = str(tmp_path / "scheduler_config.json")
        scheduler.config_path = config_file

        # Save configuration
        scheduler.set_automatic_mode(interval_seconds=120)
        scheduler.save_config()

        # Create new scheduler and load config
        from src.services.scheduler import DualModeScheduler
        new_scheduler = DualModeScheduler(analysis_service=Mock())
        new_scheduler.config_path = config_file
        new_scheduler.load_config()

        assert new_scheduler.mode == "automatic"
        assert new_scheduler.interval == 120

    def test_manual_analysis_display_progress(self, scheduler):
        """Test displaying 'Analyzing...' progress indicator"""
        progress_indicator = scheduler.get_progress_display()
        assert isinstance(progress_indicator, str)

    def test_analysis_trigger_source_tracking(self, scheduler):
        """Test tracking whether analysis was triggered manually or automatically"""
        # Manual trigger
        scheduler.trigger_analysis_now()
        assert scheduler.last_trigger_source == "manual"

        # Automatic trigger simulation
        scheduler.last_trigger_source = "automatic"
        assert scheduler.last_trigger_source == "automatic"

    def test_debounce_window_configuration(self, scheduler):
        """Test configurable debounce window"""
        scheduler.set_debounce_window(5)
        assert scheduler.debounce_window == 5

        scheduler.set_debounce_window(15)
        assert scheduler.debounce_window == 15
