"""
Module 2 — 缺口评分系统运行脚本
==============================

演示如何使用 Module 2 的缺口评分功能。
支持与 Module 1 的集成，以及独立的评分分析。

使用方法:
    python -m module2.run
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_gap_scoring():
    """演示缺口评分系统的基本用法"""

    print("🏨 Module 2 缺口评分系统演示")
    print("=" * 50)

    # 尝试加载 Module 1 的输出数据
    try:
        from module1.run import main as module1_main
        from module1.profiler import build_hotel_profiles

        print("📊 正在运行 Module 1 生成酒店档案...")
        # 这里应该从 Module 1 获取 hotel_profiles
        # 为了演示，我们创建一些模拟数据

        # 模拟酒店档案数据
        hotel_profiles = create_mock_hotel_profiles()
        print(f"✅ 加载了 {len(hotel_profiles)} 个酒店的档案数据")

    except ImportError:
        logger.warning("无法导入 Module 1，使用模拟数据进行演示")
        hotel_profiles = create_mock_hotel_profiles()

    # 导入 Module 2 功能
    from .gap_scorer import compute_gap_scores, get_top_gaps, analyze_gap_patterns
    from .business_weights import get_weight_stats

    print("\n📈 计算缺口评分...")

    # 计算所有缺口评分
    gap_scores_df = compute_gap_scores(hotel_profiles)

    print(f"✅ 完成评分计算，共 {len(gap_scores_df)} 条记录")
    print(f"📊 评分范围: {gap_scores_df['gap_score'].min():.1f} - {gap_scores_df['gap_score'].max():.1f}")

    # 显示商业权重统计
    print("\n🎯 商业权重分布:")
    weight_stats = get_weight_stats()
    for key, value in weight_stats.items():
        print(f"   {key}: {value}")

    # 显示前10个最需要关注的缺口
    print("\n🚨 前10个最需要关注的缺口:")
    top_gaps = get_top_gaps(gap_scores_df, top_n=10, min_score=30.0)
    if len(top_gaps) > 0:
        for _, row in top_gaps.head(10).iterrows():
            print(f"   🏨 {row['eg_property_id'][:12]}... | "
                  f"{row['label']:<20} | "
                  f"评分: {row['gap_score']:.1f} | "
                  f"原因: {', '.join(row['reason_breakdown'])}")
    else:
        print("   ✅ 未发现高优先级缺口")

    # 分析缺口模式
    print("\n📈 缺口模式分析:")
    analysis = analyze_gap_patterns(gap_scores_df)

    print(f"   总缺口数量: {analysis['total_gaps']}")
    print(f"   平均评分: {analysis['score_distribution']['mean']}")
    print(f"   高优先级缺口: {analysis['high_priority_gaps']['count']} "
          f"({analysis['high_priority_gaps']['percentage']}%)")

    print("\n📊 按类别分布:")
    for category, stats in analysis['category_breakdown'].items():
        print(f"   {category:<12}: "
              f"{stats['count']:3d}个 | "
              f"平均评分 {stats['mean']:4.1f} | "
              f"范围 {stats['min']:4.1f}-{stats['max']:4.1f}")

    print("\n🔍 主要缺口原因:")
    for reason, count in list(analysis['reason_frequency'].items())[:5]:
        print(f"   {reason:<12}: {count:3d} 次")

    # 保存结果
    output_file = Path("gap_scores_output.csv")
    gap_scores_df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"\n💾 评分结果已保存至: {output_file}")

    return gap_scores_df


def create_mock_hotel_profiles():
    """创建模拟的酒店档案数据用于演示"""

    from datetime import datetime, timedelta
    import random

    # 模拟3个酒店的档案
    hotel_profiles = {}

    # 导入维度定义
    try:
        from module1.dimensions import ALL_DIMENSIONS, DIMENSIONS
    except ImportError:
        # 如果无法导入，使用简化的维度定义
        ALL_DIMENSIONS = [
            "wifi_speed", "room_cleanliness", "location_convenience",
            "front_desk_efficiency", "parking", "breakfast_quality"
        ]
        DIMENSIONS = {dim: {"category": "service", "label": dim.replace("_", " ").title()}
                     for dim in ALL_DIMENSIONS}

    hotel_ids = [
        "hotel_downtown_001",
        "hotel_airport_002",
        "hotel_business_003"
    ]

    for hotel_id in hotel_ids:
        hotel_profiles[hotel_id] = {}

        for dimension in ALL_DIMENSIONS:
            # 随机生成维度信息，模拟真实的缺口场景
            mention_count = random.choices([0, 1, 2, 5, 8, 15, 25],
                                         weights=[2, 2, 2, 3, 3, 2, 1])[0]

            if mention_count > 0:
                # 有提及的维度
                last_date = datetime.now() - timedelta(days=random.randint(1, 400))
                last_mentioned = last_date.strftime("%Y-%m-%d")
                stance_variance = random.uniform(0.0, 0.4)
                dominant_stance = random.choice(["positive", "negative", "neutral", "mixed"])

                stance_counts = {
                    "positive": random.randint(0, mention_count),
                    "negative": random.randint(0, mention_count),
                    "mixed": random.randint(0, 2),
                    "neutral": random.randint(0, 3),
                }
            else:
                # 无提及的维度
                last_mentioned = None
                stance_variance = 0.0
                dominant_stance = None
                stance_counts = {"positive": 0, "negative": 0, "mixed": 0, "neutral": 0}

            # 随机决定是否有官方信息和冲突
            has_official_info = random.choice([True, False])
            official_conflict = (has_official_info and
                               dominant_stance == "negative" and
                               mention_count >= 3 and
                               random.choice([True, False]))

            hotel_profiles[hotel_id][dimension] = {
                "category": DIMENSIONS.get(dimension, {}).get("category", "service"),
                "label": DIMENSIONS.get(dimension, {}).get("label", dimension.replace("_", " ").title()),
                "mention_count": mention_count,
                "last_mentioned": last_mentioned,
                "dominant_stance": dominant_stance,
                "stance_counts": stance_counts,
                "stance_variance": stance_variance,
                "has_official_info": has_official_info,
                "official_conflict": official_conflict,
                "official_info": f"官方描述: {dimension}" if has_official_info else None,
            }

    return hotel_profiles


def main():
    """主函数"""
    try:
        demo_gap_scoring()
        print("\n✅ Module 2 演示完成！")
    except Exception as e:
        logger.error(f"运行失败: {e}")
        raise


if __name__ == "__main__":
    main()