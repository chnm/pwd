# Papers of the War Department

Static site for the [Papers of the War Department, 1784–1800](https://wardepartmentpapers.org), a project of the [Roy Rosenzweig Center for History and New Media](https://rrchnm.org) at George Mason University. The archive reconstructs the War Department's records, destroyed by fire in 1800, from copies held in repositories across the United States.

This repository replaces the original Omeka S site with a [Hugo](https://gohugo.io) build: ~42,880 documents with metadata, page images, and human and AI transcriptions; ~25 editorial guides; 240 news posts; full-text search via [Pagefind](https://pagefind.app).

## Requirements

- Hugo extended ≥ 0.128 (built with 0.164)
- Node (for Pagefind)
- [`uv`](https://docs.astral.sh/uv/) with Python 3.13 (scripts and tests)
- [`just`](https://github.com/casey/just)

## Quick start

```bash
npm ci               # pagefind
uv sync              # python deps
just serve           # dev server at http://localhost:1313 (no search index)
just build           # hugo --minify + pagefind → public/
just serve-pagefind  # build and serve with working search
just test            # pytest
```

## Layout

| Path | What |
|---|---|
| `content/document/` | One markdown file per document: YAML metadata, human transcription as body |
| `content/*.md`, `content/news/` | Editorial pages and blog posts |
| `data/transcriptions_ai.json` | AI transcriptions keyed by Omeka ID |
| `data/transcription_dashboard.json` | Coverage stats for `/transcription-dashboard/` |
| `layouts/`, `static/` | Templates and theme assets |
| `scripts/` | Python tooling: Omeka fetch, image-list repair, dashboard |
| `_transcription/` | AI transcription pipeline (`claude -p`); see its README |
| `tests/` | pytest suite for the scripts |
| `redirects.caddy`, `Dockerfile` | Legacy URL redirects and the deployment image |

Document images are served from object storage (`mediaBaseURL` in `hugo.toml`), not from this repo.

## License

MIT © Roy Rosenzweig Center for History and New Media.
