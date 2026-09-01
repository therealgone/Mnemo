# Ties everything together: system prompt + tool-bound LLM + one function that
# handles a single turn of conversation (retrieve context, ask the model,
# execute any tool call it makes).

from langchain_core.messages import SystemMessage, HumanMessage

from vectorstore import llm
from retrieval import context_retrieve
from tools import save_chat_memory, Memory_Trail

system_prompt = SystemMessage(content="""You are a personal RAG-based memory assistant, a "second brain" for the user.

Your main job is to answer the user's questions using only the retrieved context provided to you below. Do not make up information that isn't in the context.

If the context doesn't contain relevant information to answer the question, say so clearly, don't guess.

Stay concise and direct in your answers. Speak naturally, as if recalling something you remember about the user, not like you're reading from a database.
""")

# Binding tools tells the model these functions are available to call — it decides
# on its own, per message, whether to just answer, save a new memory, or edit one.
llm_with_tools = llm.bind([save_chat_memory, Memory_Trail])


def handle_message(question):
    # 1. Pull relevant memory chunks for this message (used as grounding context
    #    regardless of whether this turns out to be a question or an edit).
    context = context_retrieve(question)

    human_message = HumanMessage(content=f"Context:\n{context}\n\nUser qustion:{question}")
    response = llm_with_tools.invoke([system_prompt, human_message])

    # 2. If the model chose to call a tool, run it and print its result.
    #    Otherwise just print the plain answer it generated.
    if response.tool_calls:
        for call in response.tool_calls:
            if call["name"] == "save_chat_memory":
                result = save_chat_memory.invoke(call["args"])
            elif call["name"] == "Memory_Trail":
                result = Memory_Trail.invoke(call["args"])
            print(result)
    else:
        print(response.content)
