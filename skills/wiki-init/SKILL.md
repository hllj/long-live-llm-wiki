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

Read the template file at `skills/wiki-init/CLAUDE.md.example` using the Read tool. This file is the reference CLAUDE.md from this project and contains the complete operational schema.

Make the following substitutions throughout the content before writing:
- Replace every occurrence of `--collection wiki` with `--collection <COLLECTION_SLUG>`
- Replace the generic topic description in "What this repo is" with the actual TOPIC_TITLE and TOPIC_DESCRIPTION
- Replace the collection name in the "Search tooling" intro line with `<COLLECTION_SLUG>`
- Replace the `qmd collection add` command's collection name with `<COLLECTION_SLUG>`
- Update the "Scope" section at the bottom to name TOPIC_TITLE explicitly

Write the result to `CLAUDE.md` at the repo root using the Write tool.

After writing, verify substitution was successful:

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
- `CLAUDE.md` is at the repo root, generated from `skills/wiki-init/CLAUDE.md.example` with qmd commands referencing `<COLLECTION_SLUG>` (not the literal string `wiki`).
- `.gitignore` excludes `raw/*` and `.qmd/`.
- `.qmd/` exists in the repo root (project-local search index).
- `<COLLECTION_SLUG>` appears in `qmd collection list` output.
- `qmd status --collection <COLLECTION_SLUG>` shows a freshly updated index.

The human can now run `wiki-ingest` on any source to begin building real content
into the scaffold.
