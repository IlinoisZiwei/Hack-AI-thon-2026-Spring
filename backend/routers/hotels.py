from fastapi import APIRouter, HTTPException
from config import HOTEL_NAMES, HOTEL_REVIEW_COUNTS, DIMENSION_LABELS
from services.gap_analyzer import get_all_profiles, get_hotel_profile, get_hotel_gaps, compute_completeness

router = APIRouter(prefix="/api/hotels", tags=["hotels"])


@router.get("")
def list_hotels():
    """Return all hotels with basic info and completeness."""
    profiles = get_all_profiles()
    hotels = []
    for pid, profile in profiles.items():
        completeness = compute_completeness(profile.get("profile", profile))
        hotels.append({
            "property_id": pid,
            "name": HOTEL_NAMES.get(pid, f"Property {pid[:8]}"),
            "review_count": HOTEL_REVIEW_COUNTS.get(pid, 0),
            "completeness": completeness,
        })
    hotels.sort(key=lambda x: x["review_count"], reverse=True)
    return hotels


@router.get("/{property_id}/profile")
def get_profile(property_id: str):
    """Return detailed profile for a single hotel."""
    profile = get_hotel_profile(property_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Hotel not found")

    dims = profile.get("profile", profile)
    completeness = compute_completeness(dims)
    gaps = get_hotel_gaps(property_id)

    dimensions = []
    for dim_key, dim_data in dims.items():
        dimensions.append({
            "key": dim_key,
            "label": dim_data.get("label", DIMENSION_LABELS.get(dim_key, dim_key)),
            "category": dim_data.get("category", "unknown"),
            "mention_count": dim_data.get("mention_count", 0),
            "last_mentioned": dim_data.get("last_mentioned"),
            "dominant_stance": dim_data.get("dominant_stance"),
            "example_snippets": dim_data.get("example_snippets", [])[:3],
            "has_official_info": dim_data.get("has_official_info", False),
        })

    return {
        "property_id": property_id,
        "name": HOTEL_NAMES.get(property_id, f"Property {property_id[:8]}"),
        "review_count": HOTEL_REVIEW_COUNTS.get(property_id, 0),
        "completeness": completeness,
        "dimensions": dimensions,
        "gaps": gaps,
    }
