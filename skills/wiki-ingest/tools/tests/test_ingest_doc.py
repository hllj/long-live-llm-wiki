import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ingest_doc


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

def test_slugify_lowercases_and_hyphenates():
    assert ingest_doc.slugify("My Paper Title") == "my-paper-title"


def test_slugify_replaces_underscores():
    assert ingest_doc.slugify("attention_is_all_you_need") == "attention-is-all-you-need"


def test_slugify_strips_leading_trailing_hyphens():
    assert ingest_doc.slugify("--hello--") == "hello"


def test_slugify_collapses_multiple_separators():
    assert ingest_doc.slugify("hello   world") == "hello-world"


# ---------------------------------------------------------------------------
# parse_tool_output
# ---------------------------------------------------------------------------

def test_parse_tool_output_extracts_contract_lines():
    stdout = "markdown:raw/slug/step1_mineru_raw.md\nimages:raw/slug/images\n"
    result = ingest_doc.parse_tool_output(stdout)
    assert result["markdown"] == "raw/slug/step1_mineru_raw.md"
    assert result["images"] == "raw/slug/images"


def test_parse_tool_output_skips_mineru_progress_lines():
    stdout = (
        "[MinerU] Processing page 1/15...\n"
        "[MinerU] still running... elapsed: 12s\n"
        "markdown:raw/slug/step1_mineru_raw.md\n"
        "images:raw/slug/images\n"
        "[MinerU] Done.\n"
    )
    result = ingest_doc.parse_tool_output(stdout)
    assert result["markdown"] == "raw/slug/step1_mineru_raw.md"
    assert result["images"] == "raw/slug/images"
    assert not any(k.startswith("[") for k in result)


def test_parse_tool_output_skips_gemini_progress_lines():
    stdout = (
        "[Gemini] Describing figure 1/5: images/fig.png ... done (1.2s)\n"
        "Images found: 5 | Described: 5 | Failed: 0\n"
        "step2 written: raw/slug/step2_enhanced.md\n"
    )
    result = ingest_doc.parse_tool_output(stdout)
    # These lines contain ':' but are not key:value contract lines
    assert "Images found" not in result
    assert "step2 written" not in result


# ---------------------------------------------------------------------------
# inspect_workdir
# ---------------------------------------------------------------------------

def test_inspect_workdir_all_missing(tmp_path):
    state = ingest_doc.inspect_workdir(tmp_path)
    assert state == {"step1": False, "images": False, "step2": False}


def test_inspect_workdir_step1_and_images_present(tmp_path):
    (tmp_path / "step1_mineru_raw.md").write_text("# x\n")
    (tmp_path / "images").mkdir()
    state = ingest_doc.inspect_workdir(tmp_path)
    assert state["step1"] is True
    assert state["images"] is True
    assert state["step2"] is False


def test_inspect_workdir_all_present(tmp_path):
    (tmp_path / "step1_mineru_raw.md").write_text("# x\n")
    (tmp_path / "images").mkdir()
    (tmp_path / "step2_enhanced.md").write_text("# x\n")
    state = ingest_doc.inspect_workdir(tmp_path)
    assert all(state.values())


# ---------------------------------------------------------------------------
# write_log
# ---------------------------------------------------------------------------

def test_write_log_creates_file_with_metadata(tmp_path):
    ingest_doc.write_log(tmp_path, {"document": "test.pdf", "elapsed_s": "12.3", "exit_code": 0}, force=False)
    log = (tmp_path / "ingest.log").read_text()
    assert "document: test.pdf" in log
    assert "elapsed_s: 12.3" in log
    assert "=== Run " in log


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_file_not_found():
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/ingest_doc.py", "no_such_file.pdf"],
        capture_output=True,
        text=True,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )
    assert result.returncode == 1
    assert "Error: file not found" in result.stderr
