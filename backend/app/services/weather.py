from datetime import date
import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

async def fetch_current(lat: float, lon: float) -> dict | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m",
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        data = r.json()
        cur = data.get("current")
        if not cur:
            return None
        return {
            "temperature": cur.get("temperature_2m"),
            "windspeed": cur.get("wind_speed_10m"),
            "winddirection": cur.get("wind_direction_10m"),
        }

async def fetch_daily(lat: float, lon: float, start: date, end: date) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_min,temperature_2m_max",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("daily", {}) or {}
