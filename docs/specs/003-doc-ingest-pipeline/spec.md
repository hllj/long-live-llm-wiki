# Feature 003: wiki-ingest Binary Document Support

**Status:** Approved
**Version:** 3.1.0
**Created:** 2026-06-03
**Updated:** 2026-06-03
**Branch:** `003-doc-ingest-pipeline`

---

## Problem Statement

`wiki-ingest` currently handles only markdown source files. When a user drops a PDF or DOCX research paper into `raw/`, they must manually convert it to markdown first — and images, charts, and figures embedded in binary documents are lost entirely during that conversion, leaving gaps in the knowledge graph.

The missing capability: `wiki-ingest` should accept binary documents directly and handle conversion and image enrichment transparently, then proceed with the normal wiki integration workflow (impact scoring, source summary, entity/concept updates) — all in a single invocation.

Two additional pain points this spec also addresses:
- **Opaque intermediate state:** users have no visibility into what MinerU extracted or where each pipeline step's output landed, making debugging and manual review hard.
- **Silent long-running steps:** MinerU conversion and sequential Gemini calls can take 1–3 minutes with no output, leaving the user unsure if the process is alive.

---

## Goals

1. `wiki-ingest` accepts binary source documents (PDF, DOCX) directly — no pre-processing step required from the user.
2. When a binary document is detected, `wiki-ingest` runs Step 0: converts the document to markdown via MinerU Pro 2.5, preserving image/figure references; then calls Gemini vision to generate a description for each figure.
3. Each pipeline stage writes its output into a dedicated intermediate folder (`raw/<slug>/`), so users can inspect any step's artifact independently. The final enriched markdown is promoted to `raw/<slug>.md`.
4. Every long-running sub-step streams a live progress line to the terminal so the user can see exactly what is happening (page count, current image being described, elapsed time) without waiting for the full script to finish.
5. After Step 0, `wiki-ingest` shows the conversion summary (images found, described, failures) and asks the user to confirm before writing any wiki pages.
6. Step 0 is idempotent: re-running `wiki-ingest` on the same binary document does not duplicate image descriptions in the output.
7. All conversion and enrichment logic lives in `skills/wiki-ingest/tools/` as internal implementation — users never invoke those scripts directly.

---

## Intermediate Folder Layout

For a binary source named `attention-is-all-you-need.pdf` (slug: `attention-is-all-you-need`), Step 0 produces the following layout before any wiki pages are written:

```
raw/
├── attention-is-all-you-need.pdf          ← original source (immutable)
├── attention-is-all-you-need/             ← intermediate work folder (created by Step 0)
│   ├── step1_mineru_raw.md                ← raw markdown from MinerU, unmodified
│   ├── images/                            ← image files extracted by MinerU
│   │   ├── fig1_transformer_arch.png
│   │   ├── fig2_attention_head.png
│   │   └── ...
│   └── step2_enhanced.md                  ← markdown after Gemini figure descriptions injected
└── attention-is-all-you-need.md           ← final enriched artifact (promoted from step2_enhanced.md)
```

**Rules:**
- The intermediate folder is named `raw/<slug>/` and lives alongside the source file.
- `step1_mineru_raw.md` is never modified after MinerU writes it — it is the auditable raw extraction.
- `step2_enhanced.md` is a copy of `step1_mineru_raw.md` with Gemini figure descriptions injected inline. It is also preserved for debugging.
- The final `raw/<slug>.md` is a copy/rename of `step2_enhanced.md` promoted to the top-level `raw/` folder. This is the path `wiki-ingest` hands off to Steps 1–8.
- If `--force` is not passed and `raw/<slug>/` already exists, Step 0 skips extraction and reports which intermediate files it found, then asks whether to re-run or reuse.

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
- AC-1.2: During MinerU conversion, Step 0 streams a live progress line to the terminal, updated every ~2 seconds:
  ```
  [Step 0 — MinerU] Converting... elapsed: 14s  (output: raw/attention-is-all-you-need/step1_mineru_raw.md)
  ```
  The final line reports page count and image count when conversion completes.
- AC-1.3: During Gemini enrichment, Step 0 streams a per-image progress line for each figure:
  ```
  [Step 0 — Gemini]  Describing figure 3/10: images/fig3_encoder.png ... done (1.2s)
  [Step 0 — Gemini]  Describing figure 4/10: images/fig4_decoder.png ... done (0.9s)
  ```
  Failed images are marked inline: `... FAILED (quota exceeded)`.
- AC-1.4: Step 0 creates the intermediate folder `raw/<slug>/` with `step1_mineru_raw.md`, `images/`, and `step2_enhanced.md` as described in the **Intermediate Folder Layout** section.
- AC-1.5: Step 0 promotes `step2_enhanced.md` to `raw/<slug>.md` and displays a summary:
  ```
  Step 0 complete — images found: 10 | described: 9 | failed: 1
  Intermediate artifacts saved to: raw/attention-is-all-you-need/
  Final enriched markdown:         raw/attention-is-all-you-need.md
  ```
- AC-1.6: After Step 0, `wiki-ingest` asks the user to confirm before writing any wiki pages; the user may abort at this point.
- AC-1.7: On confirmation, `wiki-ingest` proceeds with Steps 1–8 (impact scoring, source summary, entity/concept updates) using the enriched markdown as the source.
- AC-1.8: If Step 0 fails fatally, `wiki-ingest` exits without writing any wiki pages.
- AC-1.9: If the source file is already `.md`, `wiki-ingest` skips Step 0 and proceeds to Step 1 directly.

### Story 2: Idempotent re-run

**As a** wiki owner,
**I want to** re-run `wiki-ingest` on the same binary document without duplicating figure descriptions,
**So that** I can safely retry after a partial failure.

**Acceptance Criteria:**
- AC-2.1: If `raw/<slug>/` already exists, Step 0 inspects which intermediate files are present and reports them:
  ```
  [Step 0] Intermediate folder already exists: raw/attention-is-all-you-need/
    ✓ step1_mineru_raw.md  (found)
    ✓ images/              (10 files)
    ✓ step2_enhanced.md    (found — contains Gemini descriptions)
  Re-run Step 0 and overwrite? [y/N]
  ```
- AC-2.2: Without `--force`, Step 0 defaults to reusing the existing `step2_enhanced.md` (skips MinerU + Gemini) and promotes it to `raw/<slug>.md` directly — useful for resuming after a wiki-write failure.
- AC-2.3: With `--force`, Step 0 re-runs all sub-steps unconditionally, overwriting existing intermediate files.

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
- FR-6.3: Step 0 runs `python skills/wiki-ingest/tools/ingest_doc.py <path> [--slug <slug>] [--gemini-model <model>]` with `subprocess.Popen` (not `check_output`) so that stdout is streamed in real time to the terminal as lines arrive.
- FR-6.4: After displaying the summary, Step 0 asks the user: "Pre-processing complete. Proceed with wiki ingest? [y/n]". If the user declines, exit without writing any wiki pages.
- FR-6.5: On confirmation, the enriched markdown at `raw/<slug>.md` becomes the source path for Steps 1–8 of the normal wiki-ingest workflow.

### FR-1: MinerU Pro 2.5 conversion *(internal: `doc_to_markdown.py`)*

- FR-1.1: `doc_to_markdown.py` invokes the `mineru` CLI via `subprocess.Popen` (`mineru -p <pdf> -o <workdir>`) so that MinerU's stdout is forwarded line-by-line to the caller in real time. Lines are prefixed `[MinerU]` before printing.
- FR-1.2: `<workdir>` is set to `raw/<slug>/` (the intermediate folder). MinerU writes the markdown and `images/` subfolder directly there.
- FR-1.3: After MinerU exits, `doc_to_markdown.py` renames/copies the MinerU-produced markdown to `raw/<slug>/step1_mineru_raw.md` for a stable, named artifact.
- FR-1.4: Supports at minimum PDF input; DOCX support is desired but not required for v1.
- FR-1.5: Image files are written by MinerU to `raw/<slug>/images/`, referenced in the markdown as `![](images/<hash>.jpg)`.
- FR-1.6: The tool prints on success:
  ```
  markdown:raw/<slug>/step1_mineru_raw.md
  images:raw/<slug>/images
  ```

### FR-2: Image detection *(internal)*

- FR-2.1: `enhance_images.py` parses the MinerU markdown output using regex `r'!\[.*?\]\((images/[^)]+)\)'` to identify all image references.
- FR-2.2: Each matched path is resolved relative to the MinerU output directory to obtain the image file on disk.

### FR-3: Gemini image understanding *(internal: `enhance_images.py`)*

- FR-3.1: For each detected image, `enhance_images.py` prints a progress line **before** the API call:
  ```
  [Gemini] Describing figure 3/10: images/fig3_encoder.png ...
  ```
  and appends `done (1.2s)` or `FAILED (<reason>)` on the same line when the call returns.
- FR-3.2: Each image is sent to Gemini via the `google-genai` SDK with a prompt requesting a detailed description of the figure in a technical/research context.
- FR-3.3: The Gemini API key is read from the `GEMINI_API_KEY` environment variable; fails fast with a clear error if not set.
- FR-3.4: The model is configurable (default: `gemini-3.5-flash`); wiki-ingest passes `--gemini-model` if the user requests a different model during the conversation.

### FR-4: Markdown enrichment *(internal)*

- FR-4.1: For each image reference, `enhance_images.py` appends a blockquote immediately after the image line:
  ```
  > **Figure description (Gemini):** <description text>
  ```
- FR-4.2: Original image reference lines are preserved unchanged.
- FR-4.3: The enriched markdown is written to `raw/<slug>/step2_enhanced.md`.
- FR-4.4: After writing `step2_enhanced.md`, `ingest_doc.py` copies it to `raw/<slug>.md` (the final promoted artifact). This copy is what wiki-ingest hands to Steps 1–8.

### FR-7: Obsidian wikilink compatibility *(naming convention)*

- FR-7.1: Entity and concept page filenames **must** match the wikilink text exactly. If a page is linked as `[[Multi-Head Attention]]`, the file must be `wiki/concepts/Multi-Head Attention.md`. Obsidian resolves `[[X]]` by looking for a file named `X.md`; hyphens and spaces are not interchangeable.
- FR-7.2: Entity and concept files use **Title Case with spaces** (e.g. `Transformer.md`, `Multi-Head Attention.md`, `Self-Attention.md`). Never use kebab-case for these files.
- FR-7.3: Source summary files continue to use **kebab-case** (e.g. `attention-is-all-you-need.md`) and are referenced via standard path links (`[Title](../sources/slug.md)`), not wikilinks.
- FR-7.4: When writing cross-links inside wiki pages, always use bare `[[Page Name]]` wikilinks for entity/concept pages (never piped aliases to work around a filename mismatch — fix the filename instead).

### FR-5: Internal tool contracts

- FR-5.1: `doc_to_markdown.py` prints (after all MinerU lines) on success:
  ```
  markdown:raw/<slug>/step1_mineru_raw.md
  images:raw/<slug>/images
  ```
- FR-5.2: `enhance_images.py` prints per-image progress lines (FR-3.1) and on completion:
  ```
  Images found: N | Described: M | Failed: K
  step2 written: raw/<slug>/step2_enhanced.md
  ```
- FR-5.3: Exit codes: `0` = full success, `1` = fatal error (abort), `2` = partial success (some image failures, output still written).
- FR-5.4: `ingest_doc.py` orchestrates FR-1 → FR-4 in sequence, handles `--slug`, `--force`, and `--gemini-model`, and promotes `raw/<slug>/step2_enhanced.md` → `raw/<slug>.md`.
- FR-5.5: `ingest_doc.py` writes a machine-readable log file `raw/<slug>/ingest.log` recording timestamps, page count, image count, per-image result (ok/failed), total elapsed time, and exit code. This file persists across runs and is appended to (not overwritten) unless `--force` is passed.

---

## Non-Functional Requirements

- NFR-1: The script must complete a 20-page PDF with 10 figures within 3 minutes on a standard laptop (network latency is the dominant factor).
- NFR-2: Gemini API calls are made sequentially by default to avoid rate-limit errors; no parallelism in v1.
- NFR-3: All tools must run in Python 3.10+ with dependencies declared in `skills/wiki-ingest/tools/requirements.txt`. Required packages: `mineru[all]`, `google-genai`.
- NFR-4: No hardcoded API keys or secrets anywhere in the codebase.
- NFR-5: First-run note must be surfaced — `mineru[all]` downloads model weights (~several GB) on first invocation; `skills/wiki-ingest/tools/README.md` must document the setup steps for developers (not end users).
- NFR-6: `skills/wiki-ingest/SKILL.md` frontmatter must use the `description` + `when_to_use` split pattern: `description` holds what the skill does (≤200 chars), `when_to_use` holds trigger phrases. Combined length must stay under the 1,536-character skill listing cap to prevent the description from being dropped from Claude's context budget.
- NFR-7 (live logging): No sub-step may be silent for more than 5 seconds. If MinerU does not produce a stdout line within 5 seconds, `doc_to_markdown.py` must emit a heartbeat line: `[MinerU] still running... elapsed: Xs`. This ensures the user is never staring at a frozen terminal.
- NFR-8 (intermediate artifacts): The `raw/<slug>/` folder and all intermediate files (`step1_mineru_raw.md`, `images/`, `step2_enhanced.md`, `ingest.log`) must be preserved after Step 0 completes, even on a failed wiki-ingest run. They must not be cleaned up automatically; the user may delete them manually.

---

## Error Scenarios

| Scenario | Expected behavior |
|---|---|
| Input file does not exist | Exit non-zero: `Error: file not found: <path>` |
| MinerU conversion fails | Exit non-zero; MinerU's stderr forwarded prefixed `[MinerU error]`; intermediate folder left intact for inspection |
| `GEMINI_API_KEY` not set | Exit non-zero: `Error: GEMINI_API_KEY environment variable not set` |
| `raw/<slug>/` already exists (no `--force`) | Report which intermediate files exist, default to reusing `step2_enhanced.md` if present (skip MinerU + Gemini), ask user to confirm |
| `raw/<slug>/step1_mineru_raw.md` exists but `step2_enhanced.md` missing | Report partial state; offer to resume from Gemini enrichment only (skip MinerU re-run) |
| `raw/<slug>.md` already exists | Step 0 reports existing final file and asks user to confirm overwrite |
| Single image Gemini failure | Print `FAILED (<reason>)` inline for that image; insert placeholder description; continue to next image; report in summary |
| All Gemini calls fail | Write `step2_enhanced.md` with all placeholder descriptions; exit with warning (code 2); `ingest.log` records all failures |
| MinerU silent >5s | Emit heartbeat `[MinerU] still running... elapsed: Xs` every 5s until output resumes or timeout |

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
