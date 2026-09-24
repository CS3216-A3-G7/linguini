// Print a blog post to public/blog/<slug>.pdf with headless Chrome.
// Usage: node scripts/export-post-pdf.mjs [slug] [base-url]
// Build and start the site first (npm run build && npm start). Build with
// NEXT_PUBLIC_SITE_URL set to the production URL so the PDF prints the public link.
// The page receives a `beforeprint` event first, so scroll-driven charts show their final state.
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const slug = process.argv[2] ?? "linguini-business-model";
const base = process.argv[3] ?? "http://localhost:3000";
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "public/blog", `${slug}.pdf`);
const chrome = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9400 + Math.floor(Math.random() * 400);

const proc = spawn(chrome, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${port}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "linguini-pdf-"))}`, "about:blank",
], { stdio: "ignore" });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

try {
  let targets;
  for (let i = 0; i < 50 && !targets; i++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); } catch { await sleep(200); }
  }
  const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
  await new Promise(resolve => ws.addEventListener("open", resolve));
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (pending.has(message.id)) { pending.get(message.id)(message); pending.delete(message.id); }
  });
  const send = (method, params = {}) => new Promise(resolve => {
    const next = ++id;
    pending.set(next, resolve);
    ws.send(JSON.stringify({ id: next, method, params }));
  });

  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await send("Page.enable");
  await send("Page.navigate", { url: `${base}/blog/${slug}` });
  await sleep(3000);
  await send("Runtime.evaluate", { expression: "window.dispatchEvent(new Event('beforeprint'))" });
  await sleep(2500);
  const pdf = await send("Page.printToPDF", { printBackground: true, preferCSSPageSize: true, displayHeaderFooter: false });
  writeFileSync(out, Buffer.from(pdf.result.data, "base64"));
  ws.close();
  console.log(`Wrote ${out}`);
} finally {
  proc.kill();
}
