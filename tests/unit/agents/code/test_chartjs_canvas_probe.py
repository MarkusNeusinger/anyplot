"""The Chart.js 2D canvas text recorder in `automation/js-render/render.mjs` (sandbox mode).

Two layers exercise the same acceptance figures against `automation/js-render/render.mjs`:

1. `TestInNode` runs the real `automation/js-render/render.mjs` CLI end to end (with a `node:vm` Playwright stub on
   render runs and `NO_BROWSER` on `ANYPLOT_PAGE_ONLY=1`), checking both the `plot-light.html` page written to disk,
   the in-memory page handed to `page.setContent(...)`, and the `probe-light.json` report written by `writeTextProbe`
   against the pinned library bundles in `node_modules/` (`chart.js`, `echarts`, `highcharts`). It needs only `node`
   and `node_modules/`, so every acceptance case and mutation check runs without a browser binary.
2. `TestInChromium` runs the full Playwright Chromium render (`plot-light.png` + `probe-light.json`) wherever
   Playwright's browser is installed (as in CI) and skips cleanly with the harness's skip message otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
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

# Minimal DOM + 2D canvas realm in `node:vm` so `render.mjs`'s inline scripts and `page.evaluate(...)` calls execute
# against the real `chart.js`, `echarts`, and `highcharts` UMD bundles without a Chromium binary.
MAKE_DOM_MJS = r"""
import vm from "node:vm";

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
      this._stack.push({
        ...this._matrix,
        font: this.font,
        fillStyle: this.fillStyle,
        strokeStyle: this.strokeStyle,
        lineWidth: this.lineWidth,
        globalAlpha: this.globalAlpha,
        textAlign: this.textAlign,
        textBaseline: this.textBaseline,
      });
    }
    restore() {
      const prev = this._stack.pop();
      if (prev) {
        this._matrix = { a: prev.a, b: prev.b, c: prev.c, d: prev.d, e: prev.e, f: prev.f };
        this.font = prev.font;
        this.fillStyle = prev.fillStyle;
        this.strokeStyle = prev.strokeStyle;
        this.lineWidth = prev.lineWidth;
        this.globalAlpha = prev.globalAlpha;
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
      if (name === "width") this.width = value;
      if (name === "height") this.height = value;
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

export function runHtmlInVm(html) {
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

  let thrownError = null;
  for (const match of html.matchAll(/<script(?:\s+[^>]*)?>([\s\S]*?)<\/script>/gi)) {
    if (/type="application\/json"/i.test(match[0])) continue;
    try {
      vm.runInContext(match[1], context);
    } catch (err) {
      if (thrownError === null) thrownError = err;
    }
  }

  return {
    context,
    CanvasRenderingContext2D,
    originalFillText,
    originalStrokeText,
    thrownError,
    fillTextWrapped: CanvasRenderingContext2D.prototype.fillText !== originalFillText,
    strokeTextWrapped: CanvasRenderingContext2D.prototype.strokeText !== originalStrokeText,
    hasCanvasTextsHook: typeof context.__anyplotCanvasTexts === "function",
    pageError: context.__anyplotError ?? null,
    probeResult: context.__testResult ?? null,
  };
}
"""

# Preloaded with `node --import=...` on render runs in `TestInNode`: intercepts `chromium.launch` so `render.mjs`'s
# `main()` runs end to end, capturing the exact HTML passed to `page.setContent(...)` while letting `render.mjs` write
# both `plot-light.html` and `probe-light.json` itself.
PLAYWRIGHT_VM_PRELOAD = r"""
import { writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import vm from "node:vm";
import { runHtmlInVm } from "./make_dom.mjs";

const MIN_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIAAAUAAeImBZsAAAAASUVORK5CYII=",
  "base64",
);
const requireFromHarness = createRequire(path.resolve(process.argv[1]));
const { chromium } = requireFromHarness("playwright");

chromium.launch = async function () {
  let loadedHtml = null;
  let current = null;
  const listeners = new Map();
  const pageContext = {
    async route() {},
    async routeWebSocket() {},
    async addInitScript() {},
  };
  const page = {
    context() {
      return pageContext;
    },
    on(event, fn) {
      if (!listeners.has(event)) listeners.set(event, []);
      listeners.get(event).push(fn);
    },
    async emulateMedia() {},
    async setContent(html) {
      loadedHtml = html;
      current = runHtmlInVm(html);
      if (current.thrownError) {
        for (const fn of listeners.get("pageerror") || []) fn(current.thrownError);
      }
    },
    async waitForFunction(fn, arg) {
      const expr =
        typeof fn === "function"
          ? arg === undefined
            ? `(${fn.toString()})()`
            : `(${fn.toString()})(${JSON.stringify(arg)})`
          : String(fn);
      if (!vm.runInContext(expr, current.context)) throw new Error("waitForFunction timed out");
    },
    async evaluate(fn, arg) {
      const expr = arg === undefined ? `(${fn.toString()})()` : `(${fn.toString()})(${JSON.stringify(arg)})`;
      return await vm.runInContext(expr, current.context);
    },
    locator() {
      return {
        async screenshot(opts) {
          if (opts && opts.path) writeFileSync(opts.path, MIN_PNG);
          return MIN_PNG;
        },
      };
    },
  };
  return {
    async newPage() {
      return page;
    },
    async close() {
      writeFileSync(
        path.resolve(process.cwd(), "vm-state.json"),
        JSON.stringify({
          launched: true,
          loadedHtml,
          fillTextWrapped: current ? current.fillTextWrapped : false,
          strokeTextWrapped: current ? current.strokeTextWrapped : false,
          hasCanvasTextsHook: current ? current.hasCanvasTextsHook : false,
          pageError: current ? current.pageError : null,
          probeResult: current ? current.probeResult : null,
        }),
        "utf-8",
      );
    },
  };
};
"""

# Evaluates a written `plot-light.html` file directly in `node:vm` to verify what opening the saved file in a browser
# does (for example, that neither `ANYPLOT_PAGE_ONLY=1` nor a render run's written `plot-light.html` wraps `fillText`).
EVALUATE_HTML_MJS = r"""
import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import vm from "node:vm";
import { runHtmlInVm } from "./make_dom.mjs";

const [harnessPath, htmlPath, library] = process.argv.slice(2);
const { pageTexts, textLabels } = await import(pathToFileURL(path.resolve(harnessPath)).href);
const html = readFileSync(htmlPath, "utf-8");
const current = runHtmlInVm(html);
const raw = vm.runInContext(`(${pageTexts.toString()})(${JSON.stringify([library, 2000])})`, current.context);
const probe = textLabels(raw);

process.stdout.write(
  JSON.stringify({
    fillTextWrapped: current.fillTextWrapped,
    strokeTextWrapped: current.strokeTextWrapped,
    hasCanvasTextsHook: current.hasCanvasTextsHook,
    pageError: current.pageError,
    probeResult: current.probeResult,
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
    returncode: int
    browser_launched: bool
    fill_text_wrapped: bool
    stroke_text_wrapped: bool
    has_canvas_texts_hook: bool
    page_error: str | None
    probe_result: object
    labels: list[tuple[str, str]]
    labels_truncated: bool
    written_html: str
    loaded_html: str | None


def evaluate_written_html(tmp_path: Path, html_file: Path, *, library: str = "chartjs") -> dict[str, object]:
    """Execute a written `plot-*.html` file in a fresh `node:vm` page context and return its wrapper/probe state."""
    node = shutil.which("node")
    modules = _node_modules()
    if node is None or modules is None:
        pytest.skip("needs node on PATH and the lock's node_modules")
    eval_dir = tmp_path / "html-eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / "make_dom.mjs").write_text(MAKE_DOM_MJS, encoding="utf-8")
    runner = eval_dir / "evaluate_html.mjs"
    runner.write_text(EVALUATE_HTML_MJS, encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if not key.startswith("ANYPLOT_")}
    env["ANYPLOT_NODE_MODULES"] = str(modules)
    evaluated = subprocess.run(
        [node, str(runner), str(HARNESS), str(html_file), library],
        cwd=eval_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert evaluated.returncode == 0, evaluated.stderr
    payload: dict[str, object] = json.loads(evaluated.stdout)
    assert payload["pageError"] is None, payload["pageError"]
    return payload


def run_node_probe(
    tmp_path: Path,
    source: str,
    *,
    library: str = "chartjs",
    sandbox: bool = True,
    page_only: bool = False,
    data_json: str | None = None,
) -> NodeProbeRun:
    """Run `render.mjs` in Node (`--import` VM browser stub for render runs, `NO_BROWSER` for `page_only`)."""
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
    if page_only:
        env["ANYPLOT_PAGE_ONLY"] = "1"
    if data_json is not None:
        (work / "data.json").write_text(data_json, encoding="utf-8")
        env["ANYPLOT_DATA_JSON"] = "data.json"

    html_file = work / "plot-light.html"
    probe_file = work / "probe-light.json"

    if page_only:
        built = subprocess.run(
            [node, str(HARNESS), f"--library={library}", "plot.js"],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert built.returncode == 0, built.stderr
        assert html_file.is_file(), built.stderr
        assert not probe_file.exists()
        payload = evaluate_written_html(tmp_path, html_file, library=library)
        probe = payload["probe"]
        assert isinstance(probe, dict)
        raw_labels = probe["labels"]
        assert isinstance(raw_labels, list)
        return NodeProbeRun(
            returncode=built.returncode,
            browser_launched=False,
            fill_text_wrapped=bool(payload["fillTextWrapped"]),
            stroke_text_wrapped=bool(payload["strokeTextWrapped"]),
            has_canvas_texts_hook=bool(payload["hasCanvasTextsHook"]),
            page_error=None,
            probe_result=payload["probeResult"],
            labels=[(str(item["kind"]), str(item["text"])) for item in raw_labels],
            labels_truncated=bool(probe["labels_truncated"]),
            written_html=html_file.read_text(encoding="utf-8"),
            loaded_html=None,
        )

    preload_dir = tmp_path / "preload"
    preload_dir.mkdir(parents=True, exist_ok=True)
    (preload_dir / "make_dom.mjs").write_text(MAKE_DOM_MJS, encoding="utf-8")
    preload = preload_dir / "playwright_vm_preload.mjs"
    preload.write_text(PLAYWRIGHT_VM_PRELOAD, encoding="utf-8")

    built = subprocess.run(
        [node, f"--import={preload.as_uri()}", str(HARNESS), f"--library={library}", "plot.js"],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    assert html_file.is_file(), built.stderr
    vm_state = json.loads((work / "vm-state.json").read_text(encoding="utf-8"))
    assert vm_state["pageError"] is None, vm_state["pageError"]

    if sandbox:
        assert probe_file.is_file(), built.stderr
        probe_data = json.loads(probe_file.read_text(encoding="utf-8"))
        labels = [(str(item["kind"]), str(item["text"])) for item in probe_data["labels"]]
        labels_truncated = bool(probe_data["labels_truncated"])
    else:
        assert not probe_file.exists()
        labels = []
        labels_truncated = False

    return NodeProbeRun(
        returncode=built.returncode,
        browser_launched=bool(vm_state["launched"]),
        fill_text_wrapped=bool(vm_state["fillTextWrapped"]),
        stroke_text_wrapped=bool(vm_state["strokeTextWrapped"]),
        has_canvas_texts_hook=bool(vm_state["hasCanvasTextsHook"]),
        page_error=vm_state["pageError"],
        probe_result=vm_state["probeResult"],
        labels=labels,
        labels_truncated=labels_truncated,
        written_html=html_file.read_text(encoding="utf-8"),
        loaded_html=vm_state["loadedHtml"],
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

EXPECTED_MODEL_ONLY_LABELS = [
    ("title", "Bevölkerung"),
    ("y axis label", "Personen"),
    ("legend text", "Schweizer"),
    ("y tick label", "0"),
    ("y tick label", "1"),
    ("y tick label", "2"),
    ("x tick label", "Bern"),
    ("x tick label", "Zürich"),
]

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
  options: {
    animation: false,
    plugins: { title: { display: true, text: "Many Notes" }, legend: { display: false } },
    scales: { y: { min: 0, max: 2, ticks: { stepSize: 1 }, title: { display: true, text: "Count" } } },
  },
});
"""
)

NON_CHART_CANVAS_OVER_LIMIT = (
    CANVAS
    + """
const extra = document.createElement("canvas");
extra.width = 400;
extra.height = 300;
document.getElementById("container").appendChild(extra);
const extraCtx = extra.getContext("2d");
for (let i = 0; i < 450; i += 1) {
  extraCtx.fillText(`Extra ${i}`, 20, 20 + (i % 200));
}
new Chart(canvas, {
  type: "bar",
  data: { labels: ["A"], datasets: [{ label: "Series", data: [1] }] },
  options: {
    animation: false,
    plugins: { title: { display: true, text: "Main Chart" }, legend: { display: false } },
    scales: { y: { min: 0, max: 2, ticks: { stepSize: 1 }, title: { display: true, text: "Count" } } },
  },
});
"""
)

TRANSPARENT_STYLES_CHART = (
    CANVAS
    + """
new Chart(canvas, {
  type: "bar",
  plugins: [{
    id: "transparentStyles",
    afterDraw(chart) {
      const ctx = chart.ctx;
      const zeroColors = [
        ["rgba(0,0,0,0)", "rgba zero"],
        ["rgba(255, 100, 50, 0.0)", "rgba float zero"],
        ["rgba(10, 20, 30, 0%)", "rgba pct zero"],
        ["rgb(0, 0, 0, 0)", "rgb comma zero"],
        ["transparent", "transparent keyword"],
        ["TRANSPARENT", "transparent upper"],
        ["#0000", "hex4 zero"],
        ["#fff0", "hex4 white zero"],
        ["#00000000", "hex8 zero"],
        ["#12345600", "hex8 color zero"],
        ["hsla(120, 50%, 50%, 0)", "hsla zero"],
        ["hsla(120, 50%, 50%, 0%)", "hsla pct zero"],
        ["hsl(120, 50%, 50%, 0)", "hsl comma zero"],
        ["rgb(10 20 30 / 0)", "rgb slash zero"],
        ["rgb(10 20 30 / 0%)", "rgb slash pct zero"],
        ["hsl(120 50% 50% / 0)", "hsl slash zero"],
        ["hwb(120 10% 20% / 0)", "hwb slash zero"],
        ["lab(50% 0 0 / 0)", "lab slash zero"],
        ["lch(50% 20 180 / 0%)", "lch slash zero"],
        ["oklab(0.5 0 0 / 0)", "oklab slash zero"],
        ["oklch(0.6 0.1 180 / 0)", "oklch slash zero"],
        ["color(srgb 1 0 0 / 0)", "color srgb zero"],
        ["color(display-p3 1 0 0 / 0%)", "color p3 zero"],
        ["rgb(10 20 30 / none)", "rgb slash none"],
      ];
      let y = 10;
      for (const [color, name] of zeroColors) {
        ctx.save();
        ctx.fillStyle = color;
        ctx.fillText(`Fill ${name}`, 20, y);
        ctx.strokeStyle = color;
        ctx.strokeText(`Stroke ${name}`, 80, y);
        ctx.restore();
        y = (y % 120) + 5;
      }

      // `fillText` checks `fillStyle` while `strokeText` checks `strokeStyle` independently.
      ctx.save();
      ctx.fillStyle = "transparent";
      ctx.strokeStyle = "#111";
      ctx.fillText("Hidden fill only", 30, 30);
      ctx.strokeText("Visible stroke only", 30, 40);
      ctx.restore();

      ctx.save();
      ctx.strokeStyle = "rgba(0, 0, 0, 0)";
      ctx.fillStyle = "#111";
      ctx.strokeText("Hidden stroke only", 30, 50);
      ctx.fillText("Visible fill only", 30, 60);
      ctx.restore();

      // A skipped transparent stroke must not arm `target.last` and swallow a visible fill at the same position.
      ctx.save();
      ctx.strokeStyle = "rgba(0, 0, 0, 0)";
      ctx.fillStyle = "#222";
      ctx.strokeText("Survived pair", 50, 70);
      ctx.fillText("Survived pair", 50, 70);
      ctx.restore();

      // Opaque, low-alpha, gradient, and pattern styles remain visible and must be recorded without throwing.
      ctx.save();
      ctx.fillStyle = "#ff0000";
      ctx.fillText("Hex6 red", 30, 80);
      ctx.fillStyle = "#0001";
      ctx.fillText("Hex4 nonzero", 30, 85);
      ctx.fillStyle = "#00000001";
      ctx.fillText("Hex8 nonzero", 30, 90);
      ctx.fillStyle = "rgb(0, 0, 0)";
      ctx.fillText("Rgb3 black", 30, 95);
      ctx.fillStyle = "hsl(120, 50%, 0%)";
      ctx.fillText("Hsl3 black", 30, 100);
      ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
      ctx.fillText("Low alpha", 30, 105);
      const grad = ctx.createLinearGradient(0, 0, 100, 0);
      grad.addColorStop(0, "#000");
      grad.addColorStop(1, "#fff");
      ctx.fillStyle = grad;
      ctx.fillText("Gradient fill", 30, 110);
      ctx.strokeStyle = grad;
      ctx.strokeText("Gradient stroke", 30, 115);
      const pat = ctx.createPattern(canvas, "repeat");
      if (pat) {
        ctx.fillStyle = pat;
        ctx.fillText("Pattern fill", 30, 120);
      }
      ctx.restore();
    },
  }],
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
"""
)

ZERO_FONT_SIZE_CHART = (
    CANVAS
    + """
new Chart(canvas, {
  type: "bar",
  plugins: [{
    id: "zeroFontSizes",
    afterDraw(chart) {
      const ctx = chart.ctx;
      const zeroFonts = [
        ["0px sans-serif", "0px"],
        ["bold 0px Arial", "bold 0px"],
        ["0pt serif", "0pt"],
        ["0rem sans-serif", "0rem"],
        ["0em monospace", "0em"],
        ["0px/1.2 sans-serif", "0px line"],
        ["0px / 1.4 sans-serif", "0px spaced line"],
        ["0% sans-serif", "0pct"],
        ["0.0px Arial", "0.0px"],
        [".0px Arial", "dot0px"],
        ["400 0px Inter", "weight 400 0px"],
        ["oblique 0deg 0px sans-serif", "oblique 0deg 0px"],
        ["0 sans-serif", "unitless 0"],
      ];
      for (const [fontSpec, label] of zeroFonts) {
        ctx.save();
        ctx.font = fontSpec;
        ctx.fillText(`Zero ${label}`, 25, 25);
        ctx.strokeText(`Zero stroke ${label}`, 25, 35);
        ctx.restore();
      }

      // A skipped 0px stroke at one point must not suppress a visible fill at the same point.
      ctx.save();
      ctx.font = "0px sans-serif";
      ctx.strokeText("Pair after 0px", 40, 45);
      ctx.font = "12px sans-serif";
      ctx.fillText("Pair after 0px", 40, 45);
      ctx.restore();

      const visibleFonts = [
        ["10px sans-serif", "Size 10px"],
        ["20px Arial", "Size 20px"],
        ["10.5px sans-serif", "Size 10.5px"],
        ["0.5px sans-serif", "Size 0.5px"],
        ["400 12px Inter", "Weight 400"],
        ["12px Font0", "Family Font0"],
        ['12px "0px Family", sans-serif', "Quoted 0px family"],
        ["12px/0px sans-serif", "Line-height 0px"],
        ["oblique 0deg 12px sans-serif", "Oblique 0deg 12px"],
      ];
      let y = 55;
      for (const [fontSpec, label] of visibleFonts) {
        ctx.save();
        ctx.font = fontSpec;
        ctx.fillText(label, 25, y);
        ctx.restore();
        y += 8;
      }
    },
  }],
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
"""
)

INVISIBLE_AND_OFF_CANVAS_CHART = (
    CANVAS
    + """
const container = document.getElementById("container");
const zeroCanvas = document.createElement("canvas");
zeroCanvas.width = 0;
zeroCanvas.height = 100;
container.appendChild(zeroCanvas);
zeroCanvas.getContext("2d").fillText("Zero canvas", 0, 0);

new Chart(canvas, {
  type: "bar",
  plugins: [{
    id: "visibilityChecks",
    afterDraw(chart) {
      const ctx = chart.ctx;
      ctx.save();
      ctx.globalAlpha = 0;
      ctx.fillText("Alpha zero fill", 60, 60);
      ctx.strokeText("Alpha zero stroke", 60, 80);
      ctx.restore();

      ctx.fillText("Left off", -10, 60);
      ctx.fillText("Top off", 60, -10);
      ctx.fillText("Right off", 2000, 60);
      ctx.strokeText("Bottom off", 60, 1200);

      ctx.save();
      ctx.translate(2000, 0);
      ctx.fillText("Translated off", 10, 60);
      ctx.restore();

      ctx.save();
      ctx.translate(100, 100);
      ctx.fillText("Translated in", -40, -40);
      ctx.restore();

      ctx.fillText("Origin edge", 0, 0);
      ctx.fillText("Visible note", 80, 80);
    },
  }],
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
"""
)

OBJECT_ARGUMENTS_CHART = (
    CANVAS
    + """
let textCalls = 0;
let strokeCalls = 0;
let xCalls = 0;
let yCalls = 0;
let widthCalls = 0;

const labelObj = {
  toString() {
    textCalls += 1;
    if (textCalls > 1) throw new Error("fillText toString called more than once");
    return "Object label";
  },
};
const strokeObj = {
  toString() {
    strokeCalls += 1;
    if (strokeCalls > 1) throw new Error("strokeText toString called more than once");
    return "Stroke object label";
  },
};
const xObj = {
  valueOf() {
    xCalls += 1;
    if (xCalls > 1) throw new Error("x valueOf called more than once");
    return 40;
  },
};
const yObj = {
  valueOf() {
    yCalls += 1;
    if (yCalls > 1) throw new Error("y valueOf called more than once");
    return 60;
  },
};
const widthObj = {
  valueOf() {
    widthCalls += 1;
    if (widthCalls > 1) throw new Error("maxWidth valueOf called more than once");
    return 120;
  },
};

new Chart(canvas, {
  type: "bar",
  plugins: [{
    id: "objectArgs",
    afterDraw(chart) {
      const ctx = chart.ctx;
      ctx.fillText(labelObj, 40, 40);
      ctx.strokeText(strokeObj, 40, 60);
      ctx.fillText("Object x", xObj, 80);
      ctx.fillText("Object y", 40, yObj);
      ctx.fillText("Object width", 40, 100, widthObj);
      ctx.fillText(42, 40, 120);
      ctx.strokeText("Plain string", 40, 140);
    },
  }],
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
window.__testResult = { textCalls, strokeCalls, xCalls, yCalls, widthCalls };
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
        run = run_node_probe(tmp_path / "render", EXISTING_MODEL_ONLY_CHART)
        unrecorded = run_node_probe(tmp_path / "page", EXISTING_MODEL_ONLY_CHART, page_only=True)

        assert run.labels == EXPECTED_MODEL_ONLY_LABELS
        assert unrecorded.labels == EXPECTED_MODEL_ONLY_LABELS
        assert run.labels_truncated is True

        # A dataset without `label` leaves `legendItem.text` undefined; no `"undefined"` annotation appears.
        unnamed = run_node_probe(
            tmp_path / "unnamed",
            CANVAS + "new Chart(canvas, { type: 'bar', options: { animation: false,"
            " scales: { y: { min: 0, max: 2, ticks: { stepSize: 1 } } } },"
            " data: { labels: ['a', 'b'], datasets: [{ data: [1, 2] }] } });\n",
        )
        assert unnamed.labels == [
            ("y tick label", "0"),
            ("y tick label", "1"),
            ("y tick label", "2"),
            ("x tick label", "a"),
            ("x tick label", "b"),
        ]

    def test_without_sandbox_mode_filltext_is_not_wrapped(self, tmp_path: Path) -> None:
        smoke = (REPO_ROOT / "agents" / "renderer" / "toolchain" / "smoke.js").read_text(encoding="utf-8")
        run = run_node_probe(tmp_path, smoke, sandbox=False)

        assert run.browser_launched is True
        assert run.fill_text_wrapped is False and run.stroke_text_wrapped is False
        assert run.has_canvas_texts_hook is False
        assert "recordChartjsCanvasTexts" not in run.written_html
        assert "__anyplotCanvasTexts" not in run.written_html
        assert run.loaded_html == run.written_html
        modules = _node_modules()
        assert modules is not None
        bundle = (modules / "chart.js" / "dist" / "chart.umd.js").read_text(encoding="utf-8")
        template = (REPO_ROOT / "tests" / "unit" / "automation" / "fixtures" / "js-render-page-light.html").read_text(
            encoding="utf-8"
        )
        expected = template.replace("{{SNIPPET}}", smoke).replace(
            "{{BUNDLE}}", re.sub("</script", lambda _: "<\\/script", bundle, flags=re.IGNORECASE)
        )
        assert run.written_html.encode("utf-8") == expected.encode("utf-8")

    def test_written_render_page_and_page_only_omit_the_recorder_while_loaded_page_records(
        self, tmp_path: Path
    ) -> None:
        smoke = (REPO_ROOT / "agents" / "renderer" / "toolchain" / "smoke.js").read_text(encoding="utf-8")
        table = '{"columns":["label","value"],"data":[["a",3],["b",1]]}'
        page_run = run_node_probe(tmp_path / "page", smoke, sandbox=True, page_only=True)
        page_data_run = run_node_probe(tmp_path / "page-data", smoke, sandbox=True, page_only=True, data_json=table)
        render_run = run_node_probe(tmp_path / "render", smoke, sandbox=True, page_only=False)
        render_data_run = run_node_probe(
            tmp_path / "render-data", smoke, sandbox=True, page_only=False, data_json=table
        )

        assert page_run.returncode == 0 and page_data_run.returncode == 0
        assert render_run.returncode == 0 and render_data_run.returncode == 0
        assert page_run.browser_launched is False and page_data_run.browser_launched is False
        assert render_run.browser_launched is True and render_data_run.browser_launched is True

        for html in (
            page_run.written_html,
            page_data_run.written_html,
            render_run.written_html,
            render_data_run.written_html,
        ):
            assert "recordChartjsCanvasTexts" not in html
            assert "__anyplotCanvasTexts" not in html

        assert render_run.written_html.encode("utf-8") == page_run.written_html.encode("utf-8")
        assert render_data_run.written_html.encode("utf-8") == page_data_run.written_html.encode("utf-8")
        assert page_run.written_html.count("<script") == 3
        assert render_run.written_html.count("<script") == 3
        assert page_data_run.written_html.count("<script") == 4  # `<script type="application/json">` + 3 code scripts
        assert render_data_run.written_html.count("<script") == 4
        assert page_run.fill_text_wrapped is False and page_run.stroke_text_wrapped is False
        assert page_run.has_canvas_texts_hook is False

        written_eval = evaluate_written_html(
            tmp_path / "eval-render-written", tmp_path / "render" / "work" / "plot-light.html"
        )
        assert written_eval["fillTextWrapped"] is False and written_eval["strokeTextWrapped"] is False
        assert written_eval["hasCanvasTextsHook"] is False

        assert render_run.loaded_html is not None and render_data_run.loaded_html is not None
        assert "recordChartjsCanvasTexts" in render_run.loaded_html
        assert "__anyplotCanvasTexts" in render_run.loaded_html
        assert "recordChartjsCanvasTexts" in render_data_run.loaded_html
        assert render_run.loaded_html.count("<script") == 4
        assert render_data_run.loaded_html.count("<script") == 5
        # The recorder sits in its own `<script>` before the snippet's `<script>`, so `SNIPPET_HEAD` (`\ntry {\n`)
        # and `SNIPPET_LINE_OFFSET` inside the snippet `<script>` are unchanged.
        assert f"</script>\n<script>\ntry {{\n{smoke}" in render_run.loaded_html
        assert render_run.fill_text_wrapped is True and render_run.stroke_text_wrapped is True
        assert render_run.has_canvas_texts_hook is True

    def test_more_recorded_texts_than_label_limit_keep_tick_labels_and_set_truncated(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, OVER_LABEL_LIMIT_CHART)

        assert len(run.labels) == 400
        assert run.labels[:6] == [
            ("title", "Many Notes"),
            ("y axis label", "Count"),
            ("y tick label", "0"),
            ("y tick label", "1"),
            ("y tick label", "2"),
            ("x tick label", "A"),
        ]
        assert run.labels[6] == ("annotation", "L" * 200)
        assert run.labels[7] == ("annotation", "Note 0")
        assert run.labels_truncated is True

    def test_non_chart_canvas_texts_rank_after_tick_labels_and_set_truncated(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, NON_CHART_CANVAS_OVER_LIMIT)

        assert len(run.labels) == 400
        assert run.labels[:6] == [
            ("title", "Main Chart"),
            ("y axis label", "Count"),
            ("y tick label", "0"),
            ("y tick label", "1"),
            ("y tick label", "2"),
            ("x tick label", "A"),
        ]
        assert run.labels[6] == ("annotation", "Extra 0")
        assert run.labels[7] == ("annotation", "Extra 1")
        assert run.labels_truncated is True

    def test_transparent_fill_and_stroke_styles_are_skipped_without_corrupting_outlined_pairs(
        self, tmp_path: Path
    ) -> None:
        run = run_node_probe(tmp_path, TRANSPARENT_STYLES_CHART)

        texts = [text for _, text in run.labels]
        for visible in (
            "Visible stroke only",
            "Visible fill only",
            "Hex6 red",
            "Hex4 nonzero",
            "Hex8 nonzero",
            "Rgb3 black",
            "Hsl3 black",
            "Low alpha",
            "Gradient fill",
            "Gradient stroke",
            "Pattern fill",
        ):
            assert ("annotation", visible) in run.labels, (visible, run.labels)
        assert run.labels.count(("annotation", "Survived pair")) == 1
        assert "Hidden fill only" not in texts
        assert "Hidden stroke only" not in texts
        for text in texts:
            assert not text.startswith("Fill ") and not text.startswith("Stroke "), (text, run.labels)

    def test_zero_font_sizes_are_skipped_while_nonzero_and_weight_or_family_zeros_stay(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, ZERO_FONT_SIZE_CHART)

        texts = [text for _, text in run.labels]
        for visible in (
            "Size 10px",
            "Size 20px",
            "Size 10.5px",
            "Size 0.5px",
            "Weight 400",
            "Family Font0",
            "Quoted 0px family",
            "Line-height 0px",
            "Oblique 0deg 12px",
        ):
            assert ("annotation", visible) in run.labels, (visible, run.labels)
        assert run.labels.count(("annotation", "Pair after 0px")) == 1
        for text in texts:
            assert not text.startswith("Zero "), (text, run.labels)

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
            assert echarts_run.labels.index(("annotation", "5")) < echarts_run.labels.index(("x tick label", "Zug"))
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
        assert highcharts_run.labels.index(("annotation", "5")) < highcharts_run.labels.index(("x tick label", "Zug"))
        assert highcharts_run.labels.count(("annotation", "5")) == 1
        assert highcharts_run.labels_truncated is False

    def test_the_wrapper_swallows_recording_errors_and_returns_the_originals_result(self, tmp_path: Path) -> None:
        source = (
            CANVAS
            + """
const ctx = canvas.getContext("2d");
const bad = { toString() { throw new Error("unprintable"); } };
const fillReturn = ctx.fillText("Recorded note", 15, 25);
const savedGetTransform = ctx.getTransform;
ctx.getTransform = () => { throw new Error("transform failed"); };
const strokeReturn = ctx.strokeText("Transform error", 15, 45);
ctx.getTransform = savedGetTransform;
const badReturn = ctx.strokeText(bad, 15, 65);
window.__testResult = { fillReturn, strokeReturn, badReturn, calls: ctx._calls.length };
new Chart(canvas, {
  type: "bar",
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
canvas.getContext("2d").fillText("After chart", 30, 30);
"""
        )
        run = run_node_probe(tmp_path, source)

        assert run.probe_result == {
            "fillReturn": "fill-sentinel",
            "strokeReturn": "stroke-sentinel",
            "badReturn": "stroke-sentinel",
            "calls": 3,
        }
        assert ("annotation", "After chart") in run.labels
        assert ("annotation", "Transform error") not in run.labels
        assert ("annotation", "Recorded note") not in run.labels  # wiped by `new Chart`'s complete draw on `canvas`

    def test_invisible_alpha_zero_and_off_canvas_texts_are_skipped(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path, INVISIBLE_AND_OFF_CANVAS_CHART)

        assert ("annotation", "Translated in") in run.labels
        assert ("annotation", "Origin edge") in run.labels
        assert ("annotation", "Visible note") in run.labels
        for skipped in (
            "Zero canvas",
            "Alpha zero fill",
            "Alpha zero stroke",
            "Left off",
            "Top off",
            "Right off",
            "Bottom off",
            "Translated off",
        ):
            assert not any(text == skipped for _, text in run.labels), (skipped, run.labels)

    def test_object_arguments_are_never_converted_by_the_recorder(self, tmp_path: Path) -> None:
        run = run_node_probe(tmp_path / "shim", OBJECT_ARGUMENTS_CHART)

        assert run.probe_result == {"textCalls": 0, "strokeCalls": 0, "xCalls": 0, "yCalls": 0, "widthCalls": 0}
        assert ("annotation", "42") in run.labels
        assert ("annotation", "Plain string") in run.labels
        for skipped in ("Object label", "Stroke object label", "Object x", "Object y", "Object width"):
            assert not any(text == skipped for _, text in run.labels), (skipped, run.labels)

        # Also simulate WebIDL native conversion (`String(text)`, `Number(x)`, `Number(y)`, `Number(maxWidth)`):
        # each counting object sees exact call count 1, never 2.
        native_coercing = (
            """
const origFill = CanvasRenderingContext2D.prototype.fillText;
const origStroke = CanvasRenderingContext2D.prototype.strokeText;
void origFill;
void origStroke;
"""
            + CANVAS
            + """
let fillToString = 0;
let strokeToString = 0;
let xValueOf = 0;
const ctx = canvas.getContext("2d");
const proto = Object.getPrototypeOf(ctx);
// Beneath `render.mjs`'s wrapper sits `CanvasRenderingContext2D.prototype`'s original stub; verify a single
// `toString()` inside a snippet helper that mimics WebIDL conversion after the wrapper's `try` block ran.
const countedFill = {
  toString() {
    fillToString += 1;
    if (fillToString > 1) throw new Error("fillText converted twice");
    return "Native once";
  },
};
const countedStroke = {
  toString() {
    strokeToString += 1;
    if (strokeToString > 1) throw new Error("strokeText converted twice");
    return "Stroke once";
  },
};
const countedX = {
  valueOf() {
    xValueOf += 1;
    if (xValueOf > 1) throw new Error("x converted twice");
    return 25;
  },
};
new Chart(canvas, {
  type: "bar",
  plugins: [{
    id: "coercingCheck",
    afterDraw(chart) {
      chart.ctx.fillText(countedFill, countedX, 30);
      chart.ctx.strokeText(countedStroke, 25, 50);
      // Native WebIDL conversion happens once inside the browser's C++ binding:
      String(countedFill);
      Number(countedX);
      String(countedStroke);
    },
  }],
  data: { labels: ["A"], datasets: [{ label: "S", data: [1] }] },
  options: { animation: false },
});
window.__testResult = { fillToString, strokeToString, xValueOf, wrapped: proto.fillText !== undefined };
"""
        )
        coerced = run_node_probe(tmp_path / "coerced", native_coercing)
        assert coerced.probe_result == {"fillToString": 1, "strokeToString": 1, "xValueOf": 1, "wrapped": True}

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
        for ghost in (
            "Draft note",
            "Draft title",
            "OldX",
            "OldSeries",
            "NaN x",
            "Inf y",
            "Zero maxWidth",
            "Neg maxWidth",
        ):
            assert not any(text == ghost for _, text in run.labels), (ghost, run.labels)

    def test_translated_canvas_positions_tell_an_outlined_pair_from_two_separate_labels(self, tmp_path: Path) -> None:
        source = (
            CANVAS
            + """
new Chart(canvas, {
  type: "bar",
  plugins: [{
    id: "p",
    afterDraw(c) {
      const ctx = c.ctx;
      ctx.save();
      ctx.translate(40, 50);
      ctx.strokeText("Outlined", 0, 0);
      ctx.fillText("Outlined", 0, 0);
      ctx.restore();

      ctx.save();
      ctx.translate(40, 120);
      ctx.strokeText("62%", 0, 0);
      ctx.restore();
      ctx.save();
      ctx.translate(180, 120);
      ctx.fillText("62%", 0, 0);
      ctx.restore();
    },
  }],
  data: { labels: ["A", "B"], datasets: [{ label: "Share", data: [1, 2] }] },
  options: { animation: false },
});
"""
        )
        run = run_node_probe(tmp_path, source)

        assert run.labels.count(("annotation", "Outlined")) == 1
        assert run.labels.count(("annotation", "62%")) == 2


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

    def render(
        self,
        tmp_path: Path,
        source: str,
        *,
        library: str = "chartjs",
        sandbox: bool = True,
        page_only: bool = False,
        env: dict[str, str] | None = None,
    ) -> BrowserRun:
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
        if page_only:
            environment["ANYPLOT_PAGE_ONLY"] = "1"
        environment |= env or {}
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
        assert labels == EXPECTED_MODEL_ONLY_LABELS
        assert truncated is True

    def test_without_sandbox_filltext_is_not_wrapped(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        check = (
            CANVAS + 'if (!CanvasRenderingContext2D.prototype.fillText.toString().includes("[native code]")) '
            'throw new Error("fillText wrapped outside sandbox");\n'
        )
        run = browser_harness.render(tmp_path, check, sandbox=False)
        assert run.returncode == 0, run.stderr
        assert not (run.work / "probe-light.json").exists()

    def test_page_only_and_written_render_page_omit_the_recorder(
        self, browser_harness: BrowserHarness, tmp_path: Path
    ) -> None:
        page_run = browser_harness.render(tmp_path / "page", BAR_WITH_FOUR_POINT_ZERO, page_only=True)
        render_run = browser_harness.render(tmp_path / "render", BAR_WITH_FOUR_POINT_ZERO, env={"ANYPLOT_NO_HTML": "0"})
        assert page_run.returncode == 0 and render_run.returncode == 0, (page_run.stderr, render_run.stderr)
        page_bytes = (page_run.work / "plot-light.html").read_bytes()
        render_bytes = (render_run.work / "plot-light.html").read_bytes()
        assert page_bytes == render_bytes
        html = render_bytes.decode("utf-8")
        assert "recordChartjsCanvasTexts" not in html and "__anyplotCanvasTexts" not in html
        labels, _ = render_run.probe()
        assert labels.count(("annotation", "4.0")) == 1

    def test_invisible_and_off_canvas_texts_are_skipped(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, INVISIBLE_AND_OFF_CANVAS_CHART)
        assert run.returncode == 0, run.stderr
        labels, _ = run.probe()
        assert ("annotation", "Translated in") in labels and ("annotation", "Visible note") in labels
        for skipped in (
            "Zero canvas",
            "Alpha zero fill",
            "Alpha zero stroke",
            "Left off",
            "Top off",
            "Right off",
            "Bottom off",
            "Translated off",
        ):
            assert not any(text == skipped for _, text in labels), (skipped, labels)

    def test_transparent_styles_and_zero_font_sizes_are_skipped(
        self, browser_harness: BrowserHarness, tmp_path: Path
    ) -> None:
        transparent = browser_harness.render(tmp_path / "transparent", TRANSPARENT_STYLES_CHART)
        zero_font = browser_harness.render(tmp_path / "zero-font", ZERO_FONT_SIZE_CHART)
        assert transparent.returncode == 0 and zero_font.returncode == 0, transparent.stderr + zero_font.stderr

        t_labels, _ = transparent.probe()
        t_texts = [text for _, text in t_labels]
        for visible in (
            "Visible stroke only",
            "Visible fill only",
            "Gradient fill",
            "Gradient stroke",
            "Survived pair",
        ):
            assert ("annotation", visible) in t_labels, (visible, t_labels)
        assert "Hidden fill only" not in t_texts and "Hidden stroke only" not in t_texts
        for text in t_texts:
            assert not text.startswith("Fill ") and not text.startswith("Stroke "), (text, t_labels)

        f_labels, _ = zero_font.probe()
        f_texts = [text for _, text in f_labels]
        for visible in ("Size 10px", "Size 20px", "Size 0.5px", "Weight 400", "Family Font0", "Pair after 0px"):
            assert ("annotation", visible) in f_labels, (visible, f_labels)
        for text in f_texts:
            assert not text.startswith("Zero "), (text, f_labels)

    def test_object_arguments_are_not_converted_by_the_recorder(
        self, browser_harness: BrowserHarness, tmp_path: Path
    ) -> None:
        run = browser_harness.render(tmp_path, OBJECT_ARGUMENTS_CHART)
        assert run.returncode == 0, run.stderr
        labels, _ = run.probe()
        assert ("annotation", "42") in labels and ("annotation", "Plain string") in labels
        for skipped in ("Object label", "Stroke object label", "Object x", "Object y", "Object width"):
            assert not any(text == skipped for _, text in labels), (skipped, labels)

    def test_label_limit_caps_recorded_texts(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        run = browser_harness.render(tmp_path, OVER_LABEL_LIMIT_CHART)
        assert run.returncode == 0, run.stderr
        labels, truncated = run.probe()
        assert len(labels) == 400 and truncated is True
        assert labels[:6] == [
            ("title", "Many Notes"),
            ("y axis label", "Count"),
            ("y tick label", "0"),
            ("y tick label", "1"),
            ("y tick label", "2"),
            ("x tick label", "A"),
        ]
        assert labels[6] == ("annotation", "L" * 200) and labels[7] == ("annotation", "Note 0")

    def test_non_chart_canvas_texts_rank_after_tick_labels(
        self, browser_harness: BrowserHarness, tmp_path: Path
    ) -> None:
        run = browser_harness.render(tmp_path, NON_CHART_CANVAS_OVER_LIMIT)
        assert run.returncode == 0, run.stderr
        labels, truncated = run.probe()
        assert len(labels) == 400 and truncated is True
        assert labels[:6] == [
            ("title", "Main Chart"),
            ("y axis label", "Count"),
            ("y tick label", "0"),
            ("y tick label", "1"),
            ("y tick label", "2"),
            ("x tick label", "A"),
        ]
        assert labels[6] == ("annotation", "Extra 0")

    def test_echarts_and_highcharts_probes_unchanged(self, browser_harness: BrowserHarness, tmp_path: Path) -> None:
        ec = browser_harness.render(tmp_path / "ec", ECHARTS_FIGURE, library="echarts")
        hc = browser_harness.render(tmp_path / "hc", HIGHCHARTS_FIGURE, library="highcharts")
        assert ec.returncode == 0 and hc.returncode == 0, ec.stderr + hc.stderr
        ec_labels, ec_truncated = ec.probe()
        hc_labels, hc_truncated = hc.probe()
        assert {("title", "Umsatz"), ("subtitle", "in CHF"), ("annotation", "5")} <= set(ec_labels)
        assert {("title", "Umsatz"), ("y axis label", "CHF"), ("annotation", "5")} <= set(hc_labels)
        assert ec_truncated is False and hc_truncated is False
