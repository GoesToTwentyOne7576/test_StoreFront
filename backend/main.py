"""
AI Storefront Visualizer -- FastAPI backend (single service, no Django).

Run:
    uvicorn main:app --reload --port 8000

Pipeline for POST /api/chat, matching the brief's Module B:
  1. Intent parsing        -> gemini_client.parse_intent
  2. Geospatial lookup     -> geo_service.find_venue_candidates
  3. Imagery retrieval     -> geo_service.fetch_street_view_image
  4. Vision QA + fallback  -> gemini_client.vision_qa (loops candidates)
  5. Compositing           -> image_compositor.overlay_planter
  6. Response payload      -> base64 images + venue info + chat reply
"""
import base64

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import gemini_client
import geo_service
import image_compositor
from config import MAX_CANDIDATES_TO_TRY

app = FastAPI(title="AI Storefront Visualizer")

# Lite CORS setup so the React dev server (Vite/CRA on :5173 or :3000) can
# call this API straight from localhost during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    success: bool
    venue: dict | None = None
    original_image_base64: str | None = None
    composited_image_base64: str | None = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    intent = await gemini_client.parse_intent(req.message)
    business_type = intent["business_type"]
    location = intent["location"]

    candidates = await geo_service.find_venue_candidates(
        business_type, location, limit=MAX_CANDIDATES_TO_TRY
    )

    for candidate in candidates:
        lat, lng = candidate["lat"], candidate["lng"]

        if not await geo_service.has_street_view(lat, lng):
            continue

        photo_bytes = await geo_service.fetch_street_view_image(lat, lng)
        qa = await gemini_client.vision_qa(photo_bytes)

        if not qa["usable"]:
            continue  # Step 4 fallback: try the next candidate

        composited_bytes = image_compositor.overlay_planter(photo_bytes)
        reply = await gemini_client.generate_reply(
            candidate["name"], candidate["address"], success=True
        )

        return ChatResponse(
            reply=reply,
            success=True,
            venue=candidate,
            original_image_base64=base64.b64encode(photo_bytes).decode(),
            composited_image_base64=base64.b64encode(composited_bytes).decode(),
        )

    # Ran out of candidates without a usable shot.
    reply = await gemini_client.generate_reply(
        business_type or location, location, success=False
    )
    return ChatResponse(reply=reply, success=False)


@app.get("/health")
async def health():
    return {"status": "ok"}
