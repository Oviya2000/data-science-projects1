"""Validate that each record has the required fields and sensible ranges."""
REQUIRED = ["city", "country", "latitude", "longitude", "observed_at_utc",
            "temperature_c", "humidity_pct", "wind_speed_kmh", "condition"]


def valid(r: dict) -> bool:
    if any(r.get(k) is None for k in REQUIRED):
        return False
    if not (-90 <= r["latitude"] <= 90):    return False
    if not (-180 <= r["longitude"] <= 180): return False
    if not (-70 <= r["temperature_c"] <= 60):  return False
    if not (0 <= r["humidity_pct"] <= 100):    return False
    if not (0 <= r["wind_speed_kmh"] <= 250):  return False
    return True


def handler(event, context=None):
    records = event.get("records", [])
    kept = [r for r in records if valid(r)]
    print(f"[validate] in={len(records)}  kept={len(kept)}  dropped={len(records)-len(kept)}")
    return {"run_id": event.get("run_id"),
            "records": kept,
            "valid_count": len(kept)}
