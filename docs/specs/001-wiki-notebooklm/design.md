# Design: Wiki ↔ NotebookLM Integration

**Spec:** 001-wiki-notebooklm  
**Date:** 2026-05-22  
**Status:** Draft — awaiting spec phase  

---

## Problem

`wiki-query` answers questions from the local wiki. When knowledge is insufficient (score < 0.3), the user has no structured path to research the gap, pull external knowledge in, and grow the wiki. NotebookLM can fill this gap — but there's no bridge between the two systems.

---

## Goals

- Let `wiki-query` gaps escalate to NotebookLM research without changing the existing query skill.
- Push content from `raw/<topic>/` or `wiki/` into a matching NotebookLM notebook — selectively, per session.
- Pull NotebookLM-generated artifacts (Q&A answers, reports, podcast transcripts, mind maps) back into `raw/<topic>/` for ingestion.
- Keep `wiki-ingest` completely unchanged — it just picks up whatever lands in `raw/<topic>/`.
- Let the user manually control what gets filed into the wiki (review before ingest).

## Non-Goals

- Auto-ingest from NotebookLM without user review.
- Modifying the existing `wiki-query`, `wiki-ingest`, or `wiki-lint` skills.
- Real-time or scheduled sync — all operations are on-demand.
- Managing NotebookLM audio generation workflows (podcasts are pulled as transcripts only if available).

---

## Architecture

### Core abstraction: `raw/<topic>/` ↔ NotebookLM notebook

Each topic folder in `raw/` maps 1:1 to a NotebookLM notebook:

```
raw/
├── vlm-research/         → NotebookLM: "VLM Research"
├── reasoning-techniques/ → NotebookLM: "Reasoning Techniques"
└── <topic>/              → NotebookLM: "<Notebook Title>"
```

This folder-as-protocol means:
- **Push**: files in `raw/<topic>/` or matching `wiki/` pages become NotebookLM sources.
- **Pull**: artifacts downloaded from NotebookLM land in `raw/<topic>/`.
- **Ingest**: `wiki-ingest` runs on `raw/<topic>/` as normal — no changes needed.

Notebook ↔ folder mapping is stored in a lightweight config file: `wiki/nlm-notebooks.md`.

---

### `wiki/nlm-notebooks.md` — mapping registry

A simple markdown table maintained by the skills:

```markdown
# NotebookLM Notebook Registry

| Topic Folder       | Notebook Title        | Notebook ID (alias) | Last Synced |
|--------------------|-----------------------|---------------------|-------------|
| vlm-research       | VLM Research          | vlm-research        | 2026-05-22  |
| reasoning-techniques | Reasoning Techniques | reasoning           | —           |
```

Skills read this file to resolve `raw/<topic>/` → notebook alias → `nlm` UUID.

---

### Two new skills

#### `wiki-nlm-sync` — bidirectional sync manager

Handles all content movement between local files and NotebookLM. Three sub-workflows:

**Push:**
1. User specifies topic (resolves to `raw/<topic>/` + notebook alias).
2. User selects what to push: files from `raw/<topic>/`, wiki pages, or both.
3. Skill calls `nlm source add` for each selected item.
4. Updates `wiki/nlm-notebooks.md` with last-synced date.

**Pull:**
1. User specifies topic + what to pull (Q&A answer, report, podcast transcript, mind map).
2. Skill calls `nlm` to download the artifact.
3. Saves artifact to `raw/<topic>/` with a descriptive filename.
4. Prompts: "Ready to ingest — run `wiki-ingest` on `raw/<topic>/<filename>`?"

**Notebook management:**
- Create a new notebook + register it in `wiki/nlm-notebooks.md`.
- List all registered notebooks with sync status.

---

#### `wiki-nlm-research` — gap-driven query skill

Triggered when `wiki-query` surfaces a gap. Takes a question and a topic, queries the matching NotebookLM notebook, and surfaces results with pull options.

**Workflow:**
1. User provides: gap question + topic (e.g., "vlm-research").
2. Skill resolves topic → notebook alias → runs `nlm notebook query <id> "<question>"`.
3. Displays cited answer from NotebookLM.
4. Lists available generated artifacts in the notebook (reports, transcripts, mind maps).
5. Asks: "Which artifacts do you want to pull into `raw/<topic>/`?"
6. If user selects any → calls `wiki-nlm-sync pull` for those artifacts.
7. Logs the research session to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] nlm-research | <Question>
   Notebook: <topic>, Artifacts pulled: ..., Ingest pending: yes/no
   ```

---

### Full pipeline (end-to-end)

```
wiki-query "X"
  └─► score < 0.3 → gap detected
        └─► wiki-nlm-research "X" --topic <topic>
              ├─► queries NotebookLM notebook
              ├─► surfaces answer + artifact list
              └─► user selects artifacts to pull
                    └─► wiki-nlm-sync pull → raw/<topic>/
                          └─► wiki-ingest raw/<topic>/<file>
                                └─► wiki pages updated
                                      └─► wiki-query "X"  ← now richer
```

---

## Dependency

- `nlm` CLI (`notebooklm-mcp-cli`) must be installed and authenticated.
- `wiki/nlm-notebooks.md` must exist (created on first `wiki-nlm-sync` run).
- Existing skills (`wiki-query`, `wiki-ingest`, `wiki-lint`) are unchanged.

---

## Resolved Decisions

1. **wiki-query gap message:** Yes — when score < 0.3, `wiki-query` explicitly suggests running `wiki-nlm-research` with the same question and topic.
2. **Pull artifact format:** Artifacts are saved as-is (raw text/markdown) into `raw/<topic>/` — no preprocessing. `wiki-ingest` handles interpretation.
3. **Push wiki pages:** Use `nlm source add --text` (paste markdown content as text source) — no URL publishing required.
