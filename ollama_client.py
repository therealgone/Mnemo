# Talks to a user-configured local Ollama instance: lists installed models and
# checks basic reachability + tool-calling support. Kept separate from
# agent.py/config.py so the Settings panel can probe Ollama without touching
# core chat logic.

import ollama
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


@tool
def _ping(value: str) -> str:
    """Echo back the given value. Used only to probe tool-calling support."""
    return value


def list_models(host):
    client = ollama.Client(host=host)
    return [m.model for m in client.list().models]


def check_connection(host):
    try:
        list_models(host)
        return True, f"Connected to {host}."
    except Exception as e:
        return False, f"Could not reach Ollama at {host}: {e}"


def check_tool_calling(host, model):
    # Some small local models (e.g. phi4-mini) have been unreliable at actually
    # making tool calls even when they claim to support the capability, so this
    # does a real round-trip invoke rather than trusting `ollama show`.
    try:
        llm = ChatOllama(model=model, base_url=host).bind_tools([_ping])
        response = llm.invoke(
            "Call the _ping tool with value set to the string 'ok'. "
            "You must call the tool rather than answering in text."
        )
        if response.tool_calls:
            return True, f"{model} supports tool calling."
        return False, (
            f"{model} responded without making a tool call — "
            "tool-calling may be unreliable for this model."
        )
    except Exception as e:
        return False, f"Tool-calling check failed: {e}"
