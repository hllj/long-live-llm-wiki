# Design: MinerU Persistent Server (005)

**Status:** Draft — pending sdd-specify  
**Date:** 2026-06-05  
**Platform:** macOS / Apple M1 (arm64)

---

## Problem

Every `wiki-ingest` call that processes a PDF spawns a fresh `mineru` subprocess. MinerU's `hybrid-auto-engine` backend loads its VLM weights from disk on each invocation — adding 30–60 seconds of dead overhead before any actual parsing begins. On Apple M1 this load happens over every ingest, making even short PDFs feel slow.

---

## Solution

MinerU 3.2.2 ships `mineru-api`, a FastAPI server that exposes `/file_parse`, `/tasks`, and `/health`. The `mineru` CLI already accepts `--api-url <url>` to delegate parsing to a running server instead of loading models locally. The key flag is `--enable-vlm-preload True` on the server: it loads the VLM once at startup and keeps it warm.

**Net effect:** First ingest pays the 30–60s startup cost once. All subsequent ingests in the same machine session skip model loading entirely.

---

## Architecture

```
wiki-ingest skill
      │
      ▼
doc_to_markdown.py
      │
      ├─ ensure_server()          ← NEW: checks /health, starts server if not up
      │         │
      │         └─ mineru-api     ← background process (stays up indefinitely)
      │              --host 127.0.0.1 --port 8765
      │              --enable-vlm-preload True
      │
      └─ Popen(["mineru",         ← CHANGED: adds --api-url when server is healthy
               "--api-url", "http://127.0.0.1:8765",
               "-p", str(doc_path),
               "-o", str(workdir)])
```

The `mineru` CLI, when given `--api-url`, delegates the parse to the server and streams the server's output back to stdout — identical format to the current behavior.

---

## Implementation

### 1. `ensure_server(port: int = 8765) -> int`

New function in `doc_to_markdown.py`:

1. Poll `GET http://127.0.0.1:{port}/health` — if 200, server is already up; return port.
2. Check if port is taken by a non-MinerU process (non-200 or wrong response shape) → try ports 8766, 8767, 8768 in order.
3. If no live server found on any candidate port:
   a. Pick the first free port (starting at 8765).
   b. Start `mineru-api --host 127.0.0.1 --port {port} --enable-vlm-preload True` via `subprocess.Popen(stdout=logfile, stderr=logfile)`.
   c. Write PID to `~/.mineru-api.pid`.
   d. Poll `GET /health` every 2s for up to 90s.
4. If server never becomes healthy within 90s:
   - Print `[MinerU] WARNING: server did not start; falling back to local mode`.
   - Return `None` (signals `convert()` to omit `--api-url`).
5. Return the confirmed healthy port.

### 2. `convert()` update

Current:
```python
proc = subprocess.Popen(
    ["mineru", "-p", str(doc_path), "-o", str(workdir)],
    ...
)
```

New:
```python
port = ensure_server()
cmd = ["mineru", "-p", str(doc_path), "-o", str(workdir)]
if port:
    cmd = ["mineru", "--api-url", f"http://127.0.0.1:{port}"] + cmd[1:]
proc = subprocess.Popen(cmd, ...)
```

### 3. State files

| File | Purpose |
|---|---|
| `~/.mineru-api.pid` | PID of the running `mineru-api` process; used only to detect stale processes |
| `~/.mineru-api.log` | stdout + stderr of `mineru-api`; rotated by user if needed |

No project-local files — the server is machine-scoped, not project-scoped.

### 4. SKILL.md change

One sentence appended to the "Step 0" description:

> MinerU runs as a background server (auto-started on first use, port 8765); model weights load once per machine session, making subsequent ingests ~60s faster.

---

## M1-Specific Notes

- `hybrid-auto-engine` (MinerU's default) already uses Metal/MPS on Apple Silicon — no override needed.
- `--enable-vlm-preload True` is the single most impactful flag: it loads the model at server startup, not at parse time.
- Server logs go to `~/.mineru-api.log` — useful for debugging Metal/GPU errors on M1.

---

## Non-Goals

- Stopping the server automatically (it stays up; OS handles cleanup on reboot).
- Supporting remote servers or non-localhost binding.
- Changing the output format or file layout of `doc_to_markdown.py`.
- Parallelizing ingests (MinerU's own concurrency is capped at 1).

---

## Open Questions

None — all resolved during brainstorm.

---

## Risks

| Risk | Mitigation |
|---|---|
| Port 8765 already in use | Try 8766, 8767, 8768; fall back to local mode if all occupied |
| VLM preload takes >90s on slow startup | Fallback ensures ingest still works; user sees warning |
| Server crashes mid-ingest | `mineru` CLI will error; existing error handling in `doc_to_markdown.py` surfaces it |
| Stale PID file after server crash | `ensure_server()` always checks `/health` first — PID file is informational only |
| `mineru-api` not in PATH | Catch `FileNotFoundError` from `Popen`; print clear error and fall back to local mode |
