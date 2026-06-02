# Feature 003: wiki-ingest Binary Document Support

**Status:** Approved
**Version:** 3.0.0
**Created:** 2026-06-03
**Updated:** 2026-06-03
**Branch:** `003-doc-ingest-pipeline`

---

## Problem Statement

`wiki-ingest` currently handles only markdown source files. When a user drops a PDF or DOCX research paper into `raw/`, they must manually convert it to markdown first — and images, charts, and figures embedded in binary documents are lost entirely during that conversion, leaving gaps in the knowledge graph.

The missing capability: `wiki-ingest` should accept binary documents directly and handle conversion and image enrichment transparently, then proceed with the normal wiki integration workflow (impact scoring, source summary, entity/concept updates) — all in a single invocation.

---

## Goals

1. `wiki-ingest` accepts binary source documents (PDF, DOCX) directly — no pre-processing step required from the user.
2. When a binary document is detected, `wiki-ingest` runs Step 0: converts the document to markdown via MinerU Pro 2.5, preserving image/figure references; then calls Gemini vision to generate a description for each figure.
3. The enriched markdown is saved to `raw/<slug>.md` as an auditable intermediate artifact, then feeds directly into `wiki-ingest`'s normal workflow (impact scoring, source summary page, entity/concept updates).
4. After Step 0, `wiki-ingest` shows the conversion summary (images found, described, failures) and asks the user to confirm before writing any wiki pages.
5. Step 0 is idempotent: re-running `wiki-ingest` on the same binary document does not duplicate image descriptions in the output.
6. All conversion and enrichment logic lives in `skills/wiki-ingest/tools/` as internal implementation — users never invoke those scripts directly.

---

## Non-Goals

- Exposing `ingest_doc.py`, `doc_to_markdown.py`, or `enhance_images.py` as user-facing CLIs.
- Batch-processing multiple documents in one invocation (single-file scope for v1).
- Handling image types that Gemini vision cannot process (non-image binary attachments, audio, video).
- Modifying raw source files in place — source documents remain immutable.
- OCR of scanned-only PDFs beyond what MinerU Pro 2.5 provides.
- Supporting providers other than Gemini for image understanding (v1).

---

## Users and Context

**Primary user:** The wiki owner (engineer/researcher) who drops a PDF or DOCX into `raw/` and runs `wiki-ingest` — no separate conversion step needed.
**Usage context:** Invoke `wiki-ingest` with the binary document path. Step 0 fires automatically, shows conversion results, and asks for confirmation before writing wiki pages.
**User mental model:** "I drop a PDF, I run wiki-ingest, I get fully enriched wiki pages. The conversion and figure understanding happen for me."

---

## User Stories

### Story 1: Ingest a binary document through wiki-ingest

**As a** wiki owner,
**I want to** run `wiki-ingest` on a PDF or DOCX directly,
**So that** conversion, figure enrichment, and wiki integration all happen in one step.

**Acceptance Criteria:**
- AC-1.1: When `wiki-ingest` receives a `.pdf` or `.docx` source path, it announces "Step 0: Pre-processing document..." before any wiki writes.
- AC-1.2: Step 0 produces `raw/<slug>.md` containing all text from the source document and a `> **Figure description (Gemini):** ...` block after every image reference.
- AC-1.3: Step 0 displays a summary line: images found, images described, failures.
- AC-1.4: After Step 0, `wiki-ingest` asks the user to confirm before writing any wiki pages; the user may abort at this point.
- AC-1.5: On confirmation, `wiki-ingest` proceeds with Steps 1–8 (impact scoring, source summary, entity/concept updates) using the enriched markdown as the source.
- AC-1.6: If Step 0 fails fatally, `wiki-ingest` exits without writing any wiki pages.
- AC-1.7: If the source file is already `.md`, `wiki-ingest` skips Step 0 and proceeds to Step 1 directly.

### Story 2: Idempotent re-run

**As a** wiki owner,
**I want to** re-run `wiki-ingest` on the same binary document without duplicating figure descriptions,
**So that** I can safely retry after a partial failure.

**Acceptance Criteria:**
- AC-2.1: If `raw/<slug>.md` already exists and contains `Figure description (Gemini)` blocks, Step 0 does not duplicate them.
- AC-2.2: If `raw/<slug>.md` already exists, Step 0 reports this and requires user confirmation (or `--force`) before overwriting.

### Story 3: Graceful handling of image failures

**As a** wiki owner,
**I want** individual figure description failures to be non-fatal,
**So that** one unreadable image does not abort the entire wiki ingest.

**Acceptance Criteria:**
- AC-3.1: If Gemini returns an error for a specific image, Step 0 inserts `> **Figure description:** [Gemini error — could not process image]` and continues to the next image.
- AC-3.2: The Step 0 summary counts and lists any failed images; wiki-ingest still proceeds to the confirmation prompt.

---

## Functional Requirements

### FR-6: wiki-ingest Step 0 integration *(primary)*

- FR-6.1: `skills/wiki-ingest/SKILL.md` is updated with a **Step 0: Pre-process document** block inserted before the existing Step 1.
- FR-6.2: Step 0 checks the source file extension. If `.pdf` or `.docx`, it runs the pre-process pipeline. If `.md` (or absent), it skips to Step 1.
- FR-6.3: Step 0 runs `python skills/wiki-ingest/tools/ingest_doc.py <path> [--slug <slug>] [--gemini-model <model>]` and displays the full stdout (conversion summary).
- FR-6.4: After displaying the summary, Step 0 asks the user: "Pre-processing complete. Proceed with wiki ingest? [y/n]". If the user declines, exit without writing any wiki pages.
- FR-6.5: On confirmation, the enriched markdown at `raw/<slug>.md` becomes the source path for Steps 1–8 of the normal wiki-ingest workflow.

### FR-1: MinerU Pro 2.5 conversion *(internal: `doc_to_markdown.py`)*

- FR-1.1: `doc_to_markdown.py` invokes the `mineru` CLI via subprocess (`mineru -p <pdf> -o <tmpdir>`) to convert the input document to markdown with image files extracted alongside.
- FR-1.2: Supports at minimum PDF input; DOCX support is desired but not required for v1.
- FR-1.3: Image files are written by MinerU to an `images/` subfolder, referenced as standard `![]()` with relative paths (e.g., `![](images/<hash>.jpg)`).
- FR-1.4: The tool discovers the actual MinerU output subdirectory after conversion and returns the resolved markdown path and image directory path.

### FR-2: Image detection *(internal)*

- FR-2.1: `enhance_images.py` parses the MinerU markdown output using regex `r'!\[.*?\]\((images/[^)]+)\)'` to identify all image references.
- FR-2.2: Each matched path is resolved relative to the MinerU output directory to obtain the image file on disk.

### FR-3: Gemini image understanding *(internal: `enhance_images.py`)*

- FR-3.1: For each detected image, `enhance_images.py` loads the image file and sends it to Gemini via the `google-genai` SDK with a prompt requesting a detailed description of the figure in a technical/research context.
- FR-3.2: The Gemini API key is read from the `GEMINI_API_KEY` environment variable; fails fast with a clear error if not set.
- FR-3.3: The model is configurable (default: `gemini-3.5-flash`); wiki-ingest passes `--gemini-model` if the user requests a different model during the conversation.

### FR-4: Markdown enrichment *(internal)*

- FR-4.1: For each image reference, `enhance_images.py` appends a blockquote immediately after the image line:
  ```
  > **Figure description (Gemini):** <description text>
  ```
- FR-4.2: Original image reference lines are preserved unchanged.
- FR-4.3: The enriched markdown is written to `raw/<slug>.md`.

### FR-5: Internal tool contracts

- FR-5.1: `doc_to_markdown.py` prints on success:
  ```
  markdown:/abs/path/to/<stem>.md
  images:/abs/path/to/images
  ```
- FR-5.2: `enhance_images.py` prints on completion:
  ```
  Images found: N | Described: M | Failed: K
  ```
- FR-5.3: Exit codes: `0` = full success, `1` = fatal error (abort), `2` = partial success (some image failures, output still written).
- FR-5.4: `ingest_doc.py` orchestrates FR-1 → FR-4 in sequence, handles `--slug`, `--force`, and `--gemini-model`, and writes to `raw/<slug>.md`.

---

## Non-Functional Requirements

- NFR-1: The script must complete a 20-page PDF with 10 figures within 3 minutes on a standard laptop (network latency is the dominant factor).
- NFR-2: Gemini API calls are made sequentially by default to avoid rate-limit errors; no parallelism in v1.
- NFR-3: All tools must run in Python 3.10+ with dependencies declared in `skills/wiki-ingest/tools/requirements.txt`. Required packages: `mineru[all]`, `google-genai`.
- NFR-4: No hardcoded API keys or secrets anywhere in the codebase.
- NFR-5: First-run note must be surfaced — `mineru[all]` downloads model weights (~several GB) on first invocation; `skills/wiki-ingest/tools/README.md` must document the setup steps for developers (not end users).

---

## Error Scenarios

| Scenario | Expected behavior |
|---|---|
| Input file does not exist | Exit non-zero with message: `Error: file not found: <path>` |
| MinerU conversion fails | Exit non-zero with MinerU's error message forwarded |
| `GEMINI_API_KEY` not set | Exit non-zero with message: `Error: GEMINI_API_KEY environment variable not set` |
| Output file exists | Step 0 reports existing file and asks user to confirm overwrite before proceeding |
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
| OQ-5 | `skills/wiki-ingest/tools/` directory; two tools (`doc_to_markdown.py`, `enhance_images.py`) + orchestrator (`ingest_doc.py`); SKILL.md updated with Step 0 |

---

## Out of Scope

- A UI or web interface for the pipeline.
- Support for image formats beyond what Gemini vision accepts.
- Storing extracted images permanently in the repo.
- Video or audio figure extraction.
