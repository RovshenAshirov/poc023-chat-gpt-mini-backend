# Bosqich 4 — Benchmark: Ollama vs vLLM

---

## Maqsad

```
Ollama vs vLLM — qaysi biri tezroq?

Bir xil sharoit:
✅ Bir xil model    → gemma3:1b
✅ Bir xil savollar → 3 ta prompt
✅ Bir xil mashina  → bizning kompyuter
✅ Bir xil qurilma  → ikkalasi GPU da
```

---

## Benchmark nima?

Ikki narsani **bir xil sharoitda** sinab, natijalarni taqqoslash.

```
Noto'g'ri benchmark:
Ollama → CPU da
vLLM   → GPU da
→ Natija: "vLLM tezroq!" — lekin sababi GPU, framework emas! 😤

To'g'ri benchmark:
Ollama → GPU da
vLLM   → GPU da
→ Natija: "vLLM tezroq!" — sababi PagedAttention! ✅
```

---

## O'lchanadigan ko'rsatkichlar

### TTFT — Time To First Token

```
Foydalanuvchi so'rov yubordi
        ↓
... kutish ...
        ↓
Birinchi token keldi ← shu vaqt = TTFT

Ollama: 0.49s  → foydalanuvchi 0.49 sekund kutadi
vLLM:   0.04s  → foydalanuvchi 0.04 sekund kutadi ✅
```

Nima uchun muhim?

```
Tez TTFT:
→ Yuborish bosdingiz
→ 0.04 sekundda birinchi harf chiqadi
→ "Tez ishlayapti!" ✅

Sekin TTFT:
→ Yuborish bosdingiz
→ 0.5 sekund hech narsa yo'q
→ "Ishlamayaptimi?" 😤
```

### Tok/s — Tokens per Second

```
1 sekundda nechta token chiqdi?

Ollama:  35.3 tok/s → taxminan 26 so'z/sekund
vLLM:   100.0 tok/s → taxminan 75 so'z/sekund ✅
```

---

## vLLM o'rnatish

```bash
pip install vllm
```

---

## gemma3-1b.gguf faylini olish

vLLM HuggingFace formatini kutadi, lekin Ollama GGUF saqlaydi.
Ollama allaqachon yuklagan — nusxa olamiz:

```bash
sg ollama -c "cp /usr/share/ollama/.ollama/models/blobs/sha256-7cd4618c1faf8b7233c6c906dac1694b6a47684b37b8895d470ac688520b9c01 /home/rovshen/poc023-app/gemma3-1b.gguf"
```

Tekshirish:

```bash
ls -lh ~/poc023-app/gemma3-1b.gguf
# -rw-r--r-- 1 rovshen ollama 778M gemma3-1b.gguf
```

---

## vLLM ishga tushirish

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /home/rovshen/poc023-app/gemma3-1b.gguf \
    --quantization gguf \
    --max-model-len 512 \
    --max-num-seqs 4 \
    --port 8001
```

```
--model           → qaysi model (GGUF fayl)
--quantization    → model formati
--max-model-len   → maksimum token uzunligi
--max-num-seqs    → bir vaqtda nechta so'rov
--port            → qaysi portda ishlaydi
```

Tayyor bo'lganda:

```
Application startup complete. ✅
```

Tekshirish:

```bash
curl http://localhost:8001/health
# → {}
```

---

## benchmark.py — to'liq kod va izohlar

```python
import asyncio
import time
import httpx
import statistics
import json
import subprocess

OLLAMA_URL   = "http://localhost:11434/api/generate"
VLLM_URL     = "http://localhost:8001/v1/completions"
OLLAMA_MODEL = "gemma3:1b"
VLLM_MODEL   = "/home/rovshen/poc023-app/gemma3-1b.gguf"

# 3 ta savol × 3 marta = 9 o'lchov (o'rtacha uchun)
PROMPTS = [
    "What is 2+2?",
    "Name three planets in our solar system.",
    "Write a haiku about the ocean.",
]
RUNS = 3


# vLLM ni Python dan ishga tushirish
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
        stdout=subprocess.DEVNULL,  # loglarni yashirish
        stderr=subprocess.DEVNULL,
    )
    return proc  # keyinroq to'xtatish uchun


# vLLM ni to'xtatish
def stop_vllm(proc):
    proc.terminate()
    proc.wait()


# Ollama modelini VRAM dan bo'shatish
# (vLLM uchun joy bo'shatish)
def ollama_unload():
    subprocess.run(
        ["ollama", "stop", OLLAMA_MODEL],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# Server tayyor bo'lguncha kutish
async def wait_for_url(url: str, timeout: int = 180):
    async with httpx.AsyncClient(timeout=5.0) as client:
        for _ in range(timeout):
            try:
                await client.get(url)
                return True       # tayyor ✅
            except Exception:
                await asyncio.sleep(1)  # 1 sekund kut, qayta urин
    return False  # 180 sekund o'tdi, ishlamadi ❌


# Ollama ni o'lchash
async def bench_ollama(client: httpx.AsyncClient, prompt: str) -> dict:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}

    start            = time.perf_counter()  # vaqt boshlanadi
    first_token_time = None
    eval_count       = 0
    eval_duration_ns = 0

    async with client.stream("POST", OLLAMA_URL, json=payload) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if not line:
                continue
            chunk = json.loads(line)

            # Birinchi token keldi → TTFT o'lchash
            if chunk.get("response") and first_token_time is None:
                first_token_time = time.perf_counter() - start

            # Oxirgi qator → Ollama tok/s ni o'zi beradi
            if chunk.get("done"):
                eval_count       = chunk.get("eval_count", 0)
                eval_duration_ns = chunk.get("eval_duration", 0)

    total = time.perf_counter() - start
    tps   = (eval_count / eval_duration_ns * 1e9) if eval_duration_ns else 0

    return {"ttft": first_token_time, "total": total, "tps": tps}


# vLLM ni o'lchash
async def bench_vllm(client: httpx.AsyncClient, prompt: str) -> dict:
    payload = {
        "model":      VLLM_MODEL,
        "prompt":     prompt,
        "max_tokens": 100,
        "stream":     True,
    }

    start            = time.perf_counter()
    first_token_time = None
    token_count      = 0

    async with client.stream("POST", VLLM_URL, json=payload) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            text  = chunk["choices"][0].get("text", "")

            # Birinchi token → TTFT
            if text and first_token_time is None:
                first_token_time = time.perf_counter() - start

            if text:
                token_count += 1  # tokenlarni o'zimiz sanamiz

    total = time.perf_counter() - start
    tps   = token_count / total if total else 0

    return {"ttft": first_token_time, "total": total, "tps": tps}


# 9 marta o'lchab o'rtacha olish
async def measure(fn, client):
    ttfts, totals, tps_list = [], [], []

    for prompt in PROMPTS:       # 3 ta savol
        for _ in range(RUNS):    # har biri 3 marta
            r = await fn(client, prompt)
            if r["ttft"]:
                ttfts.append(r["ttft"])
            totals.append(r["total"])
            tps_list.append(r["tps"])

    return {
        "ttft":  statistics.mean(ttfts)    if ttfts else 0,
        "total": statistics.mean(totals),
        "tps":   statistics.mean(tps_list),
    }


# Asosiy funksiya
async def run_benchmark():
    print(f"\n{'='*65}")
    print(f"{'Tizim':<28} {'TTFT (s)':>10} {'Total (s)':>10} {'Tok/s':>10}")
    print(f"{'='*65}")

    results = []

    async with httpx.AsyncClient(timeout=300.0) as client:

        # 1. Ollama benchmark (GPU)
        print("Ollama yuklanmoqda (GPU)...", end="\r")
        await wait_for_url(f"{OLLAMA_URL.rsplit('/api', 1)[0]}/")
        r = await measure(bench_ollama, client)
        results.append(("Ollama (gemma3:1b)", r, "GPU"))
        print(f"{'Ollama (gemma3:1b)':<28} {r['ttft']:>10.2f} {r['total']:>10.2f} {r['tps']:>10.1f}  [GPU]")

        # 2. Ollama modelini VRAM dan bo'shatish
        print("Ollama VRAM bo'shatilmoqda...", end="\r")
        ollama_unload()
        await asyncio.sleep(8)  # to'liq bo'shashi uchun

        # 3. vLLM ishga tushirish (GPU)
        print("vLLM ishga tushirilmoqda (GPU)...", end="\r")
        proc  = start_vllm()
        ready = await wait_for_url("http://localhost:8001/health")
        if not ready:
            print("vLLM ishga tushmadi!")
            proc.terminate()
            return

        # 4. vLLM benchmark
        r = await measure(bench_vllm, client)
        results.append(("vLLM  (gemma3:1b)", r, "GPU"))
        print(f"{'vLLM  (gemma3:1b)':<28} {r['ttft']:>10.2f} {r['total']:>10.2f} {r['tps']:>10.1f}  [GPU]")

        # 5. vLLM ni to'xtatish
        stop_vllm(proc)

    # Natijalar
    print(f"{'='*65}")
    print(f"Har bir tizim: {len(PROMPTS)} prompt x {RUNS} run = {len(PROMPTS)*RUNS} o'lchov")

    ttft_winner = "Ollama" if results[0][1]["ttft"] < results[1][1]["ttft"] else "vLLM"
    tps_winner  = "Ollama" if results[0][1]["tps"]  > results[1][1]["tps"]  else "vLLM"
    print(f"\nTTFT eng tez:   {ttft_winner}")
    print(f"Tok/s eng ko'p: {tps_winner}\n")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
```

---

## Ketma-ketlik

```
python benchmark.py
        ↓
1. Ollama ishlayaptimi? → wait_for_url ✅
        ↓
2. 9 ta so'rov → Ollama → o'rtacha
   TTFT: 0.49s, Tok/s: 35.3
        ↓
3. ollama stop → VRAM bo'shadi
   asyncio.sleep(8) → to'liq bo'shashi uchun
        ↓
4. vLLM ishga tushadi (subprocess)
   wait_for_url → tayyor ✅
        ↓
5. 9 ta so'rov → vLLM → o'rtacha
   TTFT: 0.04s, Tok/s: 100.0
        ↓
6. vLLM to'xtatiladi
        ↓
7. Natijalar:
=================================================================
Ollama (gemma3:1b)    0.49s    1.13s    35.3  [GPU]
vLLM  (gemma3:1b)    0.04s    1.00s   100.0  [GPU]
=================================================================
TTFT eng tez:   vLLM
Tok/s eng ko'p: vLLM
```

---

## Natijalar tahlili

| Tizim | TTFT | Tok/s | Qurilma |
|-------|------|-------|---------|
| Ollama | 0.49s | 35.3 | GPU |
| vLLM | **0.04s** | **100.0** | GPU |

```
TTFT:  0.49 ÷ 0.04 = 12x → vLLM tezroq
Tok/s: 100.0 ÷ 35.3 = 2.8x → vLLM ko'proq
```

### Nima uchun bunday farq?

```
TTFT 12x tezroq:
→ vLLM model GPU da allaqachon yuklangan
→ So'rov keldi → darhol ishga tushdi
→ Ollama: model yuklashga vaqt ketadi

Tok/s 2.8x ko'p:
→ PagedAttention → VRAM samarali
→ GPU parallel hisob-kitob to'liq ishlatiladi
```

---

## Xulosa

```
Development uchun → Ollama ✅
→ O'rnatish oson, 1 buyruq
→ GPU da ham yaxshi ishlaydi
→ 1 foydalanuvchi uchun yetarli

Production uchun → vLLM ✅
→ 12x tezroq TTFT
→ 2.8x ko'p tok/s
→ Ko'p foydalanuvchi → farq yanada katta
→ PagedAttention + Continuous batching
```