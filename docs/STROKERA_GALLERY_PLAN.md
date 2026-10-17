# Strokera Gallery — Product & Delivery Plan

> Status: **Planned — development not started**  
> Owner: Strokera / RONGJING CULTURE（荣景文川）  
> First milestone: **Gallery v0.1 (public exhibition MVP)**  
> Updated: 2026-10-17

## 1. Product decision

Strokera Gallery is the first public-facing product of Strokera: a mobile-first online illustration gallery for original artworks, fashion-inspired visual studies, and character IP. Launch the **responsive website first**, make it installable as a **PWA** in a later iteration, and consider native iOS/Android apps only after validating user demand.

**Public promise:** art to explore, characters to discover, series to follow.  
**Internal promise:** published artworks are rights-cleared, traceable, controlled, and separated from source photographs and experimental masters.

Strokera remains an independent visual-production and research project. Do **not** replace, break, or couple the existing SPP 0.1 CLI, SVG/HTML render path, MATLAB research plan, or AWS image-processing pipeline to website launch.

### Non-goals for v0.1

- No public AI image generator/editor, paid subscriptions, e-commerce checkout, community feeds, or social user profiles.
- No required MATLAB, GPU worker, print-preflight, or SPP engine integration in the website's runtime.
- No public release of original photography, private intermediate files, quality reports, or full-resolution print masters.
- No store/app review submission or native app.

## 2. Target users and stories

1. **Visitor:** browse a curated home page, filter artworks by creative direction, open an artwork, share its URL, and browse a related series.
2. **Character/IP fan:** discover a character, read a short introduction/story, and browse its visual collection.
3. **Editor:** securely sign in, add artwork metadata, upload/attach exhibition derivatives, preview and publish or unpublish an artwork.
4. **Producer:** retain private provenance and source-permission records; prevent accidental display of unauthorized sources or unfinished work.

## 3. v0.1 information architecture

- `/`: editorial cover, featured artworks and featured characters/series.
- `/explore`: filterable artwork gallery; start with fixed categories, no complex search requirement.
- `/characters/[slug]`: character IP page with intro, cover, linked works (examples: 黑羽翎｜KUROHA, 南风绫｜NANORA, 花间醉). These are potential collections, not auto-published inventory.
- `/series/[slug]`: curated collections; can be hidden until populated.
- `/artworks/[slug]`: responsive image viewer, title, creative direction, character/series, short story/caption, attribution, shareable canonical URL; no public raw-master download.
- `/about`: Strokera and RONGJING CULTURE story, project link, contact pathway.
- `/studio`: authentication-protected internal content management. Never index or expose internal media.

Creative-direction taxonomy:
1. 极简时尚线描 / Minimalist Fashion Line Art
2. 极简美式／日式涂鸦 / Editorial Doodle
3. 极简悬空服装设计 / Floating Garment Studies
4. 极简单品拆解 / Garment & Item Studies

Artworks should be authored as **independently approved outputs referencing an authorized original**, never made by implicitly reprocessing an earlier generated work as the new source.

## 4. Visual direction

- Minimal gallery/editorial aesthetic: large images, generous whitespace, readable type, neutral light background and restrained **朱红色** accent.
- Images are the hero; avoid clutter, distracting animations, and generic AI-generation dashboard styling.
- Mobile-first layout; accessible controls and keyboard navigation; meaningful alt text; respect reduced-motion preferences.
- Exhibition visuals are optimized previews, preserving artist-approved cropping. Use responsive thumbnails, modern formats with fallbacks, and appropriate lazy-loading; do not stretch or modify approved artwork.

## 5. Suggested implementation architecture

Keep the existing Python package and `src/` untouched in v0.1.

```text
Strokera/
├─ src/                         # Existing Strokera / SPP Python engine (unchanged)
├─ tests/                       # Existing Python tests
├─ apps/
│  └─ gallery-web/              # NEW Next.js + TypeScript public gallery + private studio
├─ docs/
│  └─ STROKERA_GALLERY_PLAN.md  # This plan
└─ ...existing files
```

**Initial stack proposal:** Next.js (App Router) + TypeScript; simple server-side API actions/routes; PostgreSQL or an equivalently reliable managed relational store for content metadata; S3 private object storage for source/masters and exhibition assets; CDN for **approved public exhibition derivatives only**. Deploy front-end with a managed service (AWS-compatible approach preferred where practical), not on the GPU experiment instance.

Boundary rules:
- `Gallery` reads a publication catalog; it does not call AI generation, MATLAB, or GPU to render a page.
- Gallery content references a stable `artwork_id`, not an arbitrary S3 file path.
- Private assets require authenticated server-side access; publishing creates/assigns separately approved, optimized public derivatives.
- Uploads are admin-authenticated, MIME/size validated, and stored using server-authorized storage operations. Strip nonessential EXIF/geolocation from public derivatives.
- Keep all credentials in server-side secret configuration. Never expose storage keys in frontend bundles.

## 6. Data model (initial)

- **CharacterIP:** `id, slug, name_zh, name_intl, synopsis, cover_asset_id, status`
- **Series:** `id, slug, title, summary, cover_asset_id, character_id?, status, sort_order`
- **Artwork:** `id, slug, title, description, category, character_id?, series_id?, publish_status, rights_status, created_at, published_at, feature_rank?`
- **Asset:** `id, artwork_id?, kind(original|master|public_derivative|thumbnail|cover), storage_key, checksum, width, height, mime_type, visibility`
- **Provenance (private):** `artwork_id, source_reference, source_checksum?, authorization_note, tool_or_version?, reviewer?, approval_timestamp?`

Publish rules: an artwork cannot become public without a rights-clearance decision, a public derivative, approved metadata, and publication review. `DRAFT → IN_REVIEW → PUBLISHED → ARCHIVED`; unpublishing must remove it from public indexes and navigation. Keep private provenance out of public API responses.

The first implementation may simplify tables while keeping these concepts and boundaries explicit. Use migrations and stable IDs.

## 7. Delivery sequence

### P0 — V0.1: Public exhibition MVP

1. **Bootstrap and design system:** initialize isolated web app, responsive shell, typography, navigation, components, basic CI.
2. **Content schema and storage:** models/migrations, public catalog reads, S3 derivatives, sample seed records, publish gating.
3. **Private Studio:** protected editor sign-in, upload/attach assets, rights fields, create/edit/preview/publish/unpublish.
4. **Gallery browsing:** editorial home and category-based Explore; optimized responsive thumbnails, loading/empty states.
5. **Characters, series and artwork pages:** stable URLs, metadata, image viewer, basic related works and share affordances.
6. **QA and deployment:** staging/prod configuration, tests, accessibility, security, SEO, robots/sitemap, metrics, rollback and backup instructions.

**Editorial launch prerequisite:** manually curate a small set of rights-cleared exhibition derivatives. Development may use temporary sample data, but example/placeholder images must never be treated as licensed final published assets.

### P1 — V0.2: Retention and distribution

- PWA manifest, install experience and offline-friendly shell when appropriate.
- Better category/search discovery and multilingual content where justified.
- Optional private favorites/collections only after the privacy and user-account design is approved.

### P2 — V0.3: Commercial discovery

- Print editions or licensing inquiries, rights-aware contact forms, catalog/collection curation.
- No checkout or licensing transaction without explicit commercial and legal policies.

### P3 — V0.4+: Production integration

- Approved-artwork ingestion from the Strokera production manifest and processing workflows.
- Provenance/QC hooks and controlled republishing only after the production system has independently validated those capabilities.
- A native mobile app is **optional**, never a prerequisite for launching the gallery.

## 8. Definition of done for Gallery v0.1

- [ ] Home, Explore, artwork detail, CharacterIP, About work on phone and desktop.
- [ ] Works are navigable through stable shareable URLs; pages have appropriate title, description, OpenGraph image and meaningful alt text.
- [ ] Editors can sign in and create/preview/publish/unpublish artworks without direct database edits.
- [ ] Published images are limited to approved exhibition derivatives; source photographs and masters cannot be accessed by anonymous visitors.
- [ ] Rights-gating prevents unapproved artwork from publication.
- [ ] Loading, empty and error states are designed; slow image connections are handled.
- [ ] Accessibility checks, tests (critical journeys and publication safeguards), and baseline performance measurements pass documented thresholds.
- [ ] Deploy and rollback are documented; storage/database backup recovery steps are tested or explicitly documented as pending.
- [ ] Existing Python CLI, SPP 0.1 tests, and research files continue to work.
- [ ] At least a small curated, rights-cleared selection is published with working character/series links.
- [ ] Public site, not demo placeholders, is reachable at a confirmed deployment URL.

## 9. Handoff / implementation rules

- Before coding, inspect `README.md`, `docs/SPP-0.1.md`, `docs/PROJECT.md`, and the existing Python tests.
- Deliver one small PR per GitHub task, with screenshots (mobile/desktop), migration notes when relevant, and test evidence.
- Avoid direct edits to existing engine protocol contracts unless separately proposed and approved.
- Record hosting, storage and DB cost assumptions before allocating paid resources.
- Don't claim 'print ready', 'verified identical to source', or 'fully reproducible' for gallery images without the relevant experimental evidence.
- Art is the primary product surface; technology stays behind it.

## 10. Issue tracking

The GitHub parent issue `Strokera Gallery v0.1` is the coordination entrypoint. Implementation issues cover the six P0 workstreams. Follow-on P1–P3 work should stay a separate backlog and **must not block first launch**.
