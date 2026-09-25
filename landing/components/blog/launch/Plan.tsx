"use client";

import { type ReactNode, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight } from "@/components/icons";
import { useInView } from "../story/hooks";
import { Img } from "./Img";
import { type Brand, Logo } from "./Logos";
import { InstagramPost, LinkedInPost, RedditPost, StoryPhone, TelegramChat, XThread } from "./Social";
import p from "./plan.module.css";

function useInViewRef<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  return [ref, useInView(ref)] as const;
}

/* ---------- The whole plan on one line ---------- */

const steps = [
  { href: "#checklist", when: "3 weeks out", title: "Fix and test", text: "Beta testers, tracking, every button works" },
  { href: "#who", when: "1 week out", title: "Tell people", text: "Friends first, then communities, then creators" },
  { href: "#day", when: "Sat 17 Oct, 3:01pm", title: "Launch", text: "Product Hunt, our posts, three shifts", live: true },
  { href: "#after", when: "The 2 weeks after", title: "Bring people back", text: "One number: a second lesson in 7 days" },
  { href: "#next", when: "Already planned", title: "Launch again", text: "Real photo analysis" },
];

export function PlanStrip() {
  const [ref, inView] = useInViewRef<HTMLOListElement>();
  return (
    <figure className={p.fig}>
      <ol ref={ref} className={p.strip} data-inview={inView || undefined}>
        {steps.map((step, i) => (
          <li key={step.title} style={{ ["--i" as string]: i }} data-live={step.live || undefined}>
            <a href={step.href}>
              <small>{step.when}</small>
              <b>{step.title}</b>
              <span>{step.text}</span>
            </a>
          </li>
        ))}
      </ol>
      <figcaption>The plan on one line. Tap a step to jump to it.</figcaption>
    </figure>
  );
}

/* ---------- What Product Hunt asks for ---------- */

const asks = [
  { need: "A product site", ours: "linguini-landing.vercel.app, with the demo on the first screen" },
  { need: "A logo", ours: "Our pasta mascot, 240 × 240" },
  { need: "A pitch", ours: "A one-line tagline and a short description" },
  { need: "A demo video", ours: "The 50-second explainer, below" },
  { need: "A first comment", ours: "Why we built it, and two questions for readers" },
];

export function ProductHuntAsks() {
  return (
    <ul className={p.asks}>
      {asks.map(item => (
        <li key={item.need}>
          <b>{item.need}</b>
          <span>{item.ours}</span>
        </li>
      ))}
    </ul>
  );
}

/* ---------- Every draft, side by side ---------- */

const drafts: { brand: Brand; label: string; note: string; body: ReactNode; wide?: boolean }[] = [
  { brand: "x", label: "X thread", note: "The first post carries the link card. The replies carry the why.", body: <XThread />, wide: true },
  { brand: "instagram", label: "Instagram carousel", note: "4:5, because it takes the most room in the feed. Double-click the photo.", body: <InstagramPost /> },
  { brand: "instagram", label: "Instagram story", note: "A countdown at T−3, then “we’re live” with a link sticker. Top and bottom left clear for Instagram’s buttons.", body: <div className={p.storyWrap}><StoryPhone /></div> },
  { brand: "linkedin", label: "LinkedIn", note: "Written by one of us, not the brand, because people reply to people.", body: <LinkedInPost />, wide: true },
  { brand: "reddit", label: "Reddit", note: "A question in the weekly self-promotion thread, not an announcement.", body: <RedditPost /> },
  { brand: "telegram", label: "Telegram", note: "Lowercase, because that’s how we actually text each other.", body: <TelegramChat /> },
];

export function DraftRail() {
  const railRef = useRef<HTMLDivElement>(null);
  const [edge, setEdge] = useState({ start: true, end: false });

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const update = () => setEdge({
      start: rail.scrollLeft < 8,
      end: rail.scrollLeft + rail.clientWidth > rail.scrollWidth - 8,
    });
    update();
    rail.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      rail.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);

  const nudge = (dir: 1 | -1) => {
    const rail = railRef.current;
    if (!rail) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    rail.scrollBy({ left: dir * rail.clientWidth * 0.8, behavior: reduced ? "auto" : "smooth" });
  };

  return (
    <div className={p.railWrap}>
      <div className={p.railBar}>
        <p className={p.railHint}>
          <span className={p.railLogos} aria-hidden="true">{drafts.map(d => <Logo key={d.label} brand={d.brand} size={16} />)}</span>
          {drafts.length} drafts, scroll or use the arrows
        </p>
        <div className={p.railButtons}>
          <button type="button" onClick={() => nudge(-1)} disabled={edge.start} aria-label="Previous drafts"><ArrowLeft size={18} /></button>
          <button type="button" onClick={() => nudge(1)} disabled={edge.end} aria-label="More drafts"><ArrowRight size={18} /></button>
        </div>
      </div>
      <div ref={railRef} className={p.rail} data-start={edge.start || undefined} data-end={edge.end || undefined}>
        {drafts.map(d => (
          <section key={d.label} className={p.slide} data-wide={d.wide || undefined} aria-label={d.label}>
            <p className={p.slideLabel}><Logo brand={d.brand} size={16} /> {d.label}</p>
            <div className={p.slideBody}>{d.body}</div>
            <p className={p.slideNote}>{d.note}</p>
          </section>
        ))}
      </div>
    </div>
  );
}

/* ---------- Who hears first: three circles ---------- */

const circles: { name: string; when: string; how: string; brands: Brand[]; extra?: string }[] = [
  { name: "People we know", when: "Testing it from three weeks out", how: "Friends, classmates and our beta testers. They try it first and get a message each on the day, because they’ll use it properly and tell us the truth.", brands: ["telegram", "instagram", "linkedin"] },
  { name: "Communities", when: "Launch afternoon", how: "Language learners and other makers, once the first circle’s bugs are fixed, and only in the threads that allow it.", brands: ["reddit", "discord", "indiehackers", "producthunt"], extra: "NUS Hackers" },
  { name: "Creators", when: "A week before", how: "A personal note to language YouTubers, with no ask to post.", brands: ["youtube"] },
];

export function Circles() {
  const [ref, inView] = useInViewRef<HTMLDivElement>();
  return (
    <div ref={ref} className={p.circles} data-inview={inView || undefined}>
      <div className={p.rings} aria-hidden="true">
        <span className={p.ring} data-n="3" />
        <span className={p.ring} data-n="2" />
        <span className={p.ring} data-n="1" />
        <Img src="/brand/mascot-180.png" alt="" className={p.ringCore} />
        <b className={p.ringTag} data-n="1">1</b>
        <b className={p.ringTag} data-n="2">2</b>
        <b className={p.ringTag} data-n="3">3</b>
      </div>
      <ol className={p.ringList}>
        {circles.map((c, i) => (
          <li key={c.name} style={{ ["--i" as string]: i }} data-n={i + 1}>
            <p className={p.ringHead}><b>{c.name}</b> <small>{c.when}</small></p>
            <p className={p.ringLogos}>
              {c.brands.map(b => <Logo key={b} brand={b} size={22} title={b} />)}
              {c.extra ? <span className={p.textMark}>{c.extra}</span> : null}
            </p>
            <p className={p.ringHow}>{c.how}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* ---------- Communities: one line each ---------- */

const communities: { brand: Brand | null; name: string; size?: string; rule: string }[] = [
  { brand: "reddit", name: "r/languagelearning", size: "3.4M", rule: "Resources thread only. Exactly our learners." },
  { brand: "reddit", name: "r/Spanish", rule: "Weekly promo thread. We ask the mods first." },
  { brand: "reddit", name: "r/SideProject", rule: "Promotion welcome. We lead with how we built it." },
  { brand: "discord", name: "Refold, Language Learning Community, Language Cafe", size: "28k to 37k each", rule: "Promo channels only. Daily learners." },
  { brand: "indiehackers", name: "Indie Hackers", rule: "One Show IH post, asking for feedback on the listing." },
  { brand: null, name: "NUS Hackers Friday Hacks", rule: "Ten minutes of live demo. Speakers wanted until 13 Nov." },
];

export function Communities() {
  return (
    <ul className={p.rows}>
      {communities.map(c => (
        <li key={c.name}>
          {c.brand ? <Logo brand={c.brand} size={22} /> : <span className={p.textMark} aria-hidden="true">NUS</span>}
          <b>{c.name}{c.size ? <small> {c.size}</small> : null}</b>
          <span>{c.rule}</span>
        </li>
      ))}
    </ul>
  );
}

/* ---------- Creators: reach against the odds of a reply ---------- */

// x: audience on a log scale (10k to 10M), y: how likely they are to try it and reply (0 to 1).
const creators = [
  { name: "Xiaomanyc", size: "7.1M", reach: 7_100_000, reply: 0.12, note: "Speak-first, and a long shot" },
  { name: "Lindie Botes", size: "357k", reach: 357_000, reply: 0.62, note: "Reviews language apps. Our first email" },
  { name: "Matt vs Japan", size: "Refold", reach: 900_000, reply: 0.4, note: "Comprehensible input" },
  { name: "Ten smaller tutors", size: "under 50k", reach: 30_000, reply: 0.85, note: "Most likely to try it and reply" },
];

const logX = (n: number) => ((Math.log10(n) - 4) / 3) * 100;

export function CreatorMap() {
  const [ref, inView] = useInViewRef<HTMLDivElement>();
  return (
    <figure className={p.fig}>
      <div ref={ref} className={p.map} data-inview={inView || undefined}>
        <span className={p.axisY}>More likely to reply</span>
        <span className={p.axisX}>Bigger audience <Logo brand="youtube" size={14} /></span>
        <div className={p.plot}>
          {creators.map((c, i) => (
            <div key={c.name} className={p.dot} data-side={logX(c.reach) > 60 ? "left" : undefined}
              style={{ left: `${logX(c.reach)}%`, bottom: `${c.reply * 100}%`, ["--i" as string]: i }}>
              <i aria-hidden="true" />
              <p><b>{c.name}</b> <small>{c.size}</small><span>{c.note}</span></p>
            </div>
          ))}
        </div>
      </div>
      <figcaption>
        Followers aren’t the point. A creator with 30,000 viewers who actually tries it beats one with seven million who
        never opens the email.
      </figcaption>
    </figure>
  );
}

/* ---------- Where we’re not posting ---------- */

const skipped: { brand: Brand | null; mark?: string; name: string; why: string; verdict: string }[] = [
  { brand: "ycombinator", name: "Show HN", why: "They’ll upload their own photo in the first minute and get sample words back. We post once real photo analysis ships.", verdict: "Not yet" },
  { brand: null, mark: "AI", name: "AI newsletters", why: "Same reason. Pitching an AI tool while the AI part is sample data would backfire.", verdict: "Not yet" },
  { brand: "reddit", name: "r/French", why: "No advertising at all. We’ll join as learners instead.", verdict: "No" },
  { brand: null, mark: "HT", name: "HelloTalk", why: "Its guidelines ban promotion.", verdict: "No" },
  { brand: "youtube", name: "Steve Kaufmann, Ikenna", why: "They run LingQ and Fluyo. Asking a competitor to feature us is awkward for everyone.", verdict: "No" },
];

export function Skipped() {
  return (
    <ul className={`${p.rows} ${p.skipped}`}>
      {skipped.map(item => (
        <li key={item.name}>
          {item.brand ? <Logo brand={item.brand} size={22} mono /> : <span className={p.textMark} aria-hidden="true">{item.mark}</span>}
          <b>{item.name} <em data-verdict={item.verdict}>{item.verdict}</em></b>
          <span>{item.why}</span>
        </li>
      ))}
    </ul>
  );
}

/* ---------- Launch day in three shifts ---------- */

const shifts = [
  {
    name: "Afternoon", hours: "14:00 to 01:00", crew: "All four of us", tone: "tomato",
    beats: [
      ["14:00", "Sign up fresh on a phone. Dashboards open."],
      ["15:01", "Live. First comment up within a minute.", true],
      ["15:10", "Posts go out. Friends get a message each."],
      ["16:00", "Every comment answered within the hour."],
      ["21:00", "US east coast wakes up. Second story."],
    ],
  },
  {
    name: "Night", hours: "01:00 to 08:00", crew: "Two on call", tone: "teal",
    beats: [
      ["01:00", "Handover to one replier and one engineer. Everyone else sleeps."],
      ["All night", "Watch errors and sign-ups. Answer the US."],
    ],
  },
  {
    name: "Morning", hours: "08:00 to 14:59", crew: "All four of us", tone: "pasta",
    beats: [
      ["08:00", "Read the overnight numbers."],
      ["10:00", "Second nudge in our NUS class chats."],
      ["14:59", "Day ends. Thank everyone. Write down what broke."],
    ],
  },
] as const;

export function DayShifts() {
  const [ref, inView] = useInViewRef<HTMLDivElement>();
  return (
    <div ref={ref} className={p.shifts} data-inview={inView || undefined}>
      {shifts.map((shift, i) => (
        <section key={shift.name} className={p.shift} data-tone={shift.tone} style={{ ["--i" as string]: i }}>
          <header>
            <h4>{shift.name}</h4>
            <p>{shift.hours}</p>
            <p className={p.crew}>{shift.crew}</p>
          </header>
          <ol>
            {shift.beats.map(([time, text, live]) => (
              <li key={time} data-live={live || undefined}>
                <time>{time}</time>
                <span>{text}</span>
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}

const roles = [
  { role: "Replier", job: "Answers every comment and support email. Our customer support for the day." },
  { role: "Engineer on call", job: "Watches the error dashboard. Fixes bugs, restarts servers, rolls back." },
  { role: "Poster", job: "Sends the posts and messages on time, and tracks what’s been sent." },
];

export function Roles() {
  return (
    <dl className={p.roles}>
      {roles.map(r => (
        <div key={r.role}>
          <dt>{r.role}</dt>
          <dd>{r.job}</dd>
        </div>
      ))}
    </dl>
  );
}

/* ---------- The one number after launch ---------- */

export function ReturnDots() {
  const [ref, inView] = useInViewRef<HTMLDivElement>();
  return (
    <figure className={p.fig}>
      <div ref={ref} className={p.returns} data-inview={inView || undefined}>
        <div className={p.dots} aria-hidden="true">
          {Array.from({ length: 30 }, (_, i) => <i key={i} data-back={i < 3 || undefined} style={{ ["--i" as string]: i }} />)}
        </div>
        <p className={p.returnsText}>
          <b>3 of 30</b>
          <span>people who sign up during launch week do a second lesson within 7 days. That’s 10%.</span>
        </p>
      </div>
      <figcaption>Our target, not a forecast. We’ll publish the real number either way.</figcaption>
    </figure>
  );
}

export function Yardstick() {
  const [ref, inView] = useInViewRef<HTMLDivElement>();
  const rows = [
    { label: "A top-quarter app, per Amplitude’s data", value: 7 },
    { label: "Our target for Linguini", value: 10, ours: true },
  ];
  return (
    <div ref={ref} className={p.yard} data-inview={inView || undefined}>
      <p className={p.yardHead}>New users still active on day 7</p>
      {rows.map((row, i) => (
        <div key={row.label} className={p.yardRow} data-ours={row.ours || undefined} style={{ ["--i" as string]: i }}>
          <span>{row.label}</span>
          <span className={p.yardTrack}><i style={{ ["--w" as string]: `${row.value * 5}%` }} /></span>
          <b>{row.value}%</b>
        </div>
      ))}
    </div>
  );
}

const followUps = [
  { day: "Day 1", text: "Fix the onboarding bugs people hit on launch day." },
  { day: "Day 3", text: "Talk to five people who came back and five who didn’t." },
  { day: "Day 7", text: "Count second lessons. Fix the biggest drop-off." },
  { day: "Day 14", text: "Publish what we learned, with the real numbers." },
];

export function FollowUps() {
  return (
    <ol className={p.follow}>
      {followUps.map(f => (
        <li key={f.day}><b>{f.day}</b><span>{f.text}</span></li>
      ))}
    </ol>
  );
}

/* ---------- Launches are spikes ---------- */

export function GrowthCurve() {
  const [ref, inView] = useInViewRef<HTMLDivElement>();
  // Weekly active users over ~10 weeks: a launch spike, a plateau, then launch two before the plateau sets in.
  const line = "M0,150 C40,150 50,148 70,146 C80,145 84,60 92,52 C104,44 118,96 150,108 C190,120 220,118 250,117 C262,117 268,112 276,104 C284,30 292,22 300,20 C316,18 330,64 370,74 C410,82 450,80 520,78";
  return (
    <figure className={p.fig}>
      <div ref={ref} className={p.curve} data-inview={inView || undefined}>
        <svg viewBox="0 0 520 170" preserveAspectRatio="none" aria-hidden="true">
          <path className={p.curveArea} d={`${line} L520,170 L0,170 Z`} />
          <path className={p.curveDash} d="M150,108 C190,120 300,122 520,122" />
          <path className={p.curveLine} d={line} />
        </svg>
        <span className={p.pin} style={{ left: "17.7%", top: "30%" }}>Launch 1<small>Sat 17 Oct</small></span>
        <span className={p.pin} data-soon style={{ left: "57.7%", top: "11%" }}>Launch 2<small>Real photo analysis</small></span>
        <span className={p.plateau} style={{ left: "64%", top: "60%" }}>Without it, we flatten here</span>
        <span className={p.planned} style={{ left: "29%", top: "88%" }}>Plan launch 2 here, before it flattens</span>
      </div>
      <figcaption>A sketch, not data: what a launch does to active users, and why the next one is planned now.</figcaption>
    </figure>
  );
}
