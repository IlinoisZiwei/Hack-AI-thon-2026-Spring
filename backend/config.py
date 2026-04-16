import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Hotel name mapping (property_id -> display name)
HOTEL_NAMES = {
    "3216b1b7885bffdb336265a8de7322ba0cd477cfb3d4f99d19acf488f76a1941": "Hampton Inn Interstate",
    "ff26cdda236b233f7c481f0e896814075ac6bed335e162e0ff01d5491343f838": "Grand Hotel Roma Termini",
    "db38b19b897dbece3e34919c662b3fd66d23b615395d11fb69264dd3a9b17723": "Oceanview Resort & Spa",
    "823fb2499b4e37d99acb65e7198e75965d6496fd1c579f976205c0e6179206df": "Hilton Garden Inn Downtown",
    "7d027ef72c02eaa17af3c993fd5dba50d17b41a6280389a46c13c7e2c32a5b06": "Courtyard by Marriott Airport",
    "fa014137b3ea9af6a90c0a86a1d099e46f7e56d6eb33db1ad1ec4bdac68c3caa": "Holiday Inn Express Midtown",
    "9a0043fd4258a1286db1e253ca591662b3aac849da12d0d4f67e08b8f59be65f": "Boutique Hotel Altstadt",
    "f2d8d9557208d58577e9df7ff34e42bf86fb5b10fdfae0c3040d14c374a2a2b9": "La Maison du Soleil",
    "110f01b8ae518a0ee41047bce5c22572988a435e10ead72dc1af793bba8ce0b0": "Park Plaza Convention Center",
    "3b984f3ba8df55b2609a1e33fd694cf8407842e1d833c9b4d993b07fc83a2820": "Seaside Cottage Inn",
    "e52d67a758ce4ad0229aacc97e5dfe89984c384c51a70208f9e0cc65c9cd4676": "Alpine Lodge & Suites",
    "a036cbe1d9fbf9cba088075d1b4d966ee871df55aa4a58ba0da23c116c499052": "The Riverside Inn",
    "5f5a0cd8662f0ddf297f2d27358f680daab5d3ac22fd45a4e1c3c3ec2c101a12": "Sunrise Beach Hotel",
}

HOTEL_REVIEW_COUNTS = {
    "3216b1b7885bffdb336265a8de7322ba0cd477cfb3d4f99d19acf488f76a1941": 1094,
    "ff26cdda236b233f7c481f0e896814075ac6bed335e162e0ff01d5491343f838": 1065,
    "db38b19b897dbece3e34919c662b3fd66d23b615395d11fb69264dd3a9b17723": 1006,
    "823fb2499b4e37d99acb65e7198e75965d6496fd1c579f976205c0e6179206df": 772,
    "7d027ef72c02eaa17af3c993fd5dba50d17b41a6280389a46c13c7e2c32a5b06": 765,
    "fa014137b3ea9af6a90c0a86a1d099e46f7e56d6eb33db1ad1ec4bdac68c3caa": 728,
    "9a0043fd4258a1286db1e253ca591662b3aac849da12d0d4f67e08b8f59be65f": 152,
    "f2d8d9557208d58577e9df7ff34e42bf86fb5b10fdfae0c3040d14c374a2a2b9": 152,
    "110f01b8ae518a0ee41047bce5c22572988a435e10ead72dc1af793bba8ce0b0": 146,
    "3b984f3ba8df55b2609a1e33fd694cf8407842e1d833c9b4d993b07fc83a2820": 51,
    "e52d67a758ce4ad0229aacc97e5dfe89984c384c51a70208f9e0cc65c9cd4676": 50,
    "a036cbe1d9fbf9cba088075d1b4d966ee871df55aa4a58ba0da23c116c499052": 10,
    "5f5a0cd8662f0ddf297f2d27358f680daab5d3ac22fd45a4e1c3c3ec2c101a12": 0,
}

DIMENSION_LABELS = {
    "wifi_speed": "WiFi & Internet",
    "soundproofing": "Soundproofing",
    "air_conditioning": "Air Conditioning / Heating",
    "elevator": "Elevator",
    "water_pressure": "Water Pressure",
    "power_outlets": "Power Outlets & Charging",
    "front_desk": "Front Desk Service",
    "housekeeping": "Housekeeping & Cleanliness",
    "restaurant_quality": "Restaurant & Dining Quality",
    "luggage_storage": "Luggage Storage",
    "transport_access": "Transport Access",
    "noise_level": "Outside Noise Level",
    "nearby_dining": "Nearby Dining Options",
    "walkable_attractions": "Walkable Attractions",
    "checkout_time": "Check-out Time",
    "breakfast_hours": "Breakfast Hours",
    "parking_fee": "Parking Fee",
    "pet_policy": "Pet Policy",
    "pool": "Swimming Pool",
    "gym": "Gym / Fitness Center",
}
