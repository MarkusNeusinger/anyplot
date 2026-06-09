#!/usr/bin/env node
// anyplot.ai — JavaScript browser render harness
// =============================================================================
//
// anyplot's R (`Rscript`) and Julia (`julia`) runtimes are CLI tools that write a
// PNG directly. JavaScript charting libraries render into a browser DOM — there
// is no headless CLI that produces a PNG. This harness is anyplot's first
// browser-rendered runtime: it wraps an idiomatic library snippet in an HTML
// page, loads the pinned library bundle, renders it under headless Chromium via
// Playwright, waits for a render-complete signal, and screenshots the mount node
// at an exact pixel size.
//
// The model mirrors the rest of the catalog: the *snippet* is the authored
// artifact (it just calls `new Chart(...)`, `d3.select(...)`, `echarts.init(...)`
// against a known mount node `#container`); the PNG is *derived* — exactly like
// matplotlib's snippet calls `plt.savefig` and CairoMakie's calls `save`. The
// self-contained HTML page is written alongside the PNG for the interactive
// detail view (the JS libraries are in INTERACTIVE_LIBRARIES).
//
// Usage:
//   ANYPLOT_THEME=light node automation/js-render/render.mjs <impl.js> [--library=<id>] [--square]
//   ANYPLOT_THEME=dark  node automation/js-render/render.mjs <impl.js>
//
// Outputs (written next to the cwd, matching the Python/R/Julia convention):
//   plot-<theme>.png   — Playwright screenshot of #container at the canonical size
//   plot-<theme>.html  — self-contained interactive page (bundle + snippet inlined)
//
// Canvas — HARD RULE (the impl-review.yml gate rejects > 16 px drift):
//   landscape  3200 × 1800  (1600 × 900 CSS × deviceScaleFactor 2)   — default
//   square     2400 × 2400  (1200 × 1200 CSS × deviceScaleFactor 2)
// Orientation is picked per snippet via a top-of-file directive
//   //# anyplot-orientation: square
// or the `--square` flag. Exact pixels come from Playwright `deviceScaleFactor`
// + a fixed-size mount node, not from anything the snippet does.
// =============================================================================

import { readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { build as esbuild } from "esbuild";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// automation/js-render/render.mjs → repo root is two levels up. node_modules is
// resolved relative to the harness so it works regardless of the snippet's cwd
// (Claude runs the render from plots/{spec}/implementations/javascript).
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const NODE_MODULES = path.join(REPO_ROOT, "node_modules");

// -----------------------------------------------------------------------------
// Canvas sizes — the two canonical pairs, no third aspect ratio.
// -----------------------------------------------------------------------------
const DEVICE_SCALE_FACTOR = 2;
const ORIENTATIONS = {
  landscape: { cssWidth: 1600, cssHeight: 900 }, // → 3200 × 1800
  square: { cssWidth: 1200, cssHeight: 1200 }, // → 2400 × 2400
};

// -----------------------------------------------------------------------------
// Theme tokens — mirror prompts/default-style-guide.md + the ggplot2/Makie
// ANYPLOT_THEME switch. Data colours are identical between themes; only chrome
// flips. Exposed to the snippet as globalThis.ANYPLOT_TOKENS.
// -----------------------------------------------------------------------------
const IMPRINT_PALETTE = [
  "#009E73", // 1 — first categorical series (anyplot brand green)
  "#C475FD", // 2 — lavender
  "#4467A3", // 3 — blue
  "#BD8233", // 4 — ochre
  "#AE3030", // 5 — matte red (semantic anchor for bad / loss / error)
  "#2ABCCD", // 6 — cyan
  "#954477", // 7 — rose
  "#99B314", // 8 — lime
];

function themeTokens(theme) {
  const light = theme !== "dark";
  const ink = light ? "#1A1A17" : "#F0EFE8";
  const pageBg = light ? "#FAF8F1" : "#1A1A17";
  return {
    theme: light ? "light" : "dark",
    pageBg,
    elevatedBg: light ? "#FFFDF6" : "#242420",
    ink,
    inkSoft: light ? "#4A4A44" : "#B8B7B0",
    // 15 %-alpha ink for gridlines, matching the Makie mapping.
    grid: light ? "rgba(26,26,23,0.15)" : "rgba(240,239,232,0.15)",
    palette: IMPRINT_PALETTE,
    amber: "#DDCC77", // warning / caution (outside the categorical pool)
    seq: ["#009E73", "#4467A3"], // single-polarity continuous
    div: ["#AE3030", pageBg, "#4467A3"], // diverging (theme-adaptive midpoint)
  };
}

// -----------------------------------------------------------------------------
// Library → bundle.
//
// framework=none libs (Chart.js, D3, ECharts, Highcharts) expose a single UMD
// global loaded from a prebuilt `dist`. Only the snippet's own library is
// inlined, so the standalone HTML stays small and the page can't accidentally
// lean on a sibling library.
//
// framework=react libs (MUI X Charts) have no UMD global — the snippet is a
// `.tsx` module that default-exports a React component. They are bundled on the
// fly with esbuild (snippet + react + react-dom + @mui/*), wrapped in a MUI
// ThemeProvider, and mounted via createRoot. `framework: "react"` selects that
// path; `dist`/`global` are unused for it.
// -----------------------------------------------------------------------------
const BUNDLES = {
  chartjs: { global: "Chart", dist: "chart.js/dist/chart.umd.js" },
  d3: { global: "d3", dist: "d3/dist/d3.min.js" },
  echarts: { global: "echarts", dist: "echarts/dist/echarts.min.js" },
  // Highcharts ships its UMD bundle at the package root (highcharts.js); loaded
  // as a <script> it defines the `Highcharts` global. Commercial license, free
  // for non-commercial use — only the core bundle is vendored (no highcharts-more
  // / modules), matching the framework=none single-global model of the Phase-1 libs.
  highcharts: { global: "Highcharts", dist: "highcharts/highcharts.js" },
  // MUI X Charts — community @mui/x-charts (MIT), React framework. Authored as
  // `.tsx`, bundled via esbuild (see bundleReactSnippet). Only the MIT community
  // surface is vendored; @mui/x-charts-pro / Premium are NOT installed.
  muix: { framework: "react" },
};

// -----------------------------------------------------------------------------
// React (framework=react) bundling — the MUI X path.
//
// The framework-agnostic libs load a prebuilt UMD bundle and the snippet draws
// into `#container` imperatively. React libs are different: the snippet is a
// `.tsx` module that *default-exports a component*, so there is nothing to draw
// until we (a) wrap it in a MUI ThemeProvider whose palette follows ANYPLOT_THEME
// and (b) mount it into `#container` with createRoot. We synthesize that mount
// entry, then esbuild-bundle entry + snippet + react/react-dom/@mui into one IIFE
// that we inline exactly like a UMD bundle. esbuild compiles the JSX/TSX (getBBox
// text layout still happens in the real browser, which is why the harness, not
// jsdom SSR, renders it). Returns the bundled JS as a string.
// -----------------------------------------------------------------------------
async function bundleReactSnippet(snippetPath) {
  // The snippet default-exports a React component. We import it by absolute path
  // so esbuild resolves it regardless of cwd, wrap it in a theme provider mapped
  // onto ANYPLOT_TOKENS, and mount it. __anyplotReady is set only after fonts +
  // a few frames so MUI X's getBBox-based axis/legend layout (it measures real
  // SVG text, then re-renders) has settled before the screenshot.
  const entry = `
import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import AnyplotChart from ${JSON.stringify(snippetPath)};

const t = window.ANYPLOT_TOKENS;
const mode = window.ANYPLOT_THEME === "dark" ? "dark" : "light";
const theme = createTheme({
  palette: {
    mode,
    background: { default: t.pageBg, paper: t.elevatedBg },
    text: { primary: t.ink, secondary: t.inkSoft },
    divider: t.grid,
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
});

const root = createRoot(document.getElementById("container"));
root.render(
  React.createElement(ThemeProvider, { theme }, React.createElement(AnyplotChart))
);

(async () => {
  try { await (document.fonts ? document.fonts.ready : Promise.resolve()); } catch (e) {}
  requestAnimationFrame(() =>
    requestAnimationFrame(() =>
      requestAnimationFrame(() => { window.__anyplotReady = true; })
    )
  );
})();
`;
  const result = await esbuild({
    stdin: {
      contents: entry,
      resolveDir: REPO_ROOT,
      sourcefile: "anyplot-react-entry.tsx",
      loader: "tsx",
    },
    bundle: true,
    write: false,
    format: "iife",
    platform: "browser",
    target: "es2020",
    jsx: "automatic",
    minify: true,
    legalComments: "none",
    absWorkingDir: REPO_ROOT,
    nodePaths: [NODE_MODULES],
    // React / MUI gate huge dev-only branches on process.env.NODE_ENV; pin it to
    // production so esbuild dead-code-eliminates them (smaller bundle, no dev
    // warnings), and shim `process` for any stray references in the browser.
    define: { "process.env.NODE_ENV": '"production"' },
    banner: { js: "globalThis.process=globalThis.process||{env:{NODE_ENV:'production'}};" },
  });
  return result.outputFiles[0].text;
}

function parseArgs(argv) {
  const args = { square: false, library: null, file: null };
  for (const arg of argv) {
    if (arg === "--square") args.square = true;
    else if (arg === "--landscape") args.square = false;
    else if (arg.startsWith("--library=")) args.library = arg.slice("--library=".length);
    else if (arg.startsWith("--orientation=")) args.square = arg.slice("--orientation=".length) === "square";
    else if (!arg.startsWith("--")) args.file = arg;
  }
  return args;
}

// A snippet may self-declare its orientation with a top-of-file directive so the
// render command stays identical for every plot (the agent never has to remember
// a flag). The CLI flag still wins when present.
function orientationFromSource(source, cliSquare) {
  if (cliSquare) return "square";
  const m = source.match(/^\s*\/\/#?\s*anyplot-orientation:\s*(square|landscape)\b/im);
  if (m) return m[1].toLowerCase();
  return "landscape";
}

function buildHtml({ tokens, bundleSource, snippetSource, css }) {
  // The bundle + snippet are inlined so the written .html is fully self-contained
  // (no CDN, no network) — the same page is screenshotted and shipped as the
  // interactive deliverable. JSON.stringify keeps the token/theme injection
  // injection-safe.
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>anyplot</title>
<style>
  html, body { margin: 0; padding: 0; background: ${tokens.pageBg}; overflow: hidden; }
  *, *::before, *::after { box-sizing: border-box; }
  #container {
    width: ${css.cssWidth}px;
    height: ${css.cssHeight}px;
    background: ${tokens.pageBg};
    color: ${tokens.ink};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    position: relative;
  }
  #container canvas, #container svg { display: block; }
</style>
</head>
<body>
<div id="container"></div>
<script>
  // anyplot render context — the snippet reads these globals (the browser has no
  // process.env, so this is the JS analogue of ANYPLOT_THEME for Python/R/Julia).
  window.ANYPLOT_THEME = ${JSON.stringify(tokens.theme)};
  window.ANYPLOT_TOKENS = ${JSON.stringify(tokens)};
  // Exact-pixel mount size, in case a snippet wants to size a canvas explicitly.
  window.ANYPLOT_SIZE = { width: ${css.cssWidth}, height: ${css.cssHeight} };
  window.__anyplotError = null;
  window.addEventListener("error", (e) => { window.__anyplotError = String(e.error || e.message); });
  window.addEventListener("unhandledrejection", (e) => { window.__anyplotError = String(e.reason); });
</script>
<script>
${bundleSource.replace(/<\/script/gi, "<\\/script")}
</script>
<script>
try {
${snippetSource.replace(/<\/script/gi, "<\\/script")}
} catch (err) {
  window.__anyplotError = String(err && err.stack ? err.stack : err);
  throw err;
}
</script>
</body>
</html>`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.file) {
    console.error("usage: node automation/js-render/render.mjs <impl.js> [--library=<id>] [--square]");
    process.exit(2);
  }

  const theme = process.env.ANYPLOT_THEME === "dark" ? "dark" : "light";
  const tokens = themeTokens(theme);

  const filePath = path.resolve(process.cwd(), args.file);
  if (!existsSync(filePath)) {
    console.error(`render: implementation file not found: ${filePath}`);
    process.exit(2);
  }
  const snippetSource = await readFile(filePath, "utf-8");

  // Library id: explicit flag wins, else the file stem (chartjs.js → chartjs).
  const library = args.library || path.basename(filePath).replace(/\.(js|mjs|cjs|ts|tsx)$/i, "");
  const bundleInfo = BUNDLES[library];
  if (!bundleInfo) {
    console.error(`render: unknown library "${library}". Known: ${Object.keys(BUNDLES).join(", ")}`);
    console.error('Pass --library=<id> if the file is not named after its library (e.g. "<id>.js").');
    process.exit(2);
  }

  const orientation = orientationFromSource(snippetSource, args.square);
  const css = ORIENTATIONS[orientation];

  // framework=react libs (MUI X) are esbuild-bundled into a single IIFE that
  // both pulls in react/@mui *and* mounts the snippet's default-exported
  // component — there is no separate UMD bundle + imperative snippet. We inline
  // that IIFE as the page's only library script (snippetSource left empty), so
  // the rest of the pipeline — self-contained HTML, draw check, screenshot — is
  // identical to the framework=none path.
  let html;
  if (bundleInfo.framework === "react") {
    const bundleSource = await bundleReactSnippet(filePath);
    html = buildHtml({ tokens, bundleSource, snippetSource: "", css });
  } else {
    const bundlePath = path.join(NODE_MODULES, bundleInfo.dist);
    if (!existsSync(bundlePath)) {
      console.error(`render: bundle missing: ${bundlePath}\nRun \`npm ci\` at the repo root first.`);
      process.exit(2);
    }
    const bundleSource = await readFile(bundlePath, "utf-8");
    html = buildHtml({ tokens, bundleSource, snippetSource, css });
  }

  // Write the self-contained interactive page first — it is a deliverable in its
  // own right and useful for debugging even if the screenshot step later fails.
  const htmlOut = path.resolve(process.cwd(), `plot-${theme}.html`);
  await writeFile(htmlOut, html, "utf-8");

  const browser = await chromium.launch({ args: ["--no-sandbox", "--force-color-profile=srgb"] });
  try {
    const page = await browser.newPage({
      viewport: { width: css.cssWidth, height: css.cssHeight },
      deviceScaleFactor: DEVICE_SCALE_FACTOR,
    });

    // Static screenshot of an animated chart must catch the *final* frame, never
    // a mid-tween one. The library prompts already mandate disabling animation
    // (Chart.js/ECharts/Highcharts `animation:false`, MUI X `skipAnimation`), but
    // emulating `prefers-reduced-motion: reduce` is a belt-and-suspenders guard:
    // well-behaved libraries (MUI X among them) skip entrance animation under it,
    // so a forgotten flag can't leak a half-grown bar into the PNG. colorScheme
    // is pinned to the active theme for any lib that keys off prefers-color-scheme.
    await page.emulateMedia({ reducedMotion: "reduce", colorScheme: theme });

    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    let pageError = null;
    page.on("pageerror", (err) => {
      pageError = err;
    });

    await page.setContent(html, { waitUntil: "load" });

    // Wait for a render-complete signal. A snippet MAY set window.__anyplotReady
    // (e.g. ECharts `chart.on('finished', ...)`) for precise timing; otherwise we
    // fall back to fonts-ready + a double rAF, which is sufficient for the
    // animation:false static renders the library prompts mandate. This is the
    // page.waitForFunction(...) signal the design calls for — never a time.sleep.
    try {
      await page.waitForFunction(() => window.__anyplotReady === true, { timeout: 2500 });
    } catch {
      // No explicit signal — settle deterministically instead.
      await page.evaluate(async () => {
        await (document.fonts ? document.fonts.ready : Promise.resolve());
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      });
    }

    // Surface snippet failures loudly — a blank/half-drawn PNG must fail the
    // render so the pipeline retries, never ship silently. Throw (don't
    // process.exit) so the `finally` below still closes the browser; the outer
    // main().catch turns the throw into a non-zero exit.
    const inPageError = await page.evaluate(() => window.__anyplotError);
    if (pageError || inPageError) {
      throw new Error(`render: the snippet threw while drawing:\n${String(pageError?.stack || pageError || inPageError)}`);
    }

    // The HTML scaffold always provides `#container`, so its mere existence
    // proves nothing — assert the snippet actually drew something into it. All
    // three Phase-1 libraries mount a <canvas> (Chart.js, ECharts) or <svg>
    // (D3); an empty mount means the snippet rendered nothing and we must fail
    // rather than ship a blank PNG.
    const container = page.locator("#container");
    const drewSomething = await page.evaluate(() => {
      const el = document.getElementById("container");
      return !!el && el.querySelector("canvas, svg, img") !== null;
    });
    if (!drewSomething) {
      throw new Error("render: snippet did not draw into #container (no <canvas>/<svg> mounted).");
    }

    const pngOut = path.resolve(process.cwd(), `plot-${theme}.png`);
    await container.screenshot({ path: pngOut });

    if (consoleErrors.length) {
      console.warn(`render: ${consoleErrors.length} console error(s) during render:`);
      for (const e of consoleErrors.slice(0, 5)) console.warn(`  ${e}`);
    }

    const expected = `${css.cssWidth * DEVICE_SCALE_FACTOR}×${css.cssHeight * DEVICE_SCALE_FACTOR}`;
    console.log(`render: ${library} ${theme} ${orientation} → ${pngOut} (target ${expected})`);
    console.log(`render: wrote ${htmlOut}`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
