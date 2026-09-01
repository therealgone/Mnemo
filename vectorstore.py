# Shared resources + ingestion (write path).
# Every other module imports its `vectorstore`/`llm`/`chunks` from here rather than
# constructing its own, so there's exactly one embedding model and one Chroma connection
# for the whole app.

import os
from datetime import datetime

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM

from config import (
    MEMORY_PATH,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
)

# SBERT embedding model, runs locally, no external API calls.
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Chroma is opened once here and reused everywhere. One collection for all
# memories (categories are metadata, not separate collections).
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_PATH,
)

# Local generation model via Ollama, used for rewriting, answering, and editing.
llm = OllamaLLM(model=LLM_MODEL)

# Splits raw notes into small chunks before embedding. chunk_size is deliberately
# small (100) so each chunk stays close to one atomic fact/memory.
splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=100,
    chunk_overlap=0,
)

# Load + chunk memory.txt once at import time. `chunks` is reused by retrieval.py
# to build the BM25 retriever, so it needs to exist before any search happens.
loader = TextLoader(file_path=MEMORY_PATH)
docs = loader.load()
chunks = splitter.split_documents(docs)


def save_memory(chunk, path, i):
    # Deterministic id from filename + chunk index, e.g. "memory.txt_3".
    # Lets file-based ingestion be re-run without duplicating chunks (same id = overwrite).
    chunk_id = f"{os.path.basename(path)}_{i}"
    chunk.metadata["id"] = chunk_id
    chunk.metadata["Date-Time"] = datetime.now().isoformat()
    chunk.metadata["last_edited"] = ""   # populated later by memory_ops.memory_edit
    chunk.metadata["edit_trail"] = ""    # cascade-summarized edit history goes here

    vectorstore.add_documents([chunk], ids=[chunk_id])
    print(f"Stored chunk {i} in Chroma with id={chunk_id!r}")


def ingest(path=MEMORY_PATH):
    # One-shot bulk ingestion of memory.txt into Chroma.
    # Run this manually when you want to (re)load the file into the vector store.
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i} ---")
        print(chunk.page_content)
        print()
        save_memory(chunk, path, i)
