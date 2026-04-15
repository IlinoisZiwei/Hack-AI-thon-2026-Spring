"""
Module 2 — 智能问题生成核心引擎
===============================

结合 LLM 增强和模板回退的问题生成系统。
基于 Module 1 的缺口分析，为每个酒店生成5个具体可操作的调研问题。

设计特点：
- 优先使用 LLM 生成个性化问题
- 模板作为回退机制，确保系统鲁棒性
- 智能控制 API 使用，避免过度消耗
- 问题质量评估和筛选机制
"""

import datetime
import json
import logging
import os
import random
from typing import Dict, List, Optional, Tuple

from .question_templates import generate_template_questions, assess_question_relevance

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """智能问题生成器"""

    def __init__(self, openai_api_key: Optional[str] = None, use_llm: bool = True):
        """
        初始化问题生成器

        Args:
            openai_api_key: OpenAI API 密钥
            use_llm: 是否使用 LLM 增强（默认 True，失败时自动回退到模板）
        """
        self.use_llm = use_llm
        self.openai_client = None

        if use_llm and openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("✅ OpenAI 客户端初始化成功")
            except ImportError:
                logger.warning("⚠️ 未安装 openai 库，将使用模板模式")
                self.use_llm = False
            except Exception as e:
                logger.warning(f"⚠️ OpenAI 客户端初始化失败: {e}，将使用模板模式")
                self.use_llm = False
        else:
            self.use_llm = False

    def generate_llm_questions(
        self,
        property_id: str,
        top_gaps: List[Dict],
        max_questions: int = 5
    ) -> List[Dict]:
        """
        使用 LLM 生成个性化问题

        Args:
            property_id: 酒店 ID
            top_gaps: 前 N 个缺口列表
            max_questions: 最大问题数量

        Returns:
            问题列表，包含问题文本和元数据
        """
        if not self.openai_client:
            logger.warning("OpenAI 客户端不可用，使用模板回退")
            return generate_template_questions(top_gaps, max_questions)

        try:
            # 构建 LLM 提示
            prompt = self._build_llm_prompt(property_id, top_gaps, max_questions)

            # 调用 OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # 使用成本较低的模型
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位经验丰富的客户体验专家，专门设计简单易懂的客户调研问题来收集酒店反馈。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            # 解析响应
            llm_output = json.loads(response.choices[0].message.content)
            questions = self._parse_llm_response(llm_output, top_gaps)

            logger.info(f"✅ LLM 生成了 {len(questions)} 个问题")
            return questions

        except Exception as e:
            logger.warning(f"⚠️ LLM 问题生成失败: {e}，使用模板回退")
            return generate_template_questions(top_gaps, max_questions)

    def _build_llm_prompt(self, property_id: str, top_gaps: List[Dict], max_questions: int) -> str:
        """构建 LLM 提示词"""

        # 缺口信息摘要
        gaps_summary = []
        for gap in top_gaps[:max_questions]:
            reason_cn = {
                "never_mentioned": "缺乏数据",
                "stale": "信息过时",
                "conflicting": "评价冲突",
                "official_conflict": "官方冲突"
            }.get(gap.get("reason"), gap.get("reason", ""))

            category_cn = {
                "hardware": "硬件设施",
                "service": "服务体验",
                "surroundings": "周边环境",
                "policy": "酒店政策"
            }.get(gap.get("category"), gap.get("category", ""))

            gap_desc = f"- {gap.get('label', '')}: {reason_cn} (优先级{gap.get('priority', 0)}, {category_cn})"
            if gap.get("reason_label"):
                gap_desc += f" - {gap.get('reason_label')}"
            gaps_summary.append(gap_desc)

        prompt = f"""
请为酒店ID {property_id[:12]}... 的以下服务缺口生成 {max_questions} 个简单易答的客户调研问题：

识别的关键缺口：
{chr(10).join(gaps_summary)}

要求：
1. 问题应该简单易懂，客人能够快速回答
2. 避免复杂的专业术语，使用口语化表达
3. 重点收集关于缺失或过时信息的反馈
4. 问题要让客人感到轻松，不会造成负担
5. 例如："WiFi快不快？"、"早餐好吃吗？"、"晚上噪音大不大？"这样的风格

请以 JSON 格式返回，结构如下：
{{
  "questions": [
    {{
      "question": "简单易答的问题内容",
      "target_gap": "对应的缺口维度",
      "question_type": "问题类型(如: simple_feedback, rating_request, experience_check)",
      "priority_level": "优先级(high/medium/low)",
      "expected_outcome": "收集到的信息类型"
    }}
  ]
}}
"""
        return prompt

    def _parse_llm_response(self, llm_output: Dict, top_gaps: List[Dict]) -> List[Dict]:
        """解析 LLM 响应并格式化"""
        questions = []

        if "questions" not in llm_output:
            logger.warning("LLM 响应格式异常，使用模板回退")
            return generate_template_questions(top_gaps, 5)

        for i, q_data in enumerate(llm_output["questions"]):
            if not isinstance(q_data, dict) or "question" not in q_data:
                continue

            # 匹配对应的缺口信息
            target_gap = q_data.get("target_gap", "")
            matched_gap = None
            for gap in top_gaps:
                if (gap.get("dimension", "") in target_gap or
                    gap.get("label", "") in target_gap):
                    matched_gap = gap
                    break

            if not matched_gap and i < len(top_gaps):
                matched_gap = top_gaps[i]

            question_info = {
                "question": q_data["question"],
                "source": "llm_enhanced",
                "gap_dimension": matched_gap.get("dimension") if matched_gap else "",
                "gap_reason": matched_gap.get("reason") if matched_gap else "",
                "priority": matched_gap.get("priority") if matched_gap else 2,
                "question_type": q_data.get("question_type", "general"),
                "expected_outcome": q_data.get("expected_outcome", ""),
                "llm_priority": q_data.get("priority_level", "medium"),
            }

            # 评估问题质量
            if matched_gap:
                relevance = assess_question_relevance(q_data["question"], matched_gap)
                question_info["relevance_score"] = relevance

            questions.append(question_info)

        return questions

    def generate_questions(
        self,
        property_id: str,
        top_gaps: List[Dict],
        max_questions: int = 5
    ) -> List[Dict]:
        """
        生成问题的主入口方法

        Args:
            property_id: 酒店 ID
            top_gaps: 缺口列表
            max_questions: 最大问题数量

        Returns:
            问题列表
        """
        if not top_gaps:
            logger.warning(f"酒店 {property_id[:12]}... 没有识别到缺口")
            return []

        # 尝试 LLM 生成
        if self.use_llm and self.openai_client:
            questions = self.generate_llm_questions(property_id, top_gaps, max_questions)
        else:
            questions = generate_template_questions(top_gaps, max_questions)

        # 确保问题数量不超过限制
        questions = questions[:max_questions]

        # 添加生成时间戳
        import datetime
        for q in questions:
            q["generated_at"] = datetime.datetime.now().isoformat()

        logger.info(f"为酒店 {property_id[:12]}... 生成了 {len(questions)} 个问题")
        return questions


def generate_hotel_questions(
    module1_output: Dict,
    openai_api_key: Optional[str] = None,
    use_llm: bool = True,
    max_questions: int = 5
) -> Dict:
    """
    基于 Module 1 输出生成酒店问题

    Args:
        module1_output: Module 1 的 JSON 输出
        openai_api_key: OpenAI API 密钥
        use_llm: 是否使用 LLM
        max_questions: 每个酒店最大问题数

    Returns:
        包含问题的结果字典
    """
    generator = QuestionGenerator(openai_api_key, use_llm)

    property_id = module1_output.get("property_id", "")
    top_gaps = module1_output.get("top_gaps", [])

    if not property_id:
        logger.error("Module 1 输出缺少 property_id")
        return {"error": "Missing property_id in Module 1 output"}

    questions = generator.generate_questions(property_id, top_gaps, max_questions)

    # 构建输出结果
    result = {
        "property_id": property_id,
        "questions_generated": len(questions),
        "generation_method": "llm_enhanced" if (generator.use_llm and generator.openai_client) else "template_based",
        "questions": questions,
        "input_gaps_count": len(top_gaps),
        "gaps_processed": top_gaps,
        "timestamp": datetime.datetime.now().isoformat()
    }

    return result


def process_multiple_hotels(
    module1_results: List[Dict],
    openai_api_key: Optional[str] = None,
    use_llm: bool = True,
    max_questions: int = 5
) -> List[Dict]:
    """
    批量处理多个酒店的问题生成

    Args:
        module1_results: 多个酒店的 Module 1 输出列表
        openai_api_key: OpenAI API 密钥
        use_llm: 是否使用 LLM
        max_questions: 每个酒店最大问题数

    Returns:
        所有酒店问题生成结果的列表
    """
    generator = QuestionGenerator(openai_api_key, use_llm)
    results = []

    for hotel_data in module1_results:
        try:
            property_id = hotel_data.get("property_id", "")
            top_gaps = hotel_data.get("top_gaps", [])

            questions = generator.generate_questions(property_id, top_gaps, max_questions)

            result = {
                "property_id": property_id,
                "questions_generated": len(questions),
                "questions": questions,
                "success": True
            }
            results.append(result)

        except Exception as e:
            logger.error(f"处理酒店 {hotel_data.get('property_id', 'unknown')} 失败: {e}")
            results.append({
                "property_id": hotel_data.get("property_id", "unknown"),
                "questions_generated": 0,
                "questions": [],
                "success": False,
                "error": str(e)
            })

    logger.info(f"批量处理完成: {len(results)} 个酒店")
    return results