# Long Live LLM Wiki

An LLM-maintained personal knowledge base. Claude Code owns the `wiki/` layer entirely — creating, updating, and cross-referencing markdown pages as sources are ingested and questions are asked. You curate the sources and direct the analysis; Claude does all the bookkeeping.

> **Core idea:** Instead of rediscovering knowledge from raw documents on every query (RAG-style), the LLM incrementally builds and maintains a persistent wiki — a structured, interlinked collection of markdown files. When you add a new source, Claude reads it, extracts key information, and integrates it into the existing wiki: updating entity pages, revising concept summaries, flagging contradictions. The knowledge compounds.

Inspired by [LLM Wiki](./llm-wiki.md), the pattern document behind this repo.

See [EXAMPLES.md](./EXAMPLES.md) for real use cases and workflows you can follow from day one.

## Features

- **Initialize**: Declare your wiki's topic, back up any existing content, clean out example pages, scaffold entity/concept stubs, and prepare the repo for production — all in one guided flow.
- **Ingest**: Drop any source (PDF, DOCX, or markdown) into `raw/` and ask Claude to process it. Binary documents are automatically converted via MinerU and enriched with Gemini vision figure descriptions (Step 0) before wiki integration. Claude then writes a summary page, updates all related entity and concept pages, and re-indexes everything.
- **Query**: Ask questions; Claude searches the wiki with hybrid BM25/vector search, synthesizes an answer with citations, and can file valuable responses as new wiki pages. When the wiki has a gap (score < 0.3), Claude automatically runs a web search, lets you pick a source, saves it to `raw/`, triggers ingest, and re-queries — no extra commands needed.
- **Lint**: Periodically health-check the wiki for contradictions, orphan pages, stale claims, and missing cross-references.
- **Skills**: Four purpose-built Claude Code skills (`wiki-init`, `wiki-ingest`, `wiki-query`, `wiki-lint`) encode the exact workflows so Claude stays consistent across sessions.
- **Local search**: Powered by [qmd](https://github.com/tobi/qmd) — hybrid BM25 + vector search with LLM re-ranking, all on-device.

## Directory structure

```
.
├── raw/                    # Immutable source documents (PDFs, markdown, images)
│   ├── <slug>.pdf          # Original binary source (never modified)
│   ├── <slug>/             # Intermediate work folder created by Step 0
│   │   ├── step1_mineru_raw.md   # Raw MinerU output
│   │   ├── images/               # Figures extracted from the document
│   │   └── step2_enhanced.md     # Markdown after Gemini figure descriptions
│   └── <slug>.md           # Final enriched artifact promoted from step2_enhanced.md
├── wiki/                   # LLM-generated markdown pages (Claude owns this)
│   ├── index.md            # Content catalog — one entry per page
│   ├── log.md              # Append-only activity log
│   ├── sources/            # One summary page per ingested source
│   ├── entities/           # Pages for named things (models, people, orgs)
│   ├── concepts/           # Pages for ideas, techniques, frameworks
│   └── analyses/           # Query outputs and synthesized comparisons
├── skills/                 # Claude Code skill definitions
│   ├── wiki-init/
│   ├── wiki-ingest/
│   ├── wiki-query/
│   └── wiki-lint/
├── CLAUDE.md               # Operational schema — tells Claude how to run the wiki
└── llm-wiki.md             # The pattern document this repo instantiates
```

## Prerequisites

- [Claude Code](https://claude.ai/code) (CLI or desktop app)
- [qmd](https://github.com/tobi/qmd) — local search engine for the wiki

```bash
npm install -g @tobilu/qmd
```

**For binary document ingestion (PDF/DOCX):**

- Python 3.10+
- [MinerU](https://github.com/opendatalab/MinerU) Pro 2.5 — PDF/DOCX → markdown conversion
- [Google Gemini API key](https://aistudio.google.com/) — figure description enrichment

```bash
pip install -r skills/wiki-ingest/tools/requirements.txt
export GEMINI_API_KEY=<your-key>
```

Markdown-only ingestion works without these dependencies.

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/hllj/long-live-llm-wiki.git
   cd long-live-llm-wiki
   ```

2. **Open Claude Code in this directory**

   ```bash
   claude
   ```

   Claude will load `CLAUDE.md` automatically and be ready to operate the wiki.

3. **Run `wiki-init` to set up your topic**

   ```
   init the wiki
   ```

   This creates the project-local qmd index (`.qmd/`), registers the `wiki` collection, and rebuilds the search index automatically — no manual `qmd init` step needed.

## Usage

### Initialize for a new topic

When you clone this repo or want to pivot to a new subject area:

```
init the wiki
```

Claude will ask for your topic description, optional entity and concept names, back up any existing content to `.backup/`, clean out example pages, scaffold stubs for your domain, update `.gitignore`, and rebuild the search index. Takes under a minute.

### Ingest a source

Drop a file into `raw/`, then in Claude Code:

```
process raw/my-paper.pdf
```

For **PDF or DOCX** sources, Claude automatically runs Step 0 first: converts the document via MinerU, extracts all figures, and calls Gemini vision to generate a description for each one. Intermediate artifacts land in `raw/<slug>/` so you can inspect or debug any stage. After Step 0 completes, Claude asks for confirmation before writing any wiki pages.

For **markdown** sources, Step 0 is skipped. Claude reads the source directly, writes `wiki/sources/<slug>.md`, updates all relevant entity and concept pages, refreshes the index, and logs the activity.

### Ask a question

```
what does the wiki say about chain-of-thought reasoning in VLMs?
```

Claude runs a hybrid search, synthesizes an answer with links to wiki pages, and offers to file a valuable response as a new analysis page.

### Lint the wiki

```
/wiki-lint
```

Claude checks index health, hunts for contradictions, orphan pages, and missing cross-references, then reports a prioritized fix list.

## Skills

The four Claude Code skills are in `skills/`. They encode precise workflows so Claude is consistent across sessions:

| Skill | Trigger | What it does |
|---|---|---|
| `wiki-init` | "init the wiki", "start a new wiki", "prepare for production" | Guided setup: collect topic → backup → update `.gitignore` → clean example content → create stubs → reset index/log → rebuild index |
| `wiki-ingest` | "ingest this", "process raw/…" | Binary doc: Step 0 (MinerU convert → Gemini figure descriptions → confirm) → then: read → impact score → summarize → update pages → re-index → log |
| `wiki-query` | Any question about wiki content | Search → synthesize → cite → gap detected? → web-search → ingest → re-query |
| `wiki-lint` | "lint the wiki", "health-check" | Index health → find contradictions/orphans/gaps → report → fix if asked |

## Customizing for your domain

Run `wiki-init` to declare your topic and scaffold the wiki for your domain in one step. It will:

1. Ask for your topic description and up to 5 key entities and concepts.
2. Back up any existing content to `.backup/` before touching anything.
3. Clean out example pages and create stubs for your named entities and concepts.
4. Reset `wiki/index.md` and `wiki/log.md` with your topic heading.
5. Update `.gitignore` so raw files (PDFs, etc.) and backups stay out of git.

Then start ingesting sources with `wiki-ingest`.

## License

MIT
