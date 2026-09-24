# Linguini marketing

Launch materials for Product Hunt and social, kept separate from the app, API and landing site.

| Path | What it is |
| --- | --- |
| [`promo-video/`](promo-video) | The launch film: an HTML animation rendered frame by frame and cut to the music |
| [`product-hunt/submission.md`](product-hunt/submission.md) | Everything to paste into the Product Hunt form: taglines, description, tags, maker comment |
| [`product-hunt/readiness.md`](product-hunt/readiness.md) | Go/no-go assessment and the must-fix list before launch day |
| [`product-hunt/launch-plan.md`](product-hunt/launch-plan.md) | Timeline, launch-day roles, reply templates, what we verified about Product Hunt's rules |
| [`product-hunt/social-posts.md`](product-hunt/social-posts.md) | X thread, LinkedIn, Telegram/WhatsApp, Instagram/TikTok, email |
| [`product-hunt/gallery/`](product-hunt/gallery) | Gallery images (1270×760), thumbnail and social card |

## Rendering the film

```sh
cd marketing/promo-video
npm install                        # Playwright; Chromium must be available to it
python3 -m http.server 8091 --directory ../..   # serve the repo root in another terminal
npm run render                     # writes out/linguini-launch.mp4
```

Gallery images are HTML compositions in `product-hunt/gallery-src/` built from 4× captures of the running landing page. The captures aren't committed; `capture.mjs` regenerates them from `landing/` on port 3200, then `render.mjs` and `thumb.mjs` export the PNGs and GIF.

`film.html` + `film.js` describe every frame as a function of time; open `film.html?t=30` in a browser to scrub. Scene boundaries and beat positions come from `timing.json`, which is derived from `audio/beats.json`, so cuts land on the music. Sound effects are placed from the cue sheet the page exports (`cues.json`). Music and sound credits are in `audio/CREDITS.md` and must go in the video description wherever the film is posted.
