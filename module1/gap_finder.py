"""
Module 1 — Gap Finder

Identifies information gaps in a hotel profile:
  - official_conflict : official desc says X, but reviews are negative → priority HIGH (4)
  - never_mentioned   : no reviews AND no official info               → priority HIGH (3)
  - stale             : last mention > 6 months ago                   → priority MEDIUM (2)
  - conflicting       : mixed positive/negative review sentiment       → priority LOW (1)

Dimensions with official info but zero reviews are NOT flagged as gaps
(we already know the answer from the hotel's own description).

Returns gaps sorted highest priority first.
"""

from datetime import datetime
from typing import Optional

STALE_DAYS = 180
CONFLICT_VARIANCE_THRESHOLD = 0.25
MIN_MENTIONS_FOR_CONFLICT = 5


def find_gaps(
    profile: dict,
    current_date: Optional[datetime] = None,
) -> list[dict]:
    """
    Analyze a hotel profile and return sorted gap records.

    Args:
        profile: hotel_profiles[pid] — output of merge_official_info()
        current_date: reference date (defaults to today)
    """
    if current_date is None:
        current_date = datetime.now()

    gaps: list[dict] = []
    seen_dims: set[str] = set()

    for dim, info in profile.items():
        mention_count = info["mention_count"]
        has_official = info.get("has_official_info", False)
        last_str = info.get("last_mentioned")

        # ── Official vs. review conflict ─────────────────────────────
        # Hotel claims X officially, but guests consistently complain
        if info.get("official_conflict"):
            sc = info.get("stance_counts", {})
            gaps.append({
                "dimension": dim,
                "label": info.get("label", dim),
                "category": info["category"],
                "reason": "official_conflict",
                "reason_label": (
                    f"Official info conflicts with reviews "
                    f"({sc.get('negative', 0)} negative)"
                ),
                "priority": 4,
                "mention_count": mention_count,
                "last_mentioned": last_str,
                "dominant_stance": info.get("dominant_stance"),
                "official_info": info.get("official_info"),
            })
            seen_dims.add(dim)
            continue

        # ── Never mentioned (and no official data either) ────────────
        if mention_count == 0 and not has_official:
            gaps.append({
                "dimension": dim,
                "label": info.get("label", dim),
                "category": info["category"],
                "reason": "never_mentioned",
                "reason_label": "No data yet",
                "priority": 3,
                "mention_count": 0,
                "last_mentioned": None,
                "dominant_stance": None,
                "official_info": None,
            })
            seen_dims.add(dim)
            continue

        # ── Stale review info ────────────────────────────────────────
        if last_str and mention_count > 0:
            last_dt = datetime.strptime(last_str, "%Y-%m-%d")
            days_since = (current_date - last_dt).days
            if days_since > STALE_DAYS:
                months_ago = days_since // 30
                gaps.append({
                    "dimension": dim,
                    "label": info.get("label", dim),
                    "category": info["category"],
                    "reason": "stale",
                    "reason_label": f"Last mentioned {months_ago} month{'s' if months_ago != 1 else ''} ago",
                    "priority": 2,
                    "mention_count": mention_count,
                    "last_mentioned": last_str,
                    "dominant_stance": info.get("dominant_stance"),
                    "official_info": info.get("official_info"),
                })
                seen_dims.add(dim)
                continue

        # ── Conflicting review sentiment ──────────────────────────────
        if (
            dim not in seen_dims
            and mention_count >= MIN_MENTIONS_FOR_CONFLICT
            and info.get("stance_variance", 0) > CONFLICT_VARIANCE_THRESHOLD
        ):
            sc = info.get("stance_counts", {})
            gaps.append({
                "dimension": dim,
                "label": info.get("label", dim),
                "category": info["category"],
                "reason": "conflicting",
                "reason_label": (
                    f"Mixed reviews — {sc.get('positive', 0)} positive / "
                    f"{sc.get('negative', 0)} negative"
                ),
                "priority": 1,
                "mention_count": mention_count,
                "last_mentioned": last_str,
                "dominant_stance": info.get("dominant_stance"),
                "official_info": info.get("official_info"),
            })

    return sorted(gaps, key=lambda g: (-g["priority"], g["dimension"]))
