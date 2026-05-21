---
name: wiki-ingest
description: >
  Processes a new source document into the LLM wiki. Use this skill whenever
  the user wants to add, ingest, or process a file into the wiki — whether they
  say "ingest this", "process raw/<file>", "I dropped a file in raw/", "add
  this article to the wiki", or any similar phrasing. This skill handles the
  complete ingest workflow: reading the source, collaborating with the user on
  emphasis, using qmd to identify which existing pages are most affected,
  writing a summary page, updating entity and concept pages throughout the wiki,
  refreshing the index, and logging the activity. Trigger even when the user
  only provides a file path and asks you to "process" or "read" it in context
  of the wiki.
---

# Wiki Ingest

You are ingesting a new source document into the wiki. Your job is to extract its knowledge and weave it into the existing wiki structure — not just summarize it in isolation, but find where it connects, where it updates, and where it contradicts what's already there.

## Workflow

### 1. Read the source

The source lives in `raw/`. Read it fully. If it references images (e.g. `![[filename.png]]`), note them and optionally read those files too for additional context.

### 2. Run impact scoring with qmd

Before touching any wiki pages, use qmd to find which existing pages this source is most likely to affect. Extract 2–4 key claims or entity names from the source, then query:

```bash
qmd query "<title or core claim>" --collection wiki --json --limit 10
qmd query "<key entity or concept>" --collection wiki --json --limit 8
```

The results give you a ranked checklist of pages to update — sorted by relevance. Pages scoring ≥ 0.5 almost certainly need updating. Pages at 0.3–0.49 are worth checking. Pages below 0.3 are unlikely to be affected but glance at them if the source is broad.

This replaces manually scanning `wiki/index.md` for large wikis, and makes the "which pages to touch" decision explicit and scored rather than guessed.

**Fallback:** if qmd is unavailable, read `wiki/index.md` to identify relevant pages manually.

### 3. Discuss with the human (if they want)

After reading and running impact scoring, briefly share:
- 3–5 key takeaways from the source
- Which existing pages qmd flagged as most affected (with scores)

Ask if there's anything they want to emphasize or any angle they care most about. If the human says "just process it" or similar, proceed without waiting.

### 4. Write the source summary page

Create `wiki/sources/<slug>.md` where `<slug>` is a short kebab-case name derived from the title or filename.

Structure the summary page as:

```markdown
# <Title>

**Source:** `raw/<filename>`
**Date ingested:** <YYYY-MM-DD>

## Summary

2–4 paragraph synthesis of the source's main argument or content.

## Key points

- Bulleted list of the most important facts, claims, or findings.

## Connections

Links to related wiki pages this source informs, supports, or contradicts.
```

### 5. Update entity and concept pages

This is the most important step. Work through the pages flagged by qmd's impact scoring in score order (highest first). For each relevant entity or concept:

- If the page exists: add new information, strengthen existing claims, or note contradictions using the inline format:
  > **Note (updated YYYY-MM-DD):** [source title](../sources/slug.md) contradicts the above — [brief explanation].
- If the page doesn't exist but the entity/concept is significant enough to warrant its own page: create it as `wiki/entities/<name>.md` or `wiki/concepts/<topic>.md`.

Cross-link liberally using `[[Page Name]]` or `[text](path.md)` links. Every page you touch should link to the new source summary, and the source summary should link back to every page it touches.

A single source typically touches 5–15 pages. That's expected.

### 6. Update the index

Add or update entries in `wiki/index.md`:
- The new source summary page under `## Sources`
- Any new entity or concept pages under their respective sections
- Update summaries for existing pages if their content changed significantly

### 7. Re-index with qmd

After all wiki writes are complete, run:

```bash
qmd update --collection wiki
```

This makes the new source summary and all updated pages immediately searchable for future queries. If you created many new pages (5+), also run `qmd embed --collection wiki` to regenerate vector embeddings.

### 8. Append to the log

Add an entry to `wiki/log.md`:

```
## [YYYY-MM-DD] ingest | <Source Title>
Pages created: wiki/sources/<slug>.md, [any new entity/concept pages]
Pages updated: [list of updated pages]
Key additions: [1–2 sentence summary of what was added to the wiki]
```

## What good ingestion looks like

The goal is not to file a summary and move on — it's to integrate the source's knowledge into the living wiki. After a good ingest, someone reading the entity and concept pages should encounter this source's perspective without having to know the source exists. The connections are already there.

The qmd impact scoring step is what separates a thorough ingest from a shallow one: it ensures that the pages most affected by the new source are the first ones you touch, not the ones you happen to remember.

If the source is thin or mostly overlaps with what's already in the wiki, say so and ask whether to proceed. Don't inflate the importance of weak sources.
