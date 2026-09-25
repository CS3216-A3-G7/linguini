import Link from "next/link";
import { SoundVideo } from "@/components/SoundVideo";
import { Checklist } from "../launch/Checklist";
import { BannerWall, LaunchClock, ProductHuntListing } from "../launch/Figures";
import { Img } from "../launch/Img";
import {
  Circles, Communities, CreatorMap, DayShifts, DraftRail, FollowUps, GrowthCurve, PlanStrip, ProductHuntAsks,
  ReturnDots, Roles, Skipped, Yardstick,
} from "../launch/Plan";
import l from "../launch/launch.module.css";
import { InView } from "../story/InView";
import story from "../story/story.module.css";
import s from "../article.module.css";

const IMG = "/blog/launch";

const kit = [
  { href: `${IMG}/01-your-world.jpg`, name: "Product Hunt gallery, 1 to 4", note: "1270 × 760, in order", img: `${IMG}/01-your-world.jpg` },
  { href: `${IMG}/product-hunt-icon-240.png`, name: "Product Hunt thumbnail", note: "240 × 240 PNG", img: `${IMG}/product-hunt-icon-240.png` },
  { href: `${IMG}/explainer-720p.mp4`, name: "Explainer video", note: "50 s, 720p, with voiceover", img: `${IMG}/explainer-poster.jpg` },
  { href: `${IMG}/explainer.vtt`, name: "Explainer captions", note: "WebVTT, upload to YouTube", img: `${IMG}/explainer-poster.jpg` },
  { href: `${IMG}/social-square.jpg`, name: "Social square", note: "1080 × 1080", img: `${IMG}/social-square.jpg` },
  { href: `${IMG}/launch-card-1200x630.jpg`, name: "Launch-day link card", note: "1200 × 630", img: `${IMG}/launch-card-1200x630.jpg` },
];

export function LaunchCampaign() {
  return (
    <div className={s.body}>
      <p className={story.status}>Draft plan · nothing posted yet · checked 25 September 2026</p>

      <InView as="p" className={story.lede}>
        We’re putting Linguini on Product Hunt on <mark>Saturday 17 October at 3:01pm Singapore time</mark>. This page
        is the whole plan: when we launch and why, what we’ll post and where, what happens on the day, and how we’ll try
        to <mark>keep the people who show up</mark>. That last part is the one that matters, so most of the thinking
        went there.
      </InView>

      <PlanStrip />

      <h2 id="when">When we launch</h2>
      <p>
        We’re four students in Singapore. So why does our launch time look like it was picked for America?
      </p>
      <p>
        Because Product Hunt picked it. Every launch lives on a daily leaderboard, and that day starts at midnight in San
        Francisco. Launch at 12:01am Pacific and you get all 24 hours on the board. Launch at noon and you get half,
        against products that have been collecting votes since midnight. So everyone launches at 12:01am Pacific,
        wherever they live.
      </p>
      <p>
        For most teams outside the US that means staying up all night. For us it’s the opposite. 12:01am in San
        Francisco is 3:01pm on a Saturday afternoon in Singapore. We get to launch wide awake, with ten hours before
        anyone needs to sleep.
      </p>
      <LaunchClock />
      <p>
        The catch is in the diagram. Most of Product Hunt’s audience is in the US and Europe, and their daytime is our
        night. So we work in shifts, which we’ll get to.
      </p>
      <p>
        Why a Saturday? Weekdays bring more visitors, but a Tuesday also has about three times as many launches, and
        Product Hunt’s own guide says weekend launches get 15% more clicks through to the product. We’re a small team
        with a small network. What we want is people trying the demo, and a quieter day gets us more of that. One more
        check: the US leaves daylight saving on 1 November, which would push our start to 4:01pm. 17 October is before
        that.
      </p>

      <h2 id="soft-launch">Open doors or an invite list?</h2>
      <p>
        The alternative to a big launch is a soft one. Clubhouse was invite-only for 16 months and Arc for over a year,
        and both made people want in. But exclusivity costs something. Arc’s CEO has said{" "}
        <a href="https://youtu.be/xJdx0BlP0iY?t=198">they lost up to 80% of sign-ups to their waitlist</a>: people who
        asked to get in and were gone by the time they were let in.
      </p>
      <p>
        Clubhouse and Arc could afford that because people were already talking about them. Nobody is talking about us
        yet. We can’t afford to lose four out of five. So we split it by what’s ready:
      </p>
      <ul>
        <li><strong>The browser demo is open to everyone</strong>, no sign-up. It works today, end to end.</li>
        <li>
          <strong>The learner app goes to 10 to 20 beta testers first.</strong> Photo upload still returns sample words
          instead of reading your picture. We’d rather a small group finds that than a front page of strangers.
        </li>
      </ul>
      <p>
        Two rules made this easy. Product Hunt doesn’t feature waitlisted products unless people get in straight away,
        and Show HN rejects anything behind a sign-up. A waitlist would have cost us both. So what we’re really
        launching is the demo, which means the listing has one job: get people to try it.
      </p>

      <h2 id="listing">The listing</h2>
      <p>Product Hunt asks for five things. Here’s what we’re giving it.</p>
      <ProductHuntAsks />
      <ProductHuntListing />
      <p>
        The tagline says what you can do in the demo today. Our full-release line, “Learn Spanish or French from the
        photos you take”, waits until the app reads your own photos. The first comment ends on two questions because
        people answer questions. Product Hunt says 70% of its Product of the Day, Week and Month winners had a first
        comment from the maker.
      </p>
      <figure className={s.fig}>
        <div className="no-print">
          <SoundVideo
            poster={`${IMG}/explainer-poster.jpg`}
            label="Linguini explainer: a photo becomes Spanish or French words, a game and a journal page"
            captions={`${IMG}/explainer.vtt`}
            sources={[{ src: `${IMG}/explainer-720p.mp4` }]}
          />
        </div>
        <Img src={`${IMG}/explainer-poster.jpg`} alt="Explainer video poster frame" className={`print-only ${l.videoPoster}`} loading="eager" />
        <figcaption>
          The 50-second explainer for the listing. It starts muted with captions, because most people scroll with the
          sound off. Tap Sound on to hear the voiceover.
        </figcaption>
      </figure>
      <p>
        A listing only works if people see it, though. Product Hunt doesn’t so much send you traffic on launch day as
        reward the traffic you bring. So the next question is what we post, and where.
      </p>

      <h2 id="posts">What we’ll post</h2>
      <p>
        These are the real drafts, one per channel. Scroll sideways to see them all. The likes, the carousel and the
        story all work.
      </p>
      <DraftRail />
      <p>
        Each one is written the way people on that channel already talk, and none of them ask for upvotes. Product Hunt
        can pull a launch for that, and a comment tells us more than a vote anyway.
      </p>

      <h2 id="banners">Banners</h2>
      <p>
        Seven files, one look: a real demo photo with the words pinned on, the same way the app shows them. One script
        draws them all, so moving the date is a one-line change.
      </p>
      <div className={`${s.fig} ${s.breakout}`}>
        <BannerWall />
      </div>
      <p>Posts and banners are the what. The harder question is who sees them first.</p>

      <h2 id="who">Who we’re telling, closest first</h2>
      <p>
        We go out in circles. The closer someone is to us, the earlier they try it and the more honest we expect them
        to be. Strangers only hear about it once the people who know us have found the worst bugs.
      </p>
      <Circles />

      <h3>Communities</h3>
      <p>Only where promotion is allowed, and only in the thread the rules point to.</p>
      <Communities />

      <h3>Creators</h3>
      <p>
        We’re emailing four kinds of language creator. The obvious move is to go for the biggest audience. But a huge
        channel gets hundreds of pitches, and a small one reads every email.
      </p>
      <CreatorMap />

      <h3>Where we’re not posting</h3>
      <Skipped />
      <p>
        Two of those are “not yet” rather than “no”. They’re waiting for the next launch, which we’ll come to. First, the
        day itself.
      </p>

      <h2 id="day">Launch day, hour by hour</h2>
      <p>Four of us, three shifts, Singapore time, Saturday into Sunday.</p>
      <DayShifts />
      <p>Whoever is on shift covers three jobs:</p>
      <Roles />
      <p className={s.note}>
        <strong>If sign-up breaks:</strong> we stop posting, put a note on the landing page and send people to the demo,
        which needs no account, while we fix it.
      </p>
      <p>
        That’s the easy part, because it’s just a schedule. By Sunday afternoon the votes stop mattering. What matters
        after that is whether anyone comes back.
      </p>

      <h2 id="after">After launch day</h2>
      <p>
        Most launch plans count visits and upvotes. Those tell you whether the listing worked. They don’t tell you
        whether the product did. For that we’re watching one number: <strong>of the people who sign up during launch
        week, how many do a second lesson within seven days?</strong>
      </p>
      <ReturnDots />
      <p>
        Is 10% good? We needed a yardstick. <a href="https://amplitude.com/blog/7-percent-retention-rule">Amplitude</a>{" "}
        makes the analytics software that thousands of apps use to count their users, so it can see how most apps do.
        Its finding: if 7% of your new users are still active on day 7, you’re already in the top quarter of apps. We’re
        not competing with Amplitude. We’re borrowing its ruler.
      </p>
      <Yardstick />
      <p>
        So 10% is ambitious, and with numbers this small one person either way changes everything. But it answers the
        question we actually have: does the loop bring anyone back at all? Here’s what we’re doing to earn the second
        visit:
      </p>
      <ul>
        <li><strong>No account for the first lesson.</strong> The demo is the onboarding.</li>
        <li><strong>Every lesson ends with picking tomorrow’s scene</strong>, so there’s a reason to open it again.</li>
        <li><strong>One reminder on day two</strong>, only if you opted in, using your own photo. Not a daily blast.</li>
        <li><strong>A streak from day one</strong>, and a weekly recap of your journal: the week’s photos and words on one page.</li>
      </ul>
      <p>And here’s what we do with what we learn, in the two weeks after:</p>
      <FollowUps />

      <h2 id="next">The next launch</h2>
      <p>
        Launches are spikes. Users jump on the day, then drift down to a plateau. If you wait until the line is flat to
        plan the next thing, you’ve waited too long.
      </p>
      <GrowthCurve />
      <p>
        So our second launch is already picked: real photo analysis, the day the app reads your own photo instead of
        returning sample words. That’s also when Show HN and the AI newsletters make sense. Product Hunt allows a
        relaunch after a major update, and we want to arrive with our week-one numbers. The business side of that, what
        we charge and what each lesson costs us, is in <Link href="/blog/linguini-business-model">our business
        model</Link>.
      </p>

      <h2 id="checklist">Our checklist</h2>
      <p>
        We copied the shape of <a href="https://gist.github.com/yangshun/1e84ae8461975e7fa9a7d153621c3756">Yangshun
        Tay’s launch dashboard for Docusaurus 2.0</a>, which won Product of the Day: links, a timed run, checkboxes,
        then channel lists. Ours is in the repo as <code>marketing/product-hunt/plan.md</code>. Here’s the first task of
        each week. Open it up for all of them; it ticks, and remembers your progress in this browser.
      </p>
      <Checklist />

      <h2 id="kit">The launch kit</h2>
      <p>Everything above, in one place. Banners are further up, each with a save button.</p>
      <ul className={l.kit}>
        {kit.map(item => (
          <li key={item.name}>
            <a href={item.href} download>
              <Img src={item.img} alt="" loading="lazy" />
              <span>{item.name}<small>{item.note}</small></span>
            </a>
          </li>
        ))}
      </ul>

      <h2 id="sources">Sources</h2>
      <p className={s.muted} style={{ fontSize: 14 }}>
        <a href="https://www.producthunt.com/launch/preparing-for-launch">Product Hunt: preparing for launch</a> ·{" "}
        <a href="https://www.producthunt.com/launch">Product Hunt launch guide</a> ·{" "}
        <a href="https://help.producthunt.com/en/articles/479557-how-to-post-a-product">How to post a product</a> ·{" "}
        <a href="https://www.producthunt.com/launch/sharing-your-launch">Sharing your launch</a> ·{" "}
        <a href="https://help.producthunt.com/en/articles/9883485-product-hunt-featuring-guidelines">Featuring guidelines</a> ·{" "}
        <a href="https://www.producthunt.com/p/databox/i-ve-analyzed-all-2026-ph-launches-to-find-the-best-day-to-launch">Databox: best day to launch in 2026</a> ·{" "}
        <a href="https://www.timeanddate.com/time/change/usa?year=2026">US daylight saving 2026</a> ·{" "}
        <a href="https://news.ycombinator.com/showhn.html">Show HN guidelines</a> ·{" "}
        <a href="https://youtu.be/xJdx0BlP0iY?t=198">Arc’s CEO on the waitlist</a> ·{" "}
        <a href="https://techcrunch.com/2023/07/25/arc-browser-is-now-available-to-download-for-everyone">Arc opens to everyone</a> ·{" "}
        <a href="https://en.wikipedia.org/wiki/Clubhouse_(app)">Clubhouse</a> ·{" "}
        <a href="https://www.hellotalk.com/community-guidelines">HelloTalk guidelines</a> ·{" "}
        <a href="https://www.nushackers.org/">NUS Hackers</a> ·{" "}
        <a href="https://lindiebotes.com/about/">Lindie Botes</a> ·{" "}
        <a href="https://amplitude.com/blog/7-percent-retention-rule">Amplitude 7% rule</a> ·{" "}
        <a href="https://gist.github.com/yangshun/1e84ae8461975e7fa9a7d153621c3756">Docusaurus 2.0 launch dashboard</a>.
        Subreddit rules and community sizes change often; we recheck each one the week before.
      </p>
    </div>
  );
}
