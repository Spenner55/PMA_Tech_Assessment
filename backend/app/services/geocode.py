import os, re
from typing import Tuple
import httpx

GEOAPIFY_KEY = os.getenv("GEOAPIFY_API_KEY")
GEOAPIFY_URL = "https://api.geoapify.com/v1/geocode/search"

# Patterns to detect the input kind
RE_LATLON = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")
RE_US_ZIP = re.compile(r"^\d{5}(?:-\d{4})?$")
RE_CA_PC  = re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$")

class GeocodeError(ValueError):
    pass

async def geocode_any(raw: str) -> Tuple[float, float, str]:
    """
    Accepts:
      - 'lat,lon'
      - US ZIP (12345 or 12345-6789)
      - Canadian postal (T2J 3J5 or t2j3j5)
      - Any free-form city/town/address globally
    Returns: (lat, lon, resolved_name)
    """
    s = raw.strip()
    # 1) lat,lon fast path
    m = RE_LATLON.match(s)
    if m:
        return float(m.group(1)), float(m.group(2)), s

    # 2) Normalize CA postal (insert space, uppercase)
    if RE_CA_PC.match(s):
        s = s.upper().replace(" ", "")
        s = f"{s[:3]} {s[3:]}"

    # 3) Build Geoapify query params
    if not GEOAPIFY_KEY:
        raise GeocodeError("Missing GEOAPIFY_API_KEY")

    params = {
        "text": s,
        "limit": 1,
        "format": "json",
        "apiKey": GEOAPIFY_KEY,
    }

    # Optional biasing to improve postal lookups (keeps global coverage)
    if RE_US_ZIP.match(raw):
        params["bias"] = "countrycode:us"
    elif RE_CA_PC.match(raw):
        params["bias"] = "countrycode:ca"

    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(GEOAPIFY_URL, params=params)
        r.raise_for_status()
        data = r.json()
        feats = data.get("results") or data.get("features") or []
        if not feats:
            raise GeocodeError("Location not found")

        # Geoapify returns either 'results' (standard) or 'features' (geojson)
        top = feats[0]
        lat = top.get("lat") or (top.get("geometry", {}).get("coordinates", [None, None])[1])
        lon = top.get("lon") or (top.get("geometry", {}).get("coordinates", [None, None])[0])
        name = top.get("formatted") or top.get("result_type") or s

        if lat is None or lon is None:
            raise GeocodeError("Geocoder returned no coordinates")

        return float(lat), float(lon), str(name)
