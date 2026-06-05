#!/usr/bin/env python3
"""Convert a document to markdown using MinerU CLI."""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


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

    # MinerU may nest output under a subdir named after the input stem; find the .md
    md_files = sorted(f for f in workdir.rglob("*.md") if f.name not in ("step1_mineru_raw.md", "step2_enhanced.md"))
    if not md_files:
        print(f"Error: MinerU produced no markdown output in {workdir}", file=sys.stderr)
        sys.exit(1)

    step1_path = workdir / "step1_mineru_raw.md"
    shutil.copy2(md_files[0], step1_path)

    # Ensure images/ lives directly under workdir, not inside a MinerU subdir
    raw_images = md_files[0].parent / "images"
    target_images = workdir / "images"
    if raw_images.exists() and raw_images != target_images:
        if target_images.exists():
            shutil.rmtree(target_images)
        shutil.copytree(raw_images, target_images)
    elif not target_images.exists():
        target_images.mkdir()

    return step1_path, target_images


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert document to markdown via MinerU")
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--workdir", required=True, help="Permanent work directory (raw/<slug>/)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    step1_path, images_dir = convert(doc_path, Path(args.workdir))

    print(f"markdown:{step1_path}")
    print(f"images:{images_dir}")


if __name__ == "__main__":
    main()
