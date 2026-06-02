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
