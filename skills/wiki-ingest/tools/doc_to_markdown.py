#!/usr/bin/env python3
"""Convert a document to markdown using MinerU CLI."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def convert(doc_path: Path, outdir: Path) -> tuple[Path, Path]:
    result = subprocess.run(
        ["mineru", "-p", str(doc_path), "-o", str(outdir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    # MinerU may nest output under a subdir named after the input stem.
    # Find the first .md file produced anywhere under outdir.
    md_files = sorted(Path(outdir).rglob("*.md"))
    if not md_files:
        print(f"Error: MinerU produced no markdown output in {outdir}", file=sys.stderr)
        sys.exit(1)

    md_path = md_files[0]
    images_dir = md_path.parent / "images"
    return md_path, images_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert document to markdown via MinerU")
    parser.add_argument("document", help="Path to input document (PDF)")
    parser.add_argument("--outdir", help="Output directory (default: auto temp dir)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(f"Error: file not found: {doc_path}", file=sys.stderr)
        sys.exit(1)

    outdir = Path(args.outdir) if args.outdir else Path(tempfile.mkdtemp(prefix="mineru_"))
    outdir.mkdir(parents=True, exist_ok=True)

    md_path, images_dir = convert(doc_path, outdir)

    # Print contract lines for the orchestrator to parse
    print(f"markdown:{md_path}")
    print(f"images:{images_dir}")


if __name__ == "__main__":
    main()
