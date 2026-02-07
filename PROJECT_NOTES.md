# Kinghermy Blog – project map

Quick reference so we don’t have to rediscover structure next time.

## Stack & routing
- Astro 5 with Tailwind 4 (via `@tailwindcss/vite`), MDX enabled.
- Base path `/kinghermy-blog` set in `astro.config.mjs` and `src/consts.ts`; `SITE_BASE` used in links/components.
- Pages: `src/pages/index.astro` (home), `src/pages/blog/index.astro` + `[slug].md`, `src/pages/projects.astro`, `src/pages/about.astro`, `src/pages/admin.astro` (local draft helper), `src/pages/rss.xml.js`.
- Layouts: `src/layouts/BaseLayout.astro`, `src/layouts/BlogPostLayout.astro`.

## Content & assets
- Posts live in `src/content/blog/*.md`; schema in `src/content/config.ts`.
- Cover images: `src/assets/blogimages/<slug>/cover.jpg`; loaded by `BlogCard.astro` and `BlogPostLayout.astro` via `import.meta.glob`.
- Global styles/theme toggles: `src/styles/global.css`, `src/components/ThemeSelector.astro`; fonts imported in `BaseLayout`.

## Build/run
- Install: `npm install`
- Dev: `npm run dev`
- Build: `npm run build` (runs `astro check` first)
- Preview: `npm run preview`

## Plugins & metadata
- `src/plugins/remark-reading-time.mjs` sets `minutesRead` via `reading-time`.
- `src/plugins/remark-modified-time.mjs` now falls back to file mtime if git history unavailable; sets `lastModified` when possible.
- Social links/nav in `src/consts.ts`; update base links here.

## Notable details
- “Suggest an edit” link in `src/layouts/BlogPostLayout.astro` points to `hermy10/kinghermy-blog`.
- Admin page is a client-side helper only; no backend/CMS. Access code lives in `src/pages/admin.astro` (`ACCESS_CODE`).
- RSS uses `SITE_BASE` trimming; sitemap enabled in `astro.config.mjs`.

## Tools directory
- `tools/alfa-scout`: Python CLI for Alfa AWUS036ACM surveys/captures (requires `iw`, `ip`, `tshark`, `nmcli`, sudo). Outputs to `tools/alfa-scout/reports/`.
- `tools/lab-queue`: Python CLI queue with JSON store `tools/lab-queue/db.json` and Markdown export.
