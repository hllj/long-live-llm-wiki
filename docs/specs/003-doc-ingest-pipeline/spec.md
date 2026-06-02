# Feature 003: Document Ingest Pipeline

**Status:** Approved
**Version:** 1.1.0
**Created:** 2026-06-03
**Updated:** 2026-06-03
**Branch:** `003-doc-ingest-pipeline`

---

## Problem Statement

When ingesting research papers, PDFs, and technical documents into the wiki, images and figures are critical information carriers — charts, architecture diagrams, tables rendered as images, and mathematical figures often contain content that plain text extraction misses entirely. Existing manual ingest drops this information, leaving gaps in the knowledge graph.

There is no automated pipeline to: (1) convert a raw document to structured markdown while preserving image references, and (2) enrich those image references with LLM-generated descriptions so the wiki captures the full information content of the source.

---

## Goals

1. A single CLI script converts a supported document (PDF, DOCX) to a markdown file using MinerU Pro 2.5, preserving image/figure references.
2. The script identifies all image references in the MinerU markdown output and, for each, calls Gemini's vision API to generate a descriptive caption/analysis.
3. The enriched markdown replaces or augments each image reference with an inline description block so the content is readable and searchable without opening the original images.
4. The enriched markdown is saved into `raw/` with a canonical slug filename, ready for `wiki-ingest` to process.
5. The script is idempotent: re-running on the same document with the same output slug does not duplicate image descriptions.

---

## Non-Goals

- Running `wiki-ingest` automatically — the user still triggers ingest manually after reviewing the enriched markdown.
- Batch-processing multiple documents in one invocation (single-file scope for v1).
- Handling image types that Gemini vision cannot process (non-image binary attachments, audio, video).
- Modifying raw source files in place — source documents remain immutable.
- OCR of scanned-only PDFs beyond what MinerU Pro 2.5 provides.
- Supporting providers other than Gemini for image understanding (extensibility is out of scope for v1).

---

## Users and Context

**Primary user:** The wiki owner (engineer/researcher) who drops source documents into `raw/` and wants fully enriched markdown ready for wiki ingest.
**Usage context:** Run from the repo root on a document path. Expected to run before `wiki-ingest`, not during or after. Typical documents: ML papers, technical reports, slide-deck exports.
**User mental model:** "Give me a markdown file where figures are explained in plain text so I don't lose anything when the wiki processes it."

---

## User Stories

### Story 1: Convert a PDF and enrich figures

**As a** wiki owner,
**I want to** run a single command pointing at a PDF,
**So that** I get an enriched markdown file in `raw/` with all figures described.

**Acceptance Criteria:**
- AC-1.1: Running `python scripts/ingest_doc.py <path-to-pdf>` completes without error on a valid PDF.
- AC-1.2: An output markdown file appears at `raw/<slug>.md` where `<slug>` is derived from the source filename.
- AC-1.3: The output markdown contains all text content from the source document.
- AC-1.4: Every image reference in the MinerU output has a corresponding `> **Figure description (Gemini):** ...` block appended immediately after it in the output markdown.
- AC-1.5: The script prints a summary line: total images found, total images described, any failures.

### Story 2: Idempotent re-run

**As a** wiki owner,
**I want to** re-run the script on the same document without duplicating figure descriptions,
**So that** I can safely re-run after partial failures.

**Acceptance Criteria:**
- AC-2.1: If `raw/<slug>.md` already exists and already contains `Figure description (Gemini)` blocks, the script does not duplicate them.
- AC-2.2: The script prints a warning if the output file already exists and offers `--force` to overwrite.

### Story 3: Graceful handling of image failures

**As a** wiki owner,
**I want** image description failures to be non-fatal,
**So that** a single unreadable figure does not abort the entire pipeline.

**Acceptance Criteria:**
- AC-3.1: If Gemini returns an error for a specific image, the script inserts `> **Figure description:** [Gemini error — could not process image]` and continues.
- AC-3.2: The final summary line counts and lists any failed images by their reference ID.

### Story 4: Custom output slug

**As a** wiki owner,
**I want to** specify a custom output slug,
**So that** I control the filename in `raw/` without renaming the source file.

**Acceptance Criteria:**
- AC-4.1: `--slug <custom-slug>` produces output at `raw/<custom-slug>.md`.
- AC-4.2: If `--slug` is omitted, the slug defaults to the source filename stem, lowercased and hyphenated.

---

## Functional Requirements

### FR-1: MinerU Pro 2.5 conversion (`tools/doc_to_markdown.py`)

- FR-1.1: `tools/doc_to_markdown.py` invokes the `mineru` CLI via subprocess (`mineru -p <pdf> -o <tmpdir>`) to convert the input document to markdown with image files extracted alongside.
- FR-1.2: The script supports at minimum PDF input; DOCX support is desired but not required for v1.
- FR-1.3: Image files are written by MinerU to an `images/` subfolder inside the MinerU output directory, referenced in the markdown as standard `![]()` with relative paths (e.g., `![](images/<hash>.jpg)`).
- FR-1.4: The tool discovers the actual MinerU output subdirectory after conversion (MinerU may nest output under a subdirectory named after the input file) and returns the resolved markdown path and image directory path.

### FR-2: Image detection

- FR-2.1: `tools/enhance_images.py` parses the MinerU markdown output using regex `r'!\[.*?\]\((images/[^)]+)\)'` to identify all image references.
- FR-2.2: Each matched path is resolved relative to the MinerU output directory to obtain the image file on disk.

### FR-3: Gemini image understanding (`tools/enhance_images.py`)

- FR-3.1: For each detected image, `tools/enhance_images.py` loads the image file from disk and sends it to Gemini via the `google-genai` SDK with a prompt requesting a detailed description of the figure, chart, or diagram and its likely purpose in a technical/research context.
- FR-3.2: The Gemini API key is read from the `GEMINI_API_KEY` environment variable; the script fails fast with a clear error if the variable is not set.
- FR-3.3: The model used is configurable via `--gemini-model` (default: `gemini-3.5-flash`).

### FR-4: Markdown enrichment

- FR-4.1: For each image reference in the markdown, the script appends a blockquote immediately after the image line:
  ```
  > **Figure description (Gemini):** <description text>
  ```
- FR-4.2: Original image reference lines are preserved unchanged.
- FR-4.3: The enriched markdown is written to `raw/<slug>.md`.

### FR-5: CLI interface

- FR-5.1: Two composable tools in `tools/`:
  - `python tools/doc_to_markdown.py <document_path> [--outdir <tmpdir>]` — runs MinerU and returns the markdown + image directory.
  - `python tools/enhance_images.py <markdown_path> <images_dir> [--output <path>] [--gemini-model <model>]` — enriches the markdown with Gemini descriptions and writes the output file.
- FR-5.2: A thin orchestrator script `tools/ingest_doc.py` calls both tools in sequence and handles the `--slug`, `--force`, and `--gemini-model` flags for end-to-end use: `python tools/ingest_doc.py <document_path> [--slug <slug>] [--force] [--gemini-model <model>]`.
- FR-5.3: `--force` in the orchestrator overwrites an existing `raw/<slug>.md`.
- FR-5.4: Missing required arguments print a usage message and exit non-zero.

---

## Non-Functional Requirements

- NFR-1: The script must complete a 20-page PDF with 10 figures within 3 minutes on a standard laptop (network latency is the dominant factor).
- NFR-2: Gemini API calls are made sequentially by default to avoid rate-limit errors; no parallelism in v1.
- NFR-3: All tools must run in Python 3.10+ with dependencies declared in `tools/requirements.txt`. Required packages: `mineru[all]`, `google-genai`.
- NFR-4: No hardcoded API keys or secrets anywhere in the codebase.
- NFR-5: First-run note must be surfaced — `mineru[all]` downloads model weights (~several GB) on first invocation; the README for `tools/` must document this.

---

## Error Scenarios

| Scenario | Expected behavior |
|---|---|
| Input file does not exist | Exit non-zero with message: `Error: file not found: <path>` |
| MinerU conversion fails | Exit non-zero with MinerU's error message forwarded |
| `GEMINI_API_KEY` not set | Exit non-zero with message: `Error: GEMINI_API_KEY environment variable not set` |
| Output file exists, no `--force` | Exit non-zero with message: `raw/<slug>.md already exists. Use --force to overwrite.` |
| Single image Gemini failure | Insert placeholder description, continue, report in summary |
| All Gemini calls fail | Complete markdown without descriptions, exit with warning (non-zero) |

---

## Open Questions

All open questions resolved. See [research.md](research.md) for full findings.

| OQ | Resolution |
|----|-----------|
| OQ-1 | MinerU CLI via subprocess (`mineru -p <pdf> -o <outdir>`); pip install `mineru[all]` |
| OQ-2 | Standard `![]()` markdown; images in `images/` subfolder; regex: `r'!\[.*?\]\((images/[^)]+)\)'` |
| OQ-3 | File-based only (default MinerU output); base64 mode not used |
| OQ-4 | `gemini-3.5-flash` via `google-genai` SDK (user decision: latest Flash) |
| OQ-5 | `tools/` directory; two tools (`doc_to_markdown.py`, `enhance_images.py`) + orchestrator (`ingest_doc.py`) |

---

## Out of Scope

- Modifying `wiki-ingest` to call this pipeline automatically.
- A UI or web interface for the pipeline.
- Support for image formats beyond what Gemini vision accepts.
- Storing extracted images permanently in the repo.
- Video or audio figure extraction.
