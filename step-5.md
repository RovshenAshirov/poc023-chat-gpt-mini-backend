# Bosqich 5 — RAG tizimi

---

## RAG nima?

**RAG = Retrieval Augmented Generation**
**= Qidirish + Kuchaytirish + Generatsiya**

### Muammo — LLM hamma narsani bilmaydi

```
LLM o'qitilgan: 2024 yilgacha internet ma'lumotlari

Savol: "Bizning kompaniyaning 2025 yilgi hisoboti nima deydi?"
LLM:   "Bilmayman" ❌

Savol: "Shu PDF dagi 5-bandni tushuntir"
LLM:   "PDF ni ko'rmadim" ❌
```

### RAG yechimi

```
Oddiy LLM:
Savol → LLM → Javob
         ↑
    faqat o'qitish ma'lumotlari

RAG bilan:
Savol → Qidiruv → Mos bo'laklar → LLM → Javob
                        ↑
                  bizning hujjatlar
                  (PDF, TXT, Word)
```

---

## Indekslash nima?

**Indekslash = hujjatni qidirishga tayyor holga keltirish**

```
Indekssiz:
"Toshkent" qidirmoqchisiz
→ 500 sahifani birma-bir o'qisiz 😤

Indeksli:
"Toshkent" → 45, 123, 287-sahifalar ✅
→ To'g'ridan-to'g'ri o'sha sahifaga borasiz
```

---

## ChromaDB nima?

**ChromaDB = vektorlarni saqlash va qidirish uchun maxsus baza**

```
PostgreSQL (oddiy baza):
→ Matn, son saqlaydi
→ Aniq moslik qidiradi: WHERE text LIKE '%32-modda%'
→ "Fuqarolar huquqi" → topmaydi ❌

ChromaDB (vektor baza):
→ Vektorlar saqlaydi
→ Ma'no bo'yicha qidiradi
→ "Fuqarolar huquqi" → "32-modda..." topadi ✅
```

### Vektor o'xshashlik

```
"32-modda. Fuqarolar..."  → [0.67, -0.12, 0.88, ...]
"Fuqarolar huquqlari..."  → [0.65, -0.11, 0.87, ...]  ← o'xshash!
"Avtomobil narxi..."      → [0.12,  0.89, -0.34, ...]  ← boshqa!

Savol: "32-modda nima?"   → [0.66, -0.11, 0.88, ...]

ChromaDB:
"32-modda..."    → 99% o'xshash ← topildi ✅
"Avtomobil..."   → 12% o'xshash ← o'tkazib yuborildi
```

---

## RAG Pipeline — 2 qism

### Qism 1 — Indekslash (1 marta)

```
PDF/TXT fayl
    ↓ (1-qadam: o'qish — pypdf/TextLoader)
Matn: "1-modda. O'zbekiston..."
    ↓ (2-qadam: bo'lish — RecursiveCharacterTextSplitter)
Bo'laklar: ["1-modda...", "2-modda...", ...]
    ↓ (3-qadam: vektorlashtirish — sentence-transformers)
Vektorlar: [[0.23, -0.87...], [0.11, 0.34...], ...]
    ↓ (4-qadam: saqlash — ChromaDB)
./chroma_db ← diskka yozildi ✅
```

### Qism 2 — Qidirish (har savol uchun)

```
Savol: "32-modda nima?"
    ↓ (1-qadam: vektorlashtirish)
[0.66, -0.11, 0.88, ...]
    ↓ (2-qadam: ChromaDB qidirish)
Eng mos 3 bo'lak
    ↓ (3-qadam: prompt yaratish)
"Shu matn asosida javob ber:
 [bo'laklar]
 Savol: 32-modda nima?"
    ↓ (4-qadam: LLM)
Javob ✅
```

### Nima uchun pipeline kerak?

```
Pipelinesiz:
→ Har savol uchun PDF qayta o'qiladi
→ Har savol uchun qayta bo'linadi
→ Juda sekin! 😤

Pipeline bilan:
→ PDF 1 marta indekslanadi
→ Savol keldi → ChromaDB dan darhol qidiradi ✅
```

---

## LangChain nima?

**LangChain = RAG pipeline ni boshqaruvchi framework**

```
Django:
→ Web dastur uchun framework
→ Routing, template, ORM — tayyor ✅

LangChain:
→ RAG uchun framework
→ PDF o'qish, bo'lish, qidirish, LLM — tayyor ✅
```

### LangChain ichida nima bor?

```
├── Document Loaders  → PDF, TXT o'qish
├── Text Splitters    → bo'laklarga bo'lish
├── Embeddings        → vektorga aylantirish
├── Vector Stores     → ChromaDB bilan ishlash
├── LLMs              → Ollama bilan ishlash
└── Chains            → barchasini birlashtirish
```

---

## Kutubxonalar

```
pypdf                  → PDF fayldan matn o'qish
langchain              → RAG pipeline framework
langchain-community    → PDF loader, Chroma, Ollama
langchain-text-splitters → bo'laklarga bo'lish
sentence-transformers  → matnni vektorga aylantirish (lokal)
chromadb               → vektorlar bazasi
```

O'rnatish:

```bash
pip install langchain langchain-community \
            langchain-text-splitters \
            chromadb sentence-transformers pypdf
```

---

## rag.py — to'liq kod va izohlar

```python
import os
from pathlib import Path

from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
import httpx

# Papkalar
UPLOAD_DIR = Path("uploads")
CHROMA_DIR = "./chroma_db"
UPLOAD_DIR.mkdir(exist_ok=True)

# Embedding modeli (lokal, token shart emas)
embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)


async def index_document(file: UploadFile) -> dict:
    """Hujjatni yuklash va indekslash"""

    # 1. Faylni saqlash
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 2. PDF yoki TXT o'qish
    if file.filename.endswith(".pdf"):
        loader = PyPDFLoader(str(file_path))
    else:
        loader = TextLoader(str(file_path))

    documents = loader.load()

    # 3. Bo'laklarga bo'lish
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,    # har bo'lak 500 ta belgi
        chunk_overlap=50   # 50 belgi qoplashtiradi
    )
    chunks = splitter.split_documents(documents)

    # 4. ChromaDB ga saqlash
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    return {
        "fayl":    file.filename,
        "bolaklar": len(chunks),
        "status":  "indekslandi"
    }


async def query_document(savol: str) -> dict:
    """Hujjat bo'yicha savol"""

    # 1. ChromaDB dan yuklash
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    # 2. Eng mos 3 bo'lakni topish
    bolaklar = vectorstore.similarity_search(savol, k=3)

    if not bolaklar:
        return {"javob": "Hujjat topilmadi"}

    # 3. Prompt yaratish
    context = "\n\n".join([b.page_content for b in bolaklar])
    prompt  = f"""Quyidagi matn asosida savolga javob ber.
Faqat berilgan matn asosida javob ber, o'zingdan qo'shma.

Matn:
{context}

Savol: {savol}
Javob:"""

    # 4. Ollama ga yuborish
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model":  "gemma3:1b",
                "prompt": prompt,
                "stream": False
            }
        )
        data = r.json()

    return {
        "savol":    savol,
        "javob":    data["response"],
        "manbalar": [b.page_content[:100] + "..." for b in bolaklar]
    }
```

---

## main.py ga qo'shish

```python
from fastapi import UploadFile, File
from rag import index_document, query_document


@app.post("/rag/upload")
async def rag_upload(file: UploadFile = File(...)):
    return await index_document(file)


@app.post("/rag/query")
async def rag_query(savol: str):
    return await query_document(savol)
```

---

## Test

### 1. Test fayl yaratish

```bash
cat > ~/poc023-app/test.txt << 'EOF'
O'zbekiston Respublikasi Markaziy Osiyoda joylashgan davlat.
Poytaxti Toshkent shahri hisoblanadi.
Toshkent O'zbekistonning eng yirik shahri va iqtisodiy markazi.
Aholisi 36 million nafardan ortiq.
Rasmiy tili o'zbek tili hisoblanadi.
Mustaqillik 1991 yil 1 sentyabrda e'lon qilingan.
Pul birligi so'm hisoblanadi.
EOF
```

### 2. Faylni yuklash

```bash
curl -X POST http://localhost:8000/rag/upload \
  -F "file=@/home/rovshen/poc023-app/test.txt"
```

Natija:

```json
{
  "fayl": "test.txt",
  "bolaklar": 1,
  "status": "indekslandi"
}
```

### 3. Savol berish

```bash
curl -X POST "http://localhost:8000/rag/query?savol=O'zbekiston poytaxti qaysi shahar?"
```

Natija:

```json
{
  "savol": "O'zbekiston poytaxti qaysi shahar",
  "javob": "Poytaxti Toshkent shahri hisoblanadi.",
  "manbalar": [
    "O'zbekiston Respublikasi Markaziy Osiyoda..."
  ]
}
```

---

## To'liq jarayon

```
POST /rag/upload → test.txt yuklandi
        ↓
LangChain: matn o'qildi
        ↓
Bo'laklarga bo'lindi: 1 bo'lak
        ↓
sentence-transformers: vektorga aylandi
        ↓
ChromaDB: ./chroma_db ga saqlanadi
        ↓
POST /rag/query → "poytaxti qaysi shahar?"
        ↓
sentence-transformers: savol vektorga aylandi
        ↓
ChromaDB: eng mos bo'lak topildi
        ↓
Prompt: "Shu matn asosida javob ber..."
        ↓
gemma3:1b: "Poytaxti Toshkent shahri hisoblanadi." ✅
```

---

## Arxitektura

```
┌─────────────────────────────────────────────────┐
│  FastAPI                                        │
│  ├── POST /rag/upload → index_document()        │
│  └── POST /rag/query  → query_document()        │
└─────────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────────┐
│  LangChain                                      │
│  ├── PyPDFLoader / TextLoader  → o'qish         │
│  ├── RecursiveCharacterTextSplitter → bo'lish   │
│  ├── SentenceTransformerEmbeddings → vektor     │
│  └── Chroma → saqlash / qidirish                │
└─────────────────────────────────────────────────┘
                    ↕
┌──────────────────┐    ┌───────────────────────┐
│  ChromaDB        │    │  Ollama               │
│  ./chroma_db     │    │  gemma3:1b            │
│  (vektorlar)     │    │  port 11434           │
└──────────────────┘    └───────────────────────┘
```

---

## Xulosa

```
RAG = hujjatlar + LLM birlashuvi

Indekslash (1 marta):
PDF/TXT → bo'laklar → vektorlar → ChromaDB ✅

Qidirish (har savol):
Savol → vektor → ChromaDB → bo'laklar → LLM → javob ✅

Natija:
→ LLM bizning hujjatlar asosida javob beradi ✅
→ Ma'lumotlar tashqariga chiqmaydi ✅
→ Har qanday PDF, TXT ishlaydi ✅
```
