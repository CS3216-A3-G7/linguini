// Renders film.html frame by frame and mixes the soundtrack.
// Usage: node render.mjs [--fps 30] [--from 0] [--to <s>] [--out out/linguini-launch.mp4]
// Needs: a static server on http://127.0.0.1:8091 serving the repo root, Playwright, ffmpeg.
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const here = path.dirname(new URL(import.meta.url).pathname);
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith("--") ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const fps = Number(args.fps ?? 30);
const timing = JSON.parse(fs.readFileSync(path.join(here, "timing.json"), "utf8"));
const from = Number(args.from ?? 0);
const to = Number(args.to ?? timing.T.end);
const out = path.resolve(here, args.out ?? "out/linguini-launch.mp4");
const frames = path.resolve(args.frames ?? "/tmp/linguini-frames");
const skipFrames = process.argv.includes("--skip-frames");
if (!skipFrames) {
  fs.rmSync(frames, { recursive: true, force: true });
  fs.mkdirSync(frames, { recursive: true });
}
fs.mkdirSync(path.dirname(out), { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.CHROME ?? "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto("http://127.0.0.1:8091/marketing/promo-video/film.html", { waitUntil: "networkidle" });
await page.evaluate(() => window.filmReady);
await page.evaluate(cfg => window.configure(cfg), timing);
const cues = await page.evaluate(() => window.cues());
fs.writeFileSync(path.join(here, "cues.json"), JSON.stringify(cues, null, 1));

const stage = page.locator("#stage");
const total = Math.round((to - from) * fps);
for (let i = 0; i < (skipFrames ? 0 : total); i++) {
  const t = from + i / fps;
  await page.evaluate(t => window.seek(t), t);
  await stage.screenshot({ path: path.join(frames, `f${String(i).padStart(5, "0")}.jpg`), type: "jpeg", quality: 92 });
  if (i % 300 === 0) console.log(`frame ${i}/${total}`);
}
await browser.close();

// Soundtrack: music + every SFX cue delayed to its time.
const audioDir = path.join(here, "audio");
const inputs = ["-framerate", String(fps), "-i", path.join(frames, "f%05d.jpg")];
const filters = [];
let n = 1;
const music = path.join(audioDir, "music.flac");
const mixIns = [];
if (fs.existsSync(music)) {
  inputs.push("-ss", String(from), "-i", music);
  filters.push(`[${n}:a]volume=${timing.musicGain ?? 0.9}[m]`);
  mixIns.push("[m]");
  n++;
}
for (const c of cues) {
  if (c.t < from || c.t > to) continue;
  const f = path.join(audioDir, `sfx-${c.sfx}.wav`);
  if (!fs.existsSync(f)) continue;
  inputs.push("-i", f);
  const ms = Math.round((c.t - from) * 1000);
  filters.push(`[${n}:a]adelay=${ms}|${ms},volume=${(c.vol * (timing.sfxGain ?? 0.7)).toFixed(3)}[s${n}]`);
  mixIns.push(`[s${n}]`);
  n++;
}
const dur = (to - from).toFixed(3);
const fadeStart = Math.max(0, to - from - 1.2).toFixed(3);
const ffArgs = ["-y", "-loglevel", "error", ...inputs];
if (mixIns.length) {
  filters.push(`${mixIns.join("")}amix=inputs=${mixIns.length}:normalize=0:duration=longest,afade=t=out:st=${fadeStart}:d=1.2,volume=1.25,alimiter=limit=0.84:level=false,atrim=0:${dur}[aout]`);
  ffArgs.push("-filter_complex", filters.join(";"), "-map", "0:v", "-map", "[aout]", "-c:a", "aac", "-b:a", "192k");
}
ffArgs.push("-c:v", "libx264", "-preset", "slow", "-crf", String(args.crf ?? 20), "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", dur, out);
execFileSync("ffmpeg", ffArgs, { stdio: "inherit" });
console.log("wrote", out, fs.statSync(out).size, "bytes");
