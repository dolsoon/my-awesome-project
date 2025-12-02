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
- Estimate what percentile this outlier ranks (e.g., 0.05 = top 5%, 0.10 = top 10%)
- Provide a CONCISE encouragement message that mentions their top X% ranking (1-2 sentences, actionable)
- Return JSON: {{"target_text": str, "unique_aspect": str, "outlier_percentile": float, "encouragement_message": str}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the document above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text

OUTPUT REQUIREMENTS:
- "outlier_percentile" should be between 0.01 (top 1%) and 0.50 (top 50%)
- "encouragement_message" MUST reference the percentile (e.g., "Your idea ranks in the top 5%...")
- Keep the message concise and actionable"""
