"""
LLM Analysis Service
SPEC-AI-FACIL-001 Phase 2: LLM-powered analysis with 4 agent modes
Minimal implementation for TDD GREEN phase
"""

import json
import re
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
import tiktoken


class PromptTemplate(ABC):
    """Abstract base class for mode-specific prompt templates"""

    @abstractmethod
    def generate(self, document: Dict[str, Any]) -> str:
        """Generate prompt for specific mode"""
        pass


class OutlierPromptTemplate(PromptTemplate):
    """Prompt template for Outlier detection mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate outlier detection prompt"""
        contributions_text = self._format_contributions(document)
        context_files_text = self._format_context_files(document)

        full_context = contributions_text
        if context_files_text:
            full_context = f"{context_files_text}\n\n{contributions_text}"

        return f"""Analyze these collaborative contributions for outlier detection.

{full_context}

Instructions:
- Identify the most unique contribution (outlier)
- Rate similarity to other contributions on a scale of 0.0 (unique) to 1.0 (similar)
- Provide encouragement message for the unique contributor
- Return JSON: {{"outlier_found": bool, "unique_aspect": str, "similarity_score": float, "confidence": float, "encouragement_message": str}}"""

    def _format_contributions(self, document: Dict) -> str:
        """Format contributions for prompt"""
        lines = []
        for contrib in document.get("contributions", []):
            author = contrib.get('author', 'Anonymous')
            text = contrib.get('text', '')
            lines.append(f"{author}: {text}")
        return "\n".join(lines)

    def _format_context_files(self, document: Dict) -> str:
        """Format context files for prompt"""
        if not document.get("context_files"):
            return ""
        lines = ["CONTEXT FILES:"]
        for ctx_file in document.get("context_files", []):
            filename = ctx_file.get("filename", "unknown")
            content = ctx_file.get("content", "")
            lines.append(f"[{filename}] {content}")
        return "\n".join(lines)


class SummaryPromptTemplate(PromptTemplate):
    """Prompt template for Summary mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate summary and clustering prompt"""
        contributions_text = self._format_contributions(document)
        return f"""Analyze these contributions for clustering and theme identification.

{contributions_text}

Instructions:
- Identify recurring themes or clusters
- Group similar ideas together
- Summarize main themes and discussion patterns
- Return JSON: {{"themes": [str], "summary": str, "contributor_count": int, "confidence": float}}"""

    def _format_contributions(self, document: Dict) -> str:
        """Format contributions for prompt"""
        lines = []
        for contrib in document.get("contributions", []):
            author = contrib.get('author', 'Anonymous')
            text = contrib.get('text', '')
            lines.append(f"{author}: {text}")
        return "\n".join(lines)


class ConnectPromptTemplate(PromptTemplate):
    """Prompt template for Connect mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate connection detection prompt"""
        contributions_text = self._format_contributions(document)
        return f"""Find connections between ideas from different authors.

{contributions_text}

Instructions:
- Find pairs of ideas from different authors that are similar or complementary
- Do NOT connect ideas from the same author
- Explain the connection and suggest collaboration
- Return JSON: {{"connections": [{{"author1": str, "author2": str, "common_theme": str, "connection_message": str}}], "confidence": float}}"""

    def _format_contributions(self, document: Dict) -> str:
        """Format contributions for prompt"""
        lines = []
        for contrib in document.get("contributions", []):
            author = contrib.get('author', 'Anonymous')
            text = contrib.get('text', '')
            lines.append(f"{author}: {text}")
        return "\n".join(lines)


class QuestionPromptTemplate(PromptTemplate):
    """Prompt template for Question mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate Socratic questioning prompt"""
        contributions_text = self._format_contributions(document)
        return f"""Generate Socratic questions to deepen contributor thinking.

{contributions_text}

Instructions:
- Select a contributor whose ideas could be deepened
- Ask clarifying questions based on their assumptions
- Use Socratic method to encourage critical thinking
- Return JSON: {{"target_author": str, "clarifying_questions": [str], "confidence": float}}"""

    def _format_contributions(self, document: Dict) -> str:
        """Format contributions for prompt"""
        lines = []
        for contrib in document.get("contributions", []):
            author = contrib.get('author', 'Anonymous')
            text = contrib.get('text', '')
            lines.append(f"{author}: {text}")
        return "\n".join(lines)


class LLMService:
    """LLM analysis service with 4 agent modes"""

    VALID_MODES = ["outlier", "summary", "connect", "question"]

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        """Initialize LLM service"""
        self.api_key = api_key
        self.model = model
        self.max_tokens = 128000
        self.confidence_threshold = 0.7

        # Initialize tiktoken for token counting
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

        # Prompt templates
        self.templates = {
            "outlier": OutlierPromptTemplate(),
            "summary": SummaryPromptTemplate(),
            "connect": ConnectPromptTemplate(),
            "question": QuestionPromptTemplate()
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        if self.encoding is None:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
        try:
            return len(self.encoding.encode(text))
        except Exception:
            return len(text) // 4

    def count_tokens_for_document(self, document: Dict[str, Any]) -> int:
        """Count total tokens for document including context files"""
        total = 0

        # Count contributions
        for contrib in document.get("contributions", []):
            total += self.count_tokens(contrib.get("text", ""))
            total += self.count_tokens(contrib.get("author", ""))

        # Count context files
        for context_file in document.get("context_files", []):
            total += self.count_tokens(context_file.get("content", ""))
            total += self.count_tokens(context_file.get("filename", ""))

        return total

    def truncate_context(self, document: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Truncate document context to fit within token limit"""
        truncated = {
            "document_id": document.get("document_id"),
            "contributions": list(document.get("contributions", [])),
            "context_files": document.get("context_files", []).copy()
        }

        # Always preserve context files
        context_tokens = sum(
            self.count_tokens(f["content"]) + self.count_tokens(f["filename"])
            for f in truncated["context_files"]
        )

        current_tokens = context_tokens
        contributions = truncated["contributions"]

        # Sort by timestamp (oldest first) to remove oldest first
        contributions_sorted = sorted(
            contributions,
            key=lambda x: x.get("timestamp", ""),
            reverse=False
        )

        # Keep contributions in reverse order (newest first)
        kept_contributions = []
        for contrib in reversed(contributions_sorted):
            contrib_tokens = (
                self.count_tokens(contrib.get("text", "")) +
                self.count_tokens(contrib.get("author", ""))
            )
            if current_tokens + contrib_tokens <= max_tokens:
                kept_contributions.insert(0, contrib)
                current_tokens += contrib_tokens

        truncated["contributions"] = kept_contributions
        return truncated

    def _generate_outlier_prompt(self, document: Dict[str, Any]) -> str:
        """Generate outlier detection prompt"""
        return self.templates["outlier"].generate(document)

    def _generate_summary_prompt(self, document: Dict[str, Any]) -> str:
        """Generate summary prompt"""
        return self.templates["summary"].generate(document)

    def _generate_connect_prompt(self, document: Dict[str, Any]) -> str:
        """Generate connection prompt"""
        return self.templates["connect"].generate(document)

    def _generate_question_prompt(self, document: Dict[str, Any]) -> str:
        """Generate Socratic question prompt"""
        return self.templates["question"].generate(document)

    def _parse_structured_response(self, response: str) -> Optional[Dict]:
        """Parse structured JSON response from LLM"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return None

    def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API (mocked for now)"""
        # This will be mocked in tests
        raise NotImplementedError("Must be implemented by subclass or mocked in tests")

    def analyze(
        self,
        document: Dict[str, Any],
        mode: str = "outlier"
    ) -> Optional[Dict[str, Any]]:
        """Analyze document with specified mode"""
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self.VALID_MODES}")

        # Generate mode-specific prompt
        if mode == "outlier":
            prompt = self._generate_outlier_prompt(document)
        elif mode == "summary":
            prompt = self._generate_summary_prompt(document)
        elif mode == "connect":
            prompt = self._generate_connect_prompt(document)
        elif mode == "question":
            prompt = self._generate_question_prompt(document)

        try:
            # Call LLM API
            response = self._call_llm_api(prompt)
            parsed = self._parse_structured_response(json.dumps(response))

            # Check confidence threshold
            if parsed and parsed.get("confidence", 0) >= self.confidence_threshold:
                return parsed
            return None

        except TimeoutError:
            return None
        except Exception as e:
            return {"error": str(e)}
