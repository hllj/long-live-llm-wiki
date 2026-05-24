# Long Live LLM Wiki

An LLM-maintained personal knowledge base. Claude Code owns the `wiki/` layer entirely — creating, updating, and cross-referencing markdown pages as sources are ingested and questions are asked. You curate the sources and direct the analysis; Claude does all the bookkeeping.

> **Core idea:** Instead of rediscovering knowledge from raw documents on every query (RAG-style), the LLM incrementally builds and maintains a persistent wiki — a structured, interlinked collection of markdown files. When you add a new source, Claude reads it, extracts key information, and integrates it into the existing wiki: updating entity pages, revising concept summaries, flagging contradictions. The knowledge compounds.

Inspired by [LLM Wiki](./llm-wiki.md), the pattern document behind this repo.

See [EXAMPLES.md](./EXAMPLES.md) for real use cases and workflows you can follow from day one.

## Features

- **Ingest**: Drop any source (PDF, markdown, article) into `raw/` and ask Claude to process it. It writes a summary page, updates all related entity and concept pages, and re-indexes everything.
- **Query**: Ask questions; Claude searches the wiki with hybrid BM25/vector search, synthesizes an answer with citations, and can file valuable responses as new wiki pages. When the wiki has a gap (score < 0.3), Claude automatically runs a web search, lets you pick a source, saves it to `raw/`, triggers ingest, and re-queries — no extra commands needed.
- **Lint**: Periodically health-check the wiki for contradictions, orphan pages, stale claims, and missing cross-references.
- **Skills**: Three purpose-built Claude Code skills (`wiki-ingest`, `wiki-query`, `wiki-lint`) encode the exact workflows so Claude stays consistent across sessions.
- **Local search**: Powered by [qmd](https://github.com/tobi/qmd) — hybrid BM25 + vector search with LLM re-ranking, all on-device.

## Directory structure

```
.
├── raw/                    # Immutable source documents (PDFs, markdown, images)
│   └── .gitkeep
├── wiki/                   # LLM-generated markdown pages (Claude owns this)
│   ├── index.md            # Content catalog — one entry per page
│   ├── log.md              # Append-only activity log
│   ├── sources/            # One summary page per ingested source
│   ├── entities/           # Pages for named things (models, people, orgs)
│   ├── concepts/           # Pages for ideas, techniques, frameworks
│   └── analyses/           # Query outputs and synthesized comparisons
├── skills/                 # Claude Code skill definitions
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

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/hllj/long-live-llm-wiki.git
   cd long-live-llm-wiki
   ```

2. **Initialize the qmd index**

   ```bash
   qmd update --collection wiki
   qmd embed --collection wiki
   ```

3. **Open Claude Code in this directory**

   ```bash
   claude
   ```

   Claude will load `CLAUDE.md` automatically and be ready to operate the wiki.

## Usage

### Ingest a source

Drop a file into `raw/`, then in Claude Code:

```
process raw/my-paper.pdf
```

Claude reads the source, writes `wiki/sources/<slug>.md`, updates all relevant entity and concept pages, refreshes the index, and logs the activity.

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

The three Claude Code skills are in `skills/` and also mirrored in `.claude-plugin/`. They encode precise workflows so Claude is consistent across sessions:

| Skill | Trigger | What it does |
|---|---|---|
| `wiki-ingest` | "ingest this", "process raw/…" | Full ingest: read → impact score → summarize → update pages → re-index → log |
| `wiki-query` | Any question about wiki content | Search → synthesize → cite → gap detected? → web-search → ingest → re-query |
| `wiki-lint` | "lint the wiki", "health-check" | Index health → find contradictions/orphans/gaps → report → fix if asked |

## Customizing for your domain

This repo is currently focused on **LLM/VLM research**. To adapt it:

1. Edit `CLAUDE.md` to describe your domain's entities and conventions.
2. Create stub pages in `wiki/entities/` and `wiki/concepts/` for the things you'll track.
3. Start ingesting sources.

## License

MIT
