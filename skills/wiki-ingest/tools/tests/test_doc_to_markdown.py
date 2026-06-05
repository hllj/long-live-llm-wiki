import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import doc_to_markdown

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


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
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1
    assert "Error: file not found" in result.stderr


def test_cli_requires_workdir():
    """CLI exits non-zero when --workdir is omitted."""
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/doc_to_markdown.py", "raw/attention.pdf"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
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


# ── helper ────────────────────────────────────────────────────────────────────

def _make_server_proc(poll_value=None):
    """MagicMock Popen-like object: poll() returns poll_value, pid=12345."""
    proc = MagicMock()
    proc.poll.return_value = poll_value
    proc.pid = 12345
    return proc


# ── ensure_server: server already running ─────────────────────────────────────

def test_ensure_server_reuses_running_server():
    """When /health returns 200 on first candidate port, no new server is started (AC-1.1)."""
    with patch("doc_to_markdown._is_mineru_healthy", return_value=True) as mock_healthy, \
         patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        port = doc_to_markdown.ensure_server()

    assert port == 8765
    mock_popen.assert_not_called()


# ── ensure_server: auto-start ─────────────────────────────────────────────────

def test_ensure_server_starts_server_when_none_running():
    """When no server is running and port is free, Popen is called for mineru-api (AC-2.1)."""
    with patch("doc_to_markdown._CANDIDATE_PORTS", [8765]), \
         patch("doc_to_markdown._is_mineru_healthy", side_effect=[False, True]), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("doc_to_markdown._pid_file_path", return_value=MagicMock(write_text=MagicMock())), \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen",
               return_value=_make_server_proc(None)) as mock_popen, \
         patch("doc_to_markdown.time.sleep"):

        port = doc_to_markdown.ensure_server()

    assert port == 8765
    mock_popen.assert_called_once()
    cmd = mock_popen.call_args[0][0]
    assert cmd[0] == "mineru-api"
    assert "--enable-vlm-preload" in cmd
    assert "True" in cmd


def test_ensure_server_prints_startup_message(capsys):
    """ensure_server() prints the AC-2.4 one-line message when starting a new server."""
    with patch("doc_to_markdown._CANDIDATE_PORTS", [8765]), \
         patch("doc_to_markdown._is_mineru_healthy", side_effect=[False, True]), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("doc_to_markdown._pid_file_path", return_value=MagicMock(write_text=MagicMock())), \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen", return_value=_make_server_proc(None)), \
         patch("doc_to_markdown.time.sleep"):

        doc_to_markdown.ensure_server()

    assert "Starting persistent server on port 8765" in capsys.readouterr().out


# ── ensure_server: fallback paths ─────────────────────────────────────────────

def test_ensure_server_fallback_binary_not_found(capsys):
    """When mineru-api is not in PATH, returns None with AC-3.1 warning."""
    with patch("doc_to_markdown._CANDIDATE_PORTS", [8765]), \
         patch("doc_to_markdown._is_mineru_healthy", return_value=False), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen", side_effect=FileNotFoundError):

        port = doc_to_markdown.ensure_server()

    assert port is None
    out = capsys.readouterr().out
    assert "mineru-api not found" in out
    assert "local mode" in out


def test_ensure_server_fallback_timeout(capsys):
    """When server never becomes healthy within timeout, returns None with AC-3.2 warning."""
    with patch("doc_to_markdown._CANDIDATE_PORTS", [8765]), \
         patch("doc_to_markdown._is_mineru_healthy", return_value=False), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("doc_to_markdown._pid_file_path", return_value=MagicMock(write_text=MagicMock())), \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen", return_value=_make_server_proc(None)), \
         patch("doc_to_markdown._STARTUP_TIMEOUT", 0):

        port = doc_to_markdown.ensure_server()

    assert port is None
    assert "server did not become ready" in capsys.readouterr().out


def test_ensure_server_fallback_all_ports_occupied(capsys):
    """When all candidate ports are occupied by non-MinerU, returns None with AC-3.3 warning."""
    with patch("doc_to_markdown._is_mineru_healthy", return_value=False), \
         patch("doc_to_markdown._port_is_free", return_value=False):

        port = doc_to_markdown.ensure_server()

    assert port is None
    assert "no available port" in capsys.readouterr().out


# ── ensure_server: env override ───────────────────────────────────────────────

def test_ensure_server_env_port_override(monkeypatch):
    """MINERU_API_PORT env var causes ensure_server to check only that port (FR-7)."""
    monkeypatch.setenv("MINERU_API_PORT", "9999")
    with patch("doc_to_markdown._is_mineru_healthy", return_value=True) as mock_healthy:
        port = doc_to_markdown.ensure_server()
    assert port == 9999
    mock_healthy.assert_called_once_with(9999)


# ── convert: server delegation ────────────────────────────────────────────────

def test_convert_uses_api_url_when_server_available(tmp_path):
    """When ensure_server returns a port, mineru CLI is called with --api-url (FR-5)."""
    nested = tmp_path / "auto"
    nested.mkdir()
    (nested / "paper.md").write_text("# Paper\n")
    (nested / "images").mkdir()

    with patch("doc_to_markdown.ensure_server", return_value=8765), \
         patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock(["line\n"])
        doc_to_markdown.convert(Path("fake.pdf"), tmp_path)

    cmd = mock_popen.call_args[0][0]
    assert "--api-url" in cmd
    assert "http://127.0.0.1:8765" in cmd


def test_convert_local_mode_when_server_unavailable(tmp_path):
    """When ensure_server returns None, mineru CLI is called without --api-url (FR-6)."""
    nested = tmp_path / "auto"
    nested.mkdir()
    (nested / "paper.md").write_text("# Paper\n")
    (nested / "images").mkdir()

    with patch("doc_to_markdown.ensure_server", return_value=None), \
         patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        mock_popen.return_value = _make_popen_mock(["line\n"])
        doc_to_markdown.convert(Path("fake.pdf"), tmp_path)

    cmd = mock_popen.call_args[0][0]
    assert "--api-url" not in cmd
