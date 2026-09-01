# LangChain @tool wrappers around memory_ops functions. These are what get bound
# to the LLM in agent.py (llm.bind([...])) so the model can decide to call them
# during a conversation. Keeping them thin — all real logic stays in memory_ops.py.

from langchain.tools import tool
from langchain_core.documents import Document

from memory_ops import save_memory_chat, memory_edit


@tool
def save_chat_memory(content: str) -> str:
    """Save a new piece of information about the user to long-term memory.
    Use this when the user shares a fact, preference, goal, or event worth remembering,
    such as something they're learning, a plan, a personal detail, or a completed task.
    Do not use this for casual chat that has no lasting value.

    Args:
        content: The information to remember, written as a clear, standalone sentence.

    """
    # Note: the docstring above IS the tool description the LLM sees — it's not
    # just documentation for humans, it directly affects when the model decides
    # to call this tool.
    doc = Document(
        page_content=content
    )
    save_memory_chat(doc)
    return f"Saved: {content}"


@tool
def Memory_Trail(context: str) -> str:
    """Edit an existing memory when the user indicates something has changed, been completed, or is no longer accurate.

    Use this when the user's new message updates, corrects, completes, or changes the status of
    something already stored in memory.

    Do NOT use this to create a new, unrelated memory — use save_chat_memory for that instead.
    Do NOT use this if you are unsure which memory the user is referring to — in that case, do nothing.

    Args:
        context: the user's message describing what changed, in their own words.
    """
    # memory_edit does the actual candidate lookup + rewrite + trail update.
    a = memory_edit(context)
    print(a)
