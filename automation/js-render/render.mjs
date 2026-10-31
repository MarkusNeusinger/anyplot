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
// Orientation is picked per snippet via a directive line, read anywhere in the
// file (by convention directly below the `// anyplot.ai` header)
//   //# anyplot-orientation: square
// or the `--square` flag. Exact pixels come from Playwright `deviceScaleFactor`
// + a fixed-size mount node, not from anything the snippet does.
//
// Sandbox mode — the agents' renderer (agents/renderer/commands.py, the
// JavaScript row) runs this harness on model-written code. Environment
// variables switch its additions on; with none of them set, the harness behaves
// exactly as the catalogue pipeline has always run it (same page, same output):
//   ANYPLOT_SANDBOX=1          page rules: every request aborted, every WebSocket
//                              closed, no popup (--block-new-web-contents), a
//                              content security policy, the zone UTC, a V8 heap
//                              cap; MUI X imports closed to the image's allowlist;
//                              a bounded console; one final error line (below)
//   ANYPLOT_NO_HTML=1          no plot-<theme>.html
//   ANYPLOT_DATA_JSON=<path>   the table as typed JSON (agents/anyplot/data/
//                              typed_json.py), injected as window.ANYPLOT_DATA
//   ANYPLOT_IMPORT_ALLOWLIST   the allowlist file (default: import-allowlist.json
//                              next to this harness, where the image puts it)
//   ANYPLOT_PAGE_ONLY=1        with ANYPLOT_SANDBOX=1 only: build the page as a
//                              render would (the policy, the data, MUI X through
//                              the closed import plugin), write plot-<theme>.html
//                              whatever ANYPLOT_NO_HTML says, and exit without
//                              starting Chromium: the agents' downloadable
//                              plot.html (JS-4b)
//
// The final error line (sandbox mode): on any failure the LAST line on stderr is
//   render: error: <kind> <Class> <file>:<line>: <message>
// or, without a line in the snippet, `-` in place of `<file>:<line>`. <kind> is
// page (an uncaught error in the page), import (an import refused or not found),
// build (esbuild could not compile the snippet), draw (nothing drawn), crash (the
// page died, out of memory most likely), data (the data file), timeout (the page
// never finished loading or never settled) or harness (anything else); <Class> an identifier
// (TypeError, ImportRefused, ...); <file> the code file's own name (plot.js,
// plot.tsx), <line> its line; <message> at most 200 characters on one line.
// Only the bounded console summary comes before it, so the renderer's
// 2,000-character stderr tail always keeps it (step 3d of
// agentic/specs/261024-agent-all-libraries.md).
// =============================================================================

import { open, readFile, writeFile } from "node:fs/promises";
import { constants, existsSync, realpathSync } from "node:fs";
import { randomBytes } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { build as esbuild } from "esbuild";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// automation/js-render/render.mjs → repo root is two levels up. node_modules is
// resolved relative to the harness so it works regardless of the snippet's cwd
// (Claude runs the render from plots/{spec}/implementations/javascript).
// ANYPLOT_NODE_MODULES names it where the harness does not sit in a checkout: the
// agents' renderer image keeps the harness at /opt/anyplot/js-render/ and the
// packages at /opt/anyplot/node_modules (agents/renderer/toolchain.Dockerfile).
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const NODE_MODULES = process.env.ANYPLOT_NODE_MODULES || path.join(REPO_ROOT, "node_modules");
// esbuild's working directory: the repository root in a checkout, the packages'
// parent where ANYPLOT_NODE_MODULES names them (/opt/anyplot in the image, where
// two levels above the harness is /opt).
const BUILD_ROOT = process.env.ANYPLOT_NODE_MODULES ? path.dirname(path.resolve(NODE_MODULES)) : REPO_ROOT;

// -----------------------------------------------------------------------------
// Sandbox mode (see the header). Each switch is off unless its variable is set.
// -----------------------------------------------------------------------------
const SANDBOX = process.env.ANYPLOT_SANDBOX === "1";
const NO_HTML = process.env.ANYPLOT_NO_HTML === "1";
const PAGE_ONLY = process.env.ANYPLOT_PAGE_ONLY === "1";
const DATA_JSON = process.env.ANYPLOT_DATA_JSON || null;
const IMPORT_ALLOWLIST = process.env.ANYPLOT_IMPORT_ALLOWLIST || path.join(__dirname, "import-allowlist.json");
// Nothing but the inlined page: no request, no socket, no frame, no worker from a
// URL, no eval, no form submission, no <base>. Images and fonts only from data:
// and blob: URLs. form-action and base-uri do not fall back to default-src, so
// they are named. Every catalogue file renders under it (the JS-2 sweep).
const CONTENT_SECURITY_POLICY =
  "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; " +
  "form-action 'none'; base-uri 'none'";
// The page's V8 heap: a runaway of JavaScript objects (arrays, strings) ends the
// page at this size, as a crash the final error line names. It does not bound
// memory outside the heap (3 GiB of ArrayBuffers were allocated under it,
// measured by the security review of JS-2): the renderer's MemAvailable watchdog
// (512 MiB left of 4 GiB) bounds the run's memory. The catalogue's heaviest render
// peaked at 1,178 MiB for the whole container (JS-1).
const PAGE_HEAP_MB = 1024;
// Sandbox mode: how long the page may take to settle after it loaded, and to
// answer the harness's questions after that. A snippet that replaces
// requestAnimationFrame or document.fonts would otherwise hold the render to the
// job's timeout. The catalogue's slowest render took 6.1 s in all.
const SETTLE_TIMEOUT_MS = 15000;
const PAGE_ERROR_CHARS = 10000; // the page's own error record, cut in the page; the first uncaught error's message and frames, cut in Node
// A proxy nothing listens on (the discard port): Chromium's WebRTC may connect
// only through a proxy in sandbox mode, so it connects nowhere.
const DEAD_PROXY = "http://127.0.0.1:9";
const CONSOLE_KEEP = 5; // console errors kept (the first ones); the rest are counted
const CONSOLE_MESSAGE_CHARS = 300; // per kept message
const ERROR_MESSAGE_CHARS = 200; // the final error line's message
// The snippet's <script> starts with a line break and `try {`, so its line N is
// line N + SNIPPET_LINE_OFFSET of the script (measured: a throw on line 4 is
// reported at line 6).
const SNIPPET_HEAD = "\ntry {\n";
const SNIPPET_LINE_OFFSET = SNIPPET_HEAD.split("\n").length - 1;
// The bundle's <script> starts with a line break too: its line N is line N + 1.
const BUNDLE_LINE_OFFSET = 1;
// The React entry's name for esbuild (bundleReactSnippet).
const ENTRY_FILE = "anyplot-react-entry.tsx";
// Failure details for the final error line, kept off the Error objects so the
// pipeline's `console.error(err)` prints them exactly as before.
const FAILURES = new WeakMap();

function failure(message, kind, cls, location = null) {
  const err = new Error(message);
  // The stack starts at the caller, as the pipeline's `new Error(...)` there did.
  Error.captureStackTrace(err, failure);
  FAILURES.set(err, { kind, cls, location });
  return err;
}

// Runs in the page, in sandbox mode, in the main frame (the context script) and
// in every child frame (an init script): the console keeps only console.error,
// whose first `keep` calls of the whole page (one counter on the top window)
// leave the page, each argument cut to `chars`. Playwright keeps the page's
// recent console messages in Node whether or not a listener reads them: 400,000
// one-line errors held 1.3 GB in Node and took 18 s, 100 errors of 10 MB each
// ended Node with "Invalid string length"; with the guard both take 1.4 s and
// 150 MiB (measured in JS-2). Messages the browser writes itself (a refused
// request) do not pass through it.
function consoleGuard(keep, chars) {
  var slot = null;
  try {
    slot = window.top.__anyplotConsoleSlot || null;
  } catch (e) {}
  if (typeof slot !== "function") {
    var seen = 0;
    slot = function () {
      seen += 1;
      return seen <= keep;
    };
    Object.defineProperty(window, "__anyplotConsoleSlot", { value: slot });
    Object.defineProperty(window, "__anyplotConsoleSeen", { value: function () { return seen; } });
  }
  var error = console.error.bind(console);
  var quiet = function () {};
  ["log", "info", "debug", "warn", "trace", "dir", "dirxml", "table", "group", "groupCollapsed", "groupEnd", "count",
    "countReset", "time", "timeEnd", "timeLog", "timeStamp", "assert", "profile", "profileEnd", "clear"].forEach(
    function (name) {
      console[name] = quiet;
    },
  );
  // Chromium's console.context() returns a fresh console whose error() passes by
  // the guard (measured: 20 of 20 messages reached Node); it returns this one.
  // The console's prototype is empty, so a deleted method leaves nothing to call.
  console.context = function () {
    return console;
  };
  console.error = function () {
    if (!slot()) return;
    error(
      Array.prototype.map
        .call(arguments, function (value) {
          try {
            return String(value).slice(0, chars);
          } catch (e) {
            return "[unprintable]";
          }
        })
        .join(" "),
    );
  };
}
const CONSOLE_GUARD = `(${consoleGuard.toString()})(${CONSOLE_KEEP}, ${CONSOLE_MESSAGE_CHARS});`;

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
// Figure libraries (figure mode, sandbox only; see renderFigure): the Python
// plot writes its figure as JSON and the page draws it with the Python
// package's own bundled JavaScript, read from the package's directory
// (ANYPLOT_FIGURE_PACKAGE), so the two versions are one; `files` are relative
// to it. bokeh's WebGL, widget and table models live in bundles of their own;
// its MathJax bundle is left out (MathJax off). No snippet runs for these.
// -----------------------------------------------------------------------------
const FIGURES = {
  plotly: { files: ["package_data/plotly.min.js"] },
  bokeh: {
    files: [
      "server/static/js/bokeh.min.js",
      "server/static/js/bokeh-gl.min.js",
      "server/static/js/bokeh-widgets.min.js",
      "server/static/js/bokeh-tables.min.js",
    ],
  },
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
  const options = {
    stdin: {
      contents: entry,
      resolveDir: BUILD_ROOT,
      sourcefile: ENTRY_FILE,
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
    absWorkingDir: BUILD_ROOT,
    nodePaths: [NODE_MODULES],
    // React / MUI gate huge dev-only branches on process.env.NODE_ENV; pin it to
    // production so esbuild dead-code-eliminates them (smaller bundle, no dev
    // warnings), and shim `process` for any stray references in the browser.
    define: { "process.env.NODE_ENV": '"production"' },
    banner: { js: "globalThis.process=globalThis.process||{env:{NODE_ENV:'production'}};" },
  };
  if (!SANDBOX) {
    const result = await esbuild(options);
    return { code: result.outputFiles[0].text, map: null };
  }
  // Sandbox mode: the imports are closed (sandboxImports), the logs stay silent
  // (the final error line reports the first error), and an external source map
  // (no comment in the bundle) lets an error in the minified bundle name its line
  // in the snippet (snippetLine).
  let result;
  try {
    result = await esbuild({
      ...options,
      outfile: path.join(BUILD_ROOT, "anyplot-bundle.js"),
      sourcemap: "external",
      metafile: true,
      logLevel: "silent",
      plugins: [sandboxImports(snippetPath, await readAllowlist())],
    });
  } catch (err) {
    throw buildFailure(err, snippetPath);
  }
  checkInputs(result.metafile, snippetPath);
  const code = result.outputFiles.find((file) => file.path.endsWith(".js")).text;
  const map = JSON.parse(result.outputFiles.find((file) => file.path.endsWith(".map")).text);
  return { code, map };
}

// -----------------------------------------------------------------------------
// Sandbox mode: MUI X's imports.
//
// esbuild bundles any file a snippet names, files of the image included
// (`import x from "/etc/os-release"`, second opinion of 2026-10-30). The plugin
// admits from the snippet only the bare specifiers of the image's allowlist
// (agents/renderer/toolchain/import_allowlist.py: the `exports` maps of react,
// react-dom, @mui/material and @mui/x-charts), refuses every relative, absolute,
// `node:` and URL import, and lets the packages' own imports resolve as esbuild
// does, as long as each lands under ANYPLOT_NODE_MODULES. The harness's entry
// imports the snippet by its path and three of the allowlist's specifiers.
// -----------------------------------------------------------------------------
async function readAllowlist() {
  let parsed;
  try {
    parsed = JSON.parse(await readFile(IMPORT_ALLOWLIST, "utf-8"));
  } catch (err) {
    throw failure(`render: the import allowlist ${IMPORT_ALLOWLIST} is unreadable: ${err.message}`, "harness", "AllowlistError");
  }
  if (parsed?.schema !== 1 || !Array.isArray(parsed.specifiers) || parsed.specifiers.some((s) => typeof s !== "string")) {
    throw failure(`render: the import allowlist ${IMPORT_ALLOWLIST} is not schema 1`, "harness", "AllowlistError");
  }
  return new Set(parsed.specifiers);
}

function under(directory, file) {
  const relative = path.relative(directory, file);
  return relative !== "" && !relative.startsWith("..") && !path.isAbsolute(relative);
}

function realpath(file) {
  try {
    return realpathSync(file);
  } catch {
    return null;
  }
}

function sandboxImports(snippetPath, allowed) {
  const modules = realpathSync(NODE_MODULES);
  const snippet = realpathSync(snippetPath);
  // build.resolve() runs the plugin again; this marks the nested call.
  const nested = { anyplotNested: true };
  const refuse = (text) => ({ errors: [{ text, detail: "ImportRefused" }] });
  return {
    name: "anyplot-sandbox-imports",
    setup(build) {
      const resolveInside = async (specifier, args, resolveDir) => {
        const result = await build.resolve(specifier, { kind: args.kind, importer: args.importer, resolveDir, pluginData: nested });
        if (result.errors.length || result.namespace !== "file" || !result.path) return result;
        const target = realpath(result.path);
        if (result.external || target === null || !under(modules, target)) {
          return refuse(`import "${specifier}" refused: it resolves outside the image's packages`);
        }
        return result;
      };
      build.onResolve({ filter: /.*/ }, async (args) => {
        if (args.pluginData === nested) return undefined;
        // esbuild names the stdin entry's importer resolveDir/sourcefile, a file that does not exist.
        if (args.importer === path.join(BUILD_ROOT, ENTRY_FILE)) {
          // The harness's own entry: the snippet by its path, the rest from the packages.
          if (args.path === snippetPath) return { path: snippet };
          return resolveInside(args.path, args, BUILD_ROOT);
        }
        if (args.importer === snippet) {
          if (!allowed.has(args.path)) {
            const why = /^(\.|\/|[a-z][a-z0-9+.-]*:)/i.test(args.path)
              ? "relative, absolute, node: and URL imports are refused"
              : "it is not on the image's import allowlist";
            return refuse(`import "${args.path}" refused: ${why}`);
          }
          return resolveInside(args.path, args, BUILD_ROOT);
        }
        // A package's own import: esbuild's resolution, without a nested resolve per
        // import (3,391 of them for one MUI X chart took 2.5 s); the load hook below
        // reads no file outside the packages, and checkInputs refuses the bundle
        // unless every file in it lies inside them.
        return undefined;
      });
      // Every file esbuild loads passes here, also those an import with a template
      // (`import(\`../etc/${name}\`)`) matches without an onResolve call (the
      // security review read every file under /etc that way): a file outside the
      // packages is refused before esbuild reads it. The snippet is read here,
      // without its sourceMappingURL comments, which would make esbuild read the
      // named file as an input source map (`/dev/zero` until it died).
      const prefix = modules + path.sep;
      build.onLoad({ filter: /.*/ }, async (args) => {
        if (args.namespace !== "file") return undefined;
        if (args.path.startsWith(prefix)) {
          const file = realpath(args.path);
          if (file !== null && under(modules, file)) return undefined;
        } else if (realpath(args.path) === snippet) {
          const source = await readFile(snippet, "utf-8");
          return { contents: withoutSourceMapComments(source), loader: loaderFor(snippet) };
        }
        return refuse("an import refused: it reaches a file outside the image's packages");
      });
    },
  };
}

// esbuild's own loader for the snippet's extension (plot.tsx in the renderer).
function loaderFor(file) {
  const loaders = { ".tsx": "tsx", ".ts": "ts", ".jsx": "jsx", ".js": "js", ".mjs": "js", ".cjs": "js" };
  return loaders[path.extname(file).toLowerCase()] || "tsx";
}

// A `//# sourceMappingURL=` or `/*# sourceMappingURL= */` comment (`@` for `#`
// too) is blanked, its line breaks kept, so every other line keeps its number.
function withoutSourceMapComments(source) {
  return source
    .replace(/\/\/[#@][ \t]*sourceMappingURL=[^\n\r]*/g, "")
    .replace(/\/\*[#@][ \t]*sourceMappingURL=[\s\S]*?\*\//g, (comment) => comment.replace(/[^\n\r]/g, ""));
}

// Every file the bundle read lies inside the packages, or is the snippet or the
// harness's entry; anything else refuses the bundle before it reaches the page.
function checkInputs(metafile, snippetPath) {
  const modules = realpathSync(NODE_MODULES);
  const snippet = realpathSync(snippetPath);
  for (const input of Object.keys(metafile.inputs)) {
    if (input === ENTRY_FILE || input === "<stdin>") continue;
    const file = realpath(path.resolve(BUILD_ROOT, input));
    if (file === snippet || (file !== null && under(modules, file))) continue;
    throw failure(`the bundle read ${input}, which is outside the image's packages`, "import", "ImportRefused");
  }
}

function buildFailure(err, snippetPath) {
  // esbuild's BuildFailure carries `errors`; the first one names the cause.
  const first = Array.isArray(err?.errors) ? err.errors[0] : null;
  if (!first) return failure("render: esbuild failed", "build", "BuildError");
  const location = first.location;
  const inSnippet = location && path.resolve(BUILD_ROOT, location.file) === path.resolve(snippetPath);
  const where = inSnippet ? { file: path.basename(snippetPath), line: location.line } : null;
  // The text can quote the file it is about; it is passed on only when that file
  // is the snippet or a package's, or when the text is the plugin's own.
  const located = location ? realpath(path.resolve(BUILD_ROOT, location.file)) : null;
  const known =
    inSnippet ||
    first.detail === "ImportRefused" ||
    (located !== null && under(realpathSync(NODE_MODULES), located));
  const text = known ? String(first.text || "") : "esbuild failed on a file outside the snippet and the image's packages";
  let kind = "build";
  let cls = inSnippet ? "SyntaxError" : "BuildError";
  if (first.detail === "ImportRefused" || first.pluginName === "anyplot-sandbox-imports") {
    kind = "import";
    cls = "ImportRefused";
  } else if (/^(Could not resolve|No matching export)/.test(text)) {
    kind = "import";
    cls = "ImportNotFound";
  }
  return failure(text, kind, cls, where);
}

function parseArgs(argv) {
  const args = { square: false, library: null, file: null, figure: null };
  for (const arg of argv) {
    if (arg === "--square") args.square = true;
    else if (arg === "--landscape") args.square = false;
    else if (arg.startsWith("--library=")) args.library = arg.slice("--library=".length);
    else if (arg.startsWith("--figure=")) args.figure = arg.slice("--figure=".length);
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

// The data file as the page carries it: parsed here, so a broken file fails in
// Node, and kept as text for a `type="application/json"` element, which the
// page never runs. `<` is escaped, so a cell cannot close the element (no
// `</script>`, no `<!--`); U+2028 and U+2029 too. Inside valid JSON all three
// occur only in strings, where the escape is the same character.
const SCRIPT_BREAKING = new RegExp("[<\\u2028\\u2029]", "g");
async function readDataJson(file) {
  let text;
  let table;
  try {
    text = await readFile(path.resolve(process.cwd(), file), "utf-8");
    table = JSON.parse(text);
  } catch (err) {
    throw failure(`render: the data file ${file} is unreadable: ${err.message}`, "data", "DataError");
  }
  const columns = table?.columns;
  const rows = table?.data;
  const shaped =
    Array.isArray(columns) &&
    columns.every((name) => typeof name === "string") &&
    Array.isArray(rows) &&
    rows.every((row) => Array.isArray(row) && row.length === columns.length);
  if (!shaped) {
    throw failure(`render: the data file ${file} is not {"columns": [...], "data": [[...], ...]}`, "data", "DataError");
  }
  return text.replace(SCRIPT_BREAKING, (char) => `\\u${char.charCodeAt(0).toString(16).padStart(4, "0")}`);
}

function buildHtml({ tokens, bundleSource, snippetSource, css, sandbox = null, dataJson = null }) {
  // The bundle + snippet are inlined so the written .html is fully self-contained
  // (no CDN, no network) — the same page is screenshotted and shipped as the
  // interactive deliverable. JSON.stringify keeps the token/theme injection
  // injection-safe.
  //
  // Sandbox mode (`sandbox`: the code file's and the bundle's names) adds the
  // content security policy, error locations for the final error line and a
  // `//# sourceURL` per script, so a stack names the snippet's frames
  // (`plot.js:6:12`) apart from the bundle's. `dataJson` (readDataJson) becomes
  // window.ANYPLOT_DATA: one object per row in column order, the shape
  // d3.csvParse returns (with `.columns`), each value already typed. Without
  // either, the page is the pipeline's, byte for byte.
  const csp = sandbox ? `\n<meta http-equiv="Content-Security-Policy" content="${CONTENT_SECURITY_POLICY}" />` : "";
  const dataElement = dataJson === null ? "" : `<script type="application/json" id="anyplot-data">${dataJson}</script>\n`;
  const dataGlobal =
    dataJson === null
      ? ""
      : `
  window.ANYPLOT_DATA = (function () {
    var table = JSON.parse(document.getElementById("anyplot-data").textContent);
    var rows = table.data.map(function (row) {
      return Object.fromEntries(table.columns.map(function (name, i) { return [name, row[i]]; }));
    });
    rows.columns = table.columns.slice();
    return rows;
  })();`;
  const errorAt = sandbox
    ? `
  ${CONSOLE_GUARD}
  window.__anyplotErrorAt = null;
  window.addEventListener("error", (e) => {
    if (window.__anyplotErrorAt === null) window.__anyplotErrorAt = { file: String(e.filename || ""), line: e.lineno | 0 };
  });`
    : "";
  const bundleName = sandbox ? `\n//# sourceURL=${sandbox.bundleName}` : "";
  const snippetName = sandbox ? `\n//# sourceURL=${sandbox.snippetName}` : "";
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />${csp}
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
${dataElement}<script>
  // anyplot render context — the snippet reads these globals (the browser has no
  // process.env, so this is the JS analogue of ANYPLOT_THEME for Python/R/Julia).
  window.ANYPLOT_THEME = ${JSON.stringify(tokens.theme)};
  window.ANYPLOT_TOKENS = ${JSON.stringify(tokens)};
  // Exact-pixel mount size, in case a snippet wants to size a canvas explicitly.
  window.ANYPLOT_SIZE = { width: ${css.cssWidth}, height: ${css.cssHeight} };
  window.__anyplotError = null;
  window.addEventListener("error", (e) => { window.__anyplotError = String(e.error || e.message); });
  window.addEventListener("unhandledrejection", (e) => { window.__anyplotError = String(e.reason); });${errorAt}${dataGlobal}
</script>
<script>
${bundleSource.replace(/<\/script/gi, "<\\/script")}${bundleName}
</script>
<script>${SNIPPET_HEAD}${snippetSource.replace(/<\/script/gi, "<\\/script")}
} catch (err) {
  window.__anyplotError = String(err && err.stack ? err.stack : err);
  throw err;
}${snippetName}
</script>
</body>
</html>`;
}

// -----------------------------------------------------------------------------
// Sandbox mode: the final error line.
// -----------------------------------------------------------------------------

// Decodes one base64 VLQ segment of a source map's `mappings`.
const VLQ_DIGITS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
function vlqSegment(segment) {
  const values = [];
  let value = 0;
  let shift = 0;
  for (const char of segment) {
    const digit = VLQ_DIGITS.indexOf(char);
    if (digit < 0) return null;
    value += (digit & 31) << shift;
    if (digit & 32) {
      shift += 5;
    } else {
      values.push(value & 1 ? -(value >>> 1) : value >>> 1);
      value = 0;
      shift = 0;
    }
  }
  return values;
}

// The source line (1-based) of a bundle position (1-based line and column, as V8
// prints them) when that position maps into `sourcePath`; null otherwise.
function mappedLine(map, line, column, sourcePath) {
  let source = 0;
  let sourceLine = 0;
  let found = null;
  const lines = String(map.mappings || "").split(";");
  for (let index = 0; index < Math.min(line, lines.length); index += 1) {
    let generated = 0;
    for (const segment of lines[index].split(",")) {
      const values = segment ? vlqSegment(segment) : null;
      if (!values || !values.length) continue;
      generated += values[0];
      if (values.length >= 4) {
        source += values[1];
        sourceLine += values[2];
      }
      if (index === line - 1 && generated <= column - 1) found = values.length >= 4 ? { source, sourceLine } : null;
    }
  }
  if (found === null) return null;
  const named = map.sources?.[found.source];
  return named && path.resolve(BUILD_ROOT, named) === path.resolve(sourcePath) ? found.sourceLine + 1 : null;
}

// The snippet's line of the first stack frame inside it: the frames of the
// snippet's own script are named by its `//# sourceURL`; MUI X's go through the
// bundle's source map.
function snippetLine(stack, context) {
  const frame = /\(?([^\s()]+):(\d+):(\d+)\)?\s*$/;
  for (const raw of String(stack || "").split("\n").slice(1)) {
    const match = raw.trim().startsWith("at ") ? frame.exec(raw.trim()) : null;
    if (!match) continue;
    const [, file, lineText, columnText] = match;
    const line = Number(lineText);
    if (context.map === null && file === context.snippetName && line > SNIPPET_LINE_OFFSET) {
      return line - SNIPPET_LINE_OFFSET;
    }
    if (context.map !== null && file === context.bundleName && line > BUNDLE_LINE_OFFSET) {
      const mapped = mappedLine(context.map, line - BUNDLE_LINE_OFFSET, Number(columnText), context.snippetPath);
      if (mapped !== null) return mapped;
    }
  }
  return null;
}

function oneLine(text, limit) {
  const flat = String(text ?? "").replace(/\s+/g, " ").trim();
  return flat.length > limit ? `${flat.slice(0, limit - 1)}…` : flat;
}

// The page's error as Node received it can be any size (`throw new Error("x".repeat(5e7))`):
// sandbox mode keeps its name, at most PAGE_ERROR_CHARS of its message and of its frames,
// and the stack's first line rebuilt from the cut message, before anything copies it.
function cappedPageError(err) {
  const name = String(err?.name ?? "Error").slice(0, 64);
  const message = String(err?.message ?? err ?? "");
  const stack = typeof err?.stack === "string" ? err.stack : "";
  const head = `${name}: ${message}`;
  const frames = stack.startsWith(head) ? stack.slice(head.length) : stack.slice(stack.indexOf("\n") + 1 || stack.length);
  const cut = message.slice(0, PAGE_ERROR_CHARS);
  return { name, message: cut, stack: `${name}: ${cut}${frames.startsWith("\n") ? "" : "\n"}${frames.slice(0, PAGE_ERROR_CHARS)}` };
}

function errorClass(name, fallback) {
  return typeof name === "string" && /^[A-Za-z_$][\w$]{0,63}$/.test(name) ? name : fallback;
}

function finalErrorLine(err, context) {
  const known = FAILURES.get(err);
  let kind = known?.kind ?? "harness";
  let cls = known?.cls ?? errorClass(err?.name, "Error");
  let location = known?.location ?? null;
  let message = err?.message ?? String(err);
  if (context.crashed && (!known || kind === "page")) {
    kind = "crash";
    cls = "PageCrashed";
    message = "the page crashed (out of memory, most likely)";
    location = null;
  } else if (kind === "page" || (!known && context.pageError)) {
    // The first uncaught error in the page: its class, its message, its line. A
    // snippet that does not parse has no frame: setContent writes the page with
    // document.write, so the window's error event names the document
    // (about:blank) with the line inside the script, and the message carries
    // document.write's prefix (measured with Playwright 1.64). Only the
    // snippet's script can fail to parse: the context script is the harness's,
    // the bundle the library's.
    const page = context.pageError;
    const text = page ? null : String(context.inPageError ?? "");
    const named = text === null ? null : /^([A-Za-z_$][\w$]*): ?(.*)/.exec(text.split("\n", 1)[0]);
    kind = "page";
    cls = errorClass(page ? page.name : named?.[1], "Error");
    message = String(page ? page.message || page : named ? named[2] : text).replace(/^Failed to execute 'write' on 'Document': /, "");
    let line = snippetLine(page ? page.stack : text, context);
    const at = context.errorAt;
    const unparsed = cls === "SyntaxError" && at?.file === "about:blank";
    if (line === null && context.map === null && (unparsed || at?.file === context.snippetName) && at.line > SNIPPET_LINE_OFFSET) {
      line = at.line - SNIPPET_LINE_OFFSET;
    }
    location = line === null ? null : { file: context.snippetName, line };
  } else if (!known && err?.name === "TimeoutError") {
    kind = "timeout";
  }
  const where = location ? `${location.file}:${location.line}` : "-";
  const text = String(message).replace(/^render: /, "");
  return `render: error: ${kind} ${cls} ${where}: ${oneLine(text, ERROR_MESSAGE_CHARS)}`;
}

function printSummary(context) {
  const { kept, total } = context.console;
  if (total) {
    console.error(`render: ${total} console error(s) during render${total > kept.length ? `, the first ${kept.length}` : ""}:`);
    for (const message of kept) console.error(`  ${message}`);
  }
  const { requests, sockets } = context.refused;
  if (requests || sockets) console.error(`render: refused ${requests} request(s) and ${sockets} WebSocket(s)`);
}

// What a sandbox-mode failure's summary and final error line read.
const CONTEXT = {
  snippetName: null,
  snippetPath: null,
  bundleName: null,
  map: null,
  pageError: null,
  inPageError: null,
  errorAt: null,
  crashed: false,
  console: { kept: [], total: 0 },
  refused: { requests: 0, sockets: 0 },
};

// Sandbox mode: no popup (window.open returns null, so no page outside the
// context's routes), no WebRTC connection and the page's V8 heap capped
// (PAGE_HEAP_MB). Neither the routes nor the content security policy see
// WebRTC: a page's RTCPeerConnection reached a local STUN server over UDP and a
// TURN server over TCP (measured in JS-2). With the forced policy WebRTC uses
// no UDP and TCP only through the proxy, which is a closed port, also for the
// loopback, which a proxy otherwise bypasses.
function launchArgs() {
  const args = ["--no-sandbox", "--force-color-profile=srgb"];
  if (SANDBOX) {
    args.push(
      "--block-new-web-contents",
      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
      `--proxy-server=${DEAD_PROXY}`,
      "--proxy-bypass-list=<-loopback>",
      `--js-flags=--max-old-space-size=${PAGE_HEAP_MB}`,
    );
  }
  return args;
}

// Sandbox mode: `new Date("2026-03-01T00:00")` is midnight UTC whatever the
// host's zone; no service worker, whose requests no route sees.
const SANDBOX_PAGE_OPTIONS = { timezoneId: "UTC", serviceWorkers: "block", acceptDownloads: false };

// Sandbox mode's rules of a new page's context.
async function applyPageRules(page) {
  // Every request of the context is aborted (fetch, XHR, sendBeacon, images,
  // styles, frames), and every WebSocket closed, which the route does not see.
  // setContent loads no URL, so the inlined page itself needs no request.
  await page.context().route("**/*", (route) => {
    CONTEXT.refused.requests += 1;
    return route.abort("blockedbyclient");
  });
  await page.context().routeWebSocket("**", (ws) => {
    CONTEXT.refused.sockets += 1;
    ws.close();
  });
  // The context script guards the main frame's console; this, every frame's
  // after it (setContent writes into the page's first document, which no init
  // script reaches).
  await page.context().addInitScript({ content: CONSOLE_GUARD });
  page.on("crash", () => {
    CONTEXT.crashed = true;
  });
}

// Sandbox mode: `promise`, or a `timeout` failure once `deadline` has passed.
function boundedBy(deadline) {
  return (promise) => {
    let timer;
    const late = new Promise((_, reject) => {
      timer = setTimeout(
        () => reject(failure(`the page did not settle within ${SETTLE_TIMEOUT_MS / 1000} s`, "timeout", "TimeoutError")),
        Math.max(0, deadline - Date.now()),
      );
    });
    return Promise.race([promise, late]).finally(() => clearTimeout(timer));
  };
}

// Sandbox mode reads the page's own records cut in the page, as scalars, since
// the snippet can write them: the error record (returned), where the first
// error happened, and how many console errors the guard kept in the page.
async function readPageRecords(page, bounded) {
  const inPageError = await bounded(
    page.evaluate((limit) => {
      try {
        const value = window.__anyplotError;
        return value == null ? null : String(value).slice(0, limit);
      } catch (e) {
        return "an error record that cannot be read";
      }
    }, PAGE_ERROR_CHARS),
  );
  CONTEXT.errorAt = await bounded(
    page.evaluate(() => {
      try {
        const at = window.__anyplotErrorAt;
        return at ? { file: String(at.file).slice(0, 200), line: Number(at.line) | 0 } : null;
      } catch (e) {
        return null;
      }
    }),
  );
  // The console.error calls the guard kept in the page count too.
  const seen = await bounded(
    page.evaluate(() => {
      try {
        return Number(window.__anyplotConsoleSeen()) || 0;
      } catch (e) {
        return 0;
      }
    }),
  );
  CONTEXT.console.total += Math.max(0, seen - CONSOLE_KEEP);
  return inPageError;
}

function usage(...lines) {
  for (const line of lines) console.error(line);
  if (SANDBOX) console.error(`render: error: harness UsageError -: ${oneLine(lines[0].replace(/^render: /, ""), ERROR_MESSAGE_CHARS)}`);
  process.exit(2);
}

// -----------------------------------------------------------------------------
// Figure mode: plotly and bokeh (PB-1 of step 4 in
// agentic/specs/261024-agent-all-libraries.md).
//
// The renderer's Python harness runs the plot first, armed, in a child of its
// own, and the plot writes its figure as JSON (`fig.write_json`,
// `bokeh.embed.json_item`); the harness, never armed, then runs this file with
// `--library=<plotly|bokeh> --figure=plot-<theme>.json` and the package's
// directory in ANYPLOT_FIGURE_PACKAGE (agents/anyplot/render/harness.py,
// figure mode). The figure is the model-written plot's output, so it is data
// here: parsed in Node, carried by a `type="application/json"` element with `<`,
// U+2028 and U+2029 escaped, parsed again in the page and handed to
// `Plotly.newPlot` or `Bokeh.embed.embed_item`, never written into the page as
// markup or script. The page is sandbox mode's, its rules and console guard
// included, under a stricter policy (`figurePolicy`): scripts by the page's
// nonce alone and no `'unsafe-eval'`, so nothing the figure carries runs as
// code; figure mode refuses to run without ANYPLOT_SANDBOX=1.
//
// The canvas: the figure's own size in CSS pixels (plotly's layout width and
// height, bokeh's root width and height; a bokeh layout without one is drawn
// once at scale 1 and measured) picks the orientation, landscape at an aspect
// of 4:3 and wider, square below, and the box of that orientation around it;
// the device scale makes the box exactly 3200 x 1800 or 2400 x 2400 pixels. A
// plotly figure 800 x 450 is drawn at scale 4, 1600 x 900 at 2, a bokeh figure
// 4800 x 2700 at 2/3: the figure's layout and type sizes stay as the code wrote
// them and only the resolution follows the canvas, the way `write_image(width,
// height, scale)` and bokeh's `export_png` scale. A figure that names no size
// (plotly) gets 1600 x 900, and one narrower than its box is centred on the
// page's background.
// -----------------------------------------------------------------------------
const FIGURE_PACKAGE = process.env.ANYPLOT_FIGURE_PACKAGE || null;
// harness.FIGURE_MAX_BYTES, pinned equal by a test: the harness refuses a larger
// figure before this file runs; this is the check behind it.
const FIGURE_MAX_BYTES = 16 * 1024 * 1024;
// The sides a figure may name, in CSS pixels: the device scale stays between 10
// (320 wide) and 1/2 (6400 wide).
const FIGURE_MIN_SIDE = 320;
const FIGURE_MAX_SIDE = 6400;
const FIGURE_JSON_ID = "anyplot-figure-json";
const FIGURE_ID = "anyplot-figure";
// plotly.js's notice in place of a WebGL trace when the page has no WebGL, as
// the headless shell has none: a render that shows it fails as `draw NoWebGL`
// instead of passing with the notice for a plot.
const PLOTLY_NO_WEBGL = "WebGL is not supported by your browser";

// A figure page's policy: sandbox mode's, with the scripts admitted by a nonce
// of the page instead of 'unsafe-inline'. Every script of a figure page is the
// harness's own, so markup the figure carries (a bokeh Div's `<img onerror>`,
// measured running under 'unsafe-inline') runs no handler and no
// `javascript:` URL; no 'unsafe-eval' either, so CustomJS models do not compile.
function figurePolicy(nonce) {
  const policy = CONTENT_SECURITY_POLICY.replace("script-src 'unsafe-inline'", `script-src 'nonce-${nonce}'`);
  if (policy === CONTENT_SECURITY_POLICY) throw failure("render: the figure policy lost its script source", "harness", "PolicyError");
  return policy;
}
// The pixels of each canvas (ORIENTATIONS at DEVICE_SCALE_FACTOR).
const CANVAS_PIXELS = Object.fromEntries(
  Object.entries(ORIENTATIONS).map(([name, css]) => [name, [css.cssWidth * DEVICE_SCALE_FACTOR, css.cssHeight * DEVICE_SCALE_FACTOR]]),
);

function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// The figure file as the page carries it, and parsed: opened without following
// a link, at most FIGURE_MAX_BYTES, JSON of the library's shape.
async function readFigure(file, library) {
  let handle;
  try {
    handle = await open(path.resolve(process.cwd(), file), constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  } catch (err) {
    throw failure(`the figure ${file} could not be opened as a regular file (${err.code || err.name})`, "figure", "FigureError");
  }
  let text;
  try {
    const info = await handle.stat();
    if (!info.isFile()) throw failure(`the figure ${file} is not a regular file`, "figure", "FigureError");
    if (info.size > FIGURE_MAX_BYTES) {
      throw failure(`the figure ${file} is ${info.size} bytes, more than the ${FIGURE_MAX_BYTES}-byte limit`, "figure", "FigureTooLarge");
    }
    text = await handle.readFile("utf-8");
  } finally {
    await handle.close();
  }
  if (Buffer.byteLength(text, "utf-8") > FIGURE_MAX_BYTES) {
    throw failure(`the figure ${file} grew past the ${FIGURE_MAX_BYTES}-byte limit while it was read`, "figure", "FigureTooLarge");
  }
  let figure;
  try {
    figure = JSON.parse(text);
  } catch (err) {
    throw failure(`the figure ${file} is not JSON: ${err.message}`, "figure", "FigureError");
  }
  const shaped =
    library === "plotly"
      ? isRecord(figure) && Array.isArray(figure.data) && (figure.layout === undefined || isRecord(figure.layout))
      : isRecord(figure) &&
        typeof figure.root_id === "string" &&
        isRecord(figure.doc) &&
        Array.isArray(figure.doc.roots) &&
        figure.doc.roots.some((root) => isRecord(root) && root.id === figure.root_id);
  if (!shaped) {
    const expected = library === "plotly" ? '{"data": [...], "layout": {...}}' : "bokeh.embed.json_item's {root_id, doc}";
    throw failure(`the figure ${file} is not a ${library} figure (${expected})`, "figure", "FigureError");
  }
  // Inside valid JSON `<`, U+2028 and U+2029 occur only in strings, where the escape is the same character.
  return { figure, text: text.replace(SCRIPT_BREAKING, (char) => `\\u${char.charCodeAt(0).toString(16).padStart(4, "0")}`) };
}

// The figure's own size in CSS pixels, or null when only drawing it tells
// (a bokeh layout without a size of its own).
function figureSize(library, figure) {
  if (library === "plotly") {
    const layout = figure.layout ?? {};
    if (typeof layout.width === "number" && typeof layout.height === "number") {
      return checkedSize({ width: layout.width, height: layout.height });
    }
    return { width: ORIENTATIONS.landscape.cssWidth, height: ORIENTATIONS.landscape.cssHeight };
  }
  const root = figure.doc.roots.find((model) => isRecord(model) && model.id === figure.root_id);
  const attributes = isRecord(root.attributes) ? root.attributes : {};
  if (typeof attributes.sizing_mode === "string" && attributes.sizing_mode !== "fixed") {
    // A responsive root fills its container: the landscape box.
    return { width: ORIENTATIONS.landscape.cssWidth, height: ORIENTATIONS.landscape.cssHeight };
  }
  if (typeof attributes.width === "number" && typeof attributes.height === "number") {
    return checkedSize({ width: attributes.width, height: attributes.height });
  }
  return null;
}

function checkedSize(size) {
  const fits = (side) => Number.isFinite(side) && side >= FIGURE_MIN_SIDE && side <= FIGURE_MAX_SIDE;
  if (!fits(size.width) || !fits(size.height)) {
    const shown = `${Number(size.width).toFixed(0)} x ${Number(size.height).toFixed(0)}`;
    throw failure(`the figure is ${shown}, outside ${FIGURE_MIN_SIDE} to ${FIGURE_MAX_SIDE} CSS pixels a side`, "figure", "FigureError");
  }
  return size;
}

// The canvas around a figure: the orientation, its box in CSS pixels (the
// figure's own size at the box's aspect, a landscape width a multiple of 16, so
// both sides are whole pixels) and the device scale that makes the box the
// canvas's pixels.
function figureCanvas(size) {
  if (3 * size.width < 4 * size.height) {
    const side = Math.ceil(Math.max(size.width, size.height));
    return { orientation: "square", cssWidth: side, cssHeight: side, scale: CANVAS_PIXELS.square[0] / side };
  }
  const width = 16 * Math.ceil(Math.max(size.width, (size.height * 16) / 9) / 16);
  return { orientation: "landscape", cssWidth: width, cssHeight: (width * 9) / 16, scale: CANVAS_PIXELS.landscape[0] / width };
}

// The page's own drawing script: parse the figure from its JSON element, draw
// it with the library, and set the ready signal once it is drawn and the fonts
// are in, or the error record when the library refuses it.
function figureScript(library, size) {
  const draw =
    library === "plotly"
      ? `var layout = figure.layout || {};
    layout.width = ${size.width};
    layout.height = ${size.height};
    layout.autosize = false;
    var config = { staticPlot: true, displayModeBar: false, typesetMath: false, responsive: false, showTips: false };
    drawn = Plotly.newPlot(target, figure.data, layout, config);`
      : `drawn = Bokeh.embed.embed_item(figure, ${JSON.stringify(FIGURE_ID)});`;
  return `
(function () {
  var target = document.getElementById(${JSON.stringify(FIGURE_ID)});
  var failed = function (err) { window.__anyplotError = String(err && err.stack ? err.stack : err); };
  var drawn;
  try {
    var figure = JSON.parse(document.getElementById(${JSON.stringify(FIGURE_JSON_ID)}).textContent);
    ${draw}
  } catch (err) {
    failed(err);
    return;
  }
  Promise.resolve(drawn)
    .then(function () { return document.fonts ? document.fonts.ready : null; })
    .then(function () {
      requestAnimationFrame(function () { requestAnimationFrame(function () { window.__anyplotReady = true; }); });
    }, failed);
})();
//# sourceURL=anyplot-figure.js`;
}

// The figure's page: sandbox mode's policy, console guard and error records,
// the library's bundles, the figure as data and the drawing script. `canvas`
// null builds the measuring page, whose container takes the figure's own size.
function buildFigureHtml({ tokens, library, bundles, figureText, size, canvas }) {
  const container = canvas
    ? `width: ${canvas.cssWidth}px; height: ${canvas.cssHeight}px; display: flex; align-items: center; justify-content: center;`
    : "display: inline-block;";
  const nonce = randomBytes(18).toString("base64");
  const scripts = bundles
    .map(
      (source, index) =>
        `<script nonce="${nonce}">\n${source.replace(/<\/script/gi, "<\\/script")}\n//# sourceURL=anyplot-${library}-${index + 1}.js\n</script>`,
    )
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="Content-Security-Policy" content="${figurePolicy(nonce)}" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>anyplot</title>
<style>
  html, body { margin: 0; padding: 0; background: ${tokens.pageBg}; overflow: hidden; }
  #container { ${container} background: ${tokens.pageBg}; position: relative; overflow: hidden; }
</style>
</head>
<body>
<div id="container"><div id="${FIGURE_ID}"></div></div>
<script type="application/json" id="${FIGURE_JSON_ID}">${figureText}</script>
<script nonce="${nonce}">
  window.ANYPLOT_THEME = ${JSON.stringify(tokens.theme)};
  window.__anyplotError = null;
  window.addEventListener("error", (e) => { window.__anyplotError = String(e.error || e.message); });
  window.addEventListener("unhandledrejection", (e) => { window.__anyplotError = String(e.reason); });
  ${CONSOLE_GUARD}
  window.__anyplotErrorAt = null;
  window.addEventListener("error", (e) => {
    if (window.__anyplotErrorAt === null) window.__anyplotErrorAt = { file: String(e.filename || ""), line: e.lineno | 0 };
  });
</script>
${scripts}
<script nonce="${nonce}">${figureScript(library, size ?? { width: 0, height: 0 })}
</script>
</body>
</html>`;
}

// One page of a figure: sandbox mode's options and rules, the canvas's
// viewport and scale, drawn until the ready signal or the error record, both
// bounded by one deadline; a page error fails it as in a snippet's render.
async function drawFigurePage(browser, html, { width, height, scale, theme }) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: scale, ...SANDBOX_PAGE_OPTIONS });
  await applyPageRules(page);
  await page.emulateMedia({ reducedMotion: "reduce", colorScheme: theme });
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    CONTEXT.console.total += 1;
    if (CONTEXT.console.kept.length < CONSOLE_KEEP) CONTEXT.console.kept.push(oneLine(msg.text(), CONSOLE_MESSAGE_CHARS));
  });
  page.on("pageerror", (err) => {
    if (CONTEXT.pageError === null) CONTEXT.pageError = cappedPageError(err);
  });
  const bounded = boundedBy(Date.now() + SETTLE_TIMEOUT_MS);
  await bounded(page.setContent(html, { waitUntil: "load" }));
  await bounded(page.waitForFunction(() => window.__anyplotReady === true || window.__anyplotError != null, null, { timeout: 0 }));
  const inPageError = await readPageRecords(page, bounded);
  if (CONTEXT.pageError || inPageError) {
    CONTEXT.inPageError = inPageError;
    throw failure(`render: the figure failed to draw:\n${String(CONTEXT.pageError?.stack || inPageError)}`, "page", "Error");
  }
  const drew = await bounded(
    page.evaluate((id) => {
      const marks = (root) => {
        if (root.querySelector("canvas, svg, img")) return true;
        for (const element of root.querySelectorAll("*")) if (element.shadowRoot && marks(element.shadowRoot)) return true;
        return false;
      };
      const target = document.getElementById(id);
      return !!target && marks(target);
    }, FIGURE_ID),
  );
  if (!drew) throw failure("render: the figure drew nothing into #container (no <canvas>/<svg> mounted).", "draw", "NoOutput");
  const noWebGl = await bounded(
    page.evaluate(
      ([id, notice]) => Array.from(document.getElementById(id).querySelectorAll("p")).some((p) => p.textContent.startsWith(notice)),
      [FIGURE_ID, PLOTLY_NO_WEBGL],
    ),
  );
  if (noWebGl) throw failure("render: a WebGL trace cannot draw: the page has no WebGL", "draw", "NoWebGL");
  return { page, bounded };
}

async function renderFigure(args) {
  const library = args.library;
  if (!Object.hasOwn(FIGURES, library ?? "")) {
    usage(`render: --figure is for ${Object.keys(FIGURES).join(" and ")}, not "${library}"`);
  }
  const info = FIGURES[library];
  if (args.figure === null || args.file !== null) {
    usage(`render: ${library} draws a figure: pass --figure=<file> and no code file`);
  }
  if (!SANDBOX) usage("render: --figure needs ANYPLOT_SANDBOX=1");
  if (PAGE_ONLY) usage("render: ANYPLOT_PAGE_ONLY=1 builds no page for a figure");
  if (!FIGURE_PACKAGE) usage("render: --figure needs ANYPLOT_FIGURE_PACKAGE, the package's directory");

  const theme = process.env.ANYPLOT_THEME === "dark" ? "dark" : "light";
  const tokens = themeTokens(theme);
  CONTEXT.snippetName = path.basename(args.figure);
  CONTEXT.snippetPath = path.resolve(process.cwd(), args.figure);
  CONTEXT.bundleName = `anyplot-${library}.js`;

  const bundles = [];
  for (const file of info.files) {
    const bundlePath = path.join(FIGURE_PACKAGE, file);
    if (!existsSync(bundlePath)) usage(`render: bundle missing: ${bundlePath}`);
    bundles.push(await readFile(bundlePath, "utf-8"));
  }
  const { figure, text } = await readFigure(args.figure, library);
  let size = figureSize(library, figure);

  const browser = await chromium.launch({ args: launchArgs() });
  try {
    if (size === null) {
      // A bokeh layout: drawn once at scale 1 on a page as large as a figure
      // may be, where the container takes its size.
      const html = buildFigureHtml({ tokens, library, bundles, figureText: text, size: null, canvas: null });
      const measuring = { width: FIGURE_MAX_SIDE, height: FIGURE_MAX_SIDE, scale: 1, theme };
      const { page, bounded } = await drawFigurePage(browser, html, measuring);
      const box = await bounded(
        page.evaluate((id) => {
          const rect = document.getElementById(id).getBoundingClientRect();
          return { width: Math.ceil(rect.width), height: Math.ceil(rect.height) };
        }, FIGURE_ID),
      );
      await page.close();
      size = checkedSize(box);
    }
    const canvas = figureCanvas(size);
    const html = buildFigureHtml({ tokens, library, bundles, figureText: text, size, canvas });
    const shape = { width: canvas.cssWidth, height: canvas.cssHeight, scale: canvas.scale, theme };
    const { page, bounded } = await drawFigurePage(browser, html, shape);
    const png = await bounded(page.locator("#container").screenshot());
    const [width, height] = [png.readUInt32BE(16), png.readUInt32BE(20)];
    const [expectedWidth, expectedHeight] = CANVAS_PIXELS[canvas.orientation];
    if (width !== expectedWidth || height !== expectedHeight) {
      throw failure(`the screenshot is ${width}x${height}, not the ${canvas.orientation} canvas's ${expectedWidth}x${expectedHeight}`, "harness", "CanvasError");
    }
    const pngOut = path.resolve(process.cwd(), `plot-${theme}.png`);
    await writeFile(pngOut, png);
    printSummary(CONTEXT);
    console.log(
      `render: ${library} ${theme} ${canvas.orientation} figure ${size.width}x${size.height} at scale ${canvas.scale.toFixed(3)} → ${pngOut} (${width}×${height})`,
    );
  } finally {
    await browser.close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.figure !== null || Object.hasOwn(FIGURES, args.library ?? "")) {
    await renderFigure(args);
    return;
  }
  if (!args.file) {
    usage("usage: node automation/js-render/render.mjs <impl.js> [--library=<id>] [--square]");
  }
  if (PAGE_ONLY && !SANDBOX) {
    // The page leaves the sandbox as a download, so it is only ever the sandbox's page, policy included.
    usage("render: ANYPLOT_PAGE_ONLY=1 needs ANYPLOT_SANDBOX=1");
  }

  const theme = process.env.ANYPLOT_THEME === "dark" ? "dark" : "light";
  const tokens = themeTokens(theme);

  const filePath = path.resolve(process.cwd(), args.file);
  if (!existsSync(filePath)) {
    usage(`render: implementation file not found: ${filePath}`);
  }
  const snippetSource = await readFile(filePath, "utf-8");

  // Library id: explicit flag wins, else the file stem (chartjs.js → chartjs).
  const library = args.library || path.basename(filePath).replace(/\.(js|mjs|cjs|ts|tsx)$/i, "");
  if (Object.hasOwn(FIGURES, library)) {
    usage(`render: ${library} draws a figure, not a code file: pass --library=${library} --figure=<file>`);
  }
  const bundleInfo = BUNDLES[library];
  if (!bundleInfo) {
    usage(
      `render: unknown library "${library}". Known: ${Object.keys(BUNDLES).join(", ")}`,
      'Pass --library=<id> if the file is not named after its library (e.g. "<id>.js").',
    );
  }

  const orientation = orientationFromSource(snippetSource, args.square);
  const css = ORIENTATIONS[orientation];

  CONTEXT.snippetName = path.basename(filePath);
  CONTEXT.snippetPath = filePath;
  CONTEXT.bundleName = `anyplot-${library}.js`;
  const sandbox = SANDBOX ? { bundleName: CONTEXT.bundleName, snippetName: CONTEXT.snippetName } : null;
  const dataJson = DATA_JSON === null ? null : await readDataJson(DATA_JSON);

  // framework=react libs (MUI X) are esbuild-bundled into a single IIFE that
  // both pulls in react/@mui *and* mounts the snippet's default-exported
  // component — there is no separate UMD bundle + imperative snippet. We inline
  // that IIFE as the page's only library script (snippetSource left empty), so
  // the rest of the pipeline — self-contained HTML, draw check, screenshot — is
  // identical to the framework=none path.
  let html;
  if (bundleInfo.framework === "react") {
    const { code, map } = await bundleReactSnippet(filePath);
    CONTEXT.map = map;
    html = buildHtml({ tokens, bundleSource: code, snippetSource: "", css, sandbox, dataJson });
  } else {
    const bundlePath = path.join(NODE_MODULES, bundleInfo.dist);
    if (!existsSync(bundlePath)) {
      usage(`render: bundle missing: ${bundlePath}\nRun \`npm ci\` at the repo root first.`);
    }
    const bundleSource = await readFile(bundlePath, "utf-8");
    html = buildHtml({ tokens, bundleSource, snippetSource, css, sandbox, dataJson });
  }

  // Write the self-contained interactive page first — it is a deliverable in its
  // own right and useful for debugging even if the screenshot step later fails.
  const htmlOut = path.resolve(process.cwd(), `plot-${theme}.html`);
  // ANYPLOT_PAGE_ONLY: the page is the whole output. No browser starts, so the
  // snippet never runs here; it runs in the browser of whoever opens the page.
  if (PAGE_ONLY) {
    await writeFile(htmlOut, html, "utf-8");
    console.log(`render: ${library} ${theme} ${orientation} page → ${htmlOut}`);
    return;
  }
  if (!NO_HTML) await writeFile(htmlOut, html, "utf-8");

  const browser = await chromium.launch({ args: launchArgs() });
  try {
    const page = await browser.newPage({
      viewport: { width: css.cssWidth, height: css.cssHeight },
      deviceScaleFactor: DEVICE_SCALE_FACTOR,
      ...(SANDBOX ? SANDBOX_PAGE_OPTIONS : {}),
    });
    if (SANDBOX) await applyPageRules(page);

    // Static screenshot of an animated chart must catch the *final* frame, never
    // a mid-tween one. The library prompts already mandate disabling animation
    // (Chart.js/ECharts/Highcharts `animation:false`, MUI X `skipAnimation`), but
    // emulating `prefers-reduced-motion: reduce` is a belt-and-suspenders guard:
    // well-behaved libraries (MUI X among them) skip entrance animation under it,
    // so a forgotten flag can't leak a half-grown bar into the PNG. colorScheme
    // is pinned to the active theme for any lib that keys off prefers-color-scheme.
    await page.emulateMedia({ reducedMotion: "reduce", colorScheme: theme });

    // Sandbox mode keeps the first CONSOLE_KEEP console errors, each cut to
    // CONSOLE_MESSAGE_CHARS, and counts the rest (20,000 lines reached 4.2 MB
    // unbounded); the first page error is the one the final line names.
    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() !== "error") return;
      if (!SANDBOX) {
        consoleErrors.push(msg.text());
        return;
      }
      CONTEXT.console.total += 1;
      if (CONTEXT.console.kept.length < CONSOLE_KEEP) CONTEXT.console.kept.push(oneLine(msg.text(), CONSOLE_MESSAGE_CHARS));
    });
    let pageError = null;
    page.on("pageerror", (err) => {
      const kept = SANDBOX ? cappedPageError(err) : err;
      pageError = kept;
      if (CONTEXT.pageError === null) CONTEXT.pageError = kept;
    });

    // Sandbox mode bounds every answer the page gives by one deadline
    // (SETTLE_TIMEOUT_MS), loading the page included: a snippet whose inline
    // script never returns, or a page that never settles, fails as `timeout`.
    const bounded = SANDBOX ? boundedBy(Date.now() + SETTLE_TIMEOUT_MS) : (promise) => promise;

    await bounded(page.setContent(html, { waitUntil: "load" }));

    // Wait for a render-complete signal. A snippet MAY set window.__anyplotReady
    // (e.g. ECharts `chart.on('finished', ...)`) for precise timing; otherwise we
    // fall back to fonts-ready + a double rAF, which is sufficient for the
    // animation:false static renders the library prompts mandate. This is the
    // page.waitForFunction(...) signal the design calls for — never a time.sleep.
    // The signal can only arrive from a snippet whose source names it or from
    // the React entry (which sets it after fonts + three rAFs), so every other
    // snippet settles directly instead of idling through the timeout.
    // Playwright's signature is (pageFunction, arg, options): the options object
    // must sit in the third slot, or it becomes the page function's argument
    // and the wait runs to the 30 s default timeout.
    const settle = () =>
      bounded(
        page.evaluate(async () => {
          await (document.fonts ? document.fonts.ready : Promise.resolve());
          await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
        }),
      );
    const expectsReadySignal = bundleInfo.framework === "react" || snippetSource.includes("__anyplotReady");
    if (expectsReadySignal) {
      try {
        await bounded(page.waitForFunction(() => window.__anyplotReady === true, null, { timeout: 2500 }));
      } catch {
        // The signal never came (a guarded `finished` handler, say) — settle instead.
        await settle();
      }
    } else {
      await settle();
    }

    // Surface snippet failures loudly — a blank/half-drawn PNG must fail the
    // render so the pipeline retries, never ship silently. Throw (don't
    // process.exit) so the `finally` below still closes the browser; the outer
    // main().catch turns the throw into a non-zero exit.
    // Sandbox mode reads the page's own records cut in the page, as scalars, since
    // the snippet can write them.
    const inPageError = SANDBOX ? await readPageRecords(page, bounded) : await page.evaluate(() => window.__anyplotError);
    if (pageError || inPageError) {
      CONTEXT.inPageError = inPageError;
      throw failure(`render: the snippet threw while drawing:\n${String(pageError?.stack || pageError || inPageError)}`, "page", "Error");
    }

    // The HTML scaffold always provides `#container`, so its mere existence
    // proves nothing — assert the snippet actually drew something into it. All
    // three Phase-1 libraries mount a <canvas> (Chart.js, ECharts) or <svg>
    // (D3); an empty mount means the snippet rendered nothing and we must fail
    // rather than ship a blank PNG.
    const container = page.locator("#container");
    const drewSomething = await bounded(
      page.evaluate(() => {
        const el = document.getElementById("container");
        return !!el && el.querySelector("canvas, svg, img") !== null;
      }),
    );
    if (!drewSomething) {
      throw failure("render: snippet did not draw into #container (no <canvas>/<svg> mounted).", "draw", "NoOutput");
    }

    const pngOut = path.resolve(process.cwd(), `plot-${theme}.png`);
    await bounded(container.screenshot({ path: pngOut }));

    if (consoleErrors.length) {
      console.warn(`render: ${consoleErrors.length} console error(s) during render:`);
      for (const e of consoleErrors.slice(0, 5)) console.warn(`  ${e}`);
    }
    if (SANDBOX) printSummary(CONTEXT);

    const expected = `${css.cssWidth * DEVICE_SCALE_FACTOR}×${css.cssHeight * DEVICE_SCALE_FACTOR}`;
    console.log(`render: ${library} ${theme} ${orientation} → ${pngOut} (target ${expected})`);
    if (!NO_HTML) console.log(`render: wrote ${htmlOut}`);
  } finally {
    await browser.close();
  }
}

// Sandbox mode: the bounded summary, then the final error line, last on stderr;
// also for an exception outside main's chain (Playwright's own, while the
// browser closes).
function failSandboxed(err) {
  printSummary(CONTEXT);
  console.error(finalErrorLine(err, CONTEXT));
  process.exit(1);
}
if (SANDBOX) process.on("uncaughtException", failSandboxed);

main().catch((err) => {
  if (!SANDBOX) {
    console.error(err);
    process.exit(1);
  }
  failSandboxed(err);
});
