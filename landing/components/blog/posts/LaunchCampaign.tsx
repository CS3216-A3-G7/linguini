import { Checklist } from "../launch/Checklist";
import { BannerWall, Funnel, LaunchClock, ProductHuntListing, Runbook } from "../launch/Figures";
import { ChannelTabs, InstagramPost, StoryPhone, XThread } from "../launch/Social";
import l from "../launch/launch.module.css";
import { InView } from "../story/InView";
import story from "../story/story.module.css";
import s from "../article.module.css";
import { Img } from "../launch/Img";

const IMG = "/blog/launch";

const communities = [
  { name: "r/SideProject", size: "", rule: "Self-promotion allowed.", why: "We lead with how we built it, since that’s what the sub is for." },
  { name: "r/languagelearning", size: "3.4M", rule: "Promotion only in the resources thread, or with mod permission.", why: "The biggest room of exactly our learners. One post, in the right thread." },
  { name: "r/Spanish", size: "", rule: "Weekly self-promotion thread; we message the mods first.", why: "Spanish is our strongest demo, so this is where feedback will be sharpest." },
  { name: "Discord: Refold Central, Language Learning Community, Language Cafe", size: "~28k to 37k each", rule: "Promo channels only.", why: "People here practise daily. They’ll tell us if it helps or just looks nice." },
  { name: "Indie Hackers", size: "", rule: "One Show IH post, framed as a request for feedback.", why: "Other makers give the most useful notes on the listing itself." },
  { name: "NUS Hackers Friday Hacks", size: "", rule: "They’re looking for speakers until 13 Nov.", why: "Ten minutes of live demo in a room beats any post." },
];

const creators = [
  { name: "Lindie Botes", size: "~357k on YouTube", why: "Reviews language apps, is a UX designer and worked in Singapore. Our first email." },
  { name: "Xiaomanyc", size: "~7.1M on YouTube", why: "Speaks to strangers in their language. The closest fit to speak-first, and a long shot." },
  { name: "Matt vs Japan (Refold)", size: "YouTube", why: "Comprehensible input. A photo of your own street is input you already understand." },
  { name: "Ten smaller tutors and study accounts", size: "under 50k", why: "Picked by audience, not follower count. More likely to try it and reply." },
];

const skipped = [
  { name: "r/French", why: "No advertising at all. We’ll join as learners instead." },
  { name: "HelloTalk", why: "Its guidelines ban promotion." },
  { name: "Steve Kaufmann and Ikenna", why: "They run LingQ and Fluyo. Asking a competitor to feature us is awkward for everyone." },
  { name: "Show HN", why: "Not yet. HN will upload their own photo in the first minute and get sample words back. We post once real photo analysis ships." },
  { name: "AI newsletters (The Rundown, TLDR AI, Ben’s Bites)", why: "Same reason. Pitching an AI tool while the AI part is sample data would backfire." },
];

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
      <p className={story.status}>Draft plan · nothing posted yet · checked 24 September 2026</p>

      <InView as="p" className={story.lede}>
        We’re putting Linguini on Product Hunt on <mark>Saturday 17 October at 3:01pm Singapore time</mark>. This page is
        the whole plan: the listing, <mark>every post we’ll publish</mark>, the banners, who we’re telling and the
        checklist we’re working through. Take whatever’s useful.
      </InView>

      <h2 id="when">When we launch</h2>
      <LaunchClock />
      <p>
        Product Hunt’s day starts at 12:01am Pacific, which is 3:01pm for us. That’s a gift. We go live in the
        afternoon, wide awake, and get ten hours of posting and replying before a night shift takes over.
      </p>
      <p>
        We picked a Saturday. Weekdays bring more visitors, but a Tuesday also has about three times as many launches as
        a Saturday, and Product Hunt’s own guide says weekend launches get 15% more clicks through to the product. We’re a small
        student team with a small network. Clicks to the demo are what we want, and a quieter day gets us more of them.
      </p>
      <p>
        One more check: the US leaves daylight saving on 1 November, which would push our start to 4:01pm. 17 October is
        before that.
      </p>

      <h2 id="soft-launch">Open doors or an invite list?</h2>
      <p>
        An invite list is tempting. Clubhouse was invite-only for 16 months and Arc for over a year, and both made people
        want in. But they had products people were already talking about. We don’t yet.
      </p>
      <p>So we split it by what’s ready:</p>
      <ul>
        <li><strong>The browser demo is open to everyone</strong>, no sign-up. It works today, end to end.</li>
        <li>
          <strong>The learner app goes to 10 to 20 beta testers first.</strong> Photo upload still returns sample words
          instead of reading your picture. We’d rather a small group finds that than a front page of strangers.
        </li>
      </ul>
      <p>
        Two rules made the call easy. Product Hunt doesn’t feature waitlisted products unless people get in straight
        away, and Show HN rejects anything behind a sign-up. A waitlist would have cost us both.
      </p>

      <h2 id="listing">The listing</h2>
      <ProductHuntListing />
      <p>
        The tagline says what you can do in the demo today. Our full-release line, “Learn Spanish or French from the
        photos you take”, waits until the app reads your own photos. The first comment ends on two questions because
        people answer questions. Product Hunt says 70% of its Product of the Day, Week and Month winners had one from
        the maker.
      </p>
      <figure className={s.fig}>
        <video className={l.video} controls preload="none" poster={`${IMG}/explainer-poster.jpg`} playsInline>
          <source src={`${IMG}/explainer-720p.mp4`} type="video/mp4" />
          <track kind="captions" src={`${IMG}/explainer.vtt`} srcLang="en" label="English" default />
        </video>
        <Img src={`${IMG}/explainer-poster.jpg`} alt="Explainer video poster frame" className={`print-only ${l.videoPoster}`} loading="eager" />
        <figcaption>
          The 50-second explainer for the listing. It ships with captions because most people watch with the sound
          off.
        </figcaption>
      </figure>

      <h2 id="posts">What we’ll post</h2>
      <p>These are the real drafts. Tap around: the likes, the carousel and the tabs all work.</p>

      <div className={`${s.fig} ${s.breakout}`}>
        <div className={l.feed}>
          <div className={l.feedCol}>
            <p className={l.label}>X · launch-day thread</p>
            <XThread />
          </div>
          <div className={l.feedCol}>
            <p className={l.label}>Instagram · 4:5 carousel</p>
            <InstagramPost />
          </div>
        </div>
      </div>
      <p>
        X gets a thread: the first post carries the link card, the replies carry the why. Instagram is 4:5 because it
        takes the most room in the feed, and a carousel gives anyone who scrolls past a second slide to stop on.
      </p>

      <div className={l.storyRow}>
        <StoryPhone />
        <div>
          <h3>Stories</h3>
          <p>
            A countdown at T−3, then “we’re live” on the day with a link sticker. The story banner leaves the top and
            bottom clear, because that’s where Instagram puts its own buttons.
          </p>
        </div>
      </div>

      <h3>Everywhere else</h3>
      <ChannelTabs />
      <p>
        LinkedIn is written by one of us, not the brand, because people reply to people. Reddit gets a question, not an
        announcement. The Telegram message is lowercase because that’s how we actually text each other. None of them ask
        for upvotes. Product Hunt can pull a launch for that, and a comment tells us more anyway.
      </p>

      <h2 id="banners">Banners</h2>
      <p>
        Seven files, one look: a real demo photo with the words pinned on, the same way the app shows them. One script
        draws them all, so moving the date is a one-line change.
      </p>
      <div className={`${s.fig} ${s.breakout}`}>
        <BannerWall />
      </div>

      <h2 id="who">Who we’re telling, closest first</h2>
      <p>
        We go out in circles. Friends, classmates and beta testers hear first, one message each, because they’ll try it
        properly and tell us the truth. Communities come next, once we’ve fixed what that first circle found. Creators
        get a personal note with no ask to post.
      </p>

      <h3>Communities</h3>
      <InView as="ul" className={l.lists}>
        {communities.map((c, i) => (
          <li key={c.name} style={{ ["--i" as string]: i }}>
            <h4>{c.name} {c.size ? <small>{c.size}</small> : null}</h4>
            <p className={l.rule}>{c.rule}</p>
            <p>{c.why}</p>
          </li>
        ))}
      </InView>

      <h3>Creators</h3>
      <InView as="ul" className={l.lists}>
        {creators.map((c, i) => (
          <li key={c.name} style={{ ["--i" as string]: i }}>
            <h4>{c.name} <small>{c.size}</small></h4>
            <p>{c.why}</p>
          </li>
        ))}
      </InView>

      <h3>Where we’re not posting, and why</h3>
      <ul>
        {skipped.map(item => (
          <li key={item.name}><strong>{item.name}.</strong> {item.why}</li>
        ))}
      </ul>

      <h2 id="day">Launch day, hour by hour</h2>
      <p>All times Singapore, Saturday into Sunday.</p>
      <Runbook />

      <h2 id="after">After launch day</h2>
      <p>
        Upvotes are over by Sunday. What we’re actually watching is whether someone does a second lesson within a week.
      </p>
      <Funnel />
      <p>
        For scale: Amplitude puts an app in the top quarter if 7% of new users are back on day 7. Duolingo, after years
        of streak tuning, sees 42% of its monthly learners on any given day (58.7 million of 140.6 million in Q2 2026).
        We’re not Duolingo. We just want to know if our loop brings anyone back.
      </p>
      <p>What we’re doing about it:</p>
      <ul>
        <li><strong>No account for the first lesson.</strong> The demo is the onboarding.</li>
        <li><strong>Every lesson ends with picking tomorrow’s scene</strong>, so there’s a reason to open it again.</li>
        <li><strong>One reminder on day two</strong>, only if you opted in, using your own photo. Not a daily blast.</li>
        <li><strong>A streak from day one</strong>, and a weekly recap of your journal: the week’s photos and words on one page.</li>
        <li>
          <strong>The next launch is already planned</strong>: real photo analysis. Product Hunt allows a relaunch
          after a big update, and we want to arrive with our week-one numbers.
        </li>
      </ul>
      <p>
        On the day itself, someone is always watching the error dashboard. If sign-up breaks, we stop posting, put a note
        on the landing page and send people to the demo while we fix it.
      </p>

      <h2 id="checklist">Our checklist</h2>
      <p>
        We copied the shape of Yangshun Tay’s launch dashboard for Docusaurus 2.0, which won Product of the Day: links,
        a timed run, checkboxes, then channel lists. Ours is in the repo as <code>launch/checklist.md</code>. This copy
        ticks, and remembers your progress in this browser.
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
        <a href="https://www.producthunt.com/launch/sharing-your-launch">Sharing your launch</a> ·{" "}
        <a href="https://help.producthunt.com/en/articles/9883485-product-hunt-featuring-guidelines">Featuring guidelines</a> ·{" "}
        <a href="https://www.producthunt.com/p/databox/i-ve-analyzed-all-2026-ph-launches-to-find-the-best-day-to-launch">Databox: best day to launch in 2026</a> ·{" "}
        <a href="https://www.timeanddate.com/time/change/usa?year=2026">US daylight saving 2026</a> ·{" "}
        <a href="https://news.ycombinator.com/showhn.html">Show HN guidelines</a> ·{" "}
        <a href="https://techcrunch.com/2023/07/25/arc-browser-is-now-available-to-download-for-everyone">Arc opens to everyone</a> ·{" "}
        <a href="https://en.wikipedia.org/wiki/Clubhouse_(app)">Clubhouse</a> ·{" "}
        <a href="https://www.hellotalk.com/community-guidelines">HelloTalk guidelines</a> ·{" "}
        <a href="https://www.nushackers.org/">NUS Hackers</a> ·{" "}
        <a href="https://lindiebotes.com/about/">Lindie Botes</a> ·{" "}
        <a href="https://amplitude.com/blog/7-percent-retention-rule">Amplitude 7% rule</a> ·{" "}
        <a href="https://www.sec.gov/Archives/edgar/data/0001562088/000162828026053299/q2fy26duolingo6-30x26share.htm">Duolingo Q2 2026 letter</a> ·{" "}
        <a href="https://gist.github.com/yangshun/1e84ae8461975e7fa9a7d153621c3756">Docusaurus 2.0 launch dashboard</a>.
        Subreddit rules and community sizes change often; we recheck each one the week before.
      </p>
    </div>
  );
}
