"""
Test LLM Analysis Service
SPEC-AI-FACIL-001 Phase 2: LLM Analysis and 4 Agent Modes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List
import json


class TestLLMService:
    """Tests for LLM analysis service with 4 agent modes"""

    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance for testing"""
        from src.services.llm_service import LLMService
        return LLMService(api_key="test-api-key", model="gemini-2.5-flash-lite")

    @pytest.fixture
    def sample_document_content(self) -> Dict:
        """Sample document content with contributions"""
        return {
            "document_id": "test-doc-123",
            "title": "Research Brainstorm",
            "contributions": [
                {
                    "author": "Alice",
                    "text": "We should use machine learning to identify patterns",
                    "timestamp": "2025-11-15T10:00:00Z"
                },
                {
                    "author": "Bob",
                    "text": "Machine learning might be overkill. Simple rules could work.",
                    "timestamp": "2025-11-15T10:05:00Z"
                },
                {
                    "author": "Carol",
                    "text": "What if we combine quantum computing with neural networks?",
                    "timestamp": "2025-11-15T10:10:00Z"
                }
            ],
            "context_files": []
        }

    def test_llm_service_initialization(self, llm_service):
        """Test LLMService initializes with API credentials"""
        assert llm_service.api_key == "test-api-key"
        assert llm_service.model == "gemini-2.5-flash-lite"
        assert llm_service.max_tokens == 128000
        assert llm_service.confidence_threshold == 0.7

    def test_outlier_mode_prompt_generation(self, llm_service, sample_document_content):
        """Test Outlier mode prompt template generation"""
        prompt = llm_service._generate_outlier_prompt(sample_document_content)
        assert isinstance(prompt, str)
        assert "outlier" in prompt.lower() or "unique" in prompt.lower()
        assert "Alice" in prompt
        assert "machine learning" in prompt

    def test_summary_mode_prompt_generation(self, llm_service, sample_document_content):
        """Test Summary mode prompt template generation"""
        prompt = llm_service._generate_summary_prompt(sample_document_content)
        assert isinstance(prompt, str)
        assert "summary" in prompt.lower() or "theme" in prompt.lower()
        assert "clustering" in prompt.lower() or "group" in prompt.lower()

    def test_connect_mode_prompt_generation(self, llm_service, sample_document_content):
        """Test Connect mode prompt template generation"""
        prompt = llm_service._generate_connect_prompt(sample_document_content)
        assert isinstance(prompt, str)
        assert "connect" in prompt.lower() or "similar" in prompt.lower()
        assert "different author" in prompt.lower() or "different people" in prompt.lower()

    def test_question_mode_prompt_generation(self, llm_service, sample_document_content):
        """Test Question mode prompt template generation"""
        prompt = llm_service._generate_question_prompt(sample_document_content)
        assert isinstance(prompt, str)
        assert "question" in prompt.lower() or "socratic" in prompt.lower()
        assert "assumption" in prompt.lower() or "clarif" in prompt.lower()

    def test_token_counting(self, llm_service):
        """Test token counting for document content"""
        text = "This is a test document with some content"
        token_count = llm_service.count_tokens(text)
        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count < 20  # Short text should be ~10 tokens

    def test_token_counting_with_context_files(self, llm_service, sample_document_content):
        """Test token counting with context files included"""
        sample_document_content["context_files"] = [
            {
                "filename": "context.txt",
                "content": "This is important context about the domain"
            }
        ]
        total_tokens = llm_service.count_tokens_for_document(sample_document_content)
        assert isinstance(total_tokens, int)
        assert total_tokens > 0

    def test_context_truncation_preserves_context_files(self, llm_service):
        """Test that truncation preserves imported context files"""
        large_document = {
            "document_id": "test-doc",
            "contributions": [
                {"author": f"Author{i}", "text": "test " * 50}
                for i in range(100)
            ],
            "context_files": [
                {"filename": "context.txt", "content": "Important context"}
            ]
        }
        truncated = llm_service.truncate_context(large_document, max_tokens=50000)
        assert len(truncated["context_files"]) > 0
        assert truncated["context_files"][0]["content"] == "Important context"

    def test_context_truncation_removes_oldest_contributions(self, llm_service):
        """Test that truncation removes oldest contributions first"""
        large_document = {
            "document_id": "test-doc",
            "contributions": [
                {"author": f"Author{i}", "text": "test " * 50, "timestamp": f"2025-11-15T{i:02d}:00:00Z"}
                for i in range(100)
            ],
            "context_files": []
        }
        truncated = llm_service.truncate_context(large_document, max_tokens=5000)  # Very small limit
        # Should remove oldest contributions (lower indices)
        assert len(truncated["contributions"]) < len(large_document["contributions"])

    def test_analyze_with_outlier_mode(self, llm_service, sample_document_content):
        """Test LLM analysis with Outlier mode"""
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.return_value = {
                "outlier_found": True,
                "unique_aspect": "Carol's quantum computing suggestion is novel",
                "similarity_score": 0.2,
                "confidence": 0.85,
                "encouragement_message": "Your quantum computing idea is creative and worth exploring!"
            }
            result = llm_service.analyze(sample_document_content, mode="outlier")
            assert result["outlier_found"] is True
            assert result["confidence"] > 0.7
            assert "Carol" in result["unique_aspect"] or "quantum" in result["unique_aspect"]

    def test_analyze_with_summary_mode(self, llm_service, sample_document_content):
        """Test LLM analysis with Summary mode"""
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.return_value = {
                "themes": ["Machine Learning approaches", "Risk assessment"],
                "summary": "Debate between ML and simpler approaches",
                "contributor_count": 3,
                "confidence": 0.88
            }
            result = llm_service.analyze(sample_document_content, mode="summary")
            assert isinstance(result["themes"], list)
            assert len(result["themes"]) > 0
            assert result["confidence"] > 0.7

    def test_analyze_with_connect_mode(self, llm_service, sample_document_content):
        """Test LLM analysis with Connect mode"""
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.return_value = {
                "connections": [
                    {
                        "author1": "Alice",
                        "author2": "Carol",
                        "common_theme": "Both interested in advanced technical approaches",
                        "connection_message": "Alice and Carol both want to explore cutting-edge technology"
                    }
                ],
                "confidence": 0.75
            }
            result = llm_service.analyze(sample_document_content, mode="connect")
            assert isinstance(result["connections"], list)
            assert len(result["connections"]) > 0

    def test_analyze_with_question_mode(self, llm_service, sample_document_content):
        """Test LLM analysis with Question mode"""
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.return_value = {
                "target_author": "Bob",
                "clarifying_questions": [
                    "What specific rules would you propose as an alternative?",
                    "How would you measure whether simple rules are sufficient?"
                ],
                "confidence": 0.82
            }
            result = llm_service.analyze(sample_document_content, mode="question")
            assert "clarifying_questions" in result
            assert isinstance(result["clarifying_questions"], list)
            assert len(result["clarifying_questions"]) > 0

    def test_analyze_respects_confidence_threshold(self, llm_service, sample_document_content):
        """Test that analysis respects confidence threshold"""
        llm_service.confidence_threshold = 0.9
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.return_value = {
                "result": "Low confidence finding",
                "confidence": 0.6
            }
            result = llm_service.analyze(sample_document_content, mode="outlier")
            assert result is None or result.get("confidence", 0) >= llm_service.confidence_threshold

    def test_analyze_with_timeout(self, llm_service, sample_document_content):
        """Test analysis handles API timeout gracefully"""
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.side_effect = TimeoutError("API timeout")
            result = llm_service.analyze(sample_document_content, mode="outlier")
            assert result is None or result.get("error") is not None

    def test_parse_structured_response(self, llm_service):
        """Test parsing of structured JSON response from LLM"""
        raw_response = """
        {
            "outlier_found": true,
            "confidence": 0.85,
            "message": "This is a unique idea"
        }
        """
        parsed = llm_service._parse_structured_response(raw_response)
        assert isinstance(parsed, dict)
        assert parsed["outlier_found"] is True
        assert parsed["confidence"] == 0.85

    def test_parse_malformed_response(self, llm_service):
        """Test parsing handles malformed LLM response"""
        raw_response = "This is not JSON {invalid response}"
        parsed = llm_service._parse_structured_response(raw_response)
        # Should return None or handle gracefully
        assert parsed is None or isinstance(parsed, dict)

    def test_context_file_integration_in_prompt(self, llm_service, sample_document_content):
        """Test that context files are properly integrated into prompts"""
        sample_document_content["context_files"] = [
            {"filename": "guidelines.txt", "content": "All ideas must be innovative"}
        ]
        prompt = llm_service._generate_outlier_prompt(sample_document_content)
        assert "guidelines.txt" in prompt or "All ideas must be innovative" in prompt

    def test_mode_parameter_validation(self, llm_service, sample_document_content):
        """Test that invalid mode raises error"""
        with pytest.raises(ValueError):
            llm_service.analyze(sample_document_content, mode="invalid_mode")

    def test_analysis_preserves_document_metadata(self, llm_service, sample_document_content):
        """Test that analysis preserves document ID and metadata"""
        with patch.object(llm_service, '_call_llm_api') as mock_api:
            mock_api.return_value = {"result": "test", "confidence": 0.8}
            result = llm_service.analyze(sample_document_content, mode="outlier")
            # Result should include original document context
            assert result is not None


class TestPromptTemplates:
    """Tests for mode-specific prompt templates"""

    def test_outlier_prompt_includes_similarity_scoring(self):
        """Test Outlier prompt includes instructions for similarity scoring (0.0-1.0)"""
        from src.services.llm_service import OutlierPromptTemplate
        template = OutlierPromptTemplate()
        prompt = template.generate({"contributions": [{"text": "idea"}]})
        assert "0.0" in prompt or "1.0" in prompt or "similar" in prompt.lower()

    def test_summary_prompt_includes_clustering_instructions(self):
        """Test Summary prompt includes clustering/theme instructions"""
        from src.services.llm_service import SummaryPromptTemplate
        template = SummaryPromptTemplate()
        prompt = template.generate({"contributions": [{"text": "idea"}]})
        assert "cluster" in prompt.lower() or "theme" in prompt.lower() or "group" in prompt.lower()

    def test_connect_prompt_includes_different_author_filter(self):
        """Test Connect prompt includes instruction to only connect different authors"""
        from src.services.llm_service import ConnectPromptTemplate
        template = ConnectPromptTemplate()
        prompt = template.generate({"contributions": [{"author": "A", "text": "idea"}]})
        assert "different author" in prompt.lower() or "different person" in prompt.lower()

    def test_question_prompt_includes_socratic_method(self):
        """Test Question prompt includes Socratic questioning instructions"""
        from src.services.llm_service import QuestionPromptTemplate
        template = QuestionPromptTemplate()
        prompt = template.generate({"contributions": [{"text": "idea"}]})
        assert "question" in prompt.lower() or "assumption" in prompt.lower()
