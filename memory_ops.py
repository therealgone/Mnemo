# Write-path operations for chat-driven memory: saving new memories and
# editing existing ones in place. This is the "MCP-style edit tool" logic
# described in ARCHITECTURE.md, minus the @tool wrappers (those live in tools.py).

import uuid
from datetime import datetime

from langchain_core.documents import Document

from vectorstore import vectorstore, llm
from prompts import select_id, edit_content_prompt
from retrieval import context_retrieve


def save_memory_chat(chunk):
    # Same idea as vectorstore.save_memory, but for memories that come from
    # chat rather than the bulk file ingest — uses a random uuid instead of
    # a filename-based id since there's no source file/index to derive one from.
    chunk.metadata["Date-Time"] = datetime.now().isoformat()
    chunk.metadata["last_edited"] = ""
    chunk.metadata["edit_trail"] = ""

    chunk_id = str(uuid.uuid4())
    vectorstore.add_documents([chunk], ids=[chunk_id])


def memory_edit(context):
    # `context` here is the user's raw message describing what changed
    # (e.g. "my dentist appointment moved to the 18th").

    # 1. Find candidate memories that this edit might be referring to.
    candidates = context_retrieve(context)

    # 2. Ask the LLM which single candidate this edit is actually about.
    select_prompt = select_id.format(context=candidates, question=context)
    context_id = llm.invoke(select_prompt).strip()

    if context_id == "NONE":
        return "No matching memory found."

    existing = vectorstore.get(ids=[context_id])
    if not existing["ids"]:
        return "No matching memory found."

    old_content = existing["documents"][0]
    old_metadata = existing["metadatas"][0]

    # 3. Ask the LLM to rewrite the memory in place + produce a short change summary.
    mem_update = edit_content_prompt.format(old_content=old_content, new_message=context)
    updated_memory = llm.invoke(mem_update).strip()

    # Parse the strict "NEW_CONTENT: ... CHANGE_SUMMARY: ..." format the prompt demands.
    try:
        new_content = updated_memory.split("NEW_CONTENT:")[1].split("CHANGE_SUMMARY:")[0].strip()
        change_summary = updated_memory.split("CHANGE_SUMMARY:")[1].strip()
    except IndexError:
        return "Failed to parse edit response."

    # 4. Append the one-line change summary to the edit trail (not the full old
    # content) — this is the cascade-summarized trail from ARCHITECTURE.md, so
    # metadata size stays roughly constant no matter how many edits pile up.
    existing_trail = old_metadata.get("edit_trail", "")
    trail_list = existing_trail if isinstance(existing_trail, list) else []
    trail_list.append(f"{change_summary} [{datetime.now().isoformat()}]")

    new_metadata = {
        "id": context_id,
        "Date-Time": old_metadata["Date-Time"],   # preserve original creation time
        "last_edited": datetime.now().isoformat(),
        "edit_trail": trail_list
    }

    # 5. Overwrite the document content + metadata in place (same id) — this is
    # an update, not a new entry, so there's never a duplicate memory floating around.
    vectorstore.update_document(
        document_id=context_id,
        document=Document(page_content=new_content, metadata=new_metadata)
    )

    return "Done Updated"
