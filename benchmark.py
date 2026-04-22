import asyncio
import time
import httpx
import statistics
import json
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"
VLLM_URL = "http://localhost:8001/v1/completions"
OLLAMA_MODEL = "gemma3:1b"
VLLM_MODEL = "/home/rovshen/poc023-app/gemma3-1b.gguf"

PROMPTS = [
    "What is 2+2?",
    "Name three planets in our solar system.",
    "Write a haiku about the ocean.",
]
RUNS = 3


def start_vllm():
    proc = subprocess.Popen(
        [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", VLLM_MODEL,
            "--quantization", "gguf",
            "--max-model-len", "512",
            "--max-num-seqs", "4",
            "--port", "8001",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def stop_vllm(proc):
    proc.terminate()
    proc.wait()


def ollama_unload():
    subprocess.run(
        ["ollama", "stop", OLLAMA_MODEL],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


async def wait_for_url(url: str, timeout: int = 180):
    async with httpx.AsyncClient(timeout=5.0) as client:
        for _ in range(timeout):
            try:
                await client.get(url)
                return True
            except Exception:
                await asyncio.sleep(1)
    return False


async def bench_ollama(client: httpx.AsyncClient, prompt: str) -> dict:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}
    start = time.perf_counter()
    first_token_time = None
    eval_count = 0
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
                eval_count = chunk.get("eval_count", 0)
                eval_duration_ns = chunk.get("eval_duration", 0)

    total = time.perf_counter() - start
    tps = (eval_count / eval_duration_ns * 1e9) if eval_duration_ns else 0
    return {"ttft": first_token_time, "total": total, "tps": tps}


async def bench_vllm(client: httpx.AsyncClient, prompt: str) -> dict:
    payload = {
        "model": VLLM_MODEL,
        "prompt": prompt,
        "max_tokens": 100,
        "stream": True,
    }
    start = time.perf_counter()
    first_token_time = None
    token_count = 0

    async with client.stream("POST", VLLM_URL, json=payload) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            text = chunk["choices"][0].get("text", "")
            if text and first_token_time is None:
                first_token_time = time.perf_counter() - start
            if text:
                token_count += 1

    total = time.perf_counter() - start
    tps = token_count / total if total else 0
    return {"ttft": first_token_time, "total": total, "tps": tps}


async def measure(fn, client):
    ttfts, totals, tps_list = [], [], []
    for prompt in PROMPTS:
        for _ in range(RUNS):
            r = await fn(client, prompt)
            if r["ttft"]:
                ttfts.append(r["ttft"])
            totals.append(r["total"])
            tps_list.append(r["tps"])
    return {
        "ttft": statistics.mean(ttfts) if ttfts else 0,
        "total": statistics.mean(totals),
        "tps": statistics.mean(tps_list),
    }


async def run_benchmark():
    print(f"\n{'='*65}")
    print(f"{'Tizim':<28} {'TTFT (s)':>10} {'Total (s)':>10} {'Tok/s':>10}")
    print(f"{'='*65}")

    results = []

    async with httpx.AsyncClient(timeout=300.0) as client:
        # --- Ollama (GPU) ---
        print("Ollama yuklanmoqda (GPU)...", end="\r")
        await wait_for_url(f"{OLLAMA_URL.rsplit('/api', 1)[0]}/")
        r = await measure(bench_ollama, client)
        results.append(("Ollama (gemma3:1b)", r, "GPU"))
        print(f"{'Ollama (gemma3:1b)':<28} {r['ttft']:>10.2f} {r['total']:>10.2f} {r['tps']:>10.1f}  [GPU]")

        # Ollama modelini VRAM dan bo'shatamiz
        print("Ollama VRAM bo'shatilmoqda...", end="\r")
        ollama_unload()
        await asyncio.sleep(8)

        # --- vLLM (GPU) ---
        print("vLLM ishga tushirilmoqda (GPU)...", end="\r")
        proc = start_vllm()
        ready = await wait_for_url("http://localhost:8001/health")
        if not ready:
            print("vLLM ishga tushmadi!")
            proc.terminate()
            return

        r = await measure(bench_vllm, client)
        results.append(("vLLM  (gemma3:1b)", r, "GPU"))
        print(f"{'vLLM  (gemma3:1b)':<28} {r['ttft']:>10.2f} {r['total']:>10.2f} {r['tps']:>10.1f}  [GPU]")
        stop_vllm(proc)

    print(f"{'='*65}")
    print(f"Har bir tizim: {len(PROMPTS)} prompt x {RUNS} run = {len(PROMPTS)*RUNS} o'lchov")
    ttft_winner = "Ollama" if results[0][1]["ttft"] < results[1][1]["ttft"] else "vLLM"
    tps_winner  = "Ollama" if results[0][1]["tps"]  > results[1][1]["tps"]  else "vLLM"
    print(f"\nTTFT eng tez:   {ttft_winner}")
    print(f"Tok/s eng ko'p: {tps_winner}\n")


if __name__ == "__main__":
    asyncio.run(run_benchmark())