"""Derive fields: apparent (feels-like) temperature and a comfort band."""
import math


def feels_like_c(temp: float, humidity: float, wind_kmh: float) -> float:
    """Australian Bureau of Meteorology apparent-temperature formula.
    AT = T + 0.33*e - 0.70*ws - 4.00, e = (rh/100) * 6.105 * exp(17.27*T/(237.7+T))
    Wind speed converted from km/h to m/s.
    """
    e = (humidity / 100.0) * 6.105 * math.exp(17.27 * temp / (237.7 + temp))
    ws = wind_kmh / 3.6
    return round(temp + 0.33 * e - 0.70 * ws - 4.0, 2)


def comfort_band(temp: float, humidity: float) -> str:
    if temp < 0:            return "Freezing"
    if temp < 10:           return "Cold"
    if temp <= 24 and humidity < 65: return "Comfortable"
    if temp <= 30 and humidity < 70: return "Warm"
    if temp > 30 or humidity >= 70:  return "Uncomfortable"
    return "Warm"


def handler(event, context=None):
    out = []
    for r in event.get("records", []):
        t, h, w = r["temperature_c"], r["humidity_pct"], r["wind_speed_kmh"]
        r2 = dict(r)
        r2["feels_like_c"] = feels_like_c(t, h, w)
        r2["comfort_band"] = comfort_band(t, h)
        out.append(r2)
    print(f"[transform] enriched {len(out)} records")
    return {"run_id": event.get("run_id"), "records": out}
