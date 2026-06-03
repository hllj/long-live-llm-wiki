# Implementation Plan: Document Ingest Pipeline (Feature 003)

**Spec:** [spec.md](spec.md) v3.1.0
**Research:** [research.md](research.md)
**Date:** 2026-06-03

---

## Goal

Extend `wiki-ingest` to accept binary source documents (PDF, DOCX) directly. Three internal Python tools in `skills/wiki-ingest/tools/` handle conversion and figure enrichment as Step 0. Each pipeline stage writes to a permanent intermediate folder (`raw/<slug>/`) so every step's artifact is inspectable. Sub-steps stream live progress to the terminal so users are never waiting in silence. `skills/wiki-ingest/SKILL.md` is updated to orchestrate the full journey in a single invocation.

---

## Architecture

```
skills/wiki-ingest/SKILL.md          ← Step 0 pre-process block (new)
       │
skills/wiki-ingest/tools/ingest_doc.py   ← orchestrator: manages workdir, idempotency, ingest.log
       │
       ├── skills/wiki-ingest/tools/doc_to_markdown.py   ← Layer 1: MinerU PDF→markdown
       │         subprocess.Popen → streams [MinerU] lines live
       │         heartbeat thread → prints "still running..." if silent >5s
       │         output: raw/<slug>/step1_mineru_raw.md + raw/<slug>/images/
       │
       └── skills/wiki-ingest/tools/enhance_images.py   ← Layer 2: Gemini figure enrichment
                 per-image progress: "[Gemini] Describing figure N/M: ... done (1.2s)"
                 output: raw/<slug>/step2_enhanced.md
```

**Data flow:**

```
input PDF
  → mineru CLI  → raw/<slug>/step1_mineru_raw.md + raw/<slug>/images/*.{jpg,png}
  → enhance_images.py  → raw/<slug>/step2_enhanced.md  (descriptions injected)
  → ingest_doc.py promotes  → raw/<slug>.md  (final artifact for Steps 1–8)
  → ingest_doc.py writes  → raw/<slug>/ingest.log  (run record)
```

On re-run without `--force`, `ingest_doc.py` inspects the existing `raw/<slug>/` folder, reports which stages completed, and offers to resume from the furthest complete stage.

---

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| PDF→Markdown | `mineru` CLI (`pip install "mineru[all]"`) | Spec FR-1.1; CLI is simplest subprocess integration |
| Image understanding | `google-genai` SDK, model `gemini-3.5-flash` | Spec FR-3.4; user decision |
| Image regex | `r'!\[.*?\]\((images/[^)]+)\)'` | Research OQ-2; matches MinerU standard output |
| Python version | 3.10+ | NFR-3 |
| Subprocess streaming | `subprocess.Popen` + line iteration | FR-6.3, FR-1.1, NFR-7 |
| Heartbeat | daemon `threading.Thread` | NFR-7; fires every 5s of silence |
| Progress output | `print(..., end="", flush=True)` + result appended | FR-3.1, AC-1.3 |

---

## File Structure

```
skills/wiki-ingest/
  SKILL.md               # Updated with Step 0 pre-process block (FR-6)
  tools/
    doc_to_markdown.py   # MinerU conversion + streaming + step1_mineru_raw.md (FR-1)
    enhance_images.py    # Gemini enrichment + per-image progress + step2_enhanced.md (FR-2, FR-3, FR-4)
    ingest_doc.py        # Orchestrator: workdir, idempotency, ingest.log (FR-5, FR-6)
    requirements.txt     # mineru[all], google-genai (NFR-3)
    README.md            # Usage + first-run model download warning (NFR-5)
    tests/
      __init__.py
      test_enhance_images.py
      test_doc_to_markdown.py
      test_ingest_doc.py
```

No modifications to `wiki/`, `raw/`, or `CLAUDE.md`.

---

## Pre-Implementation Gates

- **Simplicity Gate (≤3 components):** 3 scripts — exactly at limit, each justified by a single FR group.
- **Anti-Abstraction Gate:** No wrapper classes, no shared modules — each tool is a self-contained script.
- **Integration-First Gate:** CLI contracts defined in Phase 0 before any implementation code.

---

## Phase 0: Scaffold and CLI Contracts

**Creates:** `skills/wiki-ingest/tools/requirements.txt`, `skills/wiki-ingest/tools/README.md`

**`skills/wiki-ingest/tools/requirements.txt`:**
```
mineru[all]>=3.2.2
google-genai>=1.0.0
pytest>=8.0.0
```

**`skills/wiki-ingest/tools/README.md`:** (see tasks T01)

**Defined CLI contracts (orchestrator parses these from streamed stdout):**

`doc_to_markdown.py` stdout — mixed stream of `[MinerU]` progress lines followed by contract lines:
```
[MinerU] Processing page 1/15...
[MinerU] still running... elapsed: 12s
...
markdown:raw/<slug>/step1_mineru_raw.md
images:raw/<slug>/images
```

`enhance_images.py` stdout — per-image progress lines followed by summary:
```
[Gemini] Describing figure 1/10: images/fig1.png ... done (1.1s)
[Gemini] Describing figure 2/10: images/fig2.png ... FAILED (quota exceeded)
...
Images found: 10 | Described: 9 | Failed: 1
step2 written: raw/<slug>/step2_enhanced.md
```

Exit codes: `0` = full success, `1` = fatal error (abort), `2` = partial success (some image failures, output still written).

`parse_tool_output` in the orchestrator skips lines starting with `[` and only parses `key:value` contract lines.

---

## Phase 1: `skills/wiki-ingest/tools/doc_to_markdown.py`

**Implements:** FR-1 (MinerU conversion, streaming, heartbeat, step1_mineru_raw.md)
**Covers:** AC-1.2, NFR-7, error scenarios: "file not found", "MinerU fails", "MinerU silent >5s"

```python
#!/usr/bin/env python3
"""Convert a document to markdown using MinerU CLI."""
import argparse
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def convert(doc_path: Path, workdir: Path) -> tuple[Path, Path]:
    workdir.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        ["mineru", "-p", str(doc_path), "-o", str(workdir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    last_output = [time.time()]
    start = time.time()

    def heartbeat():
        while proc.poll() is None:
            time.sleep(1)
            if time.time() - last_output[0] >= 5:
                elapsed = int(time.time() - start)
                print(f"[MinerU] still running... elapsed: {elapsed}s", flush=True)
                last_output[0] = time.time()

    threading.Thread(target=heartbeat, daemon=True).start()

    for line in proc.stdout:
        last_output[0] = time.time()
        print(f"[MinerU] {line}", end="", flush=True)

    proc.wait()
    if proc.returncode != 0:
        sys.exit(1)

    md_files = sorted(f for f in workdir.rglob("*.md") if f.name != "step1_mineru_raw.md")
    if not md_files:
        print(f"Error: MinerU produced no markdown output in {workdir}", file=sys.stderr)
        sys.exit(1)

    step1_path = workdir / "step1_mineru_raw.md"
    shutil.copy2(md_files[0], step1_path)

    raw_images = md_files[0].parent / "images"
    target_images = workdir / "images"
    if raw_images.exists() and raw_images != target_images:
        if target_images.exists():
            shutil.rmtree(target_images)
        shutil.copytree(raw_images, target_images)

    return step1_path, target_images


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert document to markdown via MinerU")
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--workdir", required=True, help="Permanent work directory (raw/<slug>/)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    step1_path, images_dir = convert(doc_path, Path(args.workdir))

    print(f"markdown:{step1_path}")
    print(f"images:{images_dir}")


if __name__ == "__main__":
    main()
```

**Manual verification:** `python skills/wiki-ingest/tools/doc_to_markdown.py raw/attention.pdf --workdir raw/attention-test/` streams `[MinerU]` lines, then prints `markdown:` / `images:` contract lines. `ls raw/attention-test/` shows `step1_mineru_raw.md` and `images/`.

---

## Phase 2: `skills/wiki-ingest/tools/enhance_images.py`

**Implements:** FR-2 (image detection), FR-3 (Gemini + per-image progress), FR-4 (enrichment → step2_enhanced.md)
**Covers:** AC-1.3, AC-1.4, AC-1.5, AC-2.2, AC-3.1, AC-3.2

```python
#!/usr/bin/env python3
"""Enrich markdown image references with Gemini vision descriptions."""
import argparse
import os
import re
import sys
import time
from pathlib import Path

import google.genai as genai
from google.genai import types


IMAGE_RE = re.compile(r'(!\[.*?\]\((images/[^)]+)\))')
DESCRIPTION_MARKER = "**Figure description (Gemini):**"
GEMINI_PROMPT = (
    "You are analyzing a figure from a technical research document. "
    "Describe this figure in detail: what it shows, what data or relationships "
    "it represents, and its likely purpose in the context of the document. "
    "Be specific and technical. Limit your response to 3-5 sentences."
)
MIME_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "gif": "image/gif", "webp": "image/webp",
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

    Idempotent: skips images that already have a description block below them.
    Returns (enriched_text, images_found, images_described, failed_refs).
    """
    lines = markdown_text.splitlines(keepends=True)
    total = sum(1 for l in lines if IMAGE_RE.search(l))
    output: list[str] = []
    found = described = idx = 0
    failures: list[str] = []

    for i, line in enumerate(lines):
        output.append(line)
        match = IMAGE_RE.search(line)
        if not match:
            continue

        img_rel = match.group(2)
        found += 1
        idx += 1

        next_lines = [l for l in lines[i + 1 : i + 4] if l.strip()]
        if next_lines and DESCRIPTION_MARKER in next_lines[0]:
            continue

        img_path = images_dir / Path(img_rel).name
        if not img_path.exists():
            print(f"[Gemini] Describing figure {idx}/{total}: {img_rel} ... FAILED (file not found)", flush=True)
            failures.append(img_rel)
            output.append(f"> {DESCRIPTION_MARKER} [image file not found: {img_rel}]\n")
            continue

        print(f"[Gemini] Describing figure {idx}/{total}: {img_rel} ... ", end="", flush=True)
        t0 = time.time()
        try:
            description = describe_image(client, img_path, model)
            print(f"done ({time.time() - t0:.1f}s)", flush=True)
            output.append(f"> {DESCRIPTION_MARKER} {description}\n")
            described += 1
        except Exception as exc:
            print(f"FAILED ({exc}) ({time.time() - t0:.1f}s)", flush=True)
            failures.append(img_rel)
            output.append(f"> {DESCRIPTION_MARKER} [Gemini error — could not process image: {exc}]\n")

    return "".join(output), found, described, failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich markdown image references with Gemini descriptions"
    )
    parser.add_argument("markdown", help="Path to input markdown file (step1_mineru_raw.md)")
    parser.add_argument("images_dir", help="Path to images/ directory")
    parser.add_argument("--output", help="Output path (default: sibling step2_enhanced.md)")
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

    out_path = Path(args.output) if args.output else md_path.parent / "step2_enhanced.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(enriched, encoding="utf-8")

    print(f"Images found: {found} | Described: {described} | Failed: {len(failures)}")
    print(f"step2 written: {out_path}")
    if failures:
        print(f"Failed images: {', '.join(failures)}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

**Manual verification:**
```bash
GEMINI_API_KEY=<key> python skills/wiki-ingest/tools/enhance_images.py \
  raw/attention-test/step1_mineru_raw.md raw/attention-test/images/
```
Terminal shows per-image `[Gemini] Describing figure N/M: ...` lines. `raw/attention-test/step2_enhanced.md` created with `> **Figure description (Gemini):**` blocks.

---

## Phase 3: `skills/wiki-ingest/tools/ingest_doc.py`

**Implements:** FR-5 (orchestrator CLI), FR-5.5 (ingest.log)
**Covers:** AC-1.1, AC-1.4–1.8, AC-2.1–2.3, error scenarios: "output exists no --force", "partial state resume"

```python
#!/usr/bin/env python3
"""Orchestrate doc_to_markdown + enhance_images; manage workdir and ingest.log."""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_tool_output(stdout: str) -> dict[str, str]:
    """Parse key:value contract lines; skip [prefixed] progress lines."""
    result: dict[str, str] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("[") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        result[key.strip()] = val.strip()
    return result


def stream_subprocess(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    lines = []
    for line in proc.stdout:
        print(line, end="", flush=True)
        lines.append(line)
    stderr = proc.stderr.read()
    proc.wait()
    if stderr and proc.returncode != 0:
        print(stderr, file=sys.stderr)
    return proc.returncode, "".join(lines)


def inspect_workdir(workdir: Path) -> dict[str, bool]:
    return {
        "step1": (workdir / "step1_mineru_raw.md").exists(),
        "images": (workdir / "images").is_dir(),
        "step2": (workdir / "step2_enhanced.md").exists(),
    }


def report_workdir(workdir: Path, state: dict[str, bool]) -> None:
    rel = workdir.relative_to(REPO_ROOT)
    print(f"[Step 0] Intermediate folder already exists: {rel}/")
    tick = lambda b: "✓" if b else "✗"
    img_count = len(list((workdir / "images").glob("*"))) if state["images"] else 0
    print(f"  {tick(state['step1'])} step1_mineru_raw.md  ({'found' if state['step1'] else 'missing'})")
    print(f"  {tick(state['images'])} images/              ({img_count} files)" if state["images"] else f"  ✗ images/              (missing)")
    note = "(found — contains Gemini descriptions)" if state["step2"] else "(missing)"
    print(f"  {tick(state['step2'])} step2_enhanced.md    {note}")


def write_log(workdir: Path, entry: dict, force: bool) -> None:
    log_path = workdir / "ingest.log"
    mode = "w" if force else "a"
    with open(log_path, mode) as f:
        f.write(f"=== Run {datetime.datetime.utcnow().isoformat()}Z ===\n")
        for k, v in entry.items():
            f.write(f"{k}: {v}\n")
        f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a document into raw/ with Gemini-enriched figures"
    )
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--slug", help="Output slug (default: derived from filename)")
    parser.add_argument("--force", action="store_true", help="Re-run all steps, overwrite existing")
    parser.add_argument("--gemini-model", default="gemini-3.5-flash", help="Gemini model ID")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    slug = args.slug or slugify(doc_path.stem)
    workdir = REPO_ROOT / "raw" / slug
    out_path = REPO_ROOT / "raw" / f"{slug}.md"
    tools_dir = Path(__file__).resolve().parent
    start_time = time.time()
    log_entry: dict = {"document": doc_path.name, "slug": slug}

    skip_step1 = skip_step2 = False

    if workdir.exists() and not args.force:
        state = inspect_workdir(workdir)
        report_workdir(workdir, state)
        if state["step2"]:
            print("Re-run Step 0 and overwrite? [y/N] ", end="", flush=True)
            if input().strip().lower() != "y":
                skip_step1 = skip_step2 = True
        elif state["step1"]:
            print("step1_mineru_raw.md found but step2_enhanced.md missing.")
            print("Resume from Gemini enrichment only (skip MinerU re-run)? [Y/n] ", end="", flush=True)
            if input().strip().lower() != "n":
                skip_step1 = True

    workdir.mkdir(parents=True, exist_ok=True)

    if not skip_step1:
        rc, stdout = stream_subprocess([
            sys.executable, str(tools_dir / "doc_to_markdown.py"),
            str(doc_path), "--workdir", str(workdir),
        ])
        if rc != 0:
            sys.exit(1)

    step1_path = workdir / "step1_mineru_raw.md"
    images_dir = workdir / "images"

    if not step1_path.exists():
        print("Error: step1_mineru_raw.md not found after conversion", file=sys.stderr)
        sys.exit(1)

    exit_code = 0
    if not skip_step2:
        step2_path = workdir / "step2_enhanced.md"
        rc, _ = stream_subprocess([
            sys.executable, str(tools_dir / "enhance_images.py"),
            str(step1_path), str(images_dir),
            "--output", str(step2_path),
            "--gemini-model", args.gemini_model,
        ])
        if rc == 1:
            sys.exit(1)
        exit_code = rc

    step2_path = workdir / "step2_enhanced.md"
    if out_path.exists() and not args.force:
        print(f"[Step 0] {out_path.name} already exists. Overwrite? [y/N] ", end="", flush=True)
        if input().strip().lower() != "y":
            sys.exit(0)
    shutil.copy2(step2_path, out_path)

    elapsed = time.time() - start_time
    log_entry.update({"elapsed_s": f"{elapsed:.1f}", "exit_code": exit_code})
    write_log(workdir, log_entry, args.force)

    print(f"\nStep 0 complete — see terminal output above for image summary")
    print(f"Intermediate artifacts saved to: raw/{slug}/")
    print(f"Final enriched markdown:         raw/{slug}.md")


if __name__ == "__main__":
    main()
```

---

## Phase 4.5: Update `skills/wiki-ingest/SKILL.md`

**Implements:** FR-6 (Step 0 integration)
**Covers:** AC-1.1, AC-1.6–1.9, AC-2.1–2.3

Insert immediately before `### 1. Read the source`:

```markdown
### 0. Pre-process document (binary sources only)

Check the file extension of the source path the user provided.

- If **`.pdf` or `.docx`**: run Step 0 before anything else.
- If **`.md`** (or already markdown): skip to Step 1.

**Running Step 0:**

```bash
export GEMINI_API_KEY=<your-key>
python skills/wiki-ingest/tools/ingest_doc.py <source_path> [--slug <slug>] [--gemini-model <model>]
```

The script streams live output: `[MinerU]` conversion lines, then per-image `[Gemini] Describing figure N/M: ...` lines. Let all output stream through — do not suppress it.

If the intermediate folder `raw/<slug>/` already exists, the script shows a folder inspection report and prompts whether to re-run or reuse. Follow the user's answer.

After the script completes, it prints a summary:
```
Step 0 complete
Intermediate artifacts saved to: raw/<slug>/
Final enriched markdown:         raw/<slug>.md
```

Ask the user: **"Pre-processing complete. Proceed with wiki ingest? [y/n]"**

- **Yes:** use `raw/<slug>.md` as the source for Step 1 onward.
- **No:** stop — do not write any wiki pages.
- **Script exits non-zero (fatal error):** report the error and stop.
```

**Verify:** Pass `.pdf` → Step 0 fires and streams output. Pass `.md` → Step 0 skipped.

---

## Phase 4: Integration Verification

**Test fixture:** `raw/attention.pdf` (present in the repo)

```bash
export GEMINI_API_KEY=<your-key>
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test --force
```

**Verification checklist:**

| AC | Check | Command |
|---|---|---|
| AC-1.1 | "Step 0: Pre-processing" announced | check SKILL.md flow |
| AC-1.2 | MinerU lines streamed live | watch terminal during conversion |
| AC-1.3 | Per-image Gemini lines shown | watch terminal during enrichment |
| AC-1.4 | Intermediate folder created | `ls raw/attention-test/` |
| AC-1.4 | `step1_mineru_raw.md` exists | `ls raw/attention-test/step1_mineru_raw.md` |
| AC-1.4 | `images/` exists | `ls raw/attention-test/images/` |
| AC-1.4 | `step2_enhanced.md` exists | `ls raw/attention-test/step2_enhanced.md` |
| AC-1.5 | Summary + final path printed | check stdout for `raw/attention-test.md` |
| AC-1.5 | Final .md promoted | `ls raw/attention-test.md` |
| AC-1.5 | Contains figure descriptions | `grep "Figure description (Gemini)" raw/attention-test.md` |
| FR-5.5 | `ingest.log` created | `cat raw/attention-test/ingest.log` |
| AC-2.1 | Folder inspection on re-run | re-run without `--force`, check report |
| AC-2.2 | Reuse step2 without re-running | answer `n` at prompt, confirm fast skip |
| AC-2.3 | `--force` re-runs all | re-run with `--force`, confirm fresh output |
| AC-1.9 | Skip Step 0 for .md | invoke wiki-ingest on `.md` source |

**Error scenario spot-checks:**
```bash
# File not found
python skills/wiki-ingest/tools/ingest_doc.py nonexistent.pdf
# Expected: exit 1, "Error: file not found: nonexistent.pdf"

# Missing API key
unset GEMINI_API_KEY
python skills/wiki-ingest/tools/enhance_images.py /dev/null /tmp
# Expected: exit 1, "Error: GEMINI_API_KEY environment variable not set"

# MinerU silent heartbeat (hard to trigger in test; check code path in review)
```

Clean up:
```bash
rm -rf raw/attention-test/ raw/attention-test.md
```

---

## Spec Coverage Check

| FR / NFR | Phase | ✓ |
|---|---|---|
| FR-6.1 — SKILL.md Step 0 block | Phase 4.5 | ✓ |
| FR-6.2 — extension detection | Phase 4.5 | ✓ |
| FR-6.3 — Popen streaming | Phase 4.5, Phase 3 | ✓ |
| FR-6.4 — user confirmation prompt | Phase 4.5 | ✓ |
| FR-6.5 — enriched md as Steps 1–8 source | Phase 4.5 | ✓ |
| FR-1.1 — MinerU Popen + streaming + [MinerU] prefix | Phase 1 | ✓ |
| FR-1.2 — workdir = raw/<slug>/ | Phase 1 | ✓ |
| FR-1.3 — rename to step1_mineru_raw.md | Phase 1 (`shutil.copy2`) | ✓ |
| FR-1.4 — PDF input | Phase 1 | ✓ |
| FR-1.5 — images/ in workdir | Phase 1 (`shutil.copytree`) | ✓ |
| FR-1.6 — updated contract lines | Phase 1 | ✓ |
| FR-2.1 — image regex | Phase 2 (`IMAGE_RE`) | ✓ |
| FR-2.2 — resolve image path | Phase 2 (`images_dir / Path(img_rel).name`) | ✓ |
| FR-3.1 — per-image progress line before + result after | Phase 2 | ✓ |
| FR-3.2 — Gemini vision call | Phase 2 (`describe_image`) | ✓ |
| FR-3.3 — GEMINI_API_KEY env var | Phase 2 | ✓ |
| FR-3.4 — configurable model | Phase 2 (`--gemini-model`) | ✓ |
| FR-4.1 — blockquote description format | Phase 2 | ✓ |
| FR-4.2 — preserve original image lines | Phase 2 | ✓ |
| FR-4.3 — write to step2_enhanced.md | Phase 2 | ✓ |
| FR-4.4 — promote to raw/<slug>.md | Phase 3 (`shutil.copy2`) | ✓ |
| FR-5.1 — updated doc_to_markdown contract | Phase 1 | ✓ |
| FR-5.2 — updated enhance_images contract | Phase 2 | ✓ |
| FR-5.3 — exit codes | Phases 1–3 | ✓ |
| FR-5.4 — ingest_doc orchestration with workdir | Phase 3 | ✓ |
| FR-5.5 — ingest.log append-only | Phase 3 (`write_log`) | ✓ |
| NFR-3 — requirements.txt | Phase 0 | ✓ |
| NFR-4 — no hardcoded keys | All phases (env var only) | ✓ |
| NFR-5 — developer README | Phase 0 | ✓ |
| NFR-7 — heartbeat ≤5s silence | Phase 1 (daemon thread) | ✓ |
| NFR-8 — intermediate artifacts preserved | Phase 3 (no tmpdir cleanup) | ✓ |
