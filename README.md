# Gitbanner - Github Commit Banner

Gitbanner uses `fake.py` to fabricate a contribution heatmap: it initializes a Git repo, appends pseudo-random tokens to `data.txt`, and forges timestamps so hundreds of commits span the configured date range. Run it inside a disposable directory to avoid polluting existing repos.

## What it does
- Boots a Git repository (if missing) and sets the author identity
- Iterates day by day through the configured years to plan commits
- Writes random payloads to `data.txt` and commits with forged dates to paint a banner on your contribution graph

## Configuration

Copy the default environment template if you want custom values:

```bash
cp .env .env.local
```

## Run with uv
```bash
uv python install 3.11
uv run fake.py
```

> ⚠️ Warning: execution can take quite a while because the script walks day by day and generates hundreds of commits.
