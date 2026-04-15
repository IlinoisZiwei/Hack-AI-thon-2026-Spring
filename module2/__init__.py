"""
Module 2 — Intelligent Question Generator
==========================================

Generates targeted survey questions for each hotel based on
Module 1 gap analysis results. Combines question templates with
LLM enhancement to provide specific, actionable survey directions
for hotel operations teams.

Key Features:
- Generates structured questions based on gap types
- Uses LLM to enhance question specificity and naturalness
- Template fallback mechanism to avoid over-reliance on API
- Generates questions of varying depth for different priority gaps
"""

from .question_generator import QuestionGenerator, generate_hotel_questions
from .question_templates import QUESTION_TEMPLATES, get_template_question

__version__ = "2.0.0"

__all__ = [
    "QuestionGenerator",
    "generate_hotel_questions",
    "QUESTION_TEMPLATES",
    "get_template_question",
]