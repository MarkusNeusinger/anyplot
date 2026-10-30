"""Tests for agents/anyplot/code/profiles/javascript/validate.py: the SECURITY and ADAPTATION profiles for JavaScript.

The refused snippets are the named bypasses of the design passes (`agentic/specs/261024-agent-all-libraries.md`,
second opinions of 2026-10-24 and 2026-10-30) and the brief of JS-3: aliasing, computed access, optional chaining,
template literals, indirection through `globalThis`, `self` and `window`, `.constructor`, a string `setTimeout`,
dynamic `import()` and `require`. Each is refused by name or by shape, never by a helper name the test left unbound.
"""

from collections import Counter

import pytest

from agents.anyplot.code.profiles.javascript.normalise import normalise
from agents.anyplot.code.profiles.javascript.validate import (
    GLOBALS,
    module_label,
    validate_adaptation,
    validate_security,
)
from agents.anyplot.code.validate import Finding

from .conftest import JS_CATALOGUE_FILES, JS_CATALOGUE_NORMALISED, JS_WORKING, MUIX_WORKING, js_library


HEAD = (
    "//# anyplot-orientation: landscape\n"
    "const t = window.ANYPLOT_TOKENS;\n"
    'const el = document.createElement("div");\n'
    "const f = () => 1;\n"
    "let name = 'x', tag = 'div', key = 'a', cb = f, buffer = null, b = null, x = {};\n"
)
HELPERS = {"el", "f", "name", "tag", "key", "cb", "buffer", "b", "x"}
"""The names HEAD binds, so a snippet that uses them is refused for what it does with them."""
MUIX_HEAD = '//# anyplot-orientation: landscape\nimport { BarChart } from "@mui/x-charts/BarChart";\n'


def security(body: str, library: str = "chartjs") -> list[Finding]:
    return validate_security((MUIX_HEAD if library == "muix" else HEAD) + body + "\n", library=library)


def rules(findings: list[Finding]) -> set[str]:
    return {finding.rule for finding in findings}


def test_the_working_forms_in_miniature_pass_both_profiles() -> None:
    assert validate_security(JS_WORKING) == []
    assert validate_adaptation(JS_WORKING, original_palette=[]) == []
    assert validate_security(JS_CATALOGUE_NORMALISED) == []
    assert validate_security(MUIX_WORKING, library="muix") == []
    assert validate_adaptation(MUIX_WORKING, original_palette=[], library="muix") == []


def test_the_head_alone_passes() -> None:
    assert security("") == []


@pytest.mark.parametrize(
    "body",
    [
        # the network, by name, alias, shorthand, optional call and the page's objects
        'fetch("/x")',
        'fetch?.("/x")',
        "const g = fetch;",
        "const o = { fetch };",
        'window.fetch("/x")',
        'window?.fetch("/x")',
        'window["fetch"]("/x")',
        'window[`fetch`]("/x")',
        'window["fe" + "tch"]("/x")',
        'window[`fe${"tch"}`]("/x")',
        'window[name]("/x")',
        "const w = window;",
        'const { fetch: g } = window; g("/x");',
        "const all = { ...window };",
        "const pair = [window];",
        "f(window);",
        "f(document);",
        "const d = document;",
        "Object.values(window);",
        '(0, window).fetch("/x")',
        'globalThis.fetch("/x")',
        'self.fetch("/x")',
        'top.fetch("/x")',
        'parent.postMessage("x", "*")',
        "const frame = frames[0];",
        'window.self.fetch("/x")',
        'window.window.fetch("/x")',
        "window.top.location.href = name;",
        'window.open("/x")',
        'window.open?.("/x")',
        'open("/x")',
        "location.href = name;",
        "document.location = name;",
        "const c = document.cookie;",
        'const c = document["cookie"];',
        'document.write("<p>")',
        'document.defaultView.fetch("/x")',
        'el.ownerDocument.defaultView.fetch("/x")',
        "const xhr = new XMLHttpRequest();",
        'const ws = new WebSocket("ws://x");',
        'const es = new EventSource("/x");',
        'const worker = new Worker("w.js");',
        'const shared = new SharedWorker("w.js");',
        'const channel = new BroadcastChannel("x");',
        "const peer = new RTCPeerConnection();",
        'navigator.sendBeacon("/x", "d");',
        'localStorage.setItem("a", "b");',
        'window.localStorage.getItem("a");',
        'sessionStorage.getItem("a");',
        'indexedDB.open("a");',
        'caches.open("a");',
        'postMessage("x");',
        'new Image().src = "/x";',
        'const img = new window.Image(); img.src = "/x";',
        'const blob = new Blob(["x"]);',
        "const url = URL.createObjectURL(b);",
        'd3.json("/x")',
        'd3.csv("/x")',
        'd3.image("/x")',
        'Highcharts.ajax({ url: "/x" })',
        # code from strings
        'eval("1")',
        '(0, eval)("1")',
        'window.eval("1")',
        'const run = new Function("return 1");',
        'Function("return 1")()',
        '(() => {}).constructor("return 1")()',
        '[].map.constructor("x")()',
        'Object.getPrototypeOf(async () => {}).constructor("x")',
        'const C = x["constructor"];',
        "const C = x?.constructor;",
        "const { constructor: C } = f;",
        'const k = "constructor";',
        "const proto = x.__proto__;",
        'x.__defineGetter__("a", f);',
        "const w = el.getRootNode().defaultView;",
        'const k = "ownerDocument";',
        'setTimeout("go()", 1)',
        'setInterval("go()", 1)',
        "setTimeout(name, 1)",
        "setTimeout(cb, 1)",
        "window.setTimeout(name, 1)",
        "queueMicrotask(f)",
        "const parser = new DOMParser();",
        'const descriptor = Object.getOwnPropertyDescriptor(x, "a");',
        "Object.defineProperty(x, key, {});",
        "Object.setPrototypeOf(x, null);",
        'Reflect.get(x, "a");',
        "const proxy = new Proxy(x, {});",
        "WebAssembly.compile(buffer);",
        "const ref = new WeakRef(x);",
        "with (x) { f(); }",
        # code loaded at run time
        'import("data:text/javascript,1")',
        'require("fs")',
        "const meta = import.meta;",
        # elements that run code or load
        'document.createElement("script")',
        'document.createElement("SCRIPT")',
        'document.createElement("iframe")',
        "document.createElement(tag)",
        'document.createElementNS("http://www.w3.org/2000/svg", "script")',
        'd3.select("body").append("script")',
        'd3.select("body").append("svg:script")',
        'd3.select("body").insert("iframe")',
        'd3.create("iframe")',
        "el.innerHTML = '<img src=x onerror=\"go()\">';",
        'el.innerHTML = "<script>go()</script>";',
        # this as the window
        "const me = this;",
        "const arrow = () => this.fetch;",
        'function g() { return this.fetch("/x"); }',
        # literals
        'const u = "https://example.org/data.json";',
        "const v = `wss://example.org`;",
        'const dataUrl = "data:text/html,<p>";',
        'const js = "javascript:go()";',
        'const s = "' + "a" * 201 + '";',
        # the theme and the canvas
        't.pageBg = "#FF00FF";',
        't.palette.push("#FFFFFF");',
        't.palette[0] = "#FFFFFF";',
        "t.palette.sort();",
        'Object.assign(t, { ink: "#F00" });',
        "delete t.ink;",
        "t.ink += 1;",
        'window.ANYPLOT_THEME = "dark";',
        'window.ANYPLOT_TOKENS.ink = "#F00";',
        "window.ANYPLOT_SIZE.width++;",
        "var t = {};",
        "function t() {}",
        "const data = window.ANYPLOT_DATA;",
        "const window = {};",
        "const document = {};",
        "var Chart = f;",
        "function loadUserData() { return []; }",
        'const s = "//# anyplot-orientation: square";',
        "const s = `\n//# anyplot-orientation: square\n`;",
        "/* //# anyplot-orientation: square */",
        "//# anyplot-orientation: square",
        "const a = 1; //# anyplot-orientation: square",
        # imports in a classic script
        'import fs from "fs";',
        "export const a = 1;",
        # the review of JS-3 (Fable and Gemini 3.8 Flash): `this` that may be the window
        "function g() { return this; }\nconst w = g();",
        "const g = function () { return this; };\ng();",
        "(function () { const w = this; })();",
        "const all = [1].map(function () { return this; });",
        "function g() { return this; }\nsetTimeout(g, 0);",
        "function g() { return { ...this }; }\ng();",
        "function g() { const { fetch: h } = this; }\ng();",
        'function g() { return this["fe" + "tch"]; }\ng();',
        "function g() { return this[name]; }\ng();",
        "d3.select(el).call(function () { f(this); });",
        "function g() { return this; }\nconst h = g;",
        "function g() { return this; }\nconst bound = g.bind(null);",
        # computed keys built from strings
        'const k = "con" + "structor";\nconst c = [][k];',
        'const c = []["con" + "structor"];',
        "const c = [][`con${name}`];",
        "const c = []['__pro' + `to__`];",
        'const c = [][["con", "structor"].join("")];',
        "const c = [][String.fromCharCode(99)];",
        "const c = [][atob(name)];",
        'const { ["con" + "structor"]: C } = f;',
        "let k2 = 'a';\nk2 = 'con' + name;\nconst c = [][k2];",
        'el["hr" + "ef"] = name;',
        # URLs, writes that load or navigate
        'el.src = "//example.org/p?" + name;',
        'const u = "//cdn.example.org/lib.js";',
        "el.src = name;",
        "el.href = name;",
        "el.location = name;",
        'el.cookie = "a=b";',
        "el.action = name;",
        "const c = document.documentElement.parentNode.cookie;",
        'document.documentElement.parentNode.cookie = "a";',
        'el.ownerDocument.write("<p>");',
        'x.writeln("<p>");',
        'el.setAttribute("href", name);',
        'el.setAttribute("src", name);',
        'el.setAttribute("action", name);',
        'el.setAttributeNS(null, "href", name);',
        'd3.select(el).append("a").attr("href", name);',
        'd3.select(el).append("image").attr("xlink:href", name);',
        # tags handed on by a name or written as a string
        'const tag2 = "iframe";\nd3.select("body").append(tag2);',
        'const tag2 = "link";\nd3.select("body").append(tag2);',
        'const tag2 = name ? "object" : "g";\nd3.select("body").append(tag2);',
        'const s = "IFRAME";',
        'const s = "svg:script";',
        'const s = " embed ";',
        # the Copilot review of #12473: a literal index calls the member it names
        'd3["create"]("script");',
        'el["setAttribute"]("href", name);',
        'x["write"]("<p>");',
        'el.ownerDocument["writeln"]("<p>");',
        'document["createElement"]("iframe");',
        'document["createElement"](tag);',
        'd3.select(el)["append"]("object");',
        # every name a ternary may give an attribute, and a name code computes
        'el.setAttribute(name ? "x" : "href", name);',
        'el.setAttribute(name ? "action" : "x", name);',
        "el.setAttribute(name, name);",
        "d3.select(el).attr(tag, name);",
        # the page's objects through a `this` that may be the window
        "function g() { return this.document.body; }\ng();",
        "function g() { return this.window; }\ng();",
        "const all = [1].map(function () { return this.document.cookie; });",
        # `arguments` is no name at the top level
        "const a = arguments;",
        "const a = () => arguments[0];",
    ],
)
def test_refused(body: str) -> None:
    findings = security(body)

    assert findings, body
    unbound = {finding.message.split("'")[1] for finding in findings if "neither bound by the code" in finding.message}
    assert not unbound & HELPERS, findings


@pytest.mark.parametrize(
    "body",
    [
        'import fs from "fs";',
        'import x from "./local";',
        'import x from "../up";',
        'import x from "/etc/os-release";',
        'import x from "node:fs";',
        'import x from "https://example.org/x.js";',
        'import { LineChart } from "@mui/x-charts-pro/LineChart";',
        'import _ from "lodash";',
        'export * from "fs";',
        'export { readFile } from "fs";',
        'import type { Stats } from "fs";',
        'import x = require("fs");',
        "const p = import('@mui/material');",
        "const Bad = () => <script>{'go()'}</script>;",
        'const Bad = () => <iframe src="about:blank" />;',
        "const Bad = () => <div dangerouslySetInnerHTML={{ __html: '<b>' }} />;",
        'const Bad = () => <a href="https://example.org">x</a>;',
        "const p = { dangerouslySetInnerHTML: { __html: 'x' } };\nconst Bad = () => <div {...p} />;",
        "const p = { 'dangerouslySetInnerHTML': { __html: 'x' } };",
        'import React from "react";\nconst Bad = () => React.createElement("script", null, "go()");',
        'import { createElement } from "react";\nconst Bad = () => createElement("iframe");',
        'import { jsx } from "react/jsx-runtime";\nconst Bad = () => jsx("object", {});',
        'import React from "react";\nconst tag = "embed";\nconst Bad = () => React.createElement(tag);',
    ],
)
def test_refused_in_a_muix_module(body: str) -> None:
    assert security(body, "muix"), body


def test_a_banned_import_carries_a_closed_label() -> None:
    findings = security('import fs from "fs";\nimport x from "patient-records";', "muix")

    assert sorted(finding.module or "" for finding in findings if finding.rule == "banned-import") == ["?", "fs"]
    assert module_label("@mui/x-charts-pro/LineChart") == "@mui/x-charts-pro"
    assert module_label("node:child_process") == "node"


@pytest.mark.parametrize(
    ("library", "body"),
    [
        ("chartjs", "setTimeout(() => f(), 1)"),
        ("chartjs", "setTimeout(function () { f(); }, 1)"),
        ("chartjs", "window.__anyplotReady = true;"),
        ("chartjs", 'window.addEventListener("resize", f);'),
        ("chartjs", "const dpr = window.devicePixelRatio || 1;"),
        ("chartjs", "const { width } = window.ANYPLOT_SIZE;"),
        ("chartjs", "const half = window.ANYPLOT_SIZE.width / 2;"),
        ("chartjs", 'document.getElementById("container").appendChild(el);'),
        ("chartjs", 'document.createElementNS("http://www.w3.org/2000/svg", "rect");'),
        ("d3", 'd3.select("#container").append("svg").append("g");'),
        ("d3", "const sel = d3.select(el).append(() => el);"),
        ("chartjs", 'const copy = [...t.palette];\ncopy.push("#FFFFFF");'),
        ("chartjs", "const rows = Object.entries(x).map(([k, v]) => ({ k, v }));"),
        ("chartjs", "const merged = Object.assign({}, x);"),
        ("chartjs", "const open = x.open;"),
        ("chartjs", "const candle = { open: 1, close: 2 };\nconst o = candle.open;"),
        ("chartjs", 'const edge = { caller: "main", callee: "draw" };\nconst who = edge.caller + edge["callee"];'),
        ("chartjs", 'const COLUMN = "Genre </script><b> — days from onset = 3";'),
        ("chartjs", "const parent = { x: 1 }; const top = parent.x;"),
        ("chartjs", "function mean(window) { return window.reduce((a, v) => a + v, 0); }"),
        ("chartjs", "const fmt = new Intl.NumberFormat('de-DE').format(1);"),
        ("chartjs", "const big = Number.MAX_SAFE_INTEGER;"),
        ("chartjs", "const text = JSON.stringify(x);"),
        ("chartjs", "class Series { constructor() { this.points = []; } total() { return this.points.length; } }"),
        ("chartjs", "const options = { formatter() { return this.y; } };"),
        ("chartjs", "const d = new Date(Date.UTC(2024, 0, 1));"),
        ("chartjs", "const color = '#009E73';"),
        ("chartjs", "requestAnimationFrame(() => f());"),
        ("chartjs", "const f2 = (t) => t * 2;"),
        ("chartjs", "function shadow(t) { t = 1; return t; }"),
        ("muix", 'import Box from "@mui/material/Box";\nconst B = () => <Box sx={{ p: 1 }}><svg><rect /></svg></Box>;'),
        ("muix", 'import { useMemo } from "react";\nexport default function Chart() { return useMemo(() => 1, []); }'),
        # the review of JS-3: `this` where a library sets it, as the catalogue uses it
        ("d3", 'd3.select(el).each(function () { d3.select(this).attr("x", 1); });'),
        ("d3", 'd3.select(el).on("click", function (event) { const p = d3.pointer(event, this); });'),
        ("highcharts", "const o = { chart: { events: { load: function () { const chart = this; } } } };"),
        (
            "highcharts",
            "function drawAll() { const chart = this; }\nconst o = { events: { load: drawAll, render: drawAll } };",
        ),
        ("highcharts", "const drawV = function () { const c = this; };\nconst o = { events: { load: drawV } };"),
        ("highcharts", "function drawAll() { const chart = this; }\nconst o = { events: { drawAll } };"),
        ("highcharts", "const o = { events: { load() { [1].forEach(() => f(this)); } } };"),
        ("chartjs", "const o = { f() { return this; } };"),
        ("chartjs", "class K { m() { return this; } }"),
        ("chartjs", "function g() { return this.y; }\ng();"),
        ("chartjs", "function never() { return this; }"),
        # timers with a function the file declares (Gemini 3.8 Flash)
        ("chartjs", "function draw() {}\nsetTimeout(draw, 0);"),
        ("chartjs", "const draw = () => {};\nsetInterval(draw, 10);"),
        # keys the catalogue builds (andrews-curves, chernoff-basic, parallel-categories-basic, chessboard-pieces)
        ("chartjs", 'const r = { a: 1 };\nconst v = r[name + "Norm"];'),
        ("chartjs", "const w = {};\nconst v = w[`z_${name}`];\nw[`z_${name}`] = 1;"),
        ("chartjs", "const v = {}[`${name}|${tag}`];"),
        ("chartjs", "const v = {}[`${name}${tag}`];"),
        ("chartjs", "const v = [1, 2][Math.floor(f())];"),
        ("chartjs", "const v = {}[String(name)];"),
        # data URLs the code drew (heatmap-mandelbrot and recurrence-basic in D3)
        ("d3", 'const url = el.toDataURL("image/png");\nd3.select(el).append("image").attr("href", url);'),
        ("d3", 'd3.select(el).append("image").attr("href", document.createElement("canvas").toDataURL());'),
        ("chartjs", 'const img = document.createElement("img");\nimg.src = el.toDataURL();'),
        ("chartjs", 'el.setAttribute("d", "M0 0L1 1");'),
        # words that are tags only where a tag is made
        ("d3", 'const s = "link";\nconst b2 = "base";\nconst o = "object";\nd3.selectAll(".link");'),
        ("chartjs", "const loc = { location: 'Berlin' };\nconst where = loc.location;"),
        # Gemini 3.8 Flash: `undefined` is no free name, and binding forms it asked for
        ("chartjs", "const y = undefined;"),
        ("chartjs", "function g({ a = 1, b: [c = 2] = [] } = {}) { return a + c; }\ng();"),
        ("chartjs", "try { f(); } catch ({ message }) { el.textContent = message; }"),
        # the Copilot review of #12473: what the narrowed rules keep
        ("chartjs", 'el.setAttribute(name ? "x" : "y", 1);'),
        ("chartjs", 'el["setAttribute"]("d", "M0 0");'),
        ("highcharts", "const o = { tooltip: { formatter() { return this.point.y + this.series.name; } } };"),
        ("highcharts", "const o = { events: { load: function () { const c = this.chart; } } };"),
        ("chartjs", "function total() { return arguments.length; }\ntotal(1, 2);"),
        ("chartjs", "function outer() { return () => arguments[0]; }\nouter(1);"),
        ("chartjs", "const o = { m() { return arguments.length; } };"),
        (
            "muix",
            "const T = () => (\n  <>\n    <>\n      <svg><g /></svg>\n    </>\n    <span>{[1].map((v) => <b key={v}>{v}</b>)}</span>\n  </>\n);",
        ),
    ],
)
def test_admitted(library: str, body: str) -> None:
    assert security(body, library) == [], security(body, library)


@pytest.mark.parametrize(
    ("library", "body"),
    [
        ("chartjs", "function key() { return name; }\nconst v = el[key()];"),
        ("chartjs", "function put(o, k, v) { o[k] = v; }\nput(el, name, name);"),
        ("chartjs", "const o = { m: function () { return this; } };\nconst g = o.m;\nconst w = g();"),
        ("chartjs", 'el.innerHTML = "<img src=x on" + "error=go()>";'),
        ("muix", "const B = ({ url }: { url: string }) => <img src={url} />;"),
        ("highcharts", "const chart = Highcharts.chart(el, {});\nchart.renderer.image(name, 0, 0, 10, 10).add();"),
    ],
)
def test_still_passes_contained_by_the_sandbox(library: str, body: str) -> None:
    """The hygiene line, pinned (module docstring, "What still passes"): a key a function returns or a parameter
    carries, a method called off its object, markup assembled at run time, a URL a JSX attribute or a library's image
    call takes. The renderer's page rules and gVisor contain them; the exported page carries JS-4's content security
    policy. A rule that starts refusing one of them moves it to `test_refused`."""
    assert security(body, library) == [], security(body, library)


def test_the_library_global_is_the_files_own() -> None:
    assert security("const chart = echarts.init(el);", "chartjs")[0].message == (
        "'echarts' is echarts's global, which this page does not load"
    )
    assert security("const chart = echarts.init(el);".replace("echarts", "Chart"), "chartjs") == []
    assert "d3" not in GLOBALS


def test_a_protected_statement_shares_no_line() -> None:
    code = "//# anyplot-orientation: landscape\nconst t = window.ANYPLOT_TOKENS; const evil = 1;\n"

    assert rules(validate_security(code)) == {"banned-statement"}


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("const a = 1;\n", "no //# anyplot-orientation directive; keep the one the code had"),
        (
            "//# anyplot-orientation: landscape\n//# anyplot-orientation: square\n",
            "more than one orientation directive; keep the first one alone",
        ),
    ],
)
def test_one_directive(code: str, message: str) -> None:
    assert [finding.message for finding in validate_security(code)] == [message]


def test_size_encoding_and_syntax_are_findings() -> None:
    assert rules(validate_security("x" * 200_001)) == {"size"}
    assert rules(validate_security("const a = (;\n")) == {"syntax"}
    assert rules(validate_security("const a = '\udcff';\n")) == {"encoding"}


def test_messages_never_echo_string_contents() -> None:
    findings = security('fetch("SECRET-CELL-VALUE")')

    assert not any("SECRET" in finding.message for finding in findings)


# --- ADAPTATION ------------------------------------------------------------------------


def adaptation(body: str, palette: list[str] | None = None, library: str = "chartjs") -> list[Finding]:
    code = JS_WORKING.replace("const data = loadUserData();\n", "const data = loadUserData();\n" + body + "\n")
    if library == "muix":
        code = MUIX_WORKING.replace("const data = loadUserData();\n", "const data = loadUserData();\n" + body + "\n")
    return validate_adaptation(code, original_palette=palette or [], library=library)


@pytest.mark.parametrize(
    ("body", "rule"),
    [
        ("const more = loadUserData();", "placeholder-use"),
        ("const g = loadUserData;", "placeholder-use"),
        ("const n = d3.randomNormal(0, 1)();", "rng"),
        ("const e = d3.randomExponential(1)();", "rng"),
        ("const v = [" + ", ".join(str(index) for index in range(21)) + "];", "literal-data"),
        ("const m = [[1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7]];", "literal-data"),
        ('const IMPRINT_PALETTE = ["#C475FD", "#009E73"];', "palette-prefix"),
        ('const IMPRINT_PALETTE = ["#009E73", "#FF00FF"];', "palette-prefix"),
        ("const IMPRINT = t.palette;", "palette-prefix"),
        ('const IMPRINT = ["#009E73"];\nIMPRINT.push("#C475FD");', "palette-prefix"),
    ],
)
def test_adaptation_findings(body: str, rule: str) -> None:
    assert rule in rules(adaptation(body)), adaptation(body)


@pytest.mark.parametrize(
    "body",
    [
        "const jitter = Math.random() * 0.1;",
        "const u = d3.randomUniform(0, 1)();",
        "const shuffled = d3.shuffle(data.slice());",
        'const IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3"];',
        "const ticks = [0, 25, 50, 75, 100];",
    ],
)
def test_adaptation_admits(body: str) -> None:
    assert adaptation(body) == []


def test_the_placeholder_count() -> None:
    twice = JS_WORKING.replace("const data = loadUserData();", "const data = loadUserData();\nconst data2 = 1;")
    none = JS_WORKING.replace("const data = loadUserData();", "const data = [];")

    assert rules(validate_adaptation(twice, original_palette=[])) == set()
    assert rules(validate_adaptation(none, original_palette=[])) == {"placeholder-count"}


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (
            'import { ChartContainer } from "@mui/x-charts/ChartContainer";',
            "the module '@mui/x-charts/ChartContainer' is not in the image's MUI X; import from a module it exports",
        ),
        (
            'import { ChartContainer } from "@mui/x-charts";',
            "'ChartContainer' is not exported by MUI X 9; use ChartsContainer from @mui/x-charts/ChartsContainer",
        ),
    ],
)
def test_a_muix_7_import_is_an_adaptation_finding_not_a_security_one(line: str, message: str) -> None:
    code = MUIX_WORKING.replace(
        'import Typography from "@mui/material/Typography";',
        f'import Typography from "@mui/material/Typography";\n{line}',
    )

    assert validate_security(code, library="muix") == []
    findings = validate_adaptation(code, original_palette=[], library="muix")
    assert [(finding.rule, finding.message) for finding in findings] == [("unavailable-import", message)]


def test_catalogue_corpus() -> None:
    """The SECURITY profile over the 1,617 normalised files on 2026-10-30: findings in 8 files only, each for a real
    reason. qrcode-basic encodes the URL https://anyplot.ai in all five libraries (`url-literal`); line-parametric's
    Chart.js legend is a 683-character HTML string (`string-length`); the MUI X flowmap-origin-destination, a map spec,
    writes coastlines as strings past 200 characters (`string-length`)."""
    flagged: dict[str, set[str]] = {}
    for path in JS_CATALOGUE_FILES:
        library = js_library(path)
        findings = validate_security(normalise(path.read_text(encoding="utf-8"), library=library), library=library)
        if findings:
            flagged[f"{path.parts[-4]}/{library}"] = rules(findings)

    assert flagged == {
        **{
            f"qrcode-basic/{library}": {"url-literal"} for library in ("chartjs", "d3", "echarts", "highcharts", "muix")
        },
        "line-parametric/chartjs": {"string-length"},
        "flowmap-origin-destination/muix": {"string-length"},
    }


def test_the_catalogues_free_names_are_all_admitted() -> None:
    """Every name the catalogue reads from the page is in `GLOBALS` or a library's own global (a closed world)."""
    counts: Counter[str] = Counter()
    for path in JS_CATALOGUE_FILES:
        library = js_library(path)
        for finding in validate_security(path.read_text(encoding="utf-8"), library=library):
            counts[finding.rule] += "neither bound by the code" in finding.message
    assert counts.get("banned-name", 0) == 0
