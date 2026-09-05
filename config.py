# Central place for paths/constants so no other file has hardcoded strings.
# LLM model + Ollama host are now user-configurable at runtime, persisted via
# settings.py, not hardcoded here — see settings.py for that.

from pathlib import Path

# Per-user writable app data dir, not tied to wherever the app is installed —
# same pattern as settings.py's SETTINGS_DIR, since an installed app's own
# directory (e.g. Program Files) usually isn't writable without admin rights.
APP_DATA_DIR = Path.home() / ".brain-rag"

MEMORY_PATH = str(APP_DATA_DIR / "memory.txt")      # optional bulk-ingest source file, see vectorstore.ingest()
CHROMA_DB_PATH = str(APP_DATA_DIR / "chroma_db")    # on-disk Chroma persistence directory
COLLECTION_NAME = "memories"                                        # single collection for everything (see ARCHITECTURE.md)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # SBERT model used to embed chunks/queries — kept fixed, not user-configurable (swapping it would invalidate existing embeddings with no migration path)
