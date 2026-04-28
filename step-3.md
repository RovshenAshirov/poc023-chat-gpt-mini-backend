# Bosqich 3 — Streaming (SSE) + Chat UI

---

## Nima qildik?

```
Bosqich 2:  POST /chat        → to'liq javob (kutib turadi) 😤
Bosqich 3:  POST /chat/stream → token-by-token (SSE)        🚀
```

Qo'shgan narsalar:
```
1. /chat/stream endpoint  → streaming javob
2. static/index.html      → mini chat UI
3. /                      → bosh sahifa
```

---

## 1. SSE nima?

**SSE = Server-Sent Events**

### Oddiy HTTP:
```
Foydalanuvchi → so'rov → Server
Foydalanuvchi ← javob  ← Server  (hammasi birdan, 30 sekund kutish)
☠️ ulanish yopiladi
```

### SSE:
```
Foydalanuvchi → so'rov  → Server
Foydalanuvchi ← token   ← Server  (darhol!)
Foydalanuvchi ← token   ← Server
Foydalanuvchi ← token   ← Server
Foydalanuvchi ← [DONE]  ← Server
☠️ ulanish yopiladi
```

### SSE formati:
```
data: {"token": "Toshkent"}\n\n
data: {"token": " haqida"}\n\n
data: {"token": " ayt"}\n\n
data: [DONE]\n\n
```

Qoidalar:
```
1. Har xabar "data: " bilan boshlanadi
2. Oxirida 2 ta yangi qator "\n\n"
3. [DONE] — tugadi belgisi
```

---

## 2. SSE vs WebSocket

```
SSE:
→ Bir tomonlama (server → client)
→ Oddiy HTTP
→ Chat streaming uchun yetarli ✅

WebSocket:
→ Ikki tomonlama (server ↔ client)
→ Murakkabrok
→ O'yin, video call uchun kerak

Chat uchun:
→ Foydalanuvchi savol yuboradi (HTTP POST)
→ Server tokenlar yuboradi (SSE)
→ Ikki tomonlama kerak emas → SSE yetarli ✅
```

---

## 2. OpenAI-compatible API nima?

OpenAI o'zining API si uchun **standart format** yaratdi.
Bu format shu qadar mashhur bo'ldiki — butun dunyo ishlatadigan bo'ldi.

### Bizning format (Bosqich 2):
```json
POST /chat
{
    "prompt": "Salom",
    "model": "gemma3:4b"
}
```

### OpenAI formati:
```json
POST /v1/chat/completions
{
    "model": "gpt-4",
    "messages": [
        {"role": "system",    "content": "Sen yordamchisan"},
        {"role": "user",      "content": "Salom"},
        {"role": "assistant", "content": "Salom!"},
        {"role": "user",      "content": "Toshkent haqida ayt"}
    ]
}
```

### Farq:
```
Bizniki:   "prompt" → faqat 1 ta savol
OpenAI:    "messages" → butun suhbat tarixi
                        role: system    → modelga ko'rsatma
                        role: user      → foydalanuvchi
                        role: assistant → model javob
```

### Nega POC da ishlatmadik?
```
Bosqich 2: oddiy /chat       → Ollama tushundik
Bosqich 3: /chat/stream      → SSE tushundik
Bosqich 4: vLLM o'zi beradi  → openai.api_server moduli ✅
```

---

## 3. /chat/stream kodi — izohlar bilan

```python
from fastapi.responses import StreamingResponse
import json

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):

    # Ollama ga yuborish uchun payload
    # stream: True → Ollama token-by-token yuboradi
    payload = {
        "model":  req.model,
        "prompt": req.prompt,
        "stream": True,        # ← Bosqich 2 da False edi!
    }

    # generate() — ichki funksiya
    # yield ishlatadi → har token kelganda darhol yuboradi
    async def generate():
        async with httpx.AsyncClient(timeout=120.0) as client:

            # client.stream → Ollama dan stream ochadi
            async with client.stream("POST", OLLAMA_URL, json=payload) as r:
                r.raise_for_status()

                # Har qatorni birma-bir o'qiydi
                async for line in r.aiter_lines():
                    if not line:
                        continue          # bo'sh qatorni o'tkazib yuboradi

                    chunk = json.loads(line)           # JSON → dict
                    token = chunk.get("response", "")  # token ajratish

                    if token:
                        # SSE format: "data: {...}\n\n"
                        yield f"data: {json.dumps({'token': token})}\n\n"

                    if chunk.get("done"):
                        # Tugash belgisi
                        yield "data: [DONE]\n\n"

    # StreamingResponse → har yield da darhol yuboradi
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### yield nima?

```python
# oddiy return:
def funksiya():
    return "natija"    # 1 ta natija, tugadi

# yield:
async def generate():
    yield "token1"     # 1-natija → yuborildi
    yield "token2"     # 2-natija → yuborildi
    yield "token3"     # 3-natija → yuborildi
                       # tugaguncha ishlaydi ✅
```

### Bosqich 2 vs Bosqich 3 farqi:

```
Bosqich 2:
client.post(...)      → hammasi kelguncha kutadi
return ChatResponse() → 1 ta javob

Bosqich 3:
client.stream(...)    → stream ochiladi
yield token           → har token darhol yuboriladi
StreamingResponse     → yield larni uzatib beradi
```

---

## 4. Ollama dan nima keladi?

```
stream: True bilan Ollama shunday yuboradi:

{"response": "Tosh",    "done": false}
{"response": "kent",    "done": false}
{"response": " haqida", "done": false}
{"response": "",        "done": true}   ← oxirgi qator
```

Bizning kod:

```
line  = '{"response": "Tosh", "done": false}'
         ↓ json.loads
chunk = {"response": "Tosh", "done": False}
         ↓ chunk.get("response")
token = "Tosh"
         ↓ yield
"data: {"token": "Tosh"}\n\n"  → brauzerga ✅
```

---

## 5. main.py ga static va bosh sahifa qo'shish

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

# Static fayllar uchun
app.mount("/static", StaticFiles(directory="static"), name="static")

# Bosh sahifa
@app.get("/")
async def root():
    html = Path("static/index.html").read_text()
    return HTMLResponse(content=html)
```

---

## 6. HTML/JS chat UI — izohlar bilan

```html
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <title>POC-023 Chat</title>
    <style>
        /* Sahifa markazga, max 800px */
        body {
            font-family: sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f5f5f5;
        }

        /* Xabarlar maydoni */
        #messages {
            background: white;
            border-radius: 8px;
            padding: 20px;
            min-height: 300px;
            margin-bottom: 16px;
            border: 1px solid #ddd;
        }

        .user { color: #1a73e8; margin: 8px 0; }
        .bot  { color: #333; margin: 8px 0; white-space: pre-wrap; }
        /* white-space: pre-wrap → yangi qatorlar saqlanadi */

        /* Input va tugma yonma-yon */
        #input-area { display: flex; gap: 8px; }
        #prompt { flex: 1; padding: 10px; border-radius: 6px;
                  border: 1px solid #ddd; font-size: 15px; }

        button { padding: 10px 20px; background: #1a73e8;
                 color: white; border: none; border-radius: 6px;
                 cursor: pointer; font-size: 15px; }
        button:disabled { background: #aaa; }
        /* button:disabled → javob kelguncha tugma kulrang */
    </style>
</head>
<body>
    <h2>🤖 POC-023 — Local LLM Chat</h2>

    <!-- Xabarlar shu yerda ko'rinadi (JS to'ldiradi) -->
    <div id="messages"></div>

    <!-- Savol yozish maydoni -->
    <div id="input-area">
        <input id="prompt" type="text" placeholder="Savol yozing..." />
        <button id="btn" onclick="sendMessage()">Yuborish</button>
    </div>

    <script>
        async function sendMessage() {
            const input    = document.getElementById("prompt");
            const btn      = document.getElementById("btn");
            const messages = document.getElementById("messages");
            const text     = input.value.trim();
            if (!text) return;  // bo'sh bo'lsa hech narsa qilmaydi

            // Foydalanuvchi xabarini ko'rsatish
            messages.innerHTML += `<div class="user">👤 ${text}</div>`;
            input.value  = "";        // inputni tozalash
            btn.disabled = true;      // tugmani o'chirish

            // Bot javobi uchun bo'sh div (tokenlar shu yerga keladi)
            const botDiv = document.createElement("div");
            botDiv.className   = "bot";
            botDiv.textContent = "🤖 ";
            messages.appendChild(botDiv);

            // POST /chat/stream ga so'rov
            const response = await fetch("/chat/stream", {
                method:  "POST",
                headers: {"Content-Type": "application/json"},
                body:    JSON.stringify({prompt: text})
            });

            // SSE oqimini o'qish
            const reader  = response.body.getReader();
            const decoder = new TextDecoder();  // bytes → matn

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;  // stream tugadi

                // bytes → matn
                const chunk = decoder.decode(value);
                // chunk = 'data: {"token":"Tosh"}\n\ndata: {"token":"kent"}\n\n'

                const lines = chunk.split("\n");
                for (const line of lines) {

                    // SSE qatori va [DONE] emas
                    if (line.startsWith("data: ") && line !== "data: [DONE]") {
                        try {
                            // "data: " ni olib tashlash, JSON parse
                            const data = JSON.parse(line.slice(6));

                            // Token → botDiv ga qo'shish
                            botDiv.textContent += data.token;

                            // Yangi token kelganda pastga siljish
                            messages.scrollTop = messages.scrollHeight;
                        } catch {}
                    }
                }
            }

            btn.disabled = false;  // tugmani yoqish
        }

        // Enter bosilganda ham yuborish
        document.getElementById("prompt")
            .addEventListener("keypress", function(e) {
                if (e.key === "Enter") sendMessage();
            });
    </script>
</body>
</html>
```

---

## 7. To'liq jarayon

```
Foydalanuvchi: "Toshkent" yozdi, Enter bosdi
                        ↓
sendMessage() chaqirildi
                        ↓
#messages: 👤 Toshkent qo'shildi
btn o'chirildi
botDiv yaratildi: "🤖 "
                        ↓
fetch → POST /chat/stream → FastAPI
                        ↓
FastAPI: payload → Ollama stream=True
                        ↓
Ollama: token-by-token yuboradi
{"response": "Tosh",    "done": false}
{"response": "kent",    "done": false}
{"response": "...",     "done": true}
                        ↓
FastAPI generate(): yield → SSE
data: {"token":"Tosh"}\n\n
data: {"token":"kent"}\n\n
data: [DONE]\n\n
                        ↓
JS reader: token keldi → botDiv ga qo'shdi
botDiv: "🤖 Tosh" → "🤖 Toshkent" → "🤖 Toshkent..."
                        ↓
[DONE] → while loop tugadi
btn yoqildi ✅
```

---

## 8. Ishga tushirish

```bash
cd ~/poc023-app
source venv/bin/activate
uvicorn main:app --reload
```

Brauzerda:
```
http://localhost:8000/
```

---

## Xulosa

```
✅ SSE          → token-by-token, ChatGPT effekti
✅ StreamingResponse → har yield da darhol yuboradi
✅ yield        → generator funksiyasi
✅ static       → HTML fayllarni serve qilish
✅ /            → bosh sahifa
✅ fetch + reader → JS da SSE o'qish
```