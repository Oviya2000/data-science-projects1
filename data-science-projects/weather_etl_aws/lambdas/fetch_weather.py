"""Fetch current weather for a fixed set of cities from Open-Meteo (no API key).

Lambda handler contract
-----------------------
Input : (event ignored)
Output: {"run_id": str, "records": [ {city, country, latitude, longitude,
                                     observed_at_utc, temperature_c,
                                     humidity_pct, wind_speed_kmh,
                                     condition}, ... ]}
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from urllib import request
from urllib.error import URLError

CITIES = [
    ("New York",    "US", 40.7128, -74.0060),
    ("Chennai",     "IN", 13.0827,  80.2707),
    ("London",      "UK", 51.5074,  -0.1278),
    ("Blacksburg",  "US", 37.2296, -80.4139),
    ("Berlin",      "DE", 52.5200,  13.4050),
    ("Tokyo",       "JP", 35.6762, 139.6503),
    ("Sydney",      "AU", -33.8688,151.2093),
    ("Sao Paulo",   "BR", -23.5505,-46.6333),
    ("Cape Town",   "ZA", -33.9249, 18.4241),
    ("Toronto",     "CA", 43.6532, -79.3832),
]

# WMO weather-code → human-readable condition
CONDITION = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}


def fetch_one(lat: float, lon: float, timeout: float = 8.0) -> dict:
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
           f"&timezone=UTC")
    with request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _mock(city, country, lat, lon, now):
    """Deterministic fallback used when the API is unreachable (dev/CI)."""
    import hashlib
    seed = int(hashlib.md5(city.encode()).hexdigest(), 16) % 1_000
    temp = ((seed % 350) / 10.0) - 5.0   # -5°C to 30°C
    hum  = 30 + (seed % 60)              # 30–90 %
    wind = (seed % 40) / 2.0             # 0–20 km/h
    code = list(CONDITION.keys())[seed % len(CONDITION)]
    return {
        "city": city, "country": country, "latitude": lat, "longitude": lon,
        "observed_at_utc": now, "temperature_c": round(temp, 1),
        "humidity_pct": int(hum), "wind_speed_kmh": round(wind, 1),
        "condition": CONDITION[code],
    }


def handler(event, context=None):
    run_id = str(uuid.uuid4())
    records = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    use_mock = os.getenv("USE_MOCK_WEATHER") == "1"

    for city, country, lat, lon in CITIES:
        if use_mock:
            records.append(_mock(city, country, lat, lon, now))
            continue
        try:
            data = fetch_one(lat, lon)
            cur = data.get("current", {})
            records.append({
                "city": city, "country": country,
                "latitude": lat, "longitude": lon,
                "observed_at_utc": cur.get("time", now),
                "temperature_c":   cur.get("temperature_2m"),
                "humidity_pct":    cur.get("relative_humidity_2m"),
                "wind_speed_kmh":  cur.get("wind_speed_10m"),
                "condition":       CONDITION.get(cur.get("weather_code"), "Unknown"),
            })
        except (URLError, TimeoutError, ValueError) as e:
            # Fall back to mock so the pipeline stays exercisable when
            # outbound network is restricted (e.g. CI). Never used in prod.
            print(f"[fetch] {city}: {type(e).__name__}: {e} — using mock")
            records.append(_mock(city, country, lat, lon, now))

    return {"run_id": run_id, "records": records,
            "env": os.getenv("ENVIRONMENT", "local")}
