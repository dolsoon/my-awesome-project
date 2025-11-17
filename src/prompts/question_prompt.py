"""
Question Mode Prompt Template
Generates Socratic questions to deepen contributor thinking
"""

from typing import Dict, Any
from .base_prompt import PromptTemplate


class QuestionPromptTemplate(PromptTemplate):
    """Prompt template for Question mode"""

    def generate(self, document: Dict[str, Any]) -> str:
        """Generate Socratic questioning prompt"""
        contributions_text = self._format_contributions(document)
        return f"""Generate Socratic questions to deepen contributor thinking.

{contributions_text}

Instructions:
- Select a contributor whose ideas could be deepened
- Extract the EXACT TEXT from their contribution that needs deepening (5-20 words)
- Ask 1-2 CONCISE clarifying questions (specific and thought-provoking)
- Use Socratic method to encourage critical thinking
- Return JSON: {{"target_text": str, "target_author": str, "clarifying_questions": [str], "confidence": float}}

CRITICAL - TARGET_TEXT REQUIREMENTS:
- The "target_text" MUST be copied EXACTLY character-for-character from the contributions above
- Do NOT paraphrase, rephrase, summarize, or modify the text in ANY way
- Copy-paste the text VERBATIM - it must match the original word-for-word
- If you cannot find exact text to copy, return empty string "" for target_text
- Questions must be concise (1-2 questions maximum), specific and actionable"""
