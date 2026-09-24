# Linguini launch dashboard

Modelled on [Yangshun Tay's Docusaurus 2.0 launch dashboard](https://gist.github.com/yangshun/1e84ae8461975e7fa9a7d153621c3756): links, a timed run, tasks, after-launch tasks, the Product Hunt fields, then distribution lists. The blog copy at `/blog/launch-week` has the same checklist with tickable boxes; keep the two in step (`landing/components/blog/launch/Checklist.tsx`).

**Launch:** Saturday 17 October 2026, 00:01 PDT = **15:01 SGT**. US daylight saving ends on 1 November 2026. A launch after that date starts at 16:01 SGT.

## Useful links

- Landing page (Product Hunt primary URL): https://linguini-landing.vercel.app/
- Learner app: https://linguini-navy.vercel.app/
- Launch blog post: https://linguini-landing.vercel.app/blog/launch-week
- Product Hunt post: `[PH_POST_URL]` (fill in once the draft exists)
- Product Hunt copy, channel posts and reply bank: [product-hunt.md](product-hunt.md)
- Readiness audit, targets and go/no-go: [plan.md](plan.md)
- Media kit: [media/README.md](media/README.md)
- Analytics dashboard: `[DASHBOARD_URL]`
- Error logs and rollback: `[LOGS_URL]` · `[DEPLOYS_URL]`
- Support inbox owner: `[NAME]`

## Timeline (Singapore time, Saturday into Sunday)

| Time | Owner | What happens |
| --- | --- | --- |
| 14:00 | Incident lead | Fresh sign-up on a phone. Tap every landing button. Open dashboards and logs. |
| 15:01 | PH owner | Listing goes live on schedule. Post the first comment. Check gallery, video and link. |
| 15:10 | Outreach | One-to-one messages to people who asked to hear. X thread, Instagram post and story, LinkedIn. |
| 16:00–19:00 | Community | Answer every Product Hunt comment within the hour. Post in r/SideProject, the r/Spanish weekly thread and Discord promo channels. |
| 21:00 | Community | 9am Saturday on the US east coast. Second Instagram story. Reply to the new wave. |
| 01:00 | Incident lead | Hand over to one responder and one engineer on call. |
| 08:00 | Product lead | Check errors, sign-ups, demo completions. Second nudge in NUS class chats. |
| 14:59 | Everyone | Day ends. Screenshot numbers, thank commenters, list what broke. |
| Sun 15:00 | Product lead | Short retro. Assign fixes. |

If sign-up or lesson completion breaks for more than a few people: stop posting, put an honest note on the landing page, send people to the demo, fix and redeploy.

## Tasks

### Three weeks out (by 26 Sep)

- [ ] Agree the promise: browser demo open to everyone, learner app in beta
- [ ] Point every landing-page button at the production app, then tap each one on a phone
- [ ] Make every landing claim match the app today: photo analysis, speech, Plus trial
- [ ] Track demo started, demo finished, sign-up, first lesson, second lesson

### Two weeks out (by 3 Oct)

- [ ] Recruit 10 to 20 beta testers learning Spanish or French
- [ ] Watch five of them use it cold. Fix whatever confused two or more
- [ ] Draft the listing on a personal Product Hunt account and add every maker
- [ ] Upload the explainer to YouTube as unlisted, with `media/export/explainer.srt`

### One week out (by 10 Oct)

- [ ] Swap in the X header and LinkedIn cover (`media/export/banners/`)
- [ ] Reread the rules of every community below; message the r/Spanish mods
- [ ] Personal note to Lindie Botes and ten smaller language creators, with no ask to post
- [ ] Ask NUS Hackers for a Friday Hacks demo slot (active@nushackers.org)
- [ ] Schedule the listing for Sat 17 Oct, 00:01 Pacific

### Three days out (Wed 14 Oct)

- [ ] Countdown post (`countdown-1080x1080.png`) and story (`ig-story-countdown-1080x1920.png`)
- [ ] Tell friends and testers the date, and ask who wants a message on the day
- [ ] Write the duty rota: afternoon, night and morning shifts in Singapore time

### Day before (Fri 16 Oct)

- [ ] Go or no-go: buttons work, a stranger can sign up, analytics arrive, inbox staffed, someone can roll back
- [ ] Freeze the copy and the assets. No edits after this

### Launch day (Sat 17 Oct, 15:01 SGT)

- [ ] First comment up within a minute of going live
- [ ] X thread, Instagram post and story, LinkedIn out by 15:10
- [ ] Every Product Hunt comment answered within the hour
- [ ] Hourly check of errors, sign-ups and demo completions

## After launch

- [ ] Swap `[PH_POST_URL]` into every post, and add the Product Hunt badge to the landing page
- [ ] D+1: fix the onboarding bugs people hit on the day
- [ ] D+3: talk to five people who came back and five who didn't
- [ ] D+7: look at who did a second lesson; fix the biggest drop-off
- [ ] D+14: publish what we learned, with the real numbers
- [ ] Put the next launch on the calendar: real photo analysis

## Product Hunt

- Post: `[PH_POST_URL]` · Edit: `[PH_EDIT_URL]`
- Name: Linguini
- Tagline (≤60): Explore language lessons hidden in everyday photos
- Description (≤500): Explore photo scenes in Spanish or French through word cards, I-Spy and sentence games, then finish with a journal page. Try a complete interactive mini session in your browser and tell us what should make the leap into the learner app.
- Topics: Language Learning, Education, Productivity
- Thumbnail: `media/export/product-hunt-icon-240.png`
- Gallery (1270 × 760, in order): `01-your-world.png`, `02-find-your-words.png`, `03-play-and-build.png`, `04-keep-the-day.png`
- Video: YouTube link to `media/export/explainer.mp4` (`[YOUTUBE_URL]`)
- First comment: see [product-hunt.md](product-hunt.md#product-hunt-preview-launch-publishable-from-the-landing-experience)
- Rules we keep: self-hunt from personal accounts, ask for comments and never upvotes, no waitlist (Product Hunt won't feature one).

## Distribution

Sizes and rules checked 24 September 2026. Recheck each the week before; subreddit rules below came from a mirror because Reddit blocked our fetches.

### People who know us (first)

- [ ] Friends and classmates, one message each
- [ ] Beta testers
- [ ] CS3216 cohort chat

### Communities

- [ ] r/SideProject — self-promotion allowed; lead with how we built it
- [ ] r/languagelearning (3.4M) — resources thread only, or mod permission
- [ ] r/Spanish — weekly self-promotion thread; message mods first
- [ ] Discord: Refold Central (~37k), Language Learning Community (~34k), Language Cafe (~28k) — promo channels only
- [ ] Indie Hackers — one Show IH post, framed as a request for feedback
- [ ] NUS Hackers Friday Hacks — speaker slots until 13 Nov
- [ ] Show HN — **only after real photo analysis ships**; no sign-up walls, no vote requests

Not posting: r/French (no advertising), HelloTalk (bans promotion), Tandem (no public feed).

### Creators (personal note, no ask to post)

- [ ] Lindie Botes — YouTube ~357k; reviews language apps, UX designer, worked in Singapore
- [ ] Xiaomanyc — YouTube ~7.1M; speaks to strangers, closest fit to speak-first
- [ ] Matt vs Japan / Refold — comprehensible input
- [ ] Ten smaller tutors and study accounts (under 50k), chosen by audience fit

Not asking: Steve Kaufmann (founded LingQ) and Ikenna (runs Fluyo), both competitors.

### Newsletters (held until real photo analysis ships)

- [ ] The Rundown AI — 2M+, "tool of the day"
- [ ] TLDR AI — ~1.1M
- [ ] Ben's Bites — ~120–170k, submittable news feed

## Assets

| File | Use |
| --- | --- |
| `media/export/01…04-*.png` | Product Hunt gallery, 1270 × 760 |
| `media/export/product-hunt-icon-240.png` | Product Hunt thumbnail |
| `media/export/explainer.mp4` + `.srt` | Listing video, 50 s |
| `media/export/banners/x-header-1500x500.png` | X profile header from T−7 |
| `media/export/banners/linkedin-1584x396.png` | LinkedIn cover |
| `media/export/banners/launch-card-1200x630.png` | Link previews on the day |
| `media/export/banners/countdown-1080x1080.png` | T−3 feed post |
| `media/export/banners/ig-story-countdown-1080x1920.png` | T−3 story |
| `media/export/banners/ig-post-1080x1350.png` | Launch-day Instagram post |
| `media/export/banners/ig-story-1080x1920.png` | Launch-day story, link sticker in the clear area |
| `media/export/social-square.png` | Carousel slide 2 |

Regenerate banners with `python3 launch/media/banners.py`. The launch date is one constant (`LAUNCH`) at the top.
