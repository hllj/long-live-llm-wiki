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

    import importlib
    import io
    from contextlib import redirect_stdout

    doc_to_markdown_mod = importlib.import_module("doc_to_markdown")

    with patch("doc_to_markdown.convert", return_value=(md_file, nested / "images")):
        with patch("sys.argv", ["doc_to_markdown.py", str(fake_pdf)]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                doc_to_markdown_mod.main()
    output = buf.getvalue()
    assert f"markdown:{md_file}" in output
    assert f"images:{nested / 'images'}" in output
