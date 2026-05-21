---
name: wiki-lint
description: >
  Health-checks the LLM wiki for structural problems, stale content, and missing
  connections. Use this skill when the user asks to "lint the wiki", "health-check
  the wiki", "check for issues", "clean up the wiki", "find orphan pages", "check
  for contradictions", or any request to audit or improve the wiki's internal
  consistency and completeness. Also trigger proactively after the wiki has grown
  significantly (many ingests) or when the user mentions the wiki feels messy or
  hard to navigate.
---

# Wiki Lint

You are health-checking the wiki. Your job is to find what's broken, stale, disconnected, or missing — and report it clearly so the human can decide what to fix.

## Workflow

### 1. Check index health

Read `wiki/index.md` to get the full map of what exists. Also run:

```bash
qmd status --collection wiki
```

This surfaces any files that are in the collection but not yet indexed (new pages that weren't re-indexed after creation) and gives you a quick count of documents vs chunks.

### 2. Scan for each issue type

Use qmd for targeted scanning rather than reading every page. Work through these checks:

**Contradictions**

Search for pages that already have contradiction notes, then look for thematic overlaps that might hide hidden conflicts:

```bash
qmd search "contradicts" --collection wiki --json
qmd search "Note updated" --collection wiki --json
```

Read pages that appear in both a newer and older source context on the same topic. Flag where two pages assert incompatible facts and note which source is newer.

**Stale claims**

Cross-reference `wiki/log.md` for timeline. Run thematic queries to surface pages covering the same topic:

```bash
qmd query "<topic area>" --collection wiki --json --limit 10
```

Pages from early ingests that are now superseded by higher-scoring newer pages are the likeliest staleness candidates.

**Orphan pages**

```bash
qmd status --collection wiki
```

Then check each wiki page's content for outbound links and scan other pages for inbound links to it. A page is an orphan if no other wiki page links to it. Cross-check against the index: every indexed page should have at least one inbound link from another wiki page.

**Hub page identification**

Run 4–6 broad thematic queries and note which pages appear in multiple result sets. These are hub pages — the ones most likely to have stale cross-references or missing links, since they're referenced across many topics.

```bash
qmd query "<theme 1>" --collection wiki --json --limit 8
qmd query "<theme 2>" --collection wiki --json --limit 8
# etc.
```

**Missing concept pages**

```bash
qmd search "<term that appears frequently>" --collection wiki --json
```

If a term appears in 3+ page snippets but has no concept page in the index, it probably warrants one. Read the snippets to confirm the term is used substantively (not just mentioned in passing).

**Missing cross-references**

Pages that share high semantic similarity but don't link to each other:

```bash
qmd vsearch "<page title or key claim>" --collection wiki --json --limit 8
```

If two pages both score high for the same query but neither links to the other, that's a missing cross-reference.

**Data gaps**

Topics where qmd returns low scores (< 0.3) or thin snippets. These are candidates for new sources to ingest.

**Log gaps**

Check `wiki/log.md` for anything inconsistent with the index. Pages mentioned in the log but absent from the index, or index pages with no log entry, indicate bookkeeping drift.

### 3. Report findings

Present findings as a numbered list, grouped by issue type. For each issue:
- Name the specific page(s) involved
- Explain the problem concisely
- Suggest the fix (or note that a new source is needed to resolve it)

Example format:
```
## Contradictions
1. wiki/entities/x.md claims A, but wiki/sources/y.md (ingested later) says B. Update x.md to reflect y.md's finding.

## Orphan pages
2. wiki/concepts/z.md has no inbound links. Link to it from wiki/entities/a.md and wiki/sources/b.md where it's discussed.

## Missing concept pages
3. "transfer learning" appears in 4 page snippets but has no concept page. Create wiki/concepts/transfer-learning.md.

## Hub pages needing review
4. wiki/concepts/visual-reasoning-in-vlms.md appeared in 5 of 6 thematic queries — high risk of stale cross-references. Review its links section.
```

### 4. Fix issues (if asked)

If the human says to fix some or all issues:
- Apply fixes directly — update pages, add cross-links, create missing stubs
- For contradictions: update the older page with an inline note using the contradiction format:
  > **Note (updated YYYY-MM-DD):** [newer source](../sources/slug.md) supersedes the above — [brief explanation].
- For missing pages: create stub pages with a `## To do` section noting what information is needed
- After all fixes, run `qmd update --collection wiki` to re-index changes

Don't fix issues that require a new source to resolve — flag those for the human to handle.

### 5. Update the log

After completing the lint pass (whether or not you made fixes):

```
## [YYYY-MM-DD] lint
Issues found: [N total — X contradictions, Y orphans, Z missing pages, W hub pages flagged]
Fixed: [what was fixed, or "none — awaiting human review"]
Flagged for new sources: [any gaps that need external information to resolve]
```

## What good linting looks like

A lint pass should leave the human with a clear action list — not a vague sense that "things could be better." Every finding should name specific pages and suggest a concrete next step. The goal is a wiki that gets tighter and more connected over time, not one that accumulates debt.

The qmd-based approach means you don't need to read every page to find problems. Use the search results as a map — they surface which pages cluster together, which stand alone, and which have the most semantic weight. Focus your reading effort on the pages qmd flags as most important, not a full sequential scan.

If the wiki is small and clean, say so. A short "wiki looks healthy" with a few minor suggestions is a valid outcome.
