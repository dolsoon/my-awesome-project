"""
Prompt Templates for AI Facilitation Modes
Each mode has its own file for easy management and editing
"""

from .base_prompt import PromptTemplate
from .outlier_prompt import OutlierPromptTemplate
from .summary_prompt import SummaryPromptTemplate
from .connect_prompt import ConnectPromptTemplate
from .question_prompt import QuestionPromptTemplate

__all__ = [
    'PromptTemplate',
    'OutlierPromptTemplate',
    'SummaryPromptTemplate',
    'ConnectPromptTemplate',
    'QuestionPromptTemplate',
]
