"""
Module 1 — Dimension Extractor

Two extraction strategies, both producing the same output schema:

    {
        "dimension": str,           # from DIMENSIONS
        "mentioned": bool,
        # only present when mentioned=True:
        "stance":    str,           # positive | negative | mixed | neutral
        "confidence": float,        # 0.0–1.0
        "evidence":  str,           # exact quote from the review
    }

Key design principle
--------------------
We NEVER ask the model "what does this review mention?"
Instead, we ask it to evaluate EACH dimension independently:
  "Is dimension X explicitly mentioned? If yes, quote the evidence."

This prevents the model from hallucinating dimensions that aren't in the text.
A dimension is only marked mentioned=True when the model can produce a direct quote.

Rule-based strategy follows the same contract: a dimension is only included
if a keyword match produces at least one sentence, and stance is inferred
purely from sentiment words in that sentence — never from the review as a whole.
"""

import json
import logging
import os
import re
from typing import Optional

from .dimensions import ALL_DIMENSIONS, DIMENSION_RATING_MAP, DIMENSIONS

logger = logging.getLogger(__name__)

# ── Sentiment word banks ──────────────────────────────────────────────────────

POS_WORDS = {
    "good", "great", "excellent", "amazing", "nice", "clean", "comfortable",
    "friendly", "helpful", "fast", "reliable", "convenient", "quiet",
    "spacious", "perfect", "love", "loved", "awesome", "smooth", "fantastic",
    "wonderful", "outstanding", "superb", "delightful", "pleased", "happy",
}
NEG_WORDS = {
    "bad", "poor", "terrible", "awful", "dirty", "slow", "broken", "noisy",
    "loud", "small", "uncomfortable", "rude", "unhelpful", "smelly", "stained",
    "worst", "issue", "problem", "delay", "crowded", "horrible", "disgusting",
    "filthy", "disappointing", "disappointed", "unacceptable",
}


# ── Text utilities ────────────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _keyword_match(text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return bool(re.search(pattern, text.lower()))


def _matched_sentences(text: str, keywords: list[str]) -> list[str]:
    sentences = _split_sentences(text)
    matched = []
    for sent in sentences:
        sent_lower = sent.lower()
        if any(_keyword_match(sent_lower, kw) for kw in keywords):
            matched.append(sent)
    return matched


def _stance_from_sentences(sentences: list[str]) -> tuple[str, float]:
    """
    Return (stance, confidence) based on sentiment word counts in matched sentences.
    Detects mixed stance (both positive and negative words present).
    """
    pos = neg = 0
    for sent in sentences:
        for token in re.findall(r"\b[\w'-]+\b", sent.lower()):
            if token in POS_WORDS:
                pos += 1
            if token in NEG_WORDS:
                neg += 1

    total = pos + neg
    if total == 0:
        return "neutral", 0.5

    # Both sides present → mixed
    if pos > 0 and neg > 0:
        # Confidence scales with the imbalance; perfectly balanced = 0.5
        imbalance = abs(pos - neg) / total
        return "mixed", round(0.5 + 0.3 * imbalance, 2)

    if pos > neg:
        return "positive", round(0.5 + 0.5 * (pos / (pos + 1)), 2)

    return "negative", round(0.5 + 0.5 * (neg / (neg + 1)), 2)


def _numeric_to_stance(score) -> Optional[str]:
    try:
        score = float(score)
    except (TypeError, ValueError):
        return None
    if score == 0:
        return None
    if score >= 4:
        return "positive"
    if score <= 2:
        return "negative"
    return "neutral"


# ── Rule-based extraction ─────────────────────────────────────────────────────

def extract_rule_based(row: dict) -> list[dict]:
    """
    Keyword-based extraction.

    A dimension is only included if at least one sentence in the review
    contains a keyword for that dimension. Stance is inferred from sentiment
    words in those matched sentences only — never from the full review.
    """
    review_text = str(row.get("review_text_clean", "")).strip()
    rating_dict = row.get("rating_dict", {})

    results = []

    for dim, meta in DIMENSIONS.items():
        matched = _matched_sentences(review_text, meta["keywords"])
        if not matched:
            # No keyword evidence → not mentioned
            continue

        evidence = " | ".join(matched[:2])
        stance, confidence = _stance_from_sentences(matched)

        # Override with structured sub-rating when available (higher reliability)
        rating_field = DIMENSION_RATING_MAP.get(dim)
        if rating_field and isinstance(rating_dict, dict):
            structured_stance = _numeric_to_stance(rating_dict.get(rating_field))
            if structured_stance:
                stance = structured_stance
                confidence = 0.9  # structured rating is reliable

        results.append({
            "dimension": dim,
            "mentioned": True,
            "stance": stance,
            "confidence": confidence,
            "evidence": evidence,
            "source": "rule_based",
        })

    return results


# ── LLM-based extraction ──────────────────────────────────────────────────────

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None
        from openai import OpenAI
        _client = OpenAI(api_key=api_key)
    return _client


# Build a dimension reference block listing all dims + their keywords
_DIM_REFERENCE = "\n".join(
    f'  "{dim}" ({meta["category"]}): {meta["label"]} '
    f'— cues: {", ".join(meta["keywords"][:4])}'
    for dim, meta in DIMENSIONS.items()
)

_SYSTEM = (
    "You are a strict hotel review analyst. "
    "You extract only what is explicitly stated — never infer or extrapolate. "
    "Return valid JSON only."
)

_USER_TMPL = """\
Analyze the hotel review(s) below against the fixed set of dimensions.

DIMENSIONS (you must evaluate ALL of them for each review):
{dim_reference}

STRICT RULES:
1. A dimension is "mentioned" ONLY when the review contains a phrase that clearly refers to it.
2. You MUST copy an exact quote from the review as evidence (≤ 20 words).
3. If you cannot find a direct quote → set "mentioned": false. Do NOT guess.
4. stance values: "positive" | "negative" | "mixed" | "neutral"
   - mixed = the review expresses BOTH positive and negative about this dimension
5. confidence: how certain the quote is about this dimension (0.0–1.0)
6. Evaluate ALL {n_dims} dimensions for EACH review — even if most are not_mentioned.

Reviews:
{reviews_block}

Return this exact JSON structure:
{{
  "results": [
    {{
      "review_idx": 0,
      "dimensions": [
        {{"dimension": "wifi_speed",      "mentioned": true,  "stance": "negative", "confidence": 0.95, "evidence": "wifi kept dropping every hour"}},
        {{"dimension": "room_cleanliness","mentioned": false}},
        ... (all {n_dims} dimensions)
      ]
    }}
  ]
}}
"""


def extract_llm_batch(
    rows: list[dict],
    model: str = "gpt-4o-mini",
    batch_size: int = 10,   # smaller batches — each review now evaluates all dims
) -> list[list[dict]]:
    """
    LLM extraction with per-dimension mentioned/not_mentioned classification.

    Each review is evaluated against ALL dimensions explicitly.
    Only dimensions with mentioned=True and a valid evidence quote are returned.

    Falls back to rule-based if the API is unavailable or a batch fails.
    """
    client = _get_client()
    if client is None:
        logger.warning("OPENAI_API_KEY not set — using rule-based extraction.")
        return [extract_rule_based(r) for r in rows]

    all_results: list[list[dict]] = []

    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        reviews_block = "\n\n".join(
            f"[{i}] {str(r.get('review_text_clean', ''))[:500]}"
            for i, r in enumerate(batch)
        )
        prompt = _USER_TMPL.format(
            dim_reference=_DIM_REFERENCE,
            n_dims=len(ALL_DIMENSIONS),
            reviews_block=reviews_block,
        )

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            raw = json.loads(resp.choices[0].message.content)
            items = raw.get("results", [])

            batch_out: list[list[dict]] = [[] for _ in batch]
            review_text_map = {
                i: str(r.get("review_text_clean", "")).lower()
                for i, r in enumerate(batch)
            }

            for item in items:
                idx = item.get("review_idx", -1)
                if not (0 <= idx < len(batch)):
                    continue

                review_lower = review_text_map[idx]
                mentions = []

                for d in item.get("dimensions", []):
                    dim = d.get("dimension")
                    if dim not in DIMENSIONS:
                        continue
                    if not d.get("mentioned", False):
                        continue

                    evidence = str(d.get("evidence", "")).strip()
                    stance = d.get("stance", "")
                    confidence = float(d.get("confidence", 0.0))

                    # Validate: evidence must be non-empty and roughly present in review
                    if not evidence:
                        continue
                    # Check at least half the words of evidence appear in the review
                    evidence_words = re.findall(r"\b\w+\b", evidence.lower())
                    if evidence_words:
                        overlap = sum(1 for w in evidence_words if w in review_lower)
                        if overlap / len(evidence_words) < 0.5:
                            logger.debug(
                                "Rejected evidence for %s (low overlap): %s", dim, evidence
                            )
                            continue

                    if stance not in ("positive", "negative", "mixed", "neutral"):
                        continue

                    mentions.append({
                        "dimension": dim,
                        "mentioned": True,
                        "stance": stance,
                        "confidence": round(confidence, 2),
                        "evidence": evidence,
                        "source": "llm",
                    })

                batch_out[idx] = mentions

            all_results.extend(batch_out)
            logger.debug(
                "Batch %d–%d: %d mentions (LLM)",
                start, start + len(batch) - 1,
                sum(len(x) for x in batch_out),
            )

        except Exception as exc:
            logger.warning(
                "LLM batch %d–%d failed (%s) — rule-based fallback.",
                start, start + len(batch) - 1, exc,
            )
            for row in batch:
                all_results.append(extract_rule_based(row))

    return all_results
