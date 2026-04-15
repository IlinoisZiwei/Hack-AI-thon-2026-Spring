"""
Module 2 — Question Template System
=====================================

Defines structured question templates for different types of hotel service gaps.
These templates can be used directly or as a basis for LLM-enhanced generation.

Design Principles:
- Generate targeted questions based on gap type and priority
- Questions are specific and actionable for hotel operations teams
- Cover data collection, issue diagnosis, and improvement dimensions
"""

import random
from typing import Dict, List


# ═══ Base Question Templates ═══════════════════════════════════════════════════

QUESTION_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    # ── Never-mentioned dimensions (Priority 3) ─────────────────────────────
    "never_mentioned": {
        "direct_feedback": [
            "How would you rate the {label}?",
            "What was your experience with the {label}?",
            "Were you satisfied with the {label}?",
            "Did the {label} meet your expectations?",
        ],
        "simple_rating": [
            "Was the {label} good?",
            "How was the {label}?",
            "How would you describe the quality of {label}?",
        ],
    },

    # ── Stale/outdated dimensions (Priority 2) ──────────────────────────────
    "stale": {
        "current_experience": [
            "How was the {label} during this stay?",
            "What was {label} like on your recent visit?",
            "Did the {label} work well this time?",
            "How is the {label} currently?",
        ],
        "updated_feedback": [
            "What's the current state of {label}?",
            "How do you feel about the {label} now?",
            "Was the {label} good this time?",
        ],
    },

    # ── Conflicting reviews (Priority 1) ────────────────────────────────────
    "conflicting": {
        "clarifying_experience": [
            "How was your experience with {label} this time?",
            "Were you satisfied with {label}?",
            "How would you say {label} performed?",
            "What was your impression of {label}?",
        ],
        "specific_rating": [
            "Did {label} work well for you?",
            "How would you rate the quality of {label}?",
            "What's your take on {label}?",
        ],
    },

    # ── Official info conflicts (Priority 4) ────────────────────────────────
    "official_conflict": {
        "reality_check": [
            "How was the actual {label} experience?",
            "Did {label} match what you expected?",
            "Do you feel {label} lived up to the advertised standard?",
            "What was {label} actually like after checking in?",
        ],
        "expectation_vs_reality": [
            "Did {label} meet your expectations?",
            "Was the actual {label} good?",
            "Did {label} match the description?",
        ],
    },
}


# ═══ Category-Specific Questions ═══════════════════════════════════════════════

CATEGORY_SPECIFIC_QUESTIONS: Dict[str, List[str]] = {
    "hardware": [
        "Were the facilities in good working order?",
        "Did the equipment function properly?",
        "Were you satisfied with the room amenities?",
    ],
    "service": [
        "How was the service?",
        "Was the staff friendly and helpful?",
        "Were you satisfied with the service quality?",
    ],
    "surroundings": [
        "How was the surrounding area?",
        "Was the location convenient?",
        "Was it noisy around the hotel?",
    ],
    "policy": [
        "Were the hotel policies reasonable?",
        "Were the rules easy to understand?",
        "Were the policies applied consistently?",
    ],
}


# ═══ Question Generation Helpers ═══════════════════════════════════════════════

def get_template_question(gap_info: Dict, question_type: str = "mixed") -> str:
    """
    Generate a template-based question from gap information.

    Args:
        gap_info: Gap info dictionary (from Module 1)
        question_type: Question type ("data_collection", "service_audit", etc.)

    Returns:
        Formatted question string
    """
    reason = gap_info.get("reason", "never_mentioned")
    label = gap_info.get("label", gap_info.get("dimension", "this service"))
    category = gap_info.get("category", "service")

    # Get templates for the gap reason
    reason_templates = QUESTION_TEMPLATES.get(reason, QUESTION_TEMPLATES["never_mentioned"])

    # Select question type
    if question_type == "mixed":
        # Randomly select a question type
        question_type = random.choice(list(reason_templates.keys()))

    questions = reason_templates.get(question_type, reason_templates[list(reason_templates.keys())[0]])
    selected_question = random.choice(questions)

    # Format the question
    format_params = {
        "label": label,
        "dimension": gap_info.get("dimension", ""),
        "last_mentioned": gap_info.get("last_mentioned", "a long time ago"),
        "dominant_stance": gap_info.get("dominant_stance", "neutral"),
        "mention_count": gap_info.get("mention_count", 0),
    }

    try:
        formatted_question = selected_question.format(**format_params)
    except KeyError:
        # If formatting fails, return the question with basic substitution
        formatted_question = selected_question.replace("{label}", label)

    return formatted_question


def generate_template_questions(gap_list: List[Dict], max_questions: int = 5) -> List[Dict]:
    """
    Generate template-based questions for a list of gaps.

    Args:
        gap_list: List of gap info dictionaries
        max_questions: Maximum number of questions

    Returns:
        List of questions, each containing question text and metadata
    """
    questions = []

    for i, gap in enumerate(gap_list[:max_questions]):
        # Select question depth based on priority
        priority = gap.get("priority", 2)
        if priority >= 4:  # Highest priority
            question_type = "immediate_action"
        elif priority >= 3:
            question_type = "service_audit"
        elif priority >= 2:
            question_type = "current_status"
        else:
            question_type = "mixed"

        question = get_template_question(gap, question_type)

        # Add category-specific question
        category = gap.get("category", "service")
        if category in CATEGORY_SPECIFIC_QUESTIONS and len(questions) < max_questions:
            category_question = random.choice(CATEGORY_SPECIFIC_QUESTIONS[category])

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


# ═══ Question Quality Assessment ═══════════════════════════════════════════════

def assess_question_relevance(question: str, gap_info: Dict) -> float:
    """
    Assess question relevance to a gap (0.0-1.0).

    Simple keyword-matching algorithm; can be replaced with
    more sophisticated semantic similarity later.
    """
    question_lower = question.lower()
    label_lower = gap_info.get("label", "").lower()
    dimension_lower = gap_info.get("dimension", "").lower()

    # Base relevance score
    relevance = 0.0

    # Check dimension/label keywords
    if label_lower in question_lower or dimension_lower in question_lower:
        relevance += 0.4

    # Check reason-related keywords
    reason = gap_info.get("reason", "")
    reason_keywords = {
        "never_mentioned": ["collect", "understand", "assess", "establish", "rate", "experience"],
        "stale": ["current", "recent", "update", "now", "this time", "today"],
        "conflicting": ["clarify", "consistent", "stable", "standard", "impression"],
        "official_conflict": ["official", "advertised", "actual", "match", "expect"],
    }

    if reason in reason_keywords:
        for keyword in reason_keywords[reason]:
            if keyword in question_lower:
                relevance += 0.15

    # Check actionability keywords
    action_keywords = ["how", "what", "which", "did", "were", "was", "do you"]
    for keyword in action_keywords:
        if keyword in question_lower:
            relevance += 0.1
            break

    return min(relevance, 1.0)