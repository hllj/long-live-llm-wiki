# Tasks: Wiki Init

**Plan:** docs/specs/002-wiki-init/plan.md
**Generated:** 2026-05-24

> **For agentic workers:** Execute tasks in order. `[P]` tasks within the same parallel group can run concurrently. Never start an implementation task without the prior verification task completed.
>
> **Note on TDD adaptation:** This feature delivers a markdown skill file and filesystem operations — not compilable code. "Test" steps verify outcomes via shell commands after each action rather than writing failing tests beforehand.
>
> **T010 is interactive** — it requires asking the user for their wiki topic before proceeding.

---

## Sequential: Phase 1 — Write wiki-init Skill

### T001 — Create skill directory

- [ ] **T001** Create `skills/wiki-init/` directory:
  ```bash
  mkdir -p /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-init
  ```
  Expected: directory exists, no error.

---

### T002 — Write skills/wiki-init/SKILL.md

- [ ] **T002** Write `skills/wiki-init/SKILL.md` with the complete content below. Use the Write tool with the exact file path `/Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-init/SKILL.md`:

  ```
  ---
  name: wiki-init
  description: >
    Initializes the LLM Wiki Notebook for a new topic. Use this skill when the
    user wants to start fresh, set up the wiki for a new topic, scaffold
    placeholder pages, back up existing content, or prepare the repo for
    production use. Trigger when the user says "init the wiki", "start a new
    wiki", "set up the wiki for X", "initialize", "prepare for production",
    "reset the wiki", or drops a request to configure the notebook from scratch.
  ---

  # Wiki Init

  You are initializing the LLM Wiki Notebook for a new topic. Your job is to
  guide the user through declaring their wiki's scope, safely back up all existing
  content, clean out example/previous content, scaffold placeholder pages for the
  new domain, update `.gitignore`, and rebuild the search index — all before any
  real sources are ingested.

  ## Workflow

  ### 1. Collect topic information (before touching any files)

  Ask three questions **sequentially** — wait for each answer before asking the next.

  **Q1 (required):** "What is this wiki about? Describe the topic or project in 1–3 sentences."

  - Do not proceed if the user provides an empty response. Re-ask: "Topic description
    is required. Please describe what this wiki is about."
  - Derive a topic title from the first 4–5 significant words of the description,
    title-cased (e.g. "Reinforcement Learning from Human Feedback").

  **Q2 (optional, skip on empty):** "Name up to 5 key **entities** (people, models,
  systems, papers, tools) this wiki should track. Separate with commas, or press
  Enter to skip."

  **Q3 (optional, skip on empty):** "Name up to 5 key **concepts** (ideas, techniques,
  frameworks, phenomena) this wiki should track. Separate with commas, or press
  Enter to skip."

  For each name in Q2 and Q3:
  - Trim whitespace.
  - Convert to kebab-case slug: lowercase, spaces → hyphens, strip all
    non-alphanumeric characters except hyphens.
  - If the resulting slug is empty after stripping, skip that entry and inform the
    user: "Skipping '<name>' — could not produce a valid filename."

  Do not proceed to Step 2 until all three questions have been answered (or skipped).

  ### 2. Backup existing content

  Before modifying or deleting any file:

  ```bash
  mkdir -p .backup/raw .backup/wiki
  cp -r raw/. .backup/raw/ 2>&1
  cp -r wiki/. .backup/wiki/ 2>&1
  ```

  Count backed-up files:

  ```bash
  find .backup/raw .backup/wiki -type f | wc -l
  ```

  Report: "Backed up N files to `.backup/` (raw/ and wiki/)."

  **If either `cp` command fails:** Stop immediately. Do not delete or overwrite any
  file. Report: "Backup failed: <error>. Aborting init — no files have been modified."

  ### 3. Update .gitignore

  Check if `.gitignore` already contains `raw/*`:

  ```bash
  grep -qF 'raw/*' .gitignore 2>/dev/null && echo "present" || echo "absent"
  ```

  - If **absent**: append to `.gitignore`:
    ```
    
    # Wiki raw sources
    raw/*
    !raw/.gitkeep
    ```

  Check for `.backup/` in `.gitignore`:

  ```bash
  grep -qF '.backup/' .gitignore 2>/dev/null && echo "present" || echo "absent"
  ```

  - If **absent**: append to `.gitignore`:
    ```
    
    # Wiki backup
    .backup/
    ```

  - If all lines were already present: report "`.gitignore` already up to date."
  - If `.gitignore` does not exist: create it containing only the two sections above.

  ### 4. Clean wiki subdirectories and raw/

  Remove all content-bearing files, then place `.gitkeep` in each directory:

  ```bash
  for dir in wiki/concepts wiki/entities wiki/sources wiki/analyses; do
    if [ -d "$dir" ]; then
      find "$dir" -type f -not -name '.gitkeep' -delete
    else
      mkdir -p "$dir"
    fi
    touch "$dir/.gitkeep"
  done

  find raw -type f -not -name '.gitkeep' -delete
  ```

  Do **not** touch:
  - `wiki/.obsidian/` (Obsidian config — leave as-is)
  - `wiki/index.md` and `wiki/log.md` — overwritten in Steps 6 and 7, not deleted here
  - `CLAUDE.md`, `README.md`, `llm-wiki.md`, `skills/`, `docs/`

  ### 5. Create stub pages

  For each entity name provided in Q2:

  Write `wiki/entities/<slug>.md`:
  ```markdown
  # <Entity Name>

  _Stub — to be filled by wiki-ingest._

  ## Notes

  ```

  For each concept name provided in Q3:

  Write `wiki/concepts/<slug>.md`:
  ```markdown
  # <Concept Name>

  _Stub — to be filled by wiki-ingest._

  ## Notes

  ```

  If the user provided no entities or no concepts, skip that category silently.

  ### 6. Write wiki/index.md

  Write the complete file (overwrites the old index):

  ```markdown
  # <Topic Title>

  <User's topic description verbatim from Q1>

  ## Sources

  ## Entities

  - [<Entity Name>](entities/<slug>.md) — (stub)

  ## Concepts

  - [<Concept Name>](concepts/<slug>.md) — (stub)

  ## Analyses

  ```

  If no stubs were created for Entities or Concepts, leave that section's body empty
  (keep the `##` header).

  ### 7. Write wiki/log.md

  Write the complete file (this is a reset — do not append to the old log):

  ```markdown
  ## [YYYY-MM-DD] init | <Topic Title>
  Backed up: raw/ and wiki/ (N files total) → .backup/
  Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
  Stubs created: <comma-separated list of stub page filenames, or "none">
  .gitignore: <"updated" or "already up to date">
  ```

  ### 8. Rebuild qmd index

  ```bash
  qmd update --collection wiki 2>/dev/null || true
  ```

  If output before the forced exit-0 suggests failure, warn: "qmd index update may
  have failed — run `qmd update --collection wiki` manually if searches return
  stale results."

  Report: "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

  ---

  ## What good initialization looks like

  After a successful init:
  - `.backup/` holds the full previous state of `raw/` and `wiki/`.
  - `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/analyses/` each
    contain only `.gitkeep`.
  - `wiki/index.md` opens with the new topic heading and lists only the newly
    created stubs.
  - `wiki/log.md` contains exactly one entry dated today.
  - `raw/` contains only `raw/.gitkeep`.
  - `.gitignore` excludes `raw/*` and `.backup/`.
  - `qmd status --collection wiki` shows a freshly updated index.

  The human can now run `wiki-ingest` on any source to begin building real content
  into the scaffold.
  ```

---

### T003 — Verify SKILL.md written correctly

- [ ] **T003** Verify `skills/wiki-init/SKILL.md` exists and has expected structure:
  ```bash
  ls -la /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-init/SKILL.md
  head -5 /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-init/SKILL.md
  grep -c '###' /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-init/SKILL.md
  ```
  Expected:
  - File exists with non-zero size
  - First lines show `---` / `name: wiki-init`
  - At least 8 `###` section headers (Steps 1–8)

---

### T004 — Commit the skill file

- [ ] **T004** Stage and commit `skills/wiki-init/SKILL.md`:
  ```bash
  git add skills/wiki-init/SKILL.md
  git commit -m "$(cat <<'EOF'
  feat(wiki-init): add wiki-init skill

  Guided 8-step workflow: collect topic, backup raw/ and wiki/, update
  .gitignore, clean example content, create stubs, reset index/log, rebuild qmd index.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```
  Expected: commit succeeds, `git log --oneline -1` shows the commit message.

---

## Sequential: Phase 2 — Apply Production Init

*T001–T004 must be complete before starting this phase.*

### T005 — Backup raw/ and wiki/

- [ ] **T005** Run backup — copy full contents of `raw/` and `wiki/` to `.backup/`:
  ```bash
  mkdir -p .backup/raw .backup/wiki
  cp -r raw/. .backup/raw/
  cp -r wiki/. .backup/wiki/
  find .backup/raw .backup/wiki -type f | wc -l
  ```
  Expected: copy completes without error; file count > 0 (current repo has 6 PDFs + ~30 wiki pages).
  If either `cp` fails: **abort Phase 2** — make no further changes.

---

### T006 — Verify backup is complete

- [ ] **T006** Verify AC-2.1 — Given `raw/` and `wiki/` contain files When backup runs Then `.backup/raw/` and `.backup/wiki/` are non-empty:
  ```bash
  find .backup/raw -type f | head -5
  find .backup/wiki -type f | head -5
  ```
  Expected: at least 1 file listed under each path.

---

### T007 — Update .gitignore

- [ ] **T007** Check which lines are missing, then append them using the Edit tool on `/Users/hllj/Projects/LLM-Wiki-Notebook/.gitignore`. Append the following block at the end of the file for any absent sections:
  ```
  
  # Wiki raw sources
  raw/*
  !raw/.gitkeep
  
  # Wiki backup
  .backup/
  
  # qmd local index
  .qmd/
  ```
  Check each section independently and append only absent sections.
  If all three are already present, skip and note "`.gitignore` already up to date."

---

### T008 — Verify .gitignore changes (AC-3.1, AC-3.2, AC-3.3)

- [ ] **T008** Verify AC-3.1 + AC-3.2 — Given `.gitignore` exists When updated Then it contains both sections without duplicates:
  ```bash
  grep -n 'raw/\*' /Users/hllj/Projects/LLM-Wiki-Notebook/.gitignore
  grep -n '!raw/.gitkeep' /Users/hllj/Projects/LLM-Wiki-Notebook/.gitignore
  grep -n '\.backup/' /Users/hllj/Projects/LLM-Wiki-Notebook/.gitignore
  grep -c 'raw/\*' /Users/hllj/Projects/LLM-Wiki-Notebook/.gitignore
  grep -c '\.backup/' /Users/hllj/Projects/LLM-Wiki-Notebook/.gitignore
  ```
  Expected: each line appears exactly once (count = 1).

---

### T009 — Clean wiki subdirectories and raw/

- [ ] **T009** Delete all content files from the four wiki subdirs and from raw/, then place `.gitkeep` in each:
  ```bash
  for dir in wiki/concepts wiki/entities wiki/sources wiki/analyses; do
    if [ -d "$dir" ]; then
      find "$dir" -type f -not -name '.gitkeep' -delete
    else
      mkdir -p "$dir"
    fi
    touch "$dir/.gitkeep"
  done
  find raw -type f -not -name '.gitkeep' -delete
  ```
  Expected: no error output.

---

### T010 — Verify cleanup (AC-2.3, AC-2.4)

- [ ] **T010** Verify AC-2.3 + AC-2.4 — Given backup is complete When cleanup runs Then only `.gitkeep` remains in each dir:
  ```bash
  find wiki/concepts wiki/entities wiki/sources wiki/analyses raw -type f | sort
  ```
  Expected: exactly 5 lines, each ending in `.gitkeep`.
  ```bash
  ls wiki/.obsidian/ && ls CLAUDE.md && ls skills/ && ls docs/
  ```
  Expected: all present (protected files untouched).

---

### T011 — Collect topic from user [INTERACTIVE]

- [ ] **T011** ⚠️ **INTERACTIVE — requires human input before proceeding.**
  Ask the user three questions in sequence:
  1. "What is this wiki about? Describe the topic or project in 1–3 sentences." *(required)*
  2. "Name up to 5 key entities (people, models, systems, papers, tools) this wiki should track. Separate with commas, or press Enter to skip."
  3. "Name up to 5 key concepts (ideas, techniques, frameworks, phenomena) this wiki should track. Separate with commas, or press Enter to skip."

  Record:
  - `TOPIC_DESCRIPTION` = user's answer to Q1 (abort if empty)
  - `TOPIC_TITLE` = first 4–5 significant words, title-cased
  - `ENTITY_NAMES` = list from Q2 (may be empty)
  - `CONCEPT_NAMES` = list from Q3 (may be empty)

  For each name: derive kebab-case slug (lowercase, spaces→hyphens, strip non-alphanumeric except hyphens). Skip any name whose slug would be empty.

  Do not proceed to T012 until user has answered all three prompts.

---

### T012 — Create stub pages

- [ ] **T012** For each entity name from T011: write `wiki/entities/<slug>.md` using the Write tool:
  ```markdown
  # <Entity Name>

  _Stub — to be filled by wiki-ingest._

  ## Notes

  ```
  For each concept name from T011: write `wiki/concepts/<slug>.md`:
  ```markdown
  # <Concept Name>

  _Stub — to be filled by wiki-ingest._

  ## Notes

  ```
  If no entities or concepts were provided, skip silently.

  Verify AC-1.4: each stub file exists and has the correct 4-line structure:
  ```bash
  find wiki/entities wiki/concepts -name '*.md' -not -name '.gitkeep' | sort
  ```
  Expected: one `.md` file per named entity/concept (zero if user skipped both).

---

### T013 — Write wiki/index.md

- [ ] **T013** Write the complete `wiki/index.md` file using the Write tool. Content (substitute actual values from T011):
  ```markdown
  # <TOPIC_TITLE>

  <TOPIC_DESCRIPTION>

  ## Sources

  ## Entities

  - [<Entity Name>](entities/<slug>.md) — (stub)
  [one line per entity; omit section body if no entities]

  ## Concepts

  - [<Concept Name>](concepts/<slug>.md) — (stub)
  [one line per concept; omit section body if no concepts]

  ## Analyses

  ```

  Verify AC-4.1 + AC-4.2:
  ```bash
  head -5 wiki/index.md
  grep -i "visual\|vlm\|covt\|spatial\|qwen\|reasoning" wiki/index.md || echo "clean — no legacy content"
  ```
  Expected: file starts with `# <TOPIC_TITLE>`; grep returns `clean`.

---

### T014 — Write wiki/log.md

- [ ] **T014** Write the complete `wiki/log.md` file using the Write tool. Content:
  ```markdown
  ## [2026-05-24] init | <TOPIC_TITLE>
  Backed up: raw/ and wiki/ (N files total) → .backup/
  Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
  Stubs created: <comma-separated stub filenames, or "none">
  .gitignore: updated
  ```
  (Replace N with the actual file count from T005; fill in stub filenames from T012.)

  Verify AC-4.3:
  ```bash
  grep -c '^## ' wiki/log.md
  cat wiki/log.md
  ```
  Expected: count = 1; single init entry visible.

---

### T015 — Set up qmd project-local index and collection (AC-5.1–AC-5.4)

`<collection-slug>` = kebab-case slug of the topic title from T011.

- [ ] **T015a** Initialize project-local index:
  ```bash
  qmd init 2>/dev/null || true
  ls .qmd/ 2>/dev/null && echo "ok" || echo "missing"
  ```
  Expected: `.qmd/` folder exists. If missing, warn the user to run `qmd init` manually.

- [ ] **T015b** Check and register collection:
  ```bash
  qmd collection list 2>/dev/null || true
  ```
  If `<collection-slug>` is absent:
  ```bash
  qmd collection add ./wiki --name <collection-slug> 2>/dev/null || true
  ```

- [ ] **T015c** Confirm collection is listed:
  ```bash
  qmd collection list 2>/dev/null || true
  ```
  Expected: `<collection-slug>` appears in output. Report to user (AC-5.3).

- [ ] **T015d** Build the index:
  ```bash
  qmd update --collection <collection-slug> 2>/dev/null || true
  qmd status --collection <collection-slug> 2>/dev/null || true
  ```
  Expected: qmd reports an updated index. If output suggests failure before forced exit-0, warn the user to run `qmd update --collection <collection-slug>` manually.

---

### T016 — Commit all production init changes

- [ ] **T016** Stage and commit all production init changes:
  ```bash
  git add .gitignore wiki/index.md wiki/log.md
  git add wiki/concepts/ wiki/entities/ wiki/sources/ wiki/analyses/
  git add raw/
  git status
  git commit -m "$(cat <<'EOF'
  feat(wiki-init): apply production init — backup, clean, scaffold new topic

  Backed up raw/ and wiki/ to .backup/. Cleaned example VLM content from
  wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/.
  Updated .gitignore to exclude raw/* and .backup/. Reset index.md and
  log.md for new topic.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```
  Expected: commit succeeds. `git status` shows clean working tree.

---

## Sequential: Phase 3 — Integration Verification

*All prior tasks must be complete.*

### T017 — Verify all acceptance criteria

- [ ] **T017** Run full integration check:

  **AC-2.1** — `.backup/` holds pre-init content:
  ```bash
  find .backup/raw -type f | wc -l
  find .backup/wiki -type f | wc -l
  ```
  Expected: both counts > 0.

  **AC-2.3** — Wiki subdirs contain only `.gitkeep`:
  ```bash
  find wiki/concepts wiki/entities wiki/sources wiki/analyses -type f | sort
  ```
  Expected: 4 lines, each `.gitkeep`.

  **AC-2.4** — `raw/` contains only `.gitkeep`:
  ```bash
  find raw -type f | sort
  ```
  Expected: 1 line: `raw/.gitkeep`.

  **AC-3.1 + AC-3.2** — `.gitignore` contains both sections:
  ```bash
  grep 'raw/\*' .gitignore && grep '!raw/.gitkeep' .gitignore && grep '\.backup/' .gitignore
  ```
  Expected: all three lines matched.

  **AC-4.2** — `wiki/index.md` begins with topic heading:
  ```bash
  head -3 wiki/index.md
  ```
  Expected: first line is `# <TOPIC_TITLE>`.

  **AC-4.3** — `wiki/log.md` has exactly one entry:
  ```bash
  grep -c '^## ' wiki/log.md
  ```
  Expected: `1`.

  **AC-5.2** — qmd can find stub pages:
  ```bash
  qmd search "stub" --collection wiki --json --limit 3 2>/dev/null || true
  ```
  Expected: returns 0–N results without error (0 is fine if no stubs were created).

  **AC-1.4** (if stubs were created) — each stub has correct 4-line format:
  ```bash
  find wiki/entities wiki/concepts -name '*.md' -exec head -5 {} \; 2>/dev/null
  ```
  Expected: H1 title, `_Stub — to be filled by wiki-ingest._`, blank, `## Notes`.

  If all checks pass: report "All acceptance criteria verified. Wiki init complete."

---

## Task Summary

| Range | Phase | Can Parallelize? | Spec ACs Covered |
|-------|-------|-----------------|-----------------|
| T001–T004 | Write skill file | No | All ACs (skill encodes them) |
| T005–T006 | Backup | No | AC-2.1, AC-2.2 |
| T007–T008 | .gitignore update | No | AC-3.1, AC-3.2, AC-3.3 |
| T009–T010 | Cleanup | No | AC-2.3, AC-2.4 |
| T011 | Collect topic [interactive] | No | AC-1.1, AC-1.2, AC-1.3 |
| T012 | Create stubs | No | AC-1.4, AC-1.5 |
| T013–T014 | Reset index + log | No | AC-4.1, AC-4.2, AC-4.3 |
| T015 | qmd update | No | AC-5.1, AC-5.2 |
| T016 | Commit production init | No | — |
| T017 | Integration verification | No | All ACs |

**Total tasks:** 17
**Parallelizable tasks:** 0 (all steps depend on prior step output or filesystem state)
**Estimated time:** 15–20 minutes end-to-end (T011 blocked on user input)
