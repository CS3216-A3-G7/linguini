# Linguini launch kit

**Status: prepared for team review; no Product Hunt post has been published.** The public [landing page](https://linguini-landing.vercel.app/) offers a curated-photo mini session. The recommended next step is a supervised learner beta, followed by a Product Hunt launch once the checks in the [launch dashboard](plan.md) pass. The planning slot is 13 October 2026 at 00:01 PDT / 15:01 SGT; move it if readiness slips.

| Material | Use |
| --- | --- |
| [Product Hunt submission and channel copy](product-hunt.md) | Paste-ready preview listing, first maker comment, full-release draft, social posts, outreach and reply bank. |
| [Launch dashboard](plan.md) | Timeline, owner board, go/no-go criteria, launch-day response and retention measures. |
| [Media kit](media/README.md) | Product Hunt gallery, icon, social square, illustrative teaser and editable source. |

## Team decision checklist

- [ ] Agree on the launch promise: curated interactive preview now, or a full learner-app release after production verification.
- [ ] Redeploy the landing-site CTA fix and confirm that signup, login and every plan link opens the intended production route. The deployed page currently points those links to `localhost`.
- [ ] Reconcile landing claims about automatic photo analysis, speech feedback, pricing and Plus trials with working production behavior. The backend currently describes placeholder analysis and no speech grading.
- [ ] Confirm photo rights, inspect every media export, and record a genuine product walkthrough for any listing that claims the app flow is live. The supplied MP4 is an **illustrative teaser**, not a screen recording.
- [ ] Have the team review the Product Hunt preview, gallery order, first comment and outreach text. Name a human owner for support, incidents and launch replies.
- [ ] Run the beta and go/no-go checklist in [plan.md](plan.md), then schedule the listing. Replace `[PH_POST_URL]` after Product Hunt creates the post.

The source fix in `landing/lib/site.ts` makes production builds use the deployed learner-app URL when `NEXT_PUBLIC_APP_URL` is unset, including in browser-rendered components. Development keeps the local app URL. Setting that environment variable explicitly remains the preferred deployment configuration.
