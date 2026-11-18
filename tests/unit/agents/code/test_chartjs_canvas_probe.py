"""The Chart.js 2D canvas text recorder in `automation/js-render/render.mjs` (sandbox mode).

Two layers exercise the same acceptance figures against `automation/js-render/render.mjs`:

1. `TestInNode` runs the real `automation/js-render/render.mjs` CLI to build `plot-light.html` (both with
   `ANYPLOT_SANDBOX=1` and without it), executes the page's `<script>` blocks against the pinned library bundles in
   `node_modules/` (`chart.js`, `echarts`, `highcharts`) inside a `node:vm` page context with a 2D canvas and DOM
   shim, and evaluates `pageTexts` and `textLabels` imported directly from `automation/js-render/render.mjs`. It needs
   only `node` and `node_modules/`, so every acceptance case and mutation check runs without a browser binary.
2. `TestInChromium` runs the full Playwright Chromium render (`plot-light.png` + `probe-light.json`) wherever
   Playwright's browser is installed (as in CI) and skips cleanly with the harness's skip message otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
HARNESS = REPO_ROOT / "automation" / "js-render" / "render.mjs"
ALLOWLIST_BUILDER = REPO_ROOT / "agents" / "renderer" / "toolchain" / "import_allowlist.py"
CANVAS = 'const canvas = document.createElement("canvas");\ndocument.getElementById("container").appendChild(canvas);\n'
NO_BROWSER = {"PLAYWRIGHT_BROWSERS_PATH": "/nonexistent/anyplot-no-browsers"}

# Runs in Node: imports `pageTexts` and `textLabels` from the checkout's `render.mjs`, loads the HTML page that
# `render.mjs` itself wrote, executes every non-JSON `<script>` block in order inside a `node:vm` page realm with a
# minimal DOM + 2D canvas implementation, and prints `{fillTextWrapped, strokeTextWrapped, probe, pageError}`.
NODE_PAGE_RUNNER = r"""
import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import vm from "node:vm";

const [harnessPath, htmlPath, library] = process.argv.slice(2);
const { pageTexts, textLabels } = await import(pathToFileURL(path.resolve(harnessPath)).href);
const html = readFileSync(htmlPath, "utf-8");

function makeDom() {
  const Node = { ELEMENT_NODE: 1, TEXT_NODE: 3, DOCUMENT_NODE: 9 };
  const NodeFilter = { SHOW_TEXT: 4 };

  class ClassList {
    constructor(owner) {
      this._owner = owner;
    }
    _set() {
      const raw = this._owner._attrs.get("class") || "";
      return new Set(raw.split(/\s+/).filter(Boolean));
    }
    _write(items) {
      this._owner._attrs.set("class", [...items].join(" "));
    }
    add(...names) {
      const items = this._set();
      for (const name of names) if (name) items.add(name);
      this._write(items);
    }
    remove(...names) {
      const items = this._set();
      for (const name of names) items.delete(name);
      this._write(items);
    }
    contains(name) {
      return this._set().has(name);
    }
    [Symbol.iterator]() {
      return this._set()[Symbol.iterator]();
    }
  }

  function makeStyle() {
    const store = new Map();
    return new Proxy(
      {
        setProperty(name, value) {
          store.set(String(name), value == null ? "" : String(value));
        },
        getPropertyValue(name) {
          return store.get(String(name)) || "";
        },
        removeProperty(name) {
          const prev = store.get(String(name)) || "";
          store.delete(String(name));
          return prev;
        },
      },
      {
        get(target, prop) {
          if (prop in target || typeof prop === "symbol") return target[prop];
          const kebab = String(prop).replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
          return store.get(String(prop)) ?? store.get(kebab) ?? "";
        },
        set(target, prop, value) {
          const str = value == null ? "" : String(value);
          store.set(String(prop), str);
          const kebab = String(prop).replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
          store.set(kebab, str);
          return true;
        },
      },
    );
  }

  function matchesPart(el, selector) {
    const trimmed = selector.trim();
    if (!trimmed || el.nodeType !== Node.ELEMENT_NODE) return false;
    if (trimmed === "*") return true;
    const attrMatch = /^\[class\*="([^"]+)"\]$/.exec(trimmed);
    if (attrMatch) return (el.getAttribute("class") || "").includes(attrMatch[1]);
    if (trimmed.startsWith("#")) return el.id === trimmed.slice(1);
    if (trimmed.startsWith(".")) return el.classList.contains(trimmed.slice(1));
    return el.localName === trimmed.toLowerCase();
  }

  function matches(el, selector) {
    return String(selector)
      .split(",")
      .some((part) => {
        const tokens = part.trim().split(/\s+/).filter(Boolean);
        if (!tokens.length) return false;
        let current = el;
        if (!matchesPart(current, tokens[tokens.length - 1])) return false;
        for (let i = tokens.length - 2; i >= 0; i -= 1) {
          current = current.parentElement;
          while (current && !matchesPart(current, tokens[i])) current = current.parentElement;
          if (!current) return false;
        }
        return true;
      });
  }

  class DomText {
    constructor(data, ownerDocument) {
      this.nodeType = Node.TEXT_NODE;
      this.nodeName = "#text";
      this.data = String(data);
      this.childNodes = [];
      this.parentNode = null;
      this.ownerDocument = ownerDocument;
    }
    get parentElement() {
      return this.parentNode && this.parentNode.nodeType === Node.ELEMENT_NODE ? this.parentNode : null;
    }
    get textContent() {
      return this.data;
    }
    set textContent(value) {
      this.data = String(value ?? "");
    }
    cloneNode() {
      return new DomText(this.data, this.ownerDocument);
    }
  }

  class CanvasRenderingContext2D {
    constructor(canvas) {
      this.canvas = canvas;
      this.font = "12px sans-serif";
      this.fillStyle = "#000";
      this.strokeStyle = "#000";
      this.lineWidth = 1;
      this.textAlign = "start";
      this.textBaseline = "alphabetic";
      this.direction = "ltr";
      this.globalAlpha = 1;
      this.globalCompositeOperation = "source-over";
      this._matrix = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
      this._stack = [];
      this._calls = [];
    }
    save() {
      this._stack.push({ ...this._matrix, font: this.font, textAlign: this.textAlign, textBaseline: this.textBaseline });
    }
    restore() {
      const prev = this._stack.pop();
      if (prev) {
        this._matrix = { a: prev.a, b: prev.b, c: prev.c, d: prev.d, e: prev.e, f: prev.f };
        this.font = prev.font;
        this.textAlign = prev.textAlign;
        this.textBaseline = prev.textBaseline;
      }
    }
    getTransform() {
      return { ...this._matrix };
    }
    resetTransform() {
      this._matrix = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
    }
    setTransform(a, b, c, d, e, f) {
      if (typeof a === "object" && a !== null) {
        this._matrix = { a: a.a ?? 1, b: a.b ?? 0, c: a.c ?? 0, d: a.d ?? 1, e: a.e ?? 0, f: a.f ?? 0 };
      } else {
        this._matrix = { a, b, c, d, e, f };
      }
    }
    transform(a, b, c, d, e, f) {
      const m = this._matrix;
      this._matrix = {
        a: m.a * a + m.c * b,
        b: m.b * a + m.d * b,
        c: m.a * c + m.c * d,
        d: m.b * c + m.d * d,
        e: m.a * e + m.c * f + m.e,
        f: m.b * e + m.d * f + m.f,
      };
    }
    translate(x, y) {
      this.transform(1, 0, 0, 1, Number(x) || 0, Number(y) || 0);
    }
    scale(sx, sy) {
      this.transform(Number(sx) || 1, 0, 0, Number(sy) || 1, 0, 0);
    }
    rotate(angle) {
      const cos = Math.cos(Number(angle) || 0);
      const sin = Math.sin(Number(angle) || 0);
      this.transform(cos, sin, -sin, cos, 0, 0);
    }
    clearRect() {}
    fillRect() {}
    strokeRect() {}
    beginPath() {}
    closePath() {}
    moveTo() {}
    lineTo() {}
    bezierCurveTo() {}
    quadraticCurveTo() {}
    arc() {}
    arcTo() {}
    ellipse() {}
    rect() {}
    roundRect() {}
    fill() {}
    stroke() {}
    clip() {}
    setLineDash() {}
    getLineDash() {
      return [];
    }
    isPointInPath() {
      return false;
    }
    isPointInStroke() {
      return false;
    }
    drawImage() {}
    createLinearGradient() {
      return { addColorStop() {} };
    }
    createRadialGradient() {
      return { addColorStop() {} };
    }
    createPattern() {
      return {};
    }
    createImageData(w, h) {
      return { width: w, height: h, data: new Uint8ClampedArray(w * h * 4) };
    }
    getImageData(x, y, w, h) {
      return { width: w, height: h, data: new Uint8ClampedArray(Math.max(1, w * h * 4)) };
    }
    putImageData() {}
    measureText(text) {
      const width = String(text ?? "").length * 7;
      return {
        width,
        actualBoundingBoxLeft: 0,
        actualBoundingBoxRight: width,
        actualBoundingBoxAscent: 10,
        actualBoundingBoxDescent: 3,
        fontBoundingBoxAscent: 10,
        fontBoundingBoxDescent: 3,
      };
    }
    fillText(text, x, y) {
      this._calls.push(["fillText", text, x, y]);
      return "fill-sentinel";
    }
    strokeText(text, x, y) {
      this._calls.push(["strokeText", text, x, y]);
      return "stroke-sentinel";
    }
  }

  class DomElement {
    constructor(localName, ownerDocument, namespaceURI = "http://www.w3.org/1999/xhtml") {
      this.nodeType = Node.ELEMENT_NODE;
      this.localName = String(localName).toLowerCase();
      this.tagName = namespaceURI.includes("svg") ? String(localName) : this.localName.toUpperCase();
      this.nodeName = this.tagName;
      this.namespaceURI = namespaceURI;
      this.ownerDocument = ownerDocument;
      this.parentNode = null;
      this.childNodes = [];
      this._attrs = new Map();
      this.style = makeStyle();
      this.classList = new ClassList(this);
      this._listeners = new Map();
      this._ctx2d = null;
      this._width = this.localName === "canvas" ? 300 : 1600;
      this._height = this.localName === "canvas" ? 150 : 900;
    }
    get parentElement() {
      return this.parentNode && this.parentNode.nodeType === Node.ELEMENT_NODE ? this.parentNode : null;
    }
    get isConnected() {
      let cur = this;
      while (cur.parentNode) cur = cur.parentNode;
      return cur === this.ownerDocument;
    }
    get children() {
      return this.childNodes.filter((n) => n.nodeType === Node.ELEMENT_NODE);
    }
    get firstChild() {
      return this.childNodes[0] || null;
    }
    get lastChild() {
      return this.childNodes[this.childNodes.length - 1] || null;
    }
    get id() {
      return this._attrs.get("id") || "";
    }
    set id(value) {
      this._attrs.set("id", String(value));
    }
    get className() {
      return this._attrs.get("class") || "";
    }
    set className(value) {
      this._attrs.set("class", String(value));
    }
    get width() {
      return this._width;
    }
    set width(value) {
      this._width = Number(value) || 0;
      if (this._ctx2d) this._ctx2d.resetTransform();
    }
    get height() {
      return this._height;
    }
    set height(value) {
      this._height = Number(value) || 0;
      if (this._ctx2d) this._ctx2d.resetTransform();
    }
    get clientWidth() {
      return this.id === "container" ? 1600 : parseFloat(this.style.width) || this._width || 1600;
    }
    get clientHeight() {
      return this.id === "container" ? 900 : parseFloat(this.style.height) || this._height || 900;
    }
    get offsetWidth() {
      return this.clientWidth;
    }
    get offsetHeight() {
      return this.clientHeight;
    }
    get attributes() {
      return [...this._attrs.entries()].map(([name, value]) => ({ name, value }));
    }
    getAttribute(name) {
      return this._attrs.has(name) ? this._attrs.get(name) : null;
    }
    setAttribute(name, value) {
      const str = String(value);
      this._attrs.set(name, str);
      if (name === "width") this._width = Number(value) || this._width;
      if (name === "height") this._height = Number(value) || this._height;
    }
    setAttributeNS(_ns, name, value) {
      this.setAttribute(name, value);
    }
    removeAttribute(name) {
      this._attrs.delete(name);
    }
    hasAttribute(name) {
      return this._attrs.has(name);
    }
    appendChild(child) {
      if (child.parentNode) child.parentNode.removeChild(child);
      child.parentNode = this;
      this.childNodes.push(child);
      return child;
    }
    insertBefore(child, ref) {
      if (!ref) return this.appendChild(child);
      if (child.parentNode) child.parentNode.removeChild(child);
      const idx = this.childNodes.indexOf(ref);
      child.parentNode = this;
      if (idx < 0) this.childNodes.push(child);
      else this.childNodes.splice(idx, 0, child);
      return child;
    }
    removeChild(child) {
      const idx = this.childNodes.indexOf(child);
      if (idx >= 0) {
        this.childNodes.splice(idx, 1);
        child.parentNode = null;
      }
      return child;
    }
    cloneNode(deep = false) {
      const copy = new DomElement(this.localName, this.ownerDocument, this.namespaceURI);
      for (const [k, v] of this._attrs) copy._attrs.set(k, v);
      if (deep) {
        for (const child of this.childNodes) {
          copy.appendChild(
            child.nodeType === Node.TEXT_NODE ? new DomText(child.data, this.ownerDocument) : child.cloneNode(true),
          );
        }
      }
      return copy;
    }
    contains(other) {
      for (let cur = other; cur; cur = cur.parentNode) {
        if (cur === this) return true;
      }
      return false;
    }
    get textContent() {
      return this.childNodes.map((c) => c.textContent).join("");
    }
    set textContent(value) {
      this.childNodes = [];
      const str = String(value ?? "");
      if (str) this.appendChild(new DomText(str, this.ownerDocument));
    }
    get innerHTML() {
      return this.textContent;
    }
    set innerHTML(value) {
      this.textContent = value;
    }
    matches(selector) {
      return matches(this, selector);
    }
    closest(selector) {
      for (let cur = this; cur && cur.nodeType === Node.ELEMENT_NODE; cur = cur.parentElement) {
        if (matches(cur, selector)) return cur;
      }
      return null;
    }
    querySelectorAll(selector) {
      const out = [];
      const walk = (node) => {
        for (const child of node.childNodes) {
          if (child.nodeType === Node.ELEMENT_NODE) {
            if (matches(child, selector)) out.push(child);
            walk(child);
          }
        }
      };
      walk(this);
      return out;
    }
    querySelector(selector) {
      return this.querySelectorAll(selector)[0] || null;
    }
    getElementsByTagName(tag) {
      return this.querySelectorAll(tag === "*" ? "*" : tag);
    }
    getElementsByClassName(cls) {
      return this.querySelectorAll(`.${cls}`);
    }
    addEventListener(type, fn) {
      if (!this._listeners.has(type)) this._listeners.set(type, new Set());
      this._listeners.get(type).add(fn);
    }
    removeEventListener(type, fn) {
      this._listeners.get(type)?.delete(fn);
    }
    getContext(kind) {
      if (this.localName !== "canvas" || kind !== "2d") return null;
      if (!this._ctx2d) this._ctx2d = new CanvasRenderingContext2D(this);
      return this._ctx2d;
    }
    getBoundingClientRect() {
      if (this.id === "container") {
        return { left: 0, top: 0, right: 1600, bottom: 900, width: 1600, height: 900, x: 0, y: 0 };
      }
      if (this.style.opacity === "0" || this.style.visibility === "hidden" || this.style.display === "none") {
        return { left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0, x: 0, y: 0 };
      }
      const x = parseFloat(this.getAttribute("x")) || 20;
      const y = parseFloat(this.getAttribute("y")) || 20;
      const w = parseFloat(this.getAttribute("width")) || 80;
      const h = parseFloat(this.getAttribute("height")) || 20;
      return { left: x, top: y, right: x + w, bottom: y + h, width: w, height: h, x, y };
    }
    getBBox() {
      const len = Math.max(1, this.textContent.length) * 8;
      return { x: 0, y: 0, width: len, height: 16 };
    }
    getComputedTextLength() {
      return Math.max(1, this.textContent.length) * 8;
    }
    createSVGRect() {
      return { x: 0, y: 0, width: 0, height: 0 };
    }
    checkVisibility() {
      return this.style.opacity !== "0" && this.style.visibility !== "hidden" && this.style.display !== "none";
    }
  }

  const document = {
    nodeType: Node.DOCUMENT_NODE,
    parentNode: null,
    childNodes: [],
    defaultView: null,
    documentElement: null,
    head: null,
    body: null,
    implementation: {
      createHTMLDocument() {
        return { body: new DomElement("body", document) };
      },
    },
    fonts: { ready: Promise.resolve() },
    createElement(tag) {
      return new DomElement(tag, document);
    },
    createElementNS(ns, tag) {
      return new DomElement(tag, document, ns || "http://www.w3.org/2000/svg");
    },
    createTextNode(text) {
      return new DomText(text, document);
    },
    createComment() {
      return new DomText("", document);
    },
    createDocumentFragment() {
      return new DomElement("fragment", document);
    },
    getElementById(id) {
      return document.documentElement.querySelectorAll("*").find((el) => el.id === id) || null;
    },
    querySelector(sel) {
      return document.documentElement.querySelector(sel);
    },
    querySelectorAll(sel) {
      return document.documentElement.querySelectorAll(sel);
    },
    addEventListener() {},
    removeEventListener() {},
    createTreeWalker(root, whatToShow) {
      const nodes = [];
      const collect = (node) => {
        for (const child of node.childNodes || []) {
          if (whatToShow === NodeFilter.SHOW_TEXT && child.nodeType === Node.TEXT_NODE) nodes.push(child);
          if (child.childNodes) collect(child);
        }
      };
      collect(root);
      let index = -1;
      return {
        nextNode() {
          index += 1;
          return nodes[index] || null;
        },
      };
    },
  };

  const htmlEl = new DomElement("html", document);
  const headEl = new DomElement("head", document);
  const bodyEl = new DomElement("body", document);
  const container = new DomElement("div", document);
  container.id = "container";
  document.documentElement = htmlEl;
  document.head = headEl;
  document.body = bodyEl;
  document.childNodes = [htmlEl];
  htmlEl.parentNode = document;
  htmlEl.appendChild(headEl);
  htmlEl.appendChild(bodyEl);
  bodyEl.appendChild(container);

  function getComputedStyle(el) {
    const fontSize = el?.style?.fontSize || el?.getAttribute?.("font-size") || "14px";
    return new Proxy(
      {
        fontSize: String(fontSize).endsWith("px") ? String(fontSize) : `${fontSize}px`,
        getPropertyValue(prop) {
          if (prop === "font-size") return String(fontSize);
          return el?.style?.getPropertyValue?.(prop) || "";
        },
      },
      {
        get(target, prop) {
          if (prop in target) return target[prop];
          return el?.style?.[prop] || "";
        },
      },
    );
  }

  class NoopObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }

  const windowObj = {
    document,
    Node,
    NodeFilter,
    Element: DomElement,
    HTMLElement: DomElement,
    SVGElement: DomElement,
    HTMLCanvasElement: DomElement,
    CanvasRenderingContext2D,
    MutationObserver: NoopObserver,
    ResizeObserver: NoopObserver,
    devicePixelRatio: 2,
    innerWidth: 1600,
    innerHeight: 900,
    navigator: { userAgent: "Mozilla/5.0", platform: "Linux x86_64", maxTouchPoints: 0 },
    location: { href: "about:blank", protocol: "about:" },
    performance: { now: () => Date.now() },
    getComputedStyle,
    requestAnimationFrame(cb) {
      return setTimeout(() => cb(Date.now()), 0);
    },
    cancelAnimationFrame(id) {
      clearTimeout(id);
    },
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    addEventListener() {},
    removeEventListener() {},
    matchMedia() {
      return { matches: true, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} };
    },
    console: { ...console },
  };
  windowObj.window = windowObj;
  windowObj.self = windowObj;
  windowObj.top = windowObj;
  windowObj.parent = windowObj;
  windowObj.globalThis = windowObj;
  document.defaultView = windowObj;

  return { windowObj, CanvasRenderingContext2D };
}

const { windowObj, CanvasRenderingContext2D } = makeDom();
const originalFillText = CanvasRenderingContext2D.prototype.fillText;
const originalStrokeText = CanvasRenderingContext2D.prototype.strokeText;
const context = vm.createContext(windowObj);

// Populate `<script type="application/json">` elements (such as `anyplot-data`) before running code scripts.
for (const match of html.matchAll(/<script\s+type="application\/json"\s+id="([^"]+)">([\s\S]*?)<\/script>/gi)) {
  const scriptEl = windowObj.document.createElement("script");
  scriptEl.setAttribute("type", "application/json");
  scriptEl.id = match[1];
  scriptEl.textContent = match[2];
  windowObj.document.body.appendChild(scriptEl);
}

for (const match of html.matchAll(/<script(?:\s+[^>]*)?>([\s\S]*?)<\/script>/gi)) {
  if (/type="application\/json"/i.test(match[0])) continue;
  vm.runInContext(match[1], context);
}

const fillTextWrapped = CanvasRenderingContext2D.prototype.fillText !== originalFillText;
const strokeTextWrapped = CanvasRenderingContext2D.prototype.strokeText !== originalStrokeText;
const hasCanvasTextsHook = typeof context.__anyplotCanvasTexts === "function";
const raw = vm.runInContext(`(${pageTexts.toString()})(${JSON.stringify([library, 2000])})`, context);
const probe = textLabels(raw);

process.stdout.write(
  JSON.stringify({
    fillTextWrapped,
    strokeTextWrapped,
    hasCanvasTextsHook,
    pageError: context.__anyplotError ?? null,
    probeResult: context.__testResult ?? null,
    probe,
  }),
);
"""


def _node_modules() -> Path | None:
    root = Path(os.environ.get("ANYPLOT_NODE_MODULES", REPO_ROOT / "node_modules"))
    needed = (
        "chart.js/dist/chart.umd.js",
        "echarts/dist/echarts.min.js",
        "highcharts/highcharts.js",
        "playwright/package.json",
        "esbuild/package.json",
    )
    return root if all((root / name).is_file() for name in needed) else None


@dataclass
class NodeProbeRun:
    fill_text_wrapped: bool
    stroke_text_wrapped: bool
    has_canvas_texts_hook: bool
    page_error: str | None
    probe_result: object
    labels: list[tuple[str, str]]
    labels_truncated: bool
    html: str


def run_node_probe(tmp_path: Path, source: str, *, library: str = "chartjs", sandbox: bool = True) -> NodeProbeRun:
    """Build `plot-light.html` with `render.mjs`, execute its scripts in Node, and read `pageTexts` + `textLabels`."""
    node = shutil.which("node")
    modules = _node_modules()
    if node is None or modules is None:
        pytest.skip("needs node on PATH and the lock's node_modules")

    work = tmp_path / "work"
    work.mkdir(parents=True, exist_ok=True)
    (work / "plot.js").write_text(source, encoding="utf-8")

    env = {key: value for key, value in os.environ.items() if not key.startswith("ANYPLOT_")}
    env["ANYPLOT_THEME"] = "light"
    env["ANYPLOT_NODE_MODULES"] = str(modules)
    env |= NO_BROWSER
    if sandbox:
        env["ANYPLOT_SANDBOX"] = "1"
        env["ANYPLOT_PAGE_ONLY"] = "1"

    built = subprocess.run(
        [node, str(HARNESS), f"--library={library}", "plot.js"],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    html_file = work / "plot-light.html"
    if sandbox:
        assert built.returncode == 0, built.stderr
    assert html_file.is_file(), built.stderr

    runner = tmp_path / "node_page_runner.mjs"
    runner.write_text(NODE_PAGE_RUNNER, encoding="utf-8")
    evaluated = subprocess.run(
        [node, str(runner), str(HARNESS), str(html_file), library],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert evaluated.returncode == 0, evaluated.stderr
    payload = json.loads(evaluated.stdout)
    assert payload["pageError"] is None, payload["pageError"]
    probe = payload["probe"]
    labels = [(item["kind"], item["text"]) for item in probe["labels"]]
    return NodeProbeRun(
        fill_text_wrapped=payload["fillTextWrapped"],
        stroke_text_wrapped=payload["strokeTextWrapped"],
        has_canvas_texts_hook=payload["hasCanvasTextsHook"],
        page_error=payload["pageError"],
        probe_result=payload["probeResult"],
        labels=labels,
        labels_truncated=probe["labels_truncated"],
        html=html_file.read_text(encoding="utf-8"),
    )


# --- Shared Chart.js, ECharts, and Highcharts figures for both test layers ----------------------

BAR_WITH_FOUR_POINT_ZERO = (
    CANVAS
    + """
const valuePlugin = {
  id: "valueLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const bar = chart.getDatasetMeta(0).data[1];
    ctx.save();
    ctx.fillText("4.0", bar.x, bar.y - 8);
    ctx.restore();
  },
};
new Chart(canvas, {
  type: "bar",
  plugins: [valuePlugin],
  data: {
    labels: ["Bern", "Zürich"],
    datasets: [{ label: "Schweizer", data: [2.0, 4.0] }],
  },
  options: {
    animation: false,
    plugins: { title: { display: true, text: "Bevölkerung" }, legend: { display: true } },
    scales: {
      y: {
        min: 0,
        max: 4,
        title: { display: true, text: "Personen" },
        ticks: { stepSize: 2, callback: (v) => Number(v).toFixed(1) },
      },
    },
  },
});
"""
)

CHART_THAT_REDRAWS = (
    CANVAS
    + """
const topNote = {
  id: "topNote",
  afterDatasetsDraw(chart) {
    const bar = chart.getDatasetMeta(0).data[0];
    chart.ctx.fillText("Peak 18", bar.x, bar.y - 6);
  },
};
const chart = new Chart(canvas, {
  type: "bar",
  plugins: [topNote],
  data: {
    labels: ["Q1", "Q2"],
    datasets: [{ label: "Revenue", data: [18, 12] }],
  },
  options: {
    animation: false,
    plugins: { title: { display: true, text: "Quarterly Sales" }, legend: { display: true } },
    scales: { y: { min: 0, max: 20, ticks: { stepSize: 10 }, title: { display: true, text: "USD" } } },
  },
});
chart.update();
chart.resize(1200, 700);
chart.update();
"""
)

DOUGHNUT_WITH_CENTER_NUMBER = (
    CANVAS
    + """
const centerNumber = {
  id: "centerNumber",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    ctx.fillText("128", cx, cy);
    ctx.strokeText("62%", cx + 40, cy);
    ctx.fillText("62%", cx + 40, cy);
    ctx.restore();
  },
};
new Chart(canvas, {
  type: "doughnut",
  plugins: [centerNumber],
  data: {
    labels: ["Solar", "Wind"],
    datasets: [{ data: [80, 48] }],
  },
  options: {
    animation: false,
    plugins: { title: { display: true, text: "Output" }, legend: { display: true } },
  },
});
"""
)

EXISTING_MODEL_ONLY_CHART = (
    CANVAS + "new Chart(canvas, { type: 'bar', options: { animation: false, plugins: {"
    " title: { display: true, text: 'Bevölkerung' }, legend: { display: true } },"
    " scales: { y: { min: 0, max: 2, ticks: { stepSize: 1 }, title: { display: true, text: 'Personen' } } } },"
    " data: { labels: ['Bern', 'Zürich'], datasets: [{ label: 'Schweizer', data: [1, 2] }] } });\n"
)

OVER_LABEL_LIMIT_CHART = (
    CANVAS
    + """
const manyLabels = {
  id: "manyLabels",
  afterDraw(chart) {
    chart.ctx.fillText("L".repeat(240), 20, 20);
    for (let i = 0; i < 450; i += 1) {
      chart.ctx.fillText(`Note ${i}`, 30, 30 + (i % 200));
    }
  },
};
new Chart(canvas, {
  type: "bar",
  plugins: [manyLabels],
  data: { labels: ["A"], datasets: [{ label: "Series", data: [1] }] },
  options: { animation: false, plugins: { legend: { display: false } } },
});
"""
)

ECHARTS_FIGURE = """
const chart = echarts.init(document.getElementById("container"), null, { renderer: "svg" });
chart.setOption({
  animation: false,
  title: { text: "Umsatz", subtext: "in CHF" },
  legend: {},
  xAxis: { type: "category", name: "Filiale", data: ["Bern", "Zug"] },
  yAxis: { type: "value" },
  series: [{ type: "bar", name: "Nord", data: [3, 5], label: { show: true } }],
});
"""

HIGHCHARTS_FIGURE = """
Highcharts.chart("container", {
  chart: { type: "column", animation: false },
  credits: { enabled: false },
  title: { text: "Umsatz" },
  xAxis: { categories: ["Bern", "Zug"], title: { text: "Filiale" } },
  yAxis: { title: { text: "CHF" } },
  plotOptions: {
    series: { animation: false, dataLabels: { enabled: true, style: { textOutline: "1px contrast" } } },
  },
  series: [{ name: "Nord", data: [3, 5] }],
});
"""


class TestInNode:
    """Runs `render.mjs`'s page builder, Chart.js canvas wrapper, `pageTexts`, and `textLabels` in Node."""

    def test_a_plugin_value_matching_a_tick_keeps_one_annotation_beside_the_tick(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, BAR_WITH_FOUR_POINT_ZERO)

        assert run.fill_text_wrapped is True and run.stroke_text_wrapped is True
        assert run.labels[:3] == [("title", "Bevölkerung"), ("y axis label", "Personen"), ("legend text", "Schweizer")]
        assert run.labels.count(("y tick label", "4.0")) == 1
        assert run.labels.count(("annotation", "4.0")) == 1
        assert ("y tick label", "2.0") in run.labels and ("annotation", "2.0") not in run.labels
        assert run.labels_truncated is True

    def test_a_chart_that_redraws_reports_no_text_twice(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, CHART_THAT_REDRAWS)

        assert ("title", "Quarterly Sales") in run.labels
        assert ("y axis label", "USD") in run.labels
        assert ("legend text", "Revenue") in run.labels
        assert ("annotation", "Peak 18") in run.labels
        for entry in set(run.labels):
            assert run.labels.count(entry) == 1, (entry, run.labels)

    def test_a_doughnut_center_number_is_reported_as_an_annotation(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, DOUGHNUT_WITH_CENTER_NUMBER)

        assert ("title", "Output") in run.labels
        assert {("legend text", "Solar"), ("legend text", "Wind")} <= set(run.labels)
        assert run.labels.count(("annotation", "128")) == 1
        assert run.labels.count(("annotation", "62%")) == 1
        assert run.labels_truncated is True

    def test_a_chart_without_plugin_drawing_keeps_its_model_labels_and_order(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, EXISTING_MODEL_ONLY_CHART)

        expected = [
            ("title", "Bevölkerung"),
            ("y axis label", "Personen"),
            ("legend text", "Schweizer"),
            ("y tick label", "0"),
            ("y tick label", "1"),
            ("y tick label", "2"),
            ("x tick label", "Bern"),
            ("x tick label", "Zürich"),
        ]
        assert run.labels == expected
        assert not any(kind == "annotation" for kind, _ in run.labels)
        assert run.labels_truncated is True

        # A dataset without `label` leaves `legendItem.text` undefined; no `"undefined"` annotation appears.
        unnamed = run_node_probe(
            tmp_path / "unnamed",
            CANVAS + "new Chart(canvas, { type: 'bar', options: { animation: false },"
            " data: { labels: ['a', 'b'], datasets: [{ data: [1, 2] }] } });\n",
        )
        assert not any(kind == "annotation" for kind, _ in unnamed.labels)

    def test_without_sandbox_mode_filltext_is_not_wrapped(self, tmp_path: Path) -> None:
        import re

        smoke = (REPO_ROOT / "agents" / "renderer" / "toolchain" / "smoke.js").read_text(encoding="utf-8")
        run = run_node_probe(tmp_path, smoke, sandbox=False)

        assert run.fill_text_wrapped is False and run.stroke_text_wrapped is False
        assert run.has_canvas_texts_hook is False
        assert "__anyplotCanvasTexts" not in run.html
        modules = _node_modules()
        assert modules is not None
        bundle = (modules / "chart.js" / "dist" / "chart.umd.js").read_text(encoding="utf-8")
        template = (REPO_ROOT / "tests" / "unit" / "automation" / "fixtures" / "js-render-page-light.html").read_text(
            encoding="utf-8"
        )
        expected = template.replace("{{SNIPPET}}", smoke).replace(
            "{{BUNDLE}}", re.sub("</script", lambda _: "<\\/script", bundle, flags=re.IGNORECASE)
        )
        assert run.html.encode("utf-8") == expected.encode("utf-8")

    def test_more_recorded_texts_than_label_limit_cap_the_probe_and_set_truncated(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, OVER_LABEL_LIMIT_CHART)

        assert len(run.labels) == 400
        assert run.labels[0] == ("annotation", "L" * 200)
        assert run.labels[1] == ("annotation", "Note 0")
        assert run.labels_truncated is True

    def test_echarts_and_highcharts_probes_are_unchanged_and_do_not_wrap_filltext(self, tmp_path: Path) -> None:
        for renderer in ("canvas", "svg"):
            figure = ECHARTS_FIGURE.replace('"svg"', f'"{renderer}"')
            echarts_run = run_node_probe(tmp_path / f"echarts-{renderer}", figure, library="echarts")
            assert echarts_run.fill_text_wrapped is False and echarts_run.has_canvas_texts_hook is False
            assert {
                ("title", "Umsatz"),
                ("subtitle", "in CHF"),
                ("x axis label", "Filiale"),
                ("legend text", "Nord"),
                ("x tick label", "Zug"),
                ("annotation", "5"),
            } <= set(echarts_run.labels)
            assert echarts_run.labels_truncated is False

        highcharts_run = run_node_probe(tmp_path / "highcharts", HIGHCHARTS_FIGURE, library="highcharts")
        assert highcharts_run.fill_text_wrapped is False and highcharts_run.has_canvas_texts_hook is False
        assert {
            ("title", "Umsatz"),
            ("x axis label", "Filiale"),
            ("y axis label", "CHF"),
            ("legend text", "Nord"),
            ("x tick label", "Zug"),
            ("annotation", "5"),
        } <= set(highcharts_run.labels)
        assert highcharts_run.labels.count(("annotation", "5")) == 1
        assert highcharts_run.labels_truncated is False

    def test_the_wrapper_swallows_recording_errors_and_returns_the_originals_result(self, tmp_path: Path) -> None:
        source = (
            CANVAS
            + """
const ctx = canvas.getContext("2d");
const bad = { toString() { throw new Error("unprintable"); } };
const fillReturn = ctx.fillText("Recorded note", 15, 25);
const strokeReturn = ctx.strokeText(bad, 15, 45);
window.__testResult = { fillReturn, strokeReturn, calls: ctx._calls.length };
new Chart(canvas, {
  type: "bar",
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
canvas.getContext("2d").fillText("After chart", 30, 30);
"""
        )
        run = run_node_probe(tmp_path, source)

        assert run.probe_result == {"fillReturn": "fill-sentinel", "strokeReturn": "stroke-sentinel", "calls": 2}
        assert ("annotation", "After chart") in run.labels
        assert ("annotation", "Recorded note") not in run.labels  # wiped by `new Chart`'s complete draw on `canvas`

    def test_two_charts_and_an_incomplete_draw_keep_each_charts_last_complete_draw(self, tmp_path: Path) -> None:
        source = """
const container = document.getElementById("container");
const first = document.createElement("canvas");
const second = document.createElement("canvas");
const offscreen = document.createElement("canvas");
container.appendChild(first);
container.appendChild(second);
offscreen.getContext("2d").fillText("Offscreen scratch", 10, 10);

let cancelFirst = false;
const firstChart = new Chart(first, {
  type: "bar",
  plugins: [{
    id: "p1",
    beforeDraw() { return !cancelFirst; },
    afterDraw(c) { c.ctx.fillText("First badge", 20, 20); },
  }],
  data: { labels: ["A"], datasets: [{ label: "One", data: [1] }] },
  options: { animation: false },
});
const secondChart = new Chart(second, {
  type: "bar",
  plugins: [{ id: "p2", afterDraw(c) { c.ctx.fillText("Second badge", 20, 20); } }],
  data: { labels: ["B"], datasets: [{ label: "Two", data: [2] }] },
  options: { animation: false },
});
secondChart.update();
cancelFirst = true;
firstChart.draw();
"""
        run = run_node_probe(tmp_path, source)

        assert run.labels.count(("annotation", "First badge")) == 1
        assert run.labels.count(("annotation", "Second badge")) == 1
        assert ("annotation", "Offscreen scratch") not in run.labels

    def test_destroyed_chart_and_skipped_canvas_calls_leave_no_stale_annotations(self, tmp_path: Path) -> None:
        source = """
const container = document.getElementById("container");
const wiped = document.createElement("canvas");
const kept = document.createElement("canvas");
container.appendChild(wiped);
container.appendChild(kept);

const draft = new Chart(wiped, {
  type: "bar",
  plugins: [{ id: "p0", afterDraw(c) { c.ctx.fillText("Draft note", 20, 20); } }],
  data: { labels: ["OldX"], datasets: [{ label: "OldSeries", data: [9] }] },
  options: { animation: false, plugins: { title: { display: true, text: "Draft title" } } },
});
draft.destroy();

new Chart(kept, {
  type: "bar",
  plugins: [{
    id: "p1",
    afterDraw(c) {
      c.ctx.fillText("NaN x", NaN, 20);
      c.ctx.fillText("Inf y", 20, Infinity);
      c.ctx.fillText("Zero maxWidth", 20, 20, 0);
      c.ctx.fillText("Neg maxWidth", 20, 20, -5);
      c.ctx.fillText("Valid width", 20, 40, 120);
    },
  }],
  data: { labels: ["KeptX"], datasets: [{ label: "KeptSeries", data: [4] }] },
  options: { animation: false },
});
"""
        run = run_node_probe(tmp_path, source)

        assert ("annotation", "Valid width") in run.labels
        for ghost in ("Draft note", "Draft title", "OldX", "OldSeries", "NaN x", "Inf y", "Zero maxWidth", "Neg maxWidth"):
            assert not any(text == ghost for _, text in run.labels), (ghost, run.labels)


# --- Full Playwright + Chromium harness tests (run where Playwright's browser is installed) -----


@dataclass
class BrowserRun:
    returncode: int
    stdout: str
    stderr: str
    work: Path

    def probe(self) -> tuple[list[tuple[str, str]], bool]:
        data = json.loads((self.work / "probe-light.json").read_text(encoding="utf-8"))
        assert set(data) == {"labels", "labels_truncated"}
        return [(item["kind"], item["text"]) for item in data["labels"]], data["labels_truncated"]


@dataclass
class BrowserHarness:
    root: Path
    node: str
    allowlist: Path

    def render(self, tmp_path: Path, source: str, *, library: str = "chartjs", sandbox: bool = True) -> BrowserRun:
        work = tmp_path / "work"
        work.mkdir(parents=True, exist_ok=True)
        (work / "plot.js").write_text(source, encoding="utf-8")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("ANYPLOT_")}
        environment["ANYPLOT_THEME"] = "light"
        if sandbox:
            environment |= {
                "ANYPLOT_SANDBOX": "1",
                "ANYPLOT_NO_HTML": "1",
                "ANYPLOT_NODE_MODULES": str(self.root / "node_modules"),
                "ANYPLOT_IMPORT_ALLOWLIST": str(self.allowlist),
            }
        done = subprocess.run(
            [self.node, str(self.root / "automation" / "js-render" / "render.mjs"), f"--library={library}", "plot.js"],
            cwd=work,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return BrowserRun(done.returncode, done.stdout, done.stderr, work)


@pytest.fixture(scope="module")
def browser_harness(tmp_path_factory: pytest.TempPathFactory) -> BrowserHarness:
    node = shutil.which("node")
    modules = _node_modules()
    if node is None or modules is None:
        pytest.skip("needs node on PATH and the lock's node_modules (npm ci, or ANYPLOT_NODE_MODULES)")
    root = tmp_path_factory.mktemp("checkout")
    (root / "automation" / "js-render").mkdir(parents=True)
    shutil.copy(HARNESS, root / "automation" / "js-render" / "render.mjs")
    (root / "node_modules").symlink_to(modules.resolve(), target_is_directory=True)
    spec = importlib.util.spec_from_file_location("import_allowlist", ALLOWLIST_BUILDER)
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    allowlist = root / "import-allowlist.json"
    allowlist.write_text(json.dumps(builder.allowlist(modules)), encoding="utf-8")
    probe = BrowserHarness(root, node, allowlist).render(tmp_path_factory.mktemp("probe"), CANVAS, sandbox=False)
    if probe.returncode != 0:
        pytest.skip(f"the harness cannot render here (no browser?): {probe.stderr.strip()[-300:]}")
    return BrowserHarness(root, node, allowlist)


class TestInChromium:
    """The same acceptance checks end to end under headless Chromium when Playwright's browser is installed."""

    def test_bar_plugin_four_point_zero_beside_tick(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, BAR_WITH_FOUR_POINT_ZERO)
        assert run.returncode == 0, run.stderr
        labels, truncated = run.probe()
        assert labels[:3] == [("title", "Bevölkerung"), ("y axis label", "Personen"), ("legend text", "Schweizer")]
        assert labels.count(("y tick label", "4.0")) == 1 and labels.count(("annotation", "4.0")) == 1
        assert truncated is True

    def test_redraw_reports_no_text_twice(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, CHART_THAT_REDRAWS)
        assert run.returncode == 0, run.stderr
        labels, _ = run.probe()
        assert ("annotation", "Peak 18") in labels
        for entry in set(labels):
            assert labels.count(entry) == 1

    def test_doughnut_center_number_annotation(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, DOUGHNUT_WITH_CENTER_NUMBER)
        assert run.returncode == 0, run.stderr
        labels, truncated = run.probe()
        assert labels.count(("annotation", "128")) == 1 and labels.count(("annotation", "62%")) == 1
        assert truncated is True

    def test_model_only_chart_unchanged(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, EXISTING_MODEL_ONLY_CHART)
        assert run.returncode == 0, run.stderr
        labels, truncated = run.probe()
        assert labels[:3] == [("title", "Bevölkerung"), ("y axis label", "Personen"), ("legend text", "Schweizer")]
        assert not any(kind == "annotation" for kind, _ in labels) and truncated is True

    def test_without_sandbox_filltext_is_not_wrapped(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        check = (
            CANVAS + 'if (!CanvasRenderingContext2D.prototype.fillText.toString().includes("[native code]")) '
            'throw new Error("fillText wrapped outside sandbox");\n'
        )
        run = browser_harness.render(tmp_path, check, sandbox=False)
        assert run.returncode == 0, run.stderr
        assert not (run.work / "probe-light.json").exists()

    def test_label_limit_caps_recorded_texts(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, OVER_LABEL_LIMIT_CHART)
        assert run.returncode == 0, run.stderr
        labels, truncated = run.probe()
        assert len(labels) == 400 and truncated is True

    def test_echarts_and_highcharts_probes_unchanged(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        ec = browser_harness.render(tmp_path / "ec", ECHARTS_FIGURE, library="echarts")
        hc = browser_harness.render(tmp_path / "hc", HIGHCHARTS_FIGURE, library="highcharts")
        assert ec.returncode == 0 and hc.returncode == 0, ec.stderr + hc.stderr
        ec_labels, ec_truncated = ec.probe()
        hc_labels, hc_truncated = hc.probe()
        assert {("title", "Umsatz"), ("subtitle", "in CHF"), ("annotation", "5")} <= set(ec_labels)
        assert {("title", "Umsatz"), ("y axis label", "CHF"), ("annotation", "5")} <= set(hc_labels)
        assert ec_truncated is False and hc_truncated is False
