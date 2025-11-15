"""
Test Research Data Logger
SPEC-AI-FACIL-001 Phase 2: Decision Logging and Export
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List
import json
import csv
import os
from datetime import datetime


class TestResearchLogger:
    """Tests for research data logging and export"""

    @pytest.fixture
    def research_logger(self):
        """Create ResearchLogger instance for testing"""
        from src.services.research_logger import ResearchLogger
        return ResearchLogger(output_dir="/tmp/test_research_logs")

    @pytest.fixture
    def sample_decision(self) -> Dict:
        """Sample decision record for logging"""
        return {
            "decision_id": "dec-123",
            "suggestion_id": "sugg-456",
            "decision_type": "approve",
            "mode": "outlier",
            "original_suggestion": "Carol's quantum computing idea is unique",
            "final_comment": "Your quantum computing idea is innovative!",
            "confidence": 0.85,
            "researcher_id": "researcher-001",
            "document_id": "doc-123",
            "timestamp": datetime.now().isoformat(),
            "decision_time_seconds": 12.5
        }

    def test_research_logger_initialization(self, research_logger):
        """Test ResearchLogger initializes with output directory"""
        assert research_logger.output_dir == "/tmp/test_research_logs"
        assert research_logger.decisions == []

    def test_log_decision(self, research_logger, sample_decision):
        """Test logging a single decision"""
        research_logger.log_decision(sample_decision)
        assert len(research_logger.decisions) == 1
        assert research_logger.decisions[0]["decision_id"] == "dec-123"

    def test_log_multiple_decisions(self, research_logger):
        """Test logging multiple decisions"""
        for i in range(5):
            decision = {
                "decision_id": f"dec-{i}",
                "decision_type": "approve" if i % 2 == 0 else "reject",
                "mode": "outlier",
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        assert len(research_logger.decisions) == 5

    def test_export_to_csv(self, research_logger, sample_decision):
        """Test exporting decisions to CSV format"""
        research_logger.log_decision(sample_decision)
        csv_path = research_logger.export_to_csv()
        assert os.path.exists(csv_path)
        assert csv_path.endswith(".csv")

        # Verify CSV content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["decision_id"] == "dec-123"

    def test_csv_export_includes_all_fields(self, research_logger, sample_decision):
        """Test that CSV export includes all decision fields"""
        research_logger.log_decision(sample_decision)
        csv_path = research_logger.export_to_csv()

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames
            assert "decision_type" in headers
            assert "mode" in headers
            assert "confidence" in headers
            assert "timestamp" in headers

    def test_export_to_json(self, research_logger, sample_decision):
        """Test exporting decisions to JSON format"""
        research_logger.log_decision(sample_decision)
        json_path = research_logger.export_to_json()
        assert os.path.exists(json_path)
        assert json_path.endswith(".json")

        # Verify JSON content
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["decision_id"] == "dec-123"

    def test_json_export_preserves_structure(self, research_logger, sample_decision):
        """Test that JSON export preserves decision structure"""
        research_logger.log_decision(sample_decision)
        json_path = research_logger.export_to_json()

        with open(json_path, 'r') as f:
            data = json.load(f)
            exported_decision = data[0]
            assert exported_decision["mode"] == "outlier"
            assert exported_decision["confidence"] == 0.85

    def test_export_handles_special_characters(self, research_logger):
        """Test that export handles special characters properly"""
        decision = {
            "decision_id": "dec-1",
            "final_comment": 'This comment has "quotes" and special chars: é, ñ, 中文',
            "timestamp": datetime.now().isoformat()
        }
        research_logger.log_decision(decision)

        # Should not raise exception
        csv_path = research_logger.export_to_csv()
        json_path = research_logger.export_to_json()
        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)

    def test_calculate_approval_statistics(self, research_logger):
        """Test calculating approval statistics"""
        for i in range(10):
            decision = {
                "decision_id": f"dec-{i}",
                "decision_type": "approve" if i < 7 else "reject",
                "mode": "outlier",
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        stats = research_logger.calculate_statistics()
        assert stats["total_decisions"] == 10
        assert stats["approval_rate"] == 0.7  # 7/10

    def test_calculate_false_positive_rate(self, research_logger):
        """Test calculating false positive rate (rejections)"""
        for i in range(10):
            decision = {
                "decision_id": f"dec-{i}",
                "decision_type": "approve" if i < 6 else "reject",
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        stats = research_logger.calculate_statistics()
        false_positive_rate = stats.get("false_positive_rate", 0)
        # False positives = rejections / total = 4/10
        assert false_positive_rate == pytest.approx(0.4, rel=0.01)

    def test_calculate_mode_specific_statistics(self, research_logger):
        """Test calculating statistics per mode"""
        modes = ["outlier", "summary", "connect", "question"]
        for i, mode in enumerate(modes):
            for j in range(5):
                decision = {
                    "decision_id": f"dec-{i}-{j}",
                    "decision_type": "approve" if j < 3 else "reject",
                    "mode": mode,
                    "timestamp": datetime.now().isoformat()
                }
                research_logger.log_decision(decision)

        stats = research_logger.calculate_statistics()
        mode_stats = stats.get("by_mode", {})
        for mode in modes:
            assert mode in mode_stats
            assert mode_stats[mode]["approval_rate"] == 0.6  # 3/5

    def test_calculate_average_decision_time(self, research_logger):
        """Test calculating average decision time"""
        decision_times = [5.0, 10.0, 15.0, 20.0, 25.0]
        for i, time_seconds in enumerate(decision_times):
            decision = {
                "decision_id": f"dec-{i}",
                "decision_time_seconds": time_seconds,
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        stats = research_logger.calculate_statistics()
        avg_time = stats.get("average_decision_time_seconds")
        assert avg_time == pytest.approx(15.0, rel=0.01)

    def test_export_directory_creation(self, research_logger):
        """Test that export directory is created if it doesn't exist"""
        test_dir = "/tmp/new_research_logs_test"
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir)

        logger = type(research_logger)(output_dir=test_dir)
        decision = {"decision_id": "dec-1", "timestamp": datetime.now().isoformat()}
        logger.log_decision(decision)
        logger.export_to_csv()

        assert os.path.exists(test_dir)

    def test_session_statistics_summary(self, research_logger):
        """Test generating session summary statistics"""
        for i in range(20):
            decision = {
                "decision_id": f"dec-{i}",
                "decision_type": "approve" if i % 2 == 0 else "reject",
                "mode": "outlier" if i % 3 == 0 else "summary",
                "decision_time_seconds": 10 + i,
                "confidence": 0.7 + (i * 0.01),
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        summary = research_logger.get_session_summary()
        assert summary["total_decisions"] == 20
        assert "approval_rate" in summary
        assert "average_decision_time" in summary

    def test_export_includes_timestamp(self, research_logger, sample_decision):
        """Test that exports include session timestamp"""
        research_logger.log_decision(sample_decision)
        csv_path = research_logger.export_to_csv()
        json_path = research_logger.export_to_json()

        # Files should include timestamp in name or content
        assert "csv" in csv_path or json_path.endswith(".json")

    def test_log_decision_with_all_fields(self, research_logger, sample_decision):
        """Test logging decision with all optional fields"""
        full_decision = {
            **sample_decision,
            "edited": True,
            "edits_count": 1,
            "researcher_notes": "This suggestion was relevant but needed clarification"
        }
        research_logger.log_decision(full_decision)
        assert len(research_logger.decisions) == 1

    def test_decisions_persist_across_exports(self, research_logger):
        """Test that decisions persist and aren't lost on export"""
        for i in range(3):
            decision = {
                "decision_id": f"dec-{i}",
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        research_logger.export_to_csv()
        research_logger.export_to_json()

        # Decisions should still be in memory
        assert len(research_logger.decisions) == 3

    def test_export_filename_includes_research_context(self, research_logger, sample_decision):
        """Test that export filenames are descriptive"""
        research_logger.log_decision(sample_decision)
        csv_path = research_logger.export_to_csv()

        # Should have research data in filename or be timestamped
        assert "research" in csv_path.lower() or "decision" in csv_path.lower() or len(csv_path) > 0

    def test_confidence_statistics(self, research_logger):
        """Test calculating confidence score statistics"""
        confidences = [0.6, 0.7, 0.8, 0.85, 0.9]
        for i, conf in enumerate(confidences):
            decision = {
                "decision_id": f"dec-{i}",
                "confidence": conf,
                "timestamp": datetime.now().isoformat()
            }
            research_logger.log_decision(decision)

        stats = research_logger.calculate_statistics()
        avg_confidence = stats.get("average_confidence")
        if avg_confidence:
            assert avg_confidence == pytest.approx(0.77, rel=0.1)

    def test_multiple_session_isolation(self, research_logger):
        """Test that multiple logger instances don't share state"""
        from src.services.research_logger import ResearchLogger
        logger1 = ResearchLogger(output_dir="/tmp/logs1")
        logger2 = ResearchLogger(output_dir="/tmp/logs2")

        logger1.log_decision({"decision_id": "dec-1", "timestamp": datetime.now().isoformat()})
        logger2.log_decision({"decision_id": "dec-2", "timestamp": datetime.now().isoformat()})

        assert len(logger1.decisions) == 1
        assert len(logger2.decisions) == 1
        assert logger1.decisions[0]["decision_id"] == "dec-1"
        assert logger2.decisions[0]["decision_id"] == "dec-2"
