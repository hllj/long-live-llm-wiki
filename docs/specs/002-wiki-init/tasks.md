# Tasks: Wiki Init (v2.0.0)

**Plan:** docs/specs/002-wiki-init/plan.md
**Spec:** docs/specs/002-wiki-init/spec.md
**Updated:** 2026-05-25

> **For agentic workers:** Execute tasks in order. Never start an implementation task without the prior verification task completed.
>
> **T006 is interactive** — it requires calling `AskUserQuestion` to collect the wiki topic before proceeding.

---

## Sequential: Phase 1 — Rewrite wiki-init Skill

### T001 — Rewrite skills/wiki-init/SKILL.md

- [ ] **T001** Overwrite `skills/wiki-init/SKILL.md` with the 7-step v2.0.0 workflow. Use the Write tool with file path `skills/wiki-init/SKILL.md`. The skill must:
  - Step 1: Use `AskUserQuestion` tool to collect topic description (single question, not sequential text prompts). Re-prompt if empty. Derive topic title (title-cased, first 4–5 significant words) and collection slug (kebab-case).
  - Step 2: Update `.gitignore` — check and append `raw/*`, `!raw/.gitkeep`, `.qmd/` under labeled sections. No `.backup/` entry.
  - Step 3: Clean wiki subdirs and `raw/` — delete non-.gitkeep files, place `.gitkeep` in each of `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/analyses/`, and `raw/`.
  - Step 4: Generate `CLAUDE.md` — write a complete operational schema to repo root using the Write tool, parameterized with topic title, description, and collection slug. qmd commands must use the actual collection slug (not the literal string `wiki`).
  - Step 5: Write `wiki/index.md` — full file: `# <Topic Title>`, topic description, four empty section headers (Sources, Entities, Concepts, Analyses).
  - Step 6: Write `wiki/log.md` — single init entry: `## [YYYY-MM-DD] init | <Topic Title>` with cleanup summary and .gitignore state.
  - Step 7: qmd setup — `qmd init`, check/register collection, `qmd collection list`, `qmd update --collection <collection-slug>`. Report "Wiki initialized. Drop sources into `raw/` and run `wiki-ingest` to begin."

---

### T002 — Verify SKILL.md structure

- [ ] **T002** Verify `skills/wiki-init/SKILL.md` has expected structure:
  ```bash
  ls -la skills/wiki-init/SKILL.md
  grep -c '###' skills/wiki-init/SKILL.md
  grep 'AskUserQuestion' skills/wiki-init/SKILL.md
  grep -v 'backup' skills/wiki-init/SKILL.md | grep -i backup || echo "no backup references"
  grep -v 'entit\|concept' skills/wiki-init/SKILL.md | grep -i 'stub\|Q2\|Q3' || echo "no entity/concept prompts"
  ```
  Expected:
  - File exists, non-zero size
  - At least 7 `###` section headers
  - `AskUserQuestion` appears at least once
  - No backup step references
  - No entity/concept Q2/Q3 prompts

---

### T003 — Commit skill rewrite

- [ ] **T003** Stage and commit `skills/wiki-init/SKILL.md`:
  ```bash
  git add skills/wiki-init/SKILL.md
  git commit -m "$(cat <<'EOF'
  feat(wiki-init): rewrite skill to v2.0.0

  - Use AskUserQuestion tool for topic collection (replaces sequential text prompts)
  - Remove backup step
  - Remove entity/concept prompts and stub creation
  - Add CLAUDE.md generation step (topic-specific operational schema)
  - Simplify index.md (no stub entries)

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```
  Expected: commit succeeds.

---

## Sequential: Phase 2 — Apply Production Init

*T001–T003 must be complete before starting this phase.*

### T004 — Update .gitignore

- [ ] **T004** Check which lines are missing, append only absent sections using the Edit tool on `.gitignore`:
  ```bash
  grep -qF 'raw/*' .gitignore 2>/dev/null && echo "raw/* present" || echo "raw/* absent"
  grep -qF '.qmd/' .gitignore 2>/dev/null && echo ".qmd/ present" || echo ".qmd/ absent"
  ```
  Append missing blocks:
  ```
  # Wiki raw sources
  raw/*
  !raw/.gitkeep

  # qmd local index
  .qmd/
  ```
  If all present: note "`.gitignore` already up to date." and skip.

---

### T005 — Verify .gitignore (AC-4.1, AC-4.2, AC-4.3)

- [ ] **T005** Verify:
  ```bash
  grep -n 'raw/\*' .gitignore
  grep -n '!raw/.gitkeep' .gitignore
  grep -n '\.qmd/' .gitignore
  grep -c 'raw/\*' .gitignore
  grep -c '\.qmd/' .gitignore
  ```
  Expected: each line appears exactly once (count = 1). No `.backup/` entry added.

---

### T006 — Collect topic from user [INTERACTIVE]

- [ ] **T006** ⚠️ **INTERACTIVE — call `AskUserQuestion` before proceeding.**

  Use `AskUserQuestion` tool with:
  - question: "What is this wiki about? Describe the topic or project in 1–3 sentences."
  - header: "Wiki Topic"
  - options: provide a text input option

  Record:
  - `TOPIC_DESCRIPTION` = user's answer (abort if empty; re-prompt)
  - `TOPIC_TITLE` = first 4–5 significant words, title-cased
  - `COLLECTION_SLUG` = kebab-case of TOPIC_TITLE

  Do not proceed to T007 until user has provided a non-empty topic.

---

### T007 — Clean wiki subdirectories and raw/

- [ ] **T007** Delete all content files from the four wiki subdirs and from raw/, then place `.gitkeep` in each:
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

### T008 — Verify cleanup (AC-2.1, AC-2.2, AC-2.3)

- [ ] **T008** Verify:
  ```bash
  find wiki/concepts wiki/entities wiki/sources wiki/analyses raw -type f | sort
  ```
  Expected: exactly 5 lines, each ending in `.gitkeep`.
  ```bash
  ls wiki/.obsidian/ && ls skills/ && ls docs/ && ls README.md
  ```
  Expected: all present (protected files untouched).

---

### T009 — Generate CLAUDE.md (AC-3.1, AC-3.2, AC-3.3)

- [ ] **T009** Write `CLAUDE.md` at repo root using the Write tool. Content must be parameterized with TOPIC_TITLE, TOPIC_DESCRIPTION, and COLLECTION_SLUG from T006. Include all sections:
  - Header: "What this repo is" with three-layer explanation (raw/, wiki/, CLAUDE.md), topic title and description
  - qmd command reference: all standard commands (`query`, `search`, `vsearch`, `get`, `status`, `update`, `embed`) with `--collection COLLECTION_SLUG` and `2>/dev/null || true`
  - Score thresholds (≥0.6, 0.3–0.59, <0.3)
  - Operations: Ingest (8-step), Query (4-step), Lint (5-step)
  - Wiki page conventions
  - Index format (Sources, Entities, Concepts, Analyses)
  - Log format
  - Scope section naming TOPIC_TITLE

  Verify (AC-3.3):
  ```bash
  grep "collection $COLLECTION_SLUG" CLAUDE.md | head -3
  grep 'collection wiki' CLAUDE.md || echo "no literal 'wiki' collection references"
  ```
  Expected: collection slug appears; no literal `--collection wiki` remains.

---

### T010 — Write wiki/index.md (AC-5.1, AC-5.2)

- [ ] **T010** Write the complete `wiki/index.md` using the Write tool:
  ```markdown
  # <TOPIC_TITLE>

  <TOPIC_DESCRIPTION>

  ## Sources

  ## Entities

  ## Concepts

  ## Analyses

  ```

  Verify:
  ```bash
  head -5 wiki/index.md
  grep -c '^## ' wiki/index.md
  ```
  Expected: first line is `# <TOPIC_TITLE>`; 4 section headers.

---

### T011 — Write wiki/log.md (AC-5.3)

- [ ] **T011** Write the complete `wiki/log.md` using the Write tool:
  ```markdown
  ## [2026-05-25] init | <TOPIC_TITLE>
  Cleaned: wiki/concepts/, wiki/entities/, wiki/sources/, wiki/analyses/, raw/
  .gitignore: <"updated" or "already up to date">
  CLAUDE.md: generated (collection: <COLLECTION_SLUG>)
  ```

  Verify:
  ```bash
  grep -c '^## ' wiki/log.md
  cat wiki/log.md
  ```
  Expected: count = 1; single init entry visible.

---

### T012 — Set up qmd project-local index and collection (AC-6.1–AC-6.4)

`<COLLECTION_SLUG>` = kebab-case slug from T006.

- [ ] **T012a** Initialize project-local index:
  ```bash
  qmd init 2>/dev/null || true
  ls .qmd/ 2>/dev/null && echo "ok" || echo "missing"
  ```
  Expected: `.qmd/` folder exists. If missing, warn user to run `qmd init` manually.

- [ ] **T012b** Check and register collection:
  ```bash
  qmd collection list 2>/dev/null || true
  ```
  If `<COLLECTION_SLUG>` is absent:
  ```bash
  qmd collection add ./wiki --name <COLLECTION_SLUG> 2>/dev/null || true
  ```

- [ ] **T012c** Confirm collection is listed (AC-6.3):
  ```bash
  qmd collection list 2>/dev/null || true
  ```
  Expected: `<COLLECTION_SLUG>` appears. Report to user.

- [ ] **T012d** Build the index (AC-6.4):
  ```bash
  qmd update --collection <COLLECTION_SLUG> 2>/dev/null || true
  qmd status --collection <COLLECTION_SLUG> 2>/dev/null || true
  ```
  Expected: index updated. Warn if output suggests failure.

---

### T013 — Commit all production init changes

- [ ] **T013** Stage and commit all production init changes:
  ```bash
  git add CLAUDE.md .gitignore wiki/index.md wiki/log.md
  git add wiki/concepts/ wiki/entities/ wiki/sources/ wiki/analyses/
  git add raw/
  git status
  git commit -m "$(cat <<'EOF'
  feat(wiki-init): apply production init v2.0.0 — clean, generate CLAUDE.md, scaffold new topic

  Cleaned example content from wiki/concepts/, wiki/entities/, wiki/sources/,
  wiki/analyses/, raw/. Generated CLAUDE.md with topic-specific qmd collection
  slug. Reset index.md and log.md. Updated .gitignore.

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```
  Expected: commit succeeds. `git status` shows clean working tree.

---

## Sequential: Phase 3 — Integration Verification

*All prior tasks must be complete.*

### T014 — Verify all acceptance criteria

- [ ] **T014** Run full integration check:

  **AC-2.1** — Wiki subdirs contain only `.gitkeep`:
  ```bash
  find wiki/concepts wiki/entities wiki/sources wiki/analyses -type f | sort
  ```
  Expected: 4 lines, each `.gitkeep`.

  **AC-2.2** — `raw/` contains only `.gitkeep`:
  ```bash
  find raw -type f | sort
  ```
  Expected: 1 line: `raw/.gitkeep`.

  **AC-3.3** — CLAUDE.md uses collection slug, not literal `wiki`:
  ```bash
  grep 'collection wiki' CLAUDE.md || echo "clean"
  grep "collection " CLAUDE.md | head -3
  ```
  Expected: first grep returns `clean`; second shows actual slug.

  **AC-4.1 + AC-4.2** — `.gitignore` contains both sections:
  ```bash
  grep 'raw/\*' .gitignore && grep '!raw/.gitkeep' .gitignore && grep '\.qmd/' .gitignore
  ```
  Expected: all three lines matched.

  **AC-5.2** — `wiki/index.md` begins with topic heading:
  ```bash
  head -3 wiki/index.md
  ```
  Expected: first line is `# <TOPIC_TITLE>`.

  **AC-5.3** — `wiki/log.md` has exactly one entry:
  ```bash
  grep -c '^## ' wiki/log.md
  ```
  Expected: `1`.

  **AC-6.3** — collection slug in qmd list:
  ```bash
  qmd collection list 2>/dev/null || true
  ```
  Expected: `<COLLECTION_SLUG>` appears.

  If all checks pass: report "All acceptance criteria verified. Wiki init v2.0.0 complete."

---

## Task Summary

| Task | Phase | Description | Spec ACs |
|------|-------|-------------|----------|
| T001 | 1 | Rewrite SKILL.md | All ACs (skill encodes them) |
| T002 | 1 | Verify SKILL.md structure | — |
| T003 | 1 | Commit skill rewrite | — |
| T004 | 2 | Update .gitignore | AC-4.1, AC-4.2, AC-4.3 |
| T005 | 2 | Verify .gitignore | AC-4.1, AC-4.2, AC-4.3 |
| T006 | 2 | Collect topic [INTERACTIVE] | AC-1.1, AC-1.2, AC-1.3 |
| T007 | 2 | Clean wiki subdirs + raw/ | AC-2.1, AC-2.2 |
| T008 | 2 | Verify cleanup | AC-2.1, AC-2.2, AC-2.3 |
| T009 | 2 | Generate CLAUDE.md | AC-3.1, AC-3.2, AC-3.3 |
| T010 | 2 | Write wiki/index.md | AC-5.1, AC-5.2 |
| T011 | 2 | Write wiki/log.md | AC-5.3 |
| T012 | 2 | qmd setup | AC-6.1, AC-6.2, AC-6.3, AC-6.4 |
| T013 | 2 | Commit production init | — |
| T014 | 3 | Integration verification | All ACs |

**Total tasks:** 14
**Parallelizable tasks:** 0
**Estimated time:** 10–15 minutes end-to-end (T006 blocked on user input)
