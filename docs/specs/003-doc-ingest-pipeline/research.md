# Research: Document Ingest Pipeline (Feature 003)

**Date:** 2026-06-03
**Spec:** [spec.md](spec.md)

---

## Summary of Findings

- MinerU is pip-installable as `mineru` (v3.2.2); core conversion uses `UNIPipe` from `magic_pdf.pipe.UNIPipe`. CLI is also available but Python SDK is preferred for scripting.
- MinerU outputs standard `![]()` markdown image syntax with image files written as separate files in an `images/` subfolder (hash-based filenames). No base64 embedding by default.
- The latest Gemini Flash vision model is **`gemini-3.5-flash`** via the `google-genai` SDK (`google-generativeai` is deprecated as of Dec 2025).
- The script must orchestrate a temp output directory from MinerU, then walk `images/` to find files matching markdown references.
- Splitting into two tools (`tools/doc_to_markdown.py` and `tools/enhance_images.py`) is clean and testable: each tool has a single responsibility.

---

## Per Question

### OQ-1: MinerU Pro 2.5 integration method

**Context:** Need to know whether to use a CLI subprocess, a Python SDK, or a REST API to drive MinerU from our script.

**Findings:**
- **Option A — Python SDK (`magic_pdf.pipe.UNIPipe`):** Full programmatic control. Flow: instantiate `UNIPipe`, call `pipe_classify()` → `pipe_parse()` → `pipe_mk_markdown()`. Returns markdown string + writes image files to output dir.
- **Option B — CLI (`mineru` binary):** `mineru -p <pdf> -o <outdir>` — simpler to invoke but less control over output path and harder to capture return values.
- **Option C — REST API (`mineru-api`):** Third-party wrapper, requires a running server. Overkill for a local script.

**Recommendation:** Option B (CLI via subprocess) for `tools/doc_to_markdown.py` — simplest integration, well-documented, output path is controllable via `-o` flag. Fallback to Option A if CLI lacks a flag we need.

**Package:** `pip install "mineru[all]"` — the `[all]` extra includes all model backends.

---

### OQ-2: MinerU markdown image reference format

**Context:** Need to know what pattern to regex-match in the markdown to find image references.

**Findings:**
- MinerU outputs standard markdown: `![](images/<hash>.jpg)` — standard `![]()` with a relative path into the `images/` subfolder.
- Alt text is sometimes empty; the path is always relative to the markdown file.
- Figure captions, chart footnotes, and in-table images are supported as of MinerU 2.5 Pro.

**Output directory structure:**
```
<outdir>/
  <slug>.md
  <slug>_model.json
  <slug>_middle.json
  <slug>_content_list.json
  <slug>_content_list_v2.json
  <slug>_layout.pdf
  <slug>_span.pdf
  images/
    <hash1>.jpg
    <hash2>.png
    ...
```

**Recommendation:** Use regex `r'!\[.*?\]\((images/[^)]+)\)'` to extract all image paths from the markdown.

---

### OQ-3: Base64 vs file-based image handling

**Context:** Need to know whether extracted images are files on disk or base64 strings in the markdown.

**Findings:**
- Default MinerU output: **separate files** in `images/` subfolder. No base64 embedding.
- Base64 mode exists only in the third-party `mineru-api` REST server — not relevant to our CLI/SDK usage.
- Each image path in markdown resolves directly to `<outdir>/images/<hash>.<ext>`.

**Recommendation:** Handle file-based images only. Load each image from disk using its resolved path before sending to Gemini.

---

### OQ-4: Latest Gemini Flash model for vision

**Context:** User specified latest Gemini Flash. Need exact model ID and SDK.

**Findings:**
- **Model:** `gemini-3.5-flash` — GA as of May 19, 2026. Full vision/multimodal support. 1M token context window.
- `gemini-2.0-flash` — shut down June 1, 2026 (deprecated).
- `gemini-2.5-flash` — also deprecated before June 2026.
- **SDK:** `google-genai` (unified SDK, PyPI: `google-genai`, requires Python ≥ 3.10). The `google-generativeai` package is legacy (last updated Dec 2025).

**Recommendation:** Use `gemini-3.5-flash` via `google-genai`. Make model ID configurable via `--gemini-model` for future-proofing.

---

### OQ-5: Script location and structure

**Context:** User specified `tools/` directory with two separate tools.

**Decision (from user):**
- `tools/doc_to_markdown.py` — MinerU conversion (parsing layer)
- `tools/enhance_images.py` — Gemini image description (LLM enhancement layer)
- A top-level orchestrator (part of the `wiki-ingest` skill or a thin wrapper) calls both in sequence.

**Rationale:** Single-responsibility tools are independently testable. `tools/` fits the repo pattern (infrastructure tooling, not wiki content).

---

## Resolved Clarifications

| OQ | Resolution |
|----|-----------|
| OQ-1 | Use MinerU CLI via subprocess (`mineru -p <pdf> -o <outdir>`) |
| OQ-2 | Standard `![]()` markdown; images in `images/` subfolder; regex: `r'!\[.*?\]\((images/[^)]+)\)'` |
| OQ-3 | File-based only; load from `<outdir>/images/<hash>.<ext>` |
| OQ-4 | `gemini-3.5-flash` via `google-genai` SDK |
| OQ-5 | `tools/doc_to_markdown.py` + `tools/enhance_images.py` in `tools/` directory |

---

## Remaining Open Questions

None — all open questions resolved.

---

## Constraints Discovered

- **`mineru[all]` install is large** — includes model weights for layout detection. First run downloads models (~several GB). Script should document this clearly.
- **`gemini-3.5-flash` requires `GEMINI_API_KEY`** — standard Gemini API key from Google AI Studio. No special setup beyond the env var.
- **MinerU CLI output path** — the `-o` flag sets the output directory but MinerU may create a subdirectory named after the input file inside it. The script must discover the actual output path rather than assuming a fixed path.
- **Image hash filenames** — image filenames in `images/` are content-hash-based (not sequential). The regex match in the markdown is the only reliable way to enumerate them.
- **Python ≥ 3.10** required by `google-genai`; MinerU also recommends 3.10+.
