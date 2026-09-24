# Product Hunt readiness: go / no-go

*Assessed 24 September 2026 from the repository and the live sites.*

## Verdict

**Not today. Launch on Wednesday 14 October 2026 (3:01 pm SGT) as a free product, after must-fix items 1 to 5 below.**

The product itself is ready for Product Hunt. The concept is distinctive, and the demo lets anyone try it in under a minute without signing up. What's missing is the trust layer around it. The landing page offers a paid plan nobody can buy, there is no privacy policy for an app that uploads personal photos to an AI provider, there's no way to contact us, and the licences for most landing-page photos are unconfirmed. All of that can be fixed in two weeks, and each gap would come up in the first hour of comments. Launch day is hard to redo, so it's worth waiting for.

If the date has to slip, move it rather than launching with items 1 to 4 still open. A launch can be scheduled up to 30 days ahead, so pick a new date from the Pre-Launch Dashboard.

---

## What's strong

- **A demo that needs no sign-up.** The landing page runs a real session on real photos. Product Hunt visitors can try the idea straight away, which the featuring guidelines reward ("immediate access").
- **A concept that's clear in one line.** "Your camera roll is the textbook" is novel and easy to repeat, and it isn't one more AI chatbot tutor. It fits Product Hunt's "Novel" and "Creative" criteria.
- **The learner stays in charge.** The AI suggests words, and you untick or add before every session. That's a good answer to "is the AI accurate?" and it's already built.
- **A polished landing page.** Open Graph images, share cards, FAQ, how-it-works, a journal wall, a photo-credits page, and a consistent pasta brand from mascot to streak to avatars.
- **Works in the browser, nothing to install.** Phone, tablet or laptop. Nobody gets turned away for being on the wrong platform.
- **The live wiring works.** On 24 September the landing page's "Start free" and "Log in" buttons pointed at `https://linguini-navy.vercel.app/login?mode=signup` and `/login`, and both sites returned 200.

## Blockers and risks

| # | Issue | Evidence | Severity |
|---|---|---|---|
| 1 | **The pricing page offers a Plus plan you can't buy.** The page shows US$6.99/mo or $59.88/yr and a "Try Plus free for 7 days" button, but billing doesn't exist. The button goes to `…/login?mode=signup&plan=plus-yearly`, and the app ignores the `plan` parameter. The FAQ says Plus "adds unlimited sessions, pronunciation feedback and review mode", but pronunciation feedback and export aren't built. Structured data (`JsonLd.tsx`) also advertises a US$6.99 offer to search engines. | `landing/components/Pricing.tsx:81–91`, `landing/data/faq.ts`, `landing/components/JsonLd.tsx:54–70`, `frontend/src/pages/Login.tsx` (no plan handling) | **Blocker.** Product Hunt users will click it, and that breaks trust on day one |
| 2 | **No privacy policy or terms.** `/privacy` returns 404. The app stores email addresses and personal photos and sends photos to a third-party AI vision provider (OpenAI by default). We found no account-deletion flow; journal entries can be deleted. | `curl https://linguini-landing.vercel.app/privacy` returned 404; `backend/app/config.py` `VISION_PROVIDER`; `backend/app/api/routes/journals.py` (delete route only) | **Blocker.** Photo privacy will be one of the first questions, and many users, directories and app stores expect a policy link |
| 3 | **No support or contact channel.** The FAQ and footer send people to the GitHub repository. There's no email address and no password-reset flow in the app, so a locked-out user has no one to ask. | `landing/components/Faq.tsx:13`, `landing/components/SiteFooter.tsx:30`, `frontend/src/pages/Login.tsx` (no reset) | **Blocker** for a public launch |
| 4 | **Most landing-page photo licences are unconfirmed.** All 11 demo photos come from MIT-licensed theme repositories, but the MIT licence covers the code, not necessarily the photos. Our own credits file records "original photo licence not stated" or "likely Unsplash" for 9 of them, and "verify before launch" for the 2 picjumbo photos. These photos appear in the hero, the demo, the OG images and the gallery. The launch film no longer uses them: it's all Mixkit footage under the Free licence (see `marketing/promo-video/CREDITS.md`). | `landing/public/photos/credits.json` | **Blocker** for the gallery. **High risk** for the landing page |
| 5 | **App stability and cost under a traffic spike are unknown.** We have no usage history, and we found no error monitoring or analytics in `frontend/` or `landing/`. Every session calls a paid AI vision API, and the backend has rate-limit error handling, which shows limits exist. | `backend/app/ai/model_errors.py`; nothing in `package.json` for analytics or monitoring | **High.** A launch-day outage is the worst possible outcome |
| 6 | **Accessibility hasn't been audited.** We haven't checked keyboard paths, contrast on the pasta palette, screen-reader labels on photo markers, or the fallback when there's no microphone. I-Spy phase 2 has a text input, which helps. | `frontend/src/pages/ISpyPhase2.tsx`, `MicTest.tsx` | Medium |
| 7 | **The "one photo session a day" free limit** is promised on the pricing page. We found no enforcement in the code. That's fine for users, but don't repeat the claim until someone confirms either way. | `landing/components/Pricing.tsx`; nothing found in `backend/` | Medium (copy accuracy) |
| 8 | **Only two languages (Spanish and French from English).** Expect "when is X coming?" in the comments. The FAQ says "Italian is next", so only keep that if it's a commitment. | `landing/data/faq.ts` | Low. Be upfront about it; don't hide it |
| 9 | **No social login.** Email and password only adds friction for Product Hunt visitors. The no-signup demo mostly makes up for it. | App login page | Low |
| 10 | **The app URL setting can silently fall back.** `landing/lib/site.ts` falls back to `http://localhost:5173` if `NEXT_PUBLIC_APP_URL` is missing at build time. It's correct in production today, but one bad deploy would break every CTA. | `landing/lib/site.ts` | Low, but check after every deploy |
| 11 | **No real users or reviews yet.** That's fine for Product Hunt, as long as we don't claim any. Getting 10 to 20 people outside the team through a full session before launch will surface bugs early. | — | Low |

## Must-fix before launch day, ranked

1. **Make pricing honest.** Mark Plus as "Coming soon" with no price button (or keep the price with a "notify me" link), remove "Try Plus free for 7 days", reword the FAQ so pronunciation feedback and review mode are "coming to Plus", and remove the paid `Offer` from `JsonLd.tsx`. On Product Hunt, pricing stays **Free**. *(About half a day.)*
2. **Publish a privacy policy and terms,** at `/privacy` and `/terms` on the landing page, linked from the footer and the app's sign-up screen. Cover what we collect (email, photos, learning history), that photos go to the AI vision provider (name the provider and summarise its retention terms), that photos are never shown to other learners, and how to delete an entry or your whole account. If there's no account-deletion button yet, give an email address that handles deletion requests. *(1–2 days, including a team read-through.)*
3. **Add a support email,** such as a shared team inbox, to the FAQ, the footer and the app's login screen, replacing the GitHub link as the contact. Decide how password resets will be handled for launch: build a flow, or handle them manually through support. *(Half a day to 2 days.)*
4. **Replace or confirm every landing-page photo.** The quickest option is our own photos, which also fits the "real places" story. Otherwise, use Unsplash or Pexels photos with the source URL and photographer recorded in `credits.json`. Anything in the Product Hunt gallery, thumbnail or video must be fully cleared. *(1–2 days, including re-marking the object positions for the demo.)*
5. **Launch-day hardening.** Do a full end-to-end rehearsal on phones. Set a spending cap and alerts on the AI provider account and confirm its rate limits. Add uptime and error alerts. Add simple analytics (for example Vercel Web Analytics) to the landing page and the app, so we can measure the launch. *(1–2 days.)*
6. **A quick accessibility pass:** keyboard through the demo, contrast on buttons and word markers, alt text and aria labels on photo markers, and a typed fallback wherever a microphone is needed. *(1 day.)*
7. **Do before launch if there's time:** 10–20 outside testers, and a check on whether the daily free-session limit exists (then fix the copy to match).

Items 1 to 5 are the launch gate. Items 6 and 7 should be done, but they shouldn't move the date.

## Go / no-go check on T−1 (Tue 13 Oct)

Launch only if every answer is yes:

- [ ] Nobody can find a "buy" or "trial" button for Plus anywhere on the landing page or in the app.
- [ ] `/privacy` and `/terms` are live and linked from the landing footer and the app's sign-up screen.
- [ ] A support email is on the landing page, and someone checks it on launch day.
- [ ] Every image in the Product Hunt gallery, thumbnail and video has a confirmed licence or is our own.
- [ ] Two fresh sign-ups on different phones completed photo → words → session → journal on the day before launch.
- [ ] The AI provider has credit, a spending cap and alerts. Uptime and error alerts go to D.
- [ ] Analytics are recording on the landing page and in the app.
- [ ] The Product Hunt post is scheduled for 14 Oct and previewed, and the first comment is ready to paste.
