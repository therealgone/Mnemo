# User-editable app settings (Ollama host + model), persisted locally so the
# choice survives across sessions instead of being hardcoded in config.py.
# config.py still owns things that are fixed regardless of user/machine
# (paths, embedding model); this file owns the "bring your own Ollama" bits.

import json
from pathlib import Path

SETTINGS_DIR = Path.home() / ".brain-rag"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "ollama_host": "http://localhost:11434",
    "llm_model": "qwen2.5:3b",
}


def _normalize_host(host):
    host = (host or "").strip()
    if not host:
        return DEFAULT_SETTINGS["ollama_host"]
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    return host.rstrip("/")


def settings_exist():
    # Used to drive the first-run experience: no file yet means the user has
    # never confirmed a working Ollama setup.
    return SETTINGS_PATH.exists()


def load_settings():
    if not SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)
    return {**DEFAULT_SETTINGS, **data}


def save_settings(new_settings):
    current = load_settings()
    if "ollama_host" in new_settings:
        current["ollama_host"] = _normalize_host(new_settings["ollama_host"])
    if new_settings.get("llm_model"):
        current["llm_model"] = new_settings["llm_model"]

    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(current, f, indent=2)
    return current


def get_ollama_host():
    return load_settings()["ollama_host"]


def get_llm_model():
    return load_settings()["llm_model"]
