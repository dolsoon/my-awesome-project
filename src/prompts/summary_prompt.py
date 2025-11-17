"""
Summary Mode Prompt Template
Identifies recurring themes and clusters across contributions
"""

from typing import Dict, Any
from .base_prompt import PromptTemplate


class SummaryPromptTemplate(PromptTemplate):
    """Prompt template for Summary mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate summary and clustering prompt"""
        contributions_text = self._format_contributions(document)
        return f"""Analyze these contributions for clustering and theme identification.

{contributions_text}

Instructions:
- Identify recurring themes or clusters
- Extract the EXACT TEXT representing the most prominent theme (5-20 words)
- Provide a CONCISE summary (1-2 sentences maximum, highlighting key patterns)
- Return JSON: {{"target_text": str, "themes": [str], "summary": str, "contributor_count": int, "confidence": float}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the contributions above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text
- The "summary" must be 1-2 sentences, concise and actionable"""
