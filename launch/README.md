# Linguini launch kit

**Status: prepared for team review; no Product Hunt post has been published.** The public [landing page](https://linguini-landing.vercel.app/) offers a curated-photo mini session. The recommended next step is a supervised learner beta, followed by a Product Hunt launch once the checks in the [launch dashboard](plan.md) pass. The planning slot is 13 October 2026 at 00:01 PDT / 15:01 SGT; move it if readiness slips.

| Material | Use |
| --- | --- |
| [Narrated launch film and team review page](video/review.html) | Primary 30-second video for team review; includes the MP4, poster, transcript and gallery in one place. Serve the worktree locally as described in the [video guide](video/README.md). |
| [Product Hunt submission and channel copy](product-hunt.md) | Paste-ready preview listing, first maker comment, full-release draft, social posts, outreach and reply bank. |
| [Launch dashboard](plan.md) | Timeline, owner board, go/no-go criteria, launch-day response and retention measures. |
| [Media kit](media/README.md) | Product Hunt gallery, icon, social square, narrated film and editable sources. |

## Team decision checklist

- [ ] Agree on the launch promise: curated interactive preview now, or a full learner-app release after production verification.
- [ ] Redeploy the landing-site CTA fix and confirm that signup, login and every plan link opens the intended production route. The deployed page currently points those links to `localhost`.
- [ ] Reconcile landing claims about automatic photo analysis, speech feedback, pricing and Plus trials with working production behavior. The backend currently describes placeholder analysis and no speech grading.
- [ ] Confirm photo rights and inspect every media export. Review the [30-second narrated film](video/review.html) with sound and captions on desktop and phone. It depicts the **curated landing demo** through animation and one captured demo screen; it does not show a personal-photo workflow. Record a genuine product walkthrough before any listing that claims that flow is live.
- [ ] Have the team review the Product Hunt preview, gallery order, first comment and outreach text. Name a human owner for support, incidents and launch replies.
- [ ] Run the beta and go/no-go checklist in [plan.md](plan.md), then schedule the listing. Replace `[PH_POST_URL]` after Product Hunt creates the post.

The source fix in `landing/lib/site.ts` makes production builds use the deployed learner-app URL when `NEXT_PUBLIC_APP_URL` is unset, including in browser-rendered components. Development keeps the local app URL. Setting that environment variable explicitly remains the preferred deployment configuration.
