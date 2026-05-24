# Plan: Wiki Gap Research via Web Search

**Spec:** `docs/specs/001-wiki-gap-research/spec.md`  
**Date:** 2026-05-22  
**Status:** Approved  
**Version:** 2.0.0 — replaces NotebookLM integration with web-search gap handoff in wiki-query  

---

## Goal

Update `skills/wiki-query/SKILL.md` step 5 so that when the wiki has a gap (score < 0.3), the skill offers to web-search for sources, saves the chosen result to `raw/<topic>/`, and offers to re-query after ingest. No new skills, no new registry files, no external CLI dependencies.

---

## Architecture

- **No new skills.** The entire feature lives in step 5 of `skills/wiki-query/SKILL.md`.
- **No new registry files.** `wiki/nlm-notebooks.md` remains as an empty placeholder (no content needed).
- **Tools used:** `WebSearch` and `WebFetch` — both natively available in Claude Code.
- **`wiki-ingest` is untouched.** It processes whatever lands in `raw/<topic>/` as always.
- **Removed:** `skills/wiki-nlm-sync/`, `skills/wiki-nlm-research/`, and all `.claude-plugin/skills/` symlinks for those skills.

---

## Tech Stack

| Concern | Choice | Justification |
|---|---|---|
| Gap research | `WebSearch` + `WebFetch` tools | Native to Claude Code; no auth, no CLI install |
| Raw storage | `raw/<topic>/` (existing pattern) | Consistent with wiki-ingest contract |
| Skill format | SKILL.md (existing) | No new format needed |

---

## File Structure

```
skills/
└── wiki-query/
    └── SKILL.md    ← MODIFIED (step 5 gap section — web search handoff)

skills/wiki-nlm-sync/       ← DELETED
skills/wiki-nlm-research/   ← DELETED
wiki/nlm-notebooks.md       ← EMPTIED (registry table with no rows)
```

Files NOT touched: `skills/wiki-ingest/`, `skills/wiki-lint/`, `wiki/index.md`, `wiki/log.md`, `.claude-plugin/plugin.json`.

---

## Phase 1 — Update wiki-query step 5

Single phase. One file to change.

**Covers:** FR-1, FR-2, FR-3, FR-4, FR-5, US-1, US-2, US-3

### 1.1 Rewrite step 5 of `skills/wiki-query/SKILL.md`

Replace the existing step 5 gap handling block with the following content:

```markdown
### 5. Handle low-confidence results

If the best qmd score is < 0.3 **and** the index scan also turned up nothing relevant, do not guess or extrapolate. This is valuable signal: it means the question has revealed a hole in the knowledge base. (If the index scan found something the search missed, that's a cross-referencing gap to note — not a content gap.)

**Web search gap handoff (seamless):**

1. Announce the gap:
   > "The wiki doesn't have strong coverage of this topic (best match score: 0.XX). This looks like a gap — want me to web-search and ingest a new source, or do you have a document to add to `raw/`?"

2. If the user says yes to web search: use the WebSearch tool to find 2–3 relevant sources (papers, blog posts, docs). Present the results with titles and URLs and ask which to ingest.

3. If the user provides a local file: proceed directly to `wiki-ingest`.

4. After ingest completes, offer exactly once:
   > "Want me to re-run wiki-query with the original question now that the wiki has been updated? (yes/no)"
   - If yes: re-execute wiki-query with the original question and report results.
   - If no: stop.
   - If re-query still scores below 0.3: report the still-open gap and stop — do not loop again.
```

---

## Self-Review

**Spec coverage:**
- FR-1 (gap threshold) → step 5 condition: score < 0.3 and index scan empty ✓
- FR-2 (web search) → step 5 web search offer + WebSearch/WebFetch ✓
- FR-3 (ingest handoff) → step 5 tells user exact wiki-ingest command ✓
- FR-4 (re-query loop) → step 5 one-shot re-query offer ✓
- FR-5 (wiki-query step 5) → this is the only file changed ✓
- US-1 → gap announcement + web search offer ✓
- US-2 → re-query offer after ingest ✓
- US-3 → local file path mentioned in gap message ✓

**Error scenarios:**
- No web results → report, suggest local file ✓ (covered by gap message wording)
- WebFetch failure → offer different result ✓ (implicit in offer step)
- raw/ missing → wiki-ingest creates it (out of scope for wiki-query) ✓
- Re-query still < 0.3 → stop, no second loop ✓

**Removed artifacts confirmed:**
- `skills/wiki-nlm-sync/SKILL.md` — deleted ✓
- `skills/wiki-nlm-research/SKILL.md` — deleted ✓
- `.claude-plugin/skills/wiki-nlm-sync` symlink — deleted (if it existed) ✓
- `.claude-plugin/skills/wiki-nlm-research` symlink — deleted (if it existed) ✓
