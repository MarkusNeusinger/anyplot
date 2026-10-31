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
// The relay mode (JS-4b-2, the chat's interactive preview) serves the API's
// relay page (api/preview_relay.py) with its real headers on its own origin and
// checks what the chat does with it: a parent page at an allowed origin
// (http://localhost:<port>) frames the relay, scaled as the chat scales it, and
// runs the chat's side of the handshake (InteractivePreview.tsx): the wrapper
// goes out only on the relay's ready signal from the relay frame's own window.
// Before that, a sibling frame at the same origin and one at another origin
// post a page of their own, which the relay must ignore. Then the plot draws in
// a frame of origin "null" and answers a hover, a second page from the parent
// is ignored, the snippet's attempts fail as above, its attempts to navigate
// the wrapper or the relay, to post a page into the relay and to send the ready
// signal to the top fail or are ignored, the relay keeps its URL, and the ready
// signal is all the relay ever sent. A parent at another origin
// (http://127.0.0.1:<port>) cannot frame the relay (`frame-ancestors`), and with
// that check lifted for the test (`/relay-open`), the relay still ignores a page
// that origin posts. A stand-in at the relay's URL (`/relay-missing`, a 404 page
// that listens, as an error page of the edge could) gets nothing from the chat,
// while a post on its load, the chat before the handshake, would have handed it
// the page (the control).
//
// Usage:
//   node page_probe.mjs snippet <chartjs|d3|echarts|highcharts>    print the probe's plot code
//   node page_probe.mjs check <plot.html> [--hover] [--attempts]
//   node page_probe.mjs relay <relay.json> <plot.html> [--hover]
//
// relay.json is `python3 api/preview_relay.py` (the relay's page, headers and
// ready signal).
// The snippets read window.ANYPLOT_DATA as {label, value} rows; the checker
// prints one JSON report and exits 1 when a check failed. Playwright comes from
// ANYPLOT_NODE_MODULES (the image's /opt/anyplot/node_modules) or the checkout's
// node_modules; the browser from PLAYWRIGHT_BROWSERS_PATH. The listener binds
// the loopback, which a container without network still has. It runs in the
// renderer image's CI step (ci-image.yml) and in
// tests/unit/agents/code/test_profile_javascript_page_image.py.
// =============================================================================

import { readFileSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PORT = 18731;
const LISTENER = `http://127.0.0.1:${PORT}`;
const RELAY_PORT = 18732; // the relay's own origin, http://127.0.0.1:18732 (api.anyplot.ai's part)
const PARENT_PORT = 18733; // the chat's part: http://localhost:18733 is allowed, http://127.0.0.1:18733 is not
const RELAY_SCALE = 0.75; // the chat scales the relay's frame to its card
const WRAPPER_SIZE = { width: 1632, height: 932 }; // a landscape wrapper at scale 1: the canvas and 16 px around it
const SETTLE_MS = 1500;
const TIMEOUT_MS = 20000;
const VIEWPORT = { width: 1440, height: 790 }; // a laptop's window: the wrapper scales the frame to 0.8
const MIN_PAINTED = 1000;
const MIN_SHAPES = 3;
const MARKER_PAGE = '<p id="anyplot-marker">a page the relay must not show</p>';
const RELAY_READY = "anyplot-relay-ready"; // the relay's only message (READY_MESSAGE in api/preview_relay.py)

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
  record("parent_location", function () { parent.location = "${LISTENER}/parent"; });
  record("grandparent_location", function () { parent.parent.location = "${LISTENER}/grandparent"; });
  record("post_to_relay", function () { parent.parent.postMessage(${JSON.stringify(MARKER_PAGE)}, "*"); });
  record("ready_to_top", function () { top.postMessage(${JSON.stringify(RELAY_READY)}, "*"); });
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
      // mean the frame loaded the target, and `about:srcdoc` that the attempt never ran.
      expect(
        "self_navigation_blocked",
        after.length === 1 && after[0] !== "about:srcdoc" && !/^https?:/.test(after[0]),
        after
      );
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

// The chat's side of the handshake (app/src/sections/agent-chat/InteractivePreview.tsx), in the parent page: the
// page goes into the relay frame only on the ready signal from that frame's own window, once. `anyplotShow` hands
// it the page; `__anyplotChat` records what came in for the checks (every message from the relay frame, the ready
// signals from it and from anywhere, the posts).
const CHAT_SCRIPT = `
(function () {
  var READY = ${JSON.stringify(RELAY_READY)};
  var relay = document.getElementById("relay");
  var chat = (window.__anyplotChat = { fromRelay: [], ready: 0, readyAnywhere: 0, posts: 0 });
  var page = null;
  function send() {
    if (page === null || chat.ready === 0 || chat.posts > 0) return;
    chat.posts += 1;
    relay.contentWindow.postMessage(page, "*");
  }
  window.addEventListener("message", function (event) {
    if (event.data === READY) chat.readyAnywhere += 1;
    if (event.source !== relay.contentWindow) return;
    chat.fromRelay.push(typeof event.data === "string" ? event.data.slice(0, 64) : typeof event.data);
    if (event.data !== READY) return;
    chat.ready += 1;
    send();
  });
  window.anyplotShow = function (html) {
    page = html;
    send();
  };
})();
`;

// The relay mode's parent page: the relay frame scaled as the chat scales it with the chat's handshake, and, with
// `siblings`, two frames that post a page of their own into the relay before the probe hands over the real one (one
// at this origin, one at another).
function parentPage(relayPath, siblings) {
  const { width, height } = WRAPPER_SIZE;
  const others = siblings
    ? `<iframe src="http://localhost:${PARENT_PORT}/sender" hidden></iframe>` +
      `<iframe src="http://127.0.0.1:${PARENT_PORT}/sender" hidden></iframe>`
    : "";
  return `<!doctype html><html><head><meta charset="utf-8"><style>
body { margin: 0; }
#relay { display: block; border: 0; width: ${width}px; height: ${height}px; transform: scale(${RELAY_SCALE}); transform-origin: 0 0; }
</style></head><body>
<iframe id="relay" sandbox="allow-scripts" src="http://127.0.0.1:${RELAY_PORT}${relayPath}"></iframe>${others}
<script>${CHAT_SCRIPT}</script>
</body></html>`;
}

// A sibling's page: it posts the marker page into the relay, its parent's first frame.
const SENDER_PAGE = `<!doctype html><script>parent.frames[0].postMessage(${JSON.stringify(MARKER_PAGE)}, "*");</script>`;

// What may answer at the relay's URL instead of the relay (an error or challenge page of the edge, a route that
// shadows the path): a 404 page with a listener of its own, which records the length of every string it receives.
const STAND_IN_PAGE = `<!doctype html><title>404 Not Found</title><h1>Not Found</h1><script>
window.__received = [];
window.addEventListener("message", function (event) {
  window.__received.push(typeof event.data === "string" ? event.data.length : typeof event.data);
});
</script>`;

// Runs in a frame: whether it shows the marker page.
function hasMarker() {
  return document.getElementById("anyplot-marker") !== null;
}

async function relay(relayFile, pageFile, { hover }) {
  const spec = JSON.parse(readFileSync(relayFile, "utf-8"));
  const wrapper = readFileSync(pageFile, "utf-8");
  const escapes = [];
  const listener = http.createServer((request, response) => {
    escapes.push(`listener ${request.url}`);
    response.end("reached");
  });
  // The relay's origin: `/relay` with its real headers, `/relay-open` with `frame-ancestors` lifted for the
  // origin check alone, `/relay-missing` the stand-in's 404; any other request is an escape.
  const relayHeaders = { "Content-Type": "text/html; charset=utf-8", ...spec.headers };
  const openHeaders = {
    ...relayHeaders,
    "Content-Security-Policy": spec.headers["Content-Security-Policy"].replace(/frame-ancestors [^;]*/, "frame-ancestors *"),
  };
  const relayServer = http.createServer((request, response) => {
    if (request.url === "/relay-missing") {
      response.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
      response.end(STAND_IN_PAGE);
      return;
    }
    const headers = { "/relay": relayHeaders, "/relay-open": openHeaders }[request.url];
    if (!headers) escapes.push(`relay ${request.url}`);
    response.writeHead(headers ? 200 : 404, headers ?? {});
    response.end(headers ? spec.html : "");
  });
  // The relay paths a parent may frame, picked by the query and never copied from it into the page.
  const relayPathOf = (name) => {
    switch (name) {
      case "/relay-open":
        return "/relay-open";
      case "/relay-missing":
        return "/relay-missing";
      default:
        return "/relay";
    }
  };
  const parents = http.createServer((request, response) => {
    const url = new URL(request.url, "http://parent");
    const html =
      url.pathname === "/parent"
        ? parentPage(relayPathOf(url.searchParams.get("relay")), url.searchParams.has("siblings"))
        : url.pathname === "/sender"
          ? SENDER_PAGE
          : null;
    if (html === null) escapes.push(`parent ${request.url}`);
    response.writeHead(html === null ? 404 : 200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(html ?? "");
  });
  await new Promise((resolve) => listener.listen(PORT, "127.0.0.1", resolve));
  await new Promise((resolve) => relayServer.listen(RELAY_PORT, "127.0.0.1", resolve));
  await new Promise((resolve) => parents.listen(PARENT_PORT, resolve)); // localhost and 127.0.0.1 alike
  const { chromium } = await playwright();
  const browser = await chromium.launch({ args: ["--no-sandbox", "--force-color-profile=srgb"] });
  const report = { file: path.basename(pageFile), checks: {}, failures: [] };
  const expect = (name, ok, value) => {
    report.checks[name] = value;
    if (!ok) report.failures.push(name);
  };
  const relayUrl = `http://127.0.0.1:${RELAY_PORT}/relay`;
  const framesOf = (page) => page.frames().filter((frame) => frame !== page.mainFrame());
  // A post straight into the relay frame, without the handshake: what the chat did before it, on the frame's load.
  const post = (page, html = wrapper) =>
    page.evaluate((content) => document.getElementById("relay").contentWindow.postMessage(content, "*"), html);
  // The chat's way: the page waits for the relay's ready signal.
  const show = (page) => page.evaluate((html) => window.anyplotShow(html), wrapper);
  const chatState = (page) => page.evaluate(() => ({ ...window.__anyplotChat }));
  const plotFrame = async (page) => {
    for (const frame of framesOf(page)) {
      if (frame.url() === "about:srcdoc" && (await frame.evaluate(() => !!document.getElementById("container")).catch(() => false))) {
        return frame;
      }
    }
    return null;
  };
  const markerShown = async (page) => {
    for (const frame of framesOf(page)) if (await frame.evaluate(hasMarker).catch(() => false)) return true;
    return false;
  };
  try {
    const context = await browser.newContext({ acceptDownloads: true, viewport: VIEWPORT });
    const events = { popups: 0, downloads: 0, dialogs: 0 };
    context.on("page", () => (events.popups += 1));

    expect("ready_signal_is_the_chats", spec.ready === RELAY_READY, spec.ready);

    // 1. The chat's case: an allowed origin, the relay with its real headers, two siblings posting first.
    const page = await context.newPage();
    events.popups -= 1; // the page itself
    page.on("download", () => (events.downloads += 1));
    page.on("dialog", (dialog) => {
      events.dialogs += 1;
      dialog.dismiss().catch(() => {});
    });
    const parentUrl = `http://localhost:${PARENT_PORT}/parent?relay=/relay&siblings`;
    await page.goto(parentUrl, { waitUntil: "load", timeout: TIMEOUT_MS });
    await page.waitForTimeout(SETTLE_MS / 3);
    const relayFrame = framesOf(page).find((frame) => frame.url() === relayUrl);
    expect("relay_loaded", !!relayFrame, framesOf(page).map((frame) => frame.url()));
    if (!relayFrame) throw new Error("no relay frame");
    expect("relay_origin_null", (await relayFrame.evaluate(() => self.origin)) === "null", await relayFrame.evaluate(() => self.origin));
    const beforePost = await relayFrame.evaluate(() => document.querySelectorAll("iframe").length);
    expect("siblings_ignored", beforePost === 0 && !(await markerShown(page)), { relay_frames: beforePost });
    const signalled = await chatState(page);
    expect("relay_signalled_ready", signalled.ready === 1 && signalled.posts === 0, signalled);
    await show(page);
    let frame = null;
    for (let waited = 0; !frame && waited < TIMEOUT_MS; waited += 250) {
      await page.waitForTimeout(250);
      frame = await plotFrame(page);
    }
    expect("page_shown", !!frame, framesOf(page).map((item) => item.url()));
    if (!frame) throw new Error("the relay shows no page");
    await frame.waitForFunction(() => window.__anyplotProbe && "fetch" in window.__anyplotProbe, null, { timeout: TIMEOUT_MS });
    await page.waitForTimeout(SETTLE_MS);
    const pageError = await frame.evaluate(() => window.__anyplotError);
    expect("no_page_error", pageError === null, pageError);
    const plot = await frame.evaluate(drawn);
    expect("drew", plot.painted >= MIN_PAINTED || plot.shapes >= MIN_SHAPES, plot);
    expect("opaque_origin", (await frame.evaluate(() => self.origin)) === "null", await frame.evaluate(() => self.origin));
    // The relay's own frame for the page: sandboxed to scripts alone, whatever the parent's attribute adds or lacks.
    const relayChild = await relayFrame.evaluate(() => {
      const child = document.querySelector("iframe");
      return child ? { sandbox: child.getAttribute("sandbox"), src: child.getAttribute("src"), srcdoc: child.hasAttribute("srcdoc") } : null;
    });
    expect("relay_frame_sandboxed_to_scripts", relayChild?.sandbox === "allow-scripts" && relayChild.src === null, relayChild);
    const wrapperFrame = frame.parentFrame();
    const wrapperOrigin = wrapperFrame ? await wrapperFrame.evaluate(() => self.origin) : null;
    expect("wrapper_origin_null", wrapperOrigin === "null", wrapperOrigin);
    // The relay takes one page: a second one, even from the allowed parent itself, is ignored.
    await post(page, MARKER_PAGE);
    await page.waitForTimeout(SETTLE_MS / 3);
    const afterSecond = await relayFrame.evaluate(() => document.querySelectorAll("iframe").length);
    expect("second_page_ignored", afterSecond === 1 && !(await markerShown(page)), { relay_frames: afterSecond });

    if (hover) {
      // The relay frame is scaled in the parent; the wrapper inside lays the canvas out 16 px from its corner.
      const box = await page.evaluate(() => {
        const rect = document.getElementById("relay").getBoundingClientRect();
        return { x: rect.x, y: rect.y };
      });
      const before = await frame.evaluate(fingerprint);
      let changedAt = null;
      for (const share of [0.2, 0.35, 0.5, 0.65, 0.8]) {
        await page.mouse.move(box.x + (16 + 1600 * share) * RELAY_SCALE, box.y + (16 + 900 * 0.8) * RELAY_SCALE);
        await page.waitForTimeout(100);
        if ((await frame.evaluate(fingerprint)) !== before) {
          changedAt = share;
          break;
        }
      }
      expect("hover_changes_the_frame", changedAt !== null, { changed_at: changedAt });
    }

    const recorded = await frame.evaluate(() => window.__anyplotProbe || null);
    const refused = (name) => typeof recorded?.[name] === "string" && recorded[name].startsWith("refused");
    expect("top_location_refused", refused("top_location"), recorded?.top_location);
    expect("window_open_null", recorded?.window_open === "null", recorded?.window_open);
    expect("fetch_refused", refused("fetch"), recorded?.fetch);
    expect("storage_refused", refused("storage"), recorded?.storage);
    expect("cookie_refused", refused("cookie"), recorded?.cookie);
    expect("wrapper_navigation_refused", refused("parent_location"), recorded?.parent_location);
    expect("relay_navigation_refused", refused("grandparent_location"), recorded?.grandparent_location);
    await frame.evaluate(() => window.__anyplotProbeNavigate && window.__anyplotProbeNavigate()).catch(() => {});
    await page.waitForTimeout(SETTLE_MS);
    const relayFrames = await relayFrame.evaluate(() => document.querySelectorAll("iframe").length);
    expect("post_from_the_plot_ignored", relayFrames === 1 && !(await markerShown(page)), { relay_frames: relayFrames, posted: recorded?.post_to_relay });
    expect("relay_kept_its_url", relayFrame.url() === relayUrl, relayFrame.url());
    expect("parent_unchanged", page.url() === parentUrl, page.url());
    // A refused navigation of the plot's own frame ends on Chromium's error page (`chrome-error://chromewebdata/`):
    // the frame left `about:srcdoc` (the attempt ran) and reached no http(s) URL.
    const urls = framesOf(page).map((item) => item.url());
    expect(
      "self_navigation_blocked",
      frame.url() !== "about:srcdoc" && !/^https?:/.test(frame.url()) && !urls.some((url) => url.startsWith(LISTENER)),
      { plot_frame: frame.url(), frames: urls }
    );
    // The plot's ready signal reached the top (both signals counted there) but started no post: the chat answers
    // the relay frame's window alone, and the relay never said anything but its one signal.
    const chat = await chatState(page);
    expect(
      "ready_from_the_plot_ignored",
      recorded?.ready_to_top === "ok" && chat.readyAnywhere === 2 && chat.ready === 1 && chat.posts === 1,
      { ...chat, posted: recorded?.ready_to_top }
    );
    expect("relay_sent_only_the_signal", chat.fromRelay.length === 1 && chat.fromRelay[0] === RELAY_READY, chat.fromRelay);

    // 2. Another origin cannot frame the relay: `frame-ancestors` keeps its script from running there.
    const stranger = await context.newPage();
    events.popups -= 1;
    await stranger.goto(`http://127.0.0.1:${PARENT_PORT}/parent?relay=/relay`, { waitUntil: "load", timeout: TIMEOUT_MS });
    await post(stranger).catch(() => {});
    await stranger.waitForTimeout(SETTLE_MS);
    const strangerUrls = framesOf(stranger).map((item) => item.url());
    expect("frame_ancestors_refuses_another_origin", !strangerUrls.includes(relayUrl) && !(await plotFrame(stranger)), strangerUrls);

    // 3. With `frame-ancestors` lifted, the relay's own check still ignores a page from another origin.
    const lifted = await context.newPage();
    events.popups -= 1;
    await lifted.goto(`http://127.0.0.1:${PARENT_PORT}/parent?relay=/relay-open`, { waitUntil: "load", timeout: TIMEOUT_MS });
    const openFrame = framesOf(lifted).find((item) => item.url() === `http://127.0.0.1:${RELAY_PORT}/relay-open`);
    await post(lifted);
    await lifted.waitForTimeout(SETTLE_MS);
    const openFrames = openFrame ? await openFrame.evaluate(() => document.querySelectorAll("iframe").length) : null;
    expect("another_origins_page_ignored", openFrames === 0, { relay_loaded: !!openFrame, relay_frames: openFrames });
    // The control: the same lifted relay takes the page from an allowed origin, so its script ran in case 3.
    const control = await context.newPage();
    events.popups -= 1;
    await control.goto(`http://localhost:${PARENT_PORT}/parent?relay=/relay-open`, { waitUntil: "load", timeout: TIMEOUT_MS });
    await post(control);
    let controlFrame = null;
    for (let waited = 0; !controlFrame && waited < TIMEOUT_MS; waited += 250) {
      await control.waitForTimeout(250);
      controlFrame = await plotFrame(control);
    }
    expect("lifted_relay_takes_an_allowed_origins_page", !!controlFrame, framesOf(control).map((item) => item.url()));

    // 4. A stand-in at the relay's URL that listens: it sends no ready signal, so the chat posts it nothing.
    const standIn = await context.newPage();
    events.popups -= 1;
    await standIn.goto(`http://localhost:${PARENT_PORT}/parent?relay=/relay-missing`, { waitUntil: "load", timeout: TIMEOUT_MS });
    await show(standIn);
    await standIn.waitForTimeout(SETTLE_MS);
    const standInFrame = framesOf(standIn).find((item) => item.url() === `http://127.0.0.1:${RELAY_PORT}/relay-missing`);
    const received = standInFrame ? await standInFrame.evaluate(() => window.__received) : null;
    const standInChat = await chatState(standIn);
    expect("stand_in_receives_nothing", Array.isArray(received) && received.length === 0 && standInChat.posts === 0, {
      received,
      ...standInChat,
    });
    // The control: a post on the frame's load, the chat before the handshake, hands the stand-in the whole page.
    await post(standIn);
    await standIn.waitForTimeout(SETTLE_MS / 3);
    const leaked = standInFrame ? await standInFrame.evaluate(() => window.__received) : null;
    expect("stand_in_listens", Array.isArray(leaked) && leaked.length === 1 && leaked[0] === wrapper.length, leaked);

    expect("no_popup_download_or_dialog", !events.popups && !events.downloads && !events.dialogs, events);
    expect("no_request_escaped", escapes.length === 0, escapes);
  } catch (err) {
    report.failures.push(`error: ${String(err && err.message ? err.message : err).slice(0, 300)}`);
  } finally {
    await browser.close();
    for (const server of [listener, relayServer, parents]) server.close();
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
} else if (mode === "relay" && target && flags[0]) {
  await relay(target, flags[0], { hover: flags.includes("--hover") });
} else {
  fail(
    "usage: node page_probe.mjs snippet <chartjs|d3|echarts|highcharts> | check <plot.html> [--hover] [--attempts]" +
      " | relay <relay.json> <plot.html> [--hover]"
  );
}
