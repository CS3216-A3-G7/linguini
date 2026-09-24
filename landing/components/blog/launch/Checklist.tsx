"use client";

import { useSyncExternalStore } from "react";
import l from "./launch.module.css";

type Item = { text: string; owner: string };
type Phase = { title: string; when: string; items: Item[] };

/** Same shape as launch/checklist.md. Keep the two in step. */
export const phases: Phase[] = [
  {
    title: "Three weeks out",
    when: "by 26 Sep",
    items: [
      { text: "Agree the promise: browser demo open to everyone, learner app in beta", owner: "Product" },
      { text: "Point every landing-page button at the production app, then tap each one on a phone", owner: "Eng" },
      { text: "Make every landing claim match the app today: photo analysis, speech, Plus trial", owner: "Product" },
      { text: "Track demo started, demo finished, sign-up, first lesson, second lesson", owner: "Eng" },
    ],
  },
  {
    title: "Two weeks out",
    when: "by 3 Oct",
    items: [
      { text: "Recruit 10 to 20 beta testers learning Spanish or French", owner: "Beta" },
      { text: "Watch five of them use it cold. Fix whatever confused two or more", owner: "Beta" },
      { text: "Draft the listing on a personal Product Hunt account and add every maker", owner: "PH" },
      { text: "Upload the explainer to YouTube as unlisted, with captions", owner: "Marketing" },
    ],
  },
  {
    title: "One week out",
    when: "by 10 Oct",
    items: [
      { text: "Swap in the X header and LinkedIn cover", owner: "Marketing" },
      { text: "Reread the rules of every community on our list; message the r/Spanish mods", owner: "Outreach" },
      { text: "Personal note to Lindie Botes and ten smaller language creators, with no ask to post", owner: "Outreach" },
      { text: "Ask NUS Hackers for a Friday Hacks demo slot", owner: "Outreach" },
      { text: "Schedule the listing for Sat 17 Oct, 00:01 Pacific", owner: "PH" },
    ],
  },
  {
    title: "Three days out",
    when: "Wed 14 Oct",
    items: [
      { text: "Countdown post and story", owner: "Marketing" },
      { text: "Tell friends and testers the date, and ask who wants a message on the day", owner: "Outreach" },
      { text: "Write the duty rota: afternoon, night and morning shifts in Singapore time", owner: "Incident" },
    ],
  },
  {
    title: "Day before",
    when: "Fri 16 Oct",
    items: [
      { text: "Go or no-go: buttons work, a stranger can sign up, analytics arrive, inbox staffed, someone can roll back", owner: "Product" },
      { text: "Freeze the copy and the assets. No edits after this", owner: "Marketing" },
    ],
  },
  {
    title: "Launch day",
    when: "Sat 17 Oct, 3:01pm SGT",
    items: [
      { text: "First comment up within a minute of going live", owner: "PH" },
      { text: "X thread, Instagram post and story, LinkedIn out by 3:10pm", owner: "Marketing" },
      { text: "Every Product Hunt comment answered within the hour", owner: "Community" },
      { text: "Hourly check of errors, sign-ups and demo completions", owner: "Eng" },
    ],
  },
  {
    title: "After",
    when: "D+1 to D+14",
    items: [
      { text: "Swap [PH_POST_URL] into every post, and add the Product Hunt badge to the landing page", owner: "Eng" },
      { text: "D+1: fix the onboarding bugs people hit on the day", owner: "Eng" },
      { text: "D+3: talk to five people who came back and five who didn’t", owner: "Product" },
      { text: "D+7: look at who did a second lesson; fix the biggest drop-off", owner: "Product" },
      { text: "D+14: publish what we learned, with the real numbers", owner: "Marketing" },
      { text: "Put the next launch on the calendar: real photo analysis", owner: "Product" },
    ],
  },
];

const KEY = "linguini-launch-checklist";
const total = phases.reduce((n, p) => n + p.items.length, 0);

// Progress lives in localStorage; `memory` keeps it working for this visit when storage is blocked.
let memory = "{}";
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

function read() {
  try {
    return window.localStorage.getItem(KEY) ?? memory;
  } catch {
    return memory;
  }
}

function write(value: Record<string, boolean>) {
  memory = JSON.stringify(value);
  try {
    window.localStorage.setItem(KEY, memory);
  } catch {
    // Ignore: progress just won't survive a reload.
  }
  listeners.forEach(listener => listener());
}

function parse(raw: string): Record<string, boolean> {
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

export function Checklist() {
  const done = parse(useSyncExternalStore(subscribe, read, () => "{}"));
  const toggle = (id: string) => write({ ...done, [id]: !done[id] });
  const count = Object.values(done).filter(Boolean).length;

  return (
    <div className={l.checklist}>
      <div className={l.checkHead}>
        <span>{count} of {total} done</span>
        <button type="button" className={l.checkReset} onClick={() => write({})}>Reset</button>
        <span className={l.checkMeter}><span style={{ transform: `scaleX(${count / total})` }} /></span>
      </div>
      {phases.map(phase => (
        <section key={phase.title} className={l.phase}>
          <h4>{phase.title} <small>{phase.when}</small></h4>
          <ul className={l.items}>
            {phase.items.map(item => {
              const id = `${phase.title}:${item.text}`;
              return (
                <li key={id}>
                  <label className={l.item}>
                    <input type="checkbox" checked={!!done[id]} onChange={() => toggle(id)} />
                    <span>{item.text}</span>
                    <small>{item.owner}</small>
                  </label>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
