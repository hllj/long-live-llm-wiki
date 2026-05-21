# Plan: Wiki ↔ NotebookLM Integration

**Spec:** `docs/specs/001-wiki-notebooklm/spec.md`  
**Date:** 2026-05-22  
**Status:** Approved  
**Version:** 1.1.0 — adds auth, profiles, discover, source-describe, drive-sync  

---

## Goal

Implement two Claude Code skills (`wiki-nlm-sync` and `wiki-nlm-research`) that bridge the local wiki and Google NotebookLM, plus an additive gap suggestion in `wiki-query`. No runtime code — all deliverables are SKILL.md files and one markdown registry.

---

## Architecture

- **No new runtime code.** All deliverables are SKILL.md instruction files and one markdown registry file.
- **`wiki/nlm-notebooks.md`** is the single source of truth mapping `raw/<topic>/` ↔ NotebookLM notebook alias.
- **`nlm` CLI** (`notebooklm-mcp-cli`) is the only external dependency — assumed installed and authenticated by the user.
- **`wiki-ingest` is untouched.** It processes whatever lands in `raw/<topic>/` as always.
- Plugin registration uses symlinks in `.claude-plugin/skills/` pointing to `../../skills/<name>` — same pattern as the three existing skills.

> **Spec note:** The Non-Goals section says "no modification to wiki-query" while FR-5 explicitly specifies an additive gap suggestion in `wiki-query/SKILL.md`. FR-5 is more specific and reflects the agreed design — an additive-only addition to step 5 of the existing skill is implemented. No existing behaviour is removed or replaced.

---

## Tech Stack

| Concern | Choice | Justification |
|---|---|---|
| Skill format | SKILL.md (YAML frontmatter + markdown) | Matches all existing wiki skills |
| CLI | `nlm` (notebooklm-mcp-cli) | Established, already referenced in design |
| Registry | `wiki/nlm-notebooks.md` (markdown table) | Zero dependencies; readable by both human and Claude |
| Plugin registration | Symlink in `.claude-plugin/skills/` | Matches existing `wiki-ingest`, `wiki-query`, `wiki-lint` pattern |

---

## File Structure

```
skills/
├── wiki-nlm-sync/
│   └── SKILL.md          ← NEW
├── wiki-nlm-research/
│   └── SKILL.md          ← NEW
└── wiki-query/
    └── SKILL.md          ← MODIFIED (additive only — step 5 gap message)

.claude-plugin/skills/
├── wiki-nlm-sync         ← NEW symlink → ../../skills/wiki-nlm-sync
└── wiki-nlm-research     ← NEW symlink → ../../skills/wiki-nlm-research

wiki/
└── nlm-notebooks.md      ← NEW (empty registry, created in Phase 1)
```

Files NOT touched: `skills/wiki-ingest/`, `skills/wiki-lint/`, `.claude-plugin/plugin.json`, `wiki/index.md`, `wiki/log.md`.

---

## Phases

### Phase 1 — Registry + wiki-query gap suggestion

Creates the notebook registry and adds the NotebookLM escalation hint to wiki-query's gap handling.

**Covers:** FR-1, FR-5, US-1

#### 1.1 Create `wiki/nlm-notebooks.md`

Create the empty registry file:

```markdown
# NotebookLM Notebook Registry

_Maintained by wiki-nlm-sync. Maps local `raw/<topic>/` folders to NotebookLM notebooks._

| Topic Folder | Notebook Title | Notebook ID (alias) | Last Synced |
|---|---|---|---|
```

#### 1.2 Update `skills/wiki-query/SKILL.md` — additive gap suggestion

In the existing **step 5 (Handle low-confidence results)** section, append the following paragraph immediately after the existing gap message block:

```markdown
If the topic is related to a registered NotebookLM notebook (check `wiki/nlm-notebooks.md`), also suggest:
> "wiki gap detected — consider running wiki-nlm-research: '<question>' --topic <relevant-topic>"

Replace `<relevant-topic>` with the matching Topic Folder from the registry, or leave as a placeholder if the registry is empty or no topic matches.
```

---

### Phase 2 — `wiki-nlm-sync` skill

Creates the bidirectional sync skill covering push, pull, notebook creation, and listing.

**Covers:** FR-1, FR-2, FR-3, FR-4, FR-6, US-5, US-6, US-7, all pull error scenarios.

#### 2.1 Create `skills/wiki-nlm-sync/SKILL.md`

```markdown
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
```

#### 2.2 Create `.claude-plugin/skills/wiki-nlm-sync` symlink

```bash
ln -s ../../skills/wiki-nlm-sync .claude-plugin/skills/wiki-nlm-sync
```

---

### Phase 3 — `wiki-nlm-research` skill

Creates the gap-driven research skill.

**Covers:** FR-2, FR-4, FR-6, US-2, US-3, US-4, all research error scenarios.

#### 3.1 Create `skills/wiki-nlm-research/SKILL.md`

```markdown
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
```

#### 3.2 Create `.claude-plugin/skills/wiki-nlm-research` symlink

```bash
ln -s ../../skills/wiki-nlm-research .claude-plugin/skills/wiki-nlm-research
```

---

### Phase 2b — Rewrite `wiki-nlm-sync` with v1.1.0 additions

Rewrites the existing `skills/wiki-nlm-sync/SKILL.md` to add:
- Proactive auth check (`nlm login --check`) at the top of every workflow
- Dedicated **authenticate** sub-workflow (FR-7, FR-8, US-8, US-9)
- **Discover** sub-workflow — `nlm research` web/drive source discovery (FR-9, US-10)
- **Drive-sync** sub-workflow — `nlm source stale` / `nlm source sync` (FR-11, US-12)
- `nlm source describe` offered before artifact selection in pull workflow (FR-10, US-11)
- Profile support (`--profile`) in all auth steps (FR-8)

Full rewrite of `skills/wiki-nlm-sync/SKILL.md`. Symlink unchanged.

---

### Phase 3b — Rewrite `wiki-nlm-research` with v1.1.0 additions

Rewrites the existing `skills/wiki-nlm-research/SKILL.md` to add:
- Proactive auth check before any `nlm` operation (FR-7, US-8)
- `nlm source describe` offered before artifact pull (FR-10, US-11)
- Profile support in auth hint messages (FR-8)

Full rewrite of `skills/wiki-nlm-research/SKILL.md`. Symlink unchanged.

---

### Phase 4 — Integration verification

Manual end-to-end walkthrough to confirm the full pipeline works.

#### 4.1 Verify plugin registration

After creating both symlinks, run `/reload-plugins` in Claude Code and confirm both skills appear in `/skills` output.

#### 4.2 Verify registry creation

Trigger `wiki-nlm-sync` → "list notebooks" — confirm it creates `wiki/nlm-notebooks.md` if missing and displays the empty table.

#### 4.3 Verify gap suggestion in wiki-query

Ask a question with no wiki coverage — confirm the response includes the `wiki-nlm-research` suggestion with `--topic` placeholder.

#### 4.4 Verify full pipeline (requires `nlm` installed)

```
wiki-query "<unknown topic>"
  → gap message with wiki-nlm-research suggestion
wiki-nlm-sync → create notebook → register topic
wiki-nlm-sync → push → push a raw/ file to the notebook
wiki-nlm-research "<question>" --topic <topic>
  → cited answer displayed
  → artifact list shown
  → pull one artifact → saved to raw/<topic>/
  → log entry appended to wiki/log.md
wiki-ingest raw/<topic>/<artifact>
  → new wiki page created
```

---

## Self-Review

**Spec coverage:**
- FR-1 (registry) → Phase 1.1 ✓
- FR-2 (topic resolution) → Phase 2 push step 1, Phase 3 step 1 ✓
- FR-3 (push behavior) → Phase 2 push steps 5–6 ✓
- FR-4 (pull behavior) → Phase 2 pull step 4, Phase 3 step 4 ✓
- FR-5 (gap suggestion) → Phase 1.2 ✓
- FR-6 (nlm CLI check) → Phase 2 prerequisites, Phase 3 prerequisites ✓
- US-1 → Phase 1.2 ✓ | US-2 → Phase 3 steps 1–2 ✓ | US-3 → Phase 3 steps 3–4 ✓
- US-4 → Phase 3 step 5 ✓ | US-5 → Phase 2 push ✓ | US-6 → Phase 2 create ✓
- US-7 → Phase 2 list ✓

All error scenarios from spec covered: topic not found (Phase 2 step 1, Phase 3 step 1), nlm not installed (prerequisites blocks), auth expired (Phase 3 step 2), no artifacts (Phase 2 pull step 2, Phase 3 step 3), raw/ missing (Phase 2 pull step 4, Phase 3 step 4), PDF in push (Phase 2 push step 3), duplicate filename (Phase 2 pull step 4, Phase 3 step 4).

**Placeholder scan:** None found.

**Type consistency:** `nlm` CLI commands consistent across Phase 2 and Phase 3.
