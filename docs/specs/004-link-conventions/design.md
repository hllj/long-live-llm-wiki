# Design: Wiki Inter-page Link Conventions

**Feature:** 004-link-conventions
**Status:** Draft
**Date:** 2026-06-03

---

## Problem

Link conventions are currently fragmented:

- The naming rule (`Title Case with spaces` for entity/concept filenames) lives only in `wiki-ingest/SKILL.md`
- The `%20` encoding rule was just added to `wiki-ingest/SKILL.md` but no other skill knows about it
- `wiki-query` has no link convention guidance when filing analyses pages
- `wiki-lint` does not check for link hygiene violations
- Two orphan duplicate files exist from before the naming rule was established (`BLEU.md`, `Multi-Head.md`)

The root cause: no single authoritative source of truth for link conventions shared across all skills.

---

## Decision

`%20` encoding applies **only to `wiki/index.md` entries** — not to all standard markdown links project-wide.

**Rationale:** Source slugs are kebab-case (no spaces), so standard markdown links to sources never need encoding. Entity/concept cross-references inside content pages always use `[[Wikilinks]]`, which need no encoding. `index.md` is the only place where standard markdown links point to filenames that contain spaces.

---

## Two-zone model

| Zone | Files | Link style |
|---|---|---|
| **Content** | `entities/*.md`, `concepts/*.md`, `sources/*.md`, `analyses/*.md` | `[[Wikilinks]]` for all internal cross-refs; standard markdown only for source-to-source (slugs, no spaces, no encoding needed) |
| **Navigation** | `index.md`, `log.md` | Standard markdown `[text](path.md)` only; spaces in paths must be `%20`-encoded |

Rules:
- `[[Wikilinks]]` must **never** appear in `index.md` — they are navigation-zone, not content-zone
- Standard markdown links in `index.md` pointing to files with spaces in their names must use `%20`
- Inside content pages, prefer `[[Wikilinks]]` over `[text](path.md)` for all same-wiki refs

---

## Changes per file

### 1. `CLAUDE.md` — add `## Link conventions` section

Single authoritative definition of the two-zone model and both rules. All skills point here instead of duplicating rules inline. Keeps CLAUDE.md concise (the rules fit in ~15 lines).

### 2. `skills/wiki-ingest/SKILL.md`

- Collapse the current "Naming rule" + "Link encoding rule" callout in step 5 into a single one-line pointer: "Follow the **Link conventions** in `CLAUDE.md`."
- Remove the duplicated prose from the skill body — the authoritative text is in CLAUDE.md.

### 3. `skills/wiki-lint/SKILL.md`

Add two new checks to the **Scan for each issue type** section:

**Link hygiene** (new check):
- Scan `wiki/index.md` for `[[Wikilinks]]` — flag any found (wikilinks must not appear in index.md)
- Scan `wiki/index.md` for standard markdown links containing unencoded spaces in paths (i.e., `](path with space` without `%20`) — flag and offer to fix

**Orphan duplicates** (existing orphan check, now more explicit):
- Flag files where a shorter/variant name exists alongside the canonical Title-Case name (e.g., `BLEU.md` alongside `BLEU Score.md`)

### 4. `skills/wiki-query/SKILL.md`

Add a one-line "Link conventions" callout before step 7 (file the answer):

> When filing an analyses page, follow the **Link conventions** in `CLAUDE.md`: use `[[Wikilinks]]` for all cross-refs inside the page body; add the new page to `index.md` using a standard markdown link with `%20` for any spaces in the path.

### 5. `skills/wiki-init/CLAUDE.md.example`

Add the `## Link conventions` section to the template so any new wiki initialized from scratch inherits the conventions. The `wiki-init` SKILL.md itself needs no change — it already substitutes the collection name and writes the template verbatim.

---

## One-time cleanup

Delete the orphan duplicate files created before the naming rule was established:

- `wiki/concepts/BLEU.md` → canonical is `wiki/concepts/BLEU Score.md`
- `wiki/concepts/Multi-Head.md` → canonical is `wiki/concepts/Multi-Head Attention.md`

Verify no inbound links point to the orphans before deleting (they shouldn't — they predate the naming rule and were never linked).

---

## What this does NOT change

- The `[[Wikilink]]` convention inside content pages — this is already working well
- The kebab-case naming for source slugs — no spaces, so no encoding issue
- The qmd workflow, scoring thresholds, or any other skill behavior

---

## Out of scope

- Migrating existing `[[Wikilinks]]` inside content pages to standard markdown links — no benefit, would break Obsidian graph view
- Enforcing `%20` outside `index.md` — unnecessary since all other standard markdown links in the wiki point to kebab-case slugs
