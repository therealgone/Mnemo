# Central place for paths/model names/constants so no other file has hardcoded strings.
# If you move the project or swap models, this is the only file you should need to touch.

MEMORY_PATH = "/home/therealgone/Projects/Brain-Rag/memory.txt"     # source notes file that gets ingested
CHROMA_DB_PATH = "/home/therealgone/Projects/Brain-Rag/chroma_db"   # on-disk Chroma persistence directory
COLLECTION_NAME = "memories"                                        # single collection for everything (see ARCHITECTURE.md)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # SBERT model used to embed chunks/queries
LLM_MODEL = "phi4-mini"               # local Ollama model tag used for generation
