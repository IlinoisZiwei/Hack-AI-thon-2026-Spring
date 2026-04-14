"""
Module 1 — Description Enricher

Reads Description_PROC.csv and extracts official structured info per hotel.
Maps CSV fields → dimension names so the hotel profile knows what's
"officially documented" vs what only comes from guest reviews.

Output per hotel:
  {
    "pet_policy":     {"text": "Pets not allowed", "source": "pet_policy"},
    "parking":        {"text": "Free self parking on site", "source": "property_amenity_parking"},
    "checkout_time":  {"text": "11:00 AM", "source": "check_out_time"},
    ...
  }
"""

import json
import re
from typing import Optional

import pandas as pd


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_list_field(value) -> list[str]:
    """Parse a CSV field that's either a JSON list or a plain string."""
    if pd.isna(value):
        return []
    value = str(value).strip()
    if value.startswith("["):
        try:
            items = json.loads(value)
            return [str(i).strip() for i in items if str(i).strip()]
        except Exception:
            pass
    return [value] if value else []


def _join(items: list[str], sep: str = "; ") -> Optional[str]:
    cleaned = [i for i in items if i and "|MASK|" not in i]
    return sep.join(cleaned) if cleaned else None


def _filter_contains(items: list[str], keywords: list[str]) -> list[str]:
    return [
        i for i in items
        if any(kw.lower() in i.lower() for kw in keywords)
    ]


# ── Per-dimension extractors ──────────────────────────────────────────────────

def _extract_pet_policy(row: pd.Series) -> Optional[dict]:
    items = _parse_list_field(row.get("pet_policy"))
    text = _join(items)
    if text:
        return {"text": text, "source": "pet_policy"}
    # fallback: check know_before_you_go for pet mentions
    kbyg = _parse_list_field(row.get("know_before_you_go"))
    pet_items = _filter_contains(kbyg, ["pet", "dog", "cat", "animal"])
    text = _join(pet_items)
    return {"text": text, "source": "know_before_you_go"} if text else None


def _extract_checkout_time(row: pd.Series) -> Optional[dict]:
    parts = []
    t = str(row.get("check_out_time", "")).strip()
    if t and t != "nan":
        parts.append(f"Check-out by {t}")
    policy_items = _parse_list_field(row.get("check_out_policy"))
    parts.extend([i for i in policy_items if "|MASK|" not in i])
    text = _join(parts)
    return {"text": text, "source": "check_out_time"} if text else None


def _extract_checkin(row: pd.Series) -> Optional[dict]:
    parts = []
    start = str(row.get("check_in_start_time", "")).strip()
    end = str(row.get("check_in_end_time", "")).strip()
    if start and start != "nan":
        time_str = f"Check-in: {start}"
        if end and end != "nan":
            time_str += f" – {end}"
        parts.append(time_str)
    instructions = _parse_list_field(row.get("check_in_instructions"))
    parts.extend([i for i in instructions if "|MASK|" not in i][:2])
    text = _join(parts)
    return {"text": text, "source": "check_in_start_time"} if text else None


def _extract_parking(row: pd.Series) -> Optional[dict]:
    items = _parse_list_field(row.get("property_amenity_parking"))
    text = _join(items)
    return {"text": text, "source": "property_amenity_parking"} if text else None


def _extract_wifi(row: pd.Series) -> Optional[dict]:
    items = _parse_list_field(row.get("property_amenity_internet"))
    text = _join(items)
    return {"text": text, "source": "property_amenity_internet"} if text else None


def _extract_breakfast(row: pd.Series) -> Optional[dict]:
    items = _parse_list_field(row.get("property_amenity_food_and_drink"))
    breakfast_items = _filter_contains(items, ["breakfast", "brunch", "morning"])
    text = _join(breakfast_items)
    return {"text": text, "source": "property_amenity_food_and_drink"} if text else None


def _extract_restaurant(row: pd.Series) -> Optional[dict]:
    items = _parse_list_field(row.get("property_amenity_food_and_drink"))
    dining_items = _filter_contains(items, ["restaurant", "bar", "dining", "cafe", "room service"])
    text = _join(dining_items)
    return {"text": text, "source": "property_amenity_food_and_drink"} if text else None


def _extract_elevator(row: pd.Series) -> Optional[dict]:
    items = _parse_list_field(row.get("property_amenity_accessibility"))
    elevator_items = _filter_contains(items, ["elevator", "lift"])
    if elevator_items:
        return {"text": _join(elevator_items), "source": "property_amenity_accessibility"}
    # Check know_before_you_go for "does not have elevators"
    kbyg = _parse_list_field(row.get("know_before_you_go"))
    elev = _filter_contains(kbyg, ["elevator", "lift"])
    text = _join(elev)
    return {"text": text, "source": "know_before_you_go"} if text else None


def _extract_location(row: pd.Series) -> Optional[dict]:
    desc = str(row.get("area_description", "")).strip()
    if not desc or desc == "nan" or "|MASK|" in desc:
        # try to clean masked version
        cleaned = re.sub(r"\|MASK\|", "", desc).strip()
        if len(cleaned) > 20:
            return {"text": cleaned[:200], "source": "area_description"}
        return None
    return {"text": desc[:200], "source": "area_description"}


def _extract_transport(row: pd.Series) -> Optional[dict]:
    desc = str(row.get("area_description", "")).strip()
    keywords = ["subway", "metro", "station", "bus", "airport", "train", "transit", "transport"]
    if any(kw in desc.lower() for kw in keywords):
        return {"text": desc[:200], "source": "area_description"}
    return None


# ── Dimension → extractor mapping ─────────────────────────────────────────────

_EXTRACTORS = {
    "pet_policy":             _extract_pet_policy,
    "checkout_time":          _extract_checkout_time,
    "front_desk_efficiency":  _extract_checkin,
    "parking":                _extract_parking,
    "wifi_speed":             _extract_wifi,
    "breakfast_quality":      _extract_breakfast,
    "restaurant_quality":     _extract_restaurant,
    "elevator":               _extract_elevator,
    "location_convenience":   _extract_location,
    "transport_access":       _extract_transport,
}


# ── Public API ────────────────────────────────────────────────────────────────

def build_official_info(descriptions: pd.DataFrame) -> dict[str, dict[str, dict]]:
    """
    Returns:
        {
          property_id: {
            dimension_name: {"text": str, "source": str},
            ...
          }
        }
    """
    result: dict[str, dict] = {}

    for _, row in descriptions.iterrows():
        pid = str(row.get("eg_property_id", "")).strip()
        if not pid:
            continue

        hotel_info: dict[str, dict] = {}
        for dim, extractor in _EXTRACTORS.items():
            info = extractor(row)
            if info:
                hotel_info[dim] = info

        result[pid] = hotel_info

    return result
