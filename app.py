"""
Intake API — FastAPI app.
POST /complaint       → run full pipeline, return JSON result
POST /complaint/stream → SSE stream of per-node steps
GET  /                → serves the chat UI
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator import run_pipeline, stream_pipeline
from shared.state import AgentState

app = FastAPI(title="Customer Service AI Pipeline")

FRONTEND_DIR = Path(__file__).parent / "frontend"


class MessageRequest(BaseModel):
    message: str
    history: list[dict] = []  # previous turns: [{"role": "user"|"assistant", "content": "..."}]


@app.post("/complaint")
def handle_complaint(req: MessageRequest):
    """Run the full agent pipeline and return the final result."""
    state = AgentState(message=req.message, history=req.history)
    result = run_pipeline(state)
    return {
        "intent": result.intent,
        "confidence": result.confidence,
        "escalated": result.escalate,
        "response": result.draft_response,
        "sources": result.source_refs,
    }


@app.post("/complaint/stream")
def stream_complaint(req: MessageRequest):
    """
    SSE endpoint — emits one event per agent node, then a final 'done' event.
    The frontend reads these with fetch + ReadableStream to show live progress.
    """

    def generate():
        state = AgentState(message=req.message, history=req.history)
        for step in stream_pipeline(state):
            yield f"data: {json.dumps(step)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serve the single-file chat UI."""
    html_path = FRONTEND_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text())
