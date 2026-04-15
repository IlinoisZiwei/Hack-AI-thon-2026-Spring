"""
Module 2 — 酒店维度缺口评分系统
=================================

将 Module 1 的定性缺口分析转化为定量评分系统。
为每个酒店×维度组合计算 0-100 分的缺口评分，用于优先级排序。

主要功能：
- 数值化的缺口评分算法
- 商业优先级权重分配
- 批量评分和排序功能
"""

from .gap_scorer import compute_gap_scores, GapScorer
from .business_weights import BUSINESS_WEIGHTS, get_business_priority

__version__ = "1.0.0"

__all__ = [
    "compute_gap_scores",
    "GapScorer",
    "BUSINESS_WEIGHTS",
    "get_business_priority",
]