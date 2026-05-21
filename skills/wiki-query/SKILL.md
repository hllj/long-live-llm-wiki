---
name: wiki-query
description: >
  Answers questions by searching and synthesizing the LLM wiki. Use this skill
  whenever the user asks a question that the wiki might contain relevant
  information for — "what does the wiki say about X", "find everything on Y",
  "compare A and B", "summarize what we know about Z", "what have I read about
  this", or any open-ended question in the context of the knowledge base. Also
  trigger when the user is exploring a topic and wants synthesized insight rather
  than raw search results. After answering, always offer to file a valuable
  response as a new wiki page so the insight compounds.
---

# Wiki Query

You are answering a question using the wiki as your knowledge base. The wiki is a compiled, cross-referenced synthesis of everything the human has read — your job is to surface and connect the right parts.

## Workflow

### 1. Read wiki/index.md

Always start here. The index gives you the full structural map of the wiki in one pass — every page, its category, and a one-line summary. This takes seconds and does two things qmd can't:

- Shows you the **shape** of the wiki: what categories exist, how many pages per area, what's sparse vs. dense.
- Surfaces pages that might be relevant but **wouldn't score high** in semantic search because the question uses different vocabulary than the page. (e.g. a question about "depth perception" might not score high against a page titled "Continuous Visual Tokens" even though that page covers depth encoding.)

Scan every section (Sources, Entities, Concepts, Analyses) and note which pages look relevant. Be generous — it's fast.

### 2. Search with qmd

Run a hybrid search to get scored, ranked results. For simple questions, one query is enough. For complex questions, decompose into 2–3 sub-questions and run each separately, then merge.

```bash
qmd query "<question>" --collection wiki --json --limit 8
```

For sub-query decomposition:
```bash
# Example: "How does CoVT compare to tool-use approaches?"
qmd query "CoVT mechanism continuous visual tokens" --collection wiki --json --limit 5
qmd query "tool-use VLM visual reasoning" --collection wiki --json --limit 5
qmd query "visual reasoning benchmark comparison" --collection wiki --json --limit 5
```

Deduplicate results by file path across sub-queries; keep the highest score seen for each page.

**Score interpretation:**
- **≥ 0.6** — definitely read in full
- **0.3–0.59** — skim the returned snippet; read full page if the snippet connects
- **< 0.3** — wiki likely has a gap (see step 4)

### 3. Merge and prioritize

Combine the two candidate sets:
- **qmd ≥ 0.6** — read first, in score order
- **Index-flagged but not in qmd results** — read next; these are structural neighbors the search missed
- **qmd 0.3–0.59** — skim snippets; promote to full read only if the snippet is relevant

This ensures qmd's relevance ranking drives what you read first, while the index acts as a safety net for vocabulary gaps.

As you read, note:
- Direct answers to the question
- Contradictions between pages (surface these — they're valuable)
- Connections the human may not have noticed
- Gaps where the wiki doesn't have information

### 4. Synthesize and answer

Write a clear, structured answer that:
- Draws on specific wiki pages (cite them with links, e.g. `[Entity Name](entities/entity-name.md)`)
- Flags any contradictions between sources
- Notes what the wiki doesn't cover, if relevant to the question
- Is as long as the question warrants — a simple lookup gets a short answer; a complex synthesis gets a full treatment

Prefer wiki page links over raw source links. The wiki pages are the compiled knowledge; raw sources are the evidence behind them.

### 5. Handle low-confidence results

If the best qmd score is < 0.3 **and** the index scan also turned up nothing relevant, do not guess or extrapolate:

> "The wiki doesn't have strong coverage of this topic (best match score: 0.XX). This looks like a gap — want me to web-search and ingest a new source, or do you have a document to add to `raw/`?"

This is valuable signal: it means the question has revealed a hole in the knowledge base. (If the index scan found something the search missed, that's a cross-referencing gap to note — not a content gap.)

If the topic is related to a registered NotebookLM notebook (check `wiki/nlm-notebooks.md`), also include:
> "wiki gap detected — consider running wiki-nlm-research: '<question>' --topic <relevant-topic>"

Replace `<relevant-topic>` with the matching Topic Folder from the registry, or leave as a placeholder if the registry is empty or no topic matches.

### 7. Offer to file the answer

If the answer is non-trivial — a comparison, an analysis, a synthesis across multiple pages, a connection the human hadn't made explicit — offer to save it as a new wiki page:

> "This analysis touches on 4 different concept pages. Want me to file it as `wiki/analyses/<topic>.md` so it's part of the wiki going forward?"

If the human says yes:
- Write the page to `wiki/analyses/<slug>.md`
- Add it to `wiki/index.md` under `## Analyses`
- Run `qmd update --collection wiki` so the new page is immediately searchable
- Append to `wiki/log.md`:
  ```
  ## [YYYY-MM-DD] query | <Question or page title>
  Answered question about [topic]. Filed result as wiki/analyses/<slug>.md.
  ```

If the answer isn't worth filing (a quick lookup, a yes/no), skip the offer and just answer.

## Output formats

Match the format to the question:
- **Comparison**: markdown table with rows for each option/entity, columns for key dimensions
- **Synthesis**: flowing prose with headers, citing pages inline
- **Lookup**: direct answer in 1–3 sentences
- **Gap analysis**: what the wiki has, what it's missing, what sources to look for next
- **Visual summary**: if the human has Marp/Obsidian, offer a slide deck for complex topics

## What good querying looks like

You're not just retrieving — you're thinking. If two pages contradict each other, say so. If the answer requires connecting three pages the human never linked together, make that connection explicit. If the wiki doesn't have the answer, say so clearly and suggest what source would fill the gap.

The human's job is to ask good questions. Your job is to make the wiki answer them.

A note on snippets: qmd returns chunks (~900 tokens), not full pages. A chunk that scores high doesn't mean the full page is entirely relevant — always read the full page for scores ≥ 0.6 before synthesizing.
