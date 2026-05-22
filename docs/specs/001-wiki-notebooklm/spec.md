# Spec: Wiki Gap Research via Web Search

**ID:** 001-wiki-notebooklm  
**Date:** 2026-05-22  
**Status:** Approved  
**Version:** 2.0.0  

---

## Problem Statement

`wiki-query` answers questions from the local wiki using hybrid search. When no page scores above 0.3, the wiki has a genuine knowledge gap — but the user has no structured path to research that gap, pull in new knowledge, and grow the wiki. The gap should be fillable in-conversation: find a source via web search, save it to `raw/`, ingest it, and re-query — all without leaving Claude Code.

---

## Goals

1. When `wiki-query` detects a gap (score < 0.3), it immediately offers to web-search for relevant sources.
2. The user selects which found source(s) to save; the raw document is written to `raw/<topic>/`.
3. After saving, `wiki-query` tells the user the exact `wiki-ingest` command to run.
4. After ingest completes, `wiki-query` offers to re-run with the original question once.
5. `wiki-ingest` remains completely unchanged — it processes whatever lands in `raw/<topic>/` as normal.

---

## Non-Goals

- Any integration with Google NotebookLM or the `nlm` CLI.
- A `wiki/nlm-notebooks.md` registry or any notebook-mapping file.
- `wiki-nlm-sync` and `wiki-nlm-research` skills — these are removed.
- Automatic ingestion without explicit user approval.
- Any modification to `wiki-ingest` or `wiki-lint`.
- Real-time, scheduled, or background operations.

---

## Users and Context

**Primary user:** A researcher using Claude Code as their wiki maintainer. They ingest papers/articles into a local markdown wiki and query it with natural language. When the wiki can't answer a question, they need a fast in-conversation path to find a relevant source, add it to `raw/`, and grow the wiki.

**Context:** The user has a working `raw/<topic>/` folder structure (or is willing to create one). No external CLI tools or authentication are required.

---

## User Stories

### US-1: Gap detection and web search offer

**As a** researcher whose `wiki-query` returns a gap (score < 0.3),  
**I want** wiki-query to immediately offer to web-search for relevant sources,  
**so that** I can find something worth ingesting without switching context.

**Acceptance criteria:**
- When all qmd results score below 0.3 and the index scan also turns up nothing, wiki-query announces the gap with the best score seen.
- It immediately offers: "want me to web-search and ingest a new source, or do you have a document to add to `raw/`?"
- If the user says yes to web search: wiki-query runs a search and presents 2–3 relevant results (title, URL, one-line summary).
- The user selects which result(s) to save; wiki-query fetches the content and saves it to `raw/<topic>/`.
- After saving, wiki-query states the exact `wiki-ingest` command to run.

---

### US-2: Re-query after ingest

**As a** researcher who just ingested a new source,  
**I want** wiki-query to offer to re-run my original question,  
**so that** I can immediately see whether the gap is filled without re-typing.

**Acceptance criteria:**
- After `wiki-ingest` completes, wiki-query offers once: "Want me to re-run wiki-query with the original question now that the wiki has been updated? (yes/no)"
- If yes: re-executes wiki-query with the original question and reports updated results.
- If no: stops.
- If the re-query still scores below 0.3: reports the still-open gap and stops — does not loop again automatically.

---

### US-3: Local file as alternative to web search

**As a** researcher who already has a document,  
**I want** wiki-query to accept "I have a local file" as an answer to the gap offer,  
**so that** I can drop a file into `raw/` and follow the same ingest → re-query flow.

**Acceptance criteria:**
- When the user says they have a local file instead of wanting a web search, wiki-query tells them to drop it in `raw/<topic>/` and run `wiki-ingest`.
- After ingest, the same re-query offer applies (US-2).

---

## Functional Requirements

### FR-1: Gap detection threshold

- Gap is declared when the best qmd score across all sub-queries is < 0.3 **and** the index scan turns up no relevant pages.
- A score between 0.3–0.59 is not a gap — wiki-query skims the snippet and reports partial coverage.

### FR-2: Web search behavior

- wiki-query uses the `WebSearch` tool to find 2–3 relevant sources for the gap question.
- Results are presented with title, URL, and a one-line summary.
- The user selects which to fetch; wiki-query uses `WebFetch` to retrieve the content.
- Content is saved as-is (markdown or plain text) to `raw/<topic>/` with a descriptive filename (e.g., `openVLA-2024.md`).
- The `raw/<topic>/` directory is created if it does not exist.

### FR-3: Ingest handoff

- After saving, wiki-query states the exact command: `` Run `wiki-ingest` on `raw/<topic>/<filename>` to integrate into the wiki. ``
- wiki-query does not auto-ingest; the user runs `wiki-ingest` explicitly.

### FR-4: Re-query loop

- After `wiki-ingest` completes, wiki-query offers to re-run the original question exactly once.
- If the re-query still scores below 0.3: report the gap and stop — do not recurse.
- Never loop more than once automatically; further research requires a fresh user prompt.

### FR-5: wiki-query gap section

- Step 5 (Handle low-confidence results) of `skills/wiki-query/SKILL.md` contains the web search gap handoff.
- No other skills are added or modified by this spec.

---

## Non-Functional Requirements

- **No new dependencies** — uses only `WebSearch` and `WebFetch` tools already available in Claude Code.
- **No new files** beyond the raw documents saved during a gap-fill session.
- **Minimal surface area** — the entire feature lives in step 5 of `wiki-query/SKILL.md`.
- **Consistent logging** — if a source is saved and ingested, the ingest skill appends to `wiki/log.md` as normal.

---

## Error Scenarios

| Scenario | Expected behavior |
|----------|------------------|
| Web search returns no relevant results | Report so, suggest the user drop a local file in `raw/` |
| WebFetch fails for a URL | Report the failure, offer to try a different result |
| `raw/<topic>/` does not exist | Create it, then save the file |
| User declines web search and has no local file | Report the gap and stop |
| Re-query still scores below 0.3 | Report still-open gap, stop — no second loop |

---

## Out of Scope

- Google NotebookLM, `nlm` CLI, notebook registry.
- `wiki-nlm-sync` and `wiki-nlm-research` skills.
- Bulk ingestion or scheduled research.
- Any UI or web interface.
