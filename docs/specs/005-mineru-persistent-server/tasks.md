# Tasks: MinerU Persistent Server (005)

**Spec:** `docs/specs/005-mineru-persistent-server/spec.md`  
**Plan:** `docs/specs/005-mineru-persistent-server/plan.md`  
**Branch:** `005-mineru-persistent-server`

---

## Tasks

---

### [T1] Create feature branch

```bash
git checkout -b 005-mineru-persistent-server
```

**Verification:** `git branch --show-current` → `005-mineru-persistent-server`

---

### [T2] Doc-first commit

Stage and commit the three spec artifacts created so far:

```bash
git add docs/specs/005-mineru-persistent-server/design.md \
        docs/specs/005-mineru-persistent-server/spec.md \
        docs/specs/005-mineru-persistent-server/plan.md \
        docs/specs/005-mineru-persistent-server/tasks.md
git commit -m "docs(005): add spec, plan, design, tasks for MinerU persistent server"
```

**Verification:** `git log --oneline -1` shows the commit.

---

### [T3] Add `mock_open` to test file imports

In `skills/wiki-ingest/tools/tests/test_doc_to_markdown.py`, change line 6 from:

```python
from unittest.mock import MagicMock, patch
```

to:

```python
from unittest.mock import MagicMock, mock_open, patch
```

**Verification:** `python -c "from unittest.mock import MagicMock, mock_open, patch"` exits 0.

---

### [T4] Write failing tests for `ensure_server()` (RED)

Append the following to the end of `skills/wiki-ingest/tools/tests/test_doc_to_markdown.py`:

```python
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
```

**Verification:**

```bash
cd /Users/hllj/Projects/long-live-wiki
python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py \
  -k "ensure_server" -v 2>&1 | tail -20
```

Expected: 7 failures — `AttributeError: module 'doc_to_markdown' has no attribute 'ensure_server'` (or `_is_mineru_healthy`, `_port_is_free`).

---

### [T5] Verify RED for `ensure_server()` tests

```bash
cd /Users/hllj/Projects/long-live-wiki
python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py \
  -k "ensure_server" -v 2>&1 | tail -15
```

Expected output contains: `FAILED` for all 7 new tests, `AttributeError` or `ERROR`.

---

### [T6] Add imports, constants, and 4 helper functions to `doc_to_markdown.py`

In `skills/wiki-ingest/tools/doc_to_markdown.py`:

**Step 1 — add imports** (after the existing `import threading`):

```python
import os
import socket
import urllib.error
import urllib.request
```

**Step 2 — add constants and helpers** (after the imports block, before the `convert` function):

```python
_CANDIDATE_PORTS = [8765, 8766, 8767, 8768]
_STARTUP_TIMEOUT = 90   # seconds
_POLL_INTERVAL = 2      # seconds


def _get_candidate_ports() -> list[int]:
    """Return candidate ports to check/use, respecting MINERU_API_PORT env override (FR-7)."""
    env = os.environ.get("MINERU_API_PORT", "")
    try:
        p = int(env)
        if 1 <= p <= 65535:
            return [p]
    except (ValueError, TypeError):
        pass
    return _CANDIDATE_PORTS


def _pid_file_path() -> Path:
    """Return PID file path, respecting MINERU_API_PID_FILE env override (FR-7)."""
    env = os.environ.get("MINERU_API_PID_FILE", "")
    return Path(env) if env else Path.home() / ".mineru-api.pid"


def _is_mineru_healthy(port: int) -> bool:
    """Return True iff GET /health on localhost:port responds HTTP 200 (AC-4.3)."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=2
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


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

**Verification:**

```bash
cd /Users/hllj/Projects/long-live-wiki
python -c "
import sys; sys.path.insert(0, 'skills/wiki-ingest/tools')
import doc_to_markdown as d
print(d._CANDIDATE_PORTS)
print(d._is_mineru_healthy(1))   # should print False (nothing on port 1)
print(d._port_is_free(1))        # should print True
print(d._get_candidate_ports())
print(d._pid_file_path())
"
```

Expected: `[8765, 8766, 8767, 8768]`, `False`, `True`, `[8765, 8766, 8767, 8768]`, `~/.mineru-api.pid` path.

---

### [T7] Implement `ensure_server()` in `doc_to_markdown.py`

Add the following function directly after `_port_is_free()` in `skills/wiki-ingest/tools/doc_to_markdown.py`:

```python
def ensure_server() -> int | None:
    """Locate or start a mineru-api server. Returns the healthy port or None (local mode).

    Implements FR-1 (detection), FR-2 (auto-start), FR-3 (timeout), FR-4 (state
    files), FR-6 (fallback), FR-7 (env overrides).
    """
    ports = _get_candidate_ports()

    # FR-1: check if a MinerU server is already running on any candidate port
    for port in ports:
        if _is_mineru_healthy(port):
            return port

    # FR-2: no running server found — start one on the first free candidate port
    for port in ports:
        if not _port_is_free(port):
            continue  # occupied by a non-MinerU process

        log_fh = subprocess.DEVNULL
        try:
            log_fh = open(Path.home() / ".mineru-api.log", "a")  # FR-4
        except OSError:
            print(
                "[MinerU] WARNING: could not open ~/.mineru-api.log;"
                " server output discarded",
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
            print(  # AC-3.1
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

        print(  # AC-3.2
            "[MinerU] WARNING: server did not become ready;"
            " falling back to local mode",
            flush=True,
        )
        return None

    # AC-3.3: all candidate ports are occupied by non-MinerU processes
    print(
        "[MinerU] WARNING: no available port for mineru-api; running in local mode",
        flush=True,
    )
    return None
```

**Verification (syntax only):**

```bash
cd /Users/hllj/Projects/long-live-wiki
python -c "
import sys; sys.path.insert(0, 'skills/wiki-ingest/tools')
import doc_to_markdown as d
print(callable(d.ensure_server))
"
```

Expected: `True`

---

### [T8] Run `ensure_server()` tests — verify GREEN

```bash
cd /Users/hllj/Projects/long-live-wiki
python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py \
  -k "ensure_server" -v 2>&1 | tail -15
```

Expected: all 7 `ensure_server` tests pass. Example output:

```
PASSED test_ensure_server_reuses_running_server
PASSED test_ensure_server_starts_server_when_none_running
PASSED test_ensure_server_prints_startup_message
PASSED test_ensure_server_fallback_binary_not_found
PASSED test_ensure_server_fallback_timeout
PASSED test_ensure_server_fallback_all_ports_occupied
PASSED test_ensure_server_env_port_override
7 passed
```

---

### [T9] Write failing tests for `convert()` delegation (RED)

Append the following two tests to the end of `skills/wiki-ingest/tools/tests/test_doc_to_markdown.py`:

```python
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
```

**Verification:**

```bash
cd /Users/hllj/Projects/long-live-wiki
python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py \
  -k "api_url" -v 2>&1 | tail -10
```

Expected: 2 failures — `AssertionError` because `convert()` does not yet pass `--api-url`.

---

### [T10] Verify RED for `convert()` delegation tests

```bash
cd /Users/hllj/Projects/long-live-wiki
python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py \
  -k "api_url" -v 2>&1 | tail -10
```

Expected output: `FAILED test_convert_uses_api_url_when_server_available` — `AssertionError`.

---

### [T11] Update `convert()` to call `ensure_server()` and add `--api-url`

Replace the entire `convert()` function in `skills/wiki-ingest/tools/doc_to_markdown.py` with:

```python
def convert(doc_path: Path, workdir: Path) -> tuple[Path, Path]:
    """Run MinerU, stream output live, rename result to step1_mineru_raw.md.

    Returns (step1_path, images_dir) where both are inside workdir.
    """
    workdir.mkdir(parents=True, exist_ok=True)

    port = ensure_server()  # FR-1/FR-2: locate or start persistent server

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

---

### [T12] Run ALL tests — verify GREEN (including 8 existing tests)

```bash
cd /Users/hllj/Projects/long-live-wiki
python -m pytest skills/wiki-ingest/tools/tests/test_doc_to_markdown.py -v 2>&1 | tail -25
```

Expected: all 17 tests pass (8 existing + 7 `ensure_server` + 2 `convert` delegation).

```
PASSED test_convert_produces_step1_mineru_raw
PASSED test_convert_exits_when_mineru_fails
PASSED test_convert_exits_when_no_md_produced
PASSED test_convert_prefixes_mineru_lines
PASSED test_convert_moves_images_to_workdir_root
PASSED test_cli_file_not_found
PASSED test_cli_requires_workdir
PASSED test_cli_prints_contract_lines
PASSED test_ensure_server_reuses_running_server
PASSED test_ensure_server_starts_server_when_none_running
PASSED test_ensure_server_prints_startup_message
PASSED test_ensure_server_fallback_binary_not_found
PASSED test_ensure_server_fallback_timeout
PASSED test_ensure_server_fallback_all_ports_occupied
PASSED test_ensure_server_env_port_override
PASSED test_convert_uses_api_url_when_server_available
PASSED test_convert_local_mode_when_server_unavailable
17 passed
```

---

### [T13] Update `SKILL.md` Step 0 section

In `skills/wiki-ingest/SKILL.md`, after the final summary code block inside "Running Step 0" and before the "**If the intermediate folder**" paragraph, insert:

```markdown
> MinerU runs as a background server (auto-started on first use, port 8765); model weights load once per machine session, making subsequent ingests ~60s faster on Apple M1.
```

The section should look like this after the edit:

```markdown
- A final summary block:
  ```
  Step 0 complete — see terminal output above for image summary
  Intermediate artifacts saved to: raw/<slug>/
  Final enriched markdown:         raw/<slug>.md
  ```

> MinerU runs as a background server (auto-started on first use, port 8765); model weights load once per machine session, making subsequent ingests ~60s faster on Apple M1.

**If the intermediate folder `raw/<slug>/` already exists**, the script shows...
```

**Verification:**

```bash
grep "background server" /Users/hllj/Projects/long-live-wiki/skills/wiki-ingest/SKILL.md
```

Expected: the line is present.

---

### [T14] Final implementation commit

```bash
cd /Users/hllj/Projects/long-live-wiki
git add skills/wiki-ingest/tools/doc_to_markdown.py \
        skills/wiki-ingest/tools/tests/test_doc_to_markdown.py \
        skills/wiki-ingest/SKILL.md
git commit -m "$(cat <<'EOF'
feat(005): add MinerU persistent server to eliminate per-ingest model reload

Starts mineru-api --enable-vlm-preload once per machine session; subsequent
wiki-ingest PDF calls skip the 30-60s VLM load and delegate via --api-url.
Falls back to local mode if server is unavailable. All 17 tests pass.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

**Verification:** `git log --oneline -2` shows both commits on branch `005-mineru-persistent-server`.
