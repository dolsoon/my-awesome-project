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
