# LangChain @tool wrappers around memory_ops functions. These are what get bound
# to the LLM in agent.py (llm.bind([...])) so the model can decide to call them
# during a conversation. Keeping them thin — all real logic stays in memory_ops.py.

from langchain.tools import tool
from langchain_core.documents import Document

from vectorstore import save_memory_chat
from memory_ops import memory_edit, memory_delete


@tool
def save_chat_memory(content: str) -> str:
    """Save a brand-new piece of information about the user to long-term memory.

    Prefer Memory_Trail over this in almost all cases — it already checks for a
    related existing memory first and creates a new one itself if nothing related
    is found, so it's safe to call even for genuinely new information. Only reach
    for this tool directly if you're certain there is no possible related memory
    to check against.

    Do not use this for casual chat, greetings, or questions.

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
    """Save or update a memory based on something the user just said — the
    default, safe choice for any message that states or changes information
    about the user, whether or not you're sure something related is already
    stored.

    It looks for a related existing memory first: if it finds one, it edits it
    in place (blending in what changed, keeping still-true details, and logging
    a short change summary to the edit trail). If nothing related is found, it
    creates a brand-new memory itself — so it's just as safe to call for a
    genuinely new fact as for an update, you don't need to tell those apart.

    Do NOT use this if the user explicitly asks to remove/delete/forget something
    entirely with no replacement information — use Forget_Memory for that instead.

    Args:
        context: the user's message describing what changed or what's new, in
            their own words.
    """
    # memory_edit does the actual candidate lookup + rewrite + trail update.
    return memory_edit(context)


@tool
def Forget_Memory(context: str) -> str:
    """Permanently delete an existing memory when the user explicitly asks to
    remove, delete, forget, or erase something already stored.

    Only use this when the request is an explicit removal with no replacement
    information given — e.g. "forget my dentist appointment", "delete the memory
    about my old job", "remove the note about X", "erase that". If the user is
    instead correcting or updating something (giving new information in place of
    old), use Memory_Trail — do NOT use this tool just because something is "no
    longer true"; that's still an edit unless removal is explicitly requested.

    This is destructive and cannot be undone — unlike Memory_Trail, there is no
    trail kept afterward. It's safe to call even if you're not fully sure a
    matching memory exists: if none is found, this tool reports that and changes
    nothing.

    Args:
        context: the user's message describing what to forget, in their own words.
    """
    # memory_delete does the actual candidate lookup + deletion.
    return memory_delete(context)
