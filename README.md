# AI Storefront Visualizer — FastAPI-only PoC

Lean rebuild of the brief using **FastAPI only** on the backend (no Django,
no Node/Fastify). React frontend is unchanged in spirit — a single-page chat
UI.

## Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python), one process, no database
- **LLM:** Google Gemini API (called directly via REST/httpx — no SDK needed)
- **Geospatial + imagery:** Google Places Text Search + Street View Static
  API (one API key covers both)
- **Image compositing:** Pillow (alpha-composite)

## Why FastAPI-only

The brief's Fastify BFF role — parse chat → look up place → fetch photo →
QA it → composite → respond — is a single orchestration endpoint with no
persistence requirements. Django's ORM/admin/ auth stack would be pure
overhead for that; a single FastAPI app keeps it to 5 small files.

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
# edit .env: add GEMINI_API_KEY and GOOGLE_MAPS_API_KEY
uvicorn main:app --reload --port 8000
```

Get keys:
- Gemini API key: https://aistudio.google.com/apikey
- Google Maps API key (enable **Places API** and **Street View Static API**
  on it): https://console.cloud.google.com/google/maps-apis

A placeholder transparent planter PNG is already at
`backend/assets/planter.png` so the compositing step works out of the box —
swap it for your real product asset whenever you have one.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (usually http://localhost:5173). The chat UI
calls `http://localhost:8000/api/chat` — no proxy config needed for local
dev since the backend has permissive CORS.

## How a request flows

1. You type something like *"Find me an independent cafe in Soho to pitch
   our planters to"*.
2. FastAPI asks Gemini to extract `{business_type, location}`.
3. Google Places Text Search returns up to `MAX_CANDIDATES_TO_TRY` venue
   candidates (name, address, lat/lng).
4. For each candidate, in order:
   - Check Street View coverage exists at those coordinates.
   - Fetch the street-level JPEG.
   - Ask Gemini's vision model whether the shot clearly shows a usable,
     fairly bare entrance.
   - If not usable, move to the next candidate (this is the brief's
     fallback loop).
5. First usable shot gets the planter PNG alpha-composited onto it near the
   bottom of the frame.
6. Response includes the chat reply, venue details, and both images as
   base64 JPEG — the React UI renders them side by side.

## Notes on scope / trade-offs (kept deliberately lite)

- No database — everything is stateless, per-request. Add one only if you
  need to persist past results.
- Planter placement is a simple heuristic (bottom-left inset, ~22% of image
  width) rather than true doorway detection — good enough for a PoC per the
  brief's "reasonable scale" wording. If you want the planter positioned
  more precisely, that's the natural next increment (e.g. ask Gemini's
  vision model to return doorway bounding-box coordinates in the same QA
  call, then composite there instead).
- CORS is wide open (`allow_origins=["*"]`) for local dev convenience —
  tighten before deploying anywhere.
