# Central place for paths/constants so no other file has hardcoded strings.
# LLM model + Ollama host are now user-configurable at runtime, persisted via
# settings.py, not hardcoded here — see settings.py for that.

import sys
from pathlib import Path

# Per-user writable app data dir, not tied to wherever the app is installed —
# same pattern as settings.py's SETTINGS_DIR, since an installed app's own
# directory (e.g. Program Files) usually isn't writable without admin rights.
APP_DATA_DIR = Path.home() / ".brain-rag"

MEMORY_PATH = str(APP_DATA_DIR / "memory.txt")      # optional bulk-ingest source file, see vectorstore.ingest()
CHROMA_DB_PATH = str(APP_DATA_DIR / "chroma_db")    # on-disk Chroma persistence directory
COLLECTION_NAME = "memories"                                        # single collection for everything (see ARCHITECTURE.md)

# Resolves to the PyInstaller bundle dir when frozen (sys._MEIPASS), or the
# project root when running from source — either way, models/all-MiniLM-L6-v2
# sits alongside this file.
_BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

# SBERT model used to embed chunks/queries — kept fixed, not user-configurable
# (swapping it would invalidate existing embeddings with no migration path).
# Points at a bundled local copy of the model (models/all-MiniLM-L6-v2), not
# the "all-MiniLM-L6-v2" Hub id — sentence-transformers loads straight off
# disk when given a local directory, no network call at all. This used to
# resolve via a one-time download from huggingface.co on first run (still
# documented in setup.txt for a from-source dev setup), but a packaged Store
# build can't rely on that: Microsoft's certification machines sit behind a
# locked-down network that blocks huggingface.co even with general internet
# access, which made the app fail to launch during certification.
EMBEDDING_MODEL = str(_BASE_DIR / "models" / "all-MiniLM-L6-v2")
