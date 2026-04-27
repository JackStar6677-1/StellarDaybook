from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(cfg: dict) -> dict[str, Any] | None:
    w = cfg.get("weather") or {}
    lat = w.get("latitude")
    lon = w.get("longitude")
    tz = cfg.get("timezone") or "America/Santiago"
    if lat is None or lon is None:
        return None
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "timezone": tz,
    }
    try:
        r = requests.get(OPEN_METEO, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        cur = data.get("current") or {}
        return {
            "label": w.get("label", "clima"),
            "time": cur.get("time"),
            "temperature_c": cur.get("temperature_2m"),
            "relative_humidity": cur.get("relative_humidity_2m"),
            "precipitation_mm": cur.get("precipitation"),
            "weather_code": cur.get("weather_code"),
            "wind_speed_kmh": cur.get("wind_speed_10m"),
        }
    except Exception:
        logger.warning("Open-Meteo no disponible", exc_info=True)
        return None
