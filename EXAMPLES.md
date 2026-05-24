# Examples

Real use cases for Long Live LLM Wiki, from first setup through ongoing research workflows.

---

## 1. Bootstrap a new topic area

You've decided to track a new subject — say, VLM visual reasoning research. Before ingesting anything, tell Claude what entities and concepts matter so future ingests have somewhere to land.

```
I'm starting to track VLM visual reasoning research.
The key entities will be specific models (Qwen2.5-VL, LLaVA, Chameleon)
and benchmarks (VSI-Bench, V*Bench). Key concepts: chain-of-thought variants,
visual token types, spatial reasoning. Create stub pages for these.
```

Claude creates stub pages in `wiki/entities/` and `wiki/concepts/`, then updates `wiki/index.md`. Subsequent ingests will find and fill these stubs rather than creating duplicates.

---

## 2. Ingest a research paper

Drop the PDF into `raw/`, then ask Claude to process it.

```
process raw/2511.19418v2.pdf
```

Claude:
1. Reads the paper in full.
2. Runs `qmd query` to find which existing wiki pages are most affected (scored, ranked).
3. Asks if you want to emphasize anything; if not, proceeds immediately.
4. Writes `wiki/sources/covt-chain-of-visual-thought.md` with a structured summary.
5. Updates all entity and concept pages flagged by the impact scan.
6. Re-indexes with `qmd update`.
7. Appends to `wiki/log.md`.

A single paper typically touches 5–15 pages. That's normal — the wiki is supposed to grow laterally, not just vertically.

---

## 3. Ingest a batch of related papers

You have five papers from the same research thread. Drop them all into `raw/` and process them one by one in the same session. Claude maintains context across ingests and will note when a later paper contradicts or supersedes an earlier one — inline in the affected page:

```
process raw/paper-A.pdf
process raw/paper-B.pdf
process raw/paper-C.pdf
```

After each ingest, affected pages accumulate a richer cross-linked picture. By the third paper, Claude is finding connections you didn't notice.

---

## 4. Ask a synthesis question

Ask any question and Claude searches the wiki, synthesizes an answer, and cites the specific pages it drew from.

```
What techniques do VLMs use to reason visually, and what are the trade-offs?
```

Claude:
1. Reads `wiki/index.md` to map the full structure.
2. Runs `qmd query` with sub-queries to get ranked hits.
3. Reads full pages scoring ≥ 0.6, skims snippets for 0.3–0.59.
4. Synthesizes a structured answer with links to concept and entity pages.
5. Surfaces any contradictions it found across pages.
6. Offers to file the answer as `wiki/analyses/visual-thinking-techniques.md`.

The answer is grounded in what you've actually read — not the model's training data.

---

## 5. Compare two approaches

```
Compare CoVT and ICoT: same goal, different mechanism. Which handles spatial reasoning better?
```

Claude decomposes the question into sub-queries, reads both source summaries and the concept pages they share, and produces a comparison table covering mechanism, training requirements, benchmark results, and open problems. It flags where the evidence is thin or contradictory.

---

## 6. Hit a gap — trigger web search and ingest

```
What does the wiki say about GRPO training for VLMs?
```

If the wiki doesn't cover this (best match score < 0.3), Claude announces the gap and offers to search the web:

> "The wiki doesn't have strong coverage of GRPO (best match: 0.18). Want me to web-search for relevant sources?"

Say yes. Claude finds 2–3 papers or blog posts, shows you titles and URLs, and asks which to ingest. You pick one; Claude downloads it to `raw/`, runs the full ingest workflow, then offers to re-run the original query against the now-updated wiki.

---

## 7. File a query result as a wiki page

After a synthesis query, Claude offers to save the answer:

> "This analysis touches 4 concept pages and draws on 3 source summaries. Want me to file it as `wiki/analyses/vlm-reasoning-paradigms.md`?"

Say yes. The page is written, added to `wiki/index.md`, re-indexed, and logged. Now future queries can surface this synthesis directly without re-doing the work.

---

## 8. Health-check the wiki

Run a lint pass after a burst of ingests to find what drifted.

```
/wiki-lint
```

Claude:
1. Checks `qmd status` for index health and unindexed files.
2. Searches for contradiction markers and stale cross-references.
3. Finds orphan pages (no inbound links), hub pages (high semantic weight), and missing concept stubs.
4. Reports a numbered fix list — specific pages, concrete suggestions.

Example output:
```
## Orphan pages
1. wiki/concepts/grpo.md has no inbound links.
   Fix: link to it from wiki/entities/qwen2-5-vl.md and wiki/sources/mirage.md.

## Missing concept pages
2. "representation collapse" appears in 4 page snippets but has no concept page.
   Fix: create wiki/concepts/representation-collapse.md.

## Hub pages needing review
3. wiki/concepts/visual-reasoning-in-vlms.md appeared in 5 of 6 thematic queries.
   Its links section may be stale — review and update.
```

Tell Claude to fix them and it applies all changes, then re-indexes.

---

## 9. Use wiki-lint to find missed entities

After several ingests you may have sources that mention named models, benchmarks, or authors that were never given their own `wiki/entities/` page — they exist only as inline mentions scattered across other pages.

```
/wiki-lint
```

Claude scans for entity mentions that appear frequently in page snippets but have no corresponding entry in `wiki/index.md` under `## Entities`. It surfaces these as missing entity pages:

```
## Missing entity pages
1. "AdaptVis" appears in 5 page snippets (visual-reasoning-in-vlms.md,
   why-spatial-reasoning-hard-vlms.md, visual-thinking-techniques.md, …)
   but has no entity page.
   Fix: create wiki/entities/adaptvis.md.

2. "V*Bench" appears in 3 page snippets but has no entity page.
   Fix: create wiki/entities/v-star-bench.md.

3. "Chameleon-7B" is referenced as a base model in 4 sources
   but has no entity page.
   Fix: create wiki/entities/chameleon-7b.md.
```

Tell Claude to fix them:

```
Fix all missing entity pages.
```

Claude creates each stub with a `## Overview` section pre-populated from the snippets it already found, cross-links them into the pages that mention them, adds entries to `wiki/index.md`, re-indexes, and logs the pass.

You can also target this check explicitly if you suspect a specific entity is undercovered:

```
Does the wiki have a proper entity page for AdaptVis,
or is it only mentioned in passing on other pages?
```

---

## 10. Spot contradictions across papers

```
Do any papers in the wiki disagree about whether latent visual tokens are actually used at inference?
```

Claude searches for contradiction markers, cross-references log timestamps to determine which source is newer, and surfaces the conflict with context — then offers to update the older page with an inline note.

---

## 11. Adapt the wiki for a new domain

This repo ships focused on LLM/VLM research, but the pattern works for any domain — medical literature, legal documents, competitive intelligence, engineering specs.

1. Edit `CLAUDE.md`: change the domain description, update entity categories, and adjust any domain-specific conventions.
2. Clear or archive `wiki/` and start fresh (`wiki/index.md` and `wiki/log.md` only).
3. Create entity and concept stubs for your domain's vocabulary.
4. Start ingesting sources.

The skills (`wiki-ingest`, `wiki-query`, `wiki-lint`) and `qmd` are domain-agnostic — they work on whatever markdown is in `wiki/`.

---

## Quick reference: what to say

| Goal | What to type |
|---|---|
| Ingest a file | `process raw/<filename>` |
| Ask a question | Any question — Claude routes it through `wiki-query` |
| Health-check | `/wiki-lint` |
| Find missed entity pages | `/wiki-lint` — look for "Missing entity pages" section |
| Find a gap | Just ask — Claude tells you if coverage is low and offers to search |
| Save a query result | Say "yes" when Claude offers to file the analysis |
| Re-index after manual edits | `qmd update --collection wiki` |
