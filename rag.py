"""
Phase 1 – RAG in one script ("Ask the Docs")

Run:
    pip install google-genai chromadb pypdf
    export GEMINI_API_KEY="your-key"
    python rag_phase1.py handbook.pdf

First run reads the PDF and builds the database (steps 1-3).
Then you can ask questions in a loop (steps 4-5). Type 'exit' to quit.
"""
import os
from dotenv import load_dotenv
load_dotenv()   # reads .env into environment variables
import sys

import chromadb                  # vector database: stores embeddings and finds the closest ones
from pypdf import PdfReader      # reads text out of PDF files
from google import genai         # official Gemini SDK: embeddings + answers

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])  # key from env var, never hard-coded
EMBED_MODEL = "gemini-embedding-001"   # turns text into a list of numbers (meaning-map position)
CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")

db = chromadb.PersistentClient(path="chroma_db")              # saves to disk, so no rebuild each run
collection = db.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})  # cosine = "closeness by meaning"


# STEP 1 – CHUNKING: split each page into small overlapping pieces.
# Overlap stops a sentence that sits on a cut from being lost.
def load_chunks(path, size=800, overlap=150):
    chunks = []
    for page_no, page in enumerate(PdfReader(path).pages, start=1):
        text = (page.extract_text() or "").replace("\n", " ")
        for start in range(0, len(text), size - overlap):
            piece = text[start:start + size].strip()
            if len(piece) > 50:                       # skip tiny scraps
                chunks.append({"text": piece, "page": page_no})
    return chunks


# STEP 2 – EMBEDDING: send text to Gemini, get back one vector per text.
# Done in batches of 100 because the API limits how many texts per call.
def embed(texts):
    vectors = []
    for i in range(0, len(texts), 100):
        res = client.models.embed_content(model=EMBED_MODEL, contents=texts[i:i + 100])
        vectors.extend(e.values for e in res.embeddings)
    return vectors


# STEP 3 – STORING: save text + vector + page number in ChromaDB.
def build_index(pdf_path):
    chunks = load_chunks(pdf_path)
    print(f"Split into {len(chunks)} chunks. Embedding...")
    collection.upsert(
        ids=[f"{os.path.basename(pdf_path)}-{i}" for i in range(len(chunks))],
        documents=[c["text"] for c in chunks],
        embeddings=embed([c["text"] for c in chunks]),
        metadatas=[{"page": c["page"]} for c in chunks],   # metadata = extra info we get back later
    )
    print("Index built.")


# STEP 4 – RETRIEVAL: embed the question and fetch the 4 closest chunks.
# STEP 5 – GENERATION: give Gemini only those chunks + strict instructions.
def ask(question, k=4):
    q_vec = embed([question])[0]
    hits = collection.query(query_embeddings=[q_vec], n_results=k)
    docs, metas = hits["documents"][0], hits["metadatas"][0]

    context = "\n\n".join(f"[Page {m['page']}] {d}" for d, m in zip(docs, metas))
    prompt = (
        "Answer the question using ONLY the context below. "
        "The context may use different words than the question (for example 'paid time off' for 'holidays'), so match by meaning. "
        "Cite the page numbers you used, like (Page 3). "
        "If the question is ambiguous, answer with the closest matching information in the context and briefly say what the documents do not cover. "
        "Only if nothing in the context is relevant, reply exactly: I don't know based on the documents.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION: {question}"
    )
    answer = client.models.generate_content(model=CHAT_MODEL, contents=prompt).text
    return answer, sorted({m["page"] for m in metas})
