---
name: wiki-nlm-sync
description: >
  Manages bidirectional content sync between the local wiki and Google NotebookLM.
  Use when the user wants to push files from raw/<topic>/ or wiki pages into a
  NotebookLM notebook, pull generated artifacts back into raw/<topic>/, discover
  new web/Drive sources for a notebook, sync stale Drive sources, authenticate to
  NotebookLM, create and register a new topic notebook, or list all registered
  notebooks. Triggers on: "push to notebooklm", "pull from notebooklm",
  "sync to notebooklm", "discover sources", "drive sync", "create notebook",
  "register notebook", "list notebooks", "authenticate notebooklm",
  "nlm sync", "nlm push", "nlm pull", "nlm discover", "nlm drive-sync".
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

Then verify the session is valid:

```bash
nlm login --check
```

If the check fails, stop and tell the user:
> "Session invalid — run `nlm login [--profile <name>]` to authenticate, then retry.
> Note: NotebookLM sessions expire in ~20 minutes."

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
| "authenticate", "login", "nlm login" | Authenticate workflow |
| "push", "sync to notebooklm" | Push workflow |
| "pull", "download artifact" | Pull workflow |
| "discover", "find sources", "nlm research" | Discover workflow |
| "drive sync", "stale sources" | Drive-sync workflow |
| "create notebook", "register notebook" | Create notebook |
| "list notebooks", "show notebooks" | List notebooks |

---

## Authenticate workflow

Establish or refresh a NotebookLM session, optionally with a named profile.

### Steps

1. **Ask for profile** (optional): "Which profile? (press Enter for default)"

2. **Run login**:
   ```bash
   nlm login                      # default profile
   nlm login --profile <name>     # named profile
   ```
   A browser window will open — log in with your Google account.

3. **Confirm auth status**:
   ```bash
   nlm auth status
   nlm auth list    # shows all profiles
   ```
   Display the active profile and session status.

4. **Surface session lifetime warning**:
   > "Authenticated. Note: sessions expire in ~20 minutes — re-run this workflow if commands start failing."

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

3. **Offer source description**: Before selection, ask:
   > "Want a summary of any artifact before selecting? (enter number or 'no')"
   If yes:
   ```bash
   nlm source describe <artifact-id>
   ```
   Display AI summary + keywords. Repeat for any artifact the user asks about.

4. **User selects**: Ask which artifacts to pull (numbers, "all", or "none").

5. **Download each selected artifact**:
   - Construct filename: `nlm-<artifact-type>-<YYYY-MM-DD>.md`
   - If that filename already exists in `raw/<topic>/`, append a counter:
     `nlm-report-2026-05-22-2.md`
   - Create `raw/<topic>/` if it does not exist
   - Retrieve and save content as-is:
     ```bash
     nlm source content <artifact-id>
     ```
     Write output to `raw/<topic>/<filename>`.

6. **Prompt ingest**: After saving:
   > "Pulled to `raw/<topic>/`. To ingest into the wiki, run `wiki-ingest` and
   > specify `raw/<topic>/<filename>`."

---

## Discover workflow

Find new web or Drive sources and add them to a NotebookLM notebook.

### Steps

1. **Resolve topic**: Look up topic in `wiki/nlm-notebooks.md`. If not found, list valid
   topics and stop.

2. **Collect search query**: Ask the user what to search for.

3. **Choose research mode**:
   - (a) Fast web search (default, ~30s)
   - (b) Deep web search (`--mode deep`, ~5min)
   - (c) Google Drive search (`--source drive`)

4. **Start research**:
   ```bash
   nlm research start "<query>" --notebook-id <alias>               # fast web
   nlm research start "<query>" --notebook-id <alias> --mode deep   # deep web
   nlm research start "<query>" --notebook-id <alias> --source drive # Drive
   ```
   Capture the returned task ID.

5. **Poll for completion** (every 10s):
   ```bash
   nlm research status <alias> --task-id <task-id>
   ```
   Display progress message while polling: "Researching… (checking every 10s)"

6. **Show results**: Display discovered sources with numbered list. Ask user to select
   which to import (numbers, "all", or "none").

7. **Import selected sources**:
   ```bash
   nlm research import <alias> <task-id>                        # all
   nlm research import <alias> <task-id> --indices <n,n,...>    # specific
   ```

8. **Update registry**: Set "Last Synced" to today in `wiki/nlm-notebooks.md`.

9. **Report**: Summarise how many sources were imported.

---

## Drive-sync workflow

Refresh stale Google Drive sources in a notebook.

### Steps

1. **Resolve topic**: Look up topic in `wiki/nlm-notebooks.md`. If not found, list valid
   topics and stop.

2. **Check stale sources**:
   ```bash
   nlm source stale <alias>
   ```
   If none stale:
   > "No stale Drive sources found — all sources are up to date."
   Stop.

3. **Show stale list**: Display sources that need refreshing with numbered list. Ask:
   > "Sync all stale sources, or select specific ones? (all / numbers)"

4. **Sync**:
   ```bash
   nlm source sync <alias> --confirm                              # all
   nlm source sync <alias> --source-ids <id,id,...> --confirm    # specific
   ```

5. **Update registry**: Set "Last Synced" to today in `wiki/nlm-notebooks.md`.

6. **Report**: Summarise which sources were refreshed.

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
3. Show active profile via `nlm auth list`.
4. Note any row where "Last Synced" is "—" as never synced.
