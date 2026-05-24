# Implementation Plan: Wiki Init

> **For agentic workers:** Use sdd-tasks to generate an executable task list from this plan.

**Spec:** docs/specs/002-wiki-init/spec.md (v2.0.0)
**Created:** 2026-05-24
**Updated:** 2026-05-25

---

## Goal

Deliver a rewritten `skills/wiki-init/SKILL.md` (v2.0.0) that:
- Collects the wiki topic via the `AskUserQuestion` tool (not sequential text prompts)
- Skips the backup step entirely
- Skips entity/concept prompts and stub creation
- Generates a complete `CLAUDE.md` tailored to the declared topic
- Cleans wiki subdirs, resets index/log, updates .gitignore, rebuilds qmd index

## Architecture

The primary deliverable is a rewritten skill file — a markdown workflow document that Claude reads and executes step-by-step. No data model, no API contract: all operations are filesystem reads and writes, Bash commands, and the `AskUserQuestion` tool call.

The CLAUDE.md generation step produces a templated file parameterized by the topic title, description, and derived collection slug.

## Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Skill format | Markdown SKILL.md with YAML frontmatter | Matches all existing skill files in `skills/` |
| UI collection | `AskUserQuestion` tool | FR-1: single dialog instead of sequential text prompts |
| File operations | Bash (`find -delete`, `touch`, `mkdir -p`) | FR-2 selective cleanup |
| CLAUDE.md generation | Write tool with parameterized template | FR-3: topic-specific operational schema |
| Gitignore update | Bash (`grep -qF`, append via Edit tool) | FR-4 additive update |
| Search index | `qmd init`, `qmd collection add`, `qmd update` | FR-5, AC-6.x |

## File Structure

- `skills/wiki-init/SKILL.md` — rewritten skill: 7-step workflow (FR-1–FR-4, all ACs)
- `CLAUDE.md` — generated at repo root with topic-specific qmd collection slug (FR-3, AC-3.1–3.3)
- `.gitignore` — append `raw/*`, `!raw/.gitkeep`, `.qmd/` (FR-4, AC-4.1–4.2)
- `wiki/concepts/.gitkeep` — directory placeholder after cleanup (FR-2, AC-2.1)
- `wiki/entities/.gitkeep` — directory placeholder after cleanup (FR-2, AC-2.1)
- `wiki/sources/.gitkeep` — directory placeholder after cleanup (FR-2, AC-2.1)
- `wiki/analyses/.gitkeep` — directory placeholder after cleanup (FR-2, AC-2.1)
- `raw/.gitkeep` — preserved; all other raw/ files removed (FR-2, AC-2.2)
- `wiki/index.md` — reset: topic heading, empty section bodies (FR-2 + Story 5, AC-5.1–5.2)
- `wiki/log.md` — reset: single init entry, no legacy entries (Story 5, AC-5.3)

## Complexity Tracking

All pre-implementation gates pass:

- **Simplicity Gate:** 1 component (skill file). No future-proofing. No new dependencies.
- **Anti-Abstraction Gate:** Bash used directly; no wrapper scripts introduced.
- **Integration-First Gate:** No API contracts needed; skill is a markdown document, not an API.

---

## Phase 1: Rewrite skills/wiki-init/SKILL.md

**Implements:** FR-1, FR-2, FR-3, FR-4 | **Satisfies:** AC-1.1–1.3, AC-2.1–2.3, AC-3.1–3.3, AC-4.1–4.4, AC-5.1–5.3, AC-6.1–6.5

### 1.1 Rewrite SKILL.md

Overwrite `skills/wiki-init/SKILL.md` with a 7-step workflow:

**Step 1 — Collect topic via AskUserQuestion**
- Call `AskUserQuestion` with a single question asking for the topic description.
- Validate non-empty; re-prompt if empty.
- Derive topic title (first 4–5 significant words, title-cased).
- Derive collection slug (kebab-case of topic title).

**Step 2 — Update .gitignore**
- Check for `raw/*`, `!raw/.gitkeep`, `.qmd/` — append missing lines under labeled sections.
- No `.backup/` entry.

**Step 3 — Clean wiki subdirectories and raw/**
- `find … -not -name '.gitkeep' -delete` for each of the four wiki subdirs.
- `touch <dir>/.gitkeep` for each.
- `find raw -type f -not -name '.gitkeep' -delete`.

**Step 4 — Generate CLAUDE.md**
- Write a complete `CLAUDE.md` to repo root using the Write tool.
- Parameterize with: topic title, topic description, collection slug.
- Include all sections from the reference CLAUDE.md: three-layer structure, qmd commands (with collection slug substituted), ingest/query/lint schemas, page conventions, index format, log format, scope section.

**Step 5 — Write wiki/index.md**
- Full file with `# <Topic Title>`, topic description, four empty section headers (Sources, Entities, Concepts, Analyses).

**Step 6 — Write wiki/log.md**
- Single init entry with today's date, what was cleaned, .gitignore state.

**Step 7 — Set up qmd project-local index and collection**
- `qmd init`
- Check collection list; `qmd collection add ./wiki --name <collection-slug>` if absent.
- `qmd collection list` — report to user.
- `qmd update --collection <collection-slug>`.
- Report: "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

### 1.2 Verify SKILL.md

```bash
ls -la skills/wiki-init/SKILL.md
grep -c '###' skills/wiki-init/SKILL.md
grep 'AskUserQuestion' skills/wiki-init/SKILL.md
```

Expected: file exists, ≥7 `###` headers, `AskUserQuestion` mentioned.

---

## Phase 2: Apply production init to current repository

*Phase 1 must be complete before starting this phase.*

This phase applies the new init workflow to the current repo — validating the skill against a real case.

> **Interactive step at 2.1:** the executor must call `AskUserQuestion` for the wiki topic before proceeding.

### 2.1 Collect topic from user [INTERACTIVE]

- Call `AskUserQuestion` with the topic description question.
- Record `TOPIC_DESCRIPTION`, `TOPIC_TITLE`, `COLLECTION_SLUG`.

### 2.2 Update .gitignore

- Check and append `raw/*`, `!raw/.gitkeep`, `.qmd/` under correct sections.

### 2.3 Clean wiki subdirectories and raw/

- Run cleanup commands.
- Verify each dir contains only `.gitkeep`.
- Verify protected files untouched.

### 2.4 Generate CLAUDE.md

- Write `CLAUDE.md` with topic-specific content.
- Verify qmd commands contain `COLLECTION_SLUG` not the literal `wiki`.

### 2.5 Write wiki/index.md and wiki/log.md

- Write index with topic heading and empty sections.
- Write log with single init entry.

### 2.6 Set up qmd project-local index and collection

- `qmd init` → verify `.qmd/` exists.
- Register collection if absent.
- Build index.
- Report output.

### 2.7 Commit

```
feat(wiki-init): apply production init v2.0.0 — clean, generate CLAUDE.md, scaffold new topic
```

---

## Phase 3: Integration Verification

*All prior phases must be complete.*

- AC-2.1: Four wiki subdirs each contain only `.gitkeep`.
- AC-2.2: `raw/` contains only `raw/.gitkeep`.
- AC-3.3: qmd commands in `CLAUDE.md` use actual collection slug, not literal `wiki`.
- AC-4.1 + AC-4.2: `.gitignore` contains `raw/*` and `.qmd/` sections.
- AC-5.2: `wiki/index.md` starts with `# <TOPIC_TITLE>`.
- AC-5.3: `wiki/log.md` contains exactly one `##` entry.
- AC-6.3: `<collection-slug>` appears in `qmd collection list`.

---

## Quickstart Validation

After both phases are complete, a new user cloning this repo should:

1. Open the repo — no example content in `wiki/` anywhere.
2. Check `wiki/index.md` — sees the new topic heading.
3. Check `CLAUDE.md` — sees topic-specific qmd commands with correct collection slug.
4. Check `.gitignore` — `raw/*` and `.qmd/` are excluded.
5. Drop a PDF into `raw/` — git status shows it as ignored (not staged).
6. Invoke `wiki-init` on a fresh clone — skill runs all 7 steps, produces the same clean state.
