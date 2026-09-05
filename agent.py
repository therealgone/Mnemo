# Ties everything together: system prompt + tool-bound LLM + one function that
# handles a single turn of conversation (retrieve context, ask the model,
# execute any tool call it makes).

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from retrieval import context_retrieve, is_chat
from tools import save_chat_memory, Memory_Trail, Forget_Memory
from prompts import answer_prompt, chat_prompt
from vectorstore import get_llm
from settings import get_llm_model, get_ollama_host

# Used only for SAVE/DELETE now — CHAT is answered straight away by the plain
# LLM (see handle_message), and QUESTION is answered by the plain LLM too, so
# this only needs to describe the tool-calling role, not an answering persona.
system_prompt = SystemMessage(content="""You are a personal RAG-based memory assistant, a "second brain" for the user.

You have tools for saving/updating and deleting memories: Memory_Trail is the
default choice for any message that states or changes information about the
user — it checks for a related existing memory first and creates a new one
itself if nothing related is found, so it's safe to call whether or not you're
sure something related is already stored. Only use save_chat_memory directly
if you're certain no related memory could possibly exist. Use Forget_Memory
only when the user explicitly asks to remove/delete/forget something with no
replacement information given — it is destructive and permanent, so don't
call it just because something is no longer true.

You will only be asked to act on messages that already need one of these
tools — always call the matching tool instead of just replying in text.
""")
def get_llm_with_tools():
    # Built fresh from current settings on every call, so switching model/host
    # in Settings applies immediately without an app restart. Binding tools tells
    # the model these functions are available to call — it decides on its own,
    # per message, whether to just answer, save a new memory, edit one, or delete one.
    llm = ChatOllama(model=get_llm_model(), base_url=get_ollama_host(), temperature=0, seed=42)
    return llm.bind_tools([save_chat_memory, Memory_Trail, Forget_Memory])


def _format_context(context):
    # context_retrieve() returns a mixed-shape list — (Document, score) tuples
    # from similarity_search_with_score plus bare Documents from the ensemble
    # retriever (see retrieval.py's comment on why). memory_ops.select_id
    # depends on that raw shape (it reads the literal id=... text out of the
    # Document repr), so context_retrieve can't change it — this just builds a
    # clean, deduplicated, human-readable version for the answer LLM instead of
    # dumping raw Python object reprs into the prompt.
    #
    # Also surfaces each memory's edit_trail (the cascade-summarized change
    # history from memory_ops) alongside its current content, so the answer LLM
    # can see how something changed over time — not just its latest state —
    # and mention that in the answer where it's relevant (e.g. a preference
    # that was replaced, a plan that was later completed).
    seen = set()
    lines = []
    for item in context:
        doc = item[0] if isinstance(item, tuple) else item
        text = doc.page_content.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        trail = doc.metadata.get("edit_trail") if doc.metadata else None
        trail_list = trail if isinstance(trail, list) else []
        if trail_list:
            history = " -> ".join(trail_list)
            lines.append(f"- {text} (previously: {history})")
        else:
            lines.append(f"- {text}")
    return "\n".join(lines) if lines else "No relevant memories found."


def handle_message(question):
    # 1. Binary pre-filter: casual chit-chat never touches retrieval, memory,
    #    or tools at all — just a brief, in-persona reply from the plain LLM.
    if is_chat(question):
        return get_llm().invoke(chat_prompt.format(message=question)).strip()

    # 2. Everything else gets classified as SAVE/DELETE/QUESTION and retrieved
    #    against. QUESTION is answered directly by the plain (non-tool-bound)
    #    LLM — binding tools for a question was causing a small local model
    #    (qwen2.5:3b) to occasionally leak a raw tool-call JSON string into the
    #    answer instead of just replying. Only SAVE/DELETE go through the
    #    tool-bound model — those always need a tool call.
    label, context = context_retrieve(question)

    if label == "QUESTION":
        clean_context = _format_context(context)
        return get_llm().invoke(
            answer_prompt.format(context=clean_context, question=question)
        ).strip()

    if label == "SAVE":
        prompt_text = (
            "Message classification: SAVE — this states or changes information "
            "about the user (new fact, preference, plan, correction, or update). "
            "Whether this turns out to be brand-new or an edit to something "
            "already stored isn't known yet.\n\n"
            f"User message: {question}\n\n"
            "Call Memory_Trail with this message."
        )
    else:  # DELETE
        prompt_text = (
            "Message classification: DELETE — this explicitly asks to remove, "
            "delete, forget, or erase something already stored, with no "
            "replacement information given.\n\n"
            f"User message: {question}\n\n"
            "Call Forget_Memory with this message."
        )

    human_message = HumanMessage(content=prompt_text)
    response = get_llm_with_tools().invoke([system_prompt, human_message])

    # 3. If the model chose to call a tool, run it and return its result.
    #    Otherwise just return the plain answer it generated.
    if response.tool_calls:
        result = None
        for call in response.tool_calls:
            if call["name"] == "save_chat_memory":
                result = save_chat_memory.invoke(call["args"])
            elif call["name"] == "Memory_Trail":
                result = Memory_Trail.invoke(call["args"])
            elif call["name"] == "Forget_Memory":
                result = Forget_Memory.invoke(call["args"])
        return result
    else:
        return response.content
