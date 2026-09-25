"use client";

import { useEffect, useRef, useState } from "react";
import { Speaker, SpeakerOff } from "./icons";
import styles from "./Film.module.css";

/** The launch film as a muted loop between the hero and the pitch. Plays only while on screen, and stays on its poster for reduced-motion users. */
export function Film() {
  const ref = useRef<HTMLVideoElement>(null);
  const [muted, setMuted] = useState(true);

  useEffect(() => {
    const video = ref.current;
    if (!video) return;
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    let inView = false;
    const sync = () => {
      if (inView && (!query.matches || !video.muted)) void video.play().catch(() => {});
      else video.pause();
    };
    const observer = new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      sync();
    }, { rootMargin: "200px 0px" });
    observer.observe(video);
    query.addEventListener("change", sync);
    return () => {
      observer.disconnect();
      query.removeEventListener("change", sync);
    };
  }, []);

  // Turning the sound on restarts the film so the score lines up with the cuts.
  const toggleSound = () => {
    const video = ref.current;
    if (!video) return;
    const next = !muted;
    video.muted = next;
    if (!next) {
      video.currentTime = 0;
      void video.play().catch(() => {});
    }
    setMuted(next);
  };

  return (
    <div className={`container ${styles.wrap}`}>
      <div className={styles.frame}>
        <video
          ref={ref}
          className={styles.video}
          poster="/film/poster.jpg"
          muted
          loop
          playsInline
          preload="none"
          aria-label="Linguini launch film: everyday moments, each labelled with its word in Spanish and French"
        >
          <source src="/film/linguini-film-1080p.mp4" type="video/mp4" media="(min-width: 900px)" />
          <source src="/film/linguini-film-720p.mp4" type="video/mp4" />
        </video>
        <button type="button" className={styles.sound} onClick={toggleSound} aria-pressed={!muted}>
          {muted ? <SpeakerOff size={18} /> : <Speaker size={18} />}
          {muted ? "Sound on" : "Sound off"}
        </button>
      </div>
    </div>
  );
}
