# Tasks: Document Ingest Pipeline (Feature 003)

**Plan:** [plan.md](plan.md) (spec v3.0.0)
**Branch:** `003-doc-ingest-pipeline`
**Date:** 2026-06-03

---

## Legend
- `[P]` — safe to run concurrently with other `[P]` tasks in the same group
- RED / GREEN refer to test state

---

## Group 0: Scaffold

### T01 — Create skills/wiki-ingest/tools/ scaffold
**Files:** `skills/wiki-ingest/tools/requirements.txt`, `skills/wiki-ingest/tools/tests/__init__.py`, `skills/wiki-ingest/tools/README.md`

Move (or recreate) `tools/tests/__init__.py` → `skills/wiki-ingest/tools/tests/__init__.py` and remove the old `tools/` directory.

Create `skills/wiki-ingest/tools/requirements.txt`:
```
mineru[all]>=3.2.2
google-genai>=1.0.0
pytest>=8.0.0
```

Create `skills/wiki-ingest/tools/tests/__init__.py`: empty file (touch it).

Create `skills/wiki-ingest/tools/README.md`:
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

**Verify:**
```bash
ls /Users/hllj/Projects/long-live-wiki/skills/wiki-ingest/tools/
```
Expected: `README.md  requirements.txt  tests/`

---

### T02 — Install dependencies
```bash
cd /Users/hllj/Projects/long-live-wiki && pip install -r skills/wiki-ingest/tools/requirements.txt
```
Expected: All packages install successfully. `python -c "import google.genai; print('ok')"` prints `ok`.

---

## Group 1: enhance_images.py (TDD)

### T03 — Write failing tests for `enrich()`
**File:** `skills/wiki-ingest/tools/tests/test_enhance_images.py`

```python
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import enhance_images


def test_enrich_inserts_description_after_image(tmp_path):
    """enrich() appends a blockquote description immediately after each image line."""
    img = tmp_path / "images" / "abc.jpg"
    img.parent.mkdir()
    img.write_bytes(b"fake image content")

    md = "# Doc\n\n![alt text](images/abc.jpg)\n\nSome text.\n"

    with patch.object(enhance_images, "describe_image", return_value="A bar chart showing loss curves."):
        result, found, described, failures = enhance_images.enrich(
            md, tmp_path, MagicMock(), "gemini-3.5-flash"
        )

    assert found == 1
    assert described == 1
    assert failures == []
    assert "![alt text](images/abc.jpg)" in result
    assert "> **Figure description (Gemini):** A bar chart showing loss curves." in result
    lines = result.splitlines()
    img_idx = next(i for i, l in enumerate(lines) if "abc.jpg" in l)
    assert "Figure description (Gemini):" in lines[img_idx + 1]


def test_enrich_idempotent_skips_existing_description(tmp_path):
    """enrich() does not duplicate descriptions if the marker already follows the image."""
    img = tmp_path / "images" / "abc.jpg"
    img.parent.mkdir()
    img.write_bytes(b"fake")

    md = (
        "# Doc\n\n"
        "![alt](images/abc.jpg)\n"
        "> **Figure description (Gemini):** Already described.\n\n"
        "Text.\n"
    )

    with patch.object(enhance_images, "describe_image") as mock_desc:
        result, found, described, failures = enhance_images.enrich(
            md, tmp_path, MagicMock(), "gemini-3.5-flash"
        )

    mock_desc.assert_not_called()
    assert result.count("Figure description (Gemini):") == 1


def test_enrich_missing_image_file_inserts_placeholder(tmp_path):
    """enrich() inserts a placeholder and adds to failures when image file is absent."""
    (tmp_path / "images").mkdir()
    md = "# Doc\n\n![](images/missing.jpg)\n\nText.\n"

    result, found, described, failures = enhance_images.enrich(
        md, tmp_path, MagicMock(), "gemini-3.5-flash"
    )

    assert found == 1
    assert described == 0
    assert "images/missing.jpg" in failures
    assert "[image file not found:" in result


def test_enrich_gemini_exception_inserts_error_placeholder(tmp_path):
    """enrich() inserts an error placeholder and continues when Gemini raises."""
    img = tmp_path / "images" / "bad.jpg"
    img.parent.mkdir()
    img.write_bytes(b"fake")

    md = "# Doc\n\n![](images/bad.jpg)\n"

    with patch.object(enhance_images, "describe_image", side_effect=RuntimeError("API down")):
        result, found, described, failures = enhance_images.enrich(
            md, tmp_path, MagicMock(), "gemini-3.5-flash"
        )

    assert found == 1
    assert described == 0
    assert "images/bad.jpg" in failures
    assert "Gemini error" in result
    assert "API down" in result


def test_cli_missing_api_key(tmp_path):
    """CLI exits 1 with a clear message when GEMINI_API_KEY is not set."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n")
    (tmp_path / "images").mkdir()

    env = {"PATH": "/usr/bin:/bin"}  # no GEMINI_API_KEY
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/enhance_images.py", str(md_file), str(tmp_path / "images")],
        capture_output=True,
        text=True,
        env=env,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )

    assert result.returncode == 1
    assert "GEMINI_API_KEY" in result.stderr
```

**Verify (RED):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_enhance_images.py -v 2>&1 | head -30
```
Expected: `ModuleNotFoundError: No module named 'enhance_images'` (5 errors) — file doesn't exist yet.

---

### T04 — Implement `skills/wiki-ingest/tools/enhance_images.py`
**File:** `skills/wiki-ingest/tools/enhance_images.py`

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
    "Be specific and technical. Limit your response to 3-5 sentences."
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

**Verify (GREEN):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_enhance_images.py -v
```
Expected: `5 passed`

---

## Group 2: doc_to_markdown.py (TDD)

### T05 — Write failing tests for `convert()`
**File:** `skills/wiki-ingest/tools/tests/test_doc_to_markdown.py`

```python
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import doc_to_markdown


def test_convert_finds_nested_markdown(tmp_path):
    """convert() returns the .md file path even when MinerU nests it in a subdirectory."""
    nested = tmp_path / "paper" / "auto"
    nested.mkdir(parents=True)
    md_file = nested / "paper.md"
    md_file.write_text("# Paper\n")
    (nested / "images").mkdir()

    with patch.object(doc_to_markdown.subprocess, "run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        md_path, images_dir = doc_to_markdown.convert(Path("fake.pdf"), tmp_path)

    assert md_path == md_file
    assert images_dir == nested / "images"


def test_convert_exits_when_mineru_fails(tmp_path):
    """convert() calls sys.exit(1) and prints stderr when MinerU returns non-zero."""
    with patch.object(doc_to_markdown.subprocess, "run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="mineru: model load failed")
        with pytest.raises(SystemExit) as exc:
            doc_to_markdown.convert(Path("fake.pdf"), tmp_path)
    assert exc.value.code == 1


def test_convert_exits_when_no_md_produced(tmp_path):
    """convert() calls sys.exit(1) when MinerU succeeds but produces no .md file."""
    with patch.object(doc_to_markdown.subprocess, "run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        with pytest.raises(SystemExit) as exc:
            doc_to_markdown.convert(Path("fake.pdf"), tmp_path)
    assert exc.value.code == 1


def test_cli_file_not_found():
    """CLI exits 1 with 'Error: file not found' when input path does not exist."""
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/doc_to_markdown.py", "nonexistent_file.pdf"],
        capture_output=True,
        text=True,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )
    assert result.returncode == 1
    assert "Error: file not found" in result.stderr


def test_cli_prints_contract_lines(tmp_path):
    """CLI prints 'markdown:<path>' and 'images:<path>' lines on success."""
    fake_pdf = tmp_path / "test.pdf"
    fake_pdf.write_bytes(b"%PDF fake")

    nested = tmp_path / "test" / "auto"
    nested.mkdir(parents=True)
    md_file = nested / "test.md"
    md_file.write_text("# Test\n")
    (nested / "images").mkdir()

    with patch("doc_to_markdown.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        # Run via importlib to avoid subprocess overhead
        import importlib, io
        from contextlib import redirect_stdout
        doc_to_markdown_mod = importlib.import_module("doc_to_markdown")

        buf = io.StringIO()
        with redirect_stdout(buf):
            doc_to_markdown_mod.convert(fake_pdf, tmp_path)

    # convert() itself doesn't print; main() does — test that contract format is correct
    # by checking that the output lines from main() parse correctly
    with patch("doc_to_markdown.convert", return_value=(md_file, nested / "images")):
        with patch("sys.argv", ["doc_to_markdown.py", str(fake_pdf)]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                doc_to_markdown_mod.main()
    output = buf.getvalue()
    assert f"markdown:{md_file}" in output
    assert f"images:{nested / 'images'}" in output
```

**Verify (RED):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py -v 2>&1 | head -20
```
Expected: `ModuleNotFoundError: No module named 'doc_to_markdown'` — file doesn't exist yet.

---

### T06 — Implement `skills/wiki-ingest/tools/doc_to_markdown.py`
**File:** `skills/wiki-ingest/tools/doc_to_markdown.py`

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

**Verify (GREEN):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py -v
```
Expected: `5 passed`

---

## Group 3: ingest_doc.py (TDD)

### T07 — Write failing tests for `slugify`, `parse_tool_output`, and output-guard
**File:** `skills/wiki-ingest/tools/tests/test_ingest_doc.py`

```python
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ingest_doc


def test_slugify_lowercases_and_hyphenates():
    assert ingest_doc.slugify("My Paper Title") == "my-paper-title"


def test_slugify_replaces_underscores():
    assert ingest_doc.slugify("attention_is_all_you_need") == "attention-is-all-you-need"


def test_slugify_strips_leading_trailing_hyphens():
    assert ingest_doc.slugify("--hello--") == "hello"


def test_slugify_collapses_multiple_separators():
    assert ingest_doc.slugify("hello   world") == "hello-world"


def test_parse_tool_output_extracts_paths():
    stdout = "markdown:/tmp/out/paper.md\nimages:/tmp/out/images\n"
    result = ingest_doc.parse_tool_output(stdout)
    assert result["markdown"] == "/tmp/out/paper.md"
    assert result["images"] == "/tmp/out/images"


def test_parse_tool_output_handles_extra_lines():
    stdout = "[1/2] Converting...\nmarkdown:/tmp/a.md\nimages:/tmp/imgs\nDone.\n"
    result = ingest_doc.parse_tool_output(stdout)
    assert result["markdown"] == "/tmp/a.md"
    assert result["images"] == "/tmp/imgs"


def test_cli_file_not_found():
    """CLI exits 1 with error message when input document doesn't exist."""
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/ingest_doc.py", "no_such_file.pdf"],
        capture_output=True,
        text=True,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )
    assert result.returncode == 1
    assert "Error: file not found" in result.stderr


def test_cli_output_exists_no_force(tmp_path):
    """CLI exits 1 with 'already exists' when output slug exists and --force is absent."""
    sentinel = Path("/Users/hllj/Projects/long-live-wiki/raw/test-guard-sentinel.md")
    sentinel.write_text("# existing\n")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "skills/wiki-ingest/tools/ingest_doc.py",
                "raw/attention.pdf",
                "--slug",
                "test-guard-sentinel",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/hllj/Projects/long-live-wiki",
        )
        assert result.returncode == 1
        assert "already exists" in result.stderr
        assert "--force" in result.stderr
    finally:
        sentinel.unlink(missing_ok=True)
```

**Verify (RED):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_ingest_doc.py -v 2>&1 | head -20
```
Expected: `ModuleNotFoundError: No module named 'ingest_doc'` — file doesn't exist yet.

---

### T08 — Implement `skills/wiki-ingest/tools/ingest_doc.py`
**File:** `skills/wiki-ingest/tools/ingest_doc.py`

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

        # Step 2: Gemini enrichment — write to tmp first, then copy to raw/
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
            print(f"Warning: {r2.stderr.strip()}", file=sys.stderr)

        # Step 3: Copy enriched markdown to raw/
        shutil.copy2(enriched_tmp, out_path)
        print(f"Output: raw/{slug}.md")


if __name__ == "__main__":
    main()
```

**Verify (GREEN):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_ingest_doc.py -v
```
Expected: `9 passed`

---

### T09 — Run full unit test suite (all groups green)
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/ -v
```
Expected: `19 passed`, 0 failures.

---

## Group 4: Integration Verification

### T10 — Verify error scenarios (no external services required)
```bash
# File not found
python skills/wiki-ingest/tools/ingest_doc.py nonexistent.pdf
```
Expected: exit 1, stderr contains `Error: file not found: nonexistent.pdf`

```bash
# Missing GEMINI_API_KEY
unset GEMINI_API_KEY && python skills/wiki-ingest/tools/enhance_images.py /dev/null /tmp
```
Expected: exit 1, stderr contains `Error: GEMINI_API_KEY environment variable not set`

```bash
# Output exists, no --force (attention.pdf → raw/attention.md if that exists, else use sentinel)
touch raw/force-test-sentinel.md
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug force-test-sentinel
```
Expected: exit 1, stderr contains `already exists. Use --force to overwrite.`

```bash
rm raw/force-test-sentinel.md
```

---

### T11 — End-to-end pipeline integration test
**Requires:** `mineru` installed + `GEMINI_API_KEY` set.

```bash
export GEMINI_API_KEY=<your-key>
cd /Users/hllj/Projects/long-live-wiki

# Run full pipeline on the existing fixture
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test --force
```

Verify each AC:

```bash
# AC-1.1: exits 0
echo "Exit code: $?"

# AC-1.2: output file exists
ls raw/attention-test.md

# AC-1.3: contains text (expect > 50 lines)
wc -l raw/attention-test.md

# AC-1.4: contains figure descriptions
grep "Figure description (Gemini)" raw/attention-test.md | head -5

# AC-1.5: summary line in stdout (check terminal output for "Images found:")

# AC-2.2: re-run without --force triggers guard
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test
# Expected: exit 1, "already exists"

# AC-4.1: custom slug
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug my-attention --force
ls raw/my-attention.md

# AC-4.2: default slug derived from filename
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --force
ls raw/attention.md

# AC-1.7: wiki-ingest skips Step 0 for plain markdown
# (manual: invoke wiki-ingest on raw/attention.md — confirm no "Step 0" output)
```

Clean up test outputs:
```bash
rm -f raw/attention-test.md raw/my-attention.md
```

---

## Group 5: wiki-ingest SKILL.md update

### T11.5 — Add Step 0 pre-process block to `skills/wiki-ingest/SKILL.md`
**File:** `skills/wiki-ingest/SKILL.md`
**Implements:** FR-6
**Covers:** AC-1.1 – AC-1.7, AC-2.1 – AC-2.2, AC-3.1 – AC-3.2

Insert the following block immediately before the `### 1. Read the source` section:

```markdown
### 0. Pre-process document (binary sources only)

Check the file extension of the source path the user provided.

- If the extension is **`.pdf` or `.docx`**: run Step 0 before anything else.
- If the extension is **`.md`** (or no extension / already markdown): skip to Step 1.

**Running Step 0:**

```bash
export GEMINI_API_KEY=<your-key>
python skills/wiki-ingest/tools/ingest_doc.py <source_path> [--slug <slug>] [--gemini-model <model>]
```

Display the full stdout output (images found, described, failures).

After displaying the summary, ask the user:

> "Pre-processing complete. Proceed with wiki ingest? [y/n]"

- **If yes:** the enriched markdown at `raw/<slug>.md` is now the source for Step 1 onward.
- **If no:** stop here — do not write any wiki pages.
- **If the script exits non-zero (fatal error):** report the error and stop — do not write any wiki pages.
```

**Verify:**
- Invoke wiki-ingest skill pointing at a `.pdf` source → confirm "Step 0: Pre-processing" fires.
- Invoke wiki-ingest skill pointing at a `.md` source → confirm Step 0 is skipped.

---

## Group 6: Commit

### T12 — Stage and commit all changes
```bash
cd /Users/hllj/Projects/long-live-wiki
git add skills/wiki-ingest/ docs/specs/003-doc-ingest-pipeline/
git status
```
Expected: shows `skills/wiki-ingest/tools/` (new files) and `skills/wiki-ingest/SKILL.md` (modified) and `docs/specs/003-doc-ingest-pipeline/` as modified files.

```bash
git commit -m "$(cat <<'EOF'
feat(wiki-ingest): add document ingest pipeline inside skill, integrate Step 0 pre-process

Moves pipeline tools into skills/wiki-ingest/tools/ so the skill is
self-contained. wiki-ingest now detects binary sources (PDF, DOCX) and
runs MinerU + Gemini enrichment as Step 0 before writing any wiki pages.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```
