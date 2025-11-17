"""
Connect Mode Prompt Template
Finds connections between ideas from different authors
"""

from typing import Dict, Any
from .base_prompt import PromptTemplate


class ConnectPromptTemplate(PromptTemplate):
    """Prompt template for Connect mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate connection detection prompt"""
        contributions_text = self._format_contributions(document)
        return f"""Find connections between ideas from different authors.

{contributions_text}

Instructions:
- Find pairs of ideas from different authors that are similar or complementary
- Extract the EXACT TEXT from one of the connected ideas (5-20 words)
- Do NOT connect ideas from the same author
- Provide a CONCISE connection message (1-2 sentences maximum, specific and actionable)
- Return JSON: {{"target_text": str, "connections": [{{"author1": str, "author2": str, "common_theme": str, "connection_message": str}}], "confidence": float}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the contributions above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text
- The "connection_message" must be 1-2 sentences, concise and actionable"""
