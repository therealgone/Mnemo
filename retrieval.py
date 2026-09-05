# Shared search logic: turns a raw user message into ranked memory candidates.
# context_retrieve() is the one actually used by agent.py / memory_ops.py; it
# returns (label, candidates) where label is "SAVE" / "DELETE" / "QUESTION" —
# agent.py uses the label to decide how much of this to show the tool-bound LLM
# (see the comment there on why SAVE/DELETE deliberately don't get the raw
# context injected). Casual chit-chat (CHAT) is filtered out before this is
# ever called — see is_chat() below.

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from vectorstore import vectorstore, get_llm, get_all_documents
from prompts import rewrite_prompt, answer_prompt, chat_classify_prompt


def is_chat(question):
    # Cheap binary pre-filter, run before context_retrieve() for every message.
    # Keeps casual conversation ("hi", "thanks") from ever touching retrieval or
    # memory at all, and keeps rewrite_prompt/context_retrieve focused purely on
    # messages that actually need SAVE/DELETE/QUESTION handling.
    llm = get_llm()
    result = llm.invoke(chat_classify_prompt.format(question=question)).strip().upper()
    return result == "CHAT"


def context_retrieve(question):
    # Combines two retrievers rather than relying on just one:
    #   - BM25 (keyword/lexical overlap, good for exact names/dates/terms)
    #   - vector similarity (semantic meaning, good for paraphrases)
    # so a query can hit even if the wording doesn't closely match the stored text.

    all_docs = get_all_documents()
    if not all_docs:
        # Nothing stored yet (e.g. first run before any memory has been added) —
        # nothing to classify against, so treat as a fresh statement to save.
        return "SAVE", []

    llm = get_llm()

    # Step 1: classify the message and rewrite it into something more specific to
    # search with. The model responds "SAVE: ...", "DELETE: ..." or "QUESTION: ...".
    rewrite_text = rewrite_prompt.format(question=question)
    rewritten_raw = llm.invoke(rewrite_text).strip()
    label, _, rewritten_question = rewritten_raw.partition(":")
    label = label.strip().upper()
    rewritten_question = rewritten_question.strip() or rewritten_raw
    if label not in ("SAVE", "DELETE", "QUESTION"):
        label = "QUESTION"  # malformed model output — fall back to the safest path

    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    # BM25 retriever, built fresh from whatever's currently stored in Chroma.
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = 1

    # Merge BM25 + vector results using reciprocal rank fusion.
    # weights control how much each contributes to the final ranking.
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.6, 0.4],
        c=20  # tune this, e.g. 0.4/0.6 if one is more reliable
    )

    results_b = ensemble_retriever.invoke(rewritten_question)
    # Also run a plain similarity search directly so we get back (doc, score) pairs
    # — the ensemble retriever above only returns bare Documents, no scores.
    results_s = vectorstore.similarity_search_with_score(rewritten_question, k=1)

    # Note: mixed return shape — results_s is a list of (Document, score) tuples,
    # results_b is a list of bare Documents. Callers rely on this exact shape
    # (see memory_ops.memory_edit -> select_id prompt).
    context = results_s + results_b
    return label, context
