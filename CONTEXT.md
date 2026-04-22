# POC-023 — LLM Inference (davom)

## Tizim
- Ubuntu 24.04
- NVIDIA RTX 2050, 4GB VRAM, CUDA 13.0
- Python 3.12.3
- pip ishlatamiz (uv emas)

## O'rnatilganlar
- Ollama 0.21.0 ✅
- gemma4:e4b modeli yuklangan ✅ (9.6GB, CPU da ishlaydi)
- llama3.2:3b modeli yuklangan ✅
- FastAPI 0.136.0, uvicorn, httpx ✅
- Virtual muhit: ~/poc023-app/venv ✅

## Loyiha joylashuvi
~/poc023-app/

## Hozirgi holat
Bosqich 2 da — main.py yozish boshlandi
Keyingi qadam: main.py yozib uvicorn bilan ishga tushirish

## Road Map
- Bosqich 1: Muhit sozlash ✅
- Bosqich 2: FastAPI + birinchi chat endpoint ← hozir shu yerda
- Bosqich 3: Streaming (SSE)
- Bosqich 4: Benchmark Ollama vs vLLM
- Bosqich 5: RAG tizimi

## Qoidalar
- O'zbek tilida gaplashamiz
- pip ishlatamiz, uv emas
- gemma4:e4b modeli ishlatamiz