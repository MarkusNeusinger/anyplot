"""Two-profile validator of the JavaScript code profile (Chart.js, D3, ECharts, Highcharts, MUI X), over tree-sitter.

The JavaScript counterpart of `profiles/julia/validate.py`, with the same `Finding` and,
where a rule has a Python, R or Julia twin, the same rule id. `validate_security` runs on
the normalised catalogue original (eligibility) and on every adapted working form;
`validate_adaptation` on adapted code only. Both take the library, which picks the grammar
(`tsx` for MUI X) and the one library global the page defines. Both return an empty list
for valid code and never raise: oversize code, text that is not UTF-8 and code tree-sitter
cannot read are findings.

**Threat model.** The rules are hygiene, not the boundary (second opinions of 2026-10-24
and 2026-10-30, `agentic/specs/261024-agent-all-libraries.md`): the snippet runs in a
Chromium page under the harness's sandbox mode (every request aborted, every WebSocket
closed, no popup, a content security policy with `default-src 'none'`, WebRTC without a
route, `agents/renderer`'s gVisor sandbox with no network and a read-only root, JS-2), and
MUI X's imports are closed by the bundle step's allowlist. This list keeps the exported
`plot.js`, which a user opens in a browser of their own, free of the model's accidental
network, storage and frame access and of code built from strings, and it makes the
adapter's output boring. The rules refuse by shape, as Julia's do, and the named bypasses
of the design passes are tests.

SECURITY rules (rule ids in parentheses):

* **Free names** (`banned-name`): a name the file does not bind around it
  (`treesitter.js_references`, with the scopes of `var`, `let`, `const`, functions,
  classes, parameters and imports) must be one of `GLOBALS`: the ECMAScript built-ins that
  compute (`Math`, `Date`, `Array`, `Intl`, the typed arrays, ...), the page's `window`
  and `document`, the animation and timer functions, and the file's own library global
  (`Chart`, `d3`, `echarts`, `Highcharts`; MUI X imports its names). A closed world: the
  catalogue's 1,617 files read 33 such names (2026-10-30). Everything else is refused,
  read or written, with the reason of `DENIED_NAMES` where it has one (`fetch`,
  `XMLHttpRequest`, `WebSocket`, `EventSource`, `Worker`, `navigator`, `localStorage`,
  `postMessage`, `eval`, `Function`, `require`, `globalThis`, `self`, `top`, `parent`,
  `frames`, `Image`, `Blob`, `URL`, `Reflect`, `Proxy`, `WebAssembly`, ...): so an alias
  (`const f = fetch`), a shorthand property (`{ fetch }`), optional chaining
  (`fetch?.(url)`) and a call through a value (`(0, eval)(s)`) are refused like the name.
  A binding the file makes shadows a global as JavaScript does (`const open = d.open` in a
  candlestick plot); `window`, `document` and the library global may not be bound at the
  top level, where the token lines read them. `arguments` is a name only inside a function
  that is no arrow (`treesitter.js_bindings` binds it there); at the top level it is refused
  like any unknown name (Copilot review of #12473).
* **The page's objects** (`banned-name`): `window` and `document` are only ever the object
  of a member access with a name (`window.ANYPLOT_TOKENS`, `document.getElementById`), never
  a value (`const w = window`, `f(document)`, `{ ...window }`, `const { fetch } = window`)
  and never indexed by code (`window["fe" + "tch"]`, `window[name]`); a literal index
  (`window["fetch"]`, `` window[`fetch`] ``) reads as the member it names. A member of
  `window` is one of `WINDOW_MEMBERS` (the three token globals, `__anyplotReady`, event
  listeners, `devicePixelRatio`, ...; `window.open`, `window.location`, `window.parent`,
  `window.self` and `window.window` are not), and only `window.__anyplotReady`, the
  harness's ready signal, may be written; a member of `document` is one of
  `DOCUMENT_MEMBERS` (`getElementById`, `createElement`, `head`, `body`, ...; never
  `cookie`, `write`, `location` or `defaultView`); `window.ANYPLOT_DATA` is the loader's
  alone (the data comes from the placeholder). `Object` lends only `OBJECT_MEMBERS`
  (`keys`, `entries`, `fromEntries`, `assign`, ...), never its prototype and descriptor
  reflection; D3's file loaders (`d3.json`, `d3.csv`, `d3.image`, ...) and Highcharts'
  `ajax` and `getJSON` are refused (`LIBRARY_DENIED`).
* **Members of any value** (`banned-name`): `DENIED_MEMBERS` (`constructor`, `__proto__`,
  the `__define…__` and `__lookup…__` accessors, `defaultView`,
  `ownerDocument`, `contentWindow`, `contentDocument`, ...) are refused after a `.` or `?.`,
  as a literal index (`x["constructor"]`), as a destructured key (`const { constructor } =
  f`) and, for those that lead to code or another window (`DENIED_MEMBER_STRINGS`), as a
  string literal of their own (`"constructor"`): they lead from any value to `Function`, to
  the window or to a frame. `cookie` is refused on any receiver
  (`document.documentElement.parentNode.cookie` reached the document past
  `DOCUMENT_MEMBERS`).
* **Computed keys** (`banned-name`, review of JS-3): a key that code builds from strings (a
  `+` chain with a string, a template with a substitution, or a name given such a value)
  must not be able to spell a member of `DENIED_MEMBER_STRINGS` once the run fills in its
  unknown parts (`[]["con" + "structor"]`; the catalogue's `` w[`z_${v}`] `` and
  `r[m + "Norm"]` cannot), and a key a string builder returns (`.join()`,
  `String.fromCharCode(...)`, `atob(...)`) is refused unless its literals decide it
  (`fold_string`: `["con", "structor"].join("")` is `constructor`); a written key, and an
  object literal's computed key, which `Object.assign` or a spread can write onto an
  element, also must not be able to spell `dangerouslySetInnerHTML`, a name of
  `WRITE_CHECKED` (`href`, `src`, `srcdoc`, `action`, `location`, `cookie`, `innerHTML`, ...)
  or, by its written `on` start, an inline handler (`el["hr" + "ef"] = url`,
  `{ ["dangerously" + "SetInnerHTML"]: x }`; Copilot review of #12473). Names, literals,
  numbers and lookups (`d[QUARTER]`, `arr[Math.floor(i)]`) stay, and so do two MUI X `sx`
  selectors a `.join()` builds as an object's key.
* **`this`** (`banned-name`): outside a function that binds its own (`this` at the top
  level, or in an arrow function there) it is the window and is refused, and so is
  `this.<name>` for a name of `DENIED_NAMES`. Inside a plain function a classic script
  hands it the window when nothing else does (`function g() { return this } g()`, an
  array's `map`, a timer, D3's `call`), so `this` is used as a value (returned, assigned,
  passed, spread, destructured) or read by a computed key only where it is known
  (`_Scan.this_is_known`: a method or class member, an object's value such as Highcharts'
  `load` and `formatter`, a callback of D3's `each` and `on`, or a function the file only
  hands to those; 47 catalogue callbacks pass `this` to `d3.select`). In every context,
  known or not, `this.window`, `this.document`, the window-only names of `DENIED_NAMES`
  (`this.open`, `this.top`, ...) and `this[...]` by a computed key are refused, because a
  method handed to a browser callback (`addEventListener("load", o.m)`, a timer) runs with
  the window as `this` (Copilot review of #12473); `this.chart`, `this.point` and `this.x`
  stay, and no catalogue file reads one of the refused.
* **Code from strings and elements that load** (`banned-call`): `import(...)` and
  `import.meta`; `setTimeout` and `setInterval` with anything but a function literal or a
  function the file declares and never writes again (a string runs as code); an element
  created with a tag of `DENIED_TAGS` (`script`, `iframe`, `object`, `embed`, `link`,
  `base`, `form`, ...) by `document.createElement`, `createElementNS`, `d3.create`, any
  receiver's `append`, `insert` or `createElement` (D3, React), React's `jsx` runtime, or
  written as a JSX element, with the tag a literal, a ternary of literals or a `const`
  declared with one; `document.createElement` with any other tag; the high-risk
  tags of `DENIED_TAG_STRINGS` (`script`, `iframe`, `embed`, ...) as a string literal
  anywhere; `dangerouslySetInnerHTML` as a JSX attribute or an object's key (a spread
  `<div {...p} />` carries it); `.write()` and `.writeln()` on any receiver; and the
  `with` statement (`banned-statement`), which turns an object into scope. A call through a
  literal index calls the member it names (`d3["create"]("script")`,
  `el["setAttribute"](...)`), so these rules read it as the named call (`callee_name`).
* **Writes that load or navigate** (`banned-statement`, `banned-call`): a member `src` or
  `href` is written, by assignment or by `setAttribute`, `setAttributeNS` or D3's `attr`,
  only with a data URL the code drew (`canvas.toDataURL()` or a `const` declared with one:
  the catalogue's raster heatmaps), and `location`, `action`, `cookie`, `srcdoc` and
  `formAction` are never written. A setter's attribute name is checked for every literal it
  can be (`flag ? "x" : "href"`), a name code computes is refused (no catalogue file
  computes one), and an inline handler attribute (`setAttribute("onerror", ...)`, any case)
  is refused, because the attribute compiles its text. The same names are checked on an
  object that writes them onto an element (`check_written_source`): every `Object.assign`
  source whose target is no fresh `{}`, a `const` holding one, the objects spread into it,
  and Highcharts' `attr({...})`, where `innerHTML`, `outerHTML` and a handler property
  without a function written in place are refused too (Copilot review of #12473). In the
  exported page a content security policy stops a request but not a top-level navigation.
* **Imports** (`banned-import`): a Chart.js, D3, ECharts or Highcharts snippet is a
  classic script inside the harness's `try` block, so it imports and exports nothing (the
  library is the page's global). A MUI X module imports, and re-exports, only bare
  specifiers of the allowlisted packages (`allowlist.py`: `react`, `react-dom`,
  `@mui/material`, `@mui/x-charts`), never a relative, absolute, URL or `node:` path and
  never another package; a module of those packages that the image does not export is an
  ADAPTATION finding instead (`unavailable-import`), because the owner decided on
  2026-10-30 that a MUI X 7 file is served, coupled with a note.
* **The canvas and the theme** (`savefig-target`, `banned-statement`): exactly one
  orientation directive, a top-level `//` comment of its own; no directive text in a
  string, a template or a block comment, where the harness reads it all the same. A token
  line's names are bound only by that line, a token is never written, deleted or changed
  in place (`t.pageBg = ...`, `t.palette.push(...)`, `Object.assign(t, ...)`), and each
  protected statement (a token line, the placeholder) has its lines to itself.
* **Literals**: no URL (`url-literal`: `http://`, `https://`, `ftp://`, `ws://`, `wss://`,
  `file:`, `data:`, `blob:`, `javascript:`, and a protocol-relative `//host.tld/...`; the
  XML namespace URIs of SVG, XLink, XHTML and XMLNS excepted), no markup that runs or loads
  (`markup-code`: a `<script`, `<iframe`, `<object`, `<embed`, `<link`, `<meta`, `<base`,
  `<form` tag or an inline `on…=` handler, which `innerHTML` would run), and no string over
  `MAX_STRING_CHARS` characters (`string-length`), in strings, templates and JSX text.

What still passes, honestly (each a test, `test_still_passes_contained_by_the_sandbox`): a
key that a function of the file returns, or one passed in as a parameter, reaches whatever
it names (`el[key()]`, `o[k] = v`), because the catalogue reads every column and index that
way, also as an object's key written onto an element (`Object.assign(o, { [k]: v })`); an
object's method taken off its object, or handed to a browser callback, sees the window as
`this` and may pass it on as a value; an object's key a builder the run decides returns
(`{ [parts.map(f).join("")]: v }`); markup assembled from pieces at run time
(`"<img on" + "error=...>"`) runs as `innerHTML`
does, and so does markup the libraries take as text (an ECharts tooltip's HTML); a JSX
attribute (`<img src={url} />`) and a library's own image call
(`chart.renderer.image(url, ...)`) take a URL that code computes. None of them reaches a
network, a frame or the disk past the renderer's page rules (every request aborted, a
content security policy without `'unsafe-eval'`) and its sandbox, and the check stays
hygiene for the exported file, whose page JS-4 gives a content security policy of its own.

ADAPTATION rules, with the Python profile's ids: exactly one top-level
`const data = loadUserData();` (`placeholder-count`) and `loadUserData` nowhere else
(`placeholder-use`); no draws from the distributions that fabricate data (`rng`: D3's
`randomNormal`, `randomLogNormal`, `randomExponential`, ...; `Math.random`, D3's
`randomUniform`, `randomInt`, `randomLcg` and `shuffle` stay allowed for jitter and
subsampling, R's and Julia's precedent); no data from memory (`literal-data`: an array
literal with more than `MAX_LITERAL_NUMBERS` numbers); the palette prefix kept
(`palette-prefix`: an `IMPRINT_PALETTE` or `IMPRINT` the code writes out keeps the
original entries in order and adds only the next Imprint positions, and is never
reassigned or changed in place); and a MUI X import the image cannot bundle
(`unavailable-import`: a module of an allowlisted package off the allowlist, or a name of
`allowlist.REMOVED_EXPORTS`).

Messages never echo string contents, at most `MAX_SNIPPET_CHARS` of code. Findings are
sorted by line.
"""

import re

from tree_sitter import Node

from core.palette import IMPRINT

from ....schemas import MAX_CODE_CHARS
from ...treesitter import (
    COMMENTS,
    JS_FUNCTIONS,
    JS_STRINGS,
    JsBinding,
    JsReference,
    Source,
    Span,
    Visit,
    first_line,
    js_arguments,
    js_bindings,
    js_callee,
    js_named,
    js_number,
    js_object,
    js_property,
    js_references,
    js_root,
    js_string,
    js_unwrap,
    last_line,
    syntax_problems,
    walk,
)
from ...validate import MAX_LITERAL_NUMBERS, MAX_MESSAGE_CHARS, MAX_STRING_CHARS, Finding
from .allowlist import REMOVED_EXPORTS, package_of, packages, specifiers
from .regions import (
    DATA_GLOBAL,
    IMPRINT_NAMES,
    LIBRARY_GLOBALS,
    PLACEHOLDER,
    PLACEHOLDER_FUNC,
    TOKEN_GLOBALS,
    TSX_LIBRARIES,
    WINDOW,
    Regions,
    find_regions,
    grammar_for,
    is_placeholder,
)


MAX_SNIPPET_CHARS = 60
DOCUMENT = "document"
PAGE_OBJECTS = frozenset({WINDOW, DOCUMENT})
"""The page's objects a snippet reaches by name, and only ever as the object of a member access with a name."""
GLOBALS = frozenset(
    {
        # ECMAScript: values, functions and constructors that compute
        "Infinity",
        "NaN",
        "isFinite",
        "isNaN",
        "parseFloat",
        "parseInt",
        "encodeURIComponent",
        "decodeURIComponent",
        "encodeURI",
        "decodeURI",
        "structuredClone",
        "Object",
        "Array",
        "Number",
        "String",
        "Boolean",
        "BigInt",
        "Symbol",
        "Math",
        "JSON",
        "Date",
        "Intl",
        "RegExp",
        "Map",
        "Set",
        "WeakMap",
        "WeakSet",
        "Promise",
        "Iterator",
        "ArrayBuffer",
        "DataView",
        "Int8Array",
        "Uint8Array",
        "Uint8ClampedArray",
        "Int16Array",
        "Uint16Array",
        "Int32Array",
        "Uint32Array",
        "Float32Array",
        "Float64Array",
        "BigInt64Array",
        "BigUint64Array",
        "Error",
        "TypeError",
        "RangeError",
        "SyntaxError",
        "ReferenceError",
        "URIError",
        "AggregateError",
        "TextEncoder",
        "TextDecoder",
        # the page
        WINDOW,
        DOCUMENT,
        "requestAnimationFrame",
        "cancelAnimationFrame",
        "setTimeout",
        "setInterval",
        "clearTimeout",
        "clearInterval",
        "getComputedStyle",
        "console",
        "performance",
        "Path2D",
        "DOMMatrix",
        "DOMPoint",
        "DOMRect",
        "ImageData",
        # the working form's placeholder, which ADAPTATION keeps to its statement
        PLACEHOLDER_FUNC,
    }
)
"""The free names a snippet may read (module docstring, "Free names"): the catalogue's 33 on 2026-10-30 (`Math`,
`window`, `document`, `Array`, `parseInt`, `Number`, `Date`, `String`, `Infinity`, `Map`, `Set`, `Object`, the typed
arrays, `Intl`, `requestAnimationFrame`, `JSON`, `Error`, `TextEncoder`, ... and the four library globals) and the
built-ins of the same kind; the file's own library global is added per library (`LIBRARY_GLOBALS`)."""
DENIED_NAMES: dict[str, str] = {
    **dict.fromkeys(
        (
            "fetch",
            "XMLHttpRequest",
            "WebSocket",
            "WebSocketStream",
            "EventSource",
            "WebTransport",
            "RTCPeerConnection",
            "RTCDataChannel",
            "navigator",
            "location",
            "history",
            "Image",
            "Audio",
            "Request",
            "Response",
            "Headers",
            "FormData",
            "sendBeacon",
        ),
        "the network",
    ),
    **dict.fromkeys(
        ("localStorage", "sessionStorage", "indexedDB", "caches", "cookieStore", "Blob", "File", "FileReader", "URL"),
        "storage, files and object URLs",
    ),
    **dict.fromkeys(
        (
            "globalThis",
            "self",
            "top",
            "parent",
            "frames",
            "opener",
            "frameElement",
            "open",
            "close",
            "postMessage",
            "Worker",
            "SharedWorker",
            "ServiceWorker",
            "BroadcastChannel",
            "MessageChannel",
            "importScripts",
            "alert",
            "confirm",
            "prompt",
            "print",
        ),
        "other windows, frames and workers",
    ),
    **dict.fromkeys(
        (
            "eval",
            "Function",
            "require",
            "module",
            "exports",
            "process",
            "Reflect",
            "Proxy",
            "WebAssembly",
            "SharedArrayBuffer",
            "Atomics",
            "WeakRef",
            "FinalizationRegistry",
            "DOMParser",
            "queueMicrotask",
        ),
        "code built from strings or run elsewhere",
    ),
}
"""Names a snippet may not use, with the reason a message names (module docstring); none is in `GLOBALS`."""
WINDOW_MEMBERS = frozenset(
    {
        "ANYPLOT_TOKENS",
        "ANYPLOT_THEME",
        "ANYPLOT_SIZE",
        "__anyplotReady",
        "addEventListener",
        "removeEventListener",
        "devicePixelRatio",
        "innerWidth",
        "innerHeight",
        "requestAnimationFrame",
        "cancelAnimationFrame",
        "getComputedStyle",
    }
)
"""The members of `window` a snippet may read: the render context, the ready signal (the only one it may write) and the
page's geometry and events (the catalogue's `addEventListener` in 6 files, `devicePixelRatio` in 1)."""
WINDOW_WRITABLE = frozenset({"__anyplotReady"})
DOCUMENT_MEMBERS = frozenset(
    {
        "getElementById",
        "getElementsByTagName",
        "getElementsByClassName",
        "querySelector",
        "querySelectorAll",
        "createElement",
        "createElementNS",
        "createTextNode",
        "createDocumentFragment",
        "head",
        "body",
        "documentElement",
        "fonts",
    }
)
"""The members of `document` a snippet may read: finding and making elements (the catalogue's `getElementById`,
`createElement`, `createElementNS`, `head`, `body`)."""
OBJECT_MEMBERS = frozenset(
    {"keys", "values", "entries", "fromEntries", "assign", "freeze", "isFrozen", "groupBy", "hasOwn", "is", "create"}
)
"""What `Object` lends a snippet: the catalogue's `fromEntries`, `values`, `keys`, `entries` and `assign`, and the
same kind; never `getPrototypeOf`, `defineProperty` or the descriptors, which reach a value's hidden members."""
LIBRARY_DENIED: dict[str, frozenset[str]] = {
    "d3": frozenset({"json", "csv", "tsv", "dsv", "text", "xml", "html", "svg", "image", "buffer", "blob"}),
    "Highcharts": frozenset({"ajax", "getJSON", "post"}),
}
"""Library members that fetch a URL (D3's `d3-fetch`, Highcharts' AJAX helpers)."""
DENIED_MEMBERS = frozenset(
    {
        "constructor",
        "__proto__",
        "__defineGetter__",
        "__defineSetter__",
        "__lookupGetter__",
        "__lookupSetter__",
        "defaultView",
        "ownerDocument",
        "contentWindow",
        "contentDocument",
        "frameElement",
        "parentWindow",
        "srcdoc",
        "cookie",
        "localStorage",
        "sessionStorage",
        "serviceWorker",
        "sendBeacon",
        "importScripts",
    }
)
"""Member names a snippet may not use on any value (module docstring, "Members of any value"); no catalogue file reads
one (`cookie` joined after the review of JS-3: `document.documentElement.parentNode.cookie` reached the document past
`DOCUMENT_MEMBERS`). Names a data field may carry (`caller` and `callee` of a call graph, `open`, `location`) are refused
only where they reach the window: as a free name, or as a member of `window` or `document`."""
DENIED_MEMBER_STRINGS = frozenset(
    {
        "constructor",
        "__proto__",
        "__defineGetter__",
        "__defineSetter__",
        "__lookupGetter__",
        "__lookupSetter__",
        "defaultView",
        "ownerDocument",
        "contentWindow",
        "contentDocument",
        "frameElement",
        "parentWindow",
    }
)
"""The members of `DENIED_MEMBERS` that lead to code or another window, refused as a string of their own too
(`x[k]` with `k = "constructor"`), and the ones a computed key's fragments may not spell (`computed_key_risk`); a word
such as `cookie` stays a possible label."""
DENIED_TAGS = frozenset(
    {"script", "iframe", "frame", "frameset", "object", "embed", "applet", "portal", "base", "meta", "link", "form"}
)
"""Elements that run code, load a document or a resource, or submit: never created, in HTML, SVG or JSX."""
DENIED_TAG_STRINGS = frozenset({"script", "iframe", "frame", "frameset", "embed", "applet", "portal"})
"""The tags of `DENIED_TAGS` refused as a string literal anywhere (`const tag = "iframe"`), any case, with or without a
namespace prefix: no catalogue file writes one. `object`, `link`, `base`, `meta` and `form` are words a plot writes as
text (D3's `"link"` class of a network's edges in 4 files, a waterfall's `"base"` in 10), so they are refused only where
a tag is made: a literal, or a name bound to one, handed to an element creator."""
TAG_CREATORS = frozenset({"document.createElement", "document.createElementNS", "d3.create"})
TAG_METHODS = frozenset({"append", "insert", "createElement", "createElementNS"})
"""Methods that make an element from a tag name on any receiver: a D3 selection's `append` and `insert`, React's
`createElement` (Highcharts' renderer has one too, with SVG tags)."""
JSX_RUNTIME = frozenset({"jsx", "jsxs", "jsxDEV"})
"""`react/jsx-runtime`'s element makers, which take the tag first like `createElement`."""
TIMERS = frozenset({"setTimeout", "setInterval", "window.setTimeout", "window.setInterval"})
FUNCTION_LITERALS = frozenset({"arrow_function", "function_expression", "function"})
THIS_BINDING_METHODS = frozenset(
    {
        "each",
        "on",
        "attr",
        "style",
        "property",
        "classed",
        "text",
        "html",
        "filter",
        "select",
        "selectAll",
        "append",
        "insert",
        "datum",
        "tween",
        "attrTween",
        "styleTween",
    }
)
"""Methods whose callback runs with `this` set to an element or a chart: D3's selection and transition methods (`each`,
`on`: 47 catalogue callbacks hand `this` to `d3.select`) and ECharts' `on`. An array's `map` or `forEach`, a timer and
D3's `call` run a plain function with `this` undefined, which a classic script reads as the window."""
URL_MEMBERS = frozenset({"src", "href"})
"""Members a write may set only to a data URL the code drew (`canvas.toDataURL()`): an image's source, a link's target."""
NAVIGATION_MEMBERS = frozenset({"location", "action", "cookie", "srcdoc", "formAction"})
"""Members never written: a navigation, a form's target, a cookie, a frame's document."""
URL_ATTRIBUTES = frozenset({"src", "href", "xlink:href"})
NAVIGATION_ATTRIBUTES = frozenset({"action", "formaction", "srcdoc"})
MARKUP_MEMBERS = frozenset({"innerHTML", "outerHTML"})
"""Members a direct write may set (line-parametric's Chart.js legend) but a key that hides its name may not
(`Object.assign(el, { innerHTML })`, `el["inner" + "HTML"] = s`), since the hiding is the evasion."""
REACT_MARKUP = "dangerouslySetInnerHTML"
WRITE_CHECKED = URL_MEMBERS | NAVIGATION_MEMBERS | URL_ATTRIBUTES | NAVIGATION_ATTRIBUTES | MARKUP_MEMBERS
"""The names a write must not reach through a key that hides them: an object handed to `Object.assign` or to an
attribute setter, a key built from strings (Copilot review of #12473, second round)."""
HANDLER = re.compile(r"on[a-z]+", re.I)
"""An inline event handler's name (`onerror`), whose attribute compiles its string as code; a property of that name
takes only a function. The catalogue's chart options carry such keys (`onZero` 34, `onClick` 16 times), so they are
checked only where they are written onto an element."""
ATTRIBUTE_SETTERS = frozenset({"attr", "setAttribute", "setAttributeNS"})
"""D3's `attr` and the DOM's setters, which write an attribute by its name (the name is the first argument, the second
for `setAttributeNS`)."""
DRAWN_URL = "toDataURL"
"""The canvas method whose result is the one URL a plot may write: an image the code drew itself (the catalogue's raster
heatmaps, `heatmap-mandelbrot` and `recurrence-basic` in D3)."""
WRITE_METHODS = frozenset({"write", "writeln"})
"""`document.write` and `writeln` on any receiver: they write markup that runs, and a document reached by another route
(`el.ownerDocument`) would bypass `DOCUMENT_MEMBERS`."""
STRING_BUILDERS = frozenset(
    {
        "join",
        "concat",
        "fromCharCode",
        "fromCodePoint",
        "replace",
        "replaceAll",
        "repeat",
        "padStart",
        "padEnd",
        "atob",
        "decodeURIComponent",
        "decodeURI",
        "unescape",
        "toLowerCase",
        "toUpperCase",
        "trim",
        "normalize",
    }
)
"""Calls that build a string from parts, refused as a computed key (`[][["con", "structor"].join("")]`); the catalogue's
keys that a call computes are numbers and lookups (`Math.floor`, `indexOf`, `index()`, `String(col)`)."""
MUTATING_METHODS = frozenset(
    {
        "push",
        "pop",
        "shift",
        "unshift",
        "splice",
        "sort",
        "reverse",
        "fill",
        "copyWithin",
        "set",
        "add",
        "delete",
        "clear",
    }
)
"""Methods that change the array, map or set they are called on: never on a token."""
MUTATING_OBJECT_CALLS = frozenset({"Object.assign", "Object.defineProperty", "Object.defineProperties"})
NAMESPACES = frozenset(
    {
        "http://www.w3.org/2000/svg",
        "http://www.w3.org/1999/xlink",
        "http://www.w3.org/1999/xhtml",
        "http://www.w3.org/XML/1998/namespace",
        "http://www.w3.org/2000/xmlns/",
    }
)
"""XML namespace URIs, which name a vocabulary and load nothing (`createElementNS`; 7 catalogue places)."""
LOGGED_MODULES = frozenset(
    {
        "react",
        "react-dom",
        "@mui/material",
        "@mui/x-charts",
        "@mui/x-charts-pro",
        "@mui/x-charts-premium",
        "@mui/icons-material",
        "@mui/lab",
        "@mui/system",
        "@emotion/react",
        "@emotion/styled",
        "d3",
        "chart.js",
        "echarts",
        "highcharts",
        "recharts",
        "plotly.js",
        "lodash",
        "axios",
        "fs",
        "path",
        "os",
        "http",
        "https",
        "net",
        "child_process",
        "process",
        "node",
    }
)
"""The closed vocabulary a `banned-import` finding's `module` label comes from (`?` for any other module), so the
attribution log never records a name the model made up."""
UNKNOWN_MODULE = "?"
RNG_DRAWS = re.compile(
    r"^d3\.random(?:Normal|LogNormal|Exponential|Gamma|Beta|Poisson|Binomial|Geometric|Pareto|Logistic|Weibull"
    r"|Cauchy|Bates|IrwinHall|Bernoulli)$"
)
"""D3's draws from distributions that fabricate data; `Math.random`, `d3.randomUniform`, `d3.randomInt`,
`d3.randomLcg` and `d3.shuffle` stay allowed for jitter and subsampling (R's and Julia's precedent)."""

_URL_IN_TEXT = re.compile(
    r"(?i)(?:https?|ftp|wss?)://|\b(?:file|data|blob|javascript):\S|(?:^|[\s\"'(=,])/{2,}[a-z0-9_\[%]"
)
"""The Python profile's URL rule (`validate._URL_IN_TEXT`) with the browser's schemes, and a protocol-relative URL
(`"//example.org/p?" + x`, which a page reads with its own scheme; review of JS-3) to any host since PB-2a
(`"//localhost/x"`, `"//127.0.0.1/x"`)."""
_MARKUP = re.compile(
    r"(?i)<\s*(?:script|iframe|frame|object|embed|link|meta|base|form|portal)\b|<[a-z][^>]*\son[a-z]+\s*="
)
"""An opening tag of `DENIED_TAGS` or a tag with an inline `on…=` handler; a closing `</script>` (a user's column name
can hold one) and plain text such as `onset = 3` run nothing."""
_DIRECTIVE_TEXT = re.compile(r"(?i)anyplot-orientation")
_HEX = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")
_WHITESPACE = re.compile(r"\s+")
_STATEMENT_PARENTS = frozenset({"program", "statement_block", "switch_case", "switch_default"})
_WRITES = frozenset({"assignment_expression", "augmented_assignment_expression"})


def validate_security(code: str, *, library: str = "chartjs") -> list[Finding]:
    """The SECURITY profile (module docstring); never raises."""
    source, findings = _parse(code, library)
    if source is None:
        return findings
    scan = _Scan(source, library)
    scan.security()
    return scan.result()


def validate_adaptation(code: str, *, original_palette: list[str], library: str = "chartjs") -> list[Finding]:
    """The ADAPTATION profile: one placeholder, no fabricated data, the palette prefix kept, imports MUI X has."""
    source, findings = _parse(code, library)
    if source is None:
        return findings
    scan = _Scan(source, library)
    scan.adaptation(original_palette)
    return scan.result()


def module_label(specifier: str) -> str:
    """The label of a module specifier for the attribution log: its package when that is in `LOGGED_MODULES`, else
    `?`. The specifier is code the model wrote, so only a word of the closed vocabulary is logged."""
    if specifier.startswith("node:"):
        return "node"
    parts = specifier.split("/")
    name = "/".join(parts[:2]) if specifier.startswith("@") else parts[0]
    return name if name in LOGGED_MODULES else UNKNOWN_MODULE


def _parse(code: str, library: str) -> tuple[Source | None, list[Finding]]:
    """Size, encoding and syntax: the checks that run before any rule can."""
    if len(code) > MAX_CODE_CHARS:
        return None, [Finding("size", f"code is {len(code):,} characters; the limit is {MAX_CODE_CHARS:,}", None)]
    try:
        code.encode("utf-8")
    except UnicodeEncodeError:
        return None, [Finding("encoding", "code is not valid UTF-8 text", None)]
    source = Source(code, grammar_for(library))
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        return None, [Finding("syntax", f"syntax error: {problems[0].message()}", problems[0].line)]
    return source, []


def _snippet(source: Source, node: Node) -> str:
    """At most `MAX_SNIPPET_CHARS` of a node's code on one line, its string literals shown as `"..."`."""
    data = source.data
    parts: list[str] = []
    cursor = node.start_byte
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type in JS_STRINGS or current.type == "jsx_text":
            parts.append(data[cursor : current.start_byte].decode("utf-8", "replace") + '"..."')
            cursor = current.end_byte
            continue
        stack.extend(reversed(current.children))
    parts.append(data[cursor : node.end_byte].decode("utf-8", "replace"))
    text = _WHITESPACE.sub(" ", "".join(parts)).strip()
    return text if len(text) <= MAX_SNIPPET_CHARS else text[: MAX_SNIPPET_CHARS - 3] + "..."


def string_text(source: Source, node: Node) -> str:
    """A string's or template's value when it has one, else the text of its literal parts (a template with a
    substitution), or JSX text: what a URL, markup or length check reads."""
    if node.type == "jsx_text":
        return source.text(node)
    value = js_string(source, node)
    if value is not None:
        return value
    return "".join(
        source.text(child) for child in node.children if child.type in ("string_fragment", "escape_sequence")
    )


def _own_this(node: Node) -> bool:
    """Whether `this` at `node` is bound by a function around it: a non-arrow function, a method or a class body."""
    return _this_owner(node) is not None


def _this_owner(node: Node) -> Node | None:
    """The node that binds `this` at `node`: the nearest function that is no arrow function (an arrow reads its
    surroundings' `this`), or a class body; None at the top level."""
    current = node.parent
    while current is not None:
        if current.type in JS_FUNCTIONS and current.type != "arrow_function":
            return current
        if current.type in ("class_body", "class_static_block"):
            return current
        current = current.parent
    return None


def _holder(node: Node) -> Node | None:
    """`node`'s parent past any parentheses."""
    parent = node.parent
    while parent is not None and parent.type == "parenthesized_expression":
        parent = parent.parent
    return parent


def _is_object_of(node: Node, holder: Node | None) -> bool:
    """Whether `node` (or its parenthesised form) is the object `holder`, a member access or index, reads from."""
    if holder is None or holder.type not in ("member_expression", "subscript_expression"):
        return False
    inner = js_object(holder)
    return inner is not None and js_unwrap(inner).id == node.id


def key_parts(source: Source, node: Node) -> list[str | None] | None:
    """The fragments of a key that code builds from strings, `None` standing for a part only the run knows: a `+` chain
    with a string or template operand (`m + "Norm"` is `[None, "Norm"]`) or a template with a substitution
    (`` `z_${v}` `` is `["z_", None]`); None for any other key (a name, a literal, a number, arithmetic) and for one
    without a written fragment (`` `${file}${rank}` ``, `"" + x`), which is as opaque as a name (chessboard-pieces'
    squares in Highcharts)."""
    node = js_unwrap(node)
    if node.type == "template_string":
        if not any(child.type == "template_substitution" for child in node.children):
            return None
        parts: list[str | None] = []
        for child in node.children:
            if child.type == "string_fragment":
                parts.append(source.text(child))
            elif child.type in ("template_substitution", "escape_sequence"):
                parts.append(None)  # an escape reads as any text: the pattern only widens
        return parts if any(parts) else None
    if node.type != "binary_expression":
        return None
    operands: list[Node] = []
    stack = [node]
    while stack:  # the `+` chain's operands, left to right, without recursion
        current = js_unwrap(stack.pop())
        operator = current.child_by_field_name("operator") if current.type == "binary_expression" else None
        if operator is not None and source.text(operator) == "+":
            stack += [
                child for child in (current.child_by_field_name("right"), current.child_by_field_name("left")) if child
            ]
        else:
            operands.append(current)
    if not any(operand.type in ("string", "template_string") for operand in operands):
        return None
    found: list[str | None] = []
    for operand in operands:
        literal = js_string(source, operand) if operand.type in ("string", "template_string") else None
        if literal is None and operand.type == "number":
            literal = source.text(operand)
        if literal is not None:
            found.append(literal)
        elif operand.type == "template_string":
            found += key_parts(source, operand) or [None]
        else:
            found.append(None)
    return found if any(found) else None


def could_spell(parts: list[str | None], names: frozenset[str]) -> bool:
    """Whether a key built from `parts` (`key_parts`) could be one of `names` once the run fills in the unknown parts."""
    pattern = re.compile("".join(".*" if part is None else re.escape(part) for part in parts), re.S)
    return any(pattern.fullmatch(name) for name in names)


def could_be_handler(parts: list[str | None]) -> bool:
    """Whether a key built from `parts` spells an inline handler's name, `on` and letters (`HANDLER`), by its written
    fragments: they are letters only and begin with `on` (`"on" + name`). A key whose start only the run knows
    (chernoff-basic's `r[m + "Norm"]`) is no handler by its fragments."""
    if any(part is not None and not re.fullmatch(r"[A-Za-z]*", part) for part in parts):
        return False
    head = "".join(part for part in parts[: parts.index(None)] if part is not None) if None in parts else ""
    if None not in parts:
        return HANDLER.fullmatch("".join(part for part in parts if part is not None)) is not None
    return head.lower().startswith("on")


def fold_string(source: Source, node: Node) -> str | None:
    """The string a key is when its literals decide it: a string, a `+` chain of strings and numbers, `[...].join(...)`
    of strings with a written separator, `String.fromCharCode(...)` of numbers; None when the run decides it."""
    node = js_unwrap(node)
    text = js_string(source, node)
    if text is not None:
        return text
    if node.type == "binary_expression":
        parts = key_parts(source, node)
        return "".join(part for part in parts if part is not None) if parts and None not in parts else None
    if node.type != "call_expression":
        return None
    function = js_unwrap(node.child_by_field_name("function") or node)
    method = js_property(source, function) if function.type in ("member_expression", "subscript_expression") else None
    arguments = js_arguments(node)
    receiver = js_object(function)
    if method == "join" and receiver is not None and js_unwrap(receiver).type == "array" and len(arguments) <= 1:
        items = [fold_string(source, item) for item in js_named(js_unwrap(receiver))]
        separator = fold_string(source, arguments[0]) if arguments else ","
        if separator is None or any(item is None for item in items):
            return None
        return separator.join(item for item in items if item is not None)
    if method in ("fromCharCode", "fromCodePoint") and receiver is not None and source.text(receiver) == "String":
        codes = [js_number(source, item) for item in arguments]
        if any(code is None or not 0 <= code <= 0x10FFFF or code != int(code) for code in codes):
            return None
        return "".join(chr(int(code)) for code in codes if code is not None)
    return None


class _Scan:
    """One validation pass over a parsed JavaScript or TSX source."""

    def __init__(self, source: Source, library: str) -> None:
        self.source = source
        self.library = library
        self.module = library in TSX_LIBRARIES
        own_global = LIBRARY_GLOBALS.get(library)
        self.globals = GLOBALS | ({own_global} if own_global else set())
        self.findings: list[Finding] = []
        self.regions: Regions = find_regions(source)
        self.bindings: list[JsBinding] = js_bindings(source, source.root)
        self.references: list[JsReference] = js_references(source, source.root, self.bindings)
        self.resolved = {reference.visit.node.id: reference.binding for reference in self.references}
        self.token_bindings = {
            binding.node.id: binding.name
            for region in self.regions.theme_tokens
            for binding in self.bindings
            if region.statement is not None
            and binding.scope.type == "program"
            and region.statement.start <= source.char(binding.node.start_byte) < region.statement.end
        }
        """The top-level bindings the token lines make, by node, with their region's name."""

    # -- bookkeeping ---------------------------------------------------------------------

    def add(self, rule: str, message: str, node: Node | None, *, module: str | None = None) -> None:
        line = first_line(node) if node is not None else None
        self.findings.append(Finding(rule, message[:MAX_MESSAGE_CHARS], line, module))

    def result(self) -> list[Finding]:
        unique = dict.fromkeys(self.findings)
        return sorted(unique, key=lambda f: (f.line is None, f.line or 0, f.rule, f.message))

    def snippet(self, node: Node) -> str:
        return _snippet(self.source, node)

    def is_free(self, node: Node) -> bool:
        """Whether an identifier reads a name the file does not bind around it (a global)."""
        return node.id in self.resolved and self.resolved[node.id] is None

    def token_of(self, node: Node) -> str | None:
        """The token an identifier reads: the name, when it resolves to a token line's own binding, else None (a
        parameter or a local that shadows the token reads something else)."""
        binding = self.resolved.get(node.id)
        if binding is None or binding.node.id not in self.token_bindings:
            return None
        return binding.name

    def page_object(self, node: Node | None) -> str | None:
        """`window` or `document` when `node` is that free name, else None."""
        if node is None:
            return None
        node = js_unwrap(node)
        if node.type != "identifier" or not self.is_free(node):
            return None
        name = self.source.text(node)
        return name if name in PAGE_OBJECTS else None

    # -- SECURITY ------------------------------------------------------------------------

    def security(self) -> None:
        for reference in self.references:
            if not reference.bound:
                self.check_free(reference)
        for node in walk(self.source.root):
            kind = node.type
            if kind in ("member_expression", "subscript_expression"):
                self.check_member(node)
            elif kind in ("call_expression", "new_expression"):
                self.check_call(node)
            elif kind == "import":
                self.check_dynamic_import(node)
            elif kind == "meta_property":
                self.add("banned-call", "import.meta and new.target are not allowed", node)
            elif kind in ("import_statement", "export_statement"):
                self.check_module_statement(node)
            elif kind == "with_statement":
                self.add("banned-statement", "a with statement turns an object into scope; name what you read", node)
            elif kind == "this":
                self.check_this(node)
            elif kind in ("jsx_opening_element", "jsx_self_closing_element"):
                self.check_jsx_element(node)
            elif kind == "jsx_attribute":
                self.check_jsx_attribute(node)
            elif kind in ("pair_pattern", "shorthand_property_identifier_pattern"):
                self.check_destructured_key(node)
            elif kind == "pair":
                self.check_pair(node)
            if kind in ("string", "template_string", "jsx_text"):
                self.check_text(node)
            elif kind in COMMENTS:
                self.check_comment(node)
        self.check_directive()
        self.check_bindings()
        self.check_token_writes()
        self.check_alone()

    def check_free(self, reference: JsReference) -> None:
        node, name = reference.visit.node, reference.name
        if name in DENIED_NAMES:
            self.add("banned-name", f"'{name}' is not allowed: the plot reaches no {DENIED_NAMES[name]}", node)
        elif name not in self.globals:
            library = next((lib for lib, value in LIBRARY_GLOBALS.items() if value == name), None)
            if library is not None:
                self.add("banned-name", f"'{name}' is {library}'s global, which this page does not load", node)
            else:
                self.add("banned-name", f"'{name}' is neither bound by the code nor a global the page provides", node)
        elif name in PAGE_OBJECTS and not self.is_member_object(reference.visit):
            self.add("banned-name", f"'{name}' is only ever the object of a member access, as in {name}.name", node)

    def is_member_object(self, visit: Visit) -> bool:
        """Whether the identifier of a visit is the object of a member access or index (`window.x`, `window[...]`)."""
        node: Node = visit.node
        parent = node.parent
        while parent is not None and parent.type == "parenthesized_expression":
            node, parent = parent, parent.parent
        if parent is None or parent.type not in ("member_expression", "subscript_expression"):
            return False
        inner = js_object(parent)
        return inner is not None and inner.id == node.id

    def check_member(self, node: Node) -> None:
        name = js_property(self.source, node)
        inner = js_object(node)
        owner = self.page_object(inner)
        if node.type == "subscript_expression" and name is None:
            if owner is not None:
                self.add("banned-name", f"{owner}[...] reads a member that code computes; name the member", node)
            else:
                index = node.child_by_field_name("index")
                if index is not None:
                    self.check_computed_key(index, node)
            return
        if name is None:
            return
        if name in DENIED_MEMBERS:
            self.add("banned-name", f"the member '{name}' is not allowed: it leads to code, frames or the window", node)
        if self.is_written(node) and (name in NAVIGATION_MEMBERS or name in URL_MEMBERS):
            assignment = node.parent
            value = assignment.child_by_field_name("right") if assignment is not None else None
            if name in NAVIGATION_MEMBERS or value is None or not self.drawn_url(value):
                message = f"'.{name}' is written only with a data URL the code drew (canvas.toDataURL())"
                if name in NAVIGATION_MEMBERS:
                    message = f"'.{name}' is never written: it navigates, submits or sets a cookie"
                self.add("banned-statement", message, node)
        if owner == WINDOW:
            if name == DATA_GLOBAL:
                self.add("banned-name", f"the data comes from {PLACEHOLDER}, never from {WINDOW}.{DATA_GLOBAL}", node)
            elif name not in WINDOW_MEMBERS:
                self.add(
                    "banned-name", f"'{WINDOW}.{name}' is not allowed; the plot reads only the render context", node
                )
            elif name not in WINDOW_WRITABLE and self.is_written(node):
                self.add("banned-statement", f"'{WINDOW}.{name}' is the harness's and is never written", node)
        elif owner == DOCUMENT and name not in DOCUMENT_MEMBERS:
            self.add("banned-name", f"'{DOCUMENT}.{name}' is not allowed; the plot only finds and makes elements", node)
        elif inner is not None and js_unwrap(inner).type == "identifier" and self.is_free(js_unwrap(inner)):
            root = self.source.text(js_unwrap(inner))
            if root == "Object" and name not in OBJECT_MEMBERS:
                self.add("banned-name", f"'Object.{name}' is not allowed; use Object.keys, entries or assign", node)
            elif name in LIBRARY_DENIED.get(root, frozenset()):
                self.add("banned-name", f"'{root}.{name}' loads a URL; the data comes from {PLACEHOLDER}", node)

    def is_written(self, node: Node) -> bool:
        """Whether a member access is the target of an assignment, an update or a `delete`."""
        parent = node.parent
        if parent is None:
            return False
        if parent.type in _WRITES:
            left = parent.child_by_field_name("left")
            return left is not None and left.id == node.id
        if parent.type == "update_expression":
            return True
        if parent.type == "unary_expression":
            operator = parent.child_by_field_name("operator")
            return operator is not None and self.source.text(operator) == "delete"
        return False

    def check_call(self, node: Node) -> None:
        name = self.callee_name(node)
        arguments = js_arguments(node)
        method = self.method_of(node)
        if name in TIMERS:
            first = js_unwrap(arguments[0]) if arguments else None
            if first is None or not (first.type in FUNCTION_LITERALS or self.is_local_function(first)):
                message = f"{name} runs only a function written in place or declared in the file; a string runs as code"
                self.add("banned-call", message, node)
        if name in TAG_CREATORS or method in TAG_METHODS or name in JSX_RUNTIME:
            position = 1 if name.endswith("NS") or method == "createElementNS" else 0
            tag = js_unwrap(arguments[position]) if len(arguments) > position else None
            texts = self.literal_values(tag) if tag is not None else []
            if not texts:
                if name in TAG_CREATORS:
                    self.add("banned-call", f"{name} takes the tag as a literal", node)
            elif any(text.rsplit(":", 1)[-1].strip().lower() in DENIED_TAGS for text in texts):
                self.add("banned-call", "an element that runs code, loads a resource or submits is not allowed", node)
        if method in WRITE_METHODS and name != method:
            self.add("banned-call", f".{method}() writes markup that runs; build the elements instead", node)
        if method in ATTRIBUTE_SETTERS and arguments and name != method:  # a member's setter, not a function `attr`
            if len(arguments) == 1:  # Highcharts' `el.attr({ href: url })` sets every key as an attribute
                self.check_written_source(arguments[0], node, attribute=True)
            else:
                self.check_attribute_write(node, method, arguments)
        if name == "Object.assign" and arguments and js_unwrap(arguments[0]).type != "object":
            for written in arguments[1:]:  # onto an existing value, maybe an element; a fresh `{}` target is data
                self.check_written_source(written, node, attribute=False)
        if name in MUTATING_OBJECT_CALLS and arguments and self.token_root(arguments[0]) is not None:
            token = self.token_root(arguments[0])
            self.add("banned-statement", f"the theme token {token} is read only; copy it before changing it", node)
        function = node.child_by_field_name("function")
        if function is not None and node.type == "call_expression":
            unwrapped = js_unwrap(function)
            method = js_property(self.source, unwrapped) if unwrapped.type != "identifier" else None
            inner = js_object(unwrapped)
            token = self.token_root(inner) if inner is not None else None
            if method in MUTATING_METHODS and token is not None:
                self.add("banned-statement", f"the theme token {token} is read only; copy it before changing it", node)

    def method_of(self, call: Node) -> str | None:
        """The member a call calls (`append` in `svg.append("g")`, `createElement` in `React.createElement(...)`), or
        the name of a plain call (`createElement` imported from React); None otherwise."""
        if call.type != "call_expression":
            return None
        function = call.child_by_field_name("function")
        unwrapped = js_unwrap(function) if function is not None else None
        if unwrapped is None:
            return None
        if unwrapped.type == "identifier":
            return self.source.text(unwrapped)
        # `el["setAttribute"](...)` calls the member it names, as `el.setAttribute(...)` does (Copilot review of #12473)
        if unwrapped.type in ("member_expression", "subscript_expression"):
            return js_property(self.source, unwrapped)
        return None

    def callee_name(self, call: Node) -> str:
        """The dotted name a call or `new` calls, a literal index read as the member it names (`d3["create"]` is
        `d3.create`, `document["createElement"]` is `document.createElement`); `""` for a callee code computes."""
        name = js_callee(self.source, call)
        if name is not None:
            return name
        function = call.child_by_field_name("function" if call.type == "call_expression" else "constructor")
        parts: list[str] = []
        current = js_unwrap(function) if function is not None else None
        for _ in range(1000):  # a chain of members; the bound only guards a pathological file
            if current is None or current.type not in ("member_expression", "subscript_expression"):
                break
            member = js_property(self.source, current)
            inner = js_object(current)
            if member is None or inner is None:
                return ""
            parts.append(member)
            current = js_unwrap(inner)
        if current is None or current.type != "identifier":
            return ""
        return ".".join([self.source.text(current), *reversed(parts)])

    def binding_value(self, node: Node) -> Node | None:
        """The value a name was declared with (`const tag = "iframe"`), for a name that resolves to a declarator."""
        binding = self.resolved.get(node.id) if node.type == "identifier" else None
        declaration = binding.declaration if binding is not None else None
        if declaration is None or declaration.type != "variable_declarator":
            return None
        name = declaration.child_by_field_name("name")
        if name is None or name.type != "identifier":
            return None
        return declaration.child_by_field_name("value")

    def is_const(self, node: Node) -> bool:
        """Whether a name resolves to a `const` declaration, which no later write can change."""
        binding = self.resolved.get(node.id) if node.type == "identifier" else None
        return binding is not None and binding.kind == "const"

    def literal_values(self, node: Node) -> list[str]:
        """The strings a value can be when literals decide it: a string, either branch of a ternary of strings, or a
        `const` declared with one (`const tag = "iframe"`); [] when code decides it."""
        found: list[str] = []
        stack = [node]
        for _ in range(100):  # names lead to names; the bound only guards a pathological file
            if not stack:
                break
            current = js_unwrap(stack.pop())
            text = js_string(self.source, current)
            if text is not None:
                found.append(text)
            elif current.type == "ternary_expression":
                stack += [
                    branch
                    for branch in (
                        current.child_by_field_name("consequence"),
                        current.child_by_field_name("alternative"),
                    )
                    if branch is not None
                ]
            elif current.type == "identifier" and self.is_const(current):  # a `let` may be given another value later
                value = self.binding_value(current)
                if value is not None:
                    stack.append(value)
        return found

    def drawn_url(self, value: Node) -> bool:
        """Whether a value is a data URL the code drew: a `toDataURL()` call, or a `const` declared with one."""
        value = js_unwrap(value)
        if value.type == "identifier":
            inner = self.binding_value(value)
            return self.is_const(value) and inner is not None and self.drawn_url(inner)
        return value.type == "call_expression" and self.method_of(value) == DRAWN_URL

    def is_local_function(self, node: Node) -> bool:
        """Whether a name is a function the file declares (`function draw() {}`, `const draw = () => ...`) and never
        writes again, so a timer cannot be handed a string under its name."""
        binding = self.resolved.get(node.id) if node.type == "identifier" else None
        if binding is None:
            return False
        if binding.kind == "function" and binding.declaration.type in (
            "function_declaration",
            "generator_function_declaration",
        ):
            return not any(
                self.resolved.get(target.id) is binding
                for target in self.write_targets()
                if target.type == "identifier"
            )
        value = self.binding_value(node)
        return binding.kind == "const" and value is not None and js_unwrap(value).type in FUNCTION_LITERALS

    def write_targets(self) -> list[Node]:
        """The targets of every assignment and update in the file."""
        targets: list[Node] = []
        for current in walk(self.source.root):
            if current.type in _WRITES:
                target = current.child_by_field_name("left")
            elif current.type == "update_expression":
                target = current.child_by_field_name("argument")
            else:
                continue
            if target is not None:
                targets.append(js_unwrap(target))
        return targets

    def check_attribute_write(self, node: Node, method: str, arguments: list[Node]) -> None:
        """`el.setAttribute("href", v)`, `sel.attr("src", v)`: a URL attribute takes only a data URL the code drew, and
        a navigation attribute nothing."""
        position = 1 if method == "setAttributeNS" else 0
        if len(arguments) <= position + 1:
            return
        names = self.literal_values(arguments[position])
        if not names:
            # A name code computes could be any of them; no catalogue file computes one (Copilot review of #12473).
            self.add("banned-call", f"{method} takes the attribute's name as a literal", node)
            return
        for name in sorted(set(names)):  # every name a ternary may pick, not only the first
            self.check_written_name(name, arguments[position + 1], node, attribute=True)

    def check_written_name(self, name: str, value: Node | None, node: Node, *, attribute: bool) -> None:
        """One name a write sets on an element, as an attribute (`setAttribute`, D3's and Highcharts' `attr`, any case)
        or as a property (`Object.assign(el, {...})`): a navigation, a form's target, a cookie or a frame's document
        never; a URL only as a data URL the code drew; markup by a hidden name never; an inline handler never as an
        attribute, which compiles its string, and as a property only with a function written in place."""
        key = name.strip()
        folded = key.lower()
        if (
            folded in NAVIGATION_ATTRIBUTES
            or key in NAVIGATION_MEMBERS
            or (attribute and folded in {"location", "cookie"})
        ):
            self.add(
                "banned-call", f"'{key}' is never set: it navigates, submits, sets a cookie or holds a document", node
            )
        elif folded in URL_ATTRIBUTES or key in URL_MEMBERS:
            if value is None or not self.drawn_url(value):
                message = f"'{key}' takes only a data URL the code drew (canvas.toDataURL())"
                self.add("banned-call", message, node)
        elif key in MARKUP_MEMBERS or key == REACT_MARKUP:
            self.add("banned-call", f"'{key}' set through an object writes markup that runs; write the elements", node)
        elif attribute and HANDLER.fullmatch(key):
            self.add("banned-call", f"the attribute '{key}' compiles its text as code; add a listener instead", node)
        elif not attribute and re.fullmatch(r"on[a-z]+", key):
            literal = value is not None and js_unwrap(value).type in FUNCTION_LITERALS
            if not literal:
                self.add("banned-call", f"'{key}' takes only a function written in place", node)

    def check_written_source(self, source: Node, node: Node, *, attribute: bool) -> None:
        """The names an object writes onto an element: an `Object.assign` source or a Highcharts `attr({...})` object, a
        `const` that holds one, and the objects spread into it (Copilot review of #12473: `Object.assign(el, { href:
        url })` set what `el.href = url` may not)."""
        stack = [source]
        for _ in range(100):  # objects lead to objects; the bound only guards a pathological file
            if not stack:
                return
            current = js_unwrap(stack.pop())
            if current.type == "identifier" and self.is_const(current):
                value = self.binding_value(current)
                if value is not None:
                    stack.append(value)
                continue
            if current.type != "object":
                continue
            for part in js_named(current):
                if part.type == "spread_element":
                    stack += js_named(part)[:1]
                elif part.type == "shorthand_property_identifier":
                    self.check_written_name(self.source.text(part), part, node, attribute=attribute)
                elif part.type == "method_definition":
                    method_name = part.child_by_field_name("name")
                    if method_name is not None and method_name.type == "property_identifier":
                        self.check_written_name(self.source.text(method_name), part, node, attribute=attribute)
                elif part.type == "pair":
                    key, value = part.child_by_field_name("key"), part.child_by_field_name("value")
                    if key is None:
                        continue
                    if key.type == "computed_property_name":
                        inner = js_named(key)
                        names = self.literal_values(inner[0]) if inner else []
                    elif key.type == "property_identifier":
                        names = [self.source.text(key)]
                    else:
                        names = [text] if (text := js_string(self.source, key)) is not None else []
                    for name in names:
                        self.check_written_name(name, value, node, attribute=attribute)

    def check_computed_key(self, index: Node, node: Node) -> None:
        """A key that code builds from strings must not be able to spell a member of `DENIED_MEMBER_STRINGS` or React's
        `dangerouslySetInnerHTML`, and a key that a string builder returns (`.join()`, `String.fromCharCode(...)`) is
        refused (review of JS-3). A written key (`el[k] = v`) and an object literal's computed key (`{ [k]: v }`, which
        `Object.assign` or a spread can write onto an element) must not be able to spell a name of `WRITE_CHECKED` or an
        inline handler either (Copilot review of #12473). A name used as the key is judged by the values the file gives
        it (`const k = "con" + "structor"; [][k]`)."""
        unwrapped = js_unwrap(index)
        values: list[Node | None] = [unwrapped]
        binding = self.resolved.get(unwrapped.id) if unwrapped.type == "identifier" else None
        if binding is not None:
            values = [self.binding_value(unwrapped)]
            for write in walk(self.source.root):
                left = write.child_by_field_name("left") if write.type == "assignment_expression" else None
                if left is not None and self.resolved.get(js_unwrap(left).id) is binding:
                    values.append(write.child_by_field_name("right"))
        pair = node.type == "pair"
        written = pair or (node.type == "subscript_expression" and self.is_written(node))
        for value in (js_unwrap(value) for value in values if value is not None):
            folded = fold_string(self.source, value)  # also a `const` key's literal (`const k = "href"; el[k] = u`)
            parts: list[str | None] | None = [folded] if folded is not None else key_parts(self.source, value)
            if parts is not None and could_spell(parts, DENIED_MEMBER_STRINGS | {REACT_MARKUP}):
                message = "a key built from strings could name a member that leads to code; name the key"
                self.add("banned-name", message, node)
            elif written and parts is not None and (could_spell(parts, WRITE_CHECKED) or could_be_handler(parts)):
                message = "a write by a key built from strings could set a URL, markup or a handler; name the member"
                self.add("banned-statement", message, node)
            elif not pair and folded is None and self.method_of(value) in STRING_BUILDERS:
                # An object literal's key from a builder the run decides passes: two MUI X files build `sx` selectors
                # that way (andrews-curves, bar-diverging-likert); its fragments are checked where they are written.
                self.add("banned-name", "a key a string builder returns could name any member; name the key", node)

    def token_root(self, node: Node) -> str | None:
        """The token a value's chain starts from (`t` in `t.palette[0]`, `window.ANYPLOT_TOKENS` in
        `window.ANYPLOT_TOKENS.ink`), else None."""
        first: Node | None = None
        current = js_unwrap(node)
        for _ in range(1000):  # a chain of members and indexes; the bound only guards a pathological file
            inner = js_object(current)
            if inner is None:
                break
            first, current = current, js_unwrap(inner)
        if current.type != "identifier":
            return None
        token = self.token_of(current)
        if token is not None:
            return token
        if self.source.text(current) == WINDOW and self.is_free(current) and first is not None:
            prop = js_property(self.source, first)
            return f"{WINDOW}.{prop}" if prop in TOKEN_GLOBALS else None
        return None

    def check_dynamic_import(self, node: Node) -> None:
        parent = node.parent
        if parent is not None and parent.type == "call_expression":
            self.add("banned-call", "import(...) loads code at run time; the plot loads none", parent)

    def check_module_statement(self, node: Node) -> None:
        source_node = node.child_by_field_name("source")
        if node.type == "export_statement" and source_node is None:
            if not self.module:
                self.add("banned-import", "a classic script exports nothing; the harness runs it as it stands", node)
            return
        if not self.module:
            global_name = LIBRARY_GLOBALS.get(self.library)
            message = f"a {self.library} snippet imports nothing; the library is the page's global {global_name}"
            self.add("banned-import", message, node, module=UNKNOWN_MODULE)
            return
        if any(child.type == "import_require_clause" for child in js_named(node)):
            self.add("banned-import", "import ... = require(...) is not allowed; import from the allowlist", node)
            return
        specifier = js_string(self.source, source_node) if source_node is not None else None
        if specifier is None:
            return
        if package_of(specifier) is None:
            allowed = ", ".join(sorted(packages()))
            message = f"the module '{specifier}' is not available; a MUI X snippet imports only from {allowed}"
            if specifier.startswith((".", "/")) or ":" in specifier:
                message = "relative, absolute, node: and URL imports are not allowed; import a package by its name"
            self.add("banned-import", message[:MAX_MESSAGE_CHARS], node, module=module_label(specifier))

    def check_this(self, node: Node) -> None:
        if not _own_this(node):
            self.add("banned-name", "'this' outside a function is the window; name what you read", node)
            return
        holder = _holder(node)
        if _is_object_of(node, holder):
            assert holder is not None
            # In every context, known or not: a method handed to a browser callback (`addEventListener("load", o.m)`, a
            # timer, a promise) runs with the window as `this` (Copilot review of #12473, second round). No catalogue
            # file reads a window-only member or a computed key on `this`; `this.chart`, `this.point` and `this.x` stay.
            name = js_property(self.source, holder)
            if name in DENIED_NAMES:
                self.add("banned-name", f"'this.{name}' is not allowed: the plot reaches no {DENIED_NAMES[name]}", node)
            elif name is None:
                self.add("banned-name", "this[...] may read the window by a computed key; name the member", node)
            elif name in PAGE_OBJECTS:
                message = f"'this.{name}' may read the page's {name} past its rules; name what you read"
                self.add("banned-name", message, node)
        elif not self.this_is_known(node):
            message = "'this' here may be the window (a function called without a receiver); pass what you need"
            self.add("banned-name", message, node)

    def this_is_known(self, node: Node) -> bool:
        """Whether `this` at `node` is an element, a chart or an object, never the window (review of JS-3).

        In a classic script a plain function called without a receiver (`g()`, an array's
        `map` or `forEach`, a timer, D3's `call`) sees the window as `this`. It is known where
        the function that binds it is a method or a class member; the value of an object's
        key (a library callback: Highcharts' `load` and `formatter`, Chart.js' callbacks); a
        callback of `THIS_BINDING_METHODS` (D3's `each` and `on`); or a function declared, or
        bound to a `const`, whose name the file only hands to those (`events: { load:
        drawAll }`). Elsewhere `this` may be read through a member it names, never as a
        value. An arrow function reads its surroundings' `this`.
        """
        owner = _this_owner(node)
        if owner is None:
            return False
        if owner.type in ("method_definition", "class_body", "class_static_block"):
            return True
        holder = _holder(owner)
        if holder is None:
            return False
        if holder.type == "pair" or (holder.type == "arguments" and self.binds_this(holder.parent)):
            return True
        name: Node | None = None
        if owner.type in ("function_declaration", "generator_function_declaration"):
            name = owner.child_by_field_name("name")
        elif holder.type == "variable_declarator" and self.declaration_kind(holder) == "const":
            name = holder.child_by_field_name("name")
        return name is not None and name.type == "identifier" and self.only_handed_on(name)

    def binds_this(self, call: Node | None) -> bool:
        """Whether a call runs its callback with `this` set (`THIS_BINDING_METHODS` on any receiver)."""
        return call is not None and call.type == "call_expression" and self.method_of(call) in THIS_BINDING_METHODS

    def declaration_kind(self, declarator: Node) -> str | None:
        """`const`, `let` or `var` of a `variable_declarator`."""
        return next((binding.kind for binding in self.bindings if binding.declaration.id == declarator.id), None)

    def only_handed_on(self, name: Node) -> bool:
        """Whether every read of the function `name` binds hands it to a caller that sets `this`: as an object's value
        (`{ load: drawAll }`, `{ drawAll }`) or as an argument of `THIS_BINDING_METHODS`."""
        for reference in self.references:
            binding = reference.binding
            if binding is None or binding.node.id != name.id:
                continue
            read = reference.visit.node
            holder = _holder(read)
            if read.type == "shorthand_property_identifier":
                continue
            if holder is not None and holder.type == "pair":
                value = holder.child_by_field_name("value")
                if value is not None and js_unwrap(value).id == read.id:
                    continue
            if holder is not None and holder.type == "arguments" and self.binds_this(holder.parent):
                continue
            return False
        return True

    def check_pair(self, node: Node) -> None:
        key = node.child_by_field_name("key")
        text = None
        if key is not None and key.type == "computed_property_name":
            inner = js_named(key)
            if inner:  # `{ ["dangerously" + "SetInnerHTML"]: ... }` (Copilot review of #12473)
                self.check_computed_key(inner[0], node)
            return
        if key is not None:
            text = self.source.text(key) if key.type == "property_identifier" else js_string(self.source, key)
        if text == REACT_MARKUP:
            self.add("banned-call", "dangerouslySetInnerHTML runs markup from a string; write the elements", node)

    def check_jsx_element(self, node: Node) -> None:
        name = node.child_by_field_name("name")
        if name is None or name.type != "identifier":
            return
        tag = self.source.text(name)
        if tag[:1].islower() and tag.lower() in DENIED_TAGS:
            self.add("banned-call", "an element that runs code, loads a resource or submits is not allowed", node)

    def check_jsx_attribute(self, node: Node) -> None:
        named = js_named(node)
        if named and self.source.text(named[0]) == "dangerouslySetInnerHTML":
            self.add("banned-call", "dangerouslySetInnerHTML runs markup from a string; write the elements", node)

    def check_destructured_key(self, node: Node) -> None:
        key = node.child_by_field_name("key") if node.type == "pair_pattern" else node
        text = None
        if key is not None and key.type == "computed_property_name":
            inner = js_named(key)
            if inner:
                self.check_computed_key(inner[0], node)
            return
        if key is not None:
            text = (
                self.source.text(key)
                if key.type in ("property_identifier", "shorthand_property_identifier_pattern")
                else js_string(self.source, key)
            )
        if text in DENIED_MEMBERS:
            self.add("banned-name", f"the member '{text}' is not allowed: it leads to code, frames or the window", node)

    def check_text(self, node: Node) -> None:
        value = string_text(self.source, node)
        if node.type != "jsx_text" and value in DENIED_MEMBER_STRINGS:
            self.add("banned-name", f"the member name '{value}' is not allowed as a string either", node)
        if node.type != "jsx_text" and value.rsplit(":", 1)[-1].strip().lower() in DENIED_TAG_STRINGS:
            self.add(
                "banned-call", "an element that runs code or loads a frame is not allowed, as a tag name either", node
            )
        if len(value) > MAX_STRING_CHARS:
            message = f"string literal of {len(value)} characters; the limit is {MAX_STRING_CHARS}"
            self.add("string-length", message, node)
        if value not in NAMESPACES and _URL_IN_TEXT.search(value):
            self.add("url-literal", "URL or file literal; the plot reads only its data", node)
        if _MARKUP.search(value):
            self.add("markup-code", "markup that runs code or loads a resource is not allowed in a string", node)
        if _DIRECTIVE_TEXT.search(value):
            self.add("savefig-target", "the orientation directive belongs on its own comment line, once", node)

    def check_comment(self, node: Node) -> None:
        text = self.source.text(node)
        if not _DIRECTIVE_TEXT.search(text):
            return
        own = {directive.line for directive in self.regions.directives if directive.comment}
        if text.startswith("/*") or first_line(node) not in own:
            self.add("savefig-target", "the orientation directive belongs on its own comment line, once", node)

    def check_directive(self) -> None:
        directives = self.regions.directives
        if not directives:
            self.add("savefig-target", "no //# anyplot-orientation directive; keep the one the code had", None)
        elif len(directives) > 1:
            self.add("savefig-target", "more than one orientation directive; keep the first one alone", None)

    def check_bindings(self) -> None:
        """Token names bound at the top level by their own line alone (a parameter or a local of the same name
        shadows the token inside its function and leaves it as it is); the page's objects and the library global
        never at the top level; `loadUserData` never bound."""
        own_global = LIBRARY_GLOBALS.get(self.library)
        protected_top = PAGE_OBJECTS | ({own_global} if own_global else set())
        token_names = set(self.token_bindings.values())
        for binding in self.bindings:
            name, node = binding.name, binding.node
            top = binding.scope.type == "program"
            if top and name in token_names and node.id not in self.token_bindings:
                self.add("banned-statement", f"the theme token {name} is bound only by its own line", node)
            if top and name in protected_top:
                self.add(
                    "banned-statement", f"'{name}' may not be bound at the top level, where the tokens read it", node
                )
            if name == PLACEHOLDER_FUNC:
                self.add("banned-statement", f"'{PLACEHOLDER_FUNC}' is the loader's and may not be bound", node)

    def check_token_writes(self) -> None:
        """A token is never written, updated or deleted, by its name or through a member (`t.pageBg = ...`)."""
        for node in walk(self.source.root):
            if node.type in _WRITES:
                target = node.child_by_field_name("left")
            elif node.type == "update_expression":
                target = node.child_by_field_name("argument")
            elif node.type == "unary_expression":
                operator = node.child_by_field_name("operator")
                target = node.child_by_field_name("argument")
                if operator is None or self.source.text(operator) != "delete":
                    continue
            else:
                continue
            if target is None:
                continue
            token = self.token_root(target)
            if token is not None and not token.startswith(f"{WINDOW}."):
                self.add("banned-statement", f"the theme token {token} is read only; copy it before changing it", node)
            elif token is not None:
                self.add("banned-statement", f"'{token}' is the harness's and is never written", node)

    def check_alone(self) -> None:
        """Every protected statement (a token line, the placeholder) has its lines to itself.

        Another statement on the same line would ride inside the protected region: the edit
        applier protects whole lines, and the loader replaces only the placeholder statement,
        so `const data = loadUserData(); const sample = [...]` would keep the sample. A trailing comment is fine.
        """
        protected: list[tuple[str, Span | None]] = [
            (f"the theme token {region.name}", region.statement) for region in self.regions.theme_tokens
        ]
        protected += [("the placeholder", region.statement) for region in self.regions.placeholders]
        statements = [
            node
            for node in walk(self.source.root)
            if node.parent is not None
            and node.parent.type in _STATEMENT_PARENTS
            and node.is_named
            and node.type not in COMMENTS
        ]
        for what, span in protected:
            if span is None:
                continue
            for node in statements:
                start, end = self.source.char(node.start_byte), self.source.char(node.end_byte)
                if start <= span.start < end or span.start <= start < span.end:
                    continue  # the statement itself, a statement around it or one inside it
                if first_line(node) <= span.last_line and last_line(node) >= span.first_line:
                    self.add(
                        "banned-statement", f"{what} shares its line with other code; give it lines of its own", node
                    )
                    break

    # -- ADAPTATION ----------------------------------------------------------------------

    def adaptation(self, original_palette: list[str]) -> None:
        self.check_placeholder()
        for node in walk(self.source.root):
            if node.type in ("call_expression", "new_expression"):
                name = self.callee_name(node)
                if RNG_DRAWS.match(name):
                    self.add("rng", f"random data generation '{name}' is not allowed; the data comes from data", node)
            elif node.type == "array" and (node.parent is None or node.parent.type != "array"):
                count = self.numbers_in(node)
                if count > MAX_LITERAL_NUMBERS:
                    message = (
                        f"literal with {count} numeric values; the limit is {MAX_LITERAL_NUMBERS}, data comes from data"
                    )
                    self.add("literal-data", message, node)
        self.check_palette(original_palette)
        self.check_imports()

    def check_placeholder(self) -> None:
        count = len(self.regions.placeholders)
        if count != 1:
            self.add(
                "placeholder-count", f"expected exactly one top-level '{PLACEHOLDER}' statement, found {count}", None
            )
        for reference in self.references:
            node = reference.visit.node
            if reference.name != PLACEHOLDER_FUNC:
                continue
            call = node.parent
            declarator = call.parent if call is not None else None
            statement = declarator.parent if declarator is not None else None
            if not (
                call is not None
                and call.type == "call_expression"
                and statement is not None
                and statement.parent is not None
                and statement.parent.type == "program"
                and is_placeholder(self.source, statement)
            ):
                message = f"'{PLACEHOLDER_FUNC}' is only allowed in the top-level statement '{PLACEHOLDER}'"
                self.add("placeholder-use", message, node)

    def numbers_in(self, node: Node) -> int:
        count = 0
        stack = [node]
        while stack:
            current = stack.pop()
            for item in js_named(current):
                item = js_unwrap(item)
                if js_number(self.source, item) is not None:
                    count += 1
                elif item.type == "array":
                    stack.append(item)
        return count

    def check_palette(self, original_palette: list[str]) -> None:
        original = [colour.upper() for colour in original_palette]
        extension = [colour.upper() for colour in IMPRINT if colour.upper() not in set(original)]
        palette_bindings = [binding for binding in self.bindings if binding.name in IMPRINT_NAMES]
        assigned: dict[str, int] = {}
        for binding in palette_bindings:
            name, declaration = binding.name, binding.declaration
            value = declaration.child_by_field_name("value") if declaration.type == "variable_declarator" else None
            pattern = declaration.child_by_field_name("name") if declaration.type == "variable_declarator" else None
            if value is None or pattern is None or pattern.type != "identifier":
                self.add("palette-prefix", f"'{name}' holds the palette and may only be declared plainly", binding.node)
                continue
            assigned[name] = assigned.get(name, 0) + 1
            if assigned[name] > 1:
                self.add("palette-prefix", f"{name} is declared again; keep one literal palette", binding.node)
                continue
            entries = self.palette_entries(value)
            if entries is None:
                self.add("palette-prefix", f"{name} must be an array of colour literals", binding.node)
            elif entries[: len(original)] != original:
                message = f"{name} must keep the {len(original)} original palette entries in order"
                self.add("palette-prefix", message, binding.node)
            elif len(entries) > len(original) + len(extension):
                limit = len(original) + len(extension)
                message = f"{name} has {len(entries)} entries, more than the {limit} colours the palette has"
                self.add("palette-prefix", message, binding.node)
            elif entries[len(original) :] != extension[: len(entries) - len(original)]:
                next_positions = ", ".join(extension[:3]) or "none left"
                message = f"{name} may only be extended with the next Imprint positions ({next_positions})"
                self.add("palette-prefix", message, binding.node)
        for node in walk(self.source.root):
            target: Node | None = None
            if node.type in _WRITES:
                target = node.child_by_field_name("left")
            elif node.type == "call_expression":
                function = node.child_by_field_name("function")
                unwrapped = js_unwrap(function) if function is not None else None
                if unwrapped is not None and js_property(self.source, unwrapped) in MUTATING_METHODS:
                    target = js_object(unwrapped)
            if target is None:
                continue
            root = js_root(target)
            if root.type == "identifier" and self.source.text(root) in IMPRINT_NAMES:
                name = self.source.text(root)
                self.add("palette-prefix", f"{name} is changed in place; extend the literal palette instead", node)

    def palette_entries(self, value: Node) -> list[str] | None:
        node = js_unwrap(value)
        if node.type != "array":
            return None
        entries: list[str] = []
        for item in js_named(node):
            text = js_string(self.source, js_unwrap(item))
            if text is None or not _HEX.fullmatch(text):
                return None
            entries.append(text.upper())
        return entries

    def check_imports(self) -> None:
        """A module of an allowlisted package that the image does not export, or a name MUI X 9 removed."""
        for module in self.regions.imports:
            specifier = module.specifier
            if specifier is None or package_of(specifier) is None:
                continue
            node = self.import_node(module.span.first_line)
            if specifier not in specifiers():
                message = f"the module '{specifier}' is not in the image's MUI X; import from a module it exports"
                self.add("unavailable-import", message[:MAX_MESSAGE_CHARS], node)
                continue
            for name in module.names:
                if name in REMOVED_EXPORTS:
                    message = f"'{name}' is not exported by MUI X 9; use {REMOVED_EXPORTS[name]}"
                    self.add("unavailable-import", message, node)

    def import_node(self, line: int) -> Node | None:
        return next(
            (
                node
                for node in self.source.root.named_children
                if node.type == "import_statement" and first_line(node) == line
            ),
            None,
        )
