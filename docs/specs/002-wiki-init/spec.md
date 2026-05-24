# Feature 002: Wiki Init

**Status:** Approved
**Version:** 2.0.0
**Created:** 2026-05-24
**Updated:** 2026-05-25
**Branch:** `002-wiki-init`

---

## Problem Statement

When a user clones or forks the LLM Wiki Notebook, the repository arrives pre-populated with example content from a previous topic (sources, entities, concepts, analyses). There is no guided path to declare "this wiki is about X", cleanly remove example content, configure the project for the new domain, and generate the operational instructions Claude needs to run the wiki. Users either delete files manually (risky) or start ingesting on top of someone else's knowledge graph (confusing).

---

## Goals

1. A single invocation of the `wiki-init` skill guides the user through declaring their wiki's topic using the `AskUserQuestion` UI tool.
2. All example wiki subdirectories (`concepts/`, `entities/`, `sources/`, `analyses/`) are cleared; each is left with only a `.gitkeep` so the folder structure remains tracked.
3. `wiki/index.md` is reset to an empty template reflecting the new topic.
4. `wiki/log.md` is reset with a single init entry.
5. A `CLAUDE.md` file is generated (or overwritten) at the repo root, populated with the wiki's operational schema for the new topic — so Claude has the correct instructions from the first ingest onward.
6. `.gitignore` is updated to exclude raw file contents (`raw/*`) while keeping `raw/.gitkeep`, and to exclude `.qmd/`.
7. The qmd project-local index is initialized and the wiki collection is registered and built.

---

## Non-Goals

- Backing up existing content to `.backup/` — the user is responsible for version control via git.
- Creating entity or concept stub pages during init — stubs emerge organically through `wiki-ingest`.
- Auto-populating pages with real content — actual knowledge comes from `wiki-ingest`.
- Touching skill files (`skills/`), `docs/`, or `README.md` — those are project infrastructure, not wiki content.
- Running any web search or source ingest during init.
- Supporting partial resets (e.g. only resetting entities but not sources).

---

## Users and Context

**Primary users:** Anyone starting a fresh personal knowledge wiki from the LLM Wiki Notebook template — researchers, engineers, students.
**Usage context:** Run once at the start of a new wiki project, before any sources are ingested. May also be run when pivoting to a completely new topic.
**User mental model:** Users think of this as "setting up my notebook" — they answer one question in a UI dialog and then have a clean, topic-relevant scaffold ready for use.

---

## User Stories

### Story 1: Declare the wiki topic via UI

**As a** user starting a new wiki project
**I want to** describe my wiki's topic in a UI dialog (not a back-and-forth text chat)
**So that** setup feels polished and I don't have to wait for multiple sequential prompts

**Acceptance criteria:**
- [ ] **AC-1.1** Given the skill is invoked When it begins Then it uses the `AskUserQuestion` tool to show a single dialog asking for the wiki topic description.
- [ ] **AC-1.2** Given the user submits an empty topic When the skill receives the response Then it re-prompts using `AskUserQuestion` with a validation message: "Topic description is required. Please describe what this wiki is about."
- [ ] **AC-1.3** Given the user has provided a topic description When the skill derives the topic title Then it produces a title-cased string from the first 4–5 significant words (e.g. "Reinforcement Learning from Human Feedback").

### Story 2: Clean existing content

**As a** user initializing the wiki for a new topic
**I want** all example wiki pages cleared before the new topic is scaffolded
**So that** legacy content from a previous topic doesn't pollute my new knowledge graph

**Acceptance criteria:**
- [ ] **AC-2.1** Given cleanup runs When the skill completes Then all files inside `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, and `wiki/analyses/` are deleted and a `.gitkeep` is placed in each directory.
- [ ] **AC-2.2** Given cleanup runs When `raw/` is inspected Then all files except `raw/.gitkeep` are deleted.
- [ ] **AC-2.3** Given cleanup runs When protected paths are checked Then `wiki/.obsidian/`, `CLAUDE.md` (before overwrite), `skills/`, `docs/`, and `README.md` are untouched.

### Story 3: Generate CLAUDE.md

**As a** user who has just initialized the wiki
**I want** Claude to generate a `CLAUDE.md` tailored to my wiki's topic
**So that** Claude has correct operational instructions from the very first ingest — no manual editing required

**Acceptance criteria:**
- [ ] **AC-3.1** Given the topic has been declared When the skill writes `CLAUDE.md` Then it overwrites any existing file at the repo root with a complete operational schema.
- [ ] **AC-3.2** Given `CLAUDE.md` is written When it is read Then it contains: the wiki topic title and description, the three-layer structure (`raw/`, `wiki/`, `CLAUDE.md`), qmd command reference with all standard commands and the `2>/dev/null || true` note, ingest/query/lint operation schemas, wiki page conventions, index format, log format, and a scope section naming the topic.
- [ ] **AC-3.3** Given `CLAUDE.md` is written When the collection slug is inspected Then qmd commands inside `CLAUDE.md` use the `<collection-slug>` derived from the topic title (e.g. `--collection reinforcement-learning-from-human-feedback`), not the literal placeholder string `wiki`.

### Story 4: Update .gitignore for production use

**As a** user preparing the wiki for git-tracked use
**I want** large raw files and the local qmd index excluded from git automatically
**So that** I don't accidentally commit PDFs or local index state to the repository

**Acceptance criteria:**
- [ ] **AC-4.1** Given `.gitignore` exists When the skill runs Then it appends a `# Wiki raw sources` section containing `raw/*` and `!raw/.gitkeep` if those lines are not already present.
- [ ] **AC-4.2** Given `.gitignore` exists When the skill runs Then it appends `.qmd/` under a `# qmd local index` section if that line is not already present.
- [ ] **AC-4.3** Given the lines are already present When the skill checks Then it does not add duplicate entries and reports "`.gitignore` already up to date."
- [ ] **AC-4.4** Given `.gitignore` does not exist When the skill runs Then it creates it containing only the two sections above.

### Story 5: Reset wiki/index.md and wiki/log.md

**As a** user starting a fresh wiki
**I want** the index and log reset to reflect the new topic
**So that** legacy entries from example content don't appear in queries or the activity history

**Acceptance criteria:**
- [ ] **AC-5.1** Given cleanup is complete When `wiki/index.md` is written Then it contains the standard section headers (Sources, Entities, Concepts, Analyses) with empty bodies; no legacy entries remain.
- [ ] **AC-5.2** Given `wiki/index.md` is written When the topic is available Then the file begins with a `# <Topic Title>` heading followed by the user's topic description as a short paragraph.
- [ ] **AC-5.3** Given cleanup is complete When `wiki/log.md` is written Then it contains exactly one entry: `## [YYYY-MM-DD] init | <Topic Title>` describing what was cleaned and the .gitignore state; prior log entries are not carried over.

### Story 6: Set up qmd project-local index and collection

**As a** user whose wiki has just been initialised
**I want** qmd configured with a project-local index and the correct collection registered
**So that** all subsequent `wiki-query` and `wiki-ingest` calls use the right local index without any manual setup

**Acceptance criteria:**
- [ ] **AC-6.1** Given all file writes are complete When the skill runs `qmd init` Then a `.qmd/` folder is created in the repo root.
- [ ] **AC-6.2** Given `qmd init` completes When the skill checks `qmd collection list` Then if `<collection-slug>` is absent it runs `qmd collection add ./wiki --name <collection-slug>`.
- [ ] **AC-6.3** Given the collection is registered When the skill runs `qmd collection list` Then `<collection-slug>` appears in the output and is reported to the user.
- [ ] **AC-6.4** Given the collection is registered When the skill runs `qmd update --collection <collection-slug>` Then the index is built and the skill confirms success.
- [ ] **AC-6.5** Given all setup steps complete When the skill reports Then it tells the user "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

---

## Functional Requirements

### FR-1: UI-Driven Topic Collection

The skill must collect the wiki topic through the `AskUserQuestion` tool — not via text output and reply. This gives the user a structured dialog rather than a conversational back-and-forth.

**Must:**
- Use `AskUserQuestion` for the topic description prompt.
- Re-prompt using `AskUserQuestion` if the topic description is empty.
- Trim whitespace and generate a valid kebab-case slug from the topic title for use as the qmd collection name.

**Must not:**
- Ask for entity or concept names — these are not collected during init.
- Infer or guess topic details the user didn't provide.
- Proceed to file operations if the topic description is empty.

### FR-2: Selective Cleanup

Only the content-bearing subdirectories of `wiki/` are cleared. Structural files and Obsidian config are preserved.

**Must:**
- Delete all files inside `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/analyses/`.
- Place a `.gitkeep` in each of those four directories after clearing.
- Delete all files in `raw/` except `raw/.gitkeep`.

**Must not:**
- Touch `wiki/.obsidian/`, `wiki/index.md` (before the reset write), or `wiki/log.md` (before the reset write).
- Delete `CLAUDE.md` (it is overwritten in FR-3, not deleted), `README.md`, `llm-wiki.md`, `skills/`, or `docs/`.

### FR-3: Generate CLAUDE.md

The skill must write a complete `CLAUDE.md` at the repo root that gives Claude all operational instructions needed to run the wiki for the declared topic.

**Must:**
- Overwrite any existing `CLAUDE.md`.
- Include: topic title and description, three-layer structure explanation, qmd command reference (all standard commands with `2>/dev/null || true` note and score thresholds), ingest/query/lint operation schemas, wiki page conventions, index format, log format, scope section.
- Replace every occurrence of the generic collection name (`wiki`) in qmd commands with the actual `<collection-slug>` derived from the topic title.

**Must not:**
- Omit any section that the reference `CLAUDE.md` in this project contains.
- Hard-code the literal string `wiki` as the collection name in qmd commands.

### FR-4: .gitignore Update

The `.gitignore` update must be additive — it must not remove, reorder, or modify any existing lines.

**Must:**
- Append only if the required lines are absent.
- Add lines under clearly labeled comment headers (`# Wiki raw sources`, `# qmd local index`).
- Exclude `.qmd/` under a `# qmd local index` section.

**Must not:**
- Overwrite the file; only append to it.
- Add a `.backup/` entry (backup is no longer part of init).
- Remove any existing `.gitignore` entries.

---

## Non-Functional Requirements

### Performance
- The full init sequence (cleanup + CLAUDE.md + index + log + .gitignore + qmd update) must complete in under 60 seconds for a wiki with fewer than 50 existing pages.

### Reliability
- If any file write fails mid-sequence, the skill must report the failure and not continue with subsequent steps.
- The skill must be safe to run more than once: a second invocation overwrites CLAUDE.md and resets index/log rather than erroring.

### Security
- The skill must never read file contents from `raw/` during init — it only cleans them.

---

## Error Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Topic description is empty when submitted | Skill re-prompts via `AskUserQuestion`: "Topic description is required. Please describe what this wiki is about." |
| `.gitignore` does not exist | Skill creates it with only the wiki sections; does not error |
| `wiki/concepts/` (or sibling dir) does not exist | Skill skips deletion for that directory, creates it with `.gitkeep`, continues |
| `qmd init` fails (e.g. permission error) | Skill prints a warning "qmd init failed — run `qmd init` manually then `qmd collection add ./wiki --name <collection-slug>`" but does not fail the overall init |
| `qmd update` exits with non-zero code | Skill prints a warning "qmd index update failed — run `qmd update --collection <collection-slug>` manually" but does not fail the overall init |

---

## Open Questions

- None — all clarifications received before spec was written.

---

## Out of Scope (Future Considerations)

- A `wiki-reset` skill that performs only the cleanup without the topic-declaration flow.
- Support for importing a topic description from a file rather than interactive prompt.
- A `wiki-restore` skill that unpacks a git-tracked backup back into `raw/` and `wiki/`.
- Configurable collection name override (currently always derived from topic title).

---

## Change Log

| Version | Date | Summary |
|---------|------|---------|
| 1.0.0 | 2026-05-24 | Initial approved spec |
| 1.1.0 | 2026-05-24 | Added qmd project-local index setup (Step 8) |
| 2.0.0 | 2026-05-25 | Remove backup step; remove entity/concept prompts and stubs; add AskUserQuestion UI; add CLAUDE.md generation |
