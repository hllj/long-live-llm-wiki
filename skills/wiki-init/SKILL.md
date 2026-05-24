---
name: wiki-init
description: >
  Initializes the LLM Wiki Notebook for a new topic. Use this skill when the
  user wants to start fresh, set up the wiki for a new topic, clean out
  previous content, or prepare the repo for production use. Trigger when the
  user says "init the wiki", "start a new wiki", "set up the wiki for X",
  "initialize", "prepare for production", "reset the wiki", or drops a request
  to configure the notebook from scratch.
---

# Wiki Init

You are initializing the LLM Wiki Notebook for a new topic. Your job is to
collect the topic from the user via a UI dialog, clean out previous content,
generate a `CLAUDE.md` tailored to the new domain, scaffold the index and log,
update `.gitignore`, and rebuild the search index — all before any real sources
are ingested.

## Workflow

### 1. Collect topic information via AskUserQuestion

Use the `AskUserQuestion` tool to show a single dialog to the user:

```
question: "What is this wiki about? Describe the topic or project in 1–3 sentences."
header: "Wiki Topic"
options: [
  { label: "Describe your topic", description: "Enter a 1–3 sentence description of the subject this wiki will cover." }
]
```

If the user selects "Other" and provides a custom text response, use that.

**Validation:** If the returned answer is empty or only whitespace, call `AskUserQuestion` again with an added note: "Topic description is required. Please describe what this wiki is about."

**Derived values (compute before touching any files):**
- `TOPIC_DESCRIPTION` — the user's answer verbatim
- `TOPIC_TITLE` — first 4–5 significant words of the description, title-cased
  (e.g. "My wiki is about reinforcement learning from human feedback" → "Reinforcement Learning from Human Feedback")
- `COLLECTION_SLUG` — kebab-case of TOPIC_TITLE
  (e.g. "Reinforcement Learning from Human Feedback" → `reinforcement-learning-from-human-feedback`)

Do not proceed to Step 2 until TOPIC_DESCRIPTION is non-empty.

### 2. Update .gitignore

Check each required line. Append only missing sections — never remove or reorder existing lines.

```bash
grep -qF 'raw/*' .gitignore 2>/dev/null && echo "present" || echo "absent"
grep -qF '.qmd/' .gitignore 2>/dev/null && echo "present" || echo "absent"
```

- If `raw/*` is **absent**: append to `.gitignore`:
  ```
  
  # Wiki raw sources
  raw/*
  !raw/.gitkeep
  ```

- If `.qmd/` is **absent**: append to `.gitignore`:
  ```
  
  # qmd local index
  .qmd/
  ```

- If all lines were already present: report "`.gitignore` already up to date."
- If `.gitignore` does not exist: create it containing only the two sections above.

### 3. Clean wiki subdirectories and raw/

Remove all content-bearing files, then place `.gitkeep` in each directory:

```bash
for dir in wiki/concepts wiki/entities wiki/sources wiki/analyses; do
  if [ -d "$dir" ]; then
    find "$dir" -type f -not -name '.gitkeep' -delete
  else
    mkdir -p "$dir"
  fi
  touch "$dir/.gitkeep"
done

find raw -type f -not -name '.gitkeep' -delete
```

Do **not** touch:
- `wiki/.obsidian/` (Obsidian config — leave as-is)
- `wiki/index.md` and `wiki/log.md` — overwritten in Steps 5 and 6, not deleted here
- `skills/`, `docs/`, `README.md`, `llm-wiki.md`

### 4. Generate CLAUDE.md

Write a complete `CLAUDE.md` to the repo root using the Write tool. This file gives Claude all operational instructions needed to run the wiki for the declared topic. Replace `<COLLECTION_SLUG>`, `<TOPIC_TITLE>`, and `<TOPIC_DESCRIPTION>` with the values derived in Step 1.

The generated file must follow this exact structure:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An LLM-maintained personal wiki about **<TOPIC_TITLE>**. You (Claude) own the `wiki/` layer entirely — creating, updating, and cross-referencing markdown pages as sources are ingested and questions are asked. The human curates sources and directs analysis; you do all the bookkeeping.

**Topic:** <TOPIC_DESCRIPTION>

Three layers:
- `raw/` — immutable source documents (articles, papers, images, data). Never modify these.
- `wiki/` — LLM-generated markdown pages. You own this entirely.
- `CLAUDE.md` — this file; the operational schema.

Two special files in `wiki/`:
- `wiki/index.md` — content catalog; one entry per wiki page with a one-line summary. Fallback for queries when qmd is unavailable.
- `wiki/log.md` — append-only activity log. Every ingest, query, and lint pass gets an entry.

## Search tooling

This wiki uses **qmd** (`npm install -g @tobilu/qmd`) as its local search engine. The `<COLLECTION_SLUG>` collection is pre-configured. Key commands:

> **Project-local index:** Run all qmd commands from the repo root. If a `.qmd/` folder exists there (created by `wiki-init`), qmd automatically uses the project-local index instead of the global one. Check with `ls .qmd/` — if missing, run `qmd init` then `qmd collection add ./wiki --name <COLLECTION_SLUG>` to register the collection.

\`\`\`bash
qmd query "<question>" --collection <COLLECTION_SLUG> --json --limit 8 2>/dev/null || true   # hybrid search + LLM re-ranking
qmd search "<term>"   --collection <COLLECTION_SLUG> --json --limit 10 2>/dev/null || true   # fast keyword-only search
qmd vsearch "<term>"  --collection <COLLECTION_SLUG> --json --limit 8 2>/dev/null || true    # semantic/vector search
qmd get <file>        --collection <COLLECTION_SLUG> 2>/dev/null || true                     # retrieve a specific page
qmd status            --collection <COLLECTION_SLUG> 2>/dev/null || true                     # index health
qmd update            --collection <COLLECTION_SLUG> 2>/dev/null || true                     # re-index after changes
qmd embed             --collection <COLLECTION_SLUG> 2>/dev/null || true                     # regenerate vectors after bulk changes
\`\`\`

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
   \`\`\`bash
   qmd query "<title or core claim>" --collection <COLLECTION_SLUG> --json --limit 10
   \`\`\`
   Pages scoring ≥ 0.5 almost certainly need updating; 0.3–0.49 worth checking.
3. Discuss key takeaways + flagged pages with the human if they want.
4. Write a summary page: `wiki/sources/<slug>.md`.
5. Update or create entity/concept pages — work through qmd's ranked list, highest score first.
6. Update `wiki/index.md` with any new or changed pages.
7. Run `qmd update --collection <COLLECTION_SLUG>` to re-index all changes.
8. Append to `wiki/log.md`:
   \`\`\`
   ## [YYYY-MM-DD] ingest | <Source Title>
   Pages created: ..., Pages updated: ...
   Key additions: [1–2 sentence summary]
   \`\`\`

A single source may touch 5–15 wiki pages. That's expected.

### Query

When the human asks a question:

1. Run `qmd query "<question>" --collection <COLLECTION_SLUG> --json --limit 8`.
   - For complex questions, decompose into 2–3 sub-queries and run each.
   - Score ≥ 0.6 → read full page. Score 0.3–0.59 → skim snippet first. Score < 0.3 → wiki gap, tell the human.
2. Synthesize an answer with citations (link to wiki pages, not raw sources directly).
3. If the answer is valuable and non-trivial, offer to file it as `wiki/analyses/<topic>.md`.
4. If filed: update `wiki/index.md`, run `qmd update --collection <COLLECTION_SLUG>`, and append to `wiki/log.md`:
   \`\`\`
   ## [YYYY-MM-DD] query | <Question or page title>
   What was answered and whether a new page was created.
   \`\`\`

### Lint

When asked to health-check the wiki:

1. Run `qmd status --collection <COLLECTION_SLUG>` for index health.
2. Use targeted qmd searches to find contradictions, orphans, hub pages, and gaps — rather than reading every page.
3. Report findings as a numbered list with specific pages and suggested fixes.
4. Fix issues if asked; run `qmd update --collection <COLLECTION_SLUG>` after fixes.
5. Append to `wiki/log.md`:
   \`\`\`
   ## [YYYY-MM-DD] lint
   Issues found and actions taken.
   \`\`\`

## Wiki page conventions

- All pages use standard markdown. No special frontmatter required unless you want Dataview queries (add `tags:`, `date:`, `sources:` fields then).
- Cross-link liberally using `[[Page Name]]` (Obsidian wikilink syntax) or standard `[text](path.md)` links.
- Source summary pages live in `wiki/sources/`. Entity pages in `wiki/entities/`. Concept pages in `wiki/concepts/`. Analyses and query outputs in `wiki/analyses/`. Top-level overview/synthesis in `wiki/`.
- When a new source contradicts an existing claim on a page, update that page and note the contradiction inline: `> **Note (updated YYYY-MM-DD):** [new source] contradicts the above — [brief explanation].`

## Index format

`wiki/index.md` sections:
\`\`\`
## Sources
- [Title](sources/slug.md) — one-line summary

## Entities
- [Name](entities/name.md) — one-line summary

## Concepts
- [Topic](concepts/topic.md) — one-line summary

## Analyses
- [Title](analyses/slug.md) — one-line summary
\`\`\`

## Log format

Each `wiki/log.md` entry starts with `## [YYYY-MM-DD] <type> | <title>` so entries are greppable:
\`\`\`
grep "^## \[" wiki/log.md | tail -10
\`\`\`

## Scope

This wiki covers **<TOPIC_TITLE>**. The human decides which sources to ingest and what questions to ask. At the start of a new sub-topic area, create stub pages for key entities and concepts so future ingests have somewhere to land.
```

After writing `CLAUDE.md`, verify that qmd commands inside it use the actual collection slug:

```bash
grep 'collection wiki' CLAUDE.md && echo "WARNING: literal 'wiki' found — check substitution" || echo "ok"
```

### 5. Write wiki/index.md

Write the complete file (overwrites the old index):

```markdown
# <TOPIC_TITLE>

<TOPIC_DESCRIPTION>

## Sources

## Entities

## Concepts

## Analyses

```

### 6. Write wiki/log.md

Write the complete file (this is a reset — do not append to the old log):

```markdown
## [YYYY-MM-DD] init | <TOPIC_TITLE>
Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
.gitignore: <"updated" or "already up to date">
CLAUDE.md: generated (collection: <COLLECTION_SLUG>)
```

### 7. Set up qmd project-local index and collection

`<COLLECTION_SLUG>` is the kebab-case slug derived in Step 1.

#### 7a. Initialize project-local index

```bash
qmd init 2>/dev/null || true
```

Verify `.qmd/` was created:

```bash
ls .qmd/ 2>/dev/null && echo "ok" || echo "missing"
```

If missing, warn: "`.qmd/` folder was not created — run `qmd init` manually before
using search commands."

#### 7b. Register the wiki collection

Check whether the collection is already registered:

```bash
qmd collection list 2>/dev/null || true
```

If `<COLLECTION_SLUG>` does not appear in the output, add it:

```bash
qmd collection add ./wiki --name <COLLECTION_SLUG> 2>/dev/null || true
```

#### 7c. Confirm setup

```bash
qmd collection list 2>/dev/null || true
```

Report the output so the user can confirm `<COLLECTION_SLUG>` is listed.

#### 7d. Build the index

```bash
qmd update --collection <COLLECTION_SLUG> 2>/dev/null || true
```

If output before the forced exit-0 suggests failure, warn: "qmd index update may
have failed — run `qmd update --collection <COLLECTION_SLUG>` manually if searches
return stale results."

Report: "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

---

## What good initialization looks like

After a successful init:
- `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/analyses/` each
  contain only `.gitkeep`.
- `wiki/index.md` opens with `# <TOPIC_TITLE>` and has four empty section headers.
- `wiki/log.md` contains exactly one entry dated today.
- `raw/` contains only `raw/.gitkeep`.
- `CLAUDE.md` is at the repo root, with qmd commands referencing `<COLLECTION_SLUG>`.
- `.gitignore` excludes `raw/*` and `.qmd/`.
- `.qmd/` exists in the repo root (project-local search index).
- `<COLLECTION_SLUG>` appears in `qmd collection list` output.
- `qmd status --collection <COLLECTION_SLUG>` shows a freshly updated index.

The human can now run `wiki-ingest` on any source to begin building real content
into the scaffold.
