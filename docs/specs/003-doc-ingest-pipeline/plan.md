# Implementation Plan: Document Ingest Pipeline (Feature 003)

**Spec:** [spec.md](spec.md) v3.0.0
**Research:** [research.md](research.md)
**Date:** 2026-06-03

---

## Goal

Extend `wiki-ingest` to accept binary source documents (PDF, DOCX) directly. Three internal Python tools in `skills/wiki-ingest/tools/` handle conversion and figure enrichment as Step 0; `skills/wiki-ingest/SKILL.md` is updated so wiki-ingest orchestrates the full journey from binary document to enriched wiki pages in a single invocation.

---

## Architecture

```
skills/wiki-ingest/SKILL.md          ← Step 0 pre-process block (new)
       │
skills/wiki-ingest/tools/ingest_doc.py   ← orchestrator (end-to-end CLI)
       │
       ├── skills/wiki-ingest/tools/doc_to_markdown.py   ← Layer 1: MinerU PDF→markdown
       │         invokes: mineru CLI via subprocess
       │         outputs: <tmpdir>/<stem>.md + <tmpdir>/images/
       │
       └── skills/wiki-ingest/tools/enhance_images.py   ← Layer 2: Gemini image enrichment
                 reads: markdown + images/
                 outputs: enriched markdown at raw/<slug>.md
```

Each tool is independently invokable as a CLI script. The orchestrator wires them together with temp directory management and idempotency guards.

**Data flow:**

```
input PDF
  → mineru CLI → <tmpdir>/<stem>.md + <tmpdir>/images/*.{jpg,png}
  → enhance_images.py → enriched markdown with > **Figure description (Gemini):** blocks
  → raw/<slug>.md
```

---

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| PDF→Markdown | `mineru` CLI (`pip install "mineru[all]"`) | Spec FR-1.1; CLI is simplest subprocess integration |
| Image understanding | `google-genai` SDK, model `gemini-3.5-flash` | Spec FR-3.3; user decision; latest GA Flash model |
| Image regex | `r'!\[.*?\]\((images/[^)]+)\)'` | Research OQ-2; matches MinerU standard output |
| Python version | 3.10+ | NFR-3; required by `google-genai` |
| Subprocess comms | stdout lines `markdown:<path>` / `images:<path>` | Simple, no extra deps, parseable by orchestrator |

---

## File Structure

```
skills/wiki-ingest/
  SKILL.md               # Updated with Step 0 pre-process block (FR-6)
  tools/
    doc_to_markdown.py   # MinerU conversion layer (FR-1)
    enhance_images.py    # Gemini enrichment layer (FR-2, FR-3, FR-4)
    ingest_doc.py        # Orchestrator (FR-5)
    requirements.txt     # mineru[all], google-genai (NFR-3)
    README.md            # Usage + first-run model download warning (NFR-5)
    tests/
      __init__.py
      test_enhance_images.py
      test_doc_to_markdown.py
      test_ingest_doc.py
```

No modifications to `wiki/`, `raw/`, or `CLAUDE.md` — only `skills/wiki-ingest/` is updated.

---

## Pre-Implementation Gates

- **Simplicity Gate (≤3 components):** 3 scripts — exactly at limit, each justified by a single FR.
- **Anti-Abstraction Gate:** No wrapper classes, no shared modules — each tool is a self-contained script with stdlib + direct SDK calls.
- **Integration-First Gate:** CLI contracts defined in Phase 0 before any implementation code.

---

## Phase 0: Scaffold and CLI Contracts

**Creates:** `skills/wiki-ingest/tools/requirements.txt`, `skills/wiki-ingest/tools/README.md`

**`skills/wiki-ingest/tools/requirements.txt`:**
```
mineru[all]>=3.2.2
google-genai>=1.0.0
```

**`skills/wiki-ingest/tools/README.md`:**
```markdown
# skills/wiki-ingest/tools/

Internal tools for wiki-ingest binary document support (Feature 003).
These scripts are called by the wiki-ingest skill — do not invoke them directly.

## Developer Setup

```bash
pip install -r skills/wiki-ingest/tools/requirements.txt
```

> **First run:** `mineru[all]` downloads layout detection model weights (~several GB) on first
> invocation. Ensure you have disk space and a stable connection before first use.

## Running tests

```bash
cd /path/to/repo
python -m pytest skills/wiki-ingest/tools/tests/ -v
```
```

**Defined CLI contracts (orchestrator reads these from stdout):**

`doc_to_markdown.py` stdout on success:
```
markdown:/abs/path/to/<stem>.md
images:/abs/path/to/images
```

`enhance_images.py` stdout on completion:
```
Images found: N | Described: M | Failed: K
```

Exit codes:
- `0` — full success
- `1` — fatal error (abort pipeline)
- `2` — partial success (some image failures, output still written)

---

## Phase 1: `skills/wiki-ingest/tools/doc_to_markdown.py`

**Implements:** FR-1 (MinerU conversion)
**Covers:** AC-1.1, AC-1.2, AC-1.3, error scenarios: "file not found", "MinerU fails"

```python
#!/usr/bin/env python3
"""Convert a document to markdown using MinerU CLI."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def convert(doc_path: Path, outdir: Path) -> tuple[Path, Path]:
    result = subprocess.run(
        ["mineru", "-p", str(doc_path), "-o", str(outdir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    # MinerU may nest output under a subdir named after the input stem.
    # Find the first .md file produced anywhere under outdir.
    md_files = sorted(Path(outdir).rglob("*.md"))
    if not md_files:
        print(f"Error: MinerU produced no markdown output in {outdir}", file=sys.stderr)
        sys.exit(1)

    md_path = md_files[0]
    images_dir = md_path.parent / "images"
    return md_path, images_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert document to markdown via MinerU")
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--outdir", help="Output directory (default: auto temp dir)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    outdir = Path(args.outdir) if args.outdir else Path(tempfile.mkdtemp(prefix="mineru_"))
    outdir.mkdir(parents=True, exist_ok=True)

    md_path, images_dir = convert(doc_path, outdir)

    # Print contract lines for the orchestrator to parse
    print(f"markdown:{md_path}")
    print(f"images:{images_dir}")


if __name__ == "__main__":
    main()
```

**Manual verification:** `python skills/wiki-ingest/tools/doc_to_markdown.py raw/attention.pdf` prints two `markdown:` / `images:` lines and exits 0.

---

## Phase 2: `skills/wiki-ingest/tools/enhance_images.py`

**Implements:** FR-2 (image detection), FR-3 (Gemini), FR-4 (enrichment)
**Covers:** AC-1.4, AC-1.5, AC-2.1, AC-3.1, AC-3.2, error scenarios: "GEMINI_API_KEY not set", "single image failure", "all failures"

```python
#!/usr/bin/env python3
"""Enrich markdown image references with Gemini vision descriptions."""
import argparse
import os
import re
import sys
from pathlib import Path

import google.genai as genai
from google.genai import types


IMAGE_RE = re.compile(r'(!\[.*?\]\((images/[^)]+)\))')
DESCRIPTION_MARKER = "**Figure description (Gemini):**"
GEMINI_PROMPT = (
    "You are analyzing a figure from a technical research document. "
    "Describe this figure in detail: what it shows, what data or relationships "
    "it represents, and its likely purpose in the context of the document. "
    "Be specific and technical. Limit your response to 3–5 sentences."
)
MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def describe_image(client: genai.Client, image_path: Path, model: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    mime_type = MIME_MAP.get(image_path.suffix.lower().lstrip("."), "image/jpeg")
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            GEMINI_PROMPT,
        ],
    )
    return response.text.strip()


def enrich(
    markdown_text: str,
    images_dir: Path,
    client: genai.Client,
    model: str,
) -> tuple[str, int, int, list[str]]:
    """Insert Gemini descriptions after each image reference.

    Returns (enriched_text, images_found, images_described, failed_refs).
    Idempotent: skips image lines that already have a description block below them.
    """
    lines = markdown_text.splitlines(keepends=True)
    output: list[str] = []
    found = described = 0
    failures: list[str] = []

    for i, line in enumerate(lines):
        output.append(line)
        match = IMAGE_RE.search(line)
        if not match:
            continue

        img_rel = match.group(2)
        found += 1

        # Idempotency: if the very next non-empty line already has the marker, skip
        next_lines = [l for l in lines[i + 1 : i + 4] if l.strip()]
        if next_lines and DESCRIPTION_MARKER in next_lines[0]:
            continue

        img_path = images_dir / Path(img_rel).name
        if not img_path.exists():
            failures.append(img_rel)
            output.append(f"> {DESCRIPTION_MARKER} [image file not found: {img_rel}]\n")
            continue

        try:
            description = describe_image(client, img_path, model)
            output.append(f"> {DESCRIPTION_MARKER} {description}\n")
            described += 1
        except Exception as exc:
            failures.append(img_rel)
            output.append(f"> {DESCRIPTION_MARKER} [Gemini error — could not process image: {exc}]\n")

    return "".join(output), found, described, failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich markdown image references with Gemini descriptions"
    )
    parser.add_argument("markdown", help="Path to input markdown file")
    parser.add_argument("images_dir", help="Path to directory containing extracted images")
    parser.add_argument("--output", help="Output path (default: overwrite input)")
    parser.add_argument("--gemini-model", default="gemini-3.5-flash", help="Gemini model ID")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    images_dir = Path(args.images_dir)
    client = genai.Client(api_key=api_key)

    text = md_path.read_text(encoding="utf-8")
    enriched, found, described, failures = enrich(text, images_dir, client, args.gemini_model)

    out_path = Path(args.output) if args.output else md_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(enriched, encoding="utf-8")

    print(f"Images found: {found} | Described: {described} | Failed: {len(failures)}")
    if failures:
        print(f"Failed images: {', '.join(failures)}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

**Manual verification:**
1. Obtain a markdown file with `![](images/foo.jpg)` references and a real image.
2. `GEMINI_API_KEY=<key> python skills/wiki-ingest/tools/enhance_images.py /tmp/test.md /tmp/images --output /tmp/enriched.md`
3. `grep "Figure description" /tmp/enriched.md` returns at least one match.

---

## Phase 3: `skills/wiki-ingest/tools/ingest_doc.py`

**Implements:** FR-5 (orchestrator CLI)
**Covers:** AC-1.1–1.5, AC-2.2, AC-4.1, AC-4.2, error scenario: "output exists, no --force"

```python
#!/usr/bin/env python3
"""Orchestrate doc_to_markdown + enhance_images and write output to raw/."""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_tool_output(stdout: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in stdout.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a document into raw/ with Gemini-enriched figures"
    )
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--slug", help="Output slug (default: derived from filename)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    parser.add_argument("--gemini-model", default="gemini-3.5-flash", help="Gemini model ID")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    slug = args.slug or slugify(doc_path.stem)
    out_path = REPO_ROOT / "raw" / f"{slug}.md"

    if out_path.exists() and not args.force:
        print(
            f"Error: raw/{slug}.md already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    tools_dir = Path(__file__).resolve().parent

    with tempfile.TemporaryDirectory(prefix="ingest_") as tmpdir:
        # Step 1: MinerU conversion
        print(f"[1/2] Converting {doc_path.name} with MinerU...")
        r1 = subprocess.run(
            [sys.executable, str(tools_dir / "doc_to_markdown.py"), str(doc_path), "--outdir", tmpdir],
            capture_output=True,
            text=True,
        )
        if r1.returncode != 0:
            print(r1.stderr, file=sys.stderr)
            sys.exit(1)

        paths = parse_tool_output(r1.stdout)
        md_path = Path(paths.get("markdown", ""))
        images_dir = Path(paths.get("images", ""))

        if not md_path or not md_path.exists():
            print("Error: doc_to_markdown.py did not produce a markdown file", file=sys.stderr)
            sys.exit(1)

        # Step 2: Gemini enrichment (write to tmp path first, then copy)
        enriched_tmp = Path(tmpdir) / f"{slug}.md"
        print(f"[2/2] Enriching figures with {args.gemini_model}...")
        r2 = subprocess.run(
            [
                sys.executable,
                str(tools_dir / "enhance_images.py"),
                str(md_path),
                str(images_dir),
                "--output", str(enriched_tmp),
                "--gemini-model", args.gemini_model,
            ],
            capture_output=True,
            text=True,
        )
        print(r2.stdout.strip())
        if r2.returncode == 1:
            print(r2.stderr, file=sys.stderr)
            sys.exit(1)
        if r2.returncode == 2:
            # Partial failures — warn but continue
            print(f"Warning: {r2.stderr.strip()}", file=sys.stderr)

        # Step 3: Copy enriched markdown to raw/
        shutil.copy2(enriched_tmp, out_path)
        print(f"Output: raw/{slug}.md")


if __name__ == "__main__":
    main()
```

---

## Phase 4.5: Update `skills/wiki-ingest/SKILL.md`

**Implements:** FR-6 (wiki-ingest Step 0 integration)
**Covers:** AC-5.1 – AC-5.5

Insert a **Step 0: Pre-process document** block immediately before the existing `### 1. Read the source` section in `skills/wiki-ingest/SKILL.md`:

```markdown
### 0. Pre-process document (binary sources only)

Check the file extension of the source path the user provided.

- If the extension is **`.pdf` or `.docx`**: run Step 0 before anything else.
- If the extension is **`.md`** (or no extension): skip to Step 1 — source is already markdown.

**Running Step 0:**

```bash
export GEMINI_API_KEY=<your-key>
python skills/wiki-ingest/tools/ingest_doc.py <source_path> [--slug <slug>] [--gemini-model <model>]
```

Display the full stdout output (conversion summary: images found, described, failures).

After displaying the summary, ask the user:

> "Pre-processing complete. Proceed with wiki ingest? [y/n]"

- **If yes:** the enriched markdown at `raw/<slug>.md` is now the source for Step 1 onward.
- **If no:** stop here. Do not write any wiki pages.
- **If the script exits non-zero (fatal error):** report the error and stop. Do not write any wiki pages.
```

**Manual verification:** Pass a `.pdf` path to wiki-ingest and confirm Step 0 fires. Pass a `.md` path and confirm Step 0 is skipped.

---

## Phase 4: Integration Verification

**Test fixture:** `raw/attention.pdf` (already present in the repo)

Run the full pipeline end-to-end:

```bash
export GEMINI_API_KEY=<your-key>

# Run orchestrator on the existing test PDF
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test --force
```

**Verification checklist (AC coverage):**

| AC | Check | Command |
|---|---|---|
| AC-1.1 | Exits 0 | `echo $?` |
| AC-1.2 | Output file exists | `ls raw/attention-test.md` |
| AC-1.3 | Contains text content | `wc -l raw/attention-test.md` (expect > 50 lines) |
| AC-1.4 | Contains figure descriptions | `grep "Figure description (Gemini)" raw/attention-test.md` |
| AC-1.5 | Summary line printed | check stdout for `Images found:` |
| AC-2.2 | Duplicate-run guard | re-run without `--force`, expect error message |
| AC-3.1 | Placeholder on failure | inject bad image path, check placeholder inserted |
| AC-4.1 | Custom slug | `python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug my-custom` → `raw/my-custom.md` |
| AC-4.2 | Default slug | `python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --force` → `raw/attention.md` |
| AC-5.1–5.5 | wiki-ingest Step 0 fires on PDF, skips on .md | manual skill invocation test |

**Error scenario spot-checks:**
```bash
# File not found
python skills/wiki-ingest/tools/ingest_doc.py nonexistent.pdf
# Expected: "Error: file not found: nonexistent.pdf", exit 1

# Missing API key
unset GEMINI_API_KEY
python skills/wiki-ingest/tools/enhance_images.py /tmp/test.md /tmp/images
# Expected: "Error: GEMINI_API_KEY environment variable not set", exit 1

# Output exists, no --force
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test
# Expected: "Error: raw/attention-test.md already exists. Use --force to overwrite.", exit 1
```

---

## Spec Coverage Check

| FR | Phase | ✓ |
|---|---|---|
| FR-6.1 — SKILL.md Step 0 block | Phase 4.5 | ✓ |
| FR-6.2 — extension detection | Phase 4.5 | ✓ |
| FR-6.3 — orchestrator invocation | Phase 4.5 | ✓ |
| FR-6.4 — user confirmation prompt | Phase 4.5 | ✓ |
| FR-6.5 — enriched md as Steps 1–8 source | Phase 4.5 | ✓ |
| FR-1.1 — MinerU CLI subprocess | Phase 1 | ✓ |
| FR-1.2 — PDF input | Phase 1 | ✓ |
| FR-1.3 — images/ subfolder | Phase 1 | ✓ |
| FR-1.4 — discover actual output subdir | Phase 1 (`rglob("*.md")`) | ✓ |
| FR-2.1 — image regex | Phase 2 (`IMAGE_RE`) | ✓ |
| FR-2.2 — resolve image path | Phase 2 (`images_dir / Path(img_rel).name`) | ✓ |
| FR-3.1 — Gemini vision call | Phase 2 (`describe_image`) | ✓ |
| FR-3.2 — GEMINI_API_KEY env var | Phase 2 | ✓ |
| FR-3.3 — configurable model | Phase 2 (`--gemini-model`) | ✓ |
| FR-4.1 — blockquote description format | Phase 2 | ✓ |
| FR-4.2 — preserve original image lines | Phase 2 (`output.append(line)` before enrichment) | ✓ |
| FR-4.3 — write to raw/<slug>.md | Phase 3 | ✓ |
| FR-5.1 — doc_to_markdown stdout contract | Phase 1 | ✓ |
| FR-5.2 — enhance_images stdout contract | Phase 2 | ✓ |
| FR-5.3 — exit codes | Phases 1–3 | ✓ |
| FR-5.4 — ingest_doc.py orchestration | Phase 3 | ✓ |
| NFR-3 — requirements.txt | Phase 0 | ✓ |
| NFR-4 — no hardcoded keys | All phases (env var only) | ✓ |
| NFR-5 — developer README | Phase 0 | ✓ |
