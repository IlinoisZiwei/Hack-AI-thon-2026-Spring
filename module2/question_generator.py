"""
Module 2 — Intelligent Question Generation Engine
===================================================

Combines LLM-enhanced and template-fallback question generation.
Based on Module 1 gap analysis, generates specific, actionable survey
questions for each hotel.

Design Features:
- Prioritizes LLM for personalized question generation
- Templates serve as fallback to ensure system robustness
- Smart API usage control to avoid over-consumption
- Question quality assessment and filtering
"""

import datetime
import json
import logging
import os
import random
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .question_templates import generate_template_questions, assess_question_relevance
from module1.extractor import extract_rule_based
from module1.dimensions import DIMENSIONS

logger = logging.getLogger(__name__)


LOW_FRICTION_KEYWORDS = {
    "wifi", "internet", "parking", "breakfast", "pool", "gym",
    "noise", "quiet", "location", "pet", "check", "shuttle",
    "elevator", "air conditioning", "heater", "water", "shower"
}


def _build_review_row(
    review_text: str,
    review_title: str = "",
    rating_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    full_text = f"{review_title} {review_text}".strip().lower()
    return {
        "review_text_clean": full_text,
        "rating_dict": rating_dict or {},
    }


def _extract_review_mentions(
    review_text: str,
    review_title: str = "",
    rating_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    row = _build_review_row(
        review_text=review_text,
        review_title=review_title,
        rating_dict=rating_dict,
    )
    return extract_rule_based(row)


def _mentioned_dimensions(mentions: List[Dict[str, Any]]) -> Set[str]:
    return {
        m.get("dimension")
        for m in mentions
        if m.get("dimension")
    }


def _mentioned_categories(mentioned_dims: Set[str]) -> Set[str]:
    cats = set()
    for dim in mentioned_dims:
        if dim in DIMENSIONS:
            cats.add(DIMENSIONS[dim].get("category"))
    return {c for c in cats if c}


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-zA-Z]+", (text or "").lower()))


def _normalize_gap_importance(gap: Dict[str, Any], max_gap_score: float) -> float:
    """
    Normalize gap importance to [0,1].
    Prefer gap_score if present, otherwise fall back to priority.
    """
    try:
        gap_score = float(gap.get("gap_score", 0))
    except (TypeError, ValueError):
        gap_score = 0.0

    if max_gap_score > 0:
        return min(max(gap_score / max_gap_score, 0.0), 1.0)

    try:
        priority = float(gap.get("priority", 2))
    except (TypeError, ValueError):
        priority = 2.0

    return min(max(priority / 4.0, 0.0), 1.0)


def _compute_review_relevance(
    gap: Dict[str, Any],
    review_text: str,
    mentioned_categories: Set[str],
) -> float:
    """
    Relevance to this review:
    - boost if gap category matches what the user is already talking about
    - boost if label/dimension tokens overlap with review text
    - small boost if review uses problem/contrast language
    """
    score = 0.0

    gap_category = gap.get("category", "")
    if gap_category and gap_category in mentioned_categories:
        score += 0.55

    review_tokens = _tokenize(review_text)
    gap_tokens = (
        _tokenize(str(gap.get("dimension", "")).replace("_", " "))
        | _tokenize(str(gap.get("label", "")))
    )

    overlap = review_tokens & gap_tokens
    if gap_tokens:
        score += min(0.30, 0.10 * len(overlap))

    if re.search(r"\bbut\b|\bhowever\b|\bissue\b|\bproblem\b|\bnot\b|\bno\b", review_text.lower()):
        if gap.get("reason") in {"conflicting", "official_conflict", "stale"}:
            score += 0.10

    return min(score, 1.0)


def _ease_of_answering(gap: Dict[str, Any]) -> float:
    """
    Higher score = easier for the user to answer quickly.
    """
    dim = str(gap.get("dimension", "")).lower().replace("_", " ")
    label = str(gap.get("label", "")).lower()
    category = str(gap.get("category", "")).lower()

    text = f"{dim} {label}"

    if any(k in text for k in LOW_FRICTION_KEYWORDS):
        return 1.0
    if category == "policy":
        return 0.90
    if category == "surroundings":
        return 0.85
    if category == "hardware":
        return 0.80
    if category == "service":
        return 0.75
    return 0.75


def select_candidate_gaps_for_review(
    module1_output: Dict[str, Any],
    review_text: str,
    review_title: str = "",
    rating_dict: Optional[Dict[str, Any]] = None,
    max_questions: int = 2,
    min_selector_score: float = 0.55,
) -> Dict[str, Any]:
    """
    Selection policy:
    1. generate candidate gaps from hotel profile
    2. remove dimensions already mentioned by the reviewer
    3. rank remaining gaps by:
       - gap score
       - relevance to user review
       - ease of answering
    4. ask top 1-2 only if score passes threshold
    """
    property_id = module1_output.get("property_id", "")
    top_gaps = module1_output.get("top_gaps", []) or []

    mentions = _extract_review_mentions(
        review_text=review_text,
        review_title=review_title,
        rating_dict=rating_dict,
    )
    mentioned_dims = _mentioned_dimensions(mentions)
    mentioned_cats = _mentioned_categories(mentioned_dims)

    numeric_scores = []
    for gap in top_gaps:
        try:
            numeric_scores.append(float(gap.get("gap_score", 0)))
        except (TypeError, ValueError):
            pass
    max_gap_score = max(numeric_scores) if numeric_scores else 0.0

    review_full_text = f"{review_title} {review_text}".strip()

    selected = []
    for gap in top_gaps:
        dim = gap.get("dimension")
        if not dim:
            continue

        # remove dimensions already mentioned by reviewer
        if dim in mentioned_dims:
            continue

        importance = _normalize_gap_importance(gap, max_gap_score)
        relevance = _compute_review_relevance(gap, review_full_text, mentioned_cats)
        ease = _ease_of_answering(gap)

        selector_score = (
            0.55 * importance
            + 0.30 * relevance
            + 0.15 * ease
        )

        if selector_score >= min_selector_score:
            enriched_gap = {
                **gap,
                "selector_score": round(selector_score, 4),
                "selector_components": {
                    "gap_importance": round(importance, 4),
                    "review_relevance": round(relevance, 4),
                    "ease_of_answering": round(ease, 4),
                },
            }
            selected.append(enriched_gap)

    selected.sort(
        key=lambda x: (
            x.get("selector_score", 0),
            x.get("gap_score", 0),
            x.get("priority", 0),
        ),
        reverse=True,
    )

    selected = selected[:max_questions]

    return {
        "property_id": property_id,
        "mentioned_dimensions": sorted(mentioned_dims),
        "review_mentions": mentions,
        "selected_gaps": selected,
        "selection_policy": {
            "max_questions": max_questions,
            "min_selector_score": min_selector_score,
            "weights": {
                "gap_importance": 0.55,
                "review_relevance": 0.30,
                "ease_of_answering": 0.15,
            },
        },
    }


class QuestionGenerator:
    """Intelligent Question Generator"""

    def __init__(self, openai_api_key: Optional[str] = None, use_llm: bool = True):
        """
        Initialize the question generator.

        Args:
            openai_api_key: OpenAI API key
            use_llm: Whether to use LLM enhancement (default True, auto-falls back to templates on failure)
        """
        self.use_llm = use_llm
        self.openai_client = None

        if use_llm and openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("✅ OpenAI client initialized successfully")
            except ImportError:
                logger.warning("⚠️ openai library not installed, falling back to template mode")
                self.use_llm = False
            except Exception as e:
                logger.warning(f"⚠️ OpenAI client initialization failed: {e}, falling back to template mode")
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
        Generate personalized questions using LLM.

        Args:
            property_id: Hotel ID
            top_gaps: Top N gap list
            max_questions: Maximum number of questions

        Returns:
            List of questions with text and metadata
        """
        if not self.openai_client:
            logger.warning("OpenAI client unavailable, using template fallback")
            return generate_template_questions(top_gaps, max_questions)

        try:
            prompt = self._build_llm_prompt(property_id, top_gaps, max_questions)

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced customer experience expert who specializes in designing simple, easy-to-understand survey questions to collect hotel feedback from guests."
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

            llm_output = json.loads(response.choices[0].message.content)
            questions = self._parse_llm_response(llm_output, top_gaps)

            logger.info(f"✅ LLM generated {len(questions)} questions")
            return questions

        except Exception as e:
            logger.warning(f"⚠️ LLM question generation failed: {e}, using template fallback")
            return generate_template_questions(top_gaps, max_questions)

    def _build_llm_prompt(self, property_id: str, top_gaps: List[Dict], max_questions: int) -> str:
        """Build the LLM prompt."""
        gaps_summary = []
        for gap in top_gaps[:max_questions]:
            reason_en = {
                "never_mentioned": "No data available",
                "stale": "Outdated information",
                "conflicting": "Conflicting reviews",
                "official_conflict": "Official info conflict"
            }.get(gap.get("reason"), gap.get("reason", ""))

            category_en = {
                "hardware": "Hardware & Facilities",
                "service": "Service Experience",
                "surroundings": "Surroundings & Location",
                "policy": "Hotel Policies"
            }.get(gap.get("category"), gap.get("category", ""))

            gap_desc = f"- {gap.get('label', '')}: {reason_en} (Priority {gap.get('priority', 0)}, {category_en})"
            if gap.get("reason_label"):
                gap_desc += f" - {gap.get('reason_label')}"
            gaps_summary.append(gap_desc)

        prompt = f"""
Please generate {max_questions} simple, easy-to-answer guest survey questions for hotel ID {property_id[:12]}... based on the following service gaps:

Identified key gaps:
{chr(10).join(gaps_summary)}

Requirements:
1. Questions should be simple and easy to understand, allowing guests to answer quickly
2. Avoid complex jargon; use casual, conversational language
3. Focus on collecting feedback about missing or outdated information
4. Questions should feel lightweight and not burden the guest
5. Style examples: "How was the WiFi speed?", "Was breakfast good?", "Was it noisy at night?"

Please return in JSON format with this structure:
{{
  "questions": [
    {{
      "question": "Simple, easy-to-answer question",
      "target_gap": "Corresponding gap dimension",
      "question_type": "Question type (e.g.: simple_feedback, rating_request, experience_check)",
      "priority_level": "Priority (high/medium/low)",
      "expected_outcome": "Type of information to collect"
    }}
  ]
}}
"""
        return prompt

    def _parse_llm_response(self, llm_output: Dict, top_gaps: List[Dict]) -> List[Dict]:
        """Parse LLM response and format it."""
        questions = []

        if "questions" not in llm_output:
            logger.warning("LLM response format unexpected, using template fallback")
            return generate_template_questions(top_gaps, 5)

        for i, q_data in enumerate(llm_output["questions"]):
            if not isinstance(q_data, dict) or "question" not in q_data:
                continue

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
        Main entry point for question generation.

        Args:
            property_id: Hotel ID
            top_gaps: List of gaps
            max_questions: Maximum number of questions

        Returns:
            List of questions
        """
        if not top_gaps:
            logger.warning(f"Hotel {property_id[:12]}... has no identified gaps")
            return []

        if self.use_llm and self.openai_client:
            questions = self.generate_llm_questions(property_id, top_gaps, max_questions)
        else:
            questions = generate_template_questions(top_gaps, max_questions)

        questions = questions[:max_questions]

        for q in questions:
            q["generated_at"] = datetime.datetime.now().isoformat()

        logger.info(f"Generated {len(questions)} questions for hotel {property_id[:12]}...")
        return questions


def generate_hotel_questions(
    module1_output: Dict,
    openai_api_key: Optional[str] = None,
    use_llm: bool = True,
    max_questions: int = 5
) -> Dict:
    """
    Generate hotel questions based on Module 1 output.

    Args:
        module1_output: Module 1 JSON output
        openai_api_key: OpenAI API key
        use_llm: Whether to use LLM
        max_questions: Max questions per hotel

    Returns:
        Result dictionary containing questions
    """
    generator = QuestionGenerator(openai_api_key, use_llm)

    property_id = module1_output.get("property_id", "")
    top_gaps = module1_output.get("top_gaps", [])

    if not property_id:
        logger.error("Module 1 output missing property_id")
        return {"error": "Missing property_id in Module 1 output"}

    questions = generator.generate_questions(property_id, top_gaps, max_questions)

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


def generate_personalized_questions_for_review(
    module1_output: Dict,
    review_text: str,
    review_title: str = "",
    rating_dict: Optional[Dict] = None,
    openai_api_key: Optional[str] = None,
    use_llm: bool = True,
    max_questions: int = 2,
    min_selector_score: float = 0.55,
) -> Dict:
    """
    Personalized question generation for one live review.
    This is the function that fulfills the hackathon-style selection policy.
    """
    selection = select_candidate_gaps_for_review(
        module1_output=module1_output,
        review_text=review_text,
        review_title=review_title,
        rating_dict=rating_dict,
        max_questions=max_questions,
        min_selector_score=min_selector_score,
    )

    property_id = selection.get("property_id", "")
    selected_gaps = selection.get("selected_gaps", [])

    if not property_id:
        logger.error("Module 1 output missing property_id")
        return {"error": "Missing property_id in Module 1 output"}

    generator = QuestionGenerator(openai_api_key, use_llm)

    if not selected_gaps:
        return {
            "property_id": property_id,
            "questions_generated": 0,
            "generation_method": "none_below_threshold",
            "questions": [],
            "selected_gaps": [],
            "selection_metadata": selection,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    questions = generator.generate_questions(
        property_id=property_id,
        top_gaps=selected_gaps,
        max_questions=max_questions,
    )

    return {
        "property_id": property_id,
        "questions_generated": len(questions),
        "generation_method": "llm_enhanced" if (generator.use_llm and generator.openai_client) else "template_based",
        "questions": questions,
        "selected_gaps": selected_gaps,
        "selection_metadata": selection,
        "timestamp": datetime.datetime.now().isoformat(),
    }


def process_multiple_hotels(
    module1_results: List[Dict],
    openai_api_key: Optional[str] = None,
    use_llm: bool = True,
    max_questions: int = 5
) -> List[Dict]:
    """
    Batch process question generation for multiple hotels.

    Args:
        module1_results: List of Module 1 outputs for multiple hotels
        openai_api_key: OpenAI API key
        use_llm: Whether to use LLM
        max_questions: Max questions per hotel

    Returns:
        List of question generation results for all hotels
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
            logger.error(f"Failed to process hotel {hotel_data.get('property_id', 'unknown')}: {e}")
            results.append({
                "property_id": hotel_data.get("property_id", "unknown"),
                "questions_generated": 0,
                "questions": [],
                "success": False,
                "error": str(e)
            })

    logger.info(f"Batch processing complete: {len(results)} hotels")
    return results