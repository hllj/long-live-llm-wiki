import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import enhance_images


def test_enrich_inserts_description_after_image(tmp_path):
    """enrich() appends a blockquote description immediately after each image line."""
    img = tmp_path / "images" / "abc.jpg"
    img.parent.mkdir()
    img.write_bytes(b"fake image content")

    md = "# Doc\n\n![alt text](images/abc.jpg)\n\nSome text.\n"

    with patch.object(enhance_images, "describe_image", return_value="A bar chart showing loss curves."):
        result, found, described, failures = enhance_images.enrich(
            md, tmp_path, MagicMock(), "gemini-3.5-flash"
        )

    assert found == 1
    assert described == 1
    assert failures == []
    assert "![alt text](images/abc.jpg)" in result
    assert "> **Figure description (Gemini):** A bar chart showing loss curves." in result
    lines = result.splitlines()
    img_idx = next(i for i, l in enumerate(lines) if "abc.jpg" in l)
    assert "Figure description (Gemini):" in lines[img_idx + 1]


def test_enrich_idempotent_skips_existing_description(tmp_path):
    """enrich() does not duplicate descriptions if the marker already follows the image."""
    img = tmp_path / "images" / "abc.jpg"
    img.parent.mkdir()
    img.write_bytes(b"fake")

    md = (
        "# Doc\n\n"
        "![alt](images/abc.jpg)\n"
        "> **Figure description (Gemini):** Already described.\n\n"
        "Text.\n"
    )

    with patch.object(enhance_images, "describe_image") as mock_desc:
        result, found, described, failures = enhance_images.enrich(
            md, tmp_path, MagicMock(), "gemini-3.5-flash"
        )

    mock_desc.assert_not_called()
    assert result.count("Figure description (Gemini):") == 1


def test_enrich_missing_image_file_inserts_placeholder(tmp_path):
    """enrich() inserts a placeholder and adds to failures when image file is absent."""
    (tmp_path / "images").mkdir()
    md = "# Doc\n\n![](images/missing.jpg)\n\nText.\n"

    result, found, described, failures = enhance_images.enrich(
        md, tmp_path, MagicMock(), "gemini-3.5-flash"
    )

    assert found == 1
    assert described == 0
    assert "images/missing.jpg" in failures
    assert "[image file not found:" in result


def test_enrich_gemini_exception_inserts_error_placeholder(tmp_path):
    """enrich() inserts an error placeholder and continues when Gemini raises."""
    img = tmp_path / "images" / "bad.jpg"
    img.parent.mkdir()
    img.write_bytes(b"fake")

    md = "# Doc\n\n![](images/bad.jpg)\n"

    with patch.object(enhance_images, "describe_image", side_effect=RuntimeError("API down")):
        result, found, described, failures = enhance_images.enrich(
            md, tmp_path, MagicMock(), "gemini-3.5-flash"
        )

    assert found == 1
    assert described == 0
    assert "images/bad.jpg" in failures
    assert "Gemini error" in result
    assert "API down" in result


def test_cli_missing_api_key(tmp_path):
    """CLI exits 1 with a clear message when GEMINI_API_KEY is not set."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n")
    (tmp_path / "images").mkdir()

    env = {"PATH": "/usr/bin:/bin"}  # no GEMINI_API_KEY
    result = subprocess.run(
        [sys.executable, "skills/wiki-ingest/tools/enhance_images.py", str(md_file), str(tmp_path / "images")],
        capture_output=True,
        text=True,
        env=env,
        cwd="/Users/hllj/Projects/long-live-wiki",
    )

    assert result.returncode == 1
    assert "GEMINI_API_KEY" in result.stderr
