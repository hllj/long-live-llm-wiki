# Feature 005: MinerU Persistent Server

**Status:** Approved
**Version:** 1.0.0
**Created:** 2026-06-05
**Updated:** 2026-06-05

---

## Problem Statement

`doc_to_markdown.py` (the internal MinerU conversion tool used by `wiki-ingest`) starts a fresh MinerU process on every PDF ingest. MinerU's default backend (`hybrid-auto-engine`) loads its VLM model weights from disk on each invocation — adding 30–60 seconds of model-loading overhead before any actual document parsing begins. On Apple M1, this overhead occurs on every ingest regardless of how small the PDF is.

MinerU ships a FastAPI server (`mineru-api`) designed for exactly this scenario: the server loads the model once at startup and handles conversion requests from the MinerU CLI. The CLI already supports delegating to a running server. This feature wires them together transparently so that `doc_to_markdown.py` uses the server automatically when available, and the user experiences no model-loading delay on the second and subsequent ingests in a machine session.

---

## Goals

1. On the first PDF ingest in a machine session, `doc_to_markdown.py` automatically starts a MinerU API server in the background with model weights pre-loaded.
2. On all subsequent ingests in the same session (or any session where the server is still running), `doc_to_markdown.py` detects the running server and reuses it — no model reload, no extra wait.
3. The user never has to start, stop, or manage the server manually.
4. If the server cannot be started or becomes unhealthy, `doc_to_markdown.py` falls back to the original local mode without blocking the ingest.
5. All existing output — intermediate file layout, markdown format, exit codes — is unchanged.

---

## Non-Goals

- Automatically stopping or restarting the server (the server runs until the OS or user terminates it).
- Supporting non-localhost server bindings or remote MinerU instances.
- Parallelizing multiple concurrent ingests (MinerU's own concurrency is capped at 1; this spec does not change that).
- Changing the output format, intermediate folder layout, or any other behavior defined in spec-003.
- Adding a user-facing CLI command to manage the server.

---

## Users and Context

**Primary user:** The wiki owner who runs `wiki-ingest` on one or more PDFs in a working session.
**Usage context:** The user drops a PDF into `raw/`, invokes `wiki-ingest`, and expects the conversion step to complete as quickly as possible. They do not know or care that a server is involved — the speedup should be invisible.
**Machine context:** macOS, Apple M1 (arm64). MinerU 3.2.2 installed. `mineru-api` binary available in PATH.

---

## User Stories

### Story 1: Warm server on second ingest

**As a** wiki owner,
**I want** the second PDF I ingest in a session to skip model loading,
**So that** I don't wait 30–60 seconds for a model that's already loaded.

**Acceptance Criteria:**
- AC-1.1: When `doc_to_markdown.py` is invoked and a healthy MinerU server is already running on a candidate port, it delegates conversion to that server. No new server process is started.
- AC-1.2: The conversion begins (MinerU starts processing pages) within 5 seconds of `doc_to_markdown.py` being invoked (excluding document parse time itself).
- AC-1.3: The output — `step1_mineru_raw.md`, `images/`, and the `markdown:` / `images:` lines printed on stdout — is identical to a local-mode run.

### Story 2: Auto-start on first ingest

**As a** wiki owner,
**I want** the server to start automatically when I ingest a PDF for the first time in a session,
**So that** subsequent ingests in the same session are fast without any manual setup.

**Acceptance Criteria:**
- AC-2.1: When no MinerU server is running on any candidate port, `doc_to_markdown.py` starts one in the background before running the conversion.
- AC-2.2: The script waits until the server is healthy before delegating the conversion.
- AC-2.3: The first ingest completes successfully (same output as local mode) — the server startup is transparent to the result.
- AC-2.4: The user sees a one-line message when a new server is started:
  ```
  [MinerU] Starting persistent server on port 8765 (first use — loading model)...
  ```
  followed by the normal conversion progress lines once the server is ready.
- AC-2.5: Server process output (stdout + stderr) is redirected to `~/.mineru-api.log` and does not appear in the terminal during normal operation.

### Story 3: Graceful fallback when server is unavailable

**As a** wiki owner,
**I want** ingest to still work even if the persistent server fails to start or is unavailable,
**So that** I'm never blocked from converting a document.

**Acceptance Criteria:**
- AC-3.1: If the server binary is not found in PATH, `doc_to_markdown.py` prints a warning and runs in local mode:
  ```
  [MinerU] WARNING: mineru-api not found; running in local mode (model loads each run)
  ```
- AC-3.2: If the server is started but does not become healthy within the startup timeout, `doc_to_markdown.py` prints a warning and runs in local mode:
  ```
  [MinerU] WARNING: server did not become ready; falling back to local mode
  ```
- AC-3.3: If all candidate ports are occupied by non-MinerU processes, `doc_to_markdown.py` prints a warning and runs in local mode:
  ```
  [MinerU] WARNING: no available port for mineru-api; running in local mode
  ```
- AC-3.4: In all fallback cases, `doc_to_markdown.py` completes with the same output format and exit codes as before this feature was introduced.

### Story 4: Port conflict avoidance

**As a** wiki owner who runs other local services,
**I want** the MinerU server to avoid ports already in use,
**So that** it doesn't conflict with my other development tools.

**Acceptance Criteria:**
- AC-4.1: `doc_to_markdown.py` checks whether the default port (8765) is occupied before starting a server.
- AC-4.2: If port 8765 is occupied by a non-MinerU process, the script tries ports 8766, 8767, and 8768 in order before giving up and running in local mode.
- AC-4.3: A port is considered "occupied by MinerU" if and only if its `/health` endpoint responds with HTTP 200 and a response body indicating a healthy MinerU server. Any other response (connection refused, non-200 status, unexpected body) means the port is occupied by something else.

---

## Functional Requirements

### FR-1: Server detection before each conversion

Before every PDF conversion, `doc_to_markdown.py` checks whether a MinerU API server is already running. It checks candidate ports in order: 8765, 8766, 8767, 8768. The first port that returns a healthy MinerU response is used.

### FR-2: Auto-start when no server is found

If no healthy server is found on any candidate port, `doc_to_markdown.py` starts one. The server binds to localhost (127.0.0.1) on the first available candidate port. Model preloading is enabled at server startup. The script does not proceed to conversion until the server reports healthy.

### FR-3: Startup timeout

The script waits at most 90 seconds for the server to become healthy after starting it. Health is polled every 2 seconds. If the server is not healthy after 90 seconds, the script falls back to local mode.

### FR-4: Server state files (machine-scoped)

When the script starts a new server:
- Server process output is redirected to `~/.mineru-api.log`.
- The server process identifier is written to `~/.mineru-api.pid`. This file is informational: it is not required for correct operation and is never read to gate behavior.

### FR-5: Conversion delegation

When a healthy server is available, `doc_to_markdown.py` delegates PDF conversion to the server using the MinerU CLI's built-in server delegation capability. Progress lines streamed from the CLI are forwarded to the terminal with the `[MinerU]` prefix, identical to local mode (AC-1.3).

### FR-6: Local mode fallback

In all error cases (server binary absent, startup timeout, all ports occupied), `doc_to_markdown.py` runs in local mode. Local mode behavior is identical to the pre-005 implementation. No change to output format, intermediate files, or exit codes.

### FR-7: Environment variable overrides

The default port (8765) and PID file path (`~/.mineru-api.pid`) are overridable via environment variables `MINERU_API_PORT` and `MINERU_API_PID_FILE`. This is required so automated tests can run against a test-scoped server without side effects.

### FR-8: SKILL.md update

`skills/wiki-ingest/SKILL.md` is updated with one sentence in the Step 0 section noting that MinerU auto-starts as a background server on first use. The sentence must fit within the existing character budget constraint (NFR-6 of spec-003).

---

## Non-Functional Requirements

- NFR-1: Server detection (health check on candidate ports) must add no more than 5 seconds of overhead on runs where the server is already healthy.
- NFR-2: All existing tests for `doc_to_markdown.py` must pass without modification. New tests cover the server detection, auto-start, and fallback paths.
- NFR-3: No changes to the output format, intermediate folder layout, printed lines format (except the new server-start announcement in AC-2.4), or exit codes defined in spec-003.
- NFR-4: The server is never started if the input document is not a PDF (i.e., if `doc_to_markdown.py` would not be invoked at all, no server is started).
- NFR-5: Server state files (`~/.mineru-api.log`, `~/.mineru-api.pid`) are in the user's home directory — never in the project directory. This keeps the repo clean and makes the server machine-scoped rather than project-scoped.

---

## Error Scenarios

| Scenario | Expected behavior |
|---|---|
| `mineru-api` binary not in PATH | Print AC-3.1 warning; run in local mode; exit code unchanged |
| Server started but never healthy (90s timeout) | Print AC-3.2 warning; run in local mode; exit code unchanged |
| All candidate ports occupied by non-MinerU processes | Print AC-3.3 warning; run in local mode; exit code unchanged |
| Server crashes after start but before conversion begins | Health check fails; treat as "no server"; if all ports now clear, start a new server; if not, fall back to local mode |
| Server crashes mid-conversion | MinerU CLI returns non-zero; existing exit code 1 behavior applies (same as local mode crash) |
| `~/.mineru-api.log` not writable | Start server with stdout/stderr discarded (`/dev/null`); log a warning but do not abort |
| `MINERU_API_PORT` set to an invalid value | Ignore the override and use the default port (8765); do not abort |

---

## Open Questions

None. All resolved during brainstorm (see `design.md`).

---

## Out of Scope

- A user-facing command to start/stop/restart the MinerU server.
- Configuring the MinerU backend type (the default `hybrid-auto-engine` is used, which already uses Metal on Apple M1).
- Support for DOCX conversion via the persistent server (DOCX support is already out of scope in spec-003 v1).
- Log rotation for `~/.mineru-api.log`.
- Multi-machine or networked server configurations.
