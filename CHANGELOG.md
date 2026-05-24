# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
