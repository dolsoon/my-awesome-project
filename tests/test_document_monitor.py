"""
Test Document Monitor Service
SPEC-AI-FACIL-001 Phase 1: Google Docs Monitoring
"""

import pytest
from unittest.mock import Mock, patch


class TestDocumentMonitor:
    """Tests for document monitoring service"""

    @pytest.fixture
    def monitor(self):
        """Create DocumentMonitor instance for testing"""
        from src.services.document_monitor import DocumentMonitor
        return DocumentMonitor(
            google_client=Mock(),
            oauth_handler=Mock()
        )

    def test_monitor_initialization(self, monitor):
        """Test document monitor initializes correctly"""
        assert monitor.google_client is not None
        assert monitor.oauth_handler is not None
        assert hasattr(monitor, 'watched_documents')

    def test_register_document_for_monitoring(self, monitor):
        """Test registering a document for monitoring"""
        doc_id = "test-doc-id-123"
        monitor.register_document(doc_id)
        assert doc_id in monitor.watched_documents

    def test_fetch_document_content(self, monitor):
        """Test fetching document content from Google Docs API"""
        doc_id = "test-doc-id"
        mock_response = {
            "documentId": doc_id,
            "title": "Test Document",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Sample text"}}]}}
                ]
            }
        }

        with patch.object(monitor.google_client, 'documents') as mock_docs:
            mock_docs.return_value.get.return_value.execute.return_value = mock_response
            content = monitor.fetch_document_content(doc_id)
            assert content is not None

    def test_track_document_revision(self, monitor):
        """Test tracking document revision IDs"""
        doc_id = "test-doc-id"
        revision_id = "rev-123"

        monitor.track_revision(doc_id, revision_id)
        assert monitor.get_last_revision(doc_id) == revision_id

    def test_detect_new_changes(self, monitor):
        """Test detection of new changes since last revision"""
        doc_id = "test-doc-id"

        # Set initial revision
        monitor.track_revision(doc_id, "rev-1")

        # New revision should indicate changes
        has_changes = monitor.has_changes_since_revision(doc_id, "rev-2")
        assert has_changes is True

    def test_extract_text_with_author_attribution(self, monitor):
        """Test extracting text with author attribution"""
        mock_response = {
            "documentId": "test-doc",
            "suggestedChanges": [],
            "body": {
                "content": [{
                    "paragraph": {
                        "elements": [{
                            "textRun": {
                                "content": "Contribution text",
                                "suggestedInsertionIds": ["suggestion-1"]
                            }
                        }]
                    }
                }]
            }
        }

        with patch.object(monitor, 'fetch_document_content') as mock_fetch:
            mock_fetch.return_value = mock_response
            text = monitor.extract_text_from_document("test-doc")
            assert "Contribution text" in text

    def test_batch_process_multiple_documents(self, monitor):
        """Test batch processing multiple monitored documents"""
        docs = ["doc-1", "doc-2", "doc-3"]
        for doc_id in docs:
            monitor.register_document(doc_id)

        batch = monitor.get_documents_for_batch()
        assert len(batch) == 3

    def test_prevent_duplicate_processing(self, monitor):
        """Test preventing duplicate processing of same revision"""
        doc_id = "test-doc"
        revision_id = "rev-100"

        monitor.track_revision(doc_id, revision_id)

        # Same revision should not be processed again
        is_duplicate = monitor.is_duplicate_revision(doc_id, revision_id)
        assert is_duplicate is True

    def test_handle_api_rate_limit_errors(self, monitor):
        """Test handling of Google API rate limit errors"""
        with patch.object(monitor.google_client, 'documents') as mock_docs:
            error_msg = "429: Rate limit exceeded"
            mock_docs.return_value.get.return_value.execute.side_effect = (
                Exception(error_msg)
            )

            with pytest.raises(Exception) as exc_info:
                monitor.fetch_document_content("doc-id")

            assert ("429" in str(exc_info.value) or
                    "Rate limit" in str(exc_info.value))

    def test_store_revision_history(self, monitor):
        """Test storing revision history for deduplication"""
        doc_id = "test-doc"

        monitor.track_revision(doc_id, "rev-1")
        monitor.track_revision(doc_id, "rev-2")
        monitor.track_revision(doc_id, "rev-3")

        revisions = monitor.get_revision_history(doc_id)
        assert len(revisions) >= 1
        assert monitor.get_last_revision(doc_id) == "rev-3"

    def test_document_change_timestamp(self, monitor):
        """Test recording timestamp of document changes"""
        doc_id = "test-doc"
        import time

        monitor.register_document(doc_id)
        timestamp = time.time()
        monitor.record_change_timestamp(doc_id, timestamp)

        last_change = monitor.get_last_change_timestamp(doc_id)
        assert last_change == timestamp

    def test_batch_interval_configuration(self, monitor):
        """Test configurable batch processing intervals"""
        monitor.set_batch_interval(90)
        assert monitor.batch_interval == 90

        monitor.set_batch_interval(120)
        assert monitor.batch_interval == 120
