import { BusinessModelCanvas } from "../diagrams";
import { BreakEven } from "../story/BreakEven";
import { CostVideo } from "../story/CostVideo";
import { CompareApps, ModelMap, PlanMatrix, Roadmap } from "../story/figures";
import { InView } from "../story/InView";
import { PriceStory } from "../story/PriceStory";
import story from "../story/story.module.css";
import s from "../article.module.css";

export function BusinessModel() {
  return (
    <div className={s.body}>
      <p className={story.status}>Proposed pricing, not live yet · prices checked 23–24 September 2026</p>

      <InView as="p" className={story.lede}>
        Free gives every learner <mark>one photo lesson and one journal page a day</mark>. Plus is{" "}
        <mark>$49.99 a year</mark> for anyone who wants more. Each photo lesson costs us about <mark>2¢ in AI</mark>, so
        the free tier pays for itself once enough people upgrade: <mark>3.8% of learners</mark> from 2027, or about 1%
        once we move to cheaper models.
      </InView>

      <h2 id="at-a-glance">The model at a glance</h2>
      <p>
        The free plan limits the one thing that costs us money: AI reading your own photos. The learning stays free.
      </p>
      <BusinessModelCanvas />

      <h2 id="plans">Plans</h2>
      <PlanMatrix />
      <p>
        Beginners and returning learners need a small daily habit, not a heavy course, so one free photo lesson a day is
        the habit. Curated scenes are analysed once in advance, so free learners can replay them all day for almost
        nothing. You upgrade when you took more photos today than one lesson covers.
      </p>

      <h2 id="price">How we set the price</h2>
      <p>We checked $49.99 three ways: what it costs us, what other apps charge, and what a tutor costs.</p>
      <PriceStory />

      <h3>Against the competition</h3>
      <CompareApps />
      <p>
        From Duolingo we took the shape of the free tier: keep it genuinely useful, limit how much you can do, and save
        the expensive AI for paid plans.
      </p>

      <h2 id="costs">What a lesson costs us</h2>
      <CostVideo />
      <p>
        On top of that, hosting is a fixed $52–70 a month (Vercel, Supabase and Render). Stripe keeps 3.4% + 50¢ of each
        payment, which is why we push the annual plan. After fees, a Plus learner brings in about $5.24 a month.
      </p>

      <h2 id="model-choice">Why freemium</h2>
      <p>AI costs grow with every lesson, so each pricing model has to answer two questions.</p>
      <ModelMap />

      <h2 id="scale">Does the free tier pay for itself?</h2>
      <p>
        Every payer also carries the free learners: about 42 of them when 2.3% pay. On our current models at 2027 prices that
        only pays off once about 4% of learners pay. The cheaper models break even at about 1%, so that is the pipeline we launch
        on. Drag the sliders to try other numbers.
      </p>
      <BreakEven />
      <p>
        Before a wide launch we will test cheaper vision models on 50 labelled photos, enforce the daily limits on the
        server, and track what every lesson costs.
      </p>

      <h2 id="success">What success looks like, stage by stage</h2>
      <Roadmap />

      <h2 id="founding">Founding Plus</h2>
      <ul>
        <li>$34.99 a year, locked for as long as you stay, for the first 300 members.</li>
        <li>First into competitive I-Spy, a monthly roadmap vote and a call with the makers.</li>
        <li>Paying buys early access and a say, never an advantage in ranked play.</li>
      </ul>

      <h2 id="sources">Sources</h2>
      <p className={s.muted} style={{ fontSize: 14 }}>
        <a href="https://ai.google.dev/gemini-api/docs/pricing">Gemini API pricing</a> ·{" "}
        <a href="https://developers.openai.com/api/docs/pricing">OpenAI API pricing</a> ·{" "}
        <a href="https://supabase.com/pricing">Supabase</a> · <a href="https://vercel.com/pricing">Vercel</a> ·{" "}
        <a href="https://stripe.com/pricing">Stripe</a> ·{" "}
        <a href="https://www.sec.gov/Archives/edgar/data/0001562088/000162828026053299/q2fy26duolingo6-30x26share.htm">Duolingo Q2 2026 letter</a> ·{" "}
        <a href="https://www.dealnews.com/features/duolingo/cost/">Duolingo prices</a> ·{" "}
        <a href="https://www.dealnews.com/features/babbel/plan-pricing/">Babbel prices</a> ·{" "}
        <a href="https://speakshark.com/blog/speak-app-pricing-per-month-2026">Speak prices</a> ·{" "}
        <a href="https://apps.apple.com/us/app/capwords-ai-photo-vocabulary/id6738896465">CapWords</a> ·{" "}
        <a href="https://www.revenuecat.com/state-of-subscription-apps-2026-education">RevenueCat SOSA 2026</a> ·{" "}
        <a href="https://www.italki.com/en/blog/spanish-tutor-cost">italki tutor costs</a>. Token counts are estimates
        from our prompts and output limits.
      </p>
    </div>
  );
}
