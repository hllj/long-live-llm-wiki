# Tasks: Document Ingest Pipeline (Feature 003)

**Plan:** [plan.md](plan.md) (spec v3.1.0)
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

Create `skills/wiki-ingest/tools/tests/__init__.py`: empty file.

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
Expected: All packages install. `python -c "import google.genai; print('ok')"` prints `ok`.

---

## Group 1: enhance_images.py (TDD)

### T03 — Write failing tests for `enrich()` and per-image progress output
**File:** `skills/wiki-ingest/tools/tests/test_enhance_images.py`

```python
import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import enhance_images


def test_enrich_inserts_description_after_image(tmp_path):
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


def test_enrich_prints_per_image_progress(tmp_path, capsys):
    """enrich() prints '[Gemini] Describing figure N/M: ...' before each API call."""
    img = tmp_path / "images" / "fig1.png"
    img.parent.mkdir()
    img.write_bytes(b"fake")

    md = "# Doc\n\n![](images/fig1.png)\n"

    with patch.object(enhance_images, "describe_image", return_value="A chart."):
        enhance_images.enrich(md, tmp_path, MagicMock(), "gemini-3.5-flash")

    captured = capsys.readouterr()
    assert "[Gemini] Describing figure 1/1: images/fig1.png" in captured.out
    assert "done" in captured.out


def test_enrich_prints_failed_on_missing_file(tmp_path, capsys):
    """enrich() prints FAILED inline when the image file is absent."""
    (tmp_path / "images").mkdir()
    md = "# Doc\n\n![](images/gone.png)\n"

    enhance_images.enrich(md, tmp_path, MagicMock(), "gemini-3.5-flash")

    captured = capsys.readouterr()
    assert "FAILED" in captured.out
    assert "gone.png" in captured.out


def test_cli_missing_api_key(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n")
    (tmp_path / "images").mkdir()

    env = {"PATH": "/usr/bin:/bin"}
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/enhance_images.py", str(md_file), str(tmp_path / "images")],
        capture_output=True,
        text=True,
        env=env,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )

    assert result.returncode == 1
    assert "GEMINI_API_KEY" in result.stderr


def test_cli_writes_step2_enhanced_by_default(tmp_path):
    """CLI writes step2_enhanced.md sibling when --output is not given."""
    img = tmp_path / "images" / "fig.png"
    img.parent.mkdir()
    img.write_bytes(b"fake")
    md_file = tmp_path / "step1_mineru_raw.md"
    md_file.write_text("# Doc\n\n![](images/fig.png)\n")

    with patch.object(enhance_images, "describe_image", return_value="desc"):
        with patch("sys.argv", ["enhance_images.py", str(md_file), str(tmp_path / "images")]):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}):
                with patch("google.genai.Client"):
                    try:
                        enhance_images.main()
                    except SystemExit:
                        pass

    step2 = tmp_path / "step2_enhanced.md"
    assert step2.exists()
```

**Verify (RED):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_enhance_images.py -v 2>&1 | head -30
```
Expected: `ModuleNotFoundError: No module named 'enhance_images'` — file doesn't exist yet.

---

### T04 — Implement `skills/wiki-ingest/tools/enhance_images.py`
**File:** `skills/wiki-ingest/tools/enhance_images.py`

Implement exactly as shown in plan.md Phase 2. Key requirements:
- `enrich()` prints `[Gemini] Describing figure {idx}/{total}: {img_rel} ... ` (no newline, flushed) before each API call
- Appends `done ({elapsed}s)` or `FAILED ({reason}) ({elapsed}s)` on the same line
- Default output path is `md_path.parent / "step2_enhanced.md"` (not overwriting input)
- Prints `step2 written: <path>` after writing

**Verify (GREEN):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_enhance_images.py -v
```
Expected: `8 passed`

---

## Group 2: doc_to_markdown.py (TDD)

### T05 — Write failing tests for `convert()` [P]
**File:** `skills/wiki-ingest/tools/tests/test_doc_to_markdown.py`

```python
import io
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import doc_to_markdown


def _make_popen_mock(lines: list[str], returncode: int = 0):
    """Helper: mock Popen that yields lines from stdout iterator."""
    mock_proc = MagicMock()
    mock_proc.stdout.__iter__ = MagicMock(return_value=iter(lines))
    mock_proc.poll.return_value = returncode
    mock_proc.returncode = returncode
    mock_proc.wait.return_value = None
    return mock_proc


def test_convert_produces_step1_mineru_raw(tmp_path):
    """convert() copies MinerU output to step1_mineru_raw.md in workdir."""
    nested = tmp_path / "auto"
    nested.mkdir()
    md_file = nested / "paper.md"
    md_file.write_text("# Paper\n")
    (nested / "images").mkdir()

    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock(["Processing...\n"])
        step1, images_dir = doc_to_markdown.convert(Path("fake.pdf"), tmp_path)

    assert step1 == tmp_path / "step1_mineru_raw.md"
    assert step1.exists()
    assert images_dir == tmp_path / "images"


def test_convert_exits_when_mineru_fails(tmp_path):
    """convert() calls sys.exit(1) when MinerU returns non-zero."""
    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock(["error\n"], returncode=1)
        with pytest.raises(SystemExit) as exc:
            doc_to_markdown.convert(Path("fake.pdf"), tmp_path)
    assert exc.value.code == 1


def test_convert_exits_when_no_md_produced(tmp_path):
    """convert() exits 1 when MinerU succeeds but produces no .md file."""
    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock([])
        with pytest.raises(SystemExit) as exc:
            doc_to_markdown.convert(Path("fake.pdf"), tmp_path)
    assert exc.value.code == 1


def test_convert_prefixes_mineru_lines(tmp_path, capsys):
    """convert() prints streamed lines prefixed with '[MinerU] '."""
    nested = tmp_path / "auto"
    nested.mkdir()
    (nested / "out.md").write_text("# x\n")
    (nested / "images").mkdir()

    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock(["page 1\n", "page 2\n"])
        doc_to_markdown.convert(Path("fake.pdf"), tmp_path)

    captured = capsys.readouterr()
    assert "[MinerU] page 1" in captured.out
    assert "[MinerU] page 2" in captured.out


def test_cli_file_not_found():
    """CLI exits 1 with 'Error: file not found' when input path does not exist."""
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/doc_to_markdown.py",
         "nonexistent_file.pdf", "--workdir", "/tmp/nowhere"],
        capture_output=True,
        text=True,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )
    assert result.returncode == 1
    assert "Error: file not found" in result.stderr


def test_cli_requires_workdir():
    """CLI exits non-zero when --workdir is omitted."""
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/doc_to_markdown.py", "raw/attention.pdf"],
        capture_output=True,
        text=True,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )
    assert result.returncode != 0


def test_cli_prints_contract_lines(tmp_path):
    """CLI prints 'markdown:<path>' and 'images:<path>' on success."""
    fake_pdf = tmp_path / "test.pdf"
    fake_pdf.write_bytes(b"%PDF fake")
    nested = tmp_path / "auto"
    nested.mkdir()
    (nested / "test.md").write_text("# Test\n")
    (nested / "images").mkdir()

    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock([])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("sys.argv", ["doc_to_markdown.py", str(fake_pdf), "--workdir", str(tmp_path)]):
                doc_to_markdown.main()

    output = buf.getvalue()
    assert "markdown:" in output
    assert "step1_mineru_raw.md" in output
    assert "images:" in output
```

**Verify (RED):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py -v 2>&1 | head -20
```
Expected: `ModuleNotFoundError: No module named 'doc_to_markdown'`

---

### T06 — Implement `skills/wiki-ingest/tools/doc_to_markdown.py` [P]
**File:** `skills/wiki-ingest/tools/doc_to_markdown.py`

Implement exactly as shown in plan.md Phase 1. Key requirements:
- `subprocess.Popen` (not `subprocess.run`) so MinerU output is streamed line by line
- Daemon heartbeat thread that prints `[MinerU] still running... elapsed: Xs` every 5s of silence
- After MinerU exits, `shutil.copy2` the found `.md` to `workdir/step1_mineru_raw.md`
- Move `images/` to `workdir/images/` if it's nested in a MinerU subdirectory
- `--workdir` is a required argument (replaces old `--outdir`)
- Contract output: `markdown:<workdir>/step1_mineru_raw.md` and `images:<workdir>/images`

**Verify (GREEN):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py -v
```
Expected: `7 passed`

---

## Group 3: ingest_doc.py (TDD)

### T07 — Write failing tests for orchestrator logic
**File:** `skills/wiki-ingest/tools/tests/test_ingest_doc.py`

```python
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

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


def test_parse_tool_output_extracts_contract_lines():
    stdout = "markdown:/tmp/out/step1_mineru_raw.md\nimages:/tmp/out/images\n"
    result = ingest_doc.parse_tool_output(stdout)
    assert result["markdown"] == "/tmp/out/step1_mineru_raw.md"
    assert result["images"] == "/tmp/out/images"


def test_parse_tool_output_skips_mineru_progress_lines():
    stdout = (
        "[MinerU] Processing page 1/15...\n"
        "[MinerU] still running... elapsed: 12s\n"
        "markdown:/tmp/step1_mineru_raw.md\n"
        "images:/tmp/images\n"
        "[MinerU] Done.\n"
    )
    result = ingest_doc.parse_tool_output(stdout)
    assert result["markdown"] == "/tmp/step1_mineru_raw.md"
    assert result["images"] == "/tmp/images"
    assert "MinerU" not in result


def test_parse_tool_output_skips_gemini_progress_lines():
    stdout = (
        "[Gemini] Describing figure 1/5: images/fig.png ... done (1.2s)\n"
        "Images found: 5 | Described: 5 | Failed: 0\n"
        "step2 written: raw/slug/step2_enhanced.md\n"
    )
    result = ingest_doc.parse_tool_output(stdout)
    assert "Images found" not in result
    assert "step2 written" not in result


def test_inspect_workdir_detects_existing_files(tmp_path):
    (tmp_path / "step1_mineru_raw.md").write_text("# x\n")
    (tmp_path / "images").mkdir()
    state = ingest_doc.inspect_workdir(tmp_path)
    assert state["step1"] is True
    assert state["images"] is True
    assert state["step2"] is False


def test_write_log_creates_file(tmp_path):
    ingest_doc.write_log(tmp_path, {"document": "test.pdf", "elapsed_s": "12.3", "exit_code": 0}, force=False)
    log = (tmp_path / "ingest.log").read_text()
    assert "document: test.pdf" in log
    assert "elapsed_s: 12.3" in log
    assert "Run " in log


def test_write_log_appends_on_re_run(tmp_path):
    ingest_doc.write_log(tmp_path, {"exit_code": 0}, force=False)
    ingest_doc.write_log(tmp_path, {"exit_code": 0}, force=False)
    log = (tmp_path / "ingest.log").read_text()
    assert log.count("=== Run") == 2


def test_write_log_overwrites_with_force(tmp_path):
    ingest_doc.write_log(tmp_path, {"exit_code": 0}, force=False)
    ingest_doc.write_log(tmp_path, {"exit_code": 0}, force=True)
    log = (tmp_path / "ingest.log").read_text()
    assert log.count("=== Run") == 1


def test_cli_file_not_found():
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/ingest_doc.py", "no_such_file.pdf"],
        capture_output=True, text=True,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )
    assert result.returncode == 1
    assert "Error: file not found" in result.stderr
```

**Verify (RED):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_ingest_doc.py -v 2>&1 | head -20
```
Expected: `ModuleNotFoundError: No module named 'ingest_doc'`

---

### T08 — Implement `skills/wiki-ingest/tools/ingest_doc.py`
**File:** `skills/wiki-ingest/tools/ingest_doc.py`

Implement exactly as shown in plan.md Phase 3. Key requirements:
- Creates `raw/<slug>/` as a **permanent** workdir (no `tempfile.TemporaryDirectory`)
- If `workdir` exists and `--force` not set: calls `inspect_workdir` + `report_workdir`, prompts user, sets `skip_step1`/`skip_step2` flags appropriately
- Calls sub-tools via `stream_subprocess` (Popen-based) so their output streams live
- `parse_tool_output` skips lines starting with `[` (progress lines)
- Calls `write_log(workdir, entry, args.force)` after promotion
- Promotes `raw/<slug>/step2_enhanced.md` → `raw/<slug>.md` via `shutil.copy2`
- Prints final summary with paths to intermediate folder and final .md

**Verify (GREEN):**
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/test_ingest_doc.py -v
```
Expected: `11 passed`

---

### T09 — Run full unit test suite (all groups green)
```bash
cd /Users/hllj/Projects/long-live-wiki && python -m pytest skills/wiki-ingest/tools/tests/ -v
```
Expected: `26 passed`, 0 failures.

---

## Group 4: Integration Verification

### T10 — Verify error scenarios (no external services required)
```bash
# File not found
python skills/wiki-ingest/tools/ingest_doc.py nonexistent.pdf
```
Expected: exit 1, `Error: file not found: nonexistent.pdf`

```bash
# Missing GEMINI_API_KEY
unset GEMINI_API_KEY && python skills/wiki-ingest/tools/enhance_images.py /dev/null /tmp
```
Expected: exit 1, `Error: GEMINI_API_KEY environment variable not set`

```bash
# doc_to_markdown.py requires --workdir
python skills/wiki-ingest/tools/doc_to_markdown.py raw/attention.pdf
```
Expected: exit non-zero, argparse error about missing `--workdir`

---

### T11 — End-to-end pipeline integration test
**Requires:** `mineru` installed + `GEMINI_API_KEY` set.

```bash
export GEMINI_API_KEY=<your-key>
cd /Users/hllj/Projects/long-live-wiki

python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test --force
```

**Folder structure check (AC-1.4):**
```bash
ls raw/attention-test/
# Expected: step1_mineru_raw.md  images/  step2_enhanced.md  ingest.log

ls raw/attention-test/images/ | head -5
# Expected: extracted image files

ls raw/attention-test.md
# Expected: file exists (AC-1.5)
```

**Content checks:**
```bash
# AC-1.4 step1 contains raw MinerU markdown
wc -l raw/attention-test/step1_mineru_raw.md   # expect > 50 lines

# AC-1.5 final .md contains figure descriptions
grep "Figure description (Gemini)" raw/attention-test.md | head -5

# FR-5.5 ingest.log created and contains run metadata
cat raw/attention-test/ingest.log
# Expected: "=== Run ...", "document: attention.pdf", "elapsed_s: ..."
```

**Idempotency checks (AC-2.1–2.3):**
```bash
# AC-2.1: re-run without --force shows folder inspection report
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test
# Expected: prints "Intermediate folder already exists: raw/attention-test/"
# with ✓ marks for step1, images, step2; prompts "Re-run Step 0 and overwrite? [y/N]"

# AC-2.2: answering 'n' reuses step2 (fast, no MinerU/Gemini calls)
# Answer 'n' at the prompt — should skip to promotion in <1s

# AC-2.3: --force re-runs everything
python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test --force
# Expected: full MinerU + Gemini run, ingest.log still has only 1 entry (overwritten)
cat raw/attention-test/ingest.log
# Expected: only one "=== Run" entry
```

**Partial resume (AC-2.2 edge case):**
```bash
# Simulate step1 present but step2 missing
cp raw/attention-test/step1_mineru_raw.md /tmp/step1_backup.md
rm raw/attention-test/step2_enhanced.md

python skills/wiki-ingest/tools/ingest_doc.py raw/attention.pdf --slug attention-test
# Expected: reports "step2_enhanced.md (missing)", offers "Resume from Gemini only? [Y/n]"
# Answer 'Y' — only Gemini enrichment runs (no MinerU)
```

Clean up:
```bash
rm -rf raw/attention-test/ raw/attention-test.md
```

---

## Group 5: wiki-ingest SKILL.md update

### T11.5 — Add Step 0 pre-process block to `skills/wiki-ingest/SKILL.md`
**File:** `skills/wiki-ingest/SKILL.md`
**Implements:** FR-6

Insert immediately before the `### 1. Read the source` section (exact content in plan.md Phase 4.5):

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

**Verify:**
- Invoke wiki-ingest on a `.pdf` → Step 0 fires, streams output, asks confirmation.
- Invoke wiki-ingest on a `.md` → Step 0 is skipped entirely.

---

## Group 6: Commit

### T12 — Stage and commit all changes
```bash
cd /Users/hllj/Projects/long-live-wiki
git add skills/wiki-ingest/ docs/specs/003-doc-ingest-pipeline/
git status
```
Expected: `skills/wiki-ingest/tools/` (new files), `skills/wiki-ingest/SKILL.md` (modified), `docs/specs/003-doc-ingest-pipeline/` (modified).

```bash
git commit -m "$(cat <<'EOF'
feat(wiki-ingest): add document ingest pipeline with intermediate folder layout and live logging

Implements spec v3.1.0: binary sources (PDF/DOCX) go through MinerU +
Gemini enrichment as Step 0. Each stage writes to raw/<slug>/ so all
intermediate artifacts are inspectable. Sub-steps stream live progress
(per-image [Gemini] lines, heartbeat for MinerU silence) so users are
never waiting in silence. ingest.log records every run.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```
