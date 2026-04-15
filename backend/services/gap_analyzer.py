import json
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent.parent / "data"

# In-memory store loaded from seed data
_hotel_profiles: dict = {}
_hotel_gaps: dict = {}


def load_data():
    global _hotel_profiles, _hotel_gaps
    with open(DATA_DIR / "hotel_profiles.json") as f:
        _hotel_profiles = json.load(f)
    with open(DATA_DIR / "all_hotels_module2_input.json") as f:
        gaps_list = json.load(f)
        _hotel_gaps = {item["property_id"]: item["top_gaps"] for item in gaps_list}


def get_all_profiles() -> dict:
    if not _hotel_profiles:
        load_data()
    return _hotel_profiles


def get_hotel_profile(property_id: str) -> dict | None:
    profiles = get_all_profiles()
    return profiles.get(property_id)


def get_hotel_gaps(property_id: str) -> list[dict]:
    if not _hotel_gaps:
        load_data()
    return _hotel_gaps.get(property_id, [])


def compute_completeness(profile: dict) -> dict:
    """Compute completeness score from a hotel profile."""
    dimensions = profile.get("profile", profile) if "profile" in profile else profile
    total = len(dimensions)
    covered = 0
    stale = 0
    missing = 0
    conflicting = 0
    cutoff = datetime.now() - timedelta(days=180)

    for dim_key, dim_data in dimensions.items():
        mc = dim_data.get("mention_count", 0)
        if mc == 0:
            missing += 1
            continue
        covered += 1
        last = dim_data.get("last_mentioned")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt < cutoff:
                    stale += 1
            except (ValueError, TypeError):
                pass
        variance = dim_data.get("stance_variance", 0)
        if variance and variance > 0.4:
            conflicting += 1

    score = int((covered / total) * 100) if total > 0 else 0
    return {
        "score": score,
        "total_dimensions": total,
        "covered": covered,
        "missing": missing,
        "stale": stale,
        "conflicting": conflicting,
    }


def get_remaining_gaps(property_id: str, covered_dimensions: list[str]) -> list[dict]:
    """Get gaps not already covered by the user's review."""
    gaps = get_hotel_gaps(property_id)
    return [g for g in gaps if g["dimension"] not in covered_dimensions]


def update_dimension(property_id: str, dimension: str, answer: str, sentiment: str):
    """Update a hotel profile dimension with new info from user answer."""
    profiles = get_all_profiles()
    if property_id not in profiles:
        return

    profile = profiles[property_id]
    dim_data = profile.get("profile", profile).get(dimension)
    if not dim_data:
        return

    # Update mention count and timestamp
    dim_data["mention_count"] = dim_data.get("mention_count", 0) + 1
    dim_data["last_mentioned"] = datetime.now().strftime("%Y-%m-%d")

    # Update sentiment
    stance_map = {"positive": "positive", "negative": "negative", "neutral": "neutral"}
    stance_key = stance_map.get(sentiment, "neutral")
    if "stance_counts" in dim_data:
        dim_data["stance_counts"][stance_key] = dim_data["stance_counts"].get(stance_key, 0) + 1
    dim_data["dominant_stance"] = sentiment

    # Add snippet
    if "example_snippets" not in dim_data:
        dim_data["example_snippets"] = []
    dim_data["example_snippets"].insert(0, answer)
    dim_data["example_snippets"] = dim_data["example_snippets"][:5]

    # Also remove this dimension from gaps
    if property_id in _hotel_gaps:
        _hotel_gaps[property_id] = [
            g for g in _hotel_gaps[property_id] if g["dimension"] != dimension
        ]
