"""
Research Data Logger
SPEC-AI-FACIL-001 Phase 2: Decision logging and export (CSV/JSON)
Minimal implementation for TDD GREEN phase
"""

from typing import Dict, List, Any, Optional
import csv
import json
import os
from datetime import datetime


class ResearchLogger:
    """Logs and exports research decision data"""

    def __init__(self, output_dir: str = "./research_logs"):
        """Initialize ResearchLogger"""
        self.output_dir = output_dir
        self.decisions: List[Dict[str, Any]] = []

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def log_decision(self, decision: Dict[str, Any]) -> None:
        """Log a single decision"""
        self.decisions.append(decision)

    def export_to_csv(self) -> str:
        """Export decisions to CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(self.output_dir, f"research_decisions_{timestamp}.csv")

        if not self.decisions:
            return csv_path

        # Get all fieldnames from all decisions
        fieldnames = set()
        for decision in self.decisions:
            fieldnames.update(decision.keys())
        fieldnames = sorted(list(fieldnames))

        # Write CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.decisions)

        return csv_path

    def export_to_json(self) -> str:
        """Export decisions to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(self.output_dir, f"research_decisions_{timestamp}.json")

        with open(json_path, 'w') as f:
            json.dump(self.decisions, f, indent=2)

        return json_path

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from logged decisions"""
        if not self.decisions:
            return {
                "total_decisions": 0,
                "approval_rate": 0,
                "false_positive_rate": 0
            }

        stats = {
            "total_decisions": len(self.decisions)
        }

        # Calculate approval rate
        approvals = sum(1 for d in self.decisions if d.get("decision_type") == "approve")
        stats["approval_rate"] = approvals / len(self.decisions) if self.decisions else 0

        # Calculate false positive rate (rejections)
        rejections = sum(1 for d in self.decisions if d.get("decision_type") == "reject")
        stats["false_positive_rate"] = rejections / len(self.decisions) if self.decisions else 0

        # Calculate average confidence
        confidences = [d.get("confidence", 0) for d in self.decisions if "confidence" in d]
        if confidences:
            stats["average_confidence"] = sum(confidences) / len(confidences)

        # Calculate average decision time
        times = [d.get("decision_time_seconds", 0) for d in self.decisions if "decision_time_seconds" in d]
        if times:
            stats["average_decision_time_seconds"] = sum(times) / len(times)

        # Per-mode statistics
        by_mode = {}
        for decision in self.decisions:
            mode = decision.get("mode", "unknown")
            if mode not in by_mode:
                by_mode[mode] = {"count": 0, "approved": 0, "rejected": 0}
            by_mode[mode]["count"] += 1
            if decision.get("decision_type") == "approve":
                by_mode[mode]["approved"] += 1
            elif decision.get("decision_type") == "reject":
                by_mode[mode]["rejected"] += 1

        # Calculate approval rates per mode
        for mode, counts in by_mode.items():
            if counts["count"] > 0:
                counts["approval_rate"] = counts["approved"] / counts["count"]
        stats["by_mode"] = by_mode

        return stats

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        stats = self.calculate_statistics()
        return {
            "total_decisions": stats["total_decisions"],
            "approval_rate": stats.get("approval_rate", 0),
            "false_positive_rate": stats.get("false_positive_rate", 0),
            "average_decision_time": stats.get("average_decision_time_seconds", 0),
            "average_confidence": stats.get("average_confidence", 0),
            "by_mode": stats.get("by_mode", {})
        }
