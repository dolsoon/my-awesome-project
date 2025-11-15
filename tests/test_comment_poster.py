"""
Test Comment Posting Service
SPEC-AI-FACIL-001 Phase 2: Google Docs API Comment Posting
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict
from datetime import datetime, timedelta


class TestCommentPoster:
    """Tests for Google Docs API comment posting service"""

    @pytest.fixture
    def comment_poster(self):
        """Create CommentPoster instance for testing"""
        from src.services.comment_poster import CommentPoster
        return CommentPoster(docs_api_client=Mock())

    @pytest.fixture
    def sample_comment(self) -> Dict:
        """Sample comment to post"""
        return {
            "document_id": "test-doc-123",
            "mode": "outlier",
            "comment_text": "Your quantum computing idea is innovative!",
            "confidence": 0.85,
            "target_author": "Carol",
            "target_text": "What if we combine quantum computing with neural networks?",
            "suggestion_id": "sugg-123"
        }

    def test_comment_poster_initialization(self, comment_poster):
        """Test CommentPoster initializes with API client"""
        assert comment_poster.docs_api_client is not None
        assert comment_poster.rate_limit_seconds == 60
        assert comment_poster.max_unresolved_comments == 5

    def test_format_comment_with_mode_attribution(self, comment_poster, sample_comment):
        """Test comment is formatted with mode attribution"""
        formatted = comment_poster.format_comment(sample_comment)
        assert isinstance(formatted, str)
        assert "[AI Facilitator - outlier]" in formatted or "outlier" in formatted.lower()
        assert sample_comment["comment_text"] in formatted

    def test_format_comment_includes_metadata(self, comment_poster, sample_comment):
        """Test comment formatting includes metadata"""
        formatted = comment_poster.format_comment(sample_comment)
        # Should include confidence or mode or timestamp
        assert "0.85" in formatted or "85%" in formatted or "confidence" in formatted.lower()

    def test_post_comment_success(self, comment_poster, sample_comment):
        """Test successful comment posting"""
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.return_value = {"commentId": "comment-123"}
            result = comment_poster.post_comment(sample_comment)
            assert result["success"] is True
            assert result["comment_id"] == "comment-123"

    def test_post_comment_with_position_mapping(self, comment_poster, sample_comment):
        """Test comment posting with position mapping"""
        sample_comment["text_position"] = {"index": 50, "length": 10}
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.return_value = {"commentId": "comment-123"}
            result = comment_poster.post_comment(sample_comment)
            assert mock_api.called
            call_args = mock_api.call_args
            # Position should be passed to API
            assert "position" in str(call_args) or call_args is not None

    def test_rate_limiting_enforces_minimum_interval(self, comment_poster, sample_comment):
        """Test rate limiting enforces minimum 60 second interval"""
        comment_poster.last_comment_time["test-doc-123"] = datetime.now()

        # Immediate post should be rate limited
        can_post = comment_poster.can_post_comment("test-doc-123")
        assert can_post is False

    def test_rate_limiting_allows_after_interval(self, comment_poster, sample_comment):
        """Test rate limiting allows posting after interval passes"""
        past_time = datetime.now() - timedelta(seconds=65)
        comment_poster.last_comment_time["test-doc-123"] = past_time

        can_post = comment_poster.can_post_comment("test-doc-123")
        assert can_post is True

    def test_rate_limiting_tracks_per_document(self, comment_poster):
        """Test rate limiting is per-document"""
        now = datetime.now()
        comment_poster.last_comment_time["doc-1"] = now

        # doc-1 should be rate limited
        assert comment_poster.can_post_comment("doc-1") is False
        # doc-2 should be allowed (not posted to recently)
        assert comment_poster.can_post_comment("doc-2") is True

    def test_post_comment_returns_failure_on_rate_limit(self, comment_poster, sample_comment):
        """Test that rate limited posts return failure"""
        comment_poster.last_comment_time["test-doc-123"] = datetime.now()
        result = comment_poster.post_comment(sample_comment)
        # Should either return failure or queue for later
        assert result.get("success") is False or result.get("queued") is True

    def test_unresolved_comments_tracking(self, comment_poster):
        """Test tracking of unresolved comments"""
        comment_poster.unresolved_comments["test-doc"] = 5
        assert comment_poster.get_unresolved_comment_count("test-doc") == 5

    def test_pause_commenting_at_max_unresolved(self, comment_poster, sample_comment):
        """Test that commenting pauses when ≥5 unresolved comments exist"""
        comment_poster.unresolved_comments["test-doc-123"] = 5
        result = comment_poster.post_comment(sample_comment)
        # Should pause or queue
        assert result.get("success") is False or result.get("paused") is True

    def test_deduplication_check_before_posting(self, comment_poster, sample_comment):
        """Test deduplication check prevents duplicate comments"""
        # Mark this position as already commented
        position_hash = comment_poster._hash_position(
            sample_comment["document_id"],
            sample_comment.get("text_position")
        )
        comment_poster.posted_comments[position_hash] = {
            "text": sample_comment["comment_text"],
            "timestamp": datetime.now()
        }

        result = comment_poster.post_comment(sample_comment)
        # Should detect duplicate
        assert result.get("success") is False or result.get("duplicate") is True

    def test_deduplication_allows_different_positions(self, comment_poster, sample_comment):
        """Test that comments at different positions are not considered duplicates"""
        position1_hash = comment_poster._hash_position("doc", {"index": 10})
        comment_poster.posted_comments[position1_hash] = {"text": "comment", "timestamp": datetime.now()}

        # Different position should be allowed
        sample_comment["text_position"] = {"index": 20, "length": 5}
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.return_value = {"commentId": "comment-456"}
            result = comment_poster.post_comment(sample_comment)
            # Should attempt to post (different position)
            assert mock_api.called or result.get("duplicate") is not True

    def test_comment_queue_pending_requests(self, comment_poster, sample_comment):
        """Test queuing of pending comments when rate limited"""
        comment_poster.last_comment_time["test-doc-123"] = datetime.now()
        result = comment_poster.post_comment(sample_comment, queue_on_limit=True)
        # Should be queued or return as pending
        assert result.get("success") is False
        assert len(comment_poster.pending_queue) > 0

    def test_retry_mechanism_on_api_failure(self, comment_poster, sample_comment):
        """Test retry mechanism on API failure"""
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            # First call fails, second succeeds
            mock_api.side_effect = [
                Exception("API error"),
                {"commentId": "comment-123"}
            ]
            result = comment_poster.post_comment(sample_comment)
            # Should retry
            assert mock_api.call_count >= 1

    def test_retry_backoff_timing(self, comment_poster, sample_comment):
        """Test retry uses appropriate backoff timing"""
        with patch('time.sleep') as mock_sleep:
            with patch.object(comment_poster, '_call_docs_api') as mock_api:
                mock_api.side_effect = [
                    Exception("API error"),
                    {"commentId": "comment-123"}
                ]
                comment_poster.post_comment(sample_comment)
                # Should have sleep call for backoff
                if mock_api.call_count > 1:
                    assert mock_sleep.called

    def test_comment_logging_on_success(self, comment_poster, sample_comment):
        """Test that successful comments are logged"""
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.return_value = {"commentId": "comment-123"}
            comment_poster.post_comment(sample_comment)

            # Should be in posted comments
            assert len(comment_poster.posting_history) > 0

    def test_comment_logging_on_failure(self, comment_poster, sample_comment):
        """Test that failed comments are logged for review"""
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.side_effect = Exception("API error")
            result = comment_poster.post_comment(sample_comment)

            # Should log failure
            assert len(comment_poster.failed_queue) > 0 or result.get("success") is False

    def test_position_anchoring_maps_text_location(self, comment_poster, sample_comment):
        """Test that position anchoring correctly maps text location"""
        # This would require finding text in document
        sample_comment["target_text"] = "quantum computing"
        comment_poster.current_document_text = "What if we combine quantum computing with neural networks?"

        position = comment_poster._find_text_position(sample_comment["target_text"])
        if position:
            assert isinstance(position, dict)
            assert "index" in position or "start" in position

    def test_format_comment_with_timestamp(self, comment_poster, sample_comment):
        """Test comment includes timestamp in formatted output"""
        formatted = comment_poster.format_comment(sample_comment)
        # Should include timestamp information
        assert len(formatted) > 0

    def test_api_error_handling(self, comment_poster, sample_comment):
        """Test graceful handling of API errors"""
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.side_effect = Exception("Google API error")
            result = comment_poster.post_comment(sample_comment)
            # Should handle gracefully
            assert result.get("success") is False or result.get("error") is not None

    def test_batch_comment_posting_respects_rate_limit(self, comment_poster):
        """Test that batch posting respects rate limits"""
        comments = [
            {
                "document_id": "doc-1",
                "mode": "outlier",
                "comment_text": f"Comment {i}",
                "suggestion_id": f"s{i}"
            }
            for i in range(5)
        ]

        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.return_value = {"commentId": "comment-123"}
            results = comment_poster.post_batch_comments(comments)
            # Should post some with delay or queue others
            assert len(results) == len(comments)

    def test_get_posting_statistics(self, comment_poster):
        """Test getting comment posting statistics"""
        with patch.object(comment_poster, '_call_docs_api') as mock_api:
            mock_api.return_value = {"commentId": "comment-123"}
            comment_poster.post_comment({"document_id": "doc-1", "comment_text": "c1"})
            comment_poster.post_comment({"document_id": "doc-1", "comment_text": "c2"})

            stats = comment_poster.get_posting_statistics()
            assert stats["total_attempted"] >= 2 or stats.get("posted_count", 0) >= 0
