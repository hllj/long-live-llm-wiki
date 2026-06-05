# Implementation Plan: MinerU Persistent Server (005)

**Spec:** `docs/specs/005-mineru-persistent-server/spec.md`  
**Branch:** `005-mineru-persistent-server`

---

## Goal

Add `ensure_server()` to `doc_to_markdown.py` so that every `convert()` call reuses a warm `mineru-api` server instead of reloading the VLM model each time. Two files change: `doc_to_markdown.py` and `SKILL.md`.

---

## Architecture

```
convert(doc_path, workdir)
    │
    ├── ensure_server() → int | None
    │       │
    │       ├── _is_mineru_healthy(port) → bool    # HTTP 200 check on /health
    │       ├── _port_is_free(port) → bool          # TCP connect probe
    │       └── subprocess.Popen(["mineru-api", ...]) → started in background
    │
    └── subprocess.Popen(["mineru", "--api-url", ..., "-p", ...]) if port else
        subprocess.Popen(["mineru", "-p", ...])   ← local mode (unchanged)
```

Internal contract: `ensure_server()` returns the healthy port (`int`) or `None` (local mode). `convert()` branches on this value only.

---

## Files Changed

| File | Change |
|---|---|
| `skills/wiki-ingest/tools/doc_to_markdown.py` | Add 5 helpers + `ensure_server()`; update `convert()` |
| `skills/wiki-ingest/tools/tests/test_doc_to_markdown.py` | Add 9 new test cases |
| `skills/wiki-ingest/SKILL.md` | One sentence in Step 0 section |

---

## Phase 1 — Add server management to `doc_to_markdown.py`

### 1a. New imports and constants

Add to the top of `doc_to_markdown.py`, after the existing imports:

```python
import os
import socket
import urllib.error
import urllib.request

_CANDIDATE_PORTS = [8765, 8766, 8767, 8768]
_STARTUP_TIMEOUT = 90   # seconds (FR-3)
_POLL_INTERVAL = 2      # seconds (FR-3)
```

### 1b. `_get_candidate_ports()`

```python
def _get_candidate_ports() -> list[int]:
    """Return candidate ports, respecting MINERU_API_PORT env override (FR-7)."""
    env = os.environ.get("MINERU_API_PORT", "")
    try:
        p = int(env)
        if 1 <= p <= 65535:
            return [p]
    except (ValueError, TypeError):
        pass
    return _CANDIDATE_PORTS
```

### 1c. `_pid_file_path()`

```python
def _pid_file_path() -> Path:
    """Return PID file path, respecting MINERU_API_PID_FILE env override (FR-7)."""
    env = os.environ.get("MINERU_API_PID_FILE", "")
    return Path(env) if env else Path.home() / ".mineru-api.pid"
```

### 1d. `_is_mineru_healthy(port)`

```python
def _is_mineru_healthy(port: int) -> bool:
    """Return True iff /health on localhost:port responds HTTP 200 (AC-4.3)."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=2
        ) as resp:
            return resp.status == 200
    except Exception:
        return False
```

### 1e. `_port_is_free(port)`

```python
def _port_is_free(port: int) -> bool:
    """Return True iff nothing is listening on localhost:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            return False
        except (ConnectionRefusedError, OSError):
            return True
```

### 1f. `ensure_server()`

```python
def ensure_server() -> int | None:
    """Locate or start a mineru-api server. Returns healthy port or None (local mode).

    Implements FR-1 (detection), FR-2 (auto-start), FR-3 (timeout), FR-4 (state
    files), FR-6 (fallback), FR-7 (env overrides).
    """
    ports = _get_candidate_ports()

    # FR-1: check if already running on any candidate port
    for port in ports:
        if _is_mineru_healthy(port):
            return port

    # FR-2: find a free port and start the server
    for port in ports:
        if not _port_is_free(port):
            continue  # occupied by non-MinerU process (AC-4.2)

        log_fh = subprocess.DEVNULL
        try:
            log_fh = open(Path.home() / ".mineru-api.log", "a")  # FR-4
        except OSError:
            print(
                "[MinerU] WARNING: could not open ~/.mineru-api.log; server output discarded",
                flush=True,
            )

        print(
            f"[MinerU] Starting persistent server on port {port}"
            " (first use — loading model)...",  # AC-2.4
            flush=True,
        )

        try:
            proc = subprocess.Popen(
                [
                    "mineru-api",
                    "--host", "127.0.0.1",
                    "--port", str(port),
                    "--enable-vlm-preload", "True",
                ],
                stdout=log_fh,
                stderr=log_fh,
            )
        except FileNotFoundError:
            # AC-3.1
            print(
                "[MinerU] WARNING: mineru-api not found;"
                " running in local mode (model loads each run)",
                flush=True,
            )
            return None

        # FR-4: write informational PID file
        try:
            _pid_file_path().write_text(str(proc.pid))
        except OSError:
            pass

        # FR-3: poll until healthy or timeout
        deadline = time.time() + _STARTUP_TIMEOUT
        while time.time() < deadline:
            if proc.poll() is not None:
                break  # process exited unexpectedly
            if _is_mineru_healthy(port):
                return port
            time.sleep(_POLL_INTERVAL)

        # AC-3.2
        print(
            "[MinerU] WARNING: server did not become ready; falling back to local mode",
            flush=True,
        )
        return None

    # AC-3.3: all candidate ports occupied
    print(
        "[MinerU] WARNING: no available port for mineru-api; running in local mode",
        flush=True,
    )
    return None
```

---

## Phase 2 — Update `convert()` in `doc_to_markdown.py`

Replace the existing `proc = subprocess.Popen(["mineru", ...])` line inside `convert()` with:

```python
def convert(doc_path: Path, workdir: Path) -> tuple[Path, Path]:
    workdir.mkdir(parents=True, exist_ok=True)

    port = ensure_server()  # NEW: FR-1/FR-2

    # FR-5: delegate to server when available; FR-6: local mode when port is None
    if port is not None:
        cmd = [
            "mineru", "--api-url", f"http://127.0.0.1:{port}",
            "-p", str(doc_path), "-o", str(workdir),
        ]
    else:
        cmd = ["mineru", "-p", str(doc_path), "-o", str(workdir)]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # --- remainder of convert() is unchanged from pre-005 ---
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

    md_files = sorted(
        f for f in workdir.rglob("*.md")
        if f.name not in ("step1_mineru_raw.md", "step2_enhanced.md")
    )
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
    elif not target_images.exists():
        target_images.mkdir()

    return step1_path, target_images
```

> **Existing-test compatibility:** When tests patch `doc_to_markdown.subprocess.Popen`, `ensure_server()` calls it first (for `mineru-api`). The mock's `poll()` returns a non-None value immediately (see `_make_popen_mock`), so `ensure_server()` exits the polling loop on the first iteration without sleeping, prints the fallback warning, and returns `None`. `convert()` then calls `Popen` again for `mineru` — gets the same mock — and proceeds identically to pre-005. No existing test assertions are invalidated.

---

## Phase 3 — New tests in `test_doc_to_markdown.py`

Add the following test cases. Each mocks at the boundary closest to what it's testing.

```python
# ── helpers ──────────────────────────────────────────────────────────────────

def _make_server_popen_mock(poll_sequence: list):
    """Popen mock for mineru-api: poll() cycles through poll_sequence values."""
    mock_proc = MagicMock()
    mock_proc.poll.side_effect = poll_sequence
    mock_proc.pid = 12345
    return mock_proc


# ── ensure_server: server already running ─────────────────────────────────────

def test_ensure_server_reuses_running_server():
    """When /health returns 200 on the default port, no new server is started."""
    with patch("doc_to_markdown._is_mineru_healthy", return_value=True) as mock_healthy, \
         patch("doc_to_markdown.subprocess.Popen") as mock_popen:
        port = doc_to_markdown.ensure_server()

    assert port == 8765
    mock_popen.assert_not_called()


# ── ensure_server: starts server when none running ────────────────────────────

def test_ensure_server_starts_server_when_none_running():
    """When no server is running and port is free, Popen is called for mineru-api."""
    poll_values = [None, None, None]  # process stays alive during health polls

    with patch("doc_to_markdown._is_mineru_healthy", side_effect=[False, True]), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("doc_to_markdown._pid_file_path") as mock_pid, \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen",
               return_value=_make_server_popen_mock([None, None])) as mock_popen, \
         patch("doc_to_markdown.time.sleep"):

        mock_pid.return_value = MagicMock(write_text=MagicMock())
        port = doc_to_markdown.ensure_server()

    assert port == 8765
    mock_popen.assert_called_once()
    called_cmd = mock_popen.call_args[0][0]
    assert called_cmd[0] == "mineru-api"
    assert "--enable-vlm-preload" in called_cmd
    assert "True" in called_cmd


def test_ensure_server_returns_port_on_healthy(capsys):
    """ensure_server() prints the startup message and returns the port."""
    with patch("doc_to_markdown._is_mineru_healthy", side_effect=[False, True]), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("doc_to_markdown._pid_file_path", return_value=MagicMock(write_text=MagicMock())), \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen",
               return_value=_make_server_popen_mock([None])), \
         patch("doc_to_markdown.time.sleep"):

        port = doc_to_markdown.ensure_server()

    assert port == 8765
    out = capsys.readouterr().out
    assert "Starting persistent server on port 8765" in out


# ── ensure_server: fallback paths ─────────────────────────────────────────────

def test_ensure_server_fallback_binary_not_found(capsys):
    """When mineru-api is not in PATH, ensure_server returns None with AC-3.1 warning."""
    with patch("doc_to_markdown._is_mineru_healthy", return_value=False), \
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
    with patch("doc_to_markdown._is_mineru_healthy", return_value=False), \
         patch("doc_to_markdown._port_is_free", return_value=True), \
         patch("doc_to_markdown._pid_file_path", return_value=MagicMock(write_text=MagicMock())), \
         patch("builtins.open", mock_open()), \
         patch("doc_to_markdown.subprocess.Popen",
               return_value=_make_server_popen_mock([None])), \
         patch("doc_to_markdown.time.sleep"), \
         patch("doc_to_markdown.time.time", side_effect=[0, 0, 200]):
        # time.time: first call sets start, second sets deadline check (0 < 90 → True),
        # third returns 200 (> 90 → deadline exceeded)

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
    """MINERU_API_PORT env var causes ensure_server to use only that port."""
    monkeypatch.setenv("MINERU_API_PORT", "9999")
    with patch("doc_to_markdown._is_mineru_healthy", return_value=True) as mock_healthy:
        port = doc_to_markdown.ensure_server()
    assert port == 9999
    mock_healthy.assert_called_once_with(9999)


# ── convert: API URL flag ──────────────────────────────────────────────────────

def test_convert_uses_api_url_when_server_available(tmp_path):
    """When ensure_server returns a port, mineru is called with --api-url (FR-5)."""
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
    """When ensure_server returns None, mineru is called without --api-url (FR-6)."""
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
```

Add `from unittest.mock import mock_open` to the imports at the top of the test file.

---

## Phase 4 — Update `SKILL.md`

In `skills/wiki-ingest/SKILL.md`, append one sentence to the end of the "Running Step 0" subsection (after the `[MinerU]` lines description, before the "If the intermediate folder" block):

```markdown
> MinerU runs as a background server (auto-started on first use, port 8765); model weights load once per machine session, making subsequent ingests ~60s faster on Apple M1.
```

---

## Self-Review

**Spec coverage:**

| FR | Phase |
|---|---|
| FR-1 (detection) | Phase 1f: `ensure_server()` first loop |
| FR-2 (auto-start) | Phase 1f: `ensure_server()` second loop |
| FR-3 (timeout) | Phase 1f: deadline + poll loop |
| FR-4 (state files) | Phase 1f: PID write + log redirect |
| FR-5 (delegation) | Phase 2: `--api-url` in cmd |
| FR-6 (fallback) | Phase 2: `port is None` branch |
| FR-7 (env overrides) | Phase 1b + 1c: `_get_candidate_ports()`, `_pid_file_path()` |
| FR-8 (SKILL.md) | Phase 4 |

**Placeholder scan:** No TBDs, no "handle edge cases", all code is complete. ✓

**Type consistency:** `ensure_server() → int | None`; `convert()` receives it and branches on `None`. ✓

**NFR-2 (existing tests pass):** `ensure_server()` uses `poll() is not None` as its first loop check — when tests supply a mock with `poll.return_value = 0`, it breaks immediately without sleeping and returns `None`. `convert()` then runs in local mode, identical to pre-005. No existing assertions are invalidated. ✓
