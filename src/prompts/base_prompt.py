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
        """Get document text with optional context and analysis situation prepended"""
        text = document.get("text", "")
        context = document.get("context", "")
        analysis_situation = document.get("analysis_situation", "")

        parts = []

        # Add analysis situation first (highest priority framing)
        if analysis_situation:
            parts.append(analysis_situation)

        # Add background context (imported files, etc.)
        if context:
            parts.append(f"BACKGROUND CONTEXT:\n{context}")

        # Add the actual document
        parts.append(f"DOCUMENT:\n{text}")

        return "\n\n".join(parts)
