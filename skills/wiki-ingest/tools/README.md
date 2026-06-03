# skills/wiki-ingest/tools/

Internal tools for wiki-ingest binary document support (Feature 003).
These scripts are called by the wiki-ingest skill — do not invoke them directly.

## Developer Setup

```bash
pip install -r skills/wiki-ingest/tools/requirements.txt
```

> **First run:** `mineru[all]` downloads layout detection model weights (~several GB) on first
> invocation. Ensure you have disk space and a stable connection before first use.

## Running tests

```bash
cd /path/to/repo
python -m pytest skills/wiki-ingest/tools/tests/ -v
```
