# Write-path operations for chat-driven memory: saving new memories and
# editing existing ones in place. This is the "MCP-style edit tool" logic
# described in ARCHITECTURE.md, minus the @tool wrappers (those live in tools.py).
# save_memory_chat lives in vectorstore.py now, since it's also used by the
# generic upload/paste ingestion path (see vectorstore.ingest_text).

from datetime import datetime

from langchain_core.documents import Document

from vectorstore import vectorstore, get_llm, save_memory_chat
from prompts import select_id, select_id_for_delete, edit_content_prompt
from retrieval import context_retrieve


def _dedupe_candidates(candidates):
    # context_retrieve() concatenates the vector-search and ensemble-retriever
    # results, which often surface the exact same document twice (once as a
    # (Document, score) tuple, once as a bare Document) — especially when there's
    # only one real candidate in the store. Feeding the same id into select_id
    # twice in two different shapes was confusing the small local model into
    # answering NONE even on an exact single match, so drop exact-id repeats
    # before it ever sees the prompt.
    seen = set()
    deduped = []
    for item in candidates:
        doc = item[0] if isinstance(item, tuple) else item
        if doc.id not in seen:
            seen.add(doc.id)
            deduped.append(item)
    return deduped


def _save_as_new(context):
    # No related memory exists to edit — per the SAVE-merged-with-EDIT design
    # (see prompts.py's comment on rewrite_prompt), this is the "turns out to
    # actually be new" outcome of calling Memory_Trail, not a failure. Saves
    # the user's raw message as a fresh memory, same as save_chat_memory does.
    doc = Document(page_content=context)
    save_memory_chat(doc)
    return f"Saved: {context}"


def _rewrite_in_place(context_id, old_content, old_metadata, new_message):
    # Shared by memory_edit() (chat-driven, id found via candidate selection)
    # and edit_memory_by_id() (UI-driven, id already known) — everything past
    # "which memory is this about" is identical for both.
    llm = get_llm()

    # Ask the LLM to rewrite the memory in place + produce a short change summary.
    mem_update = edit_content_prompt.format(old_content=old_content, new_message=new_message)
    updated_memory = llm.invoke(mem_update).strip()

    # Parse the strict "NEW_CONTENT: ... CHANGE_SUMMARY: ..." format the prompt demands.
    try:
        new_content = updated_memory.split("NEW_CONTENT:")[1].split("CHANGE_SUMMARY:")[0].strip()
        change_summary = updated_memory.split("CHANGE_SUMMARY:")[1].strip()
    except IndexError:
        return None

    # Append the one-line change summary to the edit trail (not the full old
    # content) — this is the cascade-summarized trail from ARCHITECTURE.md, so
    # metadata size stays roughly constant no matter how many edits pile up.
    existing_trail = old_metadata.get("edit_trail", "")
    trail_list = list(existing_trail) if isinstance(existing_trail, list) else []
    trail_list.append(f"{change_summary} [{datetime.now().isoformat()}]")

    new_metadata = {
        "id": context_id,
        "Date-Time": old_metadata["Date-Time"],   # preserve original creation time
        "last_edited": datetime.now().isoformat(),
        "edit_trail": trail_list
    }

    # Overwrite the document content + metadata in place (same id) — this is
    # an update, not a new entry, so there's never a duplicate memory floating around.
    vectorstore.update_document(
        document_id=context_id,
        document=Document(page_content=new_content, metadata=new_metadata)
    )

    return new_content


def memory_edit(context):
    # `context` here is the user's raw message describing what changed
    # (e.g. "my dentist appointment moved to the 18th").

    # 1. Find candidate memories that this edit might be referring to (the
    #    SAVE/QUESTION label from context_retrieve isn't needed here — that's
    #    only used by agent.py to shape the top-level tool-selection prompt).
    _, candidates = context_retrieve(context)
    if not candidates:
        return _save_as_new(context)
    candidates = _dedupe_candidates(candidates)

    # 2. Ask the LLM which single candidate this edit is actually about. If
    #    nothing matches, this genuinely is new information — save it rather
    #    than reporting failure (this is what lets "I like coke zero lime"
    #    work whether or not a coke zero memory already exists).
    select_prompt = select_id.format(context=candidates, question=context)
    context_id = get_llm().invoke(select_prompt).strip()

    if context_id == "NONE":
        return _save_as_new(context)

    existing = vectorstore.get(ids=[context_id])
    if not existing["ids"]:
        return _save_as_new(context)

    old_content = existing["documents"][0]
    old_metadata = existing["metadatas"][0]

    if _rewrite_in_place(context_id, old_content, old_metadata, context) is None:
        return "Failed to parse edit response."

    return "Done Updated"


def edit_memory_by_id(memory_id, new_message):
    # UI-driven edit: the exact memory id is already known (picked from the
    # Memory tab), so this skips the candidate-retrieval/selection steps that
    # memory_edit() needs for a chat message and goes straight to the rewrite.
    existing = vectorstore.get(ids=[memory_id])
    if not existing["ids"]:
        return {"ok": False, "error": "Memory not found."}

    old_content = existing["documents"][0]
    old_metadata = existing["metadatas"][0]

    new_content = _rewrite_in_place(memory_id, old_content, old_metadata, new_message)
    if new_content is None:
        return {"ok": False, "error": "Failed to parse edit response."}

    return {"ok": True, "text": new_content}


def memory_delete(context):
    # `context` here is the user's raw message describing what to forget
    # (e.g. "forget my dentist appointment").
    llm = get_llm()

    # 1. Find candidate memories this might be referring to — same lookup as
    #    memory_edit, just reused for deletion instead of rewriting.
    _, candidates = context_retrieve(context)
    if not candidates:
        return "No matching memory found."
    candidates = _dedupe_candidates(candidates)

    # 2. Ask the LLM which single candidate this delete request is about — uses
    #    a stricter, delete-specific prompt (not the shared select_id used by
    #    memory_edit) since a wrong pick here permanently destroys data instead
    #    of just being a recoverable bad edit.
    select_prompt = select_id_for_delete.format(context=candidates, question=context)
    context_id = llm.invoke(select_prompt).strip()

    if context_id == "NONE":
        return "No matching memory found."

    existing = vectorstore.get(ids=[context_id])
    if not existing["ids"]:
        return "No matching memory found."

    # 3. Delete outright — unlike memory_edit, there's no rewrite/trail step,
    # the whole point is the memory no longer exists afterward.
    deleted_content = existing["documents"][0]
    vectorstore.delete(ids=[context_id])

    return f"Deleted: {deleted_content}"
