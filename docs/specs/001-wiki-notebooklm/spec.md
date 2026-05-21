# Spec: Wiki ↔ NotebookLM Integration

**ID:** 001-wiki-notebooklm  
**Date:** 2026-05-22  
**Status:** Approved  

---

## Problem Statement

`wiki-query` answers questions from the local wiki using hybrid search. When no page scores above 0.3, the wiki has a genuine knowledge gap — but the user has no structured path to research that gap, pull in new knowledge, and grow the wiki. Google NotebookLM can fill this gap: it supports document ingestion, cited Q&A, and content generation (reports, mind maps, transcripts). There is currently no bridge between the two systems.

---

## Goals

1. When `wiki-query` detects a gap (score < 0.3), it explicitly suggests running `wiki-nlm-research` with the same question.
2. Users can push content into a NotebookLM notebook — selectively choosing files from `raw/<topic>/`, wiki pages, or both — per session.
3. Users can pull NotebookLM-generated artifacts (Q&A answers, reports, podcast transcripts, mind maps) back into `raw/<topic>/` as raw files.
4. `wiki-ingest` remains completely unchanged — it processes whatever lands in `raw/<topic>/` as normal.
5. Users manually decide what gets filed into the wiki; nothing is auto-ingested.

---

## Non-Goals

- Automatic ingestion from NotebookLM without explicit user approval.
- Any modification to the existing `wiki-query`, `wiki-ingest`, or `wiki-lint` skills.
- Real-time, scheduled, or background sync — all operations are on-demand.
- Generating NotebookLM audio podcasts (transcripts may be pulled if already generated, but generation is out of scope).
- Supporting NotebookLM notebooks not registered in `wiki/nlm-notebooks.md`.

---

## Users and Context

**Primary user:** A researcher using Claude Code as their wiki maintainer. They ingest papers/articles into a local markdown wiki and query it with natural language. When the wiki can't answer a question, they need a fast path to NotebookLM — which holds additional sources — and a way to bring useful results back into the wiki without losing control of what lands there.

**Context:** The user has `nlm` CLI installed and authenticated, topic-based NotebookLM notebooks already created, and a working `raw/<topic>/` folder structure.

---

## User Stories

### US-1: Gap escalation from wiki-query

**As a** researcher whose `wiki-query` returns a gap (score < 0.3),  
**I want** the gap message to suggest the exact `wiki-nlm-research` command to run,  
**so that** I know immediately what to do next without switching context.

**Acceptance criteria:**
- When `wiki-query` scores all results below 0.3, the response includes a suggested next step referencing `wiki-nlm-research` with the same question.
- The suggestion includes a `--topic` placeholder showing which topic folder to specify.
- The existing `wiki-query` skill file is not modified; the gap suggestion is part of `wiki-query`'s existing gap-handling section (via additive instruction in the skill).

---

### US-2: Research a gap question against a NotebookLM notebook

**As a** researcher with a gap question and a relevant topic notebook,  
**I want** to query NotebookLM and see a cited answer,  
**so that** I can evaluate whether NotebookLM has knowledge the local wiki lacks.

**Acceptance criteria:**
- The skill accepts a question and a topic name as inputs.
- It resolves the topic to a notebook alias via `wiki/nlm-notebooks.md`.
- It queries the notebook and displays the cited answer in the conversation.
- If the topic is not registered, it reports an error and lists registered topics.
- The response includes a list of available generated artifacts in that notebook (reports, transcripts, mind maps), if any.

---

### US-3: Select and pull artifacts into raw/

**As a** researcher who has seen a useful NotebookLM answer,  
**I want** to choose which artifacts to download into `raw/<topic>/`,  
**so that** I can run `wiki-ingest` on them and grow the wiki.

**Acceptance criteria:**
- After the NotebookLM answer is displayed, the skill lists available artifacts with numbered options.
- The user selects which artifacts to pull (can select multiple, or none).
- Selected artifacts are saved as-is (raw text/markdown) to `raw/<topic>/` with descriptive filenames (e.g., `nlm-report-2026-05-22.md`).
- After saving, the skill tells the user the exact `wiki-ingest` command to run on each file.
- If no artifacts are available, the skill says so and skips this step.

---

### US-4: Log the research session

**As a** researcher,  
**I want** every `wiki-nlm-research` session logged in `wiki/log.md`,  
**so that** I have a record of what was researched, which notebook was used, and what was pulled.

**Acceptance criteria:**
- After each session, an entry is appended to `wiki/log.md` in the standard format:
  ```
  ## [YYYY-MM-DD] nlm-research | <Question>
  Notebook: <topic>, Artifacts pulled: <list or "none">, Ingest pending: yes/no
  ```
- The entry is appended even if no artifacts were pulled.

---

### US-5: Push content from local to NotebookLM

**As a** researcher who wants NotebookLM to have the same sources as the local wiki,  
**I want** to push files from `raw/<topic>/` or wiki pages into the matching NotebookLM notebook,  
**so that** my NotebookLM notebook stays enriched with the same knowledge base.

**Acceptance criteria:**
- The user specifies a topic; the skill resolves it to a notebook alias.
- The user chooses what to push: files from `raw/<topic>/`, wiki pages, or both.
- Each selected file/page is added as a NotebookLM source via `nlm source add --text` (content pasted as text).
- After pushing, `wiki/nlm-notebooks.md` is updated with the current date in the "Last Synced" column.
- If a file was already added as a source previously, the skill warns rather than silently creating a duplicate.

---

### US-6: Create and register a new topic notebook

**As a** researcher starting a new topic area,  
**I want** to create a NotebookLM notebook and register it in `wiki/nlm-notebooks.md` in one step,  
**so that** the topic is immediately available for push and research operations.

**Acceptance criteria:**
- The skill accepts a topic folder name and notebook title as inputs.
- It creates the notebook via `nlm notebook create` and registers the alias in `wiki/nlm-notebooks.md`.
- It creates `raw/<topic>/` if it does not already exist.
- The new entry appears in the registry table with an empty "Last Synced" value.

---

### US-7: List all registered notebooks

**As a** researcher,  
**I want** to see all registered topic notebooks with their last-synced dates,  
**so that** I know which notebooks exist and which are stale.

**Acceptance criteria:**
- The skill displays the contents of `wiki/nlm-notebooks.md` as a formatted table.
- Each row shows: topic folder, notebook title, alias, last-synced date (or "never").

---

## Functional Requirements

### FR-1: Notebook registry (`wiki/nlm-notebooks.md`)

- The file is a markdown table with columns: Topic Folder, Notebook Title, Notebook ID (alias), Last Synced.
- It is created automatically on first `wiki-nlm-sync` run if it does not exist.
- Both skills read and write this file; it is the single source of truth for topic ↔ notebook mapping.

### FR-2: Topic resolution

- Both skills resolve a topic name by looking up the "Topic Folder" column in `wiki/nlm-notebooks.md`.
- Resolution is case-insensitive and accepts both `vlm-research` and `VLM Research` as equivalent inputs.
- If resolution fails, the skill lists valid topics and exits without making any `nlm` calls.

### FR-3: Push behavior

- Files pushed from `raw/<topic>/` are added via `nlm source add --text <content> --title <filename>`.
- Wiki pages pushed are added via `nlm source add --text <markdown content> --title <page title>`.
- PDFs in `raw/<topic>/` are skipped for text-based push; the skill notifies the user that PDFs require manual upload in the NotebookLM UI.

### FR-4: Pull behavior

- Artifacts are saved to `raw/<topic>/` with filenames in the format: `nlm-<artifact-type>-<YYYY-MM-DD>.md`.
- If a file with that name already exists, the skill appends a counter: `nlm-report-2026-05-22-2.md`.
- Content is saved as-is; no preprocessing or reformatting is applied.

### FR-5: wiki-query gap suggestion

- The gap suggestion is added to the `wiki-query` skill's SKILL.md as an additive instruction (not a replacement).
- The suggestion format: `"wiki gap detected — consider running wiki-nlm-research: '<question>' --topic <relevant-topic>"`.

### FR-6: nlm CLI dependency

- Before any `nlm` operation, the skill checks that `nlm` is installed (`nlm --version`).
- If not installed, it displays the install command (`uv tool install notebooklm-mcp-cli`) and exits.
- Authentication state is not verified by the skill; `nlm` error output is surfaced directly to the user.

---

## Non-Functional Requirements

- **No new dependencies** beyond `nlm` CLI — no Python packages, no new config files beyond `wiki/nlm-notebooks.md`.
- **Idempotent pulls** — pulling the same artifact twice produces a new file with a counter suffix; it never silently overwrites.
- **Minimal surface area** — two skills only; no shared library or helper scripts.
- **Consistent logging** — every `wiki-nlm-research` session produces a `wiki/log.md` entry regardless of outcome.

---

## Error Scenarios

| Scenario | Expected behavior |
|----------|------------------|
| Topic not in registry | Report error, list valid topics, exit |
| `nlm` not installed | Show install command, exit |
| `nlm` auth expired | Surface `nlm` error output, suggest `nlm login` |
| Notebook has no artifacts | Skip artifact selection step, say so explicitly |
| `raw/<topic>/` does not exist on pull | Create the directory, then save the file |
| PDF in push selection | Skip the PDF, warn user, continue with remaining files |
| Duplicate artifact filename on pull | Append counter suffix, save, report the actual filename used |

---

## Out of Scope

- NotebookLM audio podcast generation.
- Syncing deletions (removing a source from NotebookLM when removed from `raw/`).
- Multi-account NotebookLM support.
- Bulk push of the entire wiki in one command.
- Any UI or web interface.
