# Brain-Rag

A local, privacy-preserving RAG system for personal notes/memories, with support for updating memories in place rather than only ever appending new ones.

## Tool Stack

| Layer | Choice |
|---|---|
| Framework | LangChain |
| Vector DB | Chroma (local) |
| Embeddings | SBERT via HuggingFace — `all-MiniLM-L6-v2` |
| Generation | Phi-4 Mini, run locally via Ollama |
| Evaluation | RAGAS (later phase) |

Everything runs locally — no external API calls for embedding or generation.

## Storage Design

- **One Chroma collection for everything.** No collection-per-category. Categories are metadata on chunks, not a partitioning mechanism.
- **Categories are dynamic, not preset.** The LLM assigns a category at ingestion time, choosing to match an existing one or invent a new one.
- **Category list lives in a separate JSON file.** The LLM reads this file as context before tagging, so it knows what categories already exist and can prefer reusing them.
- **The LLM never writes to the JSON file directly.** It only returns a category name in its response. Application code checks whether that name is new and appends it to the JSON file if so. This is a deliberate guardrail — the LLM cannot corrupt the categories file, because it never has write access to it.

## Pipeline 1: Core Read Path (Ingestion + Retrieval/Generation)

```
Notes ──► Load & Chunk ──► SBERT Embed ──► Store in Chroma
                                                  │
Question ──► Embed ──► Chroma Retrieve (nearest chunks) ──┤
                                                  │
                                     Chunks + Question ──► Phi-4 Mini ──► Answer
```

## Pipeline 2: Write Path (Ingestion with Dynamic Tagging)

```
New note / upload
       │
       ▼
   LLM reads existing categories (from JSON)
       │
       ▼
   LLM matches existing category OR proposes a new one
       │
       ▼
   App code validates/appends new category to JSON (LLM never writes JSON itself)
       │
       ▼
   Chunk stored in Chroma with category as metadata
```

## Edit Tool (MCP-style, update-in-place)

Memories can be **updated**, not just created. This is distinct from deletion.

**Flow:**
1. User tells the chatbot something changed or was completed.
2. The LLM identifies the relevant chunk by its unique Chroma ID.
3. The LLM calls an edit tool (rather than creating a duplicate entry).
4. The edit:
   - Rewrites the main content to reflect the current state.
   - Appends a **compact, one-sentence metadata trail entry**: what changed, and when — not a full verbatim snapshot of the old version.
5. **Cascade summarization:** as edits accumulate, older trail entries get progressively compressed/summarized down, so total metadata size stays roughly constant regardless of how many edits happen over time.
   - Result: there is always exactly **one full-detail current version** plus a **compressed history trail** behind it — never an ever-growing list of full old versions.
6. **Rationale:** mirrors how human memory works — a small compressed trace is enough to reconstruct context; you don't need the full verbatim history to remember that something changed.

**Deletion** is a separate, explicit action — used only when the user wants a memory actually removed, not updated.

## Design Constraints (do not casually change)

These were deliberate decisions, not defaults:
- Single collection, not collection-per-category.
- LLM proposes categories; it never has direct write access to the categories JSON.
- Edit trail is cascade-summarized, not append-only/full-history.
- Edit and delete are separate, explicit operations.
