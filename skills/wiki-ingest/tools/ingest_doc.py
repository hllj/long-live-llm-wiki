#!/usr/bin/env python3
"""Orchestrate doc_to_markdown + enhance_images; manage workdir and ingest.log."""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_tool_output(stdout: str) -> dict[str, str]:
    """Parse single-word key:value contract lines; skip progress/summary lines."""
    result: dict[str, str] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("[") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if " " in key:  # skip summary lines like "Images found: ..." or "step2 written: ..."
            continue
        result[key] = val.strip()
    return result


def inspect_workdir(workdir: Path) -> dict[str, bool]:
    return {
        "step1": (workdir / "step1_mineru_raw.md").exists(),
        "images": (workdir / "images").is_dir(),
        "step2": (workdir / "step2_enhanced.md").exists(),
    }


def report_workdir(workdir: Path, state: dict[str, bool]) -> None:
    try:
        rel = workdir.relative_to(REPO_ROOT)
    except ValueError:
        rel = workdir
    print(f"[Step 0] Intermediate folder already exists: {rel}/")
    tick = lambda b: "✓" if b else "✗"
    img_count = len(list((workdir / "images").glob("*"))) if state["images"] else 0
    print(f"  {tick(state['step1'])} step1_mineru_raw.md  ({'found' if state['step1'] else 'missing'})")
    if state["images"]:
        print(f"  {tick(state['images'])} images/              ({img_count} files)")
    else:
        print(f"  ✗ images/              (missing)")
    note = "(found — contains Gemini descriptions)" if state["step2"] else "(missing)"
    print(f"  {tick(state['step2'])} step2_enhanced.md    {note}")


def write_log(workdir: Path, entry: dict, force: bool) -> None:
    log_path = workdir / "ingest.log"
    mode = "w" if force else "a"
    with open(log_path, mode) as f:
        f.write(f"=== Run {datetime.datetime.utcnow().isoformat()}Z ===\n")
        for k, v in entry.items():
            f.write(f"{k}: {v}\n")
        f.write("\n")


def stream_subprocess(cmd: list[str]) -> tuple[int, str]:
    """Run cmd with Popen, stream stdout to terminal, return (returncode, full_stdout)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []
    for line in proc.stdout:
        print(line, end="", flush=True)
        lines.append(line)
    proc.wait()
    return proc.returncode, "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a document into raw/ with Gemini-enriched figures"
    )
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--slug", help="Output slug (default: derived from filename)")
    parser.add_argument("--force", action="store_true", help="Re-run all steps, overwrite existing")
    parser.add_argument("--gemini-model", default="gemini-3.5-flash", help="Gemini model ID")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    slug = args.slug or slugify(doc_path.stem)
    workdir = REPO_ROOT / "raw" / slug
    out_path = REPO_ROOT / "raw" / f"{slug}.md"
    tools_dir = Path(__file__).resolve().parent
    start_time = time.time()
    log_entry: dict = {"document": doc_path.name, "slug": slug}

    skip_step1 = skip_step2 = False

    if workdir.exists() and not args.force:
        state = inspect_workdir(workdir)
        report_workdir(workdir, state)
        if state["step2"]:
            print("Re-run Step 0 and overwrite? [y/N] ", end="", flush=True)
            if input().strip().lower() != "y":
                skip_step1 = skip_step2 = True
        elif state["step1"]:
            print("step1_mineru_raw.md found but step2_enhanced.md missing.")
            print("Resume from Gemini enrichment only (skip MinerU re-run)? [Y/n] ", end="", flush=True)
            if input().strip().lower() != "n":
                skip_step1 = True

    workdir.mkdir(parents=True, exist_ok=True)

    if not skip_step1:
        rc, _ = stream_subprocess([
            sys.executable, str(tools_dir / "doc_to_markdown.py"),
            str(doc_path), "--workdir", str(workdir),
        ])
        if rc != 0:
            sys.exit(1)

    step1_path = workdir / "step1_mineru_raw.md"
    images_dir = workdir / "images"

    if not step1_path.exists():
        print("Error: step1_mineru_raw.md not found after conversion", file=sys.stderr)
        sys.exit(1)

    exit_code = 0
    if not skip_step2:
        step2_path = workdir / "step2_enhanced.md"
        rc, _ = stream_subprocess([
            sys.executable, str(tools_dir / "enhance_images.py"),
            str(step1_path), str(images_dir),
            "--output", str(step2_path),
            "--gemini-model", args.gemini_model,
        ])
        if rc == 1:
            sys.exit(1)
        exit_code = rc

    step2_path = workdir / "step2_enhanced.md"
    if out_path.exists() and not args.force:
        print(f"[Step 0] {out_path.name} already exists. Overwrite? [y/N] ", end="", flush=True)
        if input().strip().lower() != "y":
            sys.exit(0)
    shutil.copy2(step2_path, out_path)

    elapsed = time.time() - start_time
    log_entry.update({"elapsed_s": f"{elapsed:.1f}", "exit_code": exit_code})
    write_log(workdir, log_entry, args.force)

    print(f"\nStep 0 complete — see terminal output above for image summary")
    print(f"Intermediate artifacts saved to: raw/{slug}/")
    print(f"Final enriched markdown:         raw/{slug}.md")


if __name__ == "__main__":
    main()
