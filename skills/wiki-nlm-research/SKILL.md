---
name: wiki-nlm-research
description: >
  Gap-driven research skill. Query a NotebookLM notebook when wiki-query returns
  insufficient results (score < 0.3). Use when the user wants to research a
  knowledge gap against a NotebookLM notebook and optionally pull artifacts into
  raw/<topic>/. Triggers on: "wiki-nlm-research", "research gap", "ask notebooklm",
  "query notebooklm", "nlm research", or when wiki-query suggests this skill after
  detecting a gap.
---

# Wiki ↔ NotebookLM Research

Gap-driven research against a NotebookLM notebook. Use when `wiki-query` signals
that the local wiki has insufficient coverage (score < 0.3) and you need to look
further.

## Prerequisites check

Before any operation, verify `nlm` is installed:

```bash
nlm --version
```

If not found, stop and tell the user:
> "`nlm` CLI not found. Install it with: `uv tool install notebooklm-mcp-cli`"

Then verify the session is valid:

```bash
nlm login --check
```

If the check fails, stop and tell the user:
> "Session invalid — run `nlm login [--profile <name>]` to authenticate, then retry.
> Note: NotebookLM sessions expire in ~20 minutes."

## Inputs

The user provides:
- **Question**: the gap question (from wiki-query output or a new question)
- **Topic**: the topic folder name (e.g. `vlm-research`)

If either is missing, ask for it before proceeding.

## Workflow

### 1. Resolve topic

Look up the topic in `wiki/nlm-notebooks.md` (case-insensitive match on Topic Folder).

If the file doesn't exist or the topic isn't registered:
> "Topic `<topic>` not found in registry. Registered topics: [list]. Use
> `wiki-nlm-sync` to register a new notebook first."

Stop if topic not found.

### 2. Query NotebookLM

```bash
nlm notebook query <alias> "<question>"
```

Display the full cited answer in the conversation.

If `nlm` returns an auth error:
> "NotebookLM session expired. Run `nlm login [--profile <name>]` to
> re-authenticate, then retry."

### 3. List available artifacts

```bash
nlm studio status <alias>
```

Display a numbered list of available artifacts (reports, transcripts, mind maps, etc.).

If none available:
> "No generated artifacts available in this notebook yet."
Skip to step 5.

### 4. Offer to pull artifacts

**First, offer source descriptions**: Before selection, ask:
> "Want a summary of any artifact before selecting? (enter number or 'no')"
If yes:
```bash
nlm source describe <artifact-id>
```
Display AI summary + keywords. Repeat for any artifact the user asks about.

**Then ask for selection**:
> "Which artifacts do you want to pull into `raw/<topic>/`?
> (Enter numbers, 'all', or 'none')"

For each selected artifact:
- Construct filename: `nlm-<artifact-type>-<YYYY-MM-DD>.md`
- If filename already exists in `raw/<topic>/`, append a counter suffix
- Create `raw/<topic>/` if it does not exist
- Retrieve and save content as-is:
  ```bash
  nlm source content <artifact-id>
  ```
  Write to `raw/<topic>/<filename>`.

After saving:
> "Pulled `<filename>` to `raw/<topic>/`. To integrate into the wiki, run
> `wiki-ingest` on `raw/<topic>/<filename>`."

### 5. Log the session

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] nlm-research | <Question>
Notebook: <topic>, Artifacts pulled: <comma-separated filenames or "none">, Ingest pending: yes/no
```

Always append this entry — even if no artifacts were pulled.

## What good research looks like

After this skill runs, the user should have:
1. Seen a cited NotebookLM answer to their question
2. A clear list of available artifacts with optional AI summaries
3. Any selected artifacts saved to `raw/<topic>/`, ready for `wiki-ingest`
4. A log entry recording what happened

Do not auto-ingest. Do not modify wiki pages directly. Surface results; let the
user decide what enters the wiki.
