"""
Summary Mode Prompt Template
Identifies recurring themes and clusters across the document
"""

from typing import Dict, Any
from .base_prompt import PromptTemplate


class SummaryPromptTemplate(PromptTemplate):
    """Prompt template for Summary mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate summary and clustering prompt"""
        full_context = self._get_full_context(document)

        return f"""Analyze this document for clustering and theme identification.

{full_context}

Instructions:
- Identify recurring themes or clusters
- Extract the EXACT TEXT representing the most prominent theme (5-20 words)
- Provide a CONCISE summary (1-2 sentences maximum, highlighting key patterns)
- Return JSON: {{"target_text": str, "themes": [str], "summary": str, "confidence": float}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the document above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text
- The "summary" must be 1-2 sentences, concise and actionable"""
