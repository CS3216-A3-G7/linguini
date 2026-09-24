# Linguini launch dashboard

**Recommendation:** use a small, supervised learner beta now; schedule a public Product Hunt launch only after the gates below pass. The tentative public slot is **Saturday, 17 October 2026, 00:01 Pacific Daylight Time (15:01 Singapore time)**. A Databox analysis of 2026 launches found Saturdays have about a third as many launches as Tuesdays, and Product Hunt reports 15% more visit clicks on weekend launches; for a small network, that trade favours Saturday. [Databox](https://www.producthunt.com/p/databox/i-ve-analyzed-all-2026-ph-launches-to-find-the-best-day-to-launch) · [Preparing for launch](https://www.producthunt.com/launch/preparing-for-launch) This is a planning target, not a booked launch or a claim that the learner app is ready. Product Hunt runs on Pacific 24-hour launch days and recommends 12:01 a.m. Pacific when the team can cover the day. [Product Hunt posting guide](https://help.producthunt.com/en/articles/479557-how-to-post-a-product) · [Product Hunt launch guide](https://www.producthunt.com/launch)

The primary goal is **learners who complete a lesson and return**, not a leaderboard position. A public interactive demo can collect useful feedback immediately, but a public promise that people can upload any photo and get a fully generated lesson would outrun the current backend: uploaded photos currently receive explicitly labeled sample object suggestions; real image analysis, AI generation and speech evaluation remain unimplemented. The app has Supabase login and image upload paths in the current code and backend README, but these need production end-to-end verification. The older `frontend/README.md` describes an earlier implementation, so use `backend/README.md` and a live smoke test when approving claims.

## Current readiness audit (24 September 2026)

| Item | Evidence | Decision |
| --- | --- | --- |
| Landing page | `https://linguini-landing.vercel.app/` returns HTTP 200; it has an interactive, curated-photo demo, Spanish/French content, branded OG cards and share pages. | Usable as the primary Product Hunt destination after copy/links are reconciled. |
| App destination | `https://linguini-navy.vercel.app/login?mode=signup` returns HTTP 200. Production landing HTML currently renders signup/login/Plus links to `http://localhost:5173/login...` because `NEXT_PUBLIC_APP_URL` is unset in that deployment. A source-level fallback fix is being prepared; production deployment remains pending. | **Hard no-go:** deploy the fix or set the production app URL, then click every CTA on mobile and desktop. HTTP 200 alone does not prove signup works. |
| Landing claims | Current page describes automatic photo analysis, pronunciation feedback, daily free plan, Plus trial and prices. Backend documents placeholder analysis and no speech grading. | **Hard no-go:** verify or revise each claim before directing a broad audience here; never charge or advertise a trial that cannot be fulfilled. |
| Funnel measurement | Landing source has no first-party analytics events for demo completion, CTA click or signup handoff; app HTML loads Contentsquare, but that does not establish a measured funnel. | Instrument privacy-aware events and verify them in the live dashboard before launch. |
| Support and privacy | Photo uploads involve personal images; landing has photo credits, but the public support route, user-photo explanation and response owner need review. | Assign an inbox owner and verify privacy/support links, retention/deletion wording and escalation path. |

## Why this launch mode

A pure invite-only Product Hunt announcement would create demand the team cannot immediately satisfy. A fully open app announcement would expose unverified signup links and current placeholder capabilities. Run a **10–20 person supervised beta** with consenting learners first, using access to test the real app. Then launch publicly with the **landing demo open to everyone** and a clearly labeled app availability state: open signup only if the gates pass; otherwise describe the product as a preview/beta, use Product Hunt's availability status, and invite feedback on the demo without promising full access. Do not invent a waitlist or call the landing demo an AI photo analyzer. Product Hunt explicitly supports beta/not-yet-available status. [Posting guide](https://help.producthunt.com/en/articles/479557-how-to-post-a-product)

## Launch goals and definitions

Set final numeric targets after the beta establishes a baseline. Suggested first-launch targets below are **team goals**, not forecasts or externally publishable claims.

| Measure | Target for first 14 days | Definition / source |
| --- | --- | --- |
| Qualified visits | 300 | Unique visits to the landing page from Product Hunt and relevant community links, split by UTM source. Exclude internal testers. |
| Demo activation | 30% of qualified visits | Starts a curated-photo demo and reaches its saved journal ending. Record `demo_started`, `demo_completed` with scene/language only. |
| App signup conversion | 10% of qualified visits, **only if signup is open** | Verified Supabase account and first app page loaded; attribute via first-party anonymous referral/UTM, with consent where needed. |
| First-lesson activation | 50% of new verified learners, **only if app is open** | A learner completes one session. Report both preloaded and uploaded-photo cohorts. |
| D7 learner retention | 20% of first-lesson learners, **only if app is open** | Learner completes a second session on days 1–7 after first completion. Report cohort size and numerator, not just percentage. |
| Feedback loop | 15 substantive reports | A learner describes a task, confusion, bug or useful insight; dedupe and tag by theme. |

Track landing `visit → demo_started → demo_completed → app_cta_clicked → signup_verified → session_completed → second_session_completed`; also track upload failure and session error rates. Keep image contents, raw speech, journal text and email addresses out of analytics events. Use server events for persisted sessions; client events alone may be blocked or duplicated. Review conversion by device, language, source and preloaded-vs-uploaded cohort. Use tagged links such as `?utm_source=producthunt&utm_medium=launch&utm_campaign=linguini_launch`; check that app handoff preserves attribution.

## Critical path and owner board

Assign one named human to each role before scheduling. A single teammate may hold more than one role, but **incident lead and community responder need separate coverage during peak hours**. This follows the useful structure in [Yangshun's Docusaurus 2.0 dashboard](https://gist.github.com/yangshun/1e84ae8461975e7fa9a7d153621c3756): links, minute-level timeline, assets, outreach, and after-launch tasks in one place.

| Due | Owner role | Task / acceptance check |
| --- | --- | --- |
| T−19 to T−14 | Product lead | Choose exact launch promise and audience. Compare landing, app and backend behavior; resolve Plus, AI and pronunciation claims. Decide whether app signup is open or demo-only beta. |
| T−19 to T−14 | Engineer | Set `NEXT_PUBLIC_APP_URL=https://linguini-navy.vercel.app` in the landing deployment, redeploy and prove every CTA reaches the correct route. Confirm production API, Supabase signup/email confirmation, browser permissions, upload and return visit on mobile and desktop. |
| T−14 to T−10 | Beta lead | Recruit 10–20 known learners, ideally beginners/returners in Spanish and French. Observe: understand the pitch, finish demo, sign up, finish a session, return within a week. Record consented feedback and failure counts. |
| T−14 to T−7 | Analytics owner | Instrument and test the funnel above; create a single live dashboard with error rate and source breakdown. Establish baseline from beta. |
| T−14 to T−7 | Marketing owner | Review the submission copy, first comment, gallery, demo video and channel posts in this launch kit against the actual app. Have two people who did not build Linguini explain the first gallery frame back to the team. Revise once based on confusion. |
| T−10 to T−5 | Maker / Product Hunt owner | Use an established **personal** Product Hunt account, complete onboarding, create a draft, add makers and preview the listing. New accounts require onboarding and may need a week before posting. Select only relevant topics. [Posting guide](https://help.producthunt.com/en/articles/479557-how-to-post-a-product) · [Before launch](https://www.producthunt.com/launch/before-launch) |
| T−7 to T−3 | Outreach owner | Build a consent-aware contact sheet: name, channel, relationship, relevance, planned asset, status and owner. Ask collaborators and beta testers for candid feedback; prepare personalized, unsent notes for creators and moderators. |
| T−3 to T−1 | Incident lead | Freeze launch copy/assets, record links to dashboard, deployment, rollback, logs, support inbox and status page. Run a load check and backup/recovery check appropriate to expected traffic. Create a duty roster spanning the Pacific launch day. |
| T−1 | Product lead | Run go/no-go below. Schedule Product Hunt post only after all hard gates pass. Make a screenshot of the final listing preview for team sign-off. |

### Go / no-go at T−1

**All must pass:** (1) every production CTA reaches a usable destination; (2) a new person can sign up, verify email if required, complete the advertised path and return; (3) public copy, pricing and beta status match behavior; (4) analytics events and error monitoring arrive live; (5) support inbox and two launch-day responders are staffed; (6) gallery assets render and have rights/credits; (7) a rollback/redeploy owner is available. If any fail, keep the Product Hunt draft and do a smaller preview with known testers. Reschedule rather than push traffic into a broken journey.

## Launch-day runbook — 17 October target (Singapore time)

Product Hunt's day begins **15:01 SGT / 00:01 PDT**. Replace times if the date changes across a daylight-saving boundary. Schedule the Product Hunt draft; do not rely on a manual race to publish. Product Hunt recommends self-posting with a personal account, a first comment and a direct product URL. [Posting guide](https://help.producthunt.com/en/articles/479557-how-to-post-a-product)

| Time SGT | Lead | Action |
| --- | --- | --- |
| 14:00 | Incident lead + product lead | Check landing/app/API health; repeat fresh-user mobile smoke test; open logs, traffic and support dashboard. Confirm CTA and pricing state. |
| 15:01 | Maker | Confirm Product Hunt post is live, first comment is present, gallery/video work and primary link opens the correct landing page. Claim/request Product Page management. |
| 15:10–16:00 | Outreach lead | Share the direct post link with close contacts who opted to hear launch news; publish coordinated owned social posts. Invite visits, comments and feedback. **Never ask for upvotes or coordinate fake engagement.** [Launch guide](https://www.producthunt.com/launch) |
| 16:00–19:00 | Community responder | Reply to Product Hunt questions with product facts and concrete examples. Publish in suitable communities only where rules permit self-promotion, with a discussion prompt tailored to that community. |
| 15:00–next day 15:00 | Incident lead | Check error rate, signup, demo completion and support queue at least hourly during high traffic; triage P0/P1 immediately. Keep an incident log and rollback decision. Rotate responders for overnight Pacific hours. |
| Next day 15:00 | Product lead | Capture traffic, activation, support themes and defects; thank contributors; publish an honest update and assign next fixes. |

Incident policy: if signup or session completion fails for more than a few users, pause outbound posts, show an accurate availability note on the landing page, route visitors to the working demo, and fix/redeploy with the incident lead. Do not silently funnel users to an error state. The Product Hunt launch dashboard provides comments and performance tracking, and the permanent Product Page should be claimed for follow-up. [Launch-day duties](https://www.producthunt.com/launch/launch-day-duties)

## Distribution map

The strongest asset is a **short, real screen recording** of a curated photo going from words to I-Spy to a journal page, with captions and a clear demo label. Pair it with the gallery images and written copy in the launch kit. Every channel should lead to the same Product Hunt post on launch day, while the Product Hunt primary link leads to the landing page. Preserve the specific communities' posting rules and adapt the opening question; do not dump one identical announcement everywhere.

| Priority | Channel | Angle / ask | Owner action |
| --- | --- | --- | --- |
| 1 | Team's friends, classmates, former project testers and language-learning contacts | “Try a five-minute Spanish/French photo lesson and tell us where you got stuck.” | Ask individually for honest use and comments, without upvote requests. Secure permission before naming anyone. |
| 1 | Existing social accounts: Instagram Reels/Stories, TikTok, X, LinkedIn and Facebook | 15–30 second visual lesson loop, one scene and one word; carousel or short post links to demo. | Record native aspect ratios; use an actual app/demo capture; post launch link and answer replies. |
| 2 | Language-learning communities on Reddit, Discord and Facebook | Ask whether learning from one's own surroundings helps word recall; show an example and invite critique. | First identify active communities and read each rule/mod guidance. Post only in feedback or showcase spaces where allowed; participate before asking attention. |
| 2 | Student, campus, maker and education communities | A student-built language-learning experiment and what testers taught the team. | Ask organizers/moderators to approve a relevant showcase; offer a short live demo. |
| 2 | Micro-creators: language tutors, study accounts, travel photographers, “learn Spanish/French” creators | Offer a test session and ask for independent feedback if it fits their audience. | Curate 10–15 relevant creators by audience fit, not follower count; make no scripted endorsement or paid upvote arrangement. |
| 3 | Hacker News `Show HN`, Indie Hackers and maker forums | Product and implementation story, framed honestly as an interactive prototype/beta. | Use only when there is a working product and a technical/product insight; answer questions rather than cross-posting a sales blurb. |

Do not assume an influencer or community has agreed to post. The outreach sheet must record a confirmed response before any coordinated mention. Product Hunt permits sharing a launch link, but prohibits direct upvote requests; paid promotion of hunters or artificial engagement can result in removal. [Launch guide](https://www.producthunt.com/launch) · [Before launch](https://www.producthunt.com/launch/before-launch)

**Concrete community shortlist, checked 24 September:** The [r/Spanish weekly self-promotion thread](https://www.reddit.com/r/Spanish/comments/1wl7pbz/weekly_selfpromotion_mega_thread/) explicitly accepts language-learning apps; post one honest comment in the *current* weekly thread. [r/languagelearning](https://www.reddit.com/r/languagelearning/comments/1u537kp/announcement_we_are_tightening_the_rules_around/) requires moderator permission for promotion outside its “Share your resources” thread and clear labeling. [Show HN](https://news.ycombinator.com/showhn.html) is suitable only when visitors can try the working project; its guidelines reject a landing page or signup-only pitch and prohibit soliciting votes. Recheck each venue's rules immediately before posting. Use team members' existing Discord, campus and creator relationships only after identifying a relevant space and its posting policy.

## Retention and next announcement

The first week should help learners experience the **second** useful lesson. At session completion, give one clear next step: save a journal line and choose tomorrow's scene. If consent and messaging infrastructure exist, send one helpful day-two reminder tied to their chosen language; offer an easy unsubscribe. Do not build a generic daily email blast around an unverified streak claim. Give people a way to report a wrong word or confusing lesson from the experience itself.

At **D+1**, fix broken onboarding or upload flows and reply to every substantive Product Hunt comment. At **D+3**, interview five activated and five stalled users, comparing what they expected with what the demo/app delivered. At **D+7**, review first lesson, second lesson, D7 retention, language and source cohorts; choose the largest drop-off to fix. At **D+14**, publish a small “what we learned / what changed” update with actual numbers and caveats, continue Product Page replies, and put the next product release on the calendar. Product Hunt recommends following up with users, using feedback and maintaining the Product Page after the launch day. [Post-launch guide](https://www.producthunt.com/launch/days-after-launch)

Candidate next announcement, conditional on shipping: **real photo analysis with learner-approved vocabulary**. A later pronunciation release should only be promoted after speech evaluation is truly available. Product Hunt supports launching significant new iterations, not repeated copies of the same listing. [Launch guide](https://www.producthunt.com/launch)
