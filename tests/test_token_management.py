"""
Test Token Management Service
SPEC-AI-FACIL-001 Phase 2: Token Counting and Context Truncation
"""

import pytest
from typing import Dict, List


class TestTokenManagement:
    """Tests for token counting and truncation logic"""

    @pytest.fixture
    def token_manager(self):
        """Create TokenManager instance for testing"""
        from src.services.token_management import TokenManager
        return TokenManager(max_tokens=128000)

    @pytest.fixture
    def sample_document(self) -> Dict:
        """Sample document for token testing"""
        return {
            "document_id": "test-doc",
            "contributions": [
                {
                    "author": "Author1",
                    "text": "This is a contribution about machine learning and AI systems"
                },
                {
                    "author": "Author2",
                    "text": "Building on that idea, we could use reinforcement learning"
                }
            ],
            "context_files": []
        }

    def test_token_manager_initialization(self, token_manager):
        """Test TokenManager initializes with max token limit"""
        assert token_manager.max_tokens == 128000
        assert token_manager.model_encoding is not None  # Should initialize tiktoken

    def test_count_tokens_for_text(self, token_manager):
        """Test counting tokens in plain text"""
        text = "This is a test sentence with multiple words"
        token_count = token_manager.count_tokens(text)
        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count < 50  # Short text

    def test_count_tokens_for_document(self, token_manager, sample_document):
        """Test counting tokens for entire document"""
        total_tokens = token_manager.count_tokens_for_document(sample_document)
        assert isinstance(total_tokens, int)
        assert total_tokens > 0
        # Should be sum of all contributions plus metadata
        assert total_tokens > 10

    def test_count_tokens_includes_context_files(self, token_manager):
        """Test that token count includes context files"""
        doc = {
            "document_id": "test",
            "contributions": [{"author": "A", "text": "test"}],
            "context_files": [
                {"filename": "context.txt", "content": "This is context about the domain"}
            ]
        }
        total_tokens = token_manager.count_tokens_for_document(doc)
        # Should include both contributions and context
        assert total_tokens > 5

    def test_warning_near_token_limit(self, token_manager):
        """Test that warning is issued when approaching token limit"""
        token_manager.max_tokens = 100
        doc = {
            "document_id": "test",
            "contributions": [{"author": "A", "text": "test content " * 20}],
            "context_files": []
        }
        tokens_used = token_manager.count_tokens_for_document(doc)
        warning = token_manager.check_token_limit(tokens_used)
        # Should warn if close to 100 tokens
        if tokens_used > 80:
            assert warning is not None

    def test_truncate_context_respects_max_tokens(self, token_manager):
        """Test that truncation respects max token limit"""
        large_doc = {
            "document_id": "test",
            "contributions": [
                {"author": f"Author{i}", "text": "test " * 100, "timestamp": f"2025-11-15T{i:02d}:00:00Z"}
                for i in range(20)
            ],
            "context_files": []
        }
        truncated = token_manager.truncate_context(large_doc, max_tokens=50000)
        token_count = token_manager.count_tokens_for_document(truncated)
        assert token_count <= 50000 + 1000  # Small buffer for overhead

    def test_truncation_removes_oldest_contributions_first(self, token_manager):
        """Test that truncation removes oldest contributions first"""
        doc = {
            "document_id": "test",
            "contributions": [
                {
                    "author": f"Author{i}",
                    "text": "contribution " * 50,
                    "timestamp": f"2025-11-15T{i:02d}:00:00Z"
                }
                for i in range(10)
            ],
            "context_files": []
        }
        truncated = token_manager.truncate_context(doc, max_tokens=500)  # Very small limit
        # Newer contributions (higher indices) should be preserved
        assert len(truncated["contributions"]) <= len(doc["contributions"])
        # At least one contribution should be removed to meet the limit
        if len(doc["contributions"]) > 1:
            assert len(truncated["contributions"]) < len(doc["contributions"])
        # Check that we kept newer timestamps
        if len(truncated["contributions"]) > 0:
            first_timestamp = truncated["contributions"][0]["timestamp"]
            last_timestamp = truncated["contributions"][-1]["timestamp"]
            assert first_timestamp <= last_timestamp

    def test_truncation_preserves_context_files_always(self, token_manager):
        """Test that context files are always preserved during truncation"""
        doc = {
            "document_id": "test",
            "contributions": [
                {"author": f"Author{i}", "text": "test " * 100}
                for i in range(30)
            ],
            "context_files": [
                {"filename": "guidelines.txt", "content": "Domain knowledge here"}
            ]
        }
        truncated = token_manager.truncate_context(doc, max_tokens=20000)
        assert len(truncated["context_files"]) > 0
        assert truncated["context_files"][0]["filename"] == "guidelines.txt"

    def test_truncation_preserves_multiple_context_files(self, token_manager):
        """Test that all context files are preserved"""
        doc = {
            "document_id": "test",
            "contributions": [
                {"author": f"Author{i}", "text": "test " * 100}
                for i in range(30)
            ],
            "context_files": [
                {"filename": "guidelines.txt", "content": "Guidelines here"},
                {"filename": "examples.txt", "content": "Examples here"},
                {"filename": "domain.txt", "content": "Domain knowledge"}
            ]
        }
        truncated = token_manager.truncate_context(doc, max_tokens=20000)
        assert len(truncated["context_files"]) == 3
        filenames = [f["filename"] for f in truncated["context_files"]]
        assert "guidelines.txt" in filenames
        assert "examples.txt" in filenames
        assert "domain.txt" in filenames

    def test_truncation_handles_zero_contributions(self, token_manager):
        """Test truncation handles edge case of no contributions"""
        doc = {
            "document_id": "test",
            "contributions": [],
            "context_files": [{"filename": "context.txt", "content": "context"}]
        }
        truncated = token_manager.truncate_context(doc, max_tokens=50000)
        assert "context_files" in truncated
        assert len(truncated["context_files"]) > 0

    def test_truncation_handles_single_contribution(self, token_manager):
        """Test truncation with single large contribution"""
        doc = {
            "document_id": "test",
            "contributions": [
                {"author": "A", "text": "test " * 500}  # Large single contribution
            ],
            "context_files": [{"filename": "context.txt", "content": "context"}]
        }
        truncated = token_manager.truncate_context(doc, max_tokens=10000)
        # Should keep at least the context file
        assert len(truncated["context_files"]) > 0

    def test_token_calculation_consistency(self, token_manager):
        """Test that token counting is consistent"""
        text = "This is a test sentence"
        count1 = token_manager.count_tokens(text)
        count2 = token_manager.count_tokens(text)
        assert count1 == count2

    def test_token_count_scales_with_length(self, token_manager):
        """Test that token count increases with text length"""
        short_text = "Hello"
        long_text = "Hello " * 100
        short_tokens = token_manager.count_tokens(short_text)
        long_tokens = token_manager.count_tokens(long_text)
        assert long_tokens > short_tokens

    def test_context_file_token_contribution(self, token_manager):
        """Test that context files contribute to token count"""
        doc_without_context = {
            "document_id": "test",
            "contributions": [{"author": "A", "text": "test"}],
            "context_files": []
        }
        doc_with_context = {
            "document_id": "test",
            "contributions": [{"author": "A", "text": "test"}],
            "context_files": [
                {"filename": "context.txt", "content": "This is important context information"}
            ]
        }
        tokens_without = token_manager.count_tokens_for_document(doc_without_context)
        tokens_with = token_manager.count_tokens_for_document(doc_with_context)
        assert tokens_with > tokens_without

    def test_truncation_document_structure_preserved(self, token_manager):
        """Test that truncated document preserves required fields"""
        doc = {
            "document_id": "doc-123",
            "contributions": [{"author": "A", "text": "test " * 100} for _ in range(20)],
            "context_files": [{"filename": "context.txt", "content": "context"}]
        }
        truncated = token_manager.truncate_context(doc, max_tokens=20000)
        assert "document_id" in truncated
        assert truncated["document_id"] == "doc-123"
        assert "contributions" in truncated
        assert "context_files" in truncated

    def test_max_tokens_enforced_strictly(self, token_manager):
        """Test that max tokens is enforced with small margin"""
        doc = {
            "document_id": "test",
            "contributions": [
                {"author": f"A{i}", "text": "test " * 100}
                for i in range(50)
            ],
            "context_files": []
        }
        truncated = token_manager.truncate_context(doc, max_tokens=10000)
        actual_tokens = token_manager.count_tokens_for_document(truncated)
        # Should be close to limit with small margin for overhead
        assert actual_tokens <= 10000 * 1.05  # 5% margin

    def test_empty_document_handling(self, token_manager):
        """Test handling of empty document"""
        doc = {
            "document_id": "test",
            "contributions": [],
            "context_files": []
        }
        token_count = token_manager.count_tokens_for_document(doc)
        assert isinstance(token_count, int)
        assert token_count >= 0
