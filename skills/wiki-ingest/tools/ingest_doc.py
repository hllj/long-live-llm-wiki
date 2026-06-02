#!/usr/bin/env python3
"""Orchestrate doc_to_markdown + enhance_images and write output to raw/."""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_tool_output(stdout: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in stdout.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a document into raw/ with Gemini-enriched figures"
    )
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--slug", help="Output slug (default: derived from filename)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    parser.add_argument("--gemini-model", default="gemini-3.5-flash", help="Gemini model ID")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    slug = args.slug or slugify(doc_path.stem)
    out_path = REPO_ROOT / "raw" / f"{slug}.md"

    if out_path.exists() and not args.force:
        print(
            f"Error: raw/{slug}.md already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    tools_dir = Path(__file__).resolve().parent

    with tempfile.TemporaryDirectory(prefix="ingest_") as tmpdir:
        print(f"[1/2] Converting {doc_path.name} with MinerU...")
        r1 = subprocess.run(
            [sys.executable, str(tools_dir / "doc_to_markdown.py"), str(doc_path), "--outdir", tmpdir],
            capture_output=True,
            text=True,
        )
        if r1.returncode != 0:
            print(r1.stderr, file=sys.stderr)
            sys.exit(1)

        paths = parse_tool_output(r1.stdout)
        md_path = Path(paths.get("markdown", ""))
        images_dir = Path(paths.get("images", ""))

        if not md_path or not md_path.exists():
            print("Error: doc_to_markdown.py did not produce a markdown file", file=sys.stderr)
            sys.exit(1)

        enriched_tmp = Path(tmpdir) / f"{slug}.md"
        print(f"[2/2] Enriching figures with {args.gemini_model}...")
        r2 = subprocess.run(
            [
                sys.executable,
                str(tools_dir / "enhance_images.py"),
                str(md_path),
                str(md_path.parent),
                "--output", str(enriched_tmp),
                "--gemini-model", args.gemini_model,
            ],
            capture_output=True,
            text=True,
        )
        print(r2.stdout.strip())
        if r2.returncode == 1:
            print(r2.stderr, file=sys.stderr)
            sys.exit(1)
        if r2.returncode == 2:
            print(f"Warning: {r2.stderr.strip()}", file=sys.stderr)

        shutil.copy2(enriched_tmp, out_path)
        print(f"Output: raw/{slug}.md")


if __name__ == "__main__":
    main()
