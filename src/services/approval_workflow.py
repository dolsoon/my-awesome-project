"""
Researcher Approval Workflow
SPEC-AI-FACIL-001 Phase 2: Approval workflow (y/n/e)
Minimal implementation for TDD GREEN phase
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class ApprovalWorkflow:
    """Manages researcher approval workflow"""

    VALID_DECISION_TYPES = ["approve", "reject", "edit"]

    def __init__(self):
        """Initialize approval workflow"""
        self.decisions: List[Dict[str, Any]] = []

    def format_suggestion_for_display(self, suggestion: Dict[str, Any]) -> str:
        """Format suggestion for researcher display"""
        mode = suggestion.get("mode", "unknown").upper()
        confidence = suggestion.get("confidence", 0)
        target_author = suggestion.get("target_author", "Unknown")
        comment_text = suggestion.get("comment_text", "")
        original = suggestion.get("original_suggestion", "")

        return f"""
[MODE: {mode}] [CONFIDENCE: {confidence:.0%}]
Target Author: {target_author}
Original Suggestion: {original}
Proposed Comment: {comment_text}
---
"""

    def process_decision(
        self,
        suggestion: Dict[str, Any],
        decision_type: str,
        edited_text: Optional[str] = None,
        researcher_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """Process researcher decision"""
        if decision_type not in self.VALID_DECISION_TYPES:
            raise ValueError(f"Invalid decision type: {decision_type}")

        decision = {
            "suggestion_id": suggestion.get("suggestion_id"),
            "decision_type": decision_type,
            "decision_timestamp": datetime.now().isoformat(),
            "researcher_id": researcher_id,
            "mode": suggestion.get("mode"),
            "original_suggestion": suggestion.get("original_suggestion"),
            "confidence": suggestion.get("confidence")
        }

        if decision_type == "approve":
            decision["final_comment"] = suggestion.get("comment_text")
        elif decision_type == "edit":
            decision["final_comment"] = edited_text or ""
            decision["original_comment"] = suggestion.get("comment_text")
        elif decision_type == "reject":
            decision["final_comment"] = None

        self.decisions.append(decision)
        return decision

    def get_last_decisions(self, n: int) -> List[Dict[str, Any]]:
        """Get last N decisions"""
        return self.decisions[-n:] if n > 0 else []

    def get_approval_rate(self) -> float:
        """Calculate approval rate"""
        if not self.decisions:
            return 0.0
        approvals = sum(1 for d in self.decisions if d["decision_type"] == "approve")
        return approvals / len(self.decisions)

    def get_mode_approval_rates(self) -> Dict[str, float]:
        """Get approval rates per mode"""
        modes = {}
        for decision in self.decisions:
            mode = decision.get("mode", "unknown")
            if mode not in modes:
                modes[mode] = {"count": 0, "approved": 0}
            modes[mode]["count"] += 1
            if decision["decision_type"] == "approve":
                modes[mode]["approved"] += 1

        rates = {}
        for mode, stats in modes.items():
            if stats["count"] > 0:
                rates[mode] = stats["approved"] / stats["count"]
        return rates

    def get_decision_metrics(self) -> Dict[str, Any]:
        """Get decision metrics"""
        approval_count = sum(1 for d in self.decisions if d["decision_type"] == "approve")
        rejection_count = sum(1 for d in self.decisions if d["decision_type"] == "reject")
        edit_count = sum(1 for d in self.decisions if d["decision_type"] == "edit")

        return {
            "total_decisions": len(self.decisions),
            "approval_count": approval_count,
            "rejection_count": rejection_count,
            "edit_count": edit_count,
            "approval_rate": self.get_approval_rate()
        }

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        metrics = self.get_decision_metrics()
        mode_rates = self.get_mode_approval_rates()

        return {
            "total_decisions": metrics["total_decisions"],
            "approval_rate": metrics["approval_rate"],
            "approval_count": metrics["approval_count"],
            "rejection_count": metrics["rejection_count"],
            "edit_count": metrics["edit_count"],
            "by_mode": mode_rates
        }
