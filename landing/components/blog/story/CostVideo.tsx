"use client";

import { type CSSProperties, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { lessonSteps, type Pipeline } from "../interactive/data";
import { useInView, useTween } from "./hooks";
import s from "./video.module.css";

type Scene = {
  pipeline: Pipeline;
  /** "bars": one bar per AI call. "stack": the calls merged into one bar. */
  layout: "bars" | "stack";
  label: string;
  caption: string;
  badge?: string;
};

const scenes: Scene[] = [
  { pipeline: "promo", layout: "bars", label: "Today’s prices", caption: "Every photo lesson makes five AI calls. Today they add up to about 1.2¢." },
  { pipeline: "promo", layout: "stack", label: "Today’s prices", caption: "Reading the photo is the big one: more than half of every lesson." },
  { pipeline: "list", layout: "bars", label: "From 1 January 2027", caption: "Gemini 3.7 Flash’s launch discount ends in January, and the lesson nearly doubles.", badge: "+58%" },
  { pipeline: "optimised", layout: "stack", label: "Cheaper models, being tested", caption: "A lighter vision model and smaller text models bring it down to half a cent.", badge: "−75%" },
];

const SCENE_MS = 4200;
const billed = lessonSteps.filter(step => step.id !== "moderation");
const MAX = Math.max(...billed.map(step => step.cost.list));
const TOTAL_MAX = billed.reduce((sum, step) => sum + step.cost.list, 0);
const REDUCED = "(prefers-reduced-motion: reduce)";

function subscribeReduced(onChange: () => void) {
  const query = window.matchMedia(REDUCED);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

function Value({ value }: { value: number }) {
  const shown = useTween(value, 900);
  return <>${shown.toFixed(4)}</>;
}

/** A self-playing chart: starts when it scrolls into view, plays once, then offers a replay. */
export function CostVideo() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, "0px 0px -30% 0px");
  const reduced = useSyncExternalStore(subscribeReduced, () => window.matchMedia(REDUCED).matches, () => false);
  const [index, setIndex] = useState(0);
  const [choice, setChoice] = useState<boolean | null>(null);
  const [finished, setFinished] = useState(false);
  const playing = (choice ?? (inView && !reduced)) && !finished;

  useEffect(() => {
    if (!playing) return;
    const timer = window.setTimeout(() => {
      if (index === scenes.length - 1) setFinished(true);
      else setIndex(index + 1);
    }, SCENE_MS);
    return () => window.clearTimeout(timer);
  }, [playing, index]);

  useEffect(() => {
    const toEnd = () => { setIndex(scenes.length - 1); setFinished(true); };
    window.addEventListener("beforeprint", toEnd);
    return () => window.removeEventListener("beforeprint", toEnd);
  }, []);

  const scene = scenes[index];
  const teal = scene.pipeline === "optimised";
  const total = billed.reduce((sum, step) => sum + step.cost[scene.pipeline], 0);
  const shownTotal = useTween(total, 1100);

  function toggle() {
    if (finished) { setIndex(0); setFinished(false); setChoice(true); return; }
    setChoice(!playing);
  }

  return (
    <figure
      ref={ref}
      className={s.video}
      data-layout={scene.layout}
      data-tone={teal ? "teal" : "tomato"}
      data-started={inView || choice !== null || finished || undefined}
    >
      <div className={s.screen}>
        <div className={s.top}>
          <span className={s.kicker} key={scene.label}>{scene.label}</span>
          <span className={s.total}>
            <b>{(shownTotal * 100).toFixed(2)}¢</b>
            <small>per photo lesson</small>
            {scene.badge ? <em key={scene.badge} className={s.badge}>{scene.badge}</em> : null}
          </span>
        </div>

        <div className={s.plot}>
          <ol className={s.bars}>
          {billed.map((step, i) => {
            const cost = step.cost[scene.pipeline];
            const before = billed.slice(0, i).reduce((sum, item) => sum + item.cost[scene.pipeline], 0);
            const style = {
              "--w": `${(cost / MAX) * 100}%`,
              "--sw": `${(cost / TOTAL_MAX) * 100}%`,
              "--sx": `${(before / TOTAL_MAX) * 100}%`,
              "--i": i,
            } as CSSProperties;
            return (
              <li
                key={step.id}
                className={s.bar}
                style={style}
                data-lead={i === 0 || undefined}
              >
                <span className={s.name}>{step.name}<small>{step.model[scene.pipeline]}</small></span>
                <span className={s.value}><Value value={cost} /></span>
                <span className={s.track}><span className={s.fill} /></span>
              </li>
            );
          })}
        </ol>

        <ul className={s.shares} aria-hidden={scene.layout !== "stack"}>
          {billed.map((step, i) => (
            <li key={step.id} data-lead={i === 0 || undefined} style={{ "--i": i } as CSSProperties}>
              <b>{Math.round((step.cost[scene.pipeline] / total) * 100)}%</b>
              <span>{step.name}</span>
            </li>
          ))}
        </ul>
        </div>

        <p className={s.caption} aria-live="polite" key={index}>{scene.caption}</p>
      </div>

      <div className={s.controls}>
        <button type="button" className={s.play} onClick={toggle} aria-label={finished ? "Replay" : playing ? "Pause" : "Play"}>
          {finished ? (
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M12 5a7 7 0 1 1-6.6 4.7" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" /><path d="M4 4v5h5" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
          ) : playing ? (
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M7 5h3v14H7zM14 5h3v14h-3z" fill="currentColor" /></svg>
          ) : (
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor" /></svg>
          )}
        </button>
        <ol className={s.progress}>
          {scenes.map((item, i) => (
            <li key={i}>
              <button
                type="button"
                aria-label={`Scene ${i + 1}: ${item.label}`}
                aria-current={i === index ? "step" : undefined}
                onClick={() => { setIndex(i); setFinished(false); setChoice(false); }}
              >
                <span
                  key={`${index}-${i}`}
                  className={s.progressFill}
                  data-state={i < index || (i === index && finished) ? "done" : i === index ? (playing ? "playing" : "paused") : "todo"}
                  style={{ animationDuration: `${SCENE_MS}ms` }}
                />
              </button>
            </li>
          ))}
        </ol>
      </div>

      <ol className={s.printCaptions}>
        {scenes.map(item => <li key={item.caption}><b>{item.label}.</b> {item.caption}</li>)}
      </ol>
    </figure>
  );
}
