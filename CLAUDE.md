# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Muhit

- Ubuntu 24.04, Python 3.12.3, CUDA 13.0
- NVIDIA RTX 2050, 4GB VRAM
- Faqat `pip` ishlatiladi (`uv` emas)
- Virtual muhit: `~/poc023-app/venv`

## O'rnatilganlar

- Ollama 0.21.0 — `gemma3:4b` (default chat), `gemma3:1b` (RAG), `gemma3:1b-it-q8_0` (INT8) yuklangan
- FastAPI 0.136.0, uvicorn 0.45.0, httpx 0.28.1
- LangChain, ChromaDB, sentence-transformers (RAG uchun)
- vLLM 0.19.1 (benchmark uchun, port 8001)
- `requirements.txt` mavjud

## Buyruqlar

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pip install -r requirements.txt
```

## Fayllar

```
main.py              — FastAPI server (asosiy modul)
rag.py               — RAG pipeline (LangChain + ChromaDB)
benchmark.py         — Ollama vs vLLM benchmark
benchmark_quant.py   — INT4 vs INT8 quantization benchmark
static/index.html    — Chat UI
uploads/             — Yuklangan fayllar (RAG uchun)
chroma_db/           — ChromaDB vektor bazasi
gemma3-1b.gguf       — vLLM uchun GGUF fayl
```

## Arxitektura

```
Klient → FastAPI (port 8000) → Ollama API (port 11434) → gemma3:4b
                             → RAG pipeline → ChromaDB + gemma3:1b
```

`main.py` endpointlari:
- `GET /`             — Chat UI (static/index.html)
- `GET /health`       — Server holati
- `POST /chat`        — To'liq javob (`stream: false`)
- `POST /chat/stream` — SSE, token-by-token (`text/event-stream`)
- `POST /rag/upload`  — Fayl (PDF/TXT) yuklash va indekslash
- `POST /rag/query`   — Hujjatdan savol berish

Ollama `/api/generate` ishlatadi (`/api/chat` emas). Timeout: 120s.

SSE format: `data: {"token": "..."}` ... `data: [DONE]`

## RAG tizimi (rag.py)

Embedding: `all-MiniLM-L6-v2` (lokal, internet shart emas)
Chunk: 500 belgi, 50 belgi overlap
Qidiruv: top-3 o'xshash bo'lak
LLM javob: `gemma3:1b` via Ollama

```
POST /rag/upload → fayl saqlash → LangChain → bo'lish → vektorlashtirish → ChromaDB
POST /rag/query  → savol → vektor → ChromaDB → top-3 → prompt → gemma3:1b → javob
```

## Benchmark natijalari

### Bosqich 4: Ollama vs vLLM (gemma3:1b, GPU)

| Tizim | TTFT | Jami | Tok/s |
|---|---|---|---|
| Ollama | 0.51s | 1.28s | 29.8 |
| vLLM | 0.05s | 1.01s | 99.1 |

vLLM: ~10x tezroq TTFT, ~3.3x ko'p tok/s.
`benchmark.py` — navbatma-navbat (VRAM uchun).
vLLM: `--quantization gguf --max-num-seqs 4 --max-model-len 512`, port 8001.

### Bosqich 6: Quantization (INT4 vs INT8, Ollama, GPU)

| Model | Quant | Hajm | TTFT | Tok/s |
|---|---|---|---|---|
| gemma3:1b | INT4 (Q4_K_M) | 815 MB | 0.42s | 106.7 |
| gemma3:1b-it-q8_0 | INT8 (Q8_0) | 1.1 GB | 0.40s | 80.5 |

INT4: tezroq (VRAM ga yaxshi sig'adi). INT8: aniqroq javoblar.

## Road Map

- Bosqich 1: Muhit sozlash ✅
- Bosqich 2: FastAPI + `/chat` endpoint ✅
- Bosqich 3: Streaming (SSE) ✅
- Bosqich 4: Benchmark Ollama vs vLLM ✅
- Bosqich 5: RAG tizimi ✅ (`rag.py`, `/rag/upload`, `/rag/query`)
- Bosqich 6: Quantization benchmark ✅ (`benchmark_quant.py`)

## Qoidalar

- O'zbek tilida gaplashamiz
- Default model: `gemma3:4b`
- `pip` ishlatiladi, `uv` emas