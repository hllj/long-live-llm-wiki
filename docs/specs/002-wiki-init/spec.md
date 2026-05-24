# Feature 002: Wiki Init

**Status:** Approved
**Created:** 2026-05-24
**Branch:** `002-wiki-init`

---

## Problem Statement

When a user clones or forks the LLM Wiki Notebook, the repository arrives pre-populated with example content from a previous topic (sources, entities, concepts, analyses). There is no guided path to declare "this wiki is about X", scaffold appropriate placeholder pages for the new domain, cleanly remove example content, and protect existing work with a backup — so users either delete files manually (risky) or start ingesting on top of someone else's knowledge graph (confusing).

---

## Goals

1. A single invocation of the `wiki-init` skill guides the user through declaring their wiki's topic and scope.
2. Existing `raw/` and `wiki/` content is backed up to `.backup/` before any files are modified.
3. All example wiki subdirectories (`concepts/`, `entities/`, `sources/`, `analyses/`) are cleared; each is left with only a `.gitkeep` so the folder structure remains tracked.
4. `wiki/index.md` is reset to an empty template reflecting the new topic.
5. `wiki/log.md` is reset with a single init entry.
6. The skill creates stub placeholder pages for up to 5 key entities and up to 5 key concepts that the user names during the guided conversation.
7. `.gitignore` is updated to exclude raw file contents (`raw/*`) while keeping `raw/.gitkeep`, and to exclude `.backup/`.
8. The qmd index is rebuilt after all changes.

---

## Non-Goals

- Auto-populating pages with real content — stubs only; actual knowledge comes from `wiki-ingest`.
- Touching `CLAUDE.md`, skill files (`skills/`), or `docs/` — those are project infrastructure, not wiki content.
- Running any web search or source ingest during init.
- Supporting partial resets (e.g. only resetting entities but not sources).
- Migrating or merging old wiki content into the new topic structure.

---

## Users and Context

**Primary users:** Anyone starting a fresh personal knowledge wiki from the LLM Wiki Notebook template — researchers, engineers, students.
**Usage context:** Run once at the start of a new wiki project, before any sources are ingested. May also be run when pivoting to a completely new topic.
**User mental model:** Users think of this as "setting up my notebook" — they expect to answer a few questions and then have a clean, topic-relevant scaffold ready for use.

---

## User Stories

### Story 1: Declare the wiki topic and generate stubs

**As a** user starting a new wiki project
**I want to** tell the skill what my wiki is about and name the key entities and concepts I'll track
**So that** the wiki is scaffolded for my domain from day one, with placeholder pages ready for future ingests to fill in

**Acceptance criteria:**
- [ ] **AC-1.1** Given the skill is invoked When the user has not yet provided a topic Then the skill prompts the user: "What is this wiki about? Describe the topic or project in 1–3 sentences."
- [ ] **AC-1.2** Given the user has provided a topic description When the skill continues Then it prompts: "Name up to 5 key entities (people, models, systems, papers) this wiki should track. Separate with commas."
- [ ] **AC-1.3** Given the user has provided entity names When the skill continues Then it prompts: "Name up to 5 key concepts (ideas, techniques, frameworks) this wiki should track. Separate with commas."
- [ ] **AC-1.4** Given the user has answered all three prompts When the skill proceeds Then it creates one stub page per named entity at `wiki/entities/<slug>.md` and one stub per named concept at `wiki/concepts/<slug>.md`, each containing the page title and a `_Stub — to be filled by wiki-ingest._` note.
- [ ] **AC-1.5** Given stub pages have been written When the index is updated Then `wiki/index.md` lists every new stub under its correct section (Entities / Concepts) with a `(stub)` label.

### Story 2: Back up and clean existing content

**As a** user initializing the wiki for a new topic
**I want** all existing raw files and wiki pages backed up before anything is deleted
**So that** I can retrieve previous work if needed without risking accidental data loss

**Acceptance criteria:**
- [ ] **AC-2.1** Given `raw/` or `wiki/` contains files When the skill begins file operations Then it copies the full contents of `raw/` to `.backup/raw/` and `wiki/` to `.backup/wiki/` before modifying or deleting anything.
- [ ] **AC-2.2** Given the backup completes successfully When the skill reports progress Then it prints the total number of files backed up and confirms the backup path (`.backup/`).
- [ ] **AC-2.3** Given the backup is complete When cleanup runs Then all files inside `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, and `wiki/analyses/` are deleted and a `.gitkeep` is placed in each directory.
- [ ] **AC-2.4** Given cleanup is complete When `raw/` is inspected Then all files except `raw/.gitkeep` are deleted (they exist in `.backup/raw/`).
- [ ] **AC-2.5** Given the backup step fails (e.g. disk error) When the skill detects the failure Then it aborts without deleting any wiki or raw files and reports the error to the user.

### Story 3: Update .gitignore for production use

**As a** user preparing the wiki for git-tracked use
**I want** large raw files and backups excluded from git automatically
**So that** I don't accidentally commit PDFs or backup archives to the repository

**Acceptance criteria:**
- [ ] **AC-3.1** Given `.gitignore` exists When the skill runs Then it appends a `# Wiki raw sources` section containing `raw/*` and `!raw/.gitkeep` if those lines are not already present.
- [ ] **AC-3.2** Given `.gitignore` exists When the skill runs Then it appends `.backup/` under a `# Wiki backup` section if that line is not already present.
- [ ] **AC-3.3** Given the lines are already present in `.gitignore` When the skill checks Then it does not add duplicate entries and reports "`.gitignore` already up to date."

### Story 4: Reset wiki/index.md and wiki/log.md

**As a** user starting a fresh wiki
**I want** the index and log reset to reflect the new topic
**So that** legacy entries from example content don't appear in queries or the activity history

**Acceptance criteria:**
- [ ] **AC-4.1** Given cleanup is complete When `wiki/index.md` is written Then it contains the standard section headers (Sources, Entities, Concepts, Analyses) with only the newly created stubs listed; no legacy entries remain.
- [ ] **AC-4.2** Given `wiki/index.md` is written When the topic description is available Then the file begins with a `# <Topic Title>` heading followed by the user's topic description as a short paragraph.
- [ ] **AC-4.3** Given cleanup is complete When `wiki/log.md` is written Then it contains exactly one entry: `## [YYYY-MM-DD] init | <Topic Title>` describing what was backed up, what was cleaned, and what stubs were created; prior log entries are not carried over.

### Story 5: Rebuild the qmd search index

**As a** user whose wiki has just been restructured
**I want** the search index updated immediately after init
**So that** subsequent `wiki-query` and `wiki-ingest` calls operate against the correct post-init state

**Acceptance criteria:**
- [ ] **AC-5.1** Given all file writes are complete When the skill finishes Then it runs `qmd update --collection wiki 2>/dev/null || true` and reports success.
- [ ] **AC-5.2** Given `qmd update` completes When the skill reports Then it confirms the index was refreshed and tells the user "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

---

## Functional Requirements

### FR-1: Guided Topic Collection

The skill must collect the wiki topic, entity names, and concept names through sequential prompts before performing any file operations. It must not proceed with file changes until all three prompts have been answered or the user explicitly skips a prompt.

**Must:**
- Ask topic, entities, and concepts in order, one prompt at a time.
- Accept an empty response to entity/concept prompts as "skip" (zero stubs created for that category).
- Trim whitespace and generate a valid kebab-case slug from each name for use as the filename.

**Must not:**
- Infer or guess entity/concept names the user didn't provide.
- Proceed to file operations if the topic description is empty.

### FR-2: Backup Before Modify

All destructive file operations (deletions, overwrites of `index.md` / `log.md`) must be preceded by a complete backup of the affected directories.

**Must:**
- Copy `raw/` → `.backup/raw/` and `wiki/` → `.backup/wiki/` preserving directory structure.
- Complete the backup atomically before any deletion begins.

**Must not:**
- Delete or overwrite any file before the backup of that file exists in `.backup/`.
- Proceed if the backup copy fails for any file.

### FR-3: Selective Cleanup

Only the content-bearing subdirectories of `wiki/` are cleared. Structural files and Obsidian config are preserved.

**Must:**
- Delete all files inside `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/analyses/`.
- Place a `.gitkeep` in each of those four directories after clearing.
- Delete all files in `raw/` except `raw/.gitkeep`.

**Must not:**
- Touch `wiki/.obsidian/`, `wiki/index.md` (before the reset write), or `wiki/log.md` (before the reset write) until after backup is confirmed.
- Delete `CLAUDE.md`, `README.md`, `llm-wiki.md`, `skills/`, or `docs/`.

### FR-4: Stub Page Format

Each stub page must be a valid markdown file that `qmd` can index, containing enough structure to serve as a landing page for future ingest.

**Must:**
- Begin with `# <Entity or Concept Name>` as the H1.
- Include the line `_Stub — to be filled by wiki-ingest._` on the second line.
- Include a `## Notes` section (empty body) so future editors have a place to add content.

**Must not:**
- Include any topic-specific content the user did not provide.

### FR-5: .gitignore Update

The `.gitignore` update must be additive — it must not remove, reorder, or modify any existing lines.

**Must:**
- Append only if the required lines are absent.
- Add lines under clearly labeled comment headers (`# Wiki raw sources`, `# Wiki backup`).

**Must not:**
- Overwrite the file; only append to it.
- Remove any existing `.gitignore` entries.

---

## Non-Functional Requirements

### Performance
- The full init sequence (backup + cleanup + stubs + index + log + qmd update) must complete in under 60 seconds for a wiki with fewer than 50 existing pages and a `raw/` directory with fewer than 20 files totaling under 200 MB.

### Reliability
- If any file write fails mid-sequence, the skill must report the failure and not continue with subsequent destructive steps.
- The skill must be safe to run more than once: a second invocation must back up and reset again rather than erroring on pre-existing `.backup/` content (overwrite, not abort).

### Security
- The skill must never read file contents from `raw/` during init — it only copies them to backup.

---

## Error Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Topic description is empty when submitted | Skill re-prompts: "Topic description is required. Please describe what this wiki is about." |
| Backup copy fails (e.g. disk full) | Skill aborts, prints the failing file path and error, makes no deletions |
| `.gitignore` does not exist | Skill creates it with only the two wiki sections; does not error |
| `wiki/concepts/` (or sibling dir) does not exist | Skill skips deletion for that directory, creates it with `.gitkeep`, continues |
| `qmd update` exits with non-zero code | Skill prints a warning "qmd index update failed — run `qmd update --collection wiki` manually" but does not fail the overall init |
| Entity or concept name contains characters invalid for a filename | Skill strips non-alphanumeric characters (except hyphens) to produce the slug; if the resulting slug is empty, it skips that stub and informs the user |

---

## Open Questions

- None — all clarifications received before spec was written.

---

## Out of Scope (Future Considerations)

- A `wiki-reset` skill that performs only the backup+cleanup without the topic-declaration flow (useful for pivoting topic on an already-initialized wiki).
- Support for importing a topic description from a file rather than interactive prompt.
- A `wiki-restore` skill that unpacks `.backup/` back into `raw/` and `wiki/`.
- Configurable backup location (currently hardcoded to `.backup/`).
