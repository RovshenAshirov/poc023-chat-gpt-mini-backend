

# Muhitni sozlash

## 1. Tizimni tekshirish

```bash
nvidia-smi && python3 --version && df -h ~
```

### Natija tahlili

| Parametr | Holat |
|----------|-------|
| GPU | RTX 2050 |
| VRAM | 4 GB ⚠️ |
| CUDA | 13.0 ✅ |
| Python | 3.12.3 ✅ |
| Disk | 348 GB bo'sh ✅ |

> ⚠️ **Diqqat:** VRAM 4 GB — katta modellar (7B+) sig'maydi.
> Faqat kichik modellar (1B–3B) GPU da ishlaydi.

---

## 2. Virtual muhit yaratish

```bash
mkdir ~/poc023-app && cd ~/poc023-app
python3 -m venv venv
source venv/bin/activate
```

Aktivlashgandan keyin terminalda `(venv)` ko'rinadi:

```
(venv) rovshen@rovshen:~/poc023-app$
```

---

## 3. Ollama o'rnatish

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

O'rnatilganini tekshirish:

```bash
ollama --version
# ollama version is 0.21.0
```

---

## 4. Model yuklash

### gemma3:1b — asosiy model (GPU da ishlaydi)

```bash
ollama pull gemma3:1b
```

| Model | Hajm | VRAM | Qurilma |
|-------|------|------|---------|
| gemma3:1b | 778 MB | ~1 GB | GPU ✅ |
| gemma4:e4b | 9.6 GB | 9.6 GB | CPU ⚠️ (sig'maydi) |

---

## 5. Model ishlayaptimi?

```bash
ollama run gemma3:1b "Salom, kim san?"
```

---

## 6. Yuklangan modellarni ko'rish

```bash
ollama list
```

```
NAME           ID              SIZE      MODIFIED
gemma3:1b      7cd4618c1faf    778 MB    1 hour ago
gemma4:e4b     c6eb396dbd59    9.6 GB    4 hours ago
llama3.2:3b    a80c4f17acd5    2.0 GB    4 hours ago
```

---

## Xulosa

```
✅ CUDA 13.0    — GPU ishlaydi
✅ Python 3.12  — tayyor
✅ Ollama 0.21  — o'rnatildi
✅ gemma3:1b    — GPU da ishlaydi (778 MB)
⚠️ gemma4:e4b  — CPU da ishlaydi (9.6 GB sig'maydi)
```