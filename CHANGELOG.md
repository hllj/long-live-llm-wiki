# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
