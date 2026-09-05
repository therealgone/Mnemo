"""Python side of the JS <-> Python bridge. Methods on Api are called directly
from React via window.pywebview.api.<method>() — no HTTP server involved.
"""

from agent import handle_message
from vectorstore import display_memory, ingest_text, delete_memory
from memory_ops import edit_memory_by_id
from settings import (
    load_settings,
    save_settings,
    settings_exist,
    get_ollama_host,
    get_llm_model,
)
from ollama_client import list_models, check_connection, check_tool_calling


class Api:
    def ping(self):
        return "pong"

    def send_message(self, text):
        try:
            result = handle_message(text)
            return result if result is not None else ""
        except Exception as e:
            return f"Error: {e}"

    def get_memory(self):
        return display_memory()

    def upload_memory(self, text, source_name=None):
        try:
            count = ingest_text(text, source_name=source_name or "pasted")
            return {"ok": True, "chunks_added": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def delete_memory(self, memory_id):
        try:
            delete_memory(memory_id)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def edit_memory(self, memory_id, new_message):
        try:
            return edit_memory_by_id(memory_id, new_message)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def is_configured(self):
        # Drives the first-run banner: no settings file yet means the user has
        # never confirmed a working Ollama host/model.
        return settings_exist()

    def get_settings(self):
        return load_settings()

    def save_settings(self, new_settings):
        try:
            return {"ok": True, "settings": save_settings(new_settings)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_ollama_models(self, host=None):
        try:
            return {"ok": True, "models": list_models(host or get_ollama_host())}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def test_ollama_connection(self, host=None):
        ok, message = check_connection(host or get_ollama_host())
        return {"ok": ok, "message": message}

    def test_tool_calling(self, host=None, model=None):
        ok, message = check_tool_calling(
            host or get_ollama_host(), model or get_llm_model()
        )
        return {"ok": ok, "message": message}
