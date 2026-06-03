import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import doc_to_markdown


def _make_popen_mock(lines: list[str], returncode: int = 0):
    """Return a mock Popen object that yields lines and has the given returncode."""
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
        mock_popen.return_value = _make_popen_mock(["error output\n"], returncode=1)
        with pytest.raises(SystemExit) as exc:
            doc_to_markdown.convert(Path("fake.pdf"), tmp_path)
    assert exc.value.code == 1


def test_convert_exits_when_no_md_produced(tmp_path):
    """convert() calls sys.exit(1) when MinerU succeeds but produces no .md file."""
    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock([])
        with pytest.raises(SystemExit) as exc:
            doc_to_markdown.convert(Path("fake.pdf"), tmp_path)
    assert exc.value.code == 1


def test_convert_prefixes_mineru_lines(tmp_path, capsys):
    """convert() prints each MinerU stdout line prefixed with '[MinerU] '."""
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


def test_convert_moves_images_to_workdir_root(tmp_path):
    """convert() ensures images/ is at workdir/images/, not nested inside a subdir."""
    nested = tmp_path / "subdir"
    nested.mkdir()
    (nested / "out.md").write_text("# x\n")
    img_dir = nested / "images"
    img_dir.mkdir()
    (img_dir / "fig.png").write_bytes(b"fake")

    with patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock([])
        _, images_dir = doc_to_markdown.convert(Path("fake.pdf"), tmp_path)

    assert images_dir == tmp_path / "images"
    assert (tmp_path / "images" / "fig.png").exists()


def test_cli_file_not_found():
    """CLI exits 1 with 'Error: file not found' when input path does not exist."""
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/doc_to_markdown.py",
         "nonexistent_file.pdf", "--workdir", "/tmp/test_workdir_wd"],
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
    """CLI prints 'markdown:<path>' and 'images:<path>' contract lines on success."""
    fake_pdf = tmp_path / "test.pdf"
    fake_pdf.write_bytes(b"%PDF fake")
    step1 = tmp_path / "step1_mineru_raw.md"
    images = tmp_path / "images"

    buf = io.StringIO()
    with patch("doc_to_markdown.convert", return_value=(step1, images)), \
         patch("sys.argv", ["doc_to_markdown.py", str(fake_pdf), "--workdir", str(tmp_path)]), \
         redirect_stdout(buf):
        doc_to_markdown.main()

    output = buf.getvalue()
    assert f"markdown:{step1}" in output
    assert f"images:{images}" in output
    assert "step1_mineru_raw.md" in output
