# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An LLM-maintained personal wiki. You (Claude) own the `wiki/` layer entirely — creating, updating, and cross-referencing markdown pages as sources are ingested and questions are asked. The human curates sources and directs analysis; you do all the bookkeeping.

Three layers:
- `raw/` — immutable source documents (articles, papers, images, data). Never modify these.
- `wiki/` — LLM-generated markdown pages. You own this entirely.
- `CLAUDE.md` — this file; the operational schema.

Two special files in `wiki/`:
- `wiki/index.md` — content catalog; one entry per wiki page with a one-line summary. Fallback for queries when qmd is unavailable.
- `wiki/log.md` — append-only activity log. Every ingest, query, and lint pass gets an entry.

## Search tooling

This wiki uses **qmd** (`npm install -g @tobilu/qmd`) as its local search engine. The `wiki` collection is pre-configured. Key commands:

> **Project-local index:** Run all qmd commands from the repo root. If a `.qmd/` folder exists there (created by `wiki-init`), qmd automatically uses the project-local index instead of the global one. Check with `ls .qmd/` — if missing, run `qmd init` then `qmd collection add ./wiki --name <collection-name>` to register the collection.

```bash
qmd query "<question>" --collection wiki --json --limit 8 2>/dev/null || true   # hybrid search + LLM re-ranking
qmd search "<term>"   --collection wiki --json --limit 10 2>/dev/null || true   # fast keyword-only search
qmd vsearch "<term>"  --collection wiki --json --limit 8 2>/dev/null || true    # semantic/vector search
qmd get <file>        --collection wiki 2>/dev/null || true                     # retrieve a specific page
qmd status            --collection wiki 2>/dev/null || true                     # index health
qmd update            --collection wiki 2>/dev/null || true                     # re-index after changes
qmd embed             --collection wiki 2>/dev/null || true                     # regenerate vectors after bulk changes
```

> **Note:** Always append `2>/dev/null || true` to every qmd command. qmd exits with code 134 (Metal GPU teardown crash in llama.cpp) after producing correct output — suppressing stderr and forcing exit 0 prevents false "Error" banners in Claude Code.

Score thresholds to guide confidence:
- **≥ 0.6** — high relevance, read full page
- **0.3–0.59** — moderate, skim snippet first
- **< 0.3** — wiki likely has a gap; consider ingesting a new source

## Operations

### Ingest

When the human drops a file into `raw/` and asks you to process it:

1. Read the source file.
2. Run qmd impact scoring to find which existing pages are most affected:
   ```bash
   qmd query "<title or core claim>" --collection wiki --json --limit 10
   ```
   Pages scoring ≥ 0.5 almost certainly need updating; 0.3–0.49 worth checking.
3. Discuss key takeaways + flagged pages with the human if they want.
4. Write a summary page: `wiki/sources/<slug>.md`.
5. Update or create entity/concept pages — work through qmd's ranked list, highest score first.
6. Update `wiki/index.md` with any new or changed pages.
7. Run `qmd update --collection wiki` to re-index all changes.
8. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] ingest | <Source Title>
   Pages created: ..., Pages updated: ...
   Key additions: [1–2 sentence summary]
   ```

A single source may touch 5–15 wiki pages. That's expected.

### Query

When the human asks a question:

1. Run `qmd query "<question>" --collection wiki --json --limit 8`.
   - For complex questions, decompose into 2–3 sub-queries and run each.
   - Score ≥ 0.6 → read full page. Score 0.3–0.59 → skim snippet first. Score < 0.3 → wiki gap, tell the human.
2. Synthesize an answer with citations (link to wiki pages, not raw sources directly).
3. If the answer is valuable and non-trivial, offer to file it as `wiki/analyses/<topic>.md`.
4. If filed: update `wiki/index.md`, run `qmd update --collection wiki`, and append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] query | <Question or page title>
   What was answered and whether a new page was created.
   ```

### Lint

When asked to health-check the wiki:

1. Run `qmd status --collection wiki` for index health.
2. Use targeted qmd searches to find contradictions, orphans, hub pages, and gaps — rather than reading every page.
3. Report findings as a numbered list with specific pages and suggested fixes.
4. Fix issues if asked; run `qmd update --collection wiki` after fixes.
5. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] lint
   Issues found and actions taken.
   ```

## Wiki page conventions

- All pages use standard markdown. No special frontmatter required unless you want Dataview queries (add `tags:`, `date:`, `sources:` fields then).
- Cross-link liberally using `[[Page Name]]` (Obsidian wikilink syntax) or standard `[text](path.md)` links.
- Source summary pages live in `wiki/sources/`. Entity pages in `wiki/entities/`. Concept pages in `wiki/concepts/`. Analyses and query outputs in `wiki/analyses/`. Top-level overview/synthesis in `wiki/`.
- When a new source contradicts an existing claim on a page, update that page and note the contradiction inline: `> **Note (updated YYYY-MM-DD):** [new source] contradicts the above — [brief explanation].`

## Index format

`wiki/index.md` sections:
```
## Sources
- [Title](sources/slug.md) — one-line summary

## Entities
- [Name](entities/name.md) — one-line summary

## Concepts
- [Topic](concepts/topic.md) — one-line summary

## Analyses
- [Title](analyses/slug.md) — one-line summary
```

## Log format

Each `wiki/log.md` entry starts with `## [YYYY-MM-DD] <type> | <title>` so entries are greppable:
```
grep "^## \[" wiki/log.md | tail -10
```

## Scope

The human decides what this wiki is about. At the start of a new topic area, ask what entities and concepts are most important to track, then create stub pages for them so future ingests have somewhere to land.
