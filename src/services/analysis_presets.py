"""
Analysis context preset configurations.
Predefined situational contexts for different types of collaborative sessions.
"""

from typing import Dict, TypedDict


class ContextPreset(TypedDict):
    """Type definition for analysis context preset."""
    name: str
    description: str
    context: str


ANALYSIS_CONTEXT_PRESETS: Dict[str, ContextPreset] = {
    "collaborative_feedback": {
        "name": "Collaborative Feedback Session",
        "description": "Multiple people giving feedback on presentations/proposals",
        "context": """ANALYSIS SITUATION:
This is a collaborative feedback session where multiple people have contributed their thoughts and comments.
The document contains feedback from various participants on a presentation or proposal.

TARGET AUDIENCE:
Comments should be directed at the individual contributor's ideas and perspectives, not the document itself.
Focus on the person's specific contribution and their unique thinking.

PURPOSE:
- Encourage differential thinking and unique perspectives
- Highlight what makes each contribution valuable or distinctive
- Provide constructive feedback that helps the contributor develop their ideas
- Foster diverse viewpoints and creative approaches"""
    },
    "research_review": {
        "name": "Research/Academic Review",
        "description": "Reviewing research documents or academic work",
        "context": """ANALYSIS SITUATION:
This is a research or academic review session where participants are reviewing scholarly work.

TARGET AUDIENCE:
Comments should address the intellectual content and methodology.
Focus on the rigor, clarity, and contribution to the field.

PURPOSE:
- Identify strengths and areas for improvement in the research
- Encourage rigorous thinking and evidence-based arguments
- Support the development of scholarly work"""
    },
    "brainstorming": {
        "name": "Brainstorming Session",
        "description": "Creative ideation and brainstorming",
        "context": """ANALYSIS SITUATION:
This is a brainstorming session where participants are generating and sharing creative ideas.

TARGET AUDIENCE:
Comments should encourage idea generation and creative thinking.
Focus on building upon ideas rather than critiquing.

PURPOSE:
- Foster creativity and innovative thinking
- Encourage bold and unconventional ideas
- Build connections between different concepts"""
    }
}


def get_preset(key: str) -> ContextPreset | None:
    """Get a preset by key."""
    return ANALYSIS_CONTEXT_PRESETS.get(key)


def list_preset_keys() -> list[str]:
    """List available preset keys."""
    return list(ANALYSIS_CONTEXT_PRESETS.keys())
