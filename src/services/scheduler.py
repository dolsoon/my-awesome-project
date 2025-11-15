"""
Dual-Mode Scheduler
Supports both on-demand (manual) and automatic (configurable interval) analysis
"""

import time
import json
import os
from typing import Optional, Dict


class DualModeScheduler:
    """Manages dual-mode scheduling (manual on-demand + automatic intervals)"""

    def __init__(self, analysis_service):
        """Initialize scheduler in manual mode"""
        self.analysis_service = analysis_service
        self.mode: str = "manual"  # "manual" or "automatic"
        self.interval: int = 60  # seconds
        self.debounce_window: int = 10  # seconds
        self.is_running_flag: bool = False
        self.last_analysis_time: float = 0
        self.last_trigger_source: str = "manual"
        self.config_path: str = "scheduler_config.json"

    def set_automatic_mode(self, interval_seconds: int) -> None:
        """Switch to automatic mode with specified interval"""
        self.mode = "automatic"
        self.interval = interval_seconds

    def set_manual_mode(self) -> None:
        """Switch to manual (on-demand) mode"""
        self.mode = "manual"

    def is_automatic(self) -> bool:
        """Check if in automatic mode"""
        return self.mode == "automatic"

    def trigger_analysis_now(self) -> Optional[Dict]:
        """Trigger immediate on-demand analysis with debouncing"""
        current_time = time.time()

        # Check debounce window
        if current_time - self.last_analysis_time < self.debounce_window:
            return None  # Debounced

        self.last_analysis_time = current_time
        self.last_trigger_source = "manual"
        return {"status": "triggered", "source": "manual"}

    def start_automatic_analysis(self) -> None:
        """Start automatic analysis loop"""
        self.is_running_flag = True
        self.last_analysis_time = time.time()

    def stop_automatic_analysis(self) -> None:
        """Stop automatic analysis"""
        self.is_running_flag = False

    def is_running(self) -> bool:
        """Check if automatic analysis is running"""
        return self.is_running_flag

    def get_next_analysis_countdown(self) -> int:
        """Get seconds until next automatic analysis"""
        current_time = time.time()
        elapsed = current_time - self.last_analysis_time
        remaining = max(0, self.interval - int(elapsed))
        return remaining

    def get_mode_display(self) -> str:
        """Get display string for current mode"""
        if self.mode == "manual":
            return "[MODE: MANUAL]"
        else:
            return f"[AUTO: {self.interval}s]"

    def save_config(self) -> None:
        """Save scheduler configuration to disk"""
        config = {
            "mode": self.mode,
            "interval": self.interval,
            "debounce_window": self.debounce_window,
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def load_config(self) -> None:
        """Load scheduler configuration from disk"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
            self.mode = config.get("mode", "manual")
            self.interval = config.get("interval", 60)
            self.debounce_window = config.get("debounce_window", 10)

    def get_progress_display(self) -> str:
        """Get progress indicator display"""
        return "Analyzing..."

    def set_debounce_window(self, window_seconds: int) -> None:
        """Set debounce window for manual triggers"""
        self.debounce_window = window_seconds
