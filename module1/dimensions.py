# ============================================================
# Module 1 — Dimension Definitions
# 20 predefined hotel dimensions across 4 categories
# ============================================================

DIMENSIONS: dict[str, dict] = {
    # ── Hardware ────────────────────────────────────────────
    "wifi_speed": {
        "category": "hardware",
        "label": "WiFi & Internet",
        "keywords": ["wifi", "wi-fi", "internet", "wireless", "signal", "bandwidth", "connection speed"],
    },
    "soundproofing": {
        "category": "hardware",
        "label": "Soundproofing",
        "keywords": ["soundproof", "noise", "noisy", "quiet", "loud", "thin walls", "hear through walls"],
    },
    "air_conditioning": {
        "category": "hardware",
        "label": "Air Conditioning / Heating",
        "keywords": ["air conditioning", "ac", "a/c", "heating", "heater", "temperature control", "hvac", "thermostat"],
    },
    "elevator": {
        "category": "hardware",
        "label": "Elevator",
        "keywords": ["elevator", "lift", "escalator"],
    },
    "power_outlets": {
        "category": "hardware",
        "label": "Power Outlets & Charging",
        "keywords": ["outlet", "plug", "power socket", "charging", "usb port", "usb"],
    },
    "water_pressure": {
        "category": "hardware",
        "label": "Water Pressure & Shower",
        "keywords": ["water pressure", "shower pressure", "shower", "hot water", "water temperature", "bathtub"],
    },

    # ── Service ─────────────────────────────────────────────
    "front_desk_efficiency": {
        "category": "service",
        "label": "Front Desk & Check-in",
        "keywords": ["front desk", "reception", "receptionist", "check in", "check-in", "check out", "check-out", "concierge"],
    },
    "room_cleanliness": {
        "category": "service",
        "label": "Room Cleanliness",
        "keywords": ["clean", "cleanliness", "dirty", "spotless", "filthy", "dusty", "stain", "smell", "odor", "mold"],
    },
    "restaurant_quality": {
        "category": "service",
        "label": "Restaurant & Dining",
        "keywords": ["restaurant", "dining", "food", "meal", "dinner", "lunch", "buffet", "room service", "menu"],
    },
    "breakfast_quality": {
        "category": "service",
        "label": "Breakfast",
        "keywords": ["breakfast", "morning meal", "continental breakfast", "brunch"],
    },
    "luggage_storage": {
        "category": "service",
        "label": "Luggage Storage",
        "keywords": ["luggage", "baggage", "bag storage", "stored our bags", "left our bags", "left luggage"],
    },
    "staff_friendliness": {
        "category": "service",
        "label": "Staff & Service",
        "keywords": ["staff", "service", "friendly", "helpful", "rude", "manager", "employee", "hospitality"],
    },

    # ── Surroundings ─────────────────────────────────────────
    "transport_access": {
        "category": "surroundings",
        "label": "Transport & Access",
        "keywords": ["subway", "metro", "station", "bus", "transport", "airport", "train", "transit", "walking distance"],
    },
    "noise_level": {
        "category": "surroundings",
        "label": "Outside Noise Level",
        "keywords": ["street noise", "traffic", "quiet area", "loud outside", "night noise", "noisy area", "construction noise"],
    },
    "nearby_dining": {
        "category": "surroundings",
        "label": "Nearby Dining Options",
        "keywords": ["restaurants nearby", "food nearby", "cafes nearby", "nearby dining", "nearby food", "close to restaurants"],
    },
    "location_convenience": {
        "category": "surroundings",
        "label": "Location Convenience",
        "keywords": ["location", "convenient", "central", "close to everything", "good area", "great location", "walkable"],
    },

    # ── Policy ───────────────────────────────────────────────
    "checkout_time": {
        "category": "policy",
        "label": "Check-out Time",
        "keywords": ["checkout time", "check-out time", "late checkout", "late check-out", "early checkout", "early check-out"],
    },
    "breakfast_hours": {
        "category": "policy",
        "label": "Breakfast Hours",
        "keywords": ["breakfast hours", "breakfast time", "served until", "breakfast ended", "breakfast opens", "breakfast closes"],
    },
    "parking": {
        "category": "policy",
        "label": "Parking",
        "keywords": ["parking", "garage", "car park", "parked", "valet", "parking fee", "free parking"],
    },
    "pet_policy": {
        "category": "policy",
        "label": "Pet Policy",
        "keywords": ["pet", "pets", "dog", "cat", "pet friendly", "pet-friendly", "animal"],
    },
}

ALL_DIMENSIONS: list[str] = list(DIMENSIONS.keys())

# Maps dimension name → structured sub-rating field in the Reviews data
DIMENSION_RATING_MAP: dict[str, str] = {
    "front_desk_efficiency": "checkin",
    "room_cleanliness": "roomcleanliness",
    "staff_friendliness": "service",
    "location_convenience": "location",
}
