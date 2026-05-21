# Tasks: Wiki ↔ NotebookLM Integration

**Spec:** `docs/specs/001-wiki-notebooklm/spec.md`  
**Plan:** `docs/specs/001-wiki-notebooklm/plan.md`  
**Date:** 2026-05-22  

`[P]` = safe to run concurrently with other `[P]` tasks in the same group (different files, no shared deps).

---

## Phase 1 — Registry + wiki-query gap suggestion

### T01 — Verify registry does not exist yet

```bash
ls /Users/hllj/Projects/LLM-Wiki-Notebook/wiki/nlm-notebooks.md
```

Expected: `No such file or directory`

---

### T02 — Create `wiki/nlm-notebooks.md`

Create the file at `/Users/hllj/Projects/LLM-Wiki-Notebook/wiki/nlm-notebooks.md` with this exact content:

```markdown
# NotebookLM Notebook Registry

_Maintained by wiki-nlm-sync. Maps local `raw/<topic>/` folders to NotebookLM notebooks._

| Topic Folder | Notebook Title | Notebook ID (alias) | Last Synced |
|---|---|---|---|
```

---

### T03 — Verify registry file

```bash
cat /Users/hllj/Projects/LLM-Wiki-Notebook/wiki/nlm-notebooks.md
```

Expected: file contains the header, italicised description, and empty table with four columns.

---

### T04 — Verify current wiki-query gap section (pre-change baseline)

```bash
grep -n "gap" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md
```

Expected: line containing `"The wiki doesn't have strong coverage"` and `wiki gap` — confirms step 5 exists and does NOT yet mention `wiki-nlm-research`.

---

### T05 — Add NotebookLM escalation hint to `wiki-query/SKILL.md` step 5

In `/Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md`, locate step 5's existing gap message block ending with:

```
> "The wiki doesn't have strong coverage of this topic (best match score: 0.XX). This looks like a gap — want me to web-search and ingest a new source, or do you have a document to add to `raw/`?"
```

Append the following paragraph immediately after that block (before the line starting `This is valuable signal:`):

```markdown
If the topic is related to a registered NotebookLM notebook (check `wiki/nlm-notebooks.md`), also include:
> "wiki gap detected — consider running wiki-nlm-research: '<question>' --topic <relevant-topic>"

Replace `<relevant-topic>` with the matching Topic Folder from the registry, or leave as a placeholder if the registry is empty or no topic matches.
```

---

### T06 — Verify wiki-query gap section after change

```bash
grep -A 5 "wiki gap detected" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md
```

Expected: output shows the new `wiki gap detected` line and the `--topic` placeholder text. Existing gap message is still present above it.

---

## Phase 2 — `wiki-nlm-sync` skill  `[P with Phase 3]`

### T07 — Verify skill directory does not exist yet

```bash
ls /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/
```

Expected: `No such file or directory`

---

### T08 — Create `skills/wiki-nlm-sync/SKILL.md`

Create the directory and file at `/Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md` with this exact content:

````markdown
---
name: wiki-nlm-sync
description: >
  Manages bidirectional content sync between the local wiki and Google NotebookLM.
  Use when the user wants to push files from raw/<topic>/ or wiki pages into a
  NotebookLM notebook, pull generated artifacts (reports, transcripts, mind maps)
  back into raw/<topic>/, create and register a new topic notebook, or list all
  registered notebooks. Triggers on: "push to notebooklm", "pull from notebooklm",
  "sync to notebooklm", "create notebook", "register notebook", "list notebooks",
  "nlm sync", "nlm push", "nlm pull".
---

# Wiki ↔ NotebookLM Sync

Manages all content movement between the local wiki and Google NotebookLM notebooks.
Uses the `nlm` CLI for all NotebookLM operations. The registry at `wiki/nlm-notebooks.md`
is the single source of truth for topic ↔ notebook mapping.

## Prerequisites check

Before any `nlm` operation, verify the CLI is installed:

```bash
nlm --version
```

If the command fails, stop and tell the user:
> "`nlm` CLI not found. Install it with: `uv tool install notebooklm-mcp-cli`"

## Registry: wiki/nlm-notebooks.md

The registry maps `raw/<topic>/` folders to NotebookLM notebooks:

```
| Topic Folder | Notebook Title | Notebook ID (alias) | Last Synced |
|---|---|---|---|
| vlm-research | VLM Research | vlm-research | 2026-05-22 |
```

If the file does not exist, create it with the header and empty table before proceeding.

## Workflow routing

| User intent | Workflow |
|---|---|
| "push", "sync to notebooklm" | Push workflow |
| "pull", "download artifact" | Pull workflow |
| "create notebook", "register notebook" | Create notebook |
| "list notebooks", "show notebooks" | List notebooks |

---

## Push workflow

Push local content into a NotebookLM notebook as sources.

### Steps

1. **Resolve topic**: Ask the user for the topic name. Look it up in `wiki/nlm-notebooks.md`
   (case-insensitive match on Topic Folder column). If not found, list all registered
   Topic Folder values and stop.

2. **Select content type**: Ask the user what to push:
   - (a) Files from `raw/<topic>/`
   - (b) Wiki pages from `wiki/`
   - (c) Both

3. **List candidates**: Show available files. Skip PDFs with a per-file warning:
   > "`<filename>.pdf` — skipped (PDFs require manual upload in the NotebookLM UI)"

4. **Confirm selection**: Ask the user to confirm which files to push.

5. **Check for existing sources**:
   ```bash
   nlm source list <alias> --json
   ```
   For any candidate whose title matches an existing source, warn:
   > "`<filename>` may already be a source in this notebook. Skip or push anyway?"

6. **Push each confirmed file**:
   ```bash
   nlm source add <alias> --text "<file content>" --title "<filename or page title>"
   ```
   Report success or failure per file.

7. **Update registry**: Set "Last Synced" to today (YYYY-MM-DD) in `wiki/nlm-notebooks.md`.

8. **Report**: Summarise sources added and files skipped.

---

## Pull workflow

Download a generated artifact from NotebookLM into `raw/<topic>/`.

### Steps

1. **Resolve topic**: Look up topic in `wiki/nlm-notebooks.md`. If not found, list valid
   topics and stop.

2. **List artifacts**:
   ```bash
   nlm studio status <alias>
   ```
   Display numbered list of available artifacts. If none:
   > "No generated artifacts available in this notebook yet."
   Stop.

3. **User selects**: Ask which artifacts to pull (numbers, "all", or "none").

4. **Download each selected artifact**:
   - Construct filename: `nlm-<artifact-type>-<YYYY-MM-DD>.md`
   - If that filename already exists in `raw/<topic>/`, append a counter:
     `nlm-report-2026-05-22-2.md`
   - Create `raw/<topic>/` if it does not exist
   - Retrieve and save content as-is:
     ```bash
     nlm source content <artifact-id>
     ```
     Write output to `raw/<topic>/<filename>`.

5. **Prompt ingest**: After saving:
   > "Pulled to `raw/<topic>/`. To ingest into the wiki, run `wiki-ingest` and
   > specify `raw/<topic>/<filename>`."

---

## Create notebook

Register a new topic notebook in the local registry.

### Steps

1. **Collect inputs**: Ask for topic folder name (kebab-case) and notebook title.

2. **Create notebook**:
   ```bash
   nlm notebook create "<Notebook Title>"
   ```
   Capture the returned notebook ID.

3. **Set alias**:
   ```bash
   nlm alias set <topic-folder> <notebook-id>
   ```

4. **Create raw folder if missing**:
   ```bash
   mkdir -p raw/<topic-folder>
   ```

5. **Register in wiki/nlm-notebooks.md**: Append new row:
   ```
   | <topic-folder> | <Notebook Title> | <topic-folder> | — |
   ```

6. **Confirm**: Report the new registration and the `raw/<topic>/` folder path.

---

## List notebooks

Display all registered notebooks.

### Steps

1. Read `wiki/nlm-notebooks.md`. If missing, say so and offer to initialise it.
2. Display the table as formatted markdown.
3. Note any row where "Last Synced" is "—" as never synced.
````

---

### T09 — Verify `wiki-nlm-sync/SKILL.md` content

```bash
grep "name: wiki-nlm-sync" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md
grep "Push workflow" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md
grep "Pull workflow" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md
grep "Create notebook" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md
grep "List notebooks" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md
```

Expected: all five `grep` calls return matches.

---

### T10 — Create `.claude-plugin/skills/wiki-nlm-sync` symlink

```bash
ln -s ../../skills/wiki-nlm-sync /Users/hllj/Projects/LLM-Wiki-Notebook/.claude-plugin/skills/wiki-nlm-sync
```

---

### T11 — Verify symlink

```bash
ls -la /Users/hllj/Projects/LLM-Wiki-Notebook/.claude-plugin/skills/wiki-nlm-sync
```

Expected: `wiki-nlm-sync -> ../../skills/wiki-nlm-sync`

---

## Phase 3 — `wiki-nlm-research` skill  `[P with Phase 2]`

### T12 — Verify skill directory does not exist yet

```bash
ls /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/
```

Expected: `No such file or directory`

---

### T13 — Create `skills/wiki-nlm-research/SKILL.md`

Create the directory and file at `/Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/SKILL.md` with this exact content:

````markdown
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
> "NotebookLM session expired. Run `nlm login` to re-authenticate, then retry."

### 3. List available artifacts

```bash
nlm studio status <alias>
```

Display a numbered list of available artifacts (reports, transcripts, mind maps, etc.).

If none available:
> "No generated artifacts available in this notebook yet."
Skip to step 5.

### 4. Offer to pull artifacts

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
2. A clear list of available artifacts
3. Any selected artifacts saved to `raw/<topic>/`, ready for `wiki-ingest`
4. A log entry recording what happened

Do not auto-ingest. Do not modify wiki pages directly. Surface results; let the
user decide what enters the wiki.
````

---

### T14 — Verify `wiki-nlm-research/SKILL.md` content

```bash
grep "name: wiki-nlm-research" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/SKILL.md
grep "Resolve topic" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/SKILL.md
grep "Log the session" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/SKILL.md
grep "nlm-research" /Users/hllj/Projects/LLM-Wiki-Notebook/wiki/log.md || echo "log.md pattern not in skill (expected)"
```

Expected: first three greps match; fourth confirms log format is in the skill.

---

### T15 — Create `.claude-plugin/skills/wiki-nlm-research` symlink

```bash
ln -s ../../skills/wiki-nlm-research /Users/hllj/Projects/LLM-Wiki-Notebook/.claude-plugin/skills/wiki-nlm-research
```

---

### T16 — Verify symlink

```bash
ls -la /Users/hllj/Projects/LLM-Wiki-Notebook/.claude-plugin/skills/wiki-nlm-research
```

Expected: `wiki-nlm-research -> ../../skills/wiki-nlm-research`

---

## Phase 4 — Integration verification

### T17 — Verify all new files are in place

```bash
ls /Users/hllj/Projects/LLM-Wiki-Notebook/wiki/nlm-notebooks.md
ls /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/SKILL.md
ls /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/SKILL.md
ls -la /Users/hllj/Projects/LLM-Wiki-Notebook/.claude-plugin/skills/wiki-nlm-sync
ls -la /Users/hllj/Projects/LLM-Wiki-Notebook/.claude-plugin/skills/wiki-nlm-research
```

Expected: all five commands succeed with no "No such file" errors.

---

### T18 — Verify wiki-ingest and wiki-lint are untouched

```bash
git diff skills/wiki-ingest/ skills/wiki-lint/
```

Expected: no output (no changes to either skill).

---

### T19 — Verify plugin.json is untouched

```bash
git diff .claude-plugin/plugin.json
```

Expected: no output.

---

### T20 — Run `/reload-plugins` in Claude Code

In the Claude Code session, run:

```
/reload-plugins
```

Expected: output includes both `wiki-nlm-sync` and `wiki-nlm-research` in the loaded skills count. No errors.

---

### T21 — Commit all changes

```bash
git add wiki/nlm-notebooks.md \
        skills/wiki-nlm-sync/SKILL.md \
        skills/wiki-nlm-research/SKILL.md \
        .claude-plugin/skills/wiki-nlm-sync \
        .claude-plugin/skills/wiki-nlm-research \
        skills/wiki-query/SKILL.md

git commit -m "feat(wiki-nlm): add wiki-nlm-sync and wiki-nlm-research skills

- wiki-nlm-sync: bidirectional push/pull/create/list between raw/<topic>/ and NotebookLM
- wiki-nlm-research: gap-driven query skill triggered from wiki-query gaps
- wiki/nlm-notebooks.md: topic ↔ notebook registry
- wiki-query: additive NotebookLM escalation hint in step 5 gap message

Closes #001-wiki-notebooklm

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Expected: commit succeeds, all 6 files included.
