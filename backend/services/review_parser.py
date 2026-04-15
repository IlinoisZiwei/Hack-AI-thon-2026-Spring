import json
from openai import OpenAI
from config import OPENAI_API_KEY, DIMENSION_LABELS

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DIMENSIONS_LIST = list(DIMENSION_LABELS.keys())


async def extract_dimensions(review_text: str) -> list[str]:
    """Use LLM to extract which hotel dimensions are covered in a review."""
    if not client:
        return _fallback_extract(review_text)

    prompt = f"""Analyze this hotel review and identify which dimensions are mentioned.

Available dimensions:
{json.dumps(DIMENSION_LABELS, indent=2)}

Review:
\"{review_text}\"

Return a JSON array of dimension keys (e.g. ["wifi_speed", "housekeeping"]) that are mentioned or discussed in this review. Only include dimensions that the reviewer clearly experienced or commented on.

Return ONLY the JSON array, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        result = response.choices[0].message.content.strip()
        dimensions = json.loads(result)
        return [d for d in dimensions if d in DIMENSION_LABELS]
    except Exception:
        return _fallback_extract(review_text)


def _fallback_extract(review_text: str) -> list[str]:
    """Simple keyword-based fallback when LLM is unavailable."""
    text = review_text.lower()
    found = []
    keyword_map = {
        "wifi_speed": ["wifi", "internet", "wi-fi"],
        "soundproofing": ["noise", "quiet", "loud", "soundproof", "thin walls"],
        "air_conditioning": ["ac", "air conditioning", "heating", "cold room", "hot room"],
        "elevator": ["elevator", "lift", "stairs"],
        "water_pressure": ["water pressure", "shower", "hot water"],
        "power_outlets": ["outlet", "charging", "plug", "socket"],
        "front_desk": ["front desk", "check-in", "reception", "staff"],
        "housekeeping": ["clean", "dirty", "housekeeping", "tidy", "spotless"],
        "restaurant_quality": ["restaurant", "dining", "food", "buffet", "meal"],
        "luggage_storage": ["luggage", "bag storage", "concierge"],
        "transport_access": ["metro", "subway", "bus", "transport", "train", "taxi"],
        "noise_level": ["street noise", "traffic", "noisy area", "outside noise"],
        "nearby_dining": ["nearby restaurant", "places to eat", "food nearby"],
        "walkable_attractions": ["walking distance", "nearby attractions", "close to"],
        "checkout_time": ["checkout", "check-out", "late checkout"],
        "breakfast_hours": ["breakfast", "morning meal"],
        "parking_fee": ["parking", "garage", "valet"],
        "pet_policy": ["pet", "dog", "cat"],
        "pool": ["pool", "swimming"],
        "gym": ["gym", "fitness", "workout"],
    }
    for dim, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            found.append(dim)
    return found
