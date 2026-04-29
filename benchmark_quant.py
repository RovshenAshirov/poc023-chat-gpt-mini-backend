import asyncio
import time
import httpx
import statistics
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELS = [
    ("gemma3:1b",         "INT4 (Q4_K_M)", "815 MB"),
    ("gemma3:1b-it-q8_0", "INT8 (Q8_0)",   "1.1 GB"),
]

PROMPTS = [
    "What is 2+2?",
    "Name three planets in our solar system.",
    "Write a haiku about the ocean.",
]
RUNS = 3


async def bench(client: httpx.AsyncClient, model: str, prompt: str) -> dict:
    payload = {"model": model, "prompt": prompt, "stream": True}

    start            = time.perf_counter()
    first_token_time = None
    eval_count       = 0
    eval_duration_ns = 0

    async with client.stream("POST", OLLAMA_URL, json=payload) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if chunk.get("response") and first_token_time is None:
                first_token_time = time.perf_counter() - start
            if chunk.get("done"):
                eval_count       = chunk.get("eval_count", 0)
                eval_duration_ns = chunk.get("eval_duration", 0)

    total = time.perf_counter() - start
    tps   = (eval_count / eval_duration_ns * 1e9) if eval_duration_ns else 0
    return {"ttft": first_token_time, "total": total, "tps": tps}


async def run():
    print(f"\n{'='*70}")
    print(f"{'Model':<28} {'Quant':>12} {'Hajm':>8} {'TTFT':>8} {'Tok/s':>8}")
    print(f"{'='*70}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        for model, quant, size in MODELS:
            ttfts, tps_list = [], []

            for prompt in PROMPTS:
                for _ in range(RUNS):
                    r = await bench(client, model, prompt)
                    if r["ttft"]:
                        ttfts.append(r["ttft"])
                    tps_list.append(r["tps"])

            avg_ttft = statistics.mean(ttfts) if ttfts else 0
            avg_tps  = statistics.mean(tps_list)

            print(f"{model:<28} {quant:>12} {size:>8} {avg_ttft:>8.2f} {avg_tps:>8.1f}")

    print(f"{'='*70}")
    print(f"Har bir model: {len(PROMPTS)} prompt x {RUNS} run = {len(PROMPTS)*RUNS} o'lchov\n")


if __name__ == "__main__":
    asyncio.run(run())
