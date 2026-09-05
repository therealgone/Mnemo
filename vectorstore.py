# Shared resources + ingestion (write path).
# Every other module gets its `vectorstore`/llm/documents from here rather than
# constructing its own, so there's exactly one embedding model and one Chroma
# connection for the whole app.

import os
import uuid
from datetime import datetime

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.documents import Document

from config import (
    MEMORY_PATH,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)
from settings import get_llm_model, get_ollama_host

# SBERT embedding model, runs locally, no external API calls. Kept fixed
# (not user-configurable) — swapping it would silently invalidate every
# embedding already stored in Chroma with no migration path.
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Chroma is opened once here and reused everywhere. One collection for all
# memories (categories are metadata, not separate collections).
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_PATH,
)

# Splits raw notes into small chunks before embedding. chunk_size is deliberately
# small (100) so each chunk stays close to one atomic fact/memory.
splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=100,
    chunk_overlap=0,
)


def get_llm():
    # Built fresh from current settings on every call (instead of a module-level
    # singleton) so a host/model change made in Settings takes effect immediately,
    # with no app restart required. temperature=0 because every use of this
    # (classification, rewriting, candidate selection, answering) is a
    # rules-following task with one correct output, not creative writing —
    # leaving the default (~0.8) sampling temperature made classification and
    # candidate selection noticeably flaky between identical calls. seed is
    # pinned too — temperature=0 alone doesn't make Ollama fully deterministic,
    # a fixed seed does.
    return OllamaLLM(model=get_llm_model(), base_url=get_ollama_host(), temperature=0, seed=42)


def get_all_documents():
    # Pulls whatever's currently stored in Chroma as Document objects. Used by
    # retrieval.py to build the BM25 retriever, so lexical search always reflects
    # the live store instead of a fixed file read once at import time.
    data = vectorstore.get()
    return [
        Document(page_content=doc, metadata=meta, id=id_)
        for id_, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])
    ]


def save_memory(chunk, path, i):
    # Deterministic id from filename + chunk index, e.g. "memory.txt_3".
    # Lets file-based ingestion be re-run without duplicating chunks (same id = overwrite).
    chunk_id = f"{os.path.basename(path)}_{i}"
    chunk.metadata["id"] = chunk_id
    chunk.metadata["Date-Time"] = datetime.now().isoformat()
    chunk.metadata["last_edited"] = ""   # populated later by memory_ops.memory_edit
    chunk.metadata["edit_trail"] = ""    # cascade-summarized edit history goes here

    vectorstore.add_documents([chunk], ids=[chunk_id])
    return chunk_id


def save_memory_chat(chunk):
    # Same idea as save_memory, but for memories with no source file/index to
    # derive a deterministic id from (chat turns, pasted text, uploads) — uses
    # a random uuid instead.
    chunk.metadata["Date-Time"] = datetime.now().isoformat()
    chunk.metadata["last_edited"] = ""
    chunk.metadata["edit_trail"] = ""

    chunk_id = str(uuid.uuid4())
    vectorstore.add_documents([chunk], ids=[chunk_id])
    return chunk_id


def ingest_text(text, source_name="pasted"):
    # Generic ingestion entry point for the Upload panel — used for both pasted
    # text and uploaded .txt files (the frontend reads the file client-side and
    # sends its text straight through, no temp files on disk needed). Runs through
    # the same splitter + save path as everything else, just with a fresh id per
    # chunk rather than a file-index-based one.
    count = 0
    for piece in splitter.split_text(text):
        if not piece.strip():
            continue
        doc = Document(page_content=piece, metadata={"source": source_name})
        save_memory_chat(doc)
        count += 1
    return count


def ingest(path=MEMORY_PATH):
    # One-shot bulk ingestion of a local .txt file into Chroma. Kept for manual/
    # legacy use (e.g. re-ingesting memory.txt); the Upload panel uses
    # ingest_text() instead since it works on in-memory text, not a filesystem path.
    loader = TextLoader(file_path=path)
    docs = loader.load()
    file_chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(file_chunks):
        save_memory(chunk, path, i)
    return len(file_chunks)


def delete_memory(memory_id):
    vectorstore.delete(ids=[memory_id])


def display_memory():
    data = vectorstore.get()

    combined = [
        {
            "id": id_,
            "text": doc,
            "date": meta.get("Date-Time", ""),
            "last_edited": meta.get("last_edited", ""),
            "edit_trail": meta.get("edit_trail", "")
        }
        for id_, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])
    ]

    # sort by date, oldest to newest
    combined.sort(key=lambda x: x["date"])
    return combined
