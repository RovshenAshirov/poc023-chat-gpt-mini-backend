from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import json


app = FastAPI(title="POC-023 LLM Inference")
app.mount("/static", StaticFiles(directory="static"), name="static")

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"


class ChatRequest(BaseModel):
    prompt: str
    model: str = DEFAULT_MODEL


class ChatResponse(BaseModel):
    model: str
    response: str


@app.get("/")
async def root():
    html = Path("static/index.html").read_text()
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    payload = {
        "model": req.model,
        "prompt": req.prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        data = r.json()
    return ChatResponse(model=req.model, response=data["response"])


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    payload = {
        "model": req.model,
        "prompt": req.prompt,
        "stream": True,
    }

    async def generate():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield f"data: {json.dumps({'token': token})}\n\n"
                    if chunk.get("done"):
                        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
