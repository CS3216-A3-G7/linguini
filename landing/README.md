# Linguini landing page

The public marketing site for Linguini. It is a Next.js 16 App Router project that lives apart from the learner app (`frontend/`) and the API (`backend/`), so it builds and deploys on its own.

## Run it

```sh
npm ci
npm run dev      # http://localhost:3000
npm run lint     # oxlint + TypeScript
npm run build    # production build, also pre-renders the OG images
```

Copy `.env.example` to `.env.local` to point the site at real URLs:

| Variable | Used for |
| --- | --- |
| `NEXT_PUBLIC_SITE_URL` | Canonical URL, sitemap and absolute OG image links. On Vercel it falls back to the production domain. |
| `NEXT_PUBLIC_APP_URL` | Where “Start learning” and “Log in” go. Production builds (including Vercel) default to the live app, https://linguini-navy.vercel.app; development uses `http://localhost:5173`. |

Live at https://linguini-landing.vercel.app (Vercel project `linguini-landing`, **Root Directory** `landing`).

## What’s inside

- **Interactive demo** (`components/try/`): pick a real photo, watch it get “analysed”, then play through word cards, I-Spy, a fill-in-the-blank and a sentence builder before the day is saved as a journal entry. Lesson content for each photo, in Spanish and French, is in `data/scenes.ts`.
- **SEO**: semantic sections with one `h1`, per-page metadata, `robots.txt`, `sitemap.xml`, a web manifest and JSON-LD (Organization, WebSite, SoftwareApplication with Free/Plus offers, FAQPage).
- **Social previews**: Open Graph and X cards made with `next/og` (`app/opengraph-image.tsx`). `app/og/route.tsx` renders a dynamic journal-page card, and `/share?photo=…&lang=…&words=…` uses it so a finished demo session can be shared with its own preview.
- **Blog** (`app/blog/`, `components/blog/`): the three newest posts sit below the final call to action. Post metadata is in `data/posts.ts` and each body is a component in `components/blog/posts/`. Interactive charts and the animated lesson walkthrough live in `components/blog/interactive/`; their numbers come from `business-model/model/cost_model.py`. The main post's looping cover video is rendered with `python3 scripts/render-post-video.py` (Pillow and ffmpeg). A post with a `pdf` path offers a download; regenerate it after editing with `NEXT_PUBLIC_SITE_URL=https://linguini-landing.vercel.app npm run build && npm start`, then `node scripts/export-post-pdf.mjs` in another terminal (needs Google Chrome).
- **Launch film** (`components/Film.tsx`): the 30-second real-footage film, shown right under the demo. It loops muted while on screen (browsers block autoplay with sound), and "Sound on" restarts it with the score. Reduced-motion visitors see the poster. Desktop gets the 1080p file and phones get the 720p one. The files in `public/film/` are copies of `marketing/promo-video/out/`, so copy them again after a re-render. The poster is the frame at 12.4 s: `ffmpeg -ss 12.4 -i linguini-launch.mp4 -frames:v 1 -q:v 3 public/film/poster.jpg`.
- **Share widgets**: `components/ShareBar.tsx` builds share links for X, WhatsApp, Telegram, LinkedIn and Facebook, plus the native share sheet and copy link. It loads no third-party scripts.

## Assets

- Brand wordmark, mascot and pasta avatars are copied from `frontend/public/`. Edit the originals there, then re-export them here.
- Every photo in `public/photos/` is a real photograph, not AI-generated. Each one's source repository, commit date and licence notes are in `public/photos/credits.json`, which the `/credits` page displays.
