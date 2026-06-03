#!/usr/bin/env python3
"""Convert a document to markdown using MinerU CLI."""
import argparse
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


def convert(doc_path: Path, workdir: Path) -> tuple[Path, Path]:
    """Run MinerU, stream output live, rename result to step1_mineru_raw.md.

    Returns (step1_path, images_dir) where both are inside workdir.
    """
    workdir.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        ["mineru", "-p", str(doc_path), "-o", str(workdir)],
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
