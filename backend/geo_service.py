"""
Geospatial lookup (Step 2) and street-level imagery retrieval (Step 3).

Uses Google's Places Text Search API and Street View Static API -- one API
key covers both, which keeps the "developer's choice" surface area small.
"""
from typing import List, Dict

import httpx

from config import GOOGLE_MAPS_API_KEY

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
STREETVIEW_METADATA_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
STREETVIEW_IMAGE_URL = "https://maps.googleapis.com/maps/api/streetview"


async def find_venue_candidates(business_type: str, location: str, limit: int) -> List[Dict]:
    """
    Returns a list of candidates: [{"name", "address", "lat", "lng"}, ...]
    ordered as returned by Google (roughly relevance/prominence).
    """
    query = f"{business_type} in {location}"
    params = {"query": query, "key": GOOGLE_MAPS_API_KEY}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(PLACES_TEXT_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])[:limit]
    return [
        {
            "name": r.get("name", "Unknown"),
            "address": r.get("formatted_address", ""),
            "lat": r["geometry"]["location"]["lat"],
            "lng": r["geometry"]["location"]["lng"],
        }
        for r in results
    ]


async def has_street_view(lat: float, lng: float) -> bool:
    params = {"location": f"{lat},{lng}", "key": GOOGLE_MAPS_API_KEY}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(STREETVIEW_METADATA_URL, params=params)
        resp.raise_for_status()
        return resp.json().get("status") == "OK"


async def fetch_street_view_image(lat: float, lng: float) -> bytes:
    """Fetches a single street-level JPEG frontage shot for the coordinates."""
    params = {
        "size": "640x640",
        "location": f"{lat},{lng}",
        "fov": "80",
        "key": GOOGLE_MAPS_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(STREETVIEW_IMAGE_URL, params=params)
        resp.raise_for_status()
        return resp.content
