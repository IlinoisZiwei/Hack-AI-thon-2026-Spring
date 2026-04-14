"""
Module 1 — Hotel Profile Builder

Aggregates per-review dimension observations into a per-hotel profile.

Each observation (from extractor.py) has the schema:
    {dimension, mentioned, stance, confidence, evidence, source}

The profile for each dimension stores aggregated stance counts:
    {positive_count, negative_count, mixed_count, neutral_count}

sentiment_variance is computed from positive vs negative only (mixed excluded),
since mixed already captures the ambiguity explicitly.
"""

from collections import Counter
from typing import Optional

import pandas as pd

from .dimensions import ALL_DIMENSIONS, DIMENSIONS

STANCE_KEYS = ("positive", "negative", "mixed", "neutral")


def _stance_variance(counts: dict) -> float:
    """
    Conflict score using only positive vs negative counts.
    mixed is not counted — it already represents acknowledged ambiguity.
    Formula: min(pos, neg) / (pos + neg)  → range [0.0, 0.5]
    """
    pos = counts.get("positive", 0)
    neg = counts.get("negative", 0)
    total = pos + neg
    if total == 0:
        return 0.0
    return round(min(pos, neg) / total, 4)


def _dominant_stance(counts: dict) -> Optional[str]:
    nonzero = {k: v for k, v in counts.items() if v > 0}
    return max(nonzero, key=nonzero.get) if nonzero else None


def build_hotel_profiles(
    dimension_mentions: pd.DataFrame,
    all_property_ids: list[str],
) -> dict:
    """
    Build hotel_profiles[property_id][dimension] = {
        category, label,
        mention_count,
        last_mentioned,
        dominant_stance,
        stance_counts: {positive, negative, mixed, neutral},
        stance_variance,
        avg_confidence,
        example_snippets,
    }
    """
    hotel_profiles: dict = {}

    for pid in all_property_ids:
        hotel_profiles[pid] = {}
        hotel_data = dimension_mentions[dimension_mentions["eg_property_id"] == pid]

        for dim in ALL_DIMENSIONS:
            dim_rows = hotel_data[hotel_data["dimension"] == dim]

            empty = {
                "category": DIMENSIONS[dim]["category"],
                "label": DIMENSIONS[dim]["label"],
                "mention_count": 0,
                "last_mentioned": None,
                "dominant_stance": None,
                "stance_counts": {k: 0 for k in STANCE_KEYS},
                "stance_variance": 0.0,
                "avg_confidence": None,
                "example_snippets": [],
            }

            if len(dim_rows) == 0:
                hotel_profiles[pid][dim] = empty
                continue

            counts = Counter(dim_rows["stance"].fillna("neutral"))
            stance_counts = {k: counts.get(k, 0) for k in STANCE_KEYS}

            last_mentioned = dim_rows["review_date"].max()

            snippets = (
                dim_rows["evidence"]
                .dropna()
                .astype(str)
                .loc[lambda s: s.str.len() > 0]
                .head(3)
                .tolist()
            )

            confidences = dim_rows["confidence"].dropna()
            avg_conf = round(float(confidences.mean()), 3) if len(confidences) > 0 else None

            hotel_profiles[pid][dim] = {
                "category": DIMENSIONS[dim]["category"],
                "label": DIMENSIONS[dim]["label"],
                "mention_count": int(len(dim_rows)),
                "last_mentioned": (
                    last_mentioned.strftime("%Y-%m-%d") if pd.notna(last_mentioned) else None
                ),
                "dominant_stance": _dominant_stance(stance_counts),
                "stance_counts": stance_counts,
                "stance_variance": _stance_variance(stance_counts),
                "avg_confidence": avg_conf,
                "example_snippets": snippets,
            }

    return hotel_profiles


def merge_official_info(hotel_profiles: dict, official_info: dict) -> dict:
    """
    Merge description-based official info into review-based profiles.

    Adds per-dimension:
        official_info:     str | None
        official_source:   str | None
        has_official_info: bool
        official_conflict: bool  — official data exists but dominant review stance is negative
    """
    CONFLICT_DIMS = {"parking", "wifi_speed", "pet_policy", "breakfast_quality", "elevator"}

    for pid, profile in hotel_profiles.items():
        hotel_official = official_info.get(pid, {})

        for dim, info in profile.items():
            off = hotel_official.get(dim)

            if off:
                info["official_info"] = off["text"]
                info["official_source"] = off["source"]
                info["has_official_info"] = True
                info["official_conflict"] = (
                    dim in CONFLICT_DIMS
                    and info["mention_count"] >= 3
                    and info["dominant_stance"] == "negative"
                )
            else:
                info["official_info"] = None
                info["official_source"] = None
                info["has_official_info"] = False
                info["official_conflict"] = False

    return hotel_profiles


def compute_completeness(profile: dict) -> dict:
    """
    Percentage of dimensions that are 'known' — either from reviews or official data.
    """
    total = len(profile)
    covered = sum(
        1 for info in profile.values()
        if info["mention_count"] > 0 or info.get("has_official_info")
    )
    review_covered = sum(1 for info in profile.values() if info["mention_count"] > 0)
    return {
        "completeness_score": round(100 * covered / total, 1) if total else 0.0,
        "covered_dimensions": covered,
        "review_covered_dimensions": review_covered,
        "total_dimensions": total,
    }


def profile_to_flat_rows(property_id: str, profile: dict) -> list[dict]:
    """Flatten nested profile to a list of rows (for CSV export / inspection)."""
    rows = []
    for dim, info in profile.items():
        rows.append({
            "eg_property_id": property_id,
            "dimension": dim,
            **{k: v for k, v in info.items() if k != "example_snippets"},
            "example_snippets": " || ".join(info.get("example_snippets", [])),
        })
    return rows
