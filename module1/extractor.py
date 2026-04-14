"""
Module 1 — Dimension Extractor

Two strategies:
  1. Rule-based  — fast, no API cost, used as default / fallback
  2. LLM-based   — gpt-4o-mini, higher accuracy, requires OPENAI_API_KEY

Both return the same output schema per review:
  [{"dimension": str, "sentiment": str, "evidence": str, "sentiment_source": str}, ...]
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
    "filthy", "disappointing", "disappointed", "unacceptable", "broken",
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


def _local_sentiment(sentences: list[str]) -> Optional[str]:
    pos = neg = 0
    for sent in sentences:
        for token in re.findall(r"\b[\w'-]+\b", sent.lower()):
            if token in POS_WORDS:
                pos += 1
            if token in NEG_WORDS:
                neg += 1
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    if pos == 0 and neg == 0:
        return None
    return "neutral"


def _numeric_to_sentiment(score) -> Optional[str]:
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
    Keyword + sentiment heuristic extraction.
    Always available, no API cost.
    """
    review_text = str(row.get("review_text_clean", "")).strip()
    rating_dict = row.get("rating_dict", {})
    overall_rating = row.get("overall_rating")

    results = []

    for dim, meta in DIMENSIONS.items():
        matched = _matched_sentences(review_text, meta["keywords"])
        if not matched:
            continue

        sentiment = None
        source = None

        # Priority 1: structured sub-rating
        rating_field = DIMENSION_RATING_MAP.get(dim)
        if rating_field and isinstance(rating_dict, dict):
            sentiment = _numeric_to_sentiment(rating_dict.get(rating_field))
            if sentiment:
                source = f"rating:{rating_field}"

        # Priority 2: sentence-level keyword sentiment
        if sentiment is None:
            sentiment = _local_sentiment(matched)
            if sentiment:
                source = "local_text"

        # Priority 3: overall rating fallback
        if sentiment is None:
            sentiment = _numeric_to_sentiment(overall_rating)
            if sentiment:
                source = "overall_rating"

        if sentiment is None:
            sentiment = "unknown"
            source = "none"

        results.append({
            "dimension": dim,
            "category": meta["category"],
            "sentiment": sentiment,
            "sentiment_source": source,
            "evidence": " | ".join(matched[:2]),
        })

    return results


# ── LLM-based extraction ──────────────────────────────────────────────────────

_client = None  # lazy-init


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None
        from openai import OpenAI
        _client = OpenAI(api_key=api_key)
    return _client


_DIM_LIST = "\n".join(
    f"  {dim} ({meta['category']}): {meta['label']}"
    for dim, meta in DIMENSIONS.items()
)

_SYSTEM = (
    "You are a hotel review analyzer. "
    "Extract structured dimension mentions from hotel reviews. "
    "Return valid JSON only."
)

_USER_TMPL = """\
Analyze the following hotel reviews and extract which dimensions are mentioned and the sentiment.

Available dimensions:
{dim_list}

Reviews (0-indexed):
{reviews_block}

Return this JSON structure:
{{
  "results": [
    {{
      "review_idx": 0,
      "mentions": [
        {{"dimension": "wifi_speed", "sentiment": "negative", "evidence": "the wifi was terrible"}}
      ]
    }}
  ]
}}

Rules:
- Only include dimensions that are CLEARLY mentioned
- sentiment must be: positive | negative | neutral
- evidence is a short direct quote (≤15 words)
- Empty mentions list if no relevant dimensions found
"""


def extract_llm_batch(
    rows: list[dict],
    model: str = "gpt-4o-mini",
    batch_size: int = 20,
) -> list[list[dict]]:
    """
    LLM-based extraction for a list of preprocessed review rows.
    Falls back to rule-based if the API is unavailable or a batch fails.

    Returns: list (one per row) of mention lists
    """
    client = _get_client()
    if client is None:
        logger.warning("OPENAI_API_KEY not set — falling back to rule-based extraction.")
        return [extract_rule_based(r) for r in rows]

    all_results: list[list[dict]] = []

    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        reviews_block = "\n\n".join(
            f"[{i}] {str(r.get('review_text_clean', ''))[:600]}"
            for i, r in enumerate(batch)
        )
        prompt = _USER_TMPL.format(dim_list=_DIM_LIST, reviews_block=reviews_block)

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            raw = json.loads(resp.choices[0].message.content)
            items = raw.get("results", [])

            batch_out: list[list[dict]] = [[] for _ in batch]
            for item in items:
                idx = item.get("review_idx", -1)
                if not (0 <= idx < len(batch)):
                    continue
                valid = [
                    m for m in item.get("mentions", [])
                    if m.get("dimension") in DIMENSIONS
                    and m.get("sentiment") in ("positive", "negative", "neutral")
                ]
                batch_out[idx] = valid

            all_results.extend(batch_out)
            logger.debug("Batch %d-%d: %d mentions extracted via LLM",
                         start, start + len(batch) - 1,
                         sum(len(x) for x in batch_out))

        except Exception as exc:
            logger.warning("LLM batch %d-%d failed (%s) — using rule-based fallback.",
                           start, start + len(batch) - 1, exc)
            for row in batch:
                mentions = extract_rule_based(row)
                # Strip fields not present in LLM output schema
                all_results.append([
                    {"dimension": m["dimension"], "sentiment": m["sentiment"],
                     "evidence": m["evidence"]}
                    for m in mentions
                ])

    return all_results
