# AGENTS.md

> For feature specifications and domain rules, see [SPEC.md](./SPEC.md). For the human-facing overview, see [README.md](./README.md).

---

## Project Overview

Static Hugo site for the Papers of the War Department (wardepartmentpapers.org), migrated from an Omeka S archive. The repository root **is** the Hugo project root. It was relocated from the `chnm/sustainability` monorepo (where it lived under `pwd/`) to its own repository in September 2026; older commit messages still reference the monorepo. There is no `hugo/` subdirectory and no wget'd copy of the old site in this repo.

The site has one item content type (Document) plus editorial pages and news posts, six taxonomies, Pagefind search, and a complete set of AI transcriptions. It needs no database or application server; media is served from object storage.

---

## Tech Stack

- **Hugo** extended v0.128.0+ (currently built with v0.164). Config: `hugo.toml` (+ `config/development/hugo.toml`).
- **Pagefind** (Node, `package.json`) — post-build search index.
- **Python 3.13 via `uv`** (`pyproject.toml`, `uv.lock`): `requests`, `pyyaml`, `anthropic`, `python-dotenv`; `pytest` for `tests/`.
- **just** (`justfile`) for commands.
- **Caddy** in Docker for serving (`Dockerfile`, `redirects.caddy`); GitHub Actions for CI/CD.

---

## Setup

```bash
brew install hugo just uv          # plus Node for pagefind
npm ci                             # installs pagefind
uv sync                            # python deps (tests, scripts)
just build                         # hugo --minify + pagefind → public/
just serve                         # dev server on :1313 (no search index)
just serve-pagefind                # build + pagefind --serve, to test search
just test                          # uv run pytest -q
```

`just build` raises `ulimit -n 65536` because ~43k pages exhaust the default macOS file-descriptor limit.

No fetch step is needed: all content is committed under `content/`. The Omeka fetch scripts only matter if content must be re-pulled (VPN required).

---

## Project Structure

```
pwd/
├── hugo.toml                      # Site config: taxonomies, mediaBaseURL, pagination
├── config/development/hugo.toml   # Dev override (staticDir)
├── justfile                       # Canonical commands
├── Dockerfile                     # stagex build: npm ci → hugo → pagefind → Caddy
├── redirects.caddy                # Legacy Omeka /s/home/... → Hugo path 301 map
├── .github/workflows/cicd.yml     # Calls chnm/.github shared Hugo workflow
├── package.json                   # pagefind
├── pyproject.toml / uv.lock       # Python deps
├── content/
│   ├── _index.md                  # Homepage
│   ├── {slug}.md                  # ~25 editorial pages (type: page)
│   ├── search.md                  # layout: search
│   ├── transcription-dashboard.md # type: transcription-dashboard
│   ├── ai-transcription-methodology.md
│   ├── document/{omeka_id}.md     # ~42,880 documents (frontmatter + human transcription body)
│   └── news/{wp_post_id}.md       # 240 WordPress posts (type: news) + _index.md
├── data/
│   ├── transcriptions_ai.json     # AI transcriptions keyed by omeka_id (30,479) — read by Hugo
│   ├── transcription_dashboard.json # Built by scripts/build_transcription_dashboard.py
│   └── media_map.json             # reel omeka_image_id → ordered filenames (repair scripts only)
├── layouts/
│   ├── _default/                  # baseof, single (editorial), list, taxonomy, term, search
│   ├── document/                  # single.html (viewer + metadata + transcription tabs), list.html
│   ├── news/                      # single, list, archive
│   ├── categories/term.html       # news category pages
│   ├── transcription-dashboard/single.html
│   ├── 404.html, index.html
│   └── partials/                  # head (incl. Matomo), nav, footer, news-sidebar, item/{document,browse,shared}
├── static/
│   ├── css/, fonts/, img/, assets/ # Theme assets, teaching PDFs
│   └── js/                        # global.js, tablesaw, search-pagefind.js
├── scripts/                       # Python: fetch, migrate, repair, dashboard (see below)
├── _transcription/                # claude -p transcription pipeline (README.md is the runbook)
├── tests/                         # pytest (72 tests) for repair + transcription scripts
├── docs/superpowers/              # Design specs/plans for the image fix and usage monitor
├── multipage_grown_ids.txt, multipage_fix_manifest.json   # fix_multipage_images.py outputs
├── transcriptions.json            # STALE: April 2026 Opus run (7,190 entries); nothing reads it
├── CLAUDE.md, AGENTS.md, SPEC.md, README.md, DEVNOTES.md
└── LICENSE                        # MIT, RRCHNM
```

---

## Architecture

### Content model

| Type | Count | Source | Layout |
|---|---|---|---|
| Document | ~42,880 | `scripts/fetch_items.py` (Omeka `/api/items`) | `layouts/document/` |
| Editorial page | ~25 | `scripts/fetch_pages.py` (Omeka `/api/site_pages`), then `html_to_markdown.py` | `layouts/_default/single.html` |
| News post | 240 | `scripts/fetch_news.py` / `extract_news.py` (wget'd WordPress) | `layouts/news/` |

Only Documents are items. Collections and repositories are denormalized into each document's frontmatter (`collections`, `collection_id`, `repositories`) and browsed through taxonomy pages. Image, Name, Microfilm, and Publication items have no pages.

Document frontmatter keys: `omeka_id`, `title`, `description`, `year`/`month`/`day`, `authors`, `recipients`, `collections`, `collection_id`, `repositories`, `doc_types`, `sent_from`, `document_number`, `omeka_image_id`, `images`, `num_pages`, `notable_persons`, `notable_locations`, `notable_items`, `resource_type`, `created`. Human transcription text is the markdown body.

### Taxonomies

Defined in `hugo.toml`: `authors`, `recipients`, `collections`, `repositories`, `doc_types` (documents) and `categories` (news). Term pages live at `/{taxonomy}/{slug}/` via `layouts/_default/term.html`. The `notable_*` fields are plain frontmatter lists, shown on document pages but not browsable — they are uncontrolled vocabulary with tens of thousands of single-use terms (see `DEVNOTES.md`).

### Images (microfilm reel model)

Documents share Omeka **Image resources** (microfilm reels) referenced by `omeka_image_id`. Each document's `images:` frontmatter list is the ordered slice of that reel belonging to it. Templates render `{{ site.Params.mediaBaseURL }}/files/{square|large|original}/{filename}` with `mediaBaseURL = https://obj.rrchnm.org/wardepartmentpapers.org`; no media lives in the repo.

The `images:` lists were repaired in several passes (all applied, all local, no API): `fix_multipage_images.py` (reel slicing by neighbor `page_start`), `harvest_viewer_images.py` + `apply_viewer_harvest.py` (ground truth from the legacy site's viewers), and `fix_suffix_viewers.py` (undo inflation from unbounded letterbook viewers). `data/media_map.json` exists for these scripts, not for templates. Specs: `docs/superpowers/specs/`.

### Transcriptions

- **Human**: markdown body of `content/document/{id}.md`.
- **AI**: `data/transcriptions_ai.json` keyed by `omeka_id`. The run is complete (30,479 documents; 2,512 have both human and AI, 12,341 have neither). Produced by `_transcription/transcribe.py` (`claude -p`, billed to a Claude subscription; runbook `_transcription/README.md`; `run_loop.sh` auto-resumes). Its output `_transcription/transcriptions.json` is merged manually into `data/transcriptions_ai.json`. `scripts/transcribe.py` is an alternate path using the Anthropic SDK and an API key.
- **Dashboard**: `scripts/build_transcription_dashboard.py` writes `data/transcription_dashboard.json` for `/transcription-dashboard/`. It is not run by the build; re-run it after any transcription sync.
- Document template shows a tabbed human/AI UI. Methodology is published at `content/ai-transcription-methodology.md`.

### Search

Pagefind indexes all of `public/` after the Hugo build (`just build`; the Dockerfile does the same). `layouts/_default/search.html` + `static/js/search-pagefind.js` keep a Documents / Guides & News toggle with `?q=` and `?type=` params.

### URL compatibility

- Documents have **no** Hugo aliases. Legacy Omeka URLs (`/s/home/item/{id}`, `/s/home/page/{slug}`, etc.) are 301'd by the regex `map` in `redirects.caddy`, which the Dockerfile imports into Caddy.
- Editorial pages still carry `aliases: [/s/home/page/{slug}]` and news posts `aliases: [/news/?p={id}]`.
- `/files/*` → object storage is redirected by the fronting web server, not by Caddy.

### Deployment

`.github/workflows/cicd.yml` runs the shared `chnm/.github` Hugo build/release/deploy workflow on self-hosted runners for pushes to `main` (https://wardepartmentpapers.org) and `preview` (https://pwd.dev.chnm.gmu.edu). The `Dockerfile` builds the site and Pagefind index, then serves `/srv` with Caddy.

### Omeka S API (source of truth, rarely needed)

Base URL `https://omeka.wardepartmentpapers.org/api/` (VPN only). The old `www.wardepartmentpapers.org/api/` host 302→404s. Endpoints: `/items?per_page=100&page=N&sort_by=id&sort_order=asc`, `/site_pages`, `/media`. Total count in the `Omeka-S-Total-Results` header. Resource class IDs: 168 Repository, 169 Collection, 170 Microfilm, 171 Publication, 172 Name, 173 Image, 174 Document.

---

## Scripts

| Script | Purpose |
|---|---|
| `scripts/fetch_pages.py`, `fetch_items.py`, `fetch_media.py`, `fetch_num_pages.py` | Pull from the Omeka API (VPN) |
| `scripts/fetch_news.py`, `extract_news.py` | Build `content/news/` from the wget'd WordPress site |
| `scripts/html_to_markdown.py` | Convert editorial HTML bodies to markdown |
| `scripts/build_media_map.py` | `media_catalog.json` → `data/media_map.json` |
| `scripts/fix_multipage_images.py`, `fix_empty_images.py`, `fix_image_frontmatter.py`, `harvest_viewer_images.py`, `apply_viewer_harvest.py`, `fix_suffix_viewers.py` | Image-list repairs (all applied) |
| `scripts/migrate_items.py`, `migrate_images_to_frontmatter.py` | One-time migrations (historical) |
| `scripts/build_transcription_dashboard.py` | Rebuild `data/transcription_dashboard.json` |
| `scripts/estimate_transcription_cost.py`, `scripts/transcribe.py` | API-key transcription path |
| `_transcription/build_image_list.py`, `transcribe.py`, `run_loop.sh` | Preferred `claude -p` transcription pipeline |

---

## Conventions

- Frontmatter edits across the corpus use **minimal-diff regex string surgery**, never `yaml.dump` (it reorders and requotes keys across 43k files).
- `get_all_literals()` in `fetch_items.py` must `.strip()` values; the API returns multi-valued properties with leading spaces.
- `markup.goldmark.renderer.unsafe = true` is required — editorial and news bodies contain raw HTML.
- `baseof.html` renders the CHNM sustainability banner above the header (shared snippet from `chnm/sustainability/_snippets`); `head.html` embeds Matomo (site id 4). Both are intentional.
- Editorial pages describing the retired Omeka/Scripto features set `outdated: true`; `layouts/_default/single.html` renders a notice aside (12 pages).
- Templates use `{{ with .Params.field }}` to skip empty fields; taxonomy links use `.GetTerms`.
- Tests (`uv run pytest`, 72 passing) cover the repair scripts and transcription selection/usage logic. Keep them green.
- Good test document: 79270 (3 pages, human + AI transcription, all metadata fields).

## What Not to Do

- Do not add server-side functionality; the site must stay purely static.
- Do not re-introduce per-document Hugo aliases or `notable_*` taxonomies (both were removed for build size).
- Do not create content pages for Image, Name, Microfilm, Publication, Collection, or Repository items.
- Do not commit `public/` or `node_modules/`.

---
*Last Updated: 2026-09-01*
