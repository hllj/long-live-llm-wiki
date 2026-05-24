# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.5.0] — 2026-05-25

### Added

- `wiki-init` now uses **`AskUserQuestion`** for topic collection — a single native UI dialog replaces the previous sequential Q&A flow, giving a cleaner user experience.
- `wiki-init` now **generates a tailored `CLAUDE.md`** from `skills/wiki-init/CLAUDE.md.example` — substituting the topic title, description, and collection slug into the operational schema automatically.
- `skills/wiki-init/CLAUDE.md.example` — new reference template for CLAUDE.md generation, so each wiki gets a correctly scoped operational schema out of the box.

### Changed

- `wiki-init` v2.0.0: removed the `.backup/` step — content is no longer copied before cleanup (simplifies the flow; raw sources stay in git history).
- `wiki-init` Step 4 simplified: no entity/concept stub scaffolding; the skill now focuses on `CLAUDE.md` generation, index/log reset, and search index setup.
- Docs updated: spec, plan, and tasks for `002-wiki-init` revised to reflect v2.0.0 workflow.

---

## [0.4.0] — 2026-05-25

### Added

- `wiki-init` now sets up a **project-local qmd index** (`.qmd/`) automatically — runs `qmd init`, registers the `wiki` collection under a topic-derived slug, and rebuilds the index. No manual `qmd init` step needed after running `wiki-init`.
- `.gitignore` updated by `wiki-init` to exclude `.qmd/` alongside `raw/*` and `.backup/`.
- CLAUDE.md documents the project-local index convention and notes that all qmd commands should be run from the repo root.

### Changed

- Setup instructions in README updated: `wiki-init` replaces the manual `qmd init` + `qmd collection add` + `qmd update` steps for new installs.

---

## [0.3.0] — 2026-05-24

### Added

- `wiki-init` skill — guided one-command wiki setup: collects topic, backs up existing content to `.backup/`, cleans example pages, scaffolds entity/concept stubs, resets `index.md` and `log.md`, updates `.gitignore`, and rebuilds the qmd index.
- `.gitignore` now excludes `raw/*` (keeping `raw/.gitkeep`) and `.backup/` — raw PDFs and backups stay out of git automatically.
- Production init applied: repo reset for **LLM / AI Systems Research** topic; all previous VLM example content preserved in `.backup/`.

### Changed

- README updated with `wiki-init` usage, updated Skills table, and simplified "Customizing for your domain" section.

---

## [0.2.0] — 2026-05-24

### Added

- `wiki-query` v2.0: native web-search gap-handoff flow — when a query scores < 0.3, Claude runs `WebSearch`, lets the user pick a source, saves it to `raw/`, triggers `wiki-ingest`, and offers a re-query. No external CLI or auth required.
- `EXAMPLES.md` — end-to-end usage examples for ingest, query, and lint workflows.
- Docs examples for lint and query use cases.

### Changed

- `wiki-query` gap escalation now uses web search instead of NotebookLM, removing the need for Google Drive auth or any external integration.

### Removed

- `wiki-nlm-sync` and `wiki-nlm-research` skills — NotebookLM integration replaced by the simpler web-search gap-handoff in `wiki-query`.

---

## [0.1.0] — 2026-05-22

### Added

- `CLAUDE.md` operational schema defining ingest, query, and lint workflows
- `wiki/index.md` — content catalog with one-line summaries per page
- `wiki/log.md` — append-only activity log with greppable entry headers
- Three Claude Code skills: `wiki-ingest`, `wiki-query`, `wiki-lint`
- `llm-wiki.md` — the pattern document describing the LLM-maintained wiki idea
- First ingested source: CoVT (Chain-of-Visual-Thought, arXiv 2511.19418v2)
  - `wiki/sources/covt-chain-of-visual-thought.md`
  - `wiki/entities/qwen2-5-vl.md`
  - `wiki/concepts/chain-of-visual-thought.md`
  - `wiki/concepts/continuous-visual-tokens.md`
  - `wiki/concepts/visual-reasoning-in-vlms.md`
- First analysis page: `wiki/analyses/visual-thinking-techniques.md` — comparison of 6 VLM visual reasoning paradigms
- qmd search integration (`@tobilu/qmd`) with pre-configured `wiki` collection
- `.claude-plugin/` with plugin manifest for local skill registration
