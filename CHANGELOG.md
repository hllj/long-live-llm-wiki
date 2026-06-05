# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.7.0] — 2026-06-05

### Added

- `wiki-ingest` now auto-starts a persistent `mineru-api` server (port 8765, `--enable-vlm-preload True`) on first PDF ingest and reuses it for all subsequent ingests in the same machine session via `--api-url`. Eliminates the 30–60s VLM model-loading overhead on Apple M1 for every ingest after the first.
- `doc_to_markdown.py`: new `ensure_server()` function with full fallback logic — if `mineru-api` is not in PATH, startup times out (90s), or all candidate ports (8765–8768) are occupied, the script falls back to local mode transparently.
- Server logs written to `~/.mineru-api.log`; PID written to `~/.mineru-api.pid` (informational).
- `MINERU_API_PORT` and `MINERU_API_PID_FILE` environment variables for test isolation and custom configurations.

---

## [0.6.1] — 2026-06-03

### Fixed

- `wiki-ingest` `ingest_doc.py`: `REPO_ROOT` was derived from `__file__` location, causing `raw/` artifacts to always write into the `long-live-wiki` repo regardless of which wiki the script was invoked from. Changed to `Path.cwd()` so the script respects the caller's working directory.
- `wiki-ingest` test suite: hardcoded absolute `cwd` (`/Users/hllj/Projects/long-live-wiki`) in all three CLI subprocess tests replaced with a portable `REPO_ROOT` computed from `__file__` (5 parents up to repo root). All 31 tests pass.

---

## [0.6.0] — 2026-06-03

### Added

- `wiki-ingest` **Step 0: binary document support** — PDF and DOCX sources are now automatically pre-processed via MinerU (PDF→markdown conversion) + Gemini vision (figure enrichment) before wiki integration. Step 0 runs when the source path ends in `.pdf` or `.docx`; plain `.md` sources skip directly to Step 1.
- **Intermediate folder layout** — `raw/<slug>/` stores step-by-step artifacts (`step1_mineru_raw.md`, `step2_enhanced.md`) so Step 0 is resumable: if the folder already exists, the script inspects pipeline stage and offers to overwrite or continue from Gemini enrichment only.
- **Live streaming output** during Step 0 — MinerU progress and per-image Gemini enrichment lines (`[Gemini] Describing figure N/M: ... done`) are printed in real time without buffering.
- `skills/wiki-ingest/tools/ingest_doc.py` — the MinerU + Gemini processing script that drives Step 0, including a heartbeat line every 5 s when MinerU is silent.
- **Canonical two-zone link convention** documented and enforced across all four skills: `[[Wikilinks]]` inside content pages (`entities/`, `concepts/`, `sources/`, `analyses/`); standard markdown links with `%20` encoding in navigation files (`index.md`, `log.md`).

### Changed

- `wiki-ingest` file naming: now enforces **Title Case with spaces** for entity/concept filenames, ensuring Obsidian wikilink resolution works (e.g. `[[Multi-Head Attention]]` → `wiki/concepts/Multi-Head Attention.md`).
- README updated to document binary document support and the full MinerU + Gemini pipeline.

### Fixed

- `wiki-ingest` Step 0: resolved subprocess deadlock caused by stdout/stderr buffering when calling MinerU as a child process — output now streams correctly under all terminal conditions.
- `wiki-ingest` Step 0: fixed re-run md selection bug where the wrong markdown file was used on subsequent runs when both step1 and step2 artifacts were present.

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
