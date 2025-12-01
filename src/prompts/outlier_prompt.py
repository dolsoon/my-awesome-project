"""
Outlier Detection Mode Prompt Template
Identifies unique contributions that stand out from the group
"""

from typing import Dict, Any
from .base_prompt import PromptTemplate


class OutlierPromptTemplate(PromptTemplate):
    """Prompt template for Outlier detection mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate outlier detection prompt"""
        full_context = self._get_full_context(document)

        return f"""Analyze this document for outlier detection.

{full_context}

Instructions:
- Identify the most unique idea or contribution (outlier)
- Extract the EXACT TEXT from the document that represents this unique contribution (5-20 words)
- Rate similarity to other ideas on a scale of 0.0 (unique) to 1.0 (similar)
- Provide a CONCISE encouragement message (1-2 sentences maximum, direct and specific)
- Return JSON: {{"outlier_found": bool, "target_text": str, "unique_aspect": str, "similarity_score": float, "confidence": float, "encouragement_message": str}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the document above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text
- The "encouragement_message" must be 1-2 sentences, concise and actionable"""
