# Tasks: Wiki Gap Research via Web Search

**Spec:** `docs/specs/001-wiki-gap-research/spec.md`  
**Plan:** `docs/specs/001-wiki-gap-research/plan.md`  
**Date:** 2026-05-22  
**Version:** 2.0.0  

---

## Phase 1 — Update wiki-query step 5

### T01 — Verify NLM skills are removed

```bash
ls /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-sync/ 2>&1
ls /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-nlm-research/ 2>&1
```

Expected: both return `No such file or directory`.

---

### T02 — Verify wiki-query step 5 contains web search handoff

```bash
grep -n "Web search gap handoff" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md
grep -n "WebSearch" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md
grep -n "re-run wiki-query" /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md
```

Expected: all three return matches. No mention of `nlm`, `notebooklm`, or `wiki-nlm-research` in the file.

---

### T03 — Verify no NLM references remain in wiki-query

```bash
grep -in "notebooklm\|wiki-nlm\|nlm login\|nlm notebook" \
  /Users/hllj/Projects/LLM-Wiki-Notebook/skills/wiki-query/SKILL.md
```

Expected: no output.

---

### T04 — Verify nlm-notebooks registry is empty

```bash
cat /Users/hllj/Projects/LLM-Wiki-Notebook/wiki/nlm-notebooks.md
```

Expected: file contains the header and empty table (no data rows).

---

### T05 — Verify wiki-ingest and wiki-lint are untouched

```bash
git -C /Users/hllj/Projects/LLM-Wiki-Notebook diff skills/wiki-ingest/ skills/wiki-lint/
```

Expected: no output (no changes).

---

### T06 — Verify only expected files are changed

```bash
git -C /Users/hllj/Projects/LLM-Wiki-Notebook status
```

Expected modified/deleted files:
- `skills/wiki-query/SKILL.md` — modified
- `skills/wiki-nlm-sync/SKILL.md` — deleted
- `skills/wiki-nlm-research/SKILL.md` — deleted
- `docs/specs/001-wiki-gap-research/spec.md` — modified
- `docs/specs/001-wiki-gap-research/plan.md` — modified
- `docs/specs/001-wiki-gap-research/tasks.md` — modified

Pre-existing unrelated changes (`CLAUDE.md`, `.claude/settings.json`) are expected and not part of this feature.

---

### T07 — Commit all changes

```bash
git -C /Users/hllj/Projects/LLM-Wiki-Notebook add \
  skills/wiki-query/SKILL.md \
  skills/wiki-nlm-sync/SKILL.md \
  skills/wiki-nlm-research/SKILL.md \
  wiki/nlm-notebooks.md \
  docs/specs/001-wiki-gap-research/spec.md \
  docs/specs/001-wiki-gap-research/plan.md \
  docs/specs/001-wiki-gap-research/tasks.md

git -C /Users/hllj/Projects/LLM-Wiki-Notebook commit -m "$(cat <<'EOF'
feat(wiki-query): v2.0.0 — replace NLM integration with web-search gap handoff

Remove wiki-nlm-sync and wiki-nlm-research skills entirely. Replace the
NotebookLM gap escalation in wiki-query step 5 with a native web-search
flow: gap detected → WebSearch → user picks source → save to raw/ →
wiki-ingest → optional re-query. No external CLI or auth required.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds with the listed files.
