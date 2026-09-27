"""
Thin wrapper around the Gemini REST API. Uses httpx directly instead of the
google-generativeai SDK to keep dependencies minimal.

Two jobs, matching the brief's Module B steps 1 and 4:
  - parse_intent(): text-only call, asks Gemini to return structured JSON
    with {business_type, location}.
  - vision_qa(): multimodal call, sends the candidate storefront photo and
    asks Gemini whether it's a usable "bare doorway" shot.
"""
import base64
import json
import re

import httpx

from config import GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_VISION_MODEL

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _extract_json(text: str) -> dict:
    """Gemini sometimes wraps JSON in ```json fences even when asked not to."""
    cleaned = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


async def parse_intent(user_message: str) -> dict:
    """
    Returns: {"business_type": str, "location": str}
    """
    prompt = (
        "Extract the business type and location from this request. "
        "Respond with ONLY a raw JSON object, no markdown, no commentary, "
        'in the exact shape: {"business_type": "...", "location": "..."}.\n\n'
        f"Request: {user_message}"
    )
    url = f"{GEMINI_BASE}/{GEMINI_TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = _extract_json(text)
    return {
        "business_type": parsed.get("business_type", "").strip(),
        "location": parsed.get("location", "").strip(),
    }


async def vision_qa(image_bytes: bytes) -> dict:
    """
    Returns: {"usable": bool, "reason": str}
    """
    prompt = (
        "You are looking at a street-level photo of a building. Determine "
        "whether this image clearly shows a business storefront entrance "
        "(a doorway) that is reasonably bare/plain and would fit a small "
        "decorative planter beside it. Reply with ONLY a raw JSON object, "
        'no markdown: {"usable": true or false, "reason": "short explanation"}. '
        "Set usable=false if the image shows a blank wall, faces the wrong "
        "direction, has no visible entrance, or is otherwise not usable."
    )
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    url = f"{GEMINI_BASE}/{GEMINI_VISION_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                ]
            }
        ],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = _extract_json(text)
    return {
        "usable": bool(parsed.get("usable", False)),
        "reason": parsed.get("reason", ""),
    }


async def generate_reply(business_name: str, address: str, success: bool) -> str:
    """Small, optional flourish: have Gemini phrase the chat reply."""
    if success:
        prompt = (
            f"Write one friendly sentence telling the user we found "
            f"'{business_name}' at {address} and generated a planter mockup "
            f"for its entrance."
        )
    else:
        prompt = (
            f"Write one short, friendly sentence apologizing that we could not "
            f"find a usable storefront photo near '{business_name or 'that location'}'."
        )
    url = f"{GEMINI_BASE}/{GEMINI_TEXT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
