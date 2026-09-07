# All LLM prompt templates live here, kept separate from the logic that uses them
# so wording can be tuned without touching retrieval/memory_ops code.
#
# Style note that applies to every prompt below: rules are expressed over
# sentence STRUCTURE and function words (question words, auxiliaries, removal
# verbs, "?"), never over subject matter, and examples use angle-bracket slots
# instead of real topics. The earlier versions few-shot the model with concrete
# messages about specific things (a drink, a movie, a name, an appointment),
# and a small local model doesn't extract "declarative sentence -> SAVE" from
# those — it partly extracts "this kind of topic -> SAVE", so anything outside
# those topics falls back to a weaker prior. Anchoring on grammar generalises;
# anchoring on content words doesn't.

from langchain_core.prompts import PromptTemplate

# Binary pre-filter, run before anything else. Casual chit-chat (greetings,
# thanks, small talk) should never touch memory/retrieval at all — this used
# to be one of five categories in rewrite_prompt below, but folding it in with
# the rest meant every "hi" still paid for a full classify+rewrite reasoning
# pass tangled up with the other categories. Splitting it into its own tiny
# binary check first is simpler and cheaper, and keeps rewrite_prompt focused
# on messages that actually need memory handling.
#
# Decides on one test — "did this add or request information?" — plus a set of
# structural shapes, rather than a list of literal example messages.
chat_classify_prompt = PromptTemplate.from_template(
    """Classify the message as CHAT or NOT_CHAT.

NOT_CHAT — the message does at least one of these:
  (a) states or implies anything about the user's own life: a fact, preference, opinion, possession, relationship, plan, habit, or something they did;
  (b) asks for something about the user to be recalled;
  (c) commands that stored information be removed.

CHAT — none of the above. The message is pure social contact, or is about you/the
conversation itself: greeting, farewell, thanks, acknowledgement, a reaction to
your last reply, or a question about what you are.

Decisive test — ask exactly this: after this message, is anything new known about
the user, or is the user waiting for something to be recalled or removed?
  yes -> NOT_CHAT
  no  -> CHAT

Rules:
- Length and tone decide nothing. A three-word sentence naming something in the
  user's life is NOT_CHAT. A long, warm greeting is still CHAT.
- Casual phrasing decides nothing. Information stated offhandedly is still information.
- If the message mixes a pleasantry with anything about the user, answer NOT_CHAT.

Shapes (the structure matters, not the subject; the angle brackets are slots that
stand for whatever the real message says):
  <greeting / thanks / farewell / acknowledgement>, and nothing else -> CHAT
  <question about you, the assistant, or this conversation>          -> CHAT
  I <like / love / hate / prefer / want / need / have / own / am> <anything> -> NOT_CHAT
  my <attribute / person / thing> is <value>                          -> NOT_CHAT
  I <did / am doing / will do> <activity> <optionally when or where>  -> NOT_CHAT
  <question word or auxiliary> ... <my / I> ...                       -> NOT_CHAT
  <forget / delete / remove / erase> <anything>                       -> NOT_CHAT

Answer with EXACTLY one word, nothing else: CHAT or NOT_CHAT

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
# had no reliable signal to go on and got misclassified, so an edit-worthy
# message could land in NEW and just get saved as an unrelated duplicate
# instead of updating the existing memory. SAVE routes everything through
# Memory_Trail instead (see agent.py), which retrieves first and only then
# decides — with actual candidates in front of it — whether this is an edit to
# something existing or nothing related exists, in which case it creates a new
# memory itself (see memory_ops.memory_edit's NONE fallback). The label only
# needs to know "this message provides/changes info" — the new-vs-edit
# judgment call now happens downstream, after retrieval, where there's
# actually enough information to make it well.
#
# DELETE is kept deliberately narrow (explicit removal language only) rather
# than folded into SAVE, since deletion is destructive and irreversible — a
# vague "no longer true" should still default to SAVE (update in place, keep
# the history in edit_trail), not silently erase the memory. The literal
# removal-word checklist is kept as-is: those are function words, so they
# generalise across topics in a way content examples don't.
rewrite_prompt = PromptTemplate(
    input_variables=["question"],
    template="""Label the user's message, then rewrite it according to that label.
(Casual chit-chat is filtered out earlier — every message here needs real handling.)

The label depends ONLY on sentence structure and command words, never on what the
message is about. The same topic can appear under any label.

- QUESTION: the message requests information back. Test for structure, in order:
    1. it ends with "?", OR
    2. it opens with an interrogative word (what / when / where / who / which / why / how), OR
    3. it opens with an inverted auxiliary about the user (do I / did I / does my / is my / am I / have I / can I / was my).
  If none of the three holds, it is NOT a QUESTION — no matter how question-like
  the topic feels. A declarative sentence stays declarative even when it concerns
  something you would also expect to be asked about (a name, a date, a plan, a rating).

- DELETE: the message issues a removal command aimed at the stored information.
  Hard checklist — one of these literal words/phrases must be present and used as a
  command: "forget", "delete", "remove", "erase", "stop remembering", "get rid of".
  If none appears literally, it is NOT DELETE. Change-of-state wording is not a
  removal command: "no longer", "not anymore", "used to", "stopped", "changed",
  "switched", "moved", "cancelled" all mean the fact was UPDATED, so they are SAVE.

- SAVE: everything else — the message provides or changes information about the
  user. This covers both a first-time statement and a revision of something that
  may already be stored. Do not try to tell those apart here; that decision is
  made later, once what is actually stored is known.

Then rewrite:

If SAVE — produce a short DESCRIPTIVE search phrase for finding a related existing
memory. Build it as: <the main subject, in the user's own words>, <one or two
broader category words or synonyms for that subject>. Include the attribute being
set or changed if there is one. Keep it under about eight words: too narrow misses
a differently-worded memory, too broad matches nothing. Do not phrase it as a
question. Do not add facts the message does not contain.

If DELETE — extract a short, specific search phrase naming the exact subject to be
removed, including any distinguishing name, qualifier, or date the user gave.
Keep it precise, not broad: deletion should only match a clear hit. Do not guess a
subject that was not clearly named.

If QUESTION — rewrite it as a clear, natural, search-friendly question describing
what is being asked about, phrased the way an answer would likely be written down.
Make the implied subject explicit and expand abbreviations. Preserve the original
intent, plus any names, entities, and terminology from the original. Invent no
dates, places, or names. Do not answer it. It may come out identical to the original.

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
#
# Left as it was: it carries no topic-specific few-shots. The "(previously: ...)"
# passage describes a real data format produced by agent._format_context, not an
# example subject, so it doesn't bias anything.
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
#
# The two worked examples this used to end with were replaced by an explicit
# subject-identity procedure — the examples were doing double duty as a format
# demo and a topic hint, and only the first of those was worth keeping (the
# format is covered by the id='value' line).
select_id = PromptTemplate.from_template(
    """You are matching a user's message to the ONE stored memory it is about, so that
memory can be updated. The message describes something new or changed — it is not a
question, and no candidate will already contain the new information. That is expected
and is exactly what makes a candidate out of date.

Memory candidates:
{context}

User's message: {question}

Procedure:
1. Name, to yourself, the subject of the user's message — the specific person, thing,
   plan, event, or attribute it is about.
2. Name the subject of each candidate the same way.
3. Pick the candidate whose subject is the SAME real-world subject. Nothing else matters.

Same subject includes all of these:
- the message gives a fuller, more precise, or corrected version of what the candidate records;
- the message replaces the value in the same slot (a preference, a date, a place, a status);
- the message reports that a plan, intention, or activity the candidate records has now happened.

Not the same subject:
- the candidate merely shares a word, a category, or a general theme with the message;
- the candidate concerns a different person, thing, plan, or event.

Being the only candidate, or the top-ranked one, is NOT evidence of a match. Candidates
come from keyword and similarity search, which surfaces unrelated text on incidental word
overlap. If no candidate is about the same real-world subject, respond NONE even when
only one candidate exists.

Respond with ONLY the id value, nothing else — no quotes, no labels, no explanation.
If a candidate appears as id='value', respond with exactly: value
If nothing matches, respond with exactly: NONE"""
)

# Used by memory_delete(): same shape as select_id, but deliberately much more
# conservative, because deletion is permanent and unrecoverable (no edit_trail
# kept afterward) — unlike an edit, a wrong pick here can't be undone by looking
# at history. Retrieval (BM25 + vector) can surface a loosely related candidate
# just from keyword overlap even when it isn't what the user meant, so this
# prompt is biased hard toward NONE unless the match is clear. The old
# named-gym illustration is now stated as a general specificity rule instead:
# the request's identifying details must actually appear in the candidate.
select_id_for_delete = PromptTemplate.from_template(
    """You are deciding whether any stored memory is the SPECIFIC one the user wants deleted.

Memory candidates:
{context}

User's delete request: {question}

This is DESTRUCTIVE and PERMANENT — a deleted memory cannot be recovered. Be conservative.

Test: list every identifying detail in the delete request — the named entity, plus any
qualifier, owner, place, date, or number that narrows it down. A candidate matches only
if it is about that same specific thing: its identifying details agree, and none contradict.

- Sharing a general category, activity, or keyword with the request is NOT a match.
  If the request names a specific entity and the candidate only describes the surrounding
  general topic without that entity, respond NONE.
- If two candidates could both plausibly be meant, respond NONE — ambiguity is not a match.
- If you have any real doubt at all, respond NONE. Doing nothing is always better than
  deleting the wrong memory.

Respond with ONLY the id value if there is a clear, specific match, or exactly NONE
otherwise — no quotes, no labels, no explanation, no extra text."""
)

# Does the actual in-place rewrite: blends the old memory with what changed into
# one coherent sentence, plus a short one-line CHANGE_SUMMARY that gets appended
# to the edit trail (this is the "cascade-summarized" trail from ARCHITECTURE.md,
# not a full verbatim history).
#
# Unlike the classifiers, this one still needs a visible example — the strict
# NEW_CONTENT/CHANGE_SUMMARY layout is parsed by string splitting in
# memory_ops._rewrite_in_place, so a format demo earns its place. It's written
# with angle-bracket slots so it teaches the layout without teaching a topic.
edit_content_prompt = PromptTemplate.from_template(
    """You are updating a stored memory based on new information from the user.

Old memory: {old_content}

Note: the old memory may be given in the form page_content='...'. If so, the memory text
is only what follows page_content= — ignore id, metadata, Date-Time and any other field.

User's new message: {new_message}

Task:
1. Read the old memory for details that are still true — people, places, times, reasons,
   surrounding facts. These must survive the edit even though the new message does not repeat them.
2. Read the new message to see what actually changed.
3. Write ONE standalone sentence, third person, past tense, that keeps every still-true
   detail and rewrites only the part that changed. Blend it into one coherent sentence
   rather than pasting the new message onto the old one.
4. Write one short past-tense sentence describing only what this edit changed. No dates.

Rules — do not break these:
- Invent nothing. No person, place, name, date, number, or detail that is absent from both
  the old memory and the new message. If unsure of a detail, leave it out.
- Drop or alter a detail from the old memory ONLY if the new message contradicts it.
  A detail the new message is silent about is still true and must be kept.
- CHANGE_SUMMARY describes only this edit's change. It must not mention any subject or
  detail absent from both inputs.

Respond in EXACTLY this format, nothing else:
NEW_CONTENT: <the full updated memory, one coherent standalone sentence, keeping old context, rewritten with the change>
CHANGE_SUMMARY: <one short past-tense sentence describing only the change>

Format example — the angle brackets are slots standing for whatever the real inputs say.
Never output angle brackets or the slot words themselves; copy only the layout:
Old memory: User <did/has> <thing> at <detail A> because of <reason>.
User's new message: change <thing> to <detail B>
NEW_CONTENT: User's <thing> for the <reason> has moved to <detail B>.
CHANGE_SUMMARY: User changed the <thing> to <detail B>."""
)
