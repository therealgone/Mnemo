# All LLM prompt templates live here, kept separate from the logic that uses them
# so wording can be tuned without touching retrieval/memory_ops code.

from langchain_core.prompts import PromptTemplate

# Binary pre-filter, run before anything else. Casual chit-chat (greetings,
# thanks, small talk) should never touch memory/retrieval at all — this used
# to be one of five categories in rewrite_prompt below, but folding it in with
# the rest meant every "hi" still paid for a full classify+rewrite reasoning
# pass tangled up with the other categories. Splitting it into its own tiny
# binary check first is simpler and cheaper, and keeps rewrite_prompt focused
# on messages that actually need memory handling.
chat_classify_prompt = PromptTemplate.from_template(
    """Decide if this message is CHAT (casual conversation, nothing to remember, look up, or change) or NOT_CHAT (a real message: it states or changes a fact about the user, asks for stored information back, or explicitly asks to delete something).

IMPORTANT: a short message is NOT automatically CHAT. Any sentence naming a
concrete preference, possession, plan, habit, or fact about the user — even
phrased casually, even starting with "I like", "I love", "I have", "I am",
"I want" — is NOT_CHAT, because it's information worth remembering. CHAT is
ONLY a pure social pleasantry with no factual content at all: a greeting,
thanks, or a question about the assistant/conversation itself, nothing else.

Check the message against these examples FIRST — if it matches the pattern of one, use that answer:
"hi" -> CHAT
"hello" -> CHAT
"hey there" -> CHAT
"thanks" -> CHAT
"thank you" -> CHAT
"thanks!" -> CHAT
"how are you" -> CHAT
"what's up" -> CHAT
"good morning" -> CHAT
"nice to meet you" -> CHAT
"ok" -> CHAT
"cool" -> CHAT
"I like coke zero" -> NOT_CHAT (a preference, worth remembering, even though it's phrased casually)
"I like pizza" -> NOT_CHAT (a preference, worth remembering, even though it's phrased casually)
"I love hiking on weekends" -> NOT_CHAT (a preference/habit, worth remembering)
"what's my name" -> NOT_CHAT
"forget my dentist appointment" -> NOT_CHAT

These examples are illustrative only — apply the same pattern to whatever the real message says, don't let the specific example topics bias your answer.

Respond with EXACTLY one word, nothing else: CHAT or NOT_CHAT

Message: {question}

Response:"""
)

# Classifies every non-chat message as SAVE (states or changes something about
# the user), DELETE (explicit removal request), or QUESTION (asking for info
# back), and rewrites it accordingly.
#
# SAVE deliberately merges what used to be two separate categories (NEW vs
# EDIT). Splitting new-vs-edit here — before ever looking at what's actually
# stored — meant a restatement with no obvious "changed"/"switched" language
# (e.g. "I like coke zero lime" said with no memory yet of coke zero at all)
# had no reliable signal to go on and got misclassified, so an edit-worthy
# message could land in NEW and just get saved as an unrelated duplicate
# instead of updating the existing coke zero memory. SAVE routes everything
# through Memory_Trail instead (see agent.py), which retrieves first and only
# then decides — with actual candidates in front of it — whether this is an
# edit to something existing or nothing related exists, in which case it
# creates a new memory itself (see memory_ops.memory_edit's NONE fallback).
# The label only needs to know "this message provides/changes info" — the
# new-vs-edit judgment call now happens downstream, after retrieval, where
# there's actually enough information to make it well.
#
# DELETE is kept deliberately narrow (explicit removal language only) rather
# than folded into SAVE, since deletion is destructive and irreversible — a
# vague "no longer true" should still default to SAVE (update in place, keep
# the history in edit_trail), not silently erase the memory.
rewrite_prompt = PromptTemplate(
    input_variables=["question"],
    template="""Look at the user's message and decide what it is, then rewrite it accordingly. (Casual chit-chat is filtered out before this step — every message you see here needs real handling.)

First, decide which ONE of these it is:
- SAVE: the message provides or changes information about the user — a new fact, preference, plan, activity, correction, update, reschedule, or replacement. This covers both a brand-new statement ("I like coke zero") and a change to something that might already be known ("I like coke zero lime now", "I switched from chess to badminton") — don't try to tell those two apart, that decision happens later once it's known what's actually in memory.
- DELETE: use this ONLY if the message contains one of these exact words/phrases, used as a command directed at the memory itself: "forget", "delete", "remove", "erase", "stop remembering", "get rid of". This is a hard checklist — before choosing DELETE, find the literal word in the message. If none of those words appear, it is NOT DELETE, no matter what else the message says (even "no longer", "not anymore", "used to but doesn't now" — those are SAVE, not DELETE, because nobody issued a removal command, they just stated something changed).
  - "forget my old gym membership" -> DELETE (contains "forget")
  - "delete the memory about my previous phone" -> DELETE (contains "delete")
  - "my bike is no longer red" -> SAVE (no removal word present, just a changed fact)
  - "I no longer live at my parents' house" -> SAVE (no removal word present, just a changed fact — do NOT treat "no longer" alone as a removal command)
These examples are illustrative only — apply the same rule to whatever subject the real message is about, don't let these specific example topics bias your answer.
- QUESTION: the message is asking for information back, using a question word or auxiliary ("what", "when", "where", "who", "which", "how", "do I", "does my", "am I", "is my", "have I") or ending in "?" — this includes questions about the user's own life/habits/preferences, not just general-knowledge questions. If it's phrased as a question, it's QUESTION even if answering it would just repeat back something like a stored preference.

Then rewrite it using the matching rule below.

If SAVE:
Rewrite it into a short, DESCRIPTIVE search phrase for finding a related existing memory — name the subject plus a couple of closely related words or synonyms, not just the bare topic word, so it has a better chance of matching an existing memory even if the exact wording is different.
- e.g. "I like coke zero lime" -> "coke zero lime, cola soft drink preference"
- e.g. "I switched from chess to badminton on weekends" -> "weekend hobby, chess badminton sport"
- Be descriptive enough to catch a loosely related existing memory, but don't pad it with unrelated words — over-broad phrases stop matching anything at all.
- Do NOT turn it into a question.
- Do NOT invent facts that aren't in the message.

If DELETE:
Extract a short, specific search phrase naming the exact topic/subject to be removed, so it can be matched against existing stored memories.
- Do NOT guess the topic if it isn't clearly named.
- Keep it short and specific, not descriptive/broad like SAVE — deletion should only match a clear, precise hit, not a loosely related one.

If QUESTION:
Rewrite the user's question into a clear, natural, search-friendly question — the goal is to describe what's being asked about clearly enough to match how the answer is actually phrased in someone's notes, not just repeat the question word-for-word.
- Preserve the original intent — don't change what's being asked.
- You MAY rephrase, expand abbreviations, or state the topic more explicitly to make it easier to match against stored notes (e.g. "what's my name" -> "the user's name", "when's the appt" -> "when is the appointment").
- Do NOT invent new facts, entities, or specifics that aren't implied by the question (e.g. don't guess a date, place, or name that wasn't mentioned).
- Do NOT answer the question.
- Preserve important words, names, entities, and terminology from the original question.
- The rewritten version may be identical to the original if it's already clear and specific.

Respond in EXACTLY this format, one line only:
SAVE: <descriptive search phrase>
or
DELETE: <search phrase>
or
QUESTION: <rewritten question>

No explanation, no extra text.

Message: {question}

Response:"""
)

# Final answer-generation prompt, given the question plus retrieved memory chunks.
# Explicitly told to only use the provided context, no outside knowledge. Run
# through the plain (non-tool-bound) LLM — see agent.py's comment on why: binding
# tools for a question makes small local models occasionally leak raw tool-call
# JSON into the answer instead of just answering.
answer_prompt = PromptTemplate.from_template(
    """You are answering a question using the user's personal memory notes below.

Memory notes:
{context}

Question: {question}

Instructions:
- Answer using only the information in the memory notes above.
- Speak directly to the user in a natural, casual tone — like a friend recalling something, not a report.
- Do NOT say "User mentioned..." or "Based on the notes..." — just answer like you already know them.
- A note written as "<current> (previously: <change 1> -> <change 2>)" has changed over time — the part before "(previously:" is the current, up-to-date state, and the part inside is what it used to be, oldest first. If the question is about something that changed (e.g. a preference that was replaced, a plan that got completed), briefly mention what it used to be before saying what it is now — like "you used to like X, but now it's Y." If the question doesn't care about the history, just answer with the current state and skip the history.
- If the notes don't contain enough information to answer, say "I don't have a memory about that."
- Keep it short — one to three sentences max.

Answer:"""
)

# Used for CHAT-labeled messages (greetings, thanks, small talk) — no memory
# context involved at all, just a brief, natural reply, in-persona as Memstra.
chat_prompt = PromptTemplate.from_template(
    """You are Memstra, a private, local-first memory assistant — a second brain that stores and recalls the user's own notes and thoughts, running entirely on their own machine. This message is just casual conversation (a greeting, thanks, small talk) — not something to save or answer from memory.

Respond naturally and briefly, like a helpful assistant would — one short sentence is usually enough. Don't re-introduce yourself or explain what you are unless the user actually asks; just talk normally. Do not mention memory, saving, or tools unless the user brings it up first.

User: {message}

Response:"""
)

# Used by memory_edit(): given a handful of candidate chunks, picks which one the
# edit is actually about and returns just its Chroma id (or NONE).
select_id = PromptTemplate.from_template(
    """You are matching a user's message to the ONE stored memory it is about, so it can be updated. The message below often describes a change (e.g. "I switched from X to Y") — it is not a question, and the memory won't already contain the new information, that's expected.

Memory candidates:
{context}

User's message: {question}

Instructions:
- The user's message describes something about a subject/topic. If a candidate is about that SAME subject/topic, it is the match — pick it, even though it doesn't yet say what the message says (that's exactly what makes it out of date).
- Only respond NONE if every candidate is about a genuinely different, unrelated subject/topic.
- Respond with ONLY the id value, nothing else — no quotes, no labels, no explanation, no extra text.
- For example, if the candidate is id='value', respond with exactly: value
"""
)

# Used by memory_delete(): same shape as select_id, but deliberately much more
# conservative, because deletion is permanent and unrecoverable (no edit_trail
# kept afterward) — unlike an edit, a wrong pick here can't be undone by looking
# at history. Retrieval (BM25 + vector) can surface a loosely related candidate
# just from keyword overlap (e.g. both mention "gym") even when it isn't what the
# user meant, so this prompt is biased hard toward NONE unless the match is clear.
select_id_for_delete = PromptTemplate.from_template(
    """You are deciding whether any of these stored memories is the SPECIFIC one the user wants deleted.

Memory candidates:
{context}

User's delete request: {question}

This is a DESTRUCTIVE, PERMANENT action — once deleted, the memory cannot be recovered.
Because of that, you must be conservative:
- Only respond with a candidate's id if it clearly and specifically matches what the user described — same subject, not just an overlapping keyword or general topic.
- Loosely related is NOT enough. E.g. if the user asks to forget "my membership at ZyxQuark Fitness" and a candidate talks about a workout routine at the gym but never mentions ZyxQuark Fitness, that is NOT a match — respond NONE.
- If you have any real doubt, respond NONE. It is always better to do nothing than to delete the wrong memory.

Respond with ONLY the id value if there is a clear, specific match, or exactly NONE otherwise — no quotes, no labels, no explanation, no extra text.
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
1. Read the old memory carefully, it may contain details (people, places, times, reasons, extra facts) that are still true and should NOT be lost, even if the new message doesn't repeat them.
2. Read the user's new message, it tells you what has changed.
3. Write ONE new standalone sentence that keeps every still-true detail from the old memory (same people, places, times, reasons — just because the new message doesn't repeat "friends" or "the weekend" doesn't mean drop them), but naturally rewrites in the part that actually changed. Don't just paste the new message in — blend it so it reads as one coherent sentence, in third person, past tense.
4. Write a short summary of just what changed, one past-tense sentence, no dates.

Rules — do not break these:
- Do NOT invent any person, place, name, date, number, or detail that is not present in the old memory or the new message. If you are unsure of a detail, leave it out rather than guessing.
- Do NOT change or drop a detail from the old memory unless the new message actually contradicts it.
- CHANGE_SUMMARY must describe only what this specific edit changed — never mention a topic, subject, or detail that doesn't appear in the old memory or the new message.

Respond in EXACTLY this format, nothing else:
NEW_CONTENT: <the full updated memory, one coherent standalone sentence, keeping old context, rewritten with the change>
CHANGE_SUMMARY: <one short past-tense sentence describing only the change>

Example:
Old memory: User has a dentist appointment on August 16th because of a toothache.
User's new message: change my dentist appointment to the 18th
NEW_CONTENT: User's dentist appointment for the toothache has been moved to August 18th.
CHANGE_SUMMARY: User rescheduled the dentist appointment to August 18th.

Example:
Old memory: User wanted to go watch Spider-Man this weekend with friends, heard it was good.
User's new message: I watched Spider-Man this weekend, it was 10 out of 10
NEW_CONTENT: User watched Spider-Man this weekend with friends and rated it 10 out of 10.
CHANGE_SUMMARY: User watched Spider-Man and rated it 10 out of 10.
"""
)
