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
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    # 4. ChromaDB ga saqlash
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    return {
        "fayl": file.filename,
        "bolaklar": len(chunks),
        "status": "indekslandi"
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
    prompt  = f"""Quyidagi matn asosida savollga javob ber.
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
        "savol":   savol,
        "javob":   data["response"],
        "manbalar": [b.page_content[:100] + "..." for b in bolaklar]
    }