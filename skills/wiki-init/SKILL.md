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

```bash
mkdir -p .backup/raw .backup/wiki
cp -r raw/. .backup/raw/ 2>&1
cp -r wiki/. .backup/wiki/ 2>&1
```

Count backed-up files:

```bash
find .backup/raw .backup/wiki -type f | wc -l
```

Report: "Backed up N files to `.backup/` (raw/ and wiki/)."

**If either `cp` command fails:** Stop immediately. Do not delete or overwrite any
file. Report: "Backup failed: <error>. Aborting init — no files have been modified."

### 3. Update .gitignore

Check if `.gitignore` already contains `raw/*`:

```bash
grep -qF 'raw/*' .gitignore 2>/dev/null && echo "present" || echo "absent"
```

- If **absent**: append to `.gitignore`:
  ```
  
  # Wiki raw sources
  raw/*
  !raw/.gitkeep
  ```

Check for `.backup/` in `.gitignore`:

```bash
grep -qF '.backup/' .gitignore 2>/dev/null && echo "present" || echo "absent"
```

- If **absent**: append to `.gitignore`:
  ```
  
  # Wiki backup
  .backup/
  ```

Check for `.qmd/` in `.gitignore`:

```bash
grep -qF '.qmd/' .gitignore 2>/dev/null && echo "present" || echo "absent"
```

- If **absent**: append to `.gitignore`:
  ```
  
  # qmd local index
  .qmd/
  ```

- If all lines were already present: report "`.gitignore` already up to date."
- If `.gitignore` does not exist: create it containing only the three sections above.

### 4. Clean wiki subdirectories and raw/

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
- `wiki/index.md` and `wiki/log.md` — overwritten in Steps 6 and 7, not deleted here
- `CLAUDE.md`, `README.md`, `llm-wiki.md`, `skills/`, `docs/`

### 5. Create stub pages

For each entity name provided in Q2:

Write `wiki/entities/<slug>.md`:
```markdown
# <Entity Name>

_Stub — to be filled by wiki-ingest._

## Notes

```

For each concept name provided in Q3:

Write `wiki/concepts/<slug>.md`:
```markdown
# <Concept Name>

_Stub — to be filled by wiki-ingest._

## Notes

```

If the user provided no entities or no concepts, skip that category silently.

### 6. Write wiki/index.md

Write the complete file (overwrites the old index):

```markdown
# <Topic Title>

<User's topic description verbatim from Q1>

## Sources

## Entities

- [<Entity Name>](entities/<slug>.md) — (stub)

## Concepts

- [<Concept Name>](concepts/<slug>.md) — (stub)

## Analyses

```

If no stubs were created for Entities or Concepts, leave that section's body empty
(keep the `##` header).

### 7. Write wiki/log.md

Write the complete file (this is a reset — do not append to the old log):

```markdown
## [YYYY-MM-DD] init | <Topic Title>
Backed up: raw/ and wiki/ (N files total) → .backup/
Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
Stubs created: <comma-separated list of stub page filenames, or "none">
.gitignore: <"updated" or "already up to date">
```

### 8. Set up qmd project-local index and collection

`<collection-slug>` is the kebab-case slug of the topic title derived in Step 1
(e.g. topic title "Large Language Models" → slug `large-language-models`).

#### 8a. Initialize project-local index

Run from the repo root:

```bash
qmd init 2>/dev/null || true
```

Verify `.qmd/` was created:

```bash
ls .qmd/ 2>/dev/null && echo "ok" || echo "missing"
```

If missing, warn: "`.qmd/` folder was not created — run `qmd init` manually before
using search commands."

#### 8b. Register the wiki collection

Check whether the collection is already registered:

```bash
qmd collection list 2>/dev/null || true
```

If `<collection-slug>` does not appear in the output, add it:

```bash
qmd collection add ./wiki --name <collection-slug> 2>/dev/null || true
```

#### 8c. Confirm setup

```bash
qmd collection list 2>/dev/null || true
```

Report the output so the user can confirm `<collection-slug>` is listed.

#### 8d. Build the index

```bash
qmd update --collection <collection-slug> 2>/dev/null || true
```

If output before the forced exit-0 suggests failure, warn: "qmd index update may
have failed — run `qmd update --collection <collection-slug>` manually if searches
return stale results."

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
- `.gitignore` excludes `raw/*`, `.backup/`, and `.qmd/`.
- `.qmd/` exists in the repo root (project-local search index).
- `<collection-slug>` appears in `qmd collection list` output.
- `qmd status --collection <collection-slug>` shows a freshly updated index.

The human can now run `wiki-ingest` on any source to begin building real content
into the scaffold.
