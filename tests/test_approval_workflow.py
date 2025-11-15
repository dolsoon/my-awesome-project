"""
Test Researcher Approval Workflow
SPEC-AI-FACIL-001 Phase 2: Approval Workflow (y/n/e)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Optional
from datetime import datetime


class TestApprovalWorkflow:
    """Tests for researcher approval workflow"""

    @pytest.fixture
    def approval_workflow(self):
        """Create ApprovalWorkflow instance for testing"""
        from src.services.approval_workflow import ApprovalWorkflow
        return ApprovalWorkflow()

    @pytest.fixture
    def sample_suggestion(self) -> Dict:
        """Sample LLM suggestion for approval"""
        return {
            "suggestion_id": "sugg-123",
            "mode": "outlier",
            "original_suggestion": "Carol's quantum computing idea is unique",
            "confidence": 0.85,
            "target_author": "Carol",
            "target_text": "What if we combine quantum computing with neural networks?",
            "comment_text": "Your quantum computing idea is innovative and worth exploring!",
            "timestamp": datetime.now().isoformat()
        }

    def test_approval_workflow_initialization(self, approval_workflow):
        """Test ApprovalWorkflow initializes correctly"""
        assert approval_workflow is not None
        assert approval_workflow.decisions == []

    def test_display_suggestion(self, approval_workflow, sample_suggestion):
        """Test displaying suggestion to researcher"""
        display_text = approval_workflow.format_suggestion_for_display(sample_suggestion)
        assert isinstance(display_text, str)
        assert "outlier" in display_text.lower() or sample_suggestion["mode"] in display_text
        assert "0.85" in display_text or "85%" in display_text  # Confidence

    def test_approval_decision_approve(self, approval_workflow, sample_suggestion):
        """Test researcher approves suggestion (y)"""
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="approve"
        )
        assert decision["decision_type"] == "approve"
        assert decision["suggestion_id"] == "sugg-123"
        assert decision["final_comment"] == sample_suggestion["comment_text"]

    def test_approval_decision_reject(self, approval_workflow, sample_suggestion):
        """Test researcher rejects suggestion (n)"""
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="reject"
        )
        assert decision["decision_type"] == "reject"
        assert "final_comment" not in decision or decision.get("final_comment") is None

    def test_approval_decision_edit(self, approval_workflow, sample_suggestion):
        """Test researcher edits suggestion (e)"""
        edited_comment = "Your quantum idea could work if we limit scope to simulations"
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="edit",
            edited_text=edited_comment
        )
        assert decision["decision_type"] == "edit"
        assert decision["final_comment"] == edited_comment

    def test_approval_records_timestamp(self, approval_workflow, sample_suggestion):
        """Test that approval records decision timestamp"""
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="approve"
        )
        assert "decision_timestamp" in decision
        assert isinstance(decision["decision_timestamp"], str)

    def test_approval_records_researcher_id(self, approval_workflow, sample_suggestion):
        """Test that approval records researcher identifier"""
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="approve",
            researcher_id="researcher-001"
        )
        assert decision["researcher_id"] == "researcher-001"

    def test_approval_decision_stored_in_history(self, approval_workflow, sample_suggestion):
        """Test that decisions are stored in history"""
        approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="approve"
        )
        assert len(approval_workflow.decisions) > 0
        assert approval_workflow.decisions[0]["suggestion_id"] == "sugg-123"

    def test_approval_history_tracks_multiple_decisions(self, approval_workflow):
        """Test that multiple decisions are tracked"""
        sugg1 = {"suggestion_id": "s1", "mode": "outlier", "comment_text": "comment1"}
        sugg2 = {"suggestion_id": "s2", "mode": "summary", "comment_text": "comment2"}

        approval_workflow.process_decision(sugg1, "approve")
        approval_workflow.process_decision(sugg2, "reject")

        assert len(approval_workflow.decisions) == 2

    def test_approval_retrieves_last_n_decisions(self, approval_workflow):
        """Test retrieving last N decisions"""
        for i in range(5):
            sugg = {
                "suggestion_id": f"s{i}",
                "mode": "outlier",
                "comment_text": f"comment{i}"
            }
            approval_workflow.process_decision(sugg, "approve")

        last_3 = approval_workflow.get_last_decisions(3)
        assert len(last_3) == 3
        assert last_3[0]["suggestion_id"] == "s2"  # 3rd from end
        assert last_3[-1]["suggestion_id"] == "s4"  # Most recent

    def test_approval_get_approval_rate(self, approval_workflow):
        """Test calculating approval rate"""
        approval_workflow.process_decision(
            {"suggestion_id": "s1", "comment_text": "c1"}, "approve"
        )
        approval_workflow.process_decision(
            {"suggestion_id": "s2", "comment_text": "c2"}, "approve"
        )
        approval_workflow.process_decision(
            {"suggestion_id": "s3", "comment_text": "c3"}, "reject"
        )

        approval_rate = approval_workflow.get_approval_rate()
        assert approval_rate == pytest.approx(0.667, rel=0.01)  # 2/3

    def test_approval_get_mode_approval_rates(self, approval_workflow):
        """Test getting approval rates by mode"""
        approval_workflow.process_decision(
            {"suggestion_id": "s1", "mode": "outlier", "comment_text": "c1"},
            "approve"
        )
        approval_workflow.process_decision(
            {"suggestion_id": "s2", "mode": "outlier", "comment_text": "c2"},
            "reject"
        )
        approval_workflow.process_decision(
            {"suggestion_id": "s3", "mode": "summary", "comment_text": "c3"},
            "approve"
        )

        mode_rates = approval_workflow.get_mode_approval_rates()
        assert mode_rates["outlier"] == 0.5  # 1/2
        assert mode_rates["summary"] == 1.0  # 1/1

    def test_suggestion_format_includes_confidence(self, approval_workflow, sample_suggestion):
        """Test that suggestion display includes confidence score"""
        display = approval_workflow.format_suggestion_for_display(sample_suggestion)
        assert "85" in display or "0.85" in display or "confidence" in display.lower()

    def test_suggestion_format_includes_mode(self, approval_workflow, sample_suggestion):
        """Test that suggestion display includes mode"""
        display = approval_workflow.format_suggestion_for_display(sample_suggestion)
        assert "outlier" in display.lower() or sample_suggestion["mode"].lower() in display.lower()

    def test_suggestion_format_includes_original_text(self, approval_workflow, sample_suggestion):
        """Test that suggestion display includes original contribution"""
        display = approval_workflow.format_suggestion_for_display(sample_suggestion)
        # Should include either target author or target text
        assert sample_suggestion["target_author"] in display or "quantum" in display

    def test_edit_validation_rejects_empty_edit(self, approval_workflow, sample_suggestion):
        """Test that empty edited text is rejected or handled"""
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="edit",
            edited_text=""
        )
        # Should record the decision (even if empty)
        assert decision is not None
        assert decision["decision_type"] == "edit"

    def test_edit_preserves_original_suggestion_id(self, approval_workflow, sample_suggestion):
        """Test that edits preserve original suggestion ID"""
        edited_comment = "Different comment text"
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="edit",
            edited_text=edited_comment
        )
        assert decision["suggestion_id"] == sample_suggestion["suggestion_id"]

    def test_decision_includes_original_suggestion_text(self, approval_workflow, sample_suggestion):
        """Test that decisions log original suggestion for comparison"""
        decision = approval_workflow.process_decision(
            suggestion=sample_suggestion,
            decision_type="edit",
            edited_text="New comment"
        )
        assert "original_suggestion" in decision or "original_comment" in decision

    def test_approval_handles_invalid_decision_type(self, approval_workflow, sample_suggestion):
        """Test that invalid decision type is handled"""
        with pytest.raises((ValueError, KeyError)):
            approval_workflow.process_decision(
                suggestion=sample_suggestion,
                decision_type="invalid_type"
            )

    def test_approval_workflow_state_machine(self, approval_workflow):
        """Test approval workflow state transitions"""
        suggestion = {
            "suggestion_id": "s1",
            "mode": "outlier",
            "comment_text": "test"
        }
        # Can transition from None to any decision
        decision1 = approval_workflow.process_decision(suggestion, "approve")
        assert decision1["decision_type"] == "approve"

        # Next suggestion is independent
        suggestion2 = {
            "suggestion_id": "s2",
            "mode": "outlier",
            "comment_text": "test2"
        }
        decision2 = approval_workflow.process_decision(suggestion2, "reject")
        assert decision2["decision_type"] == "reject"

    def test_approval_decision_metrics(self, approval_workflow):
        """Test that decision metrics are accurate"""
        for i in range(10):
            decision_type = "approve" if i % 3 == 0 else "reject" if i % 3 == 1 else "edit"
            sugg = {
                "suggestion_id": f"s{i}",
                "mode": "outlier",
                "comment_text": f"comment{i}"
            }
            approval_workflow.process_decision(sugg, decision_type)

        metrics = approval_workflow.get_decision_metrics()
        assert metrics["total_decisions"] == 10
        assert "approval_count" in metrics
        assert "rejection_count" in metrics
        assert "edit_count" in metrics

    def test_approval_session_statistics(self, approval_workflow):
        """Test session statistics calculation"""
        approval_workflow.process_decision(
            {"suggestion_id": "s1", "comment_text": "c1"}, "approve"
        )
        approval_workflow.process_decision(
            {"suggestion_id": "s2", "comment_text": "c2"}, "reject"
        )

        stats = approval_workflow.get_session_statistics()
        assert stats["total_decisions"] == 2
        assert stats["approval_rate"] == 0.5
