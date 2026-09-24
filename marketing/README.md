# Linguini marketing

Launch materials for Product Hunt and social, kept separate from the app, API and landing site.

| Path | What it is |
| --- | --- |
| [`promo-video/`](promo-video) | The 30-second launch film: real footage, a focus frame that finds each object and names it in Spanish and French, and an original piano score cut to the edit |
| [`product-hunt/submission.md`](product-hunt/submission.md) | Everything to paste into the Product Hunt form: taglines, description, tags, maker comment |
| [`product-hunt/readiness.md`](product-hunt/readiness.md) | Go/no-go assessment and the must-fix list before launch day |
| [`product-hunt/launch-plan.md`](product-hunt/launch-plan.md) | Timeline, launch-day roles, reply templates, what we verified about Product Hunt's rules |
| [`product-hunt/social-posts.md`](product-hunt/social-posts.md) | X thread, LinkedIn, Telegram/WhatsApp, Instagram/TikTok, email |
| [`product-hunt/gallery/`](product-hunt/gallery) | Gallery images (1270×760), thumbnail and social card |

## Rendering the film

```sh
cd marketing/promo-video
pip install -r requirements.txt
npm install    # Playwright; Chromium must be available to it
./render.sh    # downloads the footage and piano samples, then writes out/linguini-launch*.mp4
```

[`promo-video/VIDEO.md`](promo-video/VIDEO.md) explains the edit and the pipeline, and [`promo-video/CREDITS.md`](promo-video/CREDITS.md) lists every clip and licence.

Gallery images are HTML compositions in `product-hunt/gallery-src/` built from 4× captures of the running landing page. The captures aren't committed; `capture.mjs` regenerates them from `landing/` on port 3200, then `render.mjs` and `thumb.mjs` export the PNGs and GIF.
