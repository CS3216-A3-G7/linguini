/* Linguini launch film — every frame is a pure function of time `t` (seconds).
   render.mjs calls window.seek(t) for each frame and screenshots #stage. */

const W = 1920;
const H = 1080;
const stage = document.getElementById("stage");
const PUB = "../../landing/public";
const PASTA_HI = "../../frontend/public/pasta-assets";

/* ---------- timing (overridden from beats.json by render.mjs) ---------- */
const T = { curtain: 0, old: 3.2, idea: 9, spot: 12, montage: 20, play: 28, journal: 36, reveal: 42, end: 49 };
let BEATS = [];
for (let b = 0; b < 200; b++) BEATS.push(b * 0.5);

function beatsIn(a, b) {
  return BEATS.filter(x => x >= a - 1e-6 && x < b - 1e-6);
}
function snap(t) {
  if (!BEATS.length) return t;
  let best = BEATS[0];
  for (const b of BEATS) if (Math.abs(b - t) < Math.abs(best - t)) best = b;
  return best;
}
function lastBeat(t) {
  let lb = -99;
  for (const b of BEATS) { if (b <= t) lb = b; else break; }
  return lb;
}
function pulse(t, decay = 7) {
  return Math.exp(-(t - lastBeat(t)) * decay);
}

/* ---------- helpers ---------- */
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const E = {
  lin: t => t,
  out: t => 1 - Math.pow(1 - t, 3),
  outQuint: t => 1 - Math.pow(1 - t, 5),
  in: t => t * t * t,
  inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: t => { const s = 1.9; return 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2); },
};
function tw(t, t0, t1, a, b, ease = E.out) {
  const p = clamp((t - t0) / (t1 - t0));
  return a + (b - a) * ease(p);
}
function env(t, a, b, fadeIn = 0.25, fadeOut = 0.25) {
  return Math.min(clamp((t - a) / fadeIn), clamp((b - t) / fadeOut));
}
function mulberry(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let r = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}
function el(tag, cls, parent, html) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html !== undefined) n.innerHTML = html;
  (parent || stage).appendChild(n);
  return n;
}
function img(src, cls, parent, w) {
  const n = el("img", cls, parent);
  n.src = src;
  if (w) n.style.width = `${w}px`;
  return n;
}
function set(n, { x = 0, y = 0, s = 1, sx, sy, r = 0, o = 1, blur = 0 } = {}) {
  n.style.transform = `translate(${x}px, ${y}px) rotate(${r}deg) scale(${sx ?? s}, ${sy ?? s})`;
  n.style.opacity = o;
  n.style.filter = blur ? `blur(${blur}px)` : "";
}

/* A photo that covers the frame; children positioned in % of the image stay on their objects. */
function coverPhoto(parent, src, iw, ih) {
  const ar = iw / ih;
  const w = ar > W / H ? H * ar : W;
  const h = w / ar;
  const box = el("div", "photo", parent);
  box.style.width = `${w}px`;
  box.style.height = `${h}px`;
  box.style.marginLeft = `${-w / 2}px`;
  box.style.marginTop = `${-h / 2}px`;
  img(src, "", box);
  return box;
}

function gauge(parent, w = 520) {
  const wrap = el("div", "abs", parent);
  wrap.style.width = `${w}px`;
  wrap.innerHTML = `
  <svg viewBox="0 0 520 300" width="${w}" height="${(w * 300) / 520}">
    <path d="M40 270 A220 220 0 0 1 150 79.5" stroke="#2e9c99" stroke-width="46" fill="none" stroke-linecap="round"/>
    <path d="M150 79.5 A220 220 0 0 1 370 79.5" stroke="#f9ae22" stroke-width="46" fill="none"/>
    <path d="M370 79.5 A220 220 0 0 1 480 270" stroke="#ef5b32" stroke-width="46" fill="none" stroke-linecap="round"/>
    <g class="needle" style="transform-origin: 260px 270px">
      <path d="M252 270 L260 88 L268 270 Z" fill="#263238"/>
    </g>
    <circle cx="260" cy="270" r="26" fill="#263238"/>
  </svg>`;
  return { wrap, needle: wrap.querySelector(".needle") };
}

const MASCOT = `${PUB}/brand/linguini-logo.png`;
const WORDMARK = `${PUB}/brand/linguini-wordmark.png`;
const pastaSrc = n => (n === "farfalle" ? `${PUB}/pasta/farfalle.png` : `${PASTA_HI}/${n}.png`);

/* ---------- scene registry ---------- */
const scenes = [];
function scene(id, from, to, build, update, { pre = 0, post = 0 } = {}) {
  const root = el("div", "scene");
  root.id = id;
  const ctx = build(root);
  scenes.push({ root, from, to, pre, post, ctx, update });
}

/* ===== 1. Curtain ===== */
scene("curtain", "curtain", "old", root => {
  el("div", "abs spot", root);
  el("div", "abs floor", root);
  const mascot = img(MASCOT, "abs", root, 380);
  mascot.style.left = `${W / 2 - 190}px`;
  mascot.style.top = "330px";
  const shadow = el("div", "abs", root);
  Object.assign(shadow.style, { left: `${W / 2 - 150}px`, top: "760px", width: "300px", height: "40px", borderRadius: "50%", background: "rgba(90,60,20,.25)" });
  const L = el("div", "abs drape", root); L.id = "drapeL";
  const R = el("div", "abs drape", root); R.id = "drapeR";
  el("div", "abs valance", root);
  return { mascot, shadow, L, R };
}, (lt, dur, c) => {
  const open = tw(lt, 0.35, 2.1, 0, 1, E.inOut);
  set(c.L, { x: -open * 820, sx: 1 - open * 0.55 });
  set(c.R, { x: open * 820, sx: 1 - open * 0.55 });
  const pop = tw(lt, 1.3, 2.0, 0, 1, E.back);
  const bob = Math.sin(lt * 5) * 6 * clamp(lt - 2);
  const push = tw(lt, 2.2, dur, 1, 1.18, E.in);
  set(c.mascot, { y: (1 - pop) * 120 + bob, s: pop * push, r: Math.sin(lt * 3) * 3 * clamp(lt - 2) });
  set(c.shadow, { s: 0.6 + pop * 0.4, o: pop * 0.9 });
});

/* ===== 2. The old way ===== */
const OLD_WORDS = ["la manzana", "el niño", "la biblioteca", "el elefante", "la abuela", "le parapluie", "la grenouille", "el ferrocarril", "la chaussette", "el bolígrafo", "le hibou", "la cuchara", "el tenedor", "la bouilloire"];
scene("old", "old", "idea", root => {
  const cards = OLD_WORDS.map((w, i) => {
    const c = el("div", "abs flash", root, `<span>${w}</span>`);
    c.style.left = "150px";
    c.style.top = "400px";
    return c;
  });
  const t1 = el("div", "abs display bigText", root, "500 words.");
  const t2 = el("div", "abs display bigText", root, "Forgotten by<br/>Tuesday.");
  t1.style.left = t2.style.left = "180px";
  t1.style.top = "150px";
  t2.style.top = "90px";
  const g = gauge(root, 640);
  g.wrap.style.left = "1100px";
  g.wrap.style.top = "330px";
  const gl = el("div", "abs", root, "Stress");
  Object.assign(gl.style, { left: "1100px", top: "720px", width: "640px", textAlign: "center", fontWeight: 800, fontSize: "40px", color: "#5d6c70" });
  const mascot = img(MASCOT, "abs", root, 220);
  mascot.style.left = "1560px";
  mascot.style.top = "790px";
  const sweat = el("div", "abs", root);
  Object.assign(sweat.style, { left: "1590px", top: "790px", width: "26px", height: "38px", borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%", background: "#7cc4e8" });
  return { cards, t1, t2, g, mascot, sweat };
}, (lt, dur, c) => {
  // flashcards flick past, faster and faster
  const pos = lt * (0.9 + lt * 0.28);
  const span = c.cards.length * 0.55;
  const fall = tw(lt, dur - 0.9, dur, 0, 1, E.in);
  c.cards.forEach((card, i) => {
    const raw = pos - i * 0.55;
    const k = raw < 0 ? raw : raw % span;
    const live = clamp(k) * clamp(1.6 - k);
    const x = (k - 0.5) * 60;
    const drop = fall * (700 + i * 60);
    set(card, { x: x + fall * (i % 2 ? 180 : -120), y: -k * 22 + drop, r: (k - 0.8) * 6 + fall * (i % 2 ? 40 : -35), o: live > 0 ? 1 : 0, s: 0.96 + live * 0.04 });
    card.style.zIndex = 100 - i;
  });
  set(c.t1, { y: tw(lt, 0.15, 0.6, 30, 0), o: env(lt, 0.15, 2.9, 0.3, 0.2) });
  set(c.t2, { y: tw(lt, 3.0, 3.45, 30, 0), o: env(lt, 3.0, dur, 0.3, 0.15) });
  // stress climbs with jitter
  const stress = tw(lt, 0.2, dur - 0.6, 0.05, 0.97, E.in) + Math.sin(lt * 37) * 0.012 * lt;
  c.g.needle.style.transform = `rotate(${-90 + stress * 180}deg)`;
  const shake = lt > dur - 1.2 ? Math.sin(lt * 90) * 6 : 0;
  set(c.g.wrap, { x: shake });
  set(c.mascot, { sy: 1 - stress * 0.12, y: stress * 14, r: -stress * 8 });
  const drip = (lt * 1.3) % 1;
  set(c.sweat, { y: drip * 60, o: clamp(stress * 2 - 0.4) * (1 - drip) });
});

/* ===== 3. The idea ===== */
scene("idea", "idea", "spot", root => {
  const words = ["What", "if", "your", "day", "was", "the", "lesson?"].map((w, i) => {
    const s = el("span", "", undefined, w);
    s.style.display = "inline-block";
    s.style.marginRight = "0.26em";
    return s;
  });
  const line = el("div", "abs display", root);
  Object.assign(line.style, { left: "0", right: "0", top: "330px", textAlign: "center", fontSize: "170px", lineHeight: "1.05" });
  words.forEach((w, i) => { line.appendChild(w); if (i === 3) line.appendChild(document.createElement("br")); });
  words[3].style.color = "#f9ae22";
  words[6].style.color = "#f9ae22";
  const white = el("div", "abs", root); white.id = "flashWhite";
  return { words, white };
}, (lt, dur, c) => {
  c.words.forEach((w, i) => set(w, { y: tw(lt, 0.2 + i * 0.16, 0.6 + i * 0.16, 40, 0), o: tw(lt, 0.2 + i * 0.16, 0.5 + i * 0.16, 0, 1) }));
  c.white.style.opacity = tw(lt, dur - 0.14, dur, 0, 1, E.lin);
});

/* ===== 4. Spot the words ===== */
const GG = [
  { w: "el puente", x: 60, y: 61 },
  { w: "la torre", x: 93, y: 30 },
  { w: "el mar", x: 65, y: 84 },
  { w: "la colina", x: 45, y: 22 },
  { w: "el coche", x: 19, y: 70 },
];
scene("spot", "spot", "montage", root => {
  const box = coverPhoto(root, `${PUB}/photos/golden-gate-bridge.jpg`, 1570, 1047);
  const scan = el("div", "abs scan", root);
  const markers = GG.map((m, i) => {
    const mk = el("div", "marker", box, `<div class="dot">${i + 1}</div><div class="label">${m.w}</div>`);
    mk.style.left = `calc(${m.x}% - 32px)`;
    mk.style.top = `calc(${m.y}% - 32px)`;
    if (m.x > 70) { mk.style.flexDirection = "row-reverse"; mk.style.left = "auto"; mk.style.right = `calc(${100 - m.x}% - 32px)`; mk.style.transformOrigin = "calc(100% - 30px) 50%"; }
    return mk;
  });
  el("div", "abs scrimTop", root);
  const text = el("div", "abs display slam", root, "Your photo.<br/>Your words.");
  Object.assign(text.style, { left: "110px", top: "80px", fontSize: "130px" });
  const mini = el("div", "abs miniGauge", root, "<p>Stress</p>");
  Object.assign(mini.style, { top: "auto", bottom: "70px" });
  const g = gauge(mini, 288);
  g.wrap.style.position = "relative";
  return { box, scan, markers, text, mini, g, flashT: 0 };
}, (lt, dur, c) => {
  set(c.box, { s: tw(lt, 0, dur, 1.1, 1.0, E.lin), x: tw(lt, 0, dur, 30, -30, E.lin) });
  const sweep = tw(lt, 0.25, 1.6, -300, H, E.inOut);
  set(c.scan, { y: sweep, o: env(lt, 0.25, 1.7, 0.1, 0.2) });
  c.markers.forEach((m, i) => {
    const at = c.popTimes[i];
    const p = tw(lt, at, at + 0.42, 0, 1, E.back);
    set(m, { s: p, o: clamp((lt - at) * 8) });
    m.querySelector(".dot").classList.toggle("on", lt >= at && lt < at + 0.5);
  });
  const gi = env(lt, 4.1, dur, 0.35, 0.3);
  set(c.mini, { y: (1 - gi) * 40, o: gi });
  const calm = tw(lt, 4.5, 6.2, 0.97, 0.08, E.inOut) + Math.sin(lt * 9) * 0.01;
  c.g.needle.style.transform = `rotate(${-90 + calm * 180}deg)`;
  set(c.text, { y: tw(lt, 4.3, 4.8, -40, 0), o: env(lt, 4.3, dur, 0.3, 0.2) });
});

/* ===== 5. Montage ===== */
const MONTAGE = [
  { src: "alpine-castle.jpg", w: 2000, h: 1335, chips: [{ t: "le château", s: "the castle", x: 35, y: 44 }] },
  { src: "cafe-interior.jpg", w: 1900, h: 710, chips: [{ t: "la mesa", s: "the table", x: 45, y: 74 }] },
  { src: "desk-flatlay.jpg", w: 1900, h: 1267, chips: [{ t: "le cahier", s: "the notebook", x: 40, y: 48 }] },
  { src: "paris-rooftops.jpg", w: 1440, h: 642, chips: [{ t: "la tour", s: "the tower", x: 61, y: 27 }] },
  { src: "sunlit-promenade.jpg", w: 1950, h: 1300, chips: [{ t: "la farola", s: "the streetlight", x: 29, y: 21 }] },
  { src: "mountain-chalet.jpg", w: 1200, h: 800, chips: [{ t: "la piscine", s: "the pool", x: 52, y: 56 }] },
  { src: "hillside-street.jpg", w: 1570, h: 1047, chips: [{ t: "la flor", s: "the flower", x: 20, y: 62 }] },
  { src: "mountain-peaks.jpg", w: 2000, h: 1357, chips: [{ t: "la montagne", s: "the mountain", x: 62, y: 42 }] },
];
scene("montage", "montage", "play", root => {
  const shots = MONTAGE.map(m => {
    const box = coverPhoto(root, `${PUB}/photos/${m.src}`, m.w, m.h);
    const chips = m.chips.map(ch => {
      const n = el("div", "chip", box, `${ch.t}<small>${ch.s}</small>`);
      n.style.left = `${ch.x}%`;
      n.style.top = `${ch.y}%`;
      return n;
    });
    return { box, chips };
  });
  el("div", "abs scrim", root);
  const words = ["Every photo.", "Every place.", "A lesson."].map(w => {
    const n = el("div", "abs display slam", root, w);
    Object.assign(n.style, { left: "0", right: "0", textAlign: "center", bottom: "90px" });
    return n;
  });
  return { shots, words };
}, (lt, dur, c) => {
  const cuts = c.cuts;
  let idx = 0;
  for (let i = 0; i < cuts.length; i++) if (lt >= cuts[i]) idx = i;
  c.shots.forEach((s, i) => {
    const on = i === Math.min(idx, c.shots.length - 1);
    s.box.style.visibility = on ? "visible" : "hidden";
    if (!on) return;
    const since = lt - cuts[i];
    set(s.box, { s: 1.14 - Math.min(since, 1.2) * 0.07 - tw(since, 0, 0.18, 0.04, 0, E.out) });
    s.chips.forEach(ch => {
      const p = tw(since, 0.08, 0.45, 0, 1, E.back);
      ch.style.transform = `translate(-50%, -100%) scale(${p})`;
      ch.style.opacity = clamp(since * 8);
    });
  });
  const thirds = c.textCuts;
  c.words.forEach((w, i) => {
    const a = thirds[i];
    const b = thirds[i + 1] ?? dur;
    const since = lt - a;
    const on = lt >= a && lt < b;
    set(w, { s: on ? tw(since, 0, 0.25, 1.25, 1, E.outQuint) : 1, o: on ? clamp(since * 10) * env(lt, a, b, 0.01, 0.12) : 0 });
  });
});

/* ===== 6. Play (the joy room) ===== */
scene("play", "play", "journal", root => {
  const pastas = [];
  const R = mulberry(7);
  const spots = [[120, 120], [1640, 90], [70, 760], [1700, 800], [860, 40], [980, 930], [560, 880], [1380, 60]];
  const names = ["fusilli", "farfalle", "penne", "macaroni", "farfalle", "fusilli", "macaroni", "penne"];
  spots.forEach(([x, y], i) => {
    const p = img(pastaSrc(names[i]), "pasta", root, 150 + R() * 60);
    p.style.left = `${x}px`;
    p.style.top = `${y}px`;
    pastas.push({ n: p, phase: R() * 6, dir: i % 2 ? 1 : -1, base: (R() - 0.5) * 40 });
  });
  const headline = el("div", "abs display", root, "Hear it.<br/>Play it.<br/>Keep it.");
  Object.assign(headline.style, { left: "150px", top: "300px", fontSize: "150px", color: "#184f4e" });
  const lines = headline.innerHTML.split("<br>").length;
  const card = el("div", "abs card", root, `
    <div class="lbl">noun · masculine</div>
    <div class="speak"><svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9.5v5h3.5L12 18.5v-13L7.5 9.5H4Z"/><path d="M15.5 9a4 4 0 0 1 0 6"/><path d="M18 6.5a7.5 7.5 0 0 1 0 11"/></svg></div>
    <div class="word">el puente</div><div class="mean">the bridge</div><div class="ipa">/ˈpwente/</div>`);
  Object.assign(card.style, { left: "1000px", top: "150px" });
  const says = el("div", "abs says", root, `
    <div class="who"><img src="${MASCOT}" width="54" height="54"/> Linguini says</div>
    <div class="clue">Veo, veo… algo que es azul y está debajo del puente.</div>
    <div class="choices"><div class="choice">el coche</div><div class="choice">la torre</div><div class="choice ok-target">el mar</div><div class="choice">la colina</div></div>`);
  Object.assign(says.style, { left: "980px", top: "250px" });
  const target = says.querySelector(".ok-target");
  const xp = el("div", "abs xp", root, "+15 XP");
  Object.assign(xp.style, { left: "1540px", top: "200px" });
  const days = ["M", "T", "W", "T", "F", "S", "S"];
  const streak = el("div", "abs streak", root, days.map(d => `<div class="day"><div class="slot"><div class="ring"></div><img src="${PUB}/pasta/farfalle.png" width="84"/></div>${d}</div>`).join(""));
  Object.assign(streak.style, { left: "990px", top: "820px" });
  const farf = [...streak.querySelectorAll(".slot img")];
  const rings = [...streak.querySelectorAll(".ring")];
  farf.forEach(f => { f.style.position = "absolute"; });
  return { pastas, headline, card, says, target, xp, streak, farf, rings, lines };
}, (lt, dur, c) => {
  const pl = pulse(c.t0 + lt);
  c.pastas.forEach((p, i) => {
    const wob = Math.sin(lt * 3.2 + p.phase);
    set(p.n, { y: -pl * 38 + wob * 10, r: p.base + wob * 12 * p.dir + pl * 10 * p.dir, sx: 1 + pl * 0.08, sy: 1 - pl * 0.08, o: tw(lt, 0.05 + i * 0.05, 0.35 + i * 0.05, 0, 1) });
  });
  set(c.headline, { x: tw(lt, 0, 0.5, -60, 0), o: tw(lt, 0, 0.35, 0, 1) });
  // word card flips in, then hands over to the I-Spy card
  const flip = tw(lt, 0.1, 0.7, 90, 0, E.out);
  c.card.style.transform = `perspective(1600px) rotateY(${flip}deg) translateY(${tw(lt, 2.0, 2.5, 0, -40, E.inOut)}px) scale(${tw(lt, 2.0, 2.5, 1, 0.88)})`;
  c.card.style.opacity = env(lt, 0.1, 2.6, 0.2, 0.25);
  const sIn = tw(lt, 2.2, 2.75, 0, 1, E.out);
  set(c.says, { y: (1 - sIn) * 80 - tw(lt, 5.0, 5.5, 0, 150, E.inOut), o: sIn, s: 0.95 + sIn * 0.05 });
  const ok = lt >= c.tick;
  c.target.classList.toggle("ok", ok);
  c.target.innerHTML = ok ? `<span style="display:inline-flex;gap:12px;align-items:center"><svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>el mar</span>` : "el mar";
  const xpIn = tw(lt, c.tick + 0.1, c.tick + 0.5, 0, 1, E.back);
  set(c.xp, { y: (1 - xpIn) * 40 - tw(lt, c.tick + 0.6, c.tick + 1.6, 0, 30), s: xpIn, o: env(lt, c.tick + 0.1, c.tick + 2.2, 0.05, 0.3) });
  const stIn = tw(lt, 5.0, 5.5, 0, 1, E.out);
  set(c.streak, { y: (1 - stIn) * 120 - tw(lt, 5.0, 5.5, 0, 50, E.inOut), o: stIn });
  c.farf.forEach((f, i) => {
    const at = c.dayTimes[i];
    const p = tw(lt, at, at + 0.35, 0, 1, E.back);
    set(f, { s: p, o: clamp((lt - at) * 10), r: (1 - p) * -40 });
    c.rings[i].style.opacity = lt >= at ? 0 : 1;
  });
});

/* ===== 7. Journal ===== */
const JOURNAL = [
  { imgs: ["golden-gate-bridge.jpg", "hillside-street.jpg", "sunlit-promenade.jpg"], title: "El puente rojo", body: "Hoy crucé el <mark>puente</mark> en <mark>coche</mark>. Desde arriba vi el <mark>mar</mark> azul.", date: "Saturday, 19 Sep", x: 70, y: 70, r: -5 },
  { imgs: ["desk-flatlay.jpg"], title: "Un día de estudio", body: "Escribí diez palabras nuevas en mi <mark>libreta</mark> con un <mark>lápiz</mark> amarillo.", date: "Monday, 21 Sep", x: 500, y: 120, r: 3 },
  { imgs: ["paris-rooftops.jpg", "alpine-castle.jpg", "mountain-chalet.jpg"], title: "Un soir à Paris", body: "D’en haut, j’ai vu le <mark>fleuve</mark>, un <mark>pont</mark> et la <mark>tour</mark> Eiffel.", date: "Wednesday, 23 Sep", x: 930, y: 60, r: -2 },
  { imgs: ["cafe-interior.jpg"], title: "Un matin au café", body: "J’ai lu sur un <mark>canapé</mark>, près d’une <mark>table</mark> en bois.", date: "Thursday, 24 Sep", x: 690, y: 460, r: 4 },
  { imgs: ["summer-meadow.jpg", "mountain-peaks.jpg"], title: "Picnic en el campo", body: "Comimos en la <mark>hierba</mark>, entre <mark>flores</mark> blancas.", date: "Friday, 25 Sep", x: 220, y: 430, r: -3 },
];
scene("journal", "journal", "reveal", root => {
  const cards = JOURNAL.map(j => {
    const [a, ...rest] = j.imgs;
    const side = rest.map(s => `<img src="${PUB}/photos/${s}"/>`).join("");
    const grid = rest.length ? `<div class="jgrid"><img class="main" src="${PUB}/photos/${a}"/>${side}${rest.length === 1 ? "" : ""}</div>` : `<div class="jgrid" style="grid-template-columns:1fr"><img class="main" src="${PUB}/photos/${a}"/></div>`;
    const n = el("div", "jcard", root, `${grid}<div class="jtitle">${j.title}</div><div class="jbody">${j.body}</div><div class="jdate">${j.date}</div>`);
    if (rest.length === 1) n.querySelector(".jgrid img:last-child").style.gridRow = "1 / -1";
    n.style.left = `${j.x}px`;
    n.style.top = `${j.y}px`;
    return { n, j };
  });
  const t1 = el("div", "abs display", root, "Your life,<br/>in Spanish.");
  const t2 = el("div", "abs display", root, "Et en<br/>français.");
  [t1, t2].forEach(t => Object.assign(t.style, { right: "110px", top: "600px", fontSize: "124px", textAlign: "right", color: "#263238", zIndex: 50 }));
  t2.style.color = "#c84725";
  return { cards, t1, t2 };
}, (lt, dur, c) => {
  const collapse = tw(lt, dur - 0.5, dur, 0, 1, E.in);
  c.cards.forEach((card, i) => {
    const at = c.cardTimes[i];
    const p = tw(lt, at, at + 0.55, 0, 1, E.out);
    const cx = W / 2 - 260 - card.j.x;
    const cy = H / 2 - 220 - card.j.y;
    set(card.n, { x: (1 - p) * (i % 2 ? 700 : -700) + collapse * cx, y: (1 - p) * 300 + collapse * cy, r: card.j.r + (1 - p) * (i % 2 ? 25 : -25) - collapse * card.j.r, o: clamp((lt - at) * 6) * (1 - collapse * 0.6), s: 1 - collapse * 0.6 });
    card.n.style.zIndex = 10 + i;
  });
  set(c.t1, { y: tw(lt, 0.4, 0.9, 40, 0), o: env(lt, 0.4, c.swap, 0.3, 0.15) * (1 - collapse) });
  set(c.t2, { y: tw(lt, c.swap, c.swap + 0.5, 40, 0), o: env(lt, c.swap, dur, 0.2, 0.3) });
});

/* ===== 8. Reveal ===== */
scene("reveal", "reveal", "end", root => {
  const R = mulberry(21);
  const names = ["fusilli", "farfalle", "penne", "macaroni"];
  const burst = Array.from({ length: 22 }, (_, i) => {
    const n = img(pastaSrc(names[i % 4]), "pasta", root, 90 + R() * 90);
    n.style.left = `${W / 2 - 60}px`;
    n.style.top = `${H / 2 - 60}px`;
    const a = (i / 22) * Math.PI * 2 + R() * 0.3;
    return { n, a, d: 520 + R() * 520, spin: (R() - 0.5) * 540 };
  });
  const mascot = img(MASCOT, "abs", root, 250);
  Object.assign(mascot.style, { left: `${W / 2 - 125}px`, top: "170px" });
  const mark = img(WORDMARK, "abs", root, 690);
  Object.assign(mark.style, { left: `${W / 2 - 345}px`, top: "400px" });
  const tag = el("div", "abs tag", root, "Learn the language of your day.");
  Object.assign(tag.style, { left: "0", right: "0", top: "660px", textAlign: "center" });
  const pill = el("div", "abs pill", root, `Live on Product Hunt <b>·</b> linguini-landing.vercel.app`);
  Object.assign(pill.style, { left: "50%", top: "830px" });
  const white = el("div", "abs", root);
  Object.assign(white.style, { inset: 0, background: "#fff" });
  return { burst, mascot, mark, tag, pill, white };
}, (lt, dur, c) => {
  const hit = c.hit;
  c.white.style.opacity = env(lt, hit - 0.02, hit + 0.35, 0.02, 0.33) * 0.85;
  c.burst.forEach(b => {
    const p = tw(lt, hit, hit + 1.6, 0, 1, E.outQuint);
    const fallY = Math.max(0, lt - hit - 0.4) ** 2 * 140;
    set(b.n, { x: Math.cos(b.a) * b.d * p, y: Math.sin(b.a) * b.d * p * 0.75 + fallY, r: b.spin * p, s: lt < hit ? 0 : 0.6 + p * 0.5, o: lt < hit ? 0 : 1 - clamp((lt - hit - 1.4) / 1.2) });
  });
  const m = tw(lt, hit, hit + 0.55, 0, 1, E.back);
  set(c.mascot, { s: m, y: (1 - m) * 60 + Math.sin(lt * 4) * 5 * clamp(lt - hit - 0.6), o: clamp((lt - hit) * 10) });
  const wm = tw(lt, hit + 0.1, hit + 0.55, 1.5, 1, E.outQuint);
  set(c.mark, { s: wm, o: clamp((lt - hit - 0.1) * 8) });
  set(c.tag, { y: tw(lt, hit + 0.9, hit + 1.4, 30, 0), o: tw(lt, hit + 0.9, hit + 1.3, 0, 1) });
  const pi = tw(lt, hit + 1.8, hit + 2.3, 0, 1, E.back);
  c.pill.style.transform = `translateX(-50%) scale(${pi})`;
  c.pill.style.opacity = clamp((lt - hit - 1.8) * 6);
  stage.style.filter = "";
  c.fade = tw(lt, dur - 0.8, dur, 0, 1, E.inOut);
});
const fadeOut = el("div", "abs");
Object.assign(fadeOut.style, { inset: 0, background: "#000", opacity: 0, zIndex: 999 });

/* ---------- configure from music ---------- */
let RISER = 1.6;
function configure(cfg = {}) {
  if (cfg.T) Object.assign(T, cfg.T);
  if (cfg.riserLen) RISER = cfg.riserLen;
  if (cfg.beats && cfg.beats.length) BEATS = cfg.beats.slice().sort((a, b) => a - b);
  const get = id => scenes.find(s => s.root.id === id).ctx;

  const spot = get("spot");
  const firstPop = T.spot + 1.7;
  const pops = beatsIn(firstPop - 0.1, T.spot + 5).slice(0, 5);
  while (pops.length < 5) pops.push(firstPop + pops.length * 0.45);
  spot.popTimes = pops.map(b => b - T.spot);

  const mon = get("montage");
  const mb = beatsIn(T.montage, T.play);
  const step = Math.max(1, Math.round(mb.length / MONTAGE.length));
  mon.cuts = MONTAGE.map((_, i) => (mb[i * step] ?? T.montage + (i * (T.play - T.montage)) / MONTAGE.length) - T.montage);
  mon.cuts[0] = 0;
  const md = T.play - T.montage;
  mon.textCuts = [0, snap(T.montage + md / 3) - T.montage, snap(T.montage + (2 * md) / 3) - T.montage];

  const play = get("play");
  play.t0 = T.play;
  play.tick = snap(T.play + 3.4) - T.play;
  const db = beatsIn(T.play + 5.4, T.journal);
  play.dayTimes = Array.from({ length: 7 }, (_, i) => (db[i] ?? T.play + 5.4 + i * 0.3) - T.play);

  const jr = get("journal");
  const jb = beatsIn(T.journal + 0.2, T.reveal - 1);
  jr.cardTimes = JOURNAL.map((_, i) => (jb[i] ?? T.journal + 0.3 + i * 0.5) - T.journal);
  jr.swap = snap(T.journal + (T.reveal - T.journal) * 0.55) - T.journal;

  const rv = get("reveal");
  rv.hit = 0.0;
}

/* SFX cue sheet for render.mjs (absolute seconds). */
function cues() {
  const g = id => scenes.find(s => s.root.id === id).ctx;
  const list = [];
  const add = (t, sfx, vol = 1) => list.push({ t: Math.max(0, +t.toFixed(3)), sfx, vol });
  add(T.curtain + 0.3, "curtain", 0.9);
  add(T.curtain + 1.3, "pop", 0.8);
  {
    const dur = T.idea - T.old;
    let prev = -1;
    let last = -1;
    for (let lt = 0; lt < dur - 0.9; lt += 0.01) {
      const n = Math.floor((lt * (0.9 + lt * 0.28)) / 0.55);
      if (n !== prev && lt - last > 0.14) { add(T.old + lt, "flip", Math.min(0.75, 0.3 + lt * 0.07)); last = lt; }
      prev = n;
    }
  }
  add(T.idea - 0.9, "whoosh", 0.5);
  add(T.spot - 0.02, "shutter", 1);
  g("spot").popTimes.forEach((p, i) => add(T.spot + p, i % 2 ? "pop2" : "pop", 0.75));
  add(T.spot + 4.5, "chime", 0.45);
  add(T.montage - RISER, "riser", 0.8);
  g("montage").cuts.forEach((c, i) => add(T.montage + c, i % 2 ? "pop2" : "pop", 0.5));
  add(T.play - 0.08, "whoosh", 0.6);
  add(T.play + 0.1, "flip", 0.7);
  add(T.play + 2.2, "flip", 0.5);
  add(T.play + g("play").tick, "chime", 0.8);
  add(T.play + g("play").tick + 0.12, "xp", 0.7);
  g("play").dayTimes.forEach((d, i) => add(T.play + d, i % 2 ? "pop2" : "pop", 0.55));
  add(T.journal - 0.08, "whoosh", 0.55);
  g("journal").cardTimes.forEach((c, i) => add(T.journal + c, i % 2 ? "page2" : "page", 0.6));
  add(T.reveal - RISER, "riser", 0.9);
  add(T.reveal, "impact-soft", 1);
  add(T.reveal, "impact", 0.4);
  add(T.reveal + 0.15, "cheer", 0.32);
  add(T.reveal + 1.8, "chime", 0.6);
  return list.sort((a, b) => a.t - b.t);
}

/* ---------- seek ---------- */
function seek(t) {
  for (const s of scenes) {
    const a = T[s.from] - s.pre;
    const b = T[s.to] + s.post;
    const on = t >= a && t < b;
    s.root.style.visibility = on ? "visible" : "hidden";
    if (on) s.update(t - T[s.from], T[s.to] - T[s.from], s.ctx);
  }
  const rv = scenes.find(s => s.root.id === "reveal").ctx;
  fadeOut.style.opacity = t >= T.reveal ? (rv.fade || 0) : 0;
}

window.configure = configure;
window.cues = cues;
window.seek = seek;
window.TIMING = T;
window.filmReady = Promise.all([document.fonts.ready, ...[...document.images].map(i => (i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; })))]);

configure();
const qs = new URLSearchParams(location.search);
seek(parseFloat(qs.get("t") || "0"));
