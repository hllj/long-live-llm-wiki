#!/usr/bin/env python3
"""Enrich markdown image references with Gemini vision descriptions."""
import argparse
import os
import re
import sys
import time
from pathlib import Path

import google.genai as genai
from google.genai import types


IMAGE_RE = re.compile(r'(!\[.*?\]\((images/[^)]+)\))')
DESCRIPTION_MARKER = "**Figure description (Gemini):**"
GEMINI_PROMPT = (
    "You are analyzing a figure from a technical research document. "
    "Describe this figure in detail: what it shows, what data or relationships "
    "it represents, and its likely purpose in the context of the document. "
    "Be specific and technical. Limit your response to 3-5 sentences."
)
MIME_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def describe_image(client: genai.Client, image_path: Path, model: str) -> str:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    mime_type = MIME_MAP.get(image_path.suffix.lower().lstrip("."), "image/jpeg")
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            GEMINI_PROMPT,
        ],
    )
    return response.text.strip()


def enrich(
    markdown_text: str,
    images_dir: Path,
    client: genai.Client,
    model: str,
) -> tuple[str, int, int, list[str]]:
    """Insert Gemini descriptions after each image reference.

    images_dir must be the images/ directory itself (not its parent).
    Idempotent: skips image lines that already have a description block below them.
    Returns (enriched_text, images_found, images_described, failed_refs).
    """
    lines = markdown_text.splitlines(keepends=True)
    total = sum(1 for l in lines if IMAGE_RE.search(l))
    output: list[str] = []
    found = described = idx = 0
    failures: list[str] = []

    for i, line in enumerate(lines):
        output.append(line)
        match = IMAGE_RE.search(line)
        if not match:
            continue

        img_rel = match.group(2)
        found += 1
        idx += 1

        next_lines = [l for l in lines[i + 1 : i + 4] if l.strip()]
        if next_lines and DESCRIPTION_MARKER in next_lines[0]:
            continue

        img_path = images_dir / Path(img_rel).name
        if not img_path.exists():
            print(f"[Gemini] Describing figure {idx}/{total}: {img_rel} ... FAILED (file not found)", flush=True)
            failures.append(img_rel)
            output.append(f"> {DESCRIPTION_MARKER} [image file not found: {img_rel}]\n")
            continue

        print(f"[Gemini] Describing figure {idx}/{total}: {img_rel} ... ", end="", flush=True)
        t0 = time.time()
        try:
            description = describe_image(client, img_path, model)
            print(f"done ({time.time() - t0:.1f}s)", flush=True)
            output.append(f"> {DESCRIPTION_MARKER} {description}\n")
            described += 1
        except Exception as exc:
            print(f"FAILED ({exc}) ({time.time() - t0:.1f}s)", flush=True)
            failures.append(img_rel)
            output.append(f"> {DESCRIPTION_MARKER} [Gemini error — could not process image: {exc}]\n")

    return "".join(output), found, described, failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich markdown image references with Gemini descriptions"
    )
    parser.add_argument("markdown", help="Path to input markdown file (step1_mineru_raw.md)")
    parser.add_argument("images_dir", help="Path to the images/ directory")
    parser.add_argument("--output", help="Output path (default: sibling step2_enhanced.md)")
    parser.add_argument("--gemini-model", default="gemini-3.5-flash", help="Gemini model ID")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    images_dir = Path(args.images_dir)
    client = genai.Client(api_key=api_key)

    text = md_path.read_text(encoding="utf-8")
    enriched, found, described, failures = enrich(text, images_dir, client, args.gemini_model)

    out_path = Path(args.output) if args.output else md_path.parent / "step2_enhanced.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(enriched, encoding="utf-8")

    print(f"Images found: {found} | Described: {described} | Failed: {len(failures)}")
    print(f"step2 written: {out_path}")
    if failures:
        print(f"Failed images: {', '.join(failures)}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
