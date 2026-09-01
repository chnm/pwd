# DEVNOTES.md

Development notes and deployment TODOs for the PWD Hugo site.

---

## Deployment: URL Redirects

The original Omeka S site used URLs like `/s/home/item/{id}` and `/s/home/page/{slug}`. These are not Hugo aliases; they are 301'd by the regex `map` in `redirects.caddy`, which the `Dockerfile` imports into the Caddy config. Editorial pages and news posts still keep their own `aliases:` in frontmatter.

---

## Deployment: Media Files / CDN

Media files (document images) are not part of the Hugo build. This is now implemented (`mediaBaseURL = https://obj.rrchnm.org/wardepartmentpapers.org` in `hugo.toml`):

- Host media files on object storage (MinIO, S3, or similar CDN)
- Set a site param in `hugo.toml` like `[params] mediaBaseURL = "https://cdn.example.com/pwd-media"`
- Templates reference images as `{{ site.Params.mediaBaseURL }}/files/large/{{ $filename }}`
- No media files need to be part of the Hugo build at all

For local development, media can be served separately or symlinked as needed.

---

## Taxonomy Decisions

### Active taxonomies (4)
- `authors` — document author(s)
- `recipients` — document recipient(s)
- `collections` — archival collection name(s)
- `doc_types` — document type (e.g., "Autograph Letter Signed")

### Not taxonomies (kept as plain front matter)
- `notable_persons` — free-text, 41,930 unique terms, 70% used once
- `notable_locations` — free-text, 9,166 unique terms, 69% used once
- `notable_items` — free-text, 49,837 unique terms, 82% used once

These are uncontrolled vocabulary annotations. They display on document pages but don't generate browsable index/term pages. Pagefind search will cover discovery across these fields.

---

## Build Performance Notes

- Dropping 3 notable_* taxonomies eliminated ~100k+ taxonomy term pages
- Removing aliases eliminated ~88k redirect HTML files
- Removing `static-media` from `staticDir` avoids copying ~26k media files during build
- Remaining build: ~44k content pages + ~4 taxonomy indexes + taxonomy term pages + paginator pages

---

## AI Transcription Pipeline

Two implementations exist. The **preferred** one is `_transcription/transcribe.py`,
which shells out to **`claude -p`** and bills a Claude **subscription** (no API
token cost). `scripts/transcribe.py` is an alternate using the Anthropic SDK +
API key. Full runbook: `_transcription/README.md`.

Typical flow:

1. Fix any truncated image lists: `python3 scripts/fix_multipage_images.py`
   (local, no network; writes `multipage_grown_ids.txt`).
2. Rebuild the manifest: `python3 _transcription/build_image_list.py --content-dir content/document`.
3. Transcribe: `python3 _transcription/transcribe.py --ids-file multipage_grown_ids.txt --model claude-sonnet-4-6`.

Operational notes:

- **Resumable** — every doc is saved immediately (`.transcribe_progress` cache +
  `transcriptions.json`). `--ids-file` *forces* its targets, so to resume a
  targeted run without redoing work, regenerate a "remaining = targets − done"
  list first (see the README).
- **Usage guards** — `--max-tokens N` stops cleanly at a cumulative-token ceiling;
  a subscription rate limit also stops cleanly. Per-doc usage is logged to
  `_transcription/usage_log.jsonl`. There is no CLI to read remaining
  subscription allowance — check `/usage` in a Claude Code session.
- **Long runs** — wrap in `caffeinate -i -m -s -w <pid>` (or launch under
  `caffeinate`) to prevent system idle-sleep while allowing the display to sleep;
  keep the machine on AC and the lid open.
- **Sync to site (manual, required)** — Hugo reads `data/transcriptions_ai.json`,
  but the `claude -p` pipeline writes `_transcription/transcriptions.json`. Merge
  the latter into the former before building, or the new transcriptions won't
  appear on the site.
- **Stragglers** — the run is complete; ~12,300 docs remain untranscribed and
  that is expected (no usable images, content-filter refusals, or page caps).
  Candidates: `_transcription/big_doc_ids.txt`, `skip_ids.txt`, `failures.csv`.
  To retry, use `_transcription/run_loop.sh`, merge the output as above, then
  rebuild the dashboard: `uv run python3 scripts/build_transcription_dashboard.py`.
