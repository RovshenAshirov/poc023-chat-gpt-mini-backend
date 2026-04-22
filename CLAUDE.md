# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Muhit

- Ubuntu 24.04, Python 3.12.3, CUDA 13.0
- NVIDIA RTX 2050, 4GB VRAM — `gemma4:e4b` CPU da ishlaydi (9.6GB)
- Faqat `pip` ishlatiladi (`uv` emas)
- Virtual muhit: `~/poc023-app/venv`

## O'rnatilganlar

- Ollama 0.21.0 — `gemma4:e4b` (default) va `llama3.2:3b` modellari yuklangan
- FastAPI 0.136.0, uvicorn 0.45.0, httpx 0.28.1
- `requirements.txt` mavjud

## Buyruqlar

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pip install -r requirements.txt
```

## Arxitektura

```
Klient → FastAPI (port 8000) → Ollama API (port 11434) → gemma4:e4b
```

`main.py` — yagona modul:
- `GET /health` — server holati
- `POST /chat` — to'liq javob (`stream: false`)
- `POST /chat/stream` — SSE, token-by-token (`text/event-stream`)

Ollama `/api/generate` ishlatadi (`/api/chat` emas). Timeout: 120s.

SSE format: `data: {"token": "..."}` ... `data: [DONE]`

## Benchmark natijalari (Ollama vs vLLM)

Bir xil model: `gemma3:1b` (778 MB GGUF), ikkalasi ham GPU da

| Tizim | TTFT | Jami | Tok/s |
|---|---|---|---|
| Ollama | 0.51s | 1.28s | 29.8 |
| vLLM | 0.05s | 1.01s | 99.1 |

vLLM: 10x tezroq TTFT, 3.3x ko'p tok/s.

`benchmark.py` — navbatma-navbat (biri to'xtatilganda ikkinchisi ishga tushadi, VRAM uchun).
vLLM: `--quantization gguf --max-num-seqs 4 --max-model-len 512`, port 8001.
Izoh: `gemma4` vLLM da qo'llab-quvvatlanmaydi (yangi arxitektura).

## Hozirgi holat

Keyingi qadam: **Bosqich 5 — RAG tizimi**

## Road Map

- Bosqich 1: Muhit sozlash ✅
- Bosqich 2: FastAPI + `/chat` endpoint ✅
- Bosqich 3: Streaming (SSE) ✅
- Bosqich 4: Benchmark Ollama vs vLLM ✅ (vLLM 44x tez TTFT, 7x ko'p tok/s)
- Bosqich 5: RAG tizimi ← keyingi qadam

## Qoidalar

- O'zbek tilida gaplashamiz
- Default model: `gemma4:e4b`
- `pip` ishlatiladi, `uv` emas
