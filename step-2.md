# Bosqich 2 — Ollama + FastAPI: Birinchi Chat

---

## Nima qildik?

```
Ollama (port 11434)     ←httpx→     FastAPI (port 8000)
  └── gemma3:1b                       └── POST /chat
```

---

## 1. Kutubxonalar o'rnatish

```bash
pip install fastapi uvicorn httpx
```

| Kutubxona | Nima qiladi | Django analog |
|-----------|-------------|---------------|
| `fastapi` | Web framework | Django |
| `uvicorn` | Server | `manage.py runserver` |
| `httpx` | HTTP so'rov | `requests` (async versiyasi) |

---

## 2. FastAPI nima?

```python
# Django da:
from django.http import JsonResponse
# urls.py → views.py → 2 ta fayl

# FastAPI da:
from fastapi import FastAPI
app = FastAPI()
# 1 ta fayl, 1 qator — hammasi shu yerda
```

FastAPI Django dan farqi:

```
Django:
→ urls.py + views.py + settings.py
→ sekin, ko'p fayl
→ sync (ketma-ket)

FastAPI:
→ 1 ta main.py
→ tez, kam kod
→ async (bir vaqtda ko'p so'rov) ✅
```

---

## 3. Uvicorn nima?

```bash
uvicorn main:app --reload
```

```
main     → main.py fayli
app      → main.py dagi app = FastAPI()
--reload → kod o'zgarganda avtomatik qayta yuklash
           (Django --reload kabi)
```

Django bilan taqqoslash:

```
Django:   python manage.py runserver
FastAPI:  uvicorn main:app --reload
```

---

## 4. Pydantic — BaseModel nima?

```python
class ChatRequest(BaseModel):
    prompt: str
    model: str = DEFAULT_MODEL

class ChatResponse(BaseModel):
    model: str
    response: str
```

Django bilan taqqoslash:

```python
# Django REST Serializer:
class ChatSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    model  = serializers.CharField(default="gemma4:e4b")

# FastAPI BaseModel:
class ChatRequest(BaseModel):
    prompt: str
    model: str = DEFAULT_MODEL  # default qiymat
```

Pydantic nima qiladi?

```
Foydalanuvchi yubordi:
{"prompt": "Salom", "model": "gemma3:1b"}
        ↓
Pydantic tekshiradi:
→ prompt bor?    ✅
→ prompt str mi? ✅
→ model bor?     ✅
→ ChatRequest obyekti yaratildi ✅

Noto'g'ri yuborilsa:
{"prompt": 12345}  ← str emas, int!
        ↓
Pydantic: 422 Validation Error ← avtomatik! ✅
```

---

## 5. httpx nima?

```python
async with httpx.AsyncClient(timeout=120.0) as client:
    r = await client.post(OLLAMA_URL, json=payload)
    r.raise_for_status()
    data = r.json()
```

Django bilan taqqoslash:

```python
# Django da (requests):
import requests
r = requests.post(OLLAMA_URL, json=payload)
data = r.json()

# FastAPI da (httpx):
async with httpx.AsyncClient() as client:
    r = await client.post(OLLAMA_URL, json=payload)
    data = r.json()
```

Nima farq?

```
requests → sync  → 1 so'rov, kutadi, keyin keyingisi
httpx    → async → ko'p so'rov bir vaqtda ✅

async with → ishlatib bo'lgach avtomatik yopiladi
timeout=120 → 120 sekundda javob kelmasa → xato
raise_for_status → 404/500 bo'lsa → xato chiqaradi
```

---

## 6. async/await nima?

```python
async def chat(req: ChatRequest):
    async with httpx.AsyncClient() as client:
        r = await client.post(...)
```

Oddiy misol:

```python
# sync (oddiy):
def ovqat_buyurtma():
    natija = oshpazga_bor()   # oshpaz pishirguncha KUTADI 😤
    return natija              # boshqa ish qila olmaydi

# async:
async def ovqat_buyurtma():
    natija = await oshpazga_bor()  # oshpaz pishirayotganda
    return natija                   # BOSHQA ISH QILADI ✅
```

FastAPI da:

```
Foydalanuvchi 1 so'rov yubordi
→ Ollama ga so'rov ketdi (2 sekund kutish)
→ Kutayotganda Foydalanuvchi 2 so'rovi qabul qilindi ✅
→ Ikkalasi parallel ishlaydi

sync bo'lsa:
→ Foydalanuvchi 1 tugaguncha Foydalanuvchi 2 kutadi 😤
```

---

## 7. To'liq main.py — izohlar bilan

```python
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

# App yaratish
app = FastAPI(title="POC-023 LLM Inference")

# Ollama server manzili va default model
OLLAMA_URL    = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma4:e4b"


# Kirish formati (Pydantic)
class ChatRequest(BaseModel):
    prompt: str                    # majburiy
    model: str = DEFAULT_MODEL     # ixtiyoriy, default bor


# Chiqish formati (Pydantic)
class ChatResponse(BaseModel):
    model: str
    response: str


# GET /health — server ishlayaptimi?
@app.get("/health")
async def health():
    return {"status": "ok"}


# POST /chat — asosiy endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    # Ollama ga yuborish uchun payload
    payload = {
        "model":  req.model,   # qaysi model
        "prompt": req.prompt,  # savol
        "stream": False,       # to'liq javob (streaming yo'q)
    }

    # Ollama ga so'rov yuborish
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()   # xato bo'lsa exception
        data = r.json()        # JSON → dict

    # Javob qaytarish
    return ChatResponse(
        model=req.model,
        response=data["response"]  # Ollama javobidan faqat kerakli qism
    )
```

---

## 8. To'liq jarayon

```
Foydalanuvchi:
POST /chat
{"prompt": "Salom"}
        ↓
FastAPI (port 8000):
→ JSON → ChatRequest (Pydantic tekshiradi)
→ payload yaratiladi
→ httpx orqali Ollama ga yuboriladi
        ↓
Ollama (port 11434):
→ gemma3:1b model ishga tushadi
→ "Salom! Men gemma3..." javob beradi
        ↓
FastAPI:
→ data["response"] olinadi
→ ChatResponse yaratiladi
→ JSON qaytariladi
        ↓
Foydalanuvchi:
{
  "model": "gemma3:1b",
  "response": "Salom! Men gemma3..."
}
```

---

## 9. Endpointlarni test qilish

```
http://localhost:8000/docs
```

FastAPI avtomatik **Swagger UI** yaratadi:

```
Django da test uchun: Postman, curl
FastAPI da:           /docs — brauzerda test qilsa bo'ladi ✅
```

---

## Xulosa

```
✅ FastAPI    → Django ga o'xshash, lekin tez va kam kod
✅ Uvicorn    → FastAPI server (manage.py runserver analog)
✅ Pydantic   → kirish/chiqish tekshiruvi (Serializer analog)
✅ httpx      → async HTTP so'rov (requests analog)
✅ async/await → bir vaqtda ko'p foydalanuvchi ✅
✅ /docs      → avtomatik Swagger UI
```