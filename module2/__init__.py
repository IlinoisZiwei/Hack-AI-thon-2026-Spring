"""
Module 2 — 智能问题生成器
=========================

基于 Module 1 的缺口分析结果，为每个酒店生成针对性的调研问题。
结合问题模板和 LLM 增强，为酒店运营团队提供具体可操作的调研方向。

主要功能：
- 基于缺口类型生成结构化问题
- 使用 LLM 增强问题的针对性和自然性
- 支持模板回退机制，避免过度依赖 API
- 为不同优先级的缺口生成不同深度的问题
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