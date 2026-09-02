# All LLM prompt templates live here, kept separate from the logic that uses them
# so wording can be tuned without touching retrieval/memory_ops code.

from langchain_core.prompts import PromptTemplate

# Classifies the user's message as an EDIT (something changed) or a QUESTION
# (asking for info back), and rewrites it accordingly. This is the first thing
# every incoming message goes through, both for answering and for editing.
rewrite_prompt = PromptTemplate(
    input_variables=["question"],
    template="""Look at the user's message and decide what it is, then rewrite it accordingly.

First, decide:
- If the message tells you something changed, was updated, is no longer true, or provides new information about something that already exists, treat it as an EDIT.
- Otherwise, if the message is asking for information back, treat it as a QUESTION.

Then rewrite it using the matching rules below.

If EDIT:
Extract a short, specific search phrase naming the exact topic/subject being referred to, so it can be matched against existing stored memories.
- Do NOT include the new information itself, only the subject/topic being referred to.
- Do NOT guess the topic if it isn't clearly named.
- Keep it short, just the subject, not a full sentence.

If QUESTION:
Rewrite the user's question into a clear, grammatically correct, and specific question for retrieval.
- Preserve the exact meaning and intent of the original question.
- Do NOT add facts, topics, entities, context, assumptions, or interpretations that are not explicitly present in the question.
- Do NOT guess what the user means.
- Do NOT answer the question.
- Do NOT expand vague questions with invented context.
- If the original question is already clear, return it with only minor grammatical improvements.
- If the question is vague, improve its wording while keeping the same level of ambiguity.
- Preserve important words, names, entities, and terminology from the original question.
- Only use information contained in the original message.
- The rewritten version may be identical to the original if no meaningful clarification is possible.

Respond in EXACTLY this format, one line only:
EDIT: <search phrase>
or
QUESTION: <rewritten question>

No explanation, no extra text.

Message: {question}

Response:"""
)

# Final answer-generation prompt, given the question plus retrieved memory chunks.
# Explicitly told to only use the provided context, no outside knowledge.
answer_prompt = PromptTemplate.from_template(
    """ """)

# Used by memory_edit(): given a handful of candidate chunks, picks which one the
# edit is actually about and returns just its Chroma id (or NONE).
select_id = PromptTemplate.from_template(
    """You are selecting which memory best answers the user's question, then responding with its ID.

Memory candidates:
{context}

Question: {question}

Instructions:
- Choose the ONE candidate that best answers the question.
- If none of the candidates contain relevant information, respond with exactly: NONE
- Respond with ONLY the id value, nothing else — no quotes, no labels, no explanation, no extra text.
- For example, if the candidate is id='value', respond with exactly: value
"""
)

# Does the actual in-place rewrite: blends the old memory with what changed into
# one coherent sentence, plus a short one-line CHANGE_SUMMARY that gets appended
# to the edit trail (this is the "cascade-summarized" trail from ARCHITECTURE.md,
# not a full verbatim history).
edit_content_prompt = PromptTemplate.from_template(
    """You are updating a stored memory based on new information from the user.

Old memory: {old_content}

Note: the old memory above may be given in the form page_content='...', if so, the actual memory text is only what comes after page_content=, ignore any other fields like id, metadata, Date-Time, etc, those are not part of the memory content.

User's new message: {new_message}

Task:
1. Read the old memory carefully, it may contain details (reasons, context, extra facts) that are still true and should NOT be lost.
2. Read the user's new message, it tells you what has changed.
3. Write ONE new standalone sentence that keeps all still-true details from the old memory, but naturally rewrites in the part that changed, don't just paste the new message in, blend it so it reads as one coherent sentence, in third person, past tense.
4. Write a short summary of just what changed, one past-tense sentence, no dates.

Respond in EXACTLY this format, nothing else:
NEW_CONTENT: <the full updated memory, one coherent standalone sentence, keeping old context, rewritten with the change>
CHANGE_SUMMARY: <one short past-tense sentence describing only the change>

Example:
Old memory: User has a dentist appointment on August 16th because of a toothache.
User's new message: change my dentist appointment to the 18th
NEW_CONTENT: User's dentist appointment for the toothache has been moved to August 18th.
CHANGE_SUMMARY: User rescheduled the dentist appointment to August 18th.
"""
)
