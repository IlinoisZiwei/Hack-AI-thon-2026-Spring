"""
Module 2 — 智能问题生成系统运行脚本
=================================

基于 Module 1 的缺口分析结果，为酒店生成针对性的调研问题。

使用方法:
    python -m module2.run <module1_output.json>             # 处理 Module 1 的 JSON 输出
    python -m module2.run --demo                            # 使用内置示例数据演示
    python -m module2.run --template-only                   # 仅使用模板，不调用 LLM
    python -m module2.run --batch <multiple_hotels.json>    # 批量处理多个酒店

输出:
    hotel_questions_<property_id>.json  — 为特定酒店生成的问题
    或 batch_questions_output.json       — 批量处理结果
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 导入项目配置
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from config import OPENAI_API_KEY
except ImportError:
    logger.warning("⚠️ 无法导入 config.py，将尝试从环境变量获取 API 密钥")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from .question_generator import generate_hotel_questions, process_multiple_hotels


def load_module1_output(file_path: str) -> Dict:
    """加载 Module 1 的 JSON 输出"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"✅ 成功加载 Module 1 输出: {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 解析错误: {e}")
        sys.exit(1)


def get_demo_data() -> Dict:
    """返回演示用的 Module 1 输出数据"""
    return {
        "property_id": "demo_hotel_001",
        "top_gaps": [
            {
                "dimension": "breakfast_hours",
                "label": "Breakfast Hours",
                "category": "policy",
                "reason": "never_mentioned",
                "reason_label": "No data yet",
                "priority": 3,
                "mention_count": 0,
                "last_mentioned": None,
                "dominant_stance": None,
                "official_info": None
            },
            {
                "dimension": "wifi_speed",
                "label": "WiFi & Internet",
                "category": "hardware",
                "reason": "stale",
                "reason_label": "Last mentioned 8 months ago",
                "priority": 2,
                "mention_count": 12,
                "last_mentioned": "2025-08-15",
                "dominant_stance": "negative",
                "official_info": "Free WiFi in all rooms and public areas"
            },
            {
                "dimension": "room_cleanliness",
                "label": "Room Cleanliness",
                "category": "service",
                "reason": "official_conflict",
                "reason_label": "Official info conflicts with reviews (15 negative)",
                "priority": 4,
                "mention_count": 28,
                "last_mentioned": "2026-03-10",
                "dominant_stance": "negative",
                "official_info": "Daily housekeeping with premium cleaning standards"
            },
            {
                "dimension": "staff_friendliness",
                "label": "Staff & Service",
                "category": "service",
                "reason": "conflicting",
                "reason_label": "Mixed reviews — 8 positive / 6 negative",
                "priority": 1,
                "mention_count": 14,
                "last_mentioned": "2026-04-01",
                "dominant_stance": "mixed",
                "official_info": None
            },
            {
                "dimension": "parking",
                "label": "Parking",
                "category": "policy",
                "reason": "stale",
                "reason_label": "Last mentioned 6 months ago",
                "priority": 2,
                "mention_count": 5,
                "last_mentioned": "2025-10-15",
                "dominant_stance": "neutral",
                "official_info": "Self-parking available for $15/night"
            }
        ]
    }


def save_results(results: Dict, output_path: str):
    """保存结果到 JSON 文件"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 结果已保存到: {output_path}")
    except Exception as e:
        logger.error(f"❌ 保存结果失败: {e}")


def display_results(results: Dict):
    """在终端中美观地显示结果"""
    print("\n" + "="*80)
    print("🏨 HOTEL QUESTION GENERATION RESULTS")
    print("="*80)

    property_id = results.get("property_id", "Unknown")
    print(f"🏨 Hotel: {property_id}")
    print(f"📝 Questions Generated: {results.get('questions_generated', 0)}")
    print(f"🛠️  Generation Method: {results.get('generation_method', 'unknown')}")
    print(f"📊 Input Gaps: {results.get('input_gaps_count', 0)}")

    print("\n" + "─"*80)
    print("GENERATED QUESTIONS:")
    print("─"*80)

    questions = results.get("questions", [])
    if not questions:
        print("❌ No questions generated")
        return

    for i, q in enumerate(questions, 1):
        question_text = q.get("question", "")
        gap_dim = q.get("gap_dimension", "")
        priority = q.get("priority", 0)
        source = q.get("source", "unknown")

        # 优先级图标
        priority_icon = {4: "🚨", 3: "⚠️", 2: "📋", 1: "📝"}.get(priority, "❓")

        print(f"\n{i:2d}. {priority_icon} [{gap_dim}]")
        print(f"    {question_text}")
        print(f"    Source: {source} | Priority: {priority}")

        if q.get("expected_outcome"):
            print(f"    Expected: {q['expected_outcome']}")

    print("\n" + "="*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Module 2: 智能问题生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m module2.run hotel_gaps.json           # 处理单个酒店
  python -m module2.run --demo                    # 运行演示
  python -m module2.run --template-only input.json  # 仅使用模板
  python -m module2.run --batch hotels.json       # 批量处理
        """
    )

    parser.add_argument("input_file", nargs="?",
                      help="Module 1 的 JSON 输出文件路径")
    parser.add_argument("--demo", action="store_true",
                      help="使用内置示例数据运行演示")
    parser.add_argument("--template-only", action="store_true",
                      help="仅使用模板生成问题，不调用 LLM")
    parser.add_argument("--batch", action="store_true",
                      help="批量处理多个酒店（输入文件应包含酒店数组）")
    parser.add_argument("--output", "-o",
                      help="输出文件路径（可选）")
    parser.add_argument("--max-questions", type=int, default=5,
                      help="每个酒店最大问题数量（默认5）")
    parser.add_argument("--no-display", action="store_true",
                      help="不在终端显示结果")

    args = parser.parse_args()

    # 验证输入
    if not args.demo and not args.input_file:
        parser.error("需要提供输入文件或使用 --demo 选项")

    # 获取 API 密钥
    api_key = OPENAI_API_KEY
    if not api_key or api_key.startswith("your_"):
        logger.warning("⚠️ 未配置有效的 OPENAI_API_KEY，将使用模板模式")
        api_key = None

    use_llm = not args.template_only and api_key is not None

    try:
        if args.demo:
            # 演示模式
            logger.info("🎯 运行演示模式")
            module1_data = get_demo_data()

            results = generate_hotel_questions(
                module1_data,
                openai_api_key=api_key,
                use_llm=use_llm,
                max_questions=args.max_questions
            )

            output_path = args.output or "demo_questions.json"

        elif args.batch:
            # 批量处理模式
            logger.info("📦 运行批量处理模式")
            hotels_data = load_module1_output(args.input_file)

            if not isinstance(hotels_data, list):
                logger.error("❌ 批量模式需要输入文件包含酒店数组")
                sys.exit(1)

            results = process_multiple_hotels(
                hotels_data,
                openai_api_key=api_key,
                use_llm=use_llm,
                max_questions=args.max_questions
            )

            output_path = args.output or "batch_questions_output.json"

            # 批量结果的特殊显示
            if not args.no_display:
                print(f"\n🏨 批量处理完成: {len(results)} 个酒店")
                success_count = sum(1 for r in results if r.get('success', True))
                print(f"✅ 成功: {success_count} | ❌ 失败: {len(results) - success_count}")

        else:
            # 单个酒店处理模式
            logger.info("🏨 运行单酒店处理模式")
            module1_data = load_module1_output(args.input_file)

            results = generate_hotel_questions(
                module1_data,
                openai_api_key=api_key,
                use_llm=use_llm,
                max_questions=args.max_questions
            )

            property_id = results.get("property_id", "unknown")[:12]
            output_path = args.output or f"hotel_questions_{property_id}.json"

        # 保存结果
        save_results(results, output_path)

        # 显示结果（除非是批量模式或用户禁用）
        if not args.no_display and not args.batch:
            display_results(results)

        logger.info("🎉 Module 2 运行完成！")

    except KeyboardInterrupt:
        logger.info("⏹️  用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()