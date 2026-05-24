# Implementation Plan: Wiki Init

> **For agentic workers:** Use sdd-tasks to generate an executable task list from this plan.

**Spec:** docs/specs/002-wiki-init/spec.md
**Created:** 2026-05-24

---

## Goal

Deliver a `skills/wiki-init/SKILL.md` that guides Claude through a safe, idempotent wiki initialization, and apply that init to the current repository to prepare it for production use.

## Architecture

The primary deliverable is a single skill file — a markdown workflow document that Claude reads and executes step-by-step. Skill files in this project follow the pattern established by `wiki-ingest`, `wiki-query`, and `wiki-lint`. The production init (Phase 2) applies the same steps described in the skill to the current repo, serving as both the first real use of the skill and the "prepare for production" change requested.

There is no data model and no API contract: all operations are filesystem reads and writes, Bash commands, and interactive user prompts.

## Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Skill format | Markdown SKILL.md with YAML frontmatter | FR-1–FR-5; matches all existing skill files in `skills/` |
| File operations | Bash (`cp -r`, `find -delete`, `touch`, `mkdir -p`) | FR-2, FR-3 require safe backup and cleanup of filesystem trees |
| Gitignore update | Bash (`grep -qF`, append via `>>`) | FR-5 requires additive, non-destructive update |
| Search index | `qmd update --collection wiki` | FR-5, AC-5.1; existing tooling defined in CLAUDE.md |

## File Structure

- `skills/wiki-init/SKILL.md` — new skill: guided 8-step init workflow (FR-1–FR-5, all ACs)
- `.gitignore` — append `raw/*`, `!raw/.gitkeep`, `.backup/` (FR-5, AC-3.1, AC-3.2)
- `.backup/raw/` — full mirror of `raw/` at time of init (FR-2, AC-2.1)
- `.backup/wiki/` — full mirror of `wiki/` at time of init (FR-2, AC-2.1)
- `wiki/concepts/.gitkeep` — directory placeholder after cleanup (FR-3, AC-2.3)
- `wiki/entities/.gitkeep` — directory placeholder after cleanup (FR-3, AC-2.3)
- `wiki/sources/.gitkeep` — directory placeholder after cleanup (FR-3, AC-2.3)
- `wiki/analyses/.gitkeep` — directory placeholder after cleanup (FR-3, AC-2.3)
- `raw/.gitkeep` — preserved; all other raw/ files removed (FR-3, AC-2.4)
- `wiki/index.md` — reset: topic heading + stub entries only (FR-4, AC-4.1, AC-4.2)
- `wiki/log.md` — reset: single init entry, no legacy entries (FR-4, AC-4.3)

## Complexity Tracking

All pre-implementation gates pass:

- **Simplicity Gate:** 1 component (skill file). No future-proofing. No new dependencies.
- **Anti-Abstraction Gate:** Bash used directly; no wrapper scripts introduced.
- **Integration-First Gate:** No API contracts needed; skill is a markdown document, not an API.

---

## Phase 1: Write skills/wiki-init/SKILL.md

**Implements:** FR-1, FR-2, FR-3, FR-4, FR-5 | **Satisfies:** AC-1.1–AC-1.5, AC-2.1–AC-2.5, AC-3.1–AC-3.3, AC-4.1–AC-4.3, AC-5.1–AC-5.2

### 1.1 Create skill directory and write SKILL.md

- [ ] Create `skills/wiki-init/` directory.
- [ ] Write `skills/wiki-init/SKILL.md` with the following complete content:

```markdown
---
name: wiki-init
description: >
  Initializes the LLM Wiki Notebook for a new topic. Use this skill when the
  user wants to start fresh, set up the wiki for a new topic, scaffold
  placeholder pages, back up existing content, or prepare the repo for
  production use. Trigger when the user says "init the wiki", "start a new
  wiki", "set up the wiki for X", "initialize", "prepare for production",
  "reset the wiki", or drops a request to configure the notebook from scratch.
---

# Wiki Init

You are initializing the LLM Wiki Notebook for a new topic. Your job is to
guide the user through declaring their wiki's scope, safely back up all existing
content, clean out example/previous content, scaffold placeholder pages for the
new domain, update `.gitignore`, and rebuild the search index — all before any
real sources are ingested.

## Workflow

### 1. Collect topic information (before touching any files)

Ask three questions **sequentially** — wait for each answer before asking the next.

**Q1 (required):** "What is this wiki about? Describe the topic or project in 1–3 sentences."

- Do not proceed if the user provides an empty response. Re-ask: "Topic description
  is required. Please describe what this wiki is about."
- Derive a topic title from the first 4–5 significant words of the description,
  title-cased (e.g. "Reinforcement Learning from Human Feedback").

**Q2 (optional, skip on empty):** "Name up to 5 key **entities** (people, models,
systems, papers, tools) this wiki should track. Separate with commas, or press
Enter to skip."

**Q3 (optional, skip on empty):** "Name up to 5 key **concepts** (ideas, techniques,
frameworks, phenomena) this wiki should track. Separate with commas, or press
Enter to skip."

For each name in Q2 and Q3:
- Trim whitespace.
- Convert to kebab-case slug: lowercase, spaces → hyphens, strip all
  non-alphanumeric characters except hyphens.
- If the resulting slug is empty after stripping, skip that entry and inform the
  user: "Skipping '<name>' — could not produce a valid filename."

Do not proceed to Step 2 until all three questions have been answered (or skipped).

### 2. Backup existing content

Before modifying or deleting any file:

\`\`\`bash
mkdir -p .backup/raw .backup/wiki
cp -r raw/. .backup/raw/ 2>&1
cp -r wiki/. .backup/wiki/ 2>&1
\`\`\`

Count backed-up files:

\`\`\`bash
find .backup/raw .backup/wiki -type f | wc -l
\`\`\`

Report: "Backed up N files to `.backup/` (raw/ and wiki/)."

**If either `cp` command fails:** Stop immediately. Do not delete or overwrite any
file. Report: "Backup failed: <error>. Aborting init — no files have been modified."

### 3. Update .gitignore

Check if `.gitignore` already contains `raw/*`:

\`\`\`bash
grep -qF 'raw/*' .gitignore 2>/dev/null && echo "present" || echo "absent"
\`\`\`

- If **absent**: append to `.gitignore`:
  \`\`\`
  
  # Wiki raw sources
  raw/*
  !raw/.gitkeep
  \`\`\`

Check for `.backup/` in `.gitignore`:

\`\`\`bash
grep -qF '.backup/' .gitignore 2>/dev/null && echo "present" || echo "absent"
\`\`\`

- If **absent**: append to `.gitignore`:
  \`\`\`
  
  # Wiki backup
  .backup/
  \`\`\`

- If all lines were already present: report "`.gitignore` already up to date."
- If `.gitignore` does not exist: create it containing only the two sections above.

### 4. Clean wiki subdirectories and raw/

Remove all content-bearing files, then place `.gitkeep` in each directory:

\`\`\`bash
for dir in wiki/concepts wiki/entities wiki/sources wiki/analyses; do
  if [ -d "$dir" ]; then
    find "$dir" -type f -not -name '.gitkeep' -delete
  else
    mkdir -p "$dir"
  fi
  touch "$dir/.gitkeep"
done

find raw -type f -not -name '.gitkeep' -delete
\`\`\`

Do **not** touch:
- `wiki/.obsidian/` (Obsidian config — leave as-is)
- `wiki/index.md` and `wiki/log.md` — overwritten in Step 6 and 7, not deleted here
- `CLAUDE.md`, `README.md`, `llm-wiki.md`, `skills/`, `docs/`

### 5. Create stub pages

For each entity name provided in Q2:

Write `wiki/entities/<slug>.md`:
\`\`\`markdown
# <Entity Name>

_Stub — to be filled by wiki-ingest._

## Notes

\`\`\`

For each concept name provided in Q3:

Write `wiki/concepts/<slug>.md`:
\`\`\`markdown
# <Concept Name>

_Stub — to be filled by wiki-ingest._

## Notes

\`\`\`

If the user provided no entities or no concepts, skip that category silently.

### 6. Write wiki/index.md

Write the complete file (overwrites the old index):

\`\`\`markdown
# <Topic Title>

<User's topic description verbatim from Q1>

## Sources

## Entities

<one line per entity stub>
- [<Entity Name>](entities/<slug>.md) — (stub)

## Concepts

<one line per concept stub>
- [<Concept Name>](concepts/<slug>.md) — (stub)

## Analyses

\`\`\`

If no stubs were created for Entities or Concepts, leave that section's body empty
(keep the `##` header).

### 7. Write wiki/log.md

Write the complete file (this is a reset — do not append to the old log):

\`\`\`markdown
## [YYYY-MM-DD] init | <Topic Title>
Backed up: raw/ and wiki/ (N files total) → .backup/
Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
Stubs created: <comma-separated list of stub page filenames, or "none">
.gitignore: <"updated" or "already up to date">
\`\`\`

### 8. Rebuild qmd index

\`\`\`bash
qmd update --collection wiki 2>/dev/null || true
\`\`\`

If output before the forced exit-0 suggests failure, warn: "qmd index update may
have failed — run `qmd update --collection wiki` manually if searches return
stale results."

Report: "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

---

## What good initialization looks like

After a successful init:
- `.backup/` holds the full previous state of `raw/` and `wiki/`.
- `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/analyses/` each
  contain only `.gitkeep`.
- `wiki/index.md` opens with the new topic heading and lists only the newly
  created stubs.
- `wiki/log.md` contains exactly one entry dated today.
- `raw/` contains only `raw/.gitkeep`.
- `.gitignore` excludes `raw/*` and `.backup/`.
- `qmd status --collection wiki` shows a freshly updated index.

The human can now run `wiki-ingest` on any source to begin building real content
into the scaffold.
```

- [ ] Verify the file was written: `ls -la skills/wiki-init/SKILL.md`
  - Expected: file exists, non-zero size
- [ ] Commit: `feat(wiki-init): add wiki-init skill`

---

## Phase 2: Apply production init to current repository

**Implements:** FR-2, FR-3, FR-4, FR-5 | **Satisfies:** AC-2.1–AC-2.5, AC-3.1–AC-3.3, AC-4.1–AC-4.3, AC-5.1–AC-5.2

This phase applies the init workflow to the current repo — both producing the "prepare for production" changes and validating the skill's logic against a real case.

> **Interactive step at 2.4:** the executor must ask the user for their wiki topic, entities, and concepts before writing stubs, index, and log.

### 2.1 Backup existing raw/ and wiki/

- [ ] Run backup:
  ```bash
  mkdir -p .backup/raw .backup/wiki
  cp -r raw/. .backup/raw/
  cp -r wiki/. .backup/wiki/
  ```
- [ ] Verify:
  ```bash
  find .backup/raw .backup/wiki -type f | wc -l
  ```
  - Expected: count > 0 (current repo has 6 PDFs in raw/ and ~30 wiki pages)
- [ ] If either `cp` fails: abort Phase 2 immediately, report error, make no further changes.

### 2.2 Update .gitignore

- [ ] Check current state:
  ```bash
  grep -F 'raw/*' .gitignore && echo "raw/* present" || echo "raw/* absent"
  grep -F '.backup/' .gitignore && echo ".backup/ present" || echo ".backup/ absent"
  ```
- [ ] Append missing lines to `.gitignore` (use the Edit tool, not `>>`):
  ```
  
  # Wiki raw sources
  raw/*
  !raw/.gitkeep
  
  # Wiki backup
  .backup/
  ```
- [ ] Verify no duplicate lines:
  ```bash
  grep -c 'raw/\*' .gitignore
  grep -c '\.backup/' .gitignore
  ```
  - Expected: each count is exactly 1

### 2.3 Clean wiki subdirectories and raw/

- [ ] Run cleanup:
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
- [ ] Verify each dir contains only `.gitkeep`:
  ```bash
  find wiki/concepts wiki/entities wiki/sources wiki/analyses raw -type f | sort
  ```
  - Expected: exactly 5 lines, each ending in `.gitkeep`
- [ ] Verify protected files untouched:
  ```bash
  ls wiki/.obsidian/ && ls CLAUDE.md && ls skills/
  ```
  - Expected: all present

### 2.4 Collect topic from user — create stubs

- [ ] **Ask the user** (interactive — do not skip):
  1. "What is this wiki about? Describe the topic or project in 1–3 sentences."
  2. "Name up to 5 key entities this wiki should track. Separate with commas, or press Enter to skip."
  3. "Name up to 5 key concepts this wiki should track. Separate with commas, or press Enter to skip."
- [ ] For each entity name: derive slug, write `wiki/entities/<slug>.md`:
  ```markdown
  # <Entity Name>

  _Stub — to be filled by wiki-ingest._

  ## Notes

  ```
- [ ] For each concept name: derive slug, write `wiki/concepts/<slug>.md`:
  ```markdown
  # <Concept Name>

  _Stub — to be filled by wiki-ingest._

  ## Notes

  ```

### 2.5 Write wiki/index.md and wiki/log.md

- [ ] Write `wiki/index.md` (full file, not append):
  ```markdown
  # <Topic Title>

  <Topic description from user>

  ## Sources

  ## Entities

  - [<Entity Name>](entities/<slug>.md) — (stub)
  [... one line per entity]

  ## Concepts

  - [<Concept Name>](concepts/<slug>.md) — (stub)
  [... one line per concept]

  ## Analyses

  ```
- [ ] Write `wiki/log.md` (full file, not append):
  ```markdown
  ## [2026-05-24] init | <Topic Title>
  Backed up: raw/ and wiki/ (N files total) → .backup/
  Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
  Stubs created: <list or "none">
  .gitignore: updated
  ```
- [ ] Verify `wiki/index.md` has no content from the previous VLM topic:
  ```bash
  grep -i "visual\|vlm\|covt\|spatial" wiki/index.md || echo "clean"
  ```
  - Expected: `clean`

### 2.6 Rebuild qmd index

- [ ] Run:
  ```bash
  qmd update --collection wiki 2>/dev/null || true
  ```
- [ ] Verify index reflects new state:
  ```bash
  qmd status --collection wiki 2>/dev/null || true
  ```
  - Expected: reports updated collection with page count matching stubs + index
- [ ] Commit all production changes:
  ```
  feat(wiki-init): apply production init — backup, clean, scaffold new topic
  ```

---

## Phase 3: Integration Verification

**Implements:** All FRs | **Satisfies:** All ACs

- [ ] AC-2.1: `.backup/raw/` and `.backup/wiki/` both exist and are non-empty:
  ```bash
  find .backup/raw -type f | head -3
  find .backup/wiki -type f | head -3
  ```
- [ ] AC-2.3: All four wiki subdirs contain only `.gitkeep`:
  ```bash
  find wiki/concepts wiki/entities wiki/sources wiki/analyses -type f | sort
  ```
- [ ] AC-2.4: `raw/` contains only `.gitkeep`:
  ```bash
  find raw -type f | sort
  ```
- [ ] AC-3.1 + AC-3.2: `.gitignore` contains both sections:
  ```bash
  grep 'raw/\*' .gitignore
  grep '!raw/.gitkeep' .gitignore
  grep '\.backup/' .gitignore
  ```
- [ ] AC-4.2: `wiki/index.md` starts with topic heading:
  ```bash
  head -3 wiki/index.md
  ```
- [ ] AC-4.3: `wiki/log.md` contains exactly one `##` entry:
  ```bash
  grep -c '^## ' wiki/log.md
  ```
  - Expected: `1`
- [ ] AC-1.4 (if stubs were created): each stub file has correct format:
  ```bash
  head -4 wiki/entities/<slug>.md   # or wiki/concepts/<slug>.md
  ```
  - Expected: H1 title, then `_Stub — to be filled by wiki-ingest._`, then blank, then `## Notes`
- [ ] AC-5.2: qmd returns results for stub pages:
  ```bash
  qmd search "stub" --collection wiki --json --limit 3 2>/dev/null || true
  ```

---

## Quickstart Validation

After both phases are complete, a new user cloning this repo should:

1. Open the repo — no example VLM content in `wiki/` anywhere.
2. Check `wiki/index.md` — sees the new topic heading and stub entries.
3. Check `wiki/log.md` — sees a single init entry, nothing else.
4. Check `.gitignore` — `raw/*` and `.backup/` are excluded.
5. Drop a PDF into `raw/` — git status shows it as ignored (not staged).
6. Invoke `wiki-init` on a fresh clone — skill runs all 8 steps, produces the same clean state.
