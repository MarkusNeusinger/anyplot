#!/usr/bin/env node
// anyplot.ai — the boundary probe of the downloadable plot.html (JS-4b)
// =============================================================================
//
// A JavaScript plot's plot.html is the harness's page (automation/js-render/
// render.mjs, ANYPLOT_PAGE_ONLY=1) inside the agents service's wrapper
// (agents/anyplot/render/page.py): a document with no script of its own, the
// harness's content security policy plus `frame-src 'none'`, and the page in an
// <iframe sandbox="allow-scripts" srcdoc=...>. This probe opens such a wrapper
// from file://, as a user opens the download, in Playwright's Chromium, and
// checks what step 3g of agentic/specs/261024-agent-all-libraries.md promises:
//
//   - the plot drew in the frame (a canvas with painted pixels, or SVG shapes),
//     and, with --hover, hovering it changes the frame (a tooltip): the scaled
//     frame passes pointer events on;
//   - the frame's origin is opaque ("null");
//   - with --attempts, the snippet's own attempts all failed: setting
//     top.location, window.open, fetch, storage and cookies, and, last,
//     navigating its own frame to an http URL; a local listener sees no
//     request, and no popup, download or dialog appears.
//
// Usage:
//   node page_probe.mjs snippet <chartjs|d3|echarts|highcharts>    print the probe's plot code
//   node page_probe.mjs check <plot.html> [--hover] [--attempts]
//
// The snippets read window.ANYPLOT_DATA as {label, value} rows; the checker
// prints one JSON report and exits 1 when a check failed. Playwright comes from
// ANYPLOT_NODE_MODULES (the image's /opt/anyplot/node_modules) or the checkout's
// node_modules; the browser from PLAYWRIGHT_BROWSERS_PATH. The listener binds
// the loopback, which a container without network still has. It runs in the
// renderer image's CI step (ci-image.yml) and in
// tests/unit/agents/code/test_profile_javascript_page_image.py.
// =============================================================================

import http from "node:http";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PORT = 18731;
const LISTENER = `http://127.0.0.1:${PORT}`;
const SETTLE_MS = 1500;
const TIMEOUT_MS = 20000;
const VIEWPORT = { width: 1440, height: 790 }; // a laptop's window: the wrapper scales the frame to 0.8
const MIN_PAINTED = 1000;
const MIN_SHAPES = 3;

// The escape attempts, after the plot drew. Each records "refused <Error>" or
// its value; the frame's self-navigation waits for the checker, since it ends
// the plot.
const ATTEMPTS = `
window.__anyplotProbe = {};
(function () {
  var probe = window.__anyplotProbe;
  var record = function (name, run) {
    try {
      var value = run();
      probe[name] = value === undefined ? "ok" : String(value);
    } catch (e) {
      probe[name] = "refused " + e.name;
    }
  };
  record("origin", function () { return self.origin; });
  record("top_location", function () { top.location = "${LISTENER}/top"; });
  record("window_open", function () { return window.open("${LISTENER}/popup"); });
  record("storage", function () { return localStorage.length; });
  record("cookie", function () { return document.cookie; });
  fetch("${LISTENER}/fetch").then(
    function () { probe.fetch = "ok"; },
    function (e) { probe.fetch = "refused " + e.name; }
  );
  window.__anyplotProbeNavigate = function () { location.href = "${LISTENER}/self"; };
})();
`;

const SNIPPETS = {
  chartjs: `const t = window.ANYPLOT_TOKENS;
const data = window.ANYPLOT_DATA;
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);
new Chart(canvas, {
  type: "bar",
  data: {
    labels: data.map((row) => String(row.label)),
    datasets: [{ label: "value", data: data.map((row) => row.value), backgroundColor: t.palette[0] }],
  },
  options: { animation: false, responsive: true, maintainAspectRatio: false },
});
`,
  d3: `const t = window.ANYPLOT_TOKENS;
const data = window.ANYPLOT_DATA;
const { width, height } = window.ANYPLOT_SIZE;
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const x = d3.scaleBand().domain(data.map((d) => String(d.label))).range([80, width - 40]).padding(0.2);
const y = d3.scaleLinear().domain([0, d3.max(data, (d) => d.value)]).range([height - 60, 40]);
const tip = svg.append("text").attr("x", 100).attr("y", 30).attr("fill", t.ink);
svg.selectAll("rect").data(data).join("rect")
  .attr("x", (d) => x(String(d.label))).attr("y", (d) => y(d.value))
  .attr("width", x.bandwidth()).attr("height", (d) => y(0) - y(d.value))
  .attr("fill", t.palette[0])
  .on("mouseover", (event, d) => tip.text(String(d.label) + ": " + d.value));
`,
  echarts: `const t = window.ANYPLOT_TOKENS;
const data = window.ANYPLOT_DATA;
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  tooltip: { trigger: "axis" },
  xAxis: { type: "category", data: data.map((row) => String(row.label)) },
  yAxis: { type: "value" },
  series: [{ type: "bar", data: data.map((row) => row.value), itemStyle: { color: t.palette[0] } }],
});
`,
  highcharts: `const t = window.ANYPLOT_TOKENS;
const data = window.ANYPLOT_DATA;
Highcharts.chart("container", {
  chart: { type: "column", animation: false, backgroundColor: t.pageBg },
  title: { text: "" },
  credits: { enabled: false },
  xAxis: { categories: data.map((row) => String(row.label)) },
  plotOptions: { series: { animation: false } },
  series: [{ name: "value", data: data.map((row) => row.value), color: t.palette[0] }],
});
`,
};

function fail(message) {
  console.error(`page_probe: ${message}`);
  process.exit(2);
}

async function playwright() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const modules = process.env.ANYPLOT_NODE_MODULES || path.resolve(here, "..", "..", "node_modules");
  return import(pathToFileURL(path.join(modules, "playwright", "index.mjs")).href);
}

// Runs in the frame: how much of the plot is there.
function drawn() {
  const container = document.getElementById("container");
  if (!container) return { painted: 0, shapes: 0 };
  let painted = 0;
  for (const canvas of container.querySelectorAll("canvas")) {
    const context = canvas.width && canvas.height ? canvas.getContext("2d") : null;
    if (!context) continue;
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    for (let i = 3; i < pixels.length; i += 4) if (pixels[i] !== 0) painted += 1;
  }
  const shapes = container.querySelectorAll("svg rect, svg path, svg circle, svg line, svg text").length;
  return { painted, shapes };
}

// Runs in the frame: a fingerprint of what the frame shows, its DOM and its canvases.
function fingerprint() {
  let text = document.body.innerHTML;
  for (const canvas of document.querySelectorAll("canvas")) text += canvas.toDataURL();
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) hash = Math.imul(hash ^ text.charCodeAt(i), 16777619) >>> 0;
  return `${text.length}:${hash}`;
}

async function check(file, { hover, attempts }) {
  const requests = [];
  const server = http.createServer((request, response) => {
    requests.push(request.url);
    response.end("reached");
  });
  await new Promise((resolve) => server.listen(PORT, "127.0.0.1", resolve));
  const { chromium } = await playwright();
  const browser = await chromium.launch({ args: ["--no-sandbox", "--force-color-profile=srgb"] });
  const report = { file: path.basename(file), checks: {}, failures: [] };
  const expect = (name, ok, value) => {
    report.checks[name] = value;
    if (!ok) report.failures.push(name);
  };
  try {
    const context = await browser.newContext({ acceptDownloads: true, viewport: VIEWPORT });
    const page = await context.newPage();
    const events = { popups: 0, downloads: 0, dialogs: 0 };
    page.on("popup", () => (events.popups += 1));
    page.on("download", () => (events.downloads += 1));
    page.on("dialog", (dialog) => {
      events.dialogs += 1;
      dialog.dismiss().catch(() => {});
    });
    const url = pathToFileURL(path.resolve(file)).href;
    await page.goto(url, { waitUntil: "load", timeout: TIMEOUT_MS });
    const children = page.frames().filter((frame) => frame !== page.mainFrame());
    expect("one_srcdoc_frame", children.length === 1 && children[0].url() === "about:srcdoc", children.map((f) => f.url()));
    const frame = children[0];
    if (!frame) throw new Error("no frame");
    await frame.waitForFunction(() => window.__anyplotError !== undefined, null, { timeout: TIMEOUT_MS });
    await page.waitForTimeout(SETTLE_MS);
    expect("no_page_error", (await frame.evaluate(() => window.__anyplotError)) === null, await frame.evaluate(() => window.__anyplotError));
    const plot = await frame.evaluate(drawn);
    expect("drew", plot.painted >= MIN_PAINTED || plot.shapes >= MIN_SHAPES, plot);
    const origin = await frame.evaluate(() => self.origin);
    expect("opaque_origin", origin === "null", origin);

    if (hover) {
      // The mouse moves in the window's own coordinates over the plot as the wrapper shows it (scaled):
      // Playwright's `hover({position})` maps a point into the frame without the frame's transform
      // (measured: its events missed the scaled frame), while a real pointer's reach the plot.
      const before = await frame.evaluate(fingerprint);
      const box = await frame.locator("#container canvas, #container svg").first().boundingBox();
      if (!box) throw new Error("the plot has no box");
      let changedAt = null;
      for (const share of [0.2, 0.35, 0.5, 0.65, 0.8]) {
        await page.mouse.move(box.x + box.width * share, box.y + box.height * 0.8);
        await page.waitForTimeout(100);
        // A tooltip shows while the pointer is over a mark and may go between marks, so each position counts.
        if ((await frame.evaluate(fingerprint)) !== before) {
          changedAt = share;
          break;
        }
      }
      expect("hover_changes_the_frame", changedAt !== null, { box, changed_at: changedAt });
    }

    if (attempts) {
      const recorded = await frame.evaluate(() => window.__anyplotProbe || null);
      expect("attempts_ran", recorded !== null && "fetch" in recorded, recorded);
      const refused = (name) => typeof recorded?.[name] === "string" && recorded[name].startsWith("refused");
      expect("top_location_refused", refused("top_location"), recorded?.top_location);
      expect("window_open_null", recorded?.window_open === "null", recorded?.window_open);
      expect("fetch_refused", refused("fetch"), recorded?.fetch);
      expect("storage_refused", refused("storage"), recorded?.storage);
      expect("cookie_refused", refused("cookie"), recorded?.cookie);
      expect("snippet_origin_null", recorded?.origin === "null", recorded?.origin);
      await frame.evaluate(() => window.__anyplotProbeNavigate && window.__anyplotProbeNavigate()).catch(() => {});
      await page.waitForTimeout(SETTLE_MS);
      const after = page.frames().filter((item) => item !== page.mainFrame()).map((item) => item.url());
      // A refused navigation leaves the frame on Chromium's error page, `chrome-error://chromewebdata/`: that is
      // what blocked looks like (the listener's empty log below says no request left). An http(s) URL here would
      // mean the frame loaded the target.
      expect("self_navigation_blocked", after.length === 1 && !/^https?:/.test(after[0]), after);
    }

    expect("main_frame_unchanged", page.url() === url, page.url());
    expect("no_popup_download_or_dialog", !events.popups && !events.downloads && !events.dialogs, events);
    expect("listener_saw_no_request", requests.length === 0, requests);
  } catch (err) {
    report.failures.push(`error: ${String(err && err.message ? err.message : err).slice(0, 300)}`);
  } finally {
    await browser.close();
    server.close();
  }
  console.log(JSON.stringify(report, null, 1));
  process.exit(report.failures.length ? 1 : 0);
}

const [mode, target, ...flags] = process.argv.slice(2);
if (mode === "snippet") {
  const snippet = SNIPPETS[target];
  if (!snippet) fail(`no snippet for ${target}; one of ${Object.keys(SNIPPETS).join(", ")}`);
  process.stdout.write(snippet + ATTEMPTS);
} else if (mode === "check" && target) {
  await check(target, { hover: flags.includes("--hover"), attempts: flags.includes("--attempts") });
} else {
  fail("usage: node page_probe.mjs snippet <chartjs|d3|echarts|highcharts> | check <plot.html> [--hover] [--attempts]");
}
