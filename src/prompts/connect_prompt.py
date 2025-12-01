"""
Connect Mode Prompt Template
Finds connections between different ideas in the document
"""

from typing import Dict, Any
from .base_prompt import PromptTemplate


class ConnectPromptTemplate(PromptTemplate):
    """Prompt template for Connect mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate connection detection prompt"""
        full_context = self._get_full_context(document)

        return f"""Find connections between different ideas in this document.

{full_context}

Instructions:
- Find pairs of ideas that are similar or complementary
- Extract the EXACT TEXT from one of the connected ideas (5-20 words)
- Provide a CONCISE connection message (1-2 sentences maximum, specific and actionable)
- Return JSON: {{"target_text": str, "connections": [{{"idea1": str, "idea2": str, "common_theme": str, "connection_message": str}}], "confidence": float}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the document above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text
- The "connection_message" must be 1-2 sentences, concise and actionable"""
