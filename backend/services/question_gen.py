import json
from openai import OpenAI
from config import OPENAI_API_KEY
from services.gap_analyzer import get_remaining_gaps

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def generate_questions(
    property_id: str,
    hotel_name: str,
    review_text: str,
    covered_dimensions: list[str],
) -> list[dict]:
    """Generate 1-2 follow-up questions based on hotel gaps and user review."""
    remaining_gaps = get_remaining_gaps(property_id, covered_dimensions)
    if not remaining_gaps:
        return []

    top_gaps = remaining_gaps[:2]

    if not client:
        return _fallback_questions(top_gaps)

    gaps_desc = "\n".join(
        f"- {g['label']} (reason: {g.get('reason_label', g.get('reason', 'unknown'))})"
        for g in top_gaps
    )

    prompt = f"""You are a friendly hotel review assistant for Expedia. A guest just wrote a review for {hotel_name}.

Their review:
"{review_text}"

This hotel is currently missing information about:
{gaps_desc}

Generate 1-2 short, friendly follow-up questions to fill these gaps. Requirements:
- Each question should be one sentence, easy to answer
- Match the reviewer's tone and language
- Be specific, not generic
- If info is stale, ask "How was X during your stay?"
- If info is missing, ask about their experience with it

Return a JSON array of objects with "question" and "dimension" fields.
Return ONLY the JSON array."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        result = response.choices[0].message.content.strip()
        questions = json.loads(result)

        return [
            {
                "question": q["question"],
                "gap_dimension": q.get("dimension", top_gaps[i]["dimension"]),
                "gap_label": top_gaps[min(i, len(top_gaps) - 1)]["label"],
                "gap_reason": top_gaps[min(i, len(top_gaps) - 1)].get("reason", "unknown"),
                "priority": top_gaps[min(i, len(top_gaps) - 1)].get("priority", 2),
            }
            for i, q in enumerate(questions[:2])
        ]
    except Exception:
        return _fallback_questions(top_gaps)


def _fallback_questions(gaps: list[dict]) -> list[dict]:
    """Generate template-based questions when LLM is unavailable."""
    templates = {
        "never_mentioned": "How was the {label} during your stay?",
        "stale": "Has the {label} changed recently? How was it this time?",
        "conflicting": "We've heard mixed things about the {label} — what was your experience?",
    }
    questions = []
    for gap in gaps[:2]:
        reason = gap.get("reason", "never_mentioned")
        template = templates.get(reason, templates["never_mentioned"])
        questions.append({
            "question": template.format(label=gap["label"].lower()),
            "gap_dimension": gap["dimension"],
            "gap_label": gap["label"],
            "gap_reason": reason,
            "priority": gap.get("priority", 2),
        })
    return questions
