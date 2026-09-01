# SPEC.md

> For technical implementation details, see [AGENTS.md](./AGENTS.md).

---

## Overview

The **Papers of the War Department** (PWD) is a digital archive of documents from the U.S. War Department, 1784–1800, whose originals were destroyed by fire in 1800. The Roy Rosenzweig Center for History and New Media (RRCHNM) at George Mason University reconstructed the collection from copies held in repositories across the country.

The original site ran on Omeka S (PHP/MySQL) with a Scripto crowdsourced transcription tool. This project is its **Hugo static site** successor: no server, database, or PHP runtime. It preserves ~42,880 documents, ~25 editorial pages, and 240 news posts; serves document images from object storage; provides full-text search; and adds AI-generated transcriptions for documents that volunteers never transcribed.

**Audience:** researchers, historians, educators, and students of early American military and government history.

**Goals (all met):**
- Preserve all document content and metadata in a server-free format
- Keep old Omeka URLs working via web-server redirects
- Browse by author, recipient, collection, repository, and document type
- Full-text search across documents, guides, and news
- Show human and AI transcriptions side by side, with a public methodology page and progress dashboard
- Deploy from a container on CHNM infrastructure

---

## Users & Roles

Read-only public archive; no accounts.

- **Public visitor**: browse, search, view documents and transcriptions, read guides and news.
- **Site maintainer**: edits content markdown or re-runs fetch scripts, runs `just build`, pushes to `main`/`preview` to deploy.

---

## Business Rules

### URL compatibility
- Legacy Omeka URLs under `/s/home/…` (items, pages, browse) 301 to Hugo paths via `redirects.caddy`, applied at the web server. Documents carry no per-page Hugo aliases.
- Editorial pages keep `/s/home/page/{slug}` aliases; news posts keep `/news/?p={id}` aliases.
- Removed item types (Image, Name, Microfilm, Publication) and the Scripto transcription tool 404.

### Data integrity
- Items come from the Omeka S REST API, never from scraped HTML.
- Multi-valued fields are whitespace-stripped.
- Human transcriptions live in the document's markdown body; AI transcriptions in `data/transcriptions_ai.json`.
- A document's `images:` list is the ordered slice of its shared microfilm reel; several repair passes established these from reel structure and the legacy site's viewers.

### Content model
- One item type with pages: **Document** (~42,880).
- Collections and repositories are metadata on documents and browsable as taxonomies; they have no pages of their own.
- Six taxonomies: authors, recipients, collections, repositories, doc_types (documents); categories (news).
- Notable persons/locations/items are displayed on documents but are not browsable indexes.

### Editorial pages
- ~25 pages fetched from Omeka and converted to markdown; internal links rewritten to Hugo paths.
- Every page shows the CHNM sustainability banner ("static copy of the final website") above the header.
- Pages that describe retired features (Scripto accounts, transcribing, dashboards) are flagged `outdated: true` and render a notice.

---

## Features

### Document browse and taxonomy browse
Paginated lists (25 per page) with thumbnails at `/document/`, and per-term lists at `/authors/{slug}/`, `/recipients/`, `/collections/`, `/repositories/`, `/doc_types/`. Taxonomy index pages list all terms with counts.

### Document detail
`/document/{id}/`: title, description, date, linked authors/recipients/collection/repository/doc type, sent-from, document number, notable persons/locations/items, an image viewer (large images with original download from object storage), and a tabbed transcription panel (human / AI).

### Search
Pagefind index built after each Hugo build, covering documents, guides, and news. `/search/` offers a Documents vs. Guides & News toggle, `?q=` and `?type=` URL parameters, and 25 results per page.

### AI transcription
30,479 documents have Claude-generated transcriptions (complete). `/transcription-methodology/` explains the approach; `/transcription-dashboard/` reports coverage per collection (human only / AI only / both / neither).

### News
240 posts from the project's WordPress blog with author, date, categories, category term pages, a sidebar, and an archive page.

### Editorial pages
About, guides, teaching resources, paleography, citation, project history, etc.

---

## User Flows

**Browse by taxonomy:** taxonomy index → term page (paginated documents) → document detail.

**View a document:** arrive via browse, search, taxonomy, or a legacy URL redirect → read metadata → page through images → read human or AI transcription → follow linked author/collection.

**Search:** `/search/` → enter terms, pick Documents or Guides & News → results link to detail pages.

---

## Out of Scope

- Scripto crowdsourced transcription, user accounts, contributions, watchlists (require a server)
- Omeka admin and dynamic faceted search
- IIIF deep-zoom viewer (the static viewer shows large images with original download)
- Pages for Image, Name, Microfilm, Publication, Collection, or Repository items

## Open Items

None. Roughly 12,300 documents have no transcription of either kind; that is expected (no usable images, content-filter refusals, or page caps) and not tracked as work.

---
*Last Updated: 2026-09-01*
