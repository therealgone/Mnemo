# Brain-Rag

Before giving any suggestion, answering any question, or making any implementation decision in this project — read `ARCHITECTURE.md` first. If a suggestion would conflict with anything in it (storage design, single-collection rule, dynamic categories, cascade-summarized edit trail, etc.), say so explicitly rather than silently going a different direction. Treat that document's "Design Constraints" section as fixed unless the user explicitly says they're reconsidering one of them.

If a conversation starts drifting away from what's in `ARCHITECTURE.md` — a new idea, a tangent, a "what if we did X instead" — check it against the doc before running with it, and flag the discrepancy rather than assuming the doc is stale.

## Do not write or edit code directly

This is a learning project. The user is building it themselves and does not want code written into files on their behalf — that includes notebook cells (`Brain.ipynb`), scripts, or any other project file.

- When a code change is needed, give the code **in the chat response**, as a snippet, with an explanation of what it does and why.
- Let the user type/paste it in and run it themselves.
- Do not use file-editing tools on this project's code files unless the user explicitly says to edit/apply it directly (e.g. "just make the edit yourself").
- This applies even after a design discussion converges on a clear next step — convergence on *what* to build is not permission to *write* it.
