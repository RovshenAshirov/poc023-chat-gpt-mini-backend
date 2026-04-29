# Bosqich 6 — Quantization: INT4 vs INT8

---

## Quantization nima?

Model ichida **1 milliard son** bor (parametrlar).
Bu sonlar qancha joy egallashi — quantization bilan boshqariladi.

### Bit nima?

```
Kompyuter faqat 0 va 1 biladi → bu bit

1 bit  → 2 ta qiymat:   0, 1
4 bit  → 16 ta qiymat:  0 ... 15
8 bit  → 256 ta qiymat: 0 ... 255
32 bit → 4 milliard ta qiymat
```

Qancha ko'p bit → shuncha aniq son → shuncha ko'p xotira.

---

## FP32, FP16, INT8, INT4 nima?

```
FP  = Floating Point = kasrli son
INT = Integer = butun son

FP32 → 32 bit → 4 bayt → kasrli, juda aniq
FP16 → 16 bit → 2 bayt → kasrli, aniq
INT8 →  8 bit → 1 bayt → butun songa aylanib saqlanadi
INT4 →  4 bit → 0.5 bayt → butun songa aylanib saqlanadi
```

### 1 ta sonni saqlash misoli

```
Asl son: 0.823456789

FP32: 0.823456789  ← to'liq aniqlik (4 bayt)
FP16: 0.823486     ← biroz farq    (2 bayt)
INT8: 0.826        ← ancha farq    (1 bayt)
INT4: 0.812        ← ko'p farq     (0.5 bayt)
```

### INT da qanday saqlanadi?

```
Asl son: 0.823

INT8 ga o'tkazish:
1. Ko'paytirish: 0.823 × 127 = 104.5 ≈ 105  ← butun son
2. Saqlash:      105  ← INT8 da saqlanadi

Qayta o'qish:
105 ÷ 127 = 0.826  ← taxminiy qaytadi
```

---

## 1 milliard parametr uchun xotira

```
FP32 → 4 bayt × 1B = 4,000 MB = ~4 GB
FP16 → 2 bayt × 1B = 2,000 MB = ~2 GB
INT8 → 1 bayt × 1B = 1,000 MB = ~1 GB
INT4 → 0.5 bayt × 1B = 500 MB = ~0.5 GB
```

```
FP32: [████████████████████████████████] 4 GB
FP16: [████████████████] 2 GB
INT8: [████████] 1 GB
INT4: [████] 500 MB ✅
```

---

## GGUF format nima?

```
GGUF = fayl formati (konteyner)
     = modelni saqlash usuli

Xuddi ZIP kabi:
ZIP ichida har xil fayl bo'lishi mumkin
GGUF ichida ham har xil quantization bo'lishi mumkin
```

### GGUF variantlari

```
gemma3-1b.Q2_K.gguf  → INT2  (eng kichik, past sifat)
gemma3-1b.Q4_K_M.gguf → INT4  (balans) ← bizniki
gemma3-1b.Q5_K.gguf  → INT5  (yaxshiroq sifat)
gemma3-1b.Q8_0.gguf  → INT8  (yuqori sifat)
gemma3-1b.F16.gguf   → FP16  (eng aniq, katta)
```

### Q4_K_M nima degani?

```
Q   → Quantization (siqilgan)
4   → 4 bit (INT4)
K   → K-quants (yangi, yaxshiroq siqish algoritmi)
M   → Medium (o'rta sifat)

Variantlar:
Q4_K_S → Small  (kichikroq, past sifat)
Q4_K_M → Medium (balans) ← bizniki ✅
Q4_K_L → Large  (kattaroq, yuqori sifat)
```

---

## Modelni tekshirish

```bash
ollama show gemma3:1b
```

```
quantization    Q4_K_M  ← INT4 ekanligini bildiradi
parameters      999.89M ← ~1 milliard parametr
context length  32768   ← bir vaqtda 32768 token
embedding       1152    ← vektor hajmi
```

---

## INT8 modelni yuklash

```bash
ollama pull gemma3:1b-it-q8_0
```

```
gemma3:1b           → Q4_K_M → INT4 → 815 MB
gemma3:1b-it-q8_0   → Q8_0   → INT8 → 1.1 GB
```

---

## benchmark_quant.py — to'liq kod

```python
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

            # Birinchi token → TTFT
            if chunk.get("response") and first_token_time is None:
                first_token_time = time.perf_counter() - start

            # Oxirgi qator → tok/s
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

            print(f"{model:<28} {quant:>12} {size:>8} "
                  f"{avg_ttft:>8.2f} {avg_tps:>8.1f}")

    print(f"{'='*70}")
    print(f"Har bir model: {len(PROMPTS)} prompt x {RUNS} run = "
          f"{len(PROMPTS)*RUNS} o'lchov\n")


if __name__ == "__main__":
    asyncio.run(run())
```

---

## Natijalar

```
======================================================================
Model                        Quant      Hajm     TTFT    Tok/s
======================================================================
gemma3:1b             INT4 (Q4_K_M)   815 MB     0.42    106.7
gemma3:1b-it-q8_0      INT8 (Q8_0)   1.1 GB     0.40     80.5
======================================================================
```

---

## Sifat taqqoslash

```bash
ollama run gemma3:1b "O'zbekiston poytaxti qaysi?"
# → "Toshkent (O'zbek Buxar)dir" ← noto'g'ri! 😅

ollama run gemma3:1b-it-q8_0 "O'zbekiston poytaxti qaysi?"
# → "Toshkent." ← to'g'ri, aniq ✅
```

---

## Natijalar tahlili

| Model | Quant | Hajm | TTFT | Tok/s | Sifat |
|-------|-------|------|------|-------|-------|
| gemma3:1b | INT4 | 815 MB | 0.42s | **106.7** | ⚠️ ba'zan xato |
| gemma3:1b-it-q8_0 | INT8 | 1.1 GB | **0.40s** | 80.5 | ✅ aniq |

### Nima uchun INT4 tezroq?

```
INT4 → 815 MB → VRAM ga to'liq sig'adi → GPU tez ishlaydi ✅
INT8 → 1.1 GB → ko'proq VRAM → GPU sekinroq ishlaydi

Paradoks:
→ Kam aniqlik = tezroq ✅
→ Ko'p aniqlik = sekinroq
```

---

## Qaysi birini tanlash kerak?

```
Tezlik muhim, sifat o'rtacha yetarli:
→ INT4 (Q4_K_M) ✅

Sifat muhim, tezlik ikkinchi:
→ INT8 (Q8_0) ✅

Bizning loyiha:
→ RAG tizimi  → INT8 yaxshiroq (hujjatdan aniq javob kerak)
→ Oddiy chat  → INT4 yetarli
```

---

## Xulosa

```
Quantization = model sonlarini siqish

Ko'p bit → aniq → katta xotira → sekin
Kam bit  → taxminiy → kichik xotira → tez

INT4 (Q4_K_M):  tez, kichik, ba'zan xato
INT8 (Q8_0):    sekin, katta, aniq

GGUF = faqat format (konteyner)
       ichida INT2 dan FP16 gacha bo'lishi mumkin

Bizning holat (4GB VRAM):
→ INT4 → 815 MB → GPU da ishlaydi ✅
→ INT8 → 1.1 GB → GPU da ishlaydi ✅
→ FP32 → 4 GB   → sig'maydi ❌
```