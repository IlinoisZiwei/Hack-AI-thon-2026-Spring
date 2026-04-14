"""
Module 1 — Hotel Profile Builder

Aggregates per-review dimension mentions into a per-hotel profile.
Each hotel profile covers all predefined dimensions, even if mention_count == 0.
"""

from collections import Counter
from typing import Optional

import pandas as pd

from .dimensions import ALL_DIMENSIONS, DIMENSIONS


def _sentiment_variance(counts: dict) -> float:
    """
    Conflict score: higher = more mixed reviews.
    Formula: min(pos, neg) / total  (ranges 0.0 – 0.5)
    """
    pos = counts.get("positive", 0)
    neg = counts.get("negative", 0)
    total = pos + neg + counts.get("neutral", 0)
    if total == 0:
        return 0.0
    return round(min(pos, neg) / total, 4)


def _dominant_sentiment(counts: dict) -> Optional[str]:
    nonzero = {k: v for k, v in counts.items() if v > 0 and k != "unknown"}
    return max(nonzero, key=nonzero.get) if nonzero else None


def build_hotel_profiles(
    dimension_mentions: pd.DataFrame,
    all_property_ids: list[str],
) -> dict:
    """
    Build hotel_profiles[property_id][dimension] = {
        category, label, mention_count, last_mentioned,
        dominant_sentiment, sentiment_counts, sentiment_variance,
        example_snippets
    }
    """
    hotel_profiles: dict = {}

    for pid in all_property_ids:
        hotel_profiles[pid] = {}
        hotel_data = dimension_mentions[dimension_mentions["eg_property_id"] == pid]

        for dim in ALL_DIMENSIONS:
            dim_rows = hotel_data[hotel_data["dimension"] == dim]

            empty_profile = {
                "category": DIMENSIONS[dim]["category"],
                "label": DIMENSIONS[dim]["label"],
                "mention_count": 0,
                "last_mentioned": None,
                "dominant_sentiment": None,
                "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0, "unknown": 0},
                "sentiment_variance": 0.0,
                "example_snippets": [],
            }

            if len(dim_rows) == 0:
                hotel_profiles[pid][dim] = empty_profile
                continue

            counts = Counter(dim_rows["sentiment"].fillna("unknown"))
            clean_counts = {
                "positive": counts.get("positive", 0),
                "neutral":  counts.get("neutral", 0),
                "negative": counts.get("negative", 0),
                "unknown":  counts.get("unknown", 0),
            }

            last_mentioned = dim_rows["review_date"].max()
            snippets = (
                dim_rows["evidence"]
                .dropna()
                .astype(str)
                .loc[lambda s: s.str.len() > 0]
                .head(3)
                .tolist()
            )

            hotel_profiles[pid][dim] = {
                "category": DIMENSIONS[dim]["category"],
                "label": DIMENSIONS[dim]["label"],
                "mention_count": int(len(dim_rows)),
                "last_mentioned": (
                    last_mentioned.strftime("%Y-%m-%d") if pd.notna(last_mentioned) else None
                ),
                "dominant_sentiment": _dominant_sentiment(clean_counts),
                "sentiment_counts": clean_counts,
                "sentiment_variance": _sentiment_variance(clean_counts),
                "example_snippets": snippets,
            }

    return hotel_profiles


def merge_official_info(hotel_profiles: dict, official_info: dict) -> dict:
    """
    Merge description-based official info into the review-based hotel profiles.

    For each hotel + dimension that has official info, adds:
      - official_info : str   — the extracted text from Description_PROC.csv
      - official_source : str — which CSV field it came from
      - has_official_info : bool

    Also detects conflicts: official policy exists but dominant review sentiment
    is negative (e.g., hotel claims "free parking" but guests complain about fees).
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

                # Conflict detection: official data exists + reviews disagree
                if (
                    dim in CONFLICT_DIMS
                    and info["mention_count"] >= 3
                    and info["dominant_sentiment"] == "negative"
                ):
                    info["official_conflict"] = True
                else:
                    info["official_conflict"] = False
            else:
                info["official_info"] = None
                info["official_source"] = None
                info["has_official_info"] = False
                info["official_conflict"] = False

    return hotel_profiles


def compute_completeness(profile: dict) -> dict:
    """
    Percentage of dimensions that are 'known' — either from reviews
    or from official Description data.
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
    """Convert nested profile to flat list (useful for DataFrame / export)."""
    rows = []
    for dim, info in profile.items():
        rows.append({
            "eg_property_id": property_id,
            "dimension": dim,
            **info,
            "example_snippets": " || ".join(info["example_snippets"]),
        })
    return rows
