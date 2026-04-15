"""
Module 2 — 问题模板系统
======================

为不同类型的酒店服务缺口定义结构化的问题模板。
这些模板既可以直接使用，也可以作为 LLM 增强的基础。

设计原则：
- 基于缺口原因和优先级生成针对性问题
- 问题具体可操作，便于酒店运营团队实施
- 涵盖数据收集、问题诊断、改进方案等多个层面
"""

import random
from typing import Dict, List


# ═══ 基础问题模板 ═══════════════════════════════════════════════════════════════

QUESTION_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    # ── 从未提及的维度（优先级3）──────────────────────────────────────────────
    "never_mentioned": {
        "direct_feedback": [
            "您觉得{label}怎么样？",
            "请评价一下{label}的体验",
            "您对{label}满意吗？",
            "{label}符合您的期望吗？",
        ],
        "simple_rating": [
            "{label}好不好？",
            "您觉得{label}如何？",
            "{label}的质量怎么样？",
        ],
    },

    # ── 信息过时的维度（优先级2）──────────────────────────────────────────────
    "stale": {
        "current_experience": [
            "这次入住时{label}怎么样？",
            "您最近体验的{label}如何？",
            "现在的{label}好用吗？",
            "目前{label}的情况怎样？",
        ],
        "updated_feedback": [
            "{label}现在的状况如何？",
            "您觉得现在的{label}怎么样？",
            "这次{label}的体验好吗？",
        ],
    },

    # ── 评价冲突的维度（优先级1）──────────────────────────────────────────────
    "conflicting": {
        "clarifying_experience": [
            "您这次{label}的体验怎么样？",
            "请问{label}让您满意吗？",
            "您觉得{label}表现如何？",
            "这次{label}给您的感受怎样？",
        ],
        "specific_rating": [
            "{label}好不好用？",
            "{label}的质量怎么样？",
            "您对{label}的评价是？",
        ],
    },

    # ── 官方信息冲突（优先级4）────────────────────────────────────────────────
    "official_conflict": {
        "reality_check": [
            "实际的{label}体验怎么样？",
            "{label}和您预期的一样吗？",
            "您觉得{label}达到宣传的标准了吗？",
            "入住后{label}的实际情况如何？",
        ],
        "expectation_vs_reality": [
            "{label}符合您的预期吗？",
            "实际的{label}好不好？",
            "{label}和描述的一致吗？",
        ],
    },
}


# ═══ 按类别的专业问题 ═══════════════════════════════════════════════════════════

CATEGORY_SPECIFIC_QUESTIONS: Dict[str, List[str]] = {
    "hardware": [
        "设施好用吗？",
        "设备运行正常吗？",
        "硬件设施满意吗？",
    ],
    "service": [
        "服务怎么样？",
        "员工态度好吗？",
        "服务质量满意吗？",
    ],
    "surroundings": [
        "周边环境怎么样？",
        "位置方便吗？",
        "周围噪音大不大？",
    ],
    "policy": [
        "酒店政策合理吗？",
        "规定容易理解吗？",
        "政策执行得好吗？",
    ],
}


# ═══ 问题生成辅助函数 ═══════════════════════════════════════════════════════════

def get_template_question(gap_info: Dict, question_type: str = "mixed") -> str:
    """
    基于缺口信息生成模板化问题

    Args:
        gap_info: 缺口信息字典（来自 Module 1）
        question_type: 问题类型 ("data_collection", "service_audit", 等)

    Returns:
        格式化的问题字符串
    """
    reason = gap_info.get("reason", "never_mentioned")
    label = gap_info.get("label", gap_info.get("dimension", "未知服务"))
    category = gap_info.get("category", "service")

    # 获取原因对应的问题模板
    reason_templates = QUESTION_TEMPLATES.get(reason, QUESTION_TEMPLATES["never_mentioned"])

    # 选择问题类型
    if question_type == "mixed":
        # 随机选择一个问题类型
        question_type = random.choice(list(reason_templates.keys()))

    questions = reason_templates.get(question_type, reason_templates[list(reason_templates.keys())[0]])
    selected_question = random.choice(questions)

    # 格式化问题
    format_params = {
        "label": label,
        "dimension": gap_info.get("dimension", ""),
        "last_mentioned": gap_info.get("last_mentioned", "很久之前"),
        "dominant_stance": gap_info.get("dominant_stance", "中性"),
        "mention_count": gap_info.get("mention_count", 0),
    }

    try:
        formatted_question = selected_question.format(**format_params)
    except KeyError:
        # 如果格式化失败，返回原问题
        formatted_question = selected_question.replace("{label}", label)

    return formatted_question


def generate_template_questions(gap_list: List[Dict], max_questions: int = 5) -> List[Dict]:
    """
    为缺口列表生成模板化问题

    Args:
        gap_list: 缺口信息列表
        max_questions: 最大问题数量

    Returns:
        问题列表，每个包含 question 和 metadata
    """
    questions = []

    for i, gap in enumerate(gap_list[:max_questions]):
        # 基于优先级选择问题深度
        priority = gap.get("priority", 2)
        if priority >= 4:  # 最高优先级
            question_type = "immediate_action"
        elif priority >= 3:
            question_type = "service_audit"
        elif priority >= 2:
            question_type = "current_status"
        else:
            question_type = "mixed"

        question = get_template_question(gap, question_type)

        # 添加类别特定问题
        category = gap.get("category", "service")
        if category in CATEGORY_SPECIFIC_QUESTIONS and len(questions) < max_questions:
            category_question = random.choice(CATEGORY_SPECIFIC_QUESTIONS[category])
            category_question = category_question.replace("相关", gap.get("label", "相关"))

            questions.extend([
                {
                    "question": question,
                    "source": "template",
                    "gap_dimension": gap.get("dimension"),
                    "gap_reason": gap.get("reason"),
                    "priority": priority,
                    "question_type": question_type,
                },
                {
                    "question": category_question,
                    "source": "template_category",
                    "gap_dimension": gap.get("dimension"),
                    "gap_reason": gap.get("reason"),
                    "priority": priority,
                    "question_type": "category_specific",
                }
            ])
        else:
            questions.append({
                "question": question,
                "source": "template",
                "gap_dimension": gap.get("dimension"),
                "gap_reason": gap.get("reason"),
                "priority": priority,
                "question_type": question_type,
            })

    return questions[:max_questions]


# ═══ 问题质量评估 ═══════════════════════════════════════════════════════════════

def assess_question_relevance(question: str, gap_info: Dict) -> float:
    """
    评估问题与缺口的相关性 (0.0-1.0)

    简单的关键词匹配算法，可以后续用更复杂的语义相似度替换
    """
    question_lower = question.lower()
    label_lower = gap_info.get("label", "").lower()
    dimension_lower = gap_info.get("dimension", "").lower()

    # 基础相关性评分
    relevance = 0.0

    # 检查维度/标签关键词
    if label_lower in question_lower or dimension_lower in question_lower:
        relevance += 0.4

    # 检查原因相关关键词
    reason = gap_info.get("reason", "")
    reason_keywords = {
        "never_mentioned": ["收集", "了解", "评估", "建立"],
        "stale": ["当前", "最近", "更新", "监控"],
        "conflicting": ["分歧", "一致", "稳定", "标准"],
        "official_conflict": ["官方", "承诺", "实际", "差距"],
    }

    if reason in reason_keywords:
        for keyword in reason_keywords[reason]:
            if keyword in question_lower:
                relevance += 0.15

    # 检查可操作性关键词
    action_keywords = ["如何", "什么", "哪些", "是否", "需要"]
    for keyword in action_keywords:
        if keyword in question_lower:
            relevance += 0.1
            break

    return min(relevance, 1.0)