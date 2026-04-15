"""
Module 2 — 缺口评分核心算法
==========================

为每个酒店×维度组合计算数值化的缺口评分 (0-100分)。
评分公式：gap_score = missing_weight + stale_weight + conflict_weight + business_priority_weight

设计原则：
- 分数越高 = 缺口越严重 = 越需要优先关注
- 四个权重维度相互补充，全面评估信息缺口
- 可配置的阈值参数，便于调优
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .business_weights import get_business_priority

logger = logging.getLogger(__name__)

# ═══ 评分参数配置 ═══════════════════════════════════════════════════════════════

class ScoringConfig:
    """缺口评分算法的参数配置"""

    # ── 缺失权重参数 ──────────────────────────────────────────────────
    MISSING_NO_DATA = 30.0           # 完全无数据（无评价+无官方信息）
    MISSING_LOW_MENTIONS = 20.0      # 提及次数很少 (1-2次)
    MISSING_THRESHOLD = 3            # 低提及次数阈值

    # ── 过时权重参数 ──────────────────────────────────────────────────
    STALE_DAYS_THRESHOLD = 180       # 6个月 - 开始被认为过时
    STALE_DAYS_MAX = 365            # 1年 - 完全过时
    STALE_WEIGHT_MAX = 25.0         # 最大过时权重

    # ── 冲突权重参数 ──────────────────────────────────────────────────
    CONFLICT_VARIANCE_THRESHOLD = 0.25    # 情感方差阈值
    CONFLICT_MIN_MENTIONS = 5             # 判定冲突的最小提及次数
    CONFLICT_SENTIMENT_WEIGHT = 15.0      # 评价情感冲突权重
    CONFLICT_OFFICIAL_WEIGHT = 25.0       # 官方信息冲突权重

    # ── 商业优先级缩放 ──────────────────────────────────────────────────
    BUSINESS_WEIGHT_SCALE = 1.0      # 商业权重的缩放因子


class GapScorer:
    """缺口评分计算器"""

    def __init__(self, config: Optional[ScoringConfig] = None):
        """
        初始化评分器

        Args:
            config: 评分参数配置，默认使用 ScoringConfig()
        """
        self.config = config or ScoringConfig()

    def compute_missing_weight(self, mention_count: int, has_official_info: bool) -> float:
        """
        计算缺失权重 - 基于提及次数和官方信息可用性

        Args:
            mention_count: 在评价中被提及的次数
            has_official_info: 是否有官方描述信息

        Returns:
            缺失权重分数 (0-30分)
        """
        if mention_count == 0 and not has_official_info:
            # 完全无信息 - 最高缺失权重
            return self.config.MISSING_NO_DATA

        if mention_count <= self.config.MISSING_THRESHOLD and not has_official_info:
            # 提及次数很少且无官方信息 - 高缺失权重
            return self.config.MISSING_LOW_MENTIONS

        if mention_count == 0 and has_official_info:
            # 有官方信息但缺乏客户验证 - 中等缺失权重
            return self.config.MISSING_LOW_MENTIONS * 0.6

        if mention_count <= self.config.MISSING_THRESHOLD:
            # 仅有少量提及 - 低缺失权重
            return self.config.MISSING_LOW_MENTIONS * 0.4

        return 0.0

    def compute_stale_weight(
        self,
        last_mentioned: Optional[str],
        current_date: Optional[datetime] = None
    ) -> float:
        """
        计算过时权重 - 基于最后提及时间的新鲜度

        Args:
            last_mentioned: 最后提及日期字符串 (YYYY-MM-DD格式)
            current_date: 参考日期，默认为今天

        Returns:
            过时权重分数 (0-25分)
        """
        if not last_mentioned:
            return 0.0

        if current_date is None:
            current_date = datetime.now()

        try:
            last_date = datetime.strptime(last_mentioned, "%Y-%m-%d")
            days_since = (current_date - last_date).days

            if days_since <= self.config.STALE_DAYS_THRESHOLD:
                # 还算新鲜 - 无过时权重
                return 0.0

            if days_since >= self.config.STALE_DAYS_MAX:
                # 完全过时 - 最大过时权重
                return self.config.STALE_WEIGHT_MAX

            # 线性插值计算过时程度
            staleness_ratio = (
                (days_since - self.config.STALE_DAYS_THRESHOLD) /
                (self.config.STALE_DAYS_MAX - self.config.STALE_DAYS_THRESHOLD)
            )
            return self.config.STALE_WEIGHT_MAX * staleness_ratio

        except ValueError:
            logger.warning(f"无法解析日期格式: {last_mentioned}")
            return 0.0

    def compute_conflict_weight(
        self,
        mention_count: int,
        stance_variance: float,
        has_official_conflict: bool,
        stance_counts: Optional[Dict[str, int]] = None
    ) -> float:
        """
        计算冲突权重 - 基于评价情感冲突和官方信息冲突

        Args:
            mention_count: 提及次数
            stance_variance: 情感方差 (0-0.5范围)
            has_official_conflict: 是否存在官方信息冲突
            stance_counts: 各情感类型的统计次数

        Returns:
            冲突权重分数 (0-25分)
        """
        conflict_weight = 0.0

        # 1. 官方信息冲突 - 最严重的冲突类型
        if has_official_conflict:
            conflict_weight += self.config.CONFLICT_OFFICIAL_WEIGHT

        # 2. 评价情感冲突 - 客户意见分化
        elif (mention_count >= self.config.CONFLICT_MIN_MENTIONS and
              stance_variance > self.config.CONFLICT_VARIANCE_THRESHOLD):
            # 根据冲突严重程度调整权重
            conflict_intensity = min(stance_variance / 0.5, 1.0)  # 标准化到0-1
            conflict_weight += self.config.CONFLICT_SENTIMENT_WEIGHT * conflict_intensity

            # 额外考虑：如果同时存在很多正面和负面评价，增加权重
            if stance_counts:
                pos_count = stance_counts.get("positive", 0)
                neg_count = stance_counts.get("negative", 0)
                if pos_count >= 3 and neg_count >= 3:
                    conflict_weight += 5.0  # 强烈分化的额外权重

        return round(conflict_weight, 2)

    def compute_gap_score(
        self,
        property_id: str,
        dimension: str,
        dimension_info: Dict,
        current_date: Optional[datetime] = None
    ) -> Dict:
        """
        计算单个酒店×维度的缺口评分

        Args:
            property_id: 酒店ID
            dimension: 维度名称
            dimension_info: 维度信息字典 (来自 Module 1 的 hotel_profiles)
            current_date: 参考日期

        Returns:
            包含评分详情的字典
        """
        # 提取维度信息
        mention_count = dimension_info.get("mention_count", 0)
        last_mentioned = dimension_info.get("last_mentioned")
        stance_variance = dimension_info.get("stance_variance", 0.0)
        has_official_info = dimension_info.get("has_official_info", False)
        has_official_conflict = dimension_info.get("official_conflict", False)
        stance_counts = dimension_info.get("stance_counts", {})

        # 计算各权重分量
        missing_weight = self.compute_missing_weight(mention_count, has_official_info)
        stale_weight = self.compute_stale_weight(last_mentioned, current_date)
        conflict_weight = self.compute_conflict_weight(
            mention_count, stance_variance, has_official_conflict, stance_counts
        )
        business_priority = get_business_priority(dimension) * self.config.BUSINESS_WEIGHT_SCALE

        # 计算总评分
        gap_score = missing_weight + stale_weight + conflict_weight + business_priority

        # 确定缺口原因标签
        reasons = []
        if missing_weight > 15:
            reasons.append("数据缺失" if mention_count == 0 else "提及不足")
        if stale_weight > 10:
            reasons.append("信息过时")
        if conflict_weight > 10:
            reasons.append("官方冲突" if has_official_conflict else "评价冲突")
        if business_priority > 15:
            reasons.append("高商业优先级")

        return {
            "eg_property_id": property_id,
            "dimension": dimension,
            "category": dimension_info.get("category", "unknown"),
            "label": dimension_info.get("label", dimension),
            "gap_score": round(gap_score, 2),
            "missing_weight": round(missing_weight, 2),
            "stale_weight": round(stale_weight, 2),
            "conflict_weight": round(conflict_weight, 2),
            "business_priority": round(business_priority, 2),
            "reason_breakdown": reasons,
            "mention_count": mention_count,
            "last_mentioned": last_mentioned,
            "dominant_stance": dimension_info.get("dominant_stance"),
            "stance_variance": stance_variance,
            "has_official_conflict": has_official_conflict,
        }


def compute_gap_scores(
    hotel_profiles: Dict[str, Dict[str, Dict]],
    current_date: Optional[datetime] = None,
    config: Optional[ScoringConfig] = None
) -> pd.DataFrame:
    """
    为所有酒店×维度组合批量计算缺口评分

    Args:
        hotel_profiles: Module 1 输出的酒店档案字典
                       格式: {property_id: {dimension: dimension_info}}
        current_date: 参考日期，默认为今天
        config: 评分配置，默认使用 ScoringConfig()

    Returns:
        包含所有评分记录的 DataFrame，按 gap_score 降序排列
    """
    scorer = GapScorer(config)

    all_scores = []

    for property_id, profile in hotel_profiles.items():
        for dimension, dimension_info in profile.items():
            score_record = scorer.compute_gap_score(
                property_id, dimension, dimension_info, current_date
            )
            all_scores.append(score_record)

    # 转换为 DataFrame 并按评分排序
    df = pd.DataFrame(all_scores)
    df = df.sort_values(["gap_score", "eg_property_id", "dimension"],
                       ascending=[False, True, True])

    logger.info(f"计算完成：{len(df)} 个酒店×维度的缺口评分")
    logger.info(f"评分范围：{df['gap_score'].min():.1f} - {df['gap_score'].max():.1f}")

    return df.reset_index(drop=True)


def get_top_gaps(
    gap_scores_df: pd.DataFrame,
    top_n: int = 50,
    min_score: float = 30.0,
    category_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    获取最需要关注的缺口列表

    Args:
        gap_scores_df: 缺口评分 DataFrame
        top_n: 返回前N个结果
        min_score: 最小评分阈值
        category_filter: 类别筛选 (hardware/service/surroundings/policy)

    Returns:
        筛选后的高优先级缺口 DataFrame
    """
    df = gap_scores_df.copy()

    # 应用筛选条件
    if min_score > 0:
        df = df[df["gap_score"] >= min_score]

    if category_filter:
        df = df[df["category"] == category_filter]

    # 限制返回数量
    df = df.head(top_n)

    logger.info(
        f"筛选条件: 最低评分={min_score}, 类别={category_filter or '全部'}, "
        f"结果数量={len(df)}"
    )

    return df


def analyze_gap_patterns(gap_scores_df: pd.DataFrame) -> Dict:
    """
    分析缺口评分的统计模式和趋势

    Args:
        gap_scores_df: 缺口评分 DataFrame

    Returns:
        包含统计分析结果的字典
    """
    df = gap_scores_df

    # 基础统计
    score_stats = df["gap_score"].describe()

    # 按类别统计
    category_stats = df.groupby("category")["gap_score"].agg([
        "count", "mean", "std", "min", "max"
    ]).round(2)

    # 转换为更友好的字典格式
    category_breakdown = {}
    for category in category_stats.index:
        category_breakdown[category] = {
            "count": int(category_stats.loc[category, "count"]),
            "mean": round(category_stats.loc[category, "mean"], 2),
            "std": round(category_stats.loc[category, "std"], 2),
            "min": round(category_stats.loc[category, "min"], 2),
            "max": round(category_stats.loc[category, "max"], 2),
        }

    # 缺口原因分析
    reason_counts = {}
    for reasons in df["reason_breakdown"]:
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    # 高分缺口 (>= 50分) 分析
    high_score_gaps = df[df["gap_score"] >= 50.0]

    return {
        "total_gaps": len(df),
        "score_distribution": {
            "mean": round(score_stats["mean"], 2),
            "std": round(score_stats["std"], 2),
            "min": round(score_stats["min"], 2),
            "max": round(score_stats["max"], 2),
            "median": round(score_stats["50%"], 2),
        },
        "category_breakdown": category_breakdown,
        "reason_frequency": dict(sorted(reason_counts.items(),
                                       key=lambda x: x[1], reverse=True)),
        "high_priority_gaps": {
            "count": len(high_score_gaps),
            "percentage": round(len(high_score_gaps) / len(df) * 100, 1),
            "avg_score": round(high_score_gaps["gap_score"].mean(), 2) if len(high_score_gaps) > 0 else 0,
        }
    }