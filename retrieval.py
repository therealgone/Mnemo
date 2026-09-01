# Shared search logic: turns a raw user message into ranked memory candidates.
# Two entry points:
#   - context_retrieve(): the one actually used by agent.py / memory_ops.py. Returns
#     Document objects (with scores) for a question.
#   - retrieve(): an older/incomplete variant that also tried category + keyword
#     filtering. Left in place for reference, but it calls select_categories/
#     categories/keyword_search which are NOT defined anywhere (that experiment
#     was abandoned mid-notebook) — calling this will raise NameError.

import json

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from vectorstore import vectorstore, llm, chunks
from prompts import rewrite_prompt, answer_prompt


def retrieve(question, k=3):
    # NOTE: broken, see module docstring above — kept as-is from the prototype.

    # Step 1: rewrite the vague question
    rewrite_text = rewrite_prompt.format(question=question)

    rewritten_question = llm.invoke(rewrite_text).strip()

    print("new q", rewritten_question)
    # Step 2: get keyword + category together, from the rewritten question
    combined_text = select_categories.format(
        # categories=categories if categories else "None yet",
        question=rewritten_question,
    )
    raw_response = llm.invoke(combined_text).strip()

    try:
        parsed = json.loads(raw_response)
        predicted_keyword = parsed.get("keyword", "")
        # predicted_category = parsed.get("category", "")
    except json.JSONDecodeError:
        print("Failed to parse JSON, falling back to unfiltered search")
        predicted_keyword = ""
        # predicted_category = ""

    print("BM")
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    # bm25 retriever, built from the same chunked documents
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = 3

    # combine them, weights control how much each contributes
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.6, 0.4],
        c=20  # tune this, e.g. 0.4/0.6 if one is more reliable
    )

    results_b = ensemble_retriever.invoke(rewritten_question)
    print("BM")

    results = []

    # try category-filtered search first
    # if predicted_category in categories:
    #     results = vectorstore.similarity_search_with_score(
    #         rewritten_question, k=k, filter={"category": predicted_category}
    #     )

    # fall back to keyword search if category search gave nothing

    if predicted_keyword in results:
        print("keyword")
        results = keyword_search(predicted_keyword, vectorstore, k=k)

    # final fallback, plain unfiltered similarity search
    if not results:
        print("Falling back to unfiltered search")
        results = vectorstore.similarity_search_with_score(rewritten_question, k=k)

    # combine both lists into one list of Document objects first
    combined_docs = results_b + [doc for doc, score in results]

    # now build context string from page_content
    context = "\n\n".join([doc.page_content for doc in combined_docs])

    response = answer_prompt.format(context=context, question=rewritten_question)
    answer = llm.invoke(response)
    print(answer)


def context_retrieve(question):
    # The retrieval function actually used elsewhere in the app.
    # Combines two retrievers rather than relying on just one:
    #   - BM25 (keyword/lexical overlap, good for exact names/dates/terms)
    #   - vector similarity (semantic meaning, good for paraphrases)
    # so a query can hit even if the wording doesn't closely match the stored text.

    # Step 1: rewrite the vague question into something more specific to search with.
    rewrite_text = rewrite_prompt.format(question=question)

    rewritten_question = llm.invoke(rewrite_text).strip()

    print("new q", rewritten_question)

    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    # BM25 retriever, built fresh from the same chunks every call (cheap since
    # chunks is small; would need caching if memory.txt grows large).
    bm25_retriever = BM25Retriever.from_documents(chunks)
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

    print("------------------------------------")
    print("\n BM:\n", results_b)

    print("------------------------------------")

    print("\n Similartiy:\n", results_s)
    print("------------------------------------")

    # Note: mixed return shape — results_s is a list of (Document, score) tuples,
    # results_b is a list of bare Documents. Callers rely on this exact shape
    # (see memory_ops.memory_edit -> select_id prompt).
    context = results_s + results_b
    return context
