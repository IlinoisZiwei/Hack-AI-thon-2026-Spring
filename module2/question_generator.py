"""
Module 2 — Intelligent Question Generation Engine
===================================================

Combines LLM-enhanced and template-fallback question generation.
Based on Module 1 gap analysis, generates 5 specific, actionable survey
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
from typing import Dict, List, Optional, Tuple

from .question_templates import generate_template_questions, assess_question_relevance

logger = logging.getLogger(__name__)


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
            # Build LLM prompt
            prompt = self._build_llm_prompt(property_id, top_gaps, max_questions)

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cost-effective model
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

            # Parse response
            llm_output = json.loads(response.choices[0].message.content)
            questions = self._parse_llm_response(llm_output, top_gaps)

            logger.info(f"✅ LLM generated {len(questions)} questions")
            return questions

        except Exception as e:
            logger.warning(f"⚠️ LLM question generation failed: {e}, using template fallback")
            return generate_template_questions(top_gaps, max_questions)

    def _build_llm_prompt(self, property_id: str, top_gaps: List[Dict], max_questions: int) -> str:
        """Build the LLM prompt."""

        # Gap information summary
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

            # Match corresponding gap info
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

            # Assess question quality
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

        # Try LLM generation
        if self.use_llm and self.openai_client:
            questions = self.generate_llm_questions(property_id, top_gaps, max_questions)
        else:
            questions = generate_template_questions(top_gaps, max_questions)

        # Ensure question count doesn't exceed limit
        questions = questions[:max_questions]

        # Add generation timestamp
        import datetime
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

    # Build output result
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