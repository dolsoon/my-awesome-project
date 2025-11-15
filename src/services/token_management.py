"""
Token Management Service
SPEC-AI-FACIL-001 Phase 2: Token counting and context truncation
Minimal implementation for TDD GREEN phase
"""

from typing import Dict, Any, Optional
import tiktoken


class TokenManager:
    """Manages token counting and context truncation"""

    def __init__(self, max_tokens: int = 128000):
        """Initialize TokenManager"""
        self.max_tokens = max_tokens

        # Initialize tiktoken
        try:
            self.model_encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.model_encoding = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.model_encoding is None:
            # Fallback: rough estimation
            return len(text) // 4
        try:
            return len(self.model_encoding.encode(text))
        except Exception:
            return len(text) // 4

    def count_tokens_for_document(self, document: Dict[str, Any]) -> int:
        """Count total tokens for document"""
        total = 0

        # Count contributions
        for contrib in document.get("contributions", []):
            total += self.count_tokens(contrib.get("text", ""))
            total += self.count_tokens(contrib.get("author", ""))

        # Count context files
        for context_file in document.get("context_files", []):
            total += self.count_tokens(context_file.get("content", ""))

        return total

    def check_token_limit(self, tokens_used: int) -> Optional[str]:
        """Check if approaching token limit and return warning"""
        if tokens_used > self.max_tokens * 0.9:  # 90% threshold
            return f"Warning: Using {tokens_used}/{self.max_tokens} tokens (90% of limit)"
        return None

    def truncate_context(self, document: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Truncate document to fit token limit"""
        truncated = {
            "document_id": document.get("document_id"),
            "contributions": document.get("contributions", []).copy(),
            "context_files": document.get("context_files", []).copy()
        }

        # Count context file tokens
        context_tokens = sum(
            self.count_tokens(f.get("content", ""))
            for f in truncated["context_files"]
        )

        current_tokens = context_tokens
        contributions = list(truncated["contributions"])

        # Sort by timestamp (oldest first)
        contributions.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=False
        )

        # Remove oldest contributions until under limit
        kept_contributions = []
        for contrib in reversed(contributions):
            contrib_tokens = (
                self.count_tokens(contrib.get("text", "")) +
                self.count_tokens(contrib.get("author", ""))
            )
            if current_tokens + contrib_tokens <= max_tokens:
                kept_contributions.insert(0, contrib)
                current_tokens += contrib_tokens

        truncated["contributions"] = kept_contributions
        return truncated
