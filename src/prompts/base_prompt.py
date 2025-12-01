"""
Base Prompt Template
Abstract class for mode-specific prompt templates
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class PromptTemplate(ABC):
    """Abstract base class for mode-specific prompt templates"""

    @abstractmethod
    def generate(self, document: Dict[str, Any]) -> str:
        """Generate prompt for specific mode"""
        pass

    def _get_full_context(self, document: Dict) -> str:
        """Get document text with optional context prepended"""
        text = document.get("text", "")
        context = document.get("context", "")

        if context:
            return f"CONTEXT:\n{context}\n\nDOCUMENT:\n{text}"
        return text
