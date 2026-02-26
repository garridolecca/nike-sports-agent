"""
Nike Sports Agent — FastAPI backend.
Serves the frontend, chat API, and CSV data endpoints.
"""

import os
import uuid
import sys
import traceback
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, FileResponse
from pydantic import BaseModel

from agent import run_agent, clear_session, HISTORY_CACHE
from tools import load_athletes_json, load_events_json

load_dotenv()

PORT = int(os.environ.get("PORT", 8000))
TITLE = os.environ.get("APP_TITLE", "Nike Sports Agent")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# =============================================================================
# STARTUP
# =============================================================================

@asynccontextmanager
async def lifespan(app_: FastAPI):
    print(f"\n{'='*50}")
    print(f"  {TITLE}")
    print(f"  http://localhost:{PORT}")
    print(f"{'='*50}\n")
    yield


app = FastAPI(
    title=TITLE,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    debug=DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# REQUEST MODELS
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ResetRequest(BaseModel):
    session_id: str


# =============================================================================
# ROUTES
# =============================================================================

@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend HTML."""
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return ORJSONResponse({"error": "index.html not found"}, status_code=404)


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Request:  { "message": "How many Nike stores are in the US?", "session_id": "abc" }
    Response: { "reply": "There are 482 stores...", "session_id": "abc" }
    """
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())

    try:
        reply = run_agent(session_id=session_id, user_message=message)
        return {"reply": reply, "session_id": session_id}
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.get("/athletes")
async def get_athletes():
    """
    Return all Nike athletes as JSON for frontend map plotting.
    Each record includes home_lat and home_lon for placing points on the map.
    """
    try:
        return load_athletes_json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events-csv")
async def get_events_csv():
    """
    Return all sports events from the CSV as JSON for frontend map plotting.
    Each record includes lat and lon for placing points on the map.
    """
    try:
        return load_events_json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset_session(req: ResetRequest):
    """Clear conversation history for a session."""
    clear_session(req.session_id)
    return {"message": "Session cleared.", "session_id": req.session_id}


@app.get("/config")
async def config():
    """Return non-secret frontend config (ArcGIS API key)."""
    return {"arcgis_api_key": os.environ.get("ARCGIS_API_KEY", "")}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "title": TITLE,
        "active_sessions": len(HISTORY_CACHE),
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=DEBUG)
