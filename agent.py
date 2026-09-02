# Ties everything together: system prompt + tool-bound LLM + one function that
# handles a single turn of conversation (retrieve context, ask the model,
# execute any tool call it makes).

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from vectorstore import llm
from retrieval import context_retrieve
from tools import save_chat_memory, Memory_Trail
from config import (
    LLM_MODEL,
)

system_prompt = SystemMessage(content="""You are a personal RAG-based memory assistant, a "second brain" for the user.

Your main job is to answer the user's questions using only the retrieved context provided to you below. Do not make up information that isn't in the context.

If the context doesn't contain relevant information to answer the question, say so clearly, don't guess.

Stay concise and direct in your answers. Speak naturally, as if recalling something you remember about the user, not like you're reading from a database. 

You are answering a question using the user's personal memory notes below.

Instructions:
- Answer using only the information in the memory excerpts above.
- Speak directly to the user in a natural, casual tone — like a friend recalling something, not a report.
- Do NOT say "User mentioned..." or "Based on the notes..." — just answer like you already know them.
- If the excerpts don't contain enough information to answer, say "I don't have a memory about that."
- Keep it short — one or two sentences max.
""")
llm = ChatOllama(model=LLM_MODEL)
# Binding tools tells the model these functions are available to call — it decides
# on its own, per message, whether to just answer, save a new memory, or edit one.
llm_with_tools = llm.bind_tools([save_chat_memory, Memory_Trail])


def handle_message(question):
    # 1. Pull relevant memory chunks for this message (used as grounding context
    #    regardless of whether this turns out to be a question or an edit).
    context = context_retrieve(question)


    human_message = HumanMessage(content=f"Context:\n{context}\n\nUser qustion:{question} ")
    response = llm_with_tools.invoke([system_prompt, human_message])

    # 2. If the model chose to call a tool, run it and return its result.
    #    Otherwise just return the plain answer it generated.
    if response.tool_calls:
        result = None
        for call in response.tool_calls:
            if call["name"] == "save_chat_memory":
                result = save_chat_memory.invoke(call["args"])
            elif call["name"] == "Memory_Trail":
                result = Memory_Trail.invoke(call["args"])
        return result
    else:
        return response.content
