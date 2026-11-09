"""Machine reads: one content-free JSON line per request by a crawler, an AI assistant or an MCP client.

The line answers "which machines read the catalogue, on whose behalf, and what did they read" without
recording anything about a person. The API writes one for every machine request it answers (this module,
called by the `record_machine_read` middleware in `api/main.py` and by `MachineReadMcpMiddleware` in
`api/mcp/server.py`); the site's nginx writes the same keys for the requests it answers itself
(`log_format machine_read` in `app/nginx.conf`). A Cloud Logging sink routes every line with
`jsonPayload.log_type="machine_read"` into the `machine-reads` log bucket, which BigQuery reads through a
linked dataset (`docs/reference/machine-readers.md`).

Who answers, writes. The API is the writer for everything it answers, including the prerendered pages nginx
fetches from `/seo-proxy/*` for a crawler; nginx is the writer for what it answers without the API (robots.txt,
llms.txt, the SPA shell a crawler it does not prerender receives, a redirect, the origin gate's refusal) and for
a failed hop, which the API cannot see. So the API leaves a 5xx on a hop path to nginx.

A line is written when the request is a machine's by one of three signs: a user agent token of `AI_AGENTS`
(`api/analytics.py`), Cloudflare's verified bot category, or the path. Every `/seo-proxy/*` request is a machine
read by definition, because nginx sends only crawlers there; an MCP request is one by definition too and is
written per JSON-RPC request by the MCP middleware, so the HTTP middleware skips `/mcp/`. A browser carries none
of the three signs.

Never on a line: an IP address, the user agent, the referer, a query string, the raw path, a request body, a
tool argument other than a validated catalogue id, or any session or client identifier. Every field is a
`Literal` set, a bounded integer or an id that matches a fixed pattern; a value outside its set becomes `None`
before the line is built, and a line that still fails validation is dropped with a warning that names the field,
never the value. `spec_id`, `language` and `library` are written only for a served response (2xx or 304), so an
id a caller made up never lands: a 404 or a redirect carries the route name only.

Verified or not comes from `X-Verified-Bot-Category`, which a Cloudflare Transform Rule sets from
`cf.verified_bot_category` on every request and removes when it is empty, so a client cannot forge it through
the edge. The same rule removes it on nginx's own hop to `api.anyplot.ai` (nginx is not a verified bot), so nginx
copies the edge's verdict into `X-Prerender-Bot-Category`, which this module accepts on the hop paths only. A
direct caller of `api.anyplot.ai/seo-proxy/*` can forge that copy; the path is internal and the residual is
documented. `source` is `synthetic` for a request that reached a raw `*.run.app` origin instead of the edge: the
two smoke checks of this repository (`bot-serving-check.yml`, the app deploy's smoke) and anyone else knocking on
the raw origin. Google's front end answers a foreign Host on a `run.app` address itself, so the host cannot be
forged there; nginx passes its verdict on the hop as `X-Prerender-Source`.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import sys
from collections.abc import Mapping
from typing import Annotated, Any, Literal, get_args

from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError
from starlette.requests import Request

from api.analytics import AI_AGENTS, detect_ai_agent
from core.constants import SUPPORTED_LANGUAGES, SUPPORTED_LIBRARIES


LOGGER_NAME = "anyplot.machine_reads"
"""The logger of the lines. It does not propagate and writes the bare message to stdout: the root handler of
`api/main.py` (`logging.basicConfig`) would prefix the time and level, and Cloud Run would store the line as
`textPayload`, which the sink's `jsonPayload.log_type` filter never matches."""
LOG_TYPE: Literal["machine_read"] = "machine_read"
SCHEMA: Literal[1] = 1
"""The line format's version: a field renamed or removed is a new schema; a field or a value added is not."""


class _LineHandler(logging.StreamHandler):
    """The stdout handler of the lines; its own class so a re-import can tell it is already attached."""


def _stdout_logger() -> logging.Logger:
    """The dedicated logger, with exactly one stdout handler however often the module is imported."""
    lines = logging.getLogger(LOGGER_NAME)
    if not any(isinstance(handler, _LineHandler) for handler in lines.handlers):
        handler = _LineHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        lines.addHandler(handler)
    lines.setLevel(logging.INFO)
    lines.propagate = False
    return lines


logger = _stdout_logger()
warn = logging.getLogger(__name__)


# --- Closed sets --------------------------------------------------------------------------

Writer = Literal["api", "nginx"]
Source = Literal["live", "synthetic"]
Kind = Literal["user_directed", "index", "training", "search", "inspection", "seo", "unknown"]
"""The purpose `AI_AGENTS` records for the user agent's vendor token; `unknown` when no token matched."""
Surface = Literal["page", "shell", "code", "spec", "og", "mcp", "machine_file", "api", "other"]
"""`page` is a prerendered `/seo-proxy/*` read at the API; `shell` the SPA shell nginx serves a crawler it does
not prerender (nginx writes those)."""
Route = Literal[
    # pages, prerendered (API) or the shell (nginx)
    "home",
    "plots",
    "specs",
    "libraries",
    "legal",
    "mcp_page",
    "about",
    "palette",
    "map",
    "stats",
    "spec_hub",
    "spec_language",
    "spec_detail",
    # og images
    "og_home",
    "og_plots",
    "og_spec",
    "og_detail",
    # the JSON API (`libraries` and `stats` name both a page and an endpoint; `surface` tells them apart)
    "specs_list",
    "specs_map",
    "spec",
    "code",
    "spec_images",
    "plots_filter",
    "library_images",
    "languages",
    "insights",
    "download",
    "preview",
    "openapi",
    # machine files
    "robots",
    "sitemap",
    "llms",
    "llms_full",
    "mcp",
    "other",
]
Host = Literal["anyplot.ai", "www.anyplot.ai", "python.anyplot.ai", "api.anyplot.ai", "other"]
Method = Literal["GET", "POST", "HEAD", "other"]
Rpc = Literal["initialize", "tools_list", "tools_call", "ping", "other"]
Tool = Literal[
    "list_specs",
    "search_specs_by_tags",
    "get_spec_detail",
    "get_implementation",
    "list_libraries",
    "get_tag_values",
    "other",
]
Client = Literal["claude", "python", "node", "curl", "other"]
"""An MCP client's user agent family. MCP clients other than Claude carry no `AI_AGENTS` token, so this is the
only thing an MCP line says about the software that sent it; the user agent itself is never stored."""

VERIFIED_CATEGORIES: tuple[str, ...] = (
    "Academic Research",
    "Accessibility",
    "Advertising & Marketing",
    "Aggregator",
    "AI Assistant",
    "AI Crawler",
    "AI Search",
    "Archiver",
    "Feed Fetcher",
    "Monitoring & Analytics",
    "Page Preview",
    "Search Engine Crawler",
    "Search Engine Optimization",
    "Security",
    "Social Media Marketing",
    "Webhooks",
    "Other",
)
"""Cloudflare's verified bot categories (`cf.verified_bot_category`). A value Cloudflare adds later is written as
`other`, never as the string it sent; `app/nginx.conf`'s `$machine_category` map carries the same list."""
_CATEGORY_BY_KEY = {category.lower(): category for category in VERIFIED_CATEGORIES}

ASSISTANTS: frozenset[str] = frozenset({assistant for _, assistant, _ in AI_AGENTS} | {"other"})
"""The vendors of `AI_AGENTS`, plus `other` for a machine read no token names. Both writers name a vendor alike:
`app/nginx.conf`'s `$machine_who` map repeats every `AI_AGENTS` entry in the same order
(`tests/unit/api/test_machine_reads_nginx.py` holds the two together)."""


def _assistant(value: str) -> str:
    if value not in ASSISTANTS:
        raise ValueError("not a known assistant")
    return value


def _language(value: str) -> str:
    if value not in SUPPORTED_LANGUAGES:
        raise ValueError("not a supported language")
    return value


def _library(value: str) -> str:
    if value not in SUPPORTED_LIBRARIES:
        raise ValueError("not a supported library")
    return value


def _category(value: str) -> str:
    if value not in VERIFIED_CATEGORIES and value != "other":
        raise ValueError("not a verified bot category")
    return value


SPEC_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SpecId = Annotated[str, Field(pattern=SPEC_ID_PATTERN.pattern, max_length=80)]
Assistant = Annotated[str, AfterValidator(_assistant)]
Language = Annotated[str, AfterValidator(_language)]
Library = Annotated[str, AfterValidator(_library)]
VerifiedCategory = Annotated[str, AfterValidator(_category)]


class MachineRead(BaseModel):
    """One line, schema 1. Field order is irrelevant: the line is written with sorted keys."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    log_type: Literal["machine_read"] = LOG_TYPE
    schema_: Literal[1] = Field(default=SCHEMA, alias="schema")
    severity: Literal["INFO"] = "INFO"
    writer: Writer = "api"
    service: Annotated[str, Field(pattern=r"^[a-z0-9-]{1,63}$")]
    revision: Annotated[str, Field(pattern=r"^[a-z0-9-]{1,63}$")]
    source: Source
    line_id: Annotated[str, Field(pattern=r"^[0-9a-f]{16,32}$")]
    """A per-line random value, for deduplication only: it correlates nothing across requests."""
    assistant: Assistant
    kind: Kind
    verified_category: VerifiedCategory | None = None
    """`None` when the request carried no verdict: the unverified bucket, which includes every spoofer."""
    client: Client | None = None
    """MCP lines only."""
    surface: Surface
    route: Route
    spec_id: SpecId | None = None
    language: Language | None = None
    library: Library | None = None
    host: Host
    method: Method
    status: Annotated[int, Field(ge=100, le=599)]
    """The HTTP status; on an MCP line 200 for a JSON-RPC result and 500 for an error answer."""
    rpc: Rpc | None = None
    tool: Tool | None = None


AUDIENCE_SQL = """CASE
    WHEN kind = 'user_directed' THEN 'for_person'
    WHEN kind IN ('index', 'training') THEN 'index_training'
    WHEN kind IN ('search', 'inspection') THEN 'search'
    WHEN kind = 'seo' THEN 'seo'
    WHEN verified_category = 'AI Assistant' THEN 'for_person'
    WHEN verified_category IN ('AI Crawler', 'AI Search') THEN 'index_training'
    WHEN verified_category = 'Search Engine Crawler' THEN 'search'
    WHEN verified_category = 'Search Engine Optimization' THEN 'seo'
    WHEN verified_category = 'Page Preview' THEN 'preview'
    ELSE 'other'
  END"""
"""Who a read was for, folded from the line's `kind` and `verified_category` columns (not stored on the line).

The curated `kind` wins and Cloudflare's category is the fallback, so a vendor Cloudflare files differently from
`AI_AGENTS` keeps its documented purpose. Cloudflare treats `AI Search` as search behaviour; it folds into
`index_training` here because an AI search index is what the assistant later answers from. The daily view
(`api/telemetry/views/02_daily.sql`) carries this text verbatim, and a test keeps the two equal."""


# --- Routes -------------------------------------------------------------------------------

_SEG = r"[^/.]+"
"""A path segment without a dot, as nginx's `$machine_route` map has it: the route table names the route,
`_served_ids` decides whether the segment may be written as an id."""

PAGE_ROUTES: tuple[tuple[re.Pattern[str], Route], ...] = (
    (re.compile(r"^/?$"), "home"),
    (re.compile(r"^/plots/?$"), "plots"),
    (re.compile(r"^/specs/?$"), "specs"),
    (re.compile(r"^/libraries/?$"), "libraries"),
    (re.compile(r"^/legal/?$"), "legal"),
    (re.compile(r"^/mcp/?$"), "mcp_page"),
    (re.compile(r"^/about/?$"), "about"),
    (re.compile(r"^/palette/?$"), "palette"),
    (re.compile(r"^/map/?$"), "map"),
    (re.compile(r"^/stats/?$"), "stats"),
    (re.compile(rf"^/(?P<spec>{_SEG})/(?P<language>{_SEG})/(?P<library>{_SEG})/?$"), "spec_detail"),
    (re.compile(rf"^/(?P<spec>{_SEG})/(?P<language>{_SEG})/?$"), "spec_language"),
    (re.compile(rf"^/(?P<spec>{_SEG})/?$"), "spec_hub"),
)
"""The public page paths, matched after the `/seo-proxy` prefix is stripped; the named pages before the spec
shapes, as in `api/routers/seo.py`. A trailing slash names the same route, as nginx's `$machine_route` map has
it (FastAPI answers it with a redirect, so no id is written for it)."""

API_ROUTES: tuple[tuple[re.Pattern[str], Surface, Route], ...] = (
    (re.compile(r"^/robots\.txt$"), "machine_file", "robots"),
    (re.compile(r"^/sitemap\.xml$"), "machine_file", "sitemap"),
    (re.compile(r"^/llms\.txt$"), "machine_file", "llms"),
    (re.compile(r"^/llms-full\.txt$"), "machine_file", "llms_full"),
    (re.compile(r"^/og/home\.png$"), "og", "og_home"),
    (re.compile(r"^/og/plots\.png$"), "og", "og_plots"),
    (re.compile(rf"^/og/(?P<spec>{_SEG})/(?P<language>{_SEG})/(?P<library>{_SEG})\.png$"), "og", "og_detail"),
    (re.compile(rf"^/og/(?P<spec>{_SEG})\.png$"), "og", "og_spec"),
    (re.compile(r"^/specs$"), "api", "specs_list"),
    # `map` has the shape of a spec id, so it is matched by name first.
    (re.compile(r"^/specs/map$"), "api", "specs_map"),
    (re.compile(rf"^/specs/(?P<spec>{_SEG})/(?P<library>{_SEG})/code$"), "code", "code"),
    (re.compile(rf"^/specs/(?P<spec>{_SEG})/images$"), "api", "spec_images"),
    (re.compile(rf"^/specs/(?P<spec>{_SEG})$"), "spec", "spec"),
    (re.compile(r"^/plots/filter$"), "api", "plots_filter"),
    (re.compile(r"^/libraries$"), "api", "libraries"),
    (re.compile(rf"^/libraries/(?P<library>{_SEG})/images$"), "api", "library_images"),
    (re.compile(r"^/languages$"), "api", "languages"),
    (re.compile(r"^/stats$"), "api", "stats"),
    (re.compile(r"^/insights/"), "api", "insights"),
    (re.compile(rf"^/download/(?P<spec>{_SEG})/(?P<library>{_SEG})$"), "api", "download"),
    (re.compile(r"^/preview/"), "api", "preview"),
    (re.compile(r"^/openapi\.json$"), "api", "openapi"),
    # Only a refused MCP transport request is written over HTTP; the JSON-RPC requests are the MCP middleware's.
    (re.compile(r"^/mcp(/|$)"), "mcp", "mcp"),
)
"""Every other path the API answers; anything unlisted is `other`."""


def is_prerender_path(path: str) -> bool:
    """A `/seo-proxy/*` path: the prerendered pages nginx fetches for a crawler."""
    return path == "/seo-proxy" or path.startswith("/seo-proxy/")


def is_hop_path(path: str) -> bool:
    """A path nginx fetches from the API for the site: the prerendered pages and the two generated machine files.

    On these, and only these, the API reads what nginx put on the hop (`X-Prerender-Bot-Category`,
    `X-Prerender-Source`, `X-Forwarded-Host`), and leaves a 5xx line to nginx. The hop passes the edge, so a direct
    caller can send the same three headers; it can only move its own line between closed buckets (see the
    residuals in docs/reference/machine-readers.md), and an nginx-stamped secret on the hop would close it.
    """
    return is_prerender_path(path) or path in ("/sitemap.xml", "/llms-full.txt")


def is_mcp_path(path: str) -> bool:
    """The MCP endpoint, which `MachineReadMcpMiddleware` writes per JSON-RPC request."""
    return path == "/mcp" or path.startswith("/mcp/")


WRITTEN_SCOPE_KEY = "anyplot.machine_read"
"""Set on the request's ASGI scope once the MCP middleware wrote a line for it. The scope is one dict from the
outer HTTP middleware down to the mounted MCP app (Starlette's router updates it in place for the mount), so the
HTTP middleware sees the mark and never writes a second line for the same request."""


def route_of(path: str) -> tuple[Surface, Route, dict[str, str]]:
    """(surface, route, captured segments) for a request path; `("other", "other", {})` for anything unlisted."""
    if is_prerender_path(path):
        public = path.removeprefix("/seo-proxy")
        for pattern, route in PAGE_ROUTES:
            match = pattern.match(public)
            if match is not None:
                return "page", route, match.groupdict()
        return "page", "other", {}
    for pattern, surface, route in API_ROUTES:
        match = pattern.match(path)
        if match is not None:
            return surface, route, match.groupdict()
    return "other", "other", {}


def is_served(status: int) -> bool:
    """A response that served the thing asked for: 2xx, or 304 for a conditional request."""
    return 200 <= status < 300 or status == 304


def _served_ids(segments: Mapping[str, str], status: int) -> dict[str, str]:
    """The catalogue ids of a served response, each only if it is in its set; nothing for any other status."""
    if not is_served(status):
        return {}
    ids: dict[str, str] = {}
    spec = segments.get("spec")
    if spec is not None and len(spec) <= 80 and SPEC_ID_PATTERN.fullmatch(spec):
        ids["spec_id"] = spec
    language = segments.get("language")
    if language in SUPPORTED_LANGUAGES:
        ids["language"] = language
    library = segments.get("library")
    if library in SUPPORTED_LIBRARIES:
        ids["library"] = library
    return ids


# --- Request facts ------------------------------------------------------------------------


def verified_category(headers: Mapping[str, str], path: str) -> str | None:
    """Cloudflare's verdict for the request: one of `VERIFIED_CATEGORIES`, `other` for a string not in it, `None`
    when absent or empty.

    `X-Verified-Bot-Category` on any path; nginx's copy, `X-Prerender-Bot-Category`, on a hop path only, and
    there first: on the hop, an `X-Verified-Bot-Category` would be the edge's verdict about nginx's own egress,
    not about the crawler.
    """
    value = ""
    if is_hop_path(path):
        value = (headers.get("x-prerender-bot-category") or "").strip()
    if not value:
        value = (headers.get("x-verified-bot-category") or "").strip()
    if not value:
        return None
    return _CATEGORY_BY_KEY.get(value.lower(), "other")


def _is_run_app(host: str) -> bool:
    return host.split(":", 1)[0].strip().lower().endswith(".run.app")


def source_of(headers: Mapping[str, str], path: str) -> Source:
    """`synthetic` for a request that reached a raw `*.run.app` origin rather than the edge, else `live`."""
    if is_hop_path(path):
        relayed = (headers.get("x-prerender-source") or "").strip().lower()
        if relayed in ("live", "synthetic"):
            return "synthetic" if relayed == "synthetic" else "live"
    return "synthetic" if _is_run_app(headers.get("host") or "") else "live"


_HOSTS: dict[str, Host] = {
    "anyplot.ai": "anyplot.ai",
    "www.anyplot.ai": "www.anyplot.ai",
    "python.anyplot.ai": "python.anyplot.ai",
    "api.anyplot.ai": "api.anyplot.ai",
}


def host_of(headers: Mapping[str, str], path: str) -> Host:
    """The host the reader asked: the site's on a hop (`X-Forwarded-Host`, which nginx sets), else the API's own."""
    raw = (headers.get("x-forwarded-host") if is_hop_path(path) else None) or headers.get("host") or ""
    return _HOSTS.get(raw.split(",", 1)[0].split(":", 1)[0].strip().lower(), "other")


_METHODS: dict[str, Method] = {"GET": "GET", "POST": "POST", "HEAD": "HEAD"}


def method_of(method: str) -> Method:
    return _METHODS.get(method.upper(), "other")


def client_of(user_agent: str) -> Client:
    """The user agent family of an MCP client."""
    ua = user_agent.lower()
    if "claude" in ua:
        return "claude"
    if "python" in ua or "httpx" in ua or "aiohttp" in ua:
        return "python"
    if "node" in ua or "undici" in ua or "axios" in ua:
        return "node"
    if ua.startswith("curl/"):
        return "curl"
    return "other"


def _service() -> tuple[str, str]:
    """Cloud Run's `K_SERVICE` and `K_REVISION`, cut to the line's pattern."""
    clean = re.compile(r"[^a-z0-9-]")
    service = clean.sub("-", (os.environ.get("K_SERVICE") or "anyplot-api").lower())[:63] or "anyplot-api"
    revision = clean.sub("-", (os.environ.get("K_REVISION") or "local").lower())[:63] or "local"
    return service, revision


def _build(**fields: Any) -> MachineRead | None:
    """`MachineRead(**fields)` with the envelope filled in, or None (and a warning naming the fields) when a value
    is outside its set."""
    service, revision = _service()
    try:
        return MachineRead(service=service, revision=revision, line_id=secrets.token_hex(8), **fields)
    except ValidationError as exc:
        names = sorted({str(error["loc"][0]) for error in exc.errors() if error.get("loc")})
        warn.warning("machine read dropped: fails %s", ", ".join(names))
        return None


def classify(request: Request, status: int) -> MachineRead | None:
    """The line for one HTTP request the API answered, or None when it is not a machine read.

    None for a request without any of the three signs (a person's browser); for an answered `/mcp/` request,
    whose JSON-RPC requests the MCP middleware writes (a 4xx or 5xx there is the transport refusing the request
    before that middleware ran, so a crawler's is written here; a person who opens the MCP URL in a browser
    carries no sign and writes nothing); and for a 5xx on a hop nginx made, which nginx writes because it also
    sees the hop fail. nginx sends `X-Prerender-Source` on every hop, so a direct caller's 5xx on a hop path is
    still written.
    """
    path = request.url.path
    # The status rule alone is not enough: an error answer after the JSON-RPC chain ran (a 4xx the MCP SDK
    # sends once the middleware wrote its line) carries the mark. The mark alone is not enough either: in
    # streaming mode the response starts before the handler finished, so a 200 may arrive unmarked.
    if is_mcp_path(path) and (status < 400 or request.scope.get(WRITTEN_SCOPE_KEY)):
        return None
    headers = request.headers
    agent = detect_ai_agent(headers.get("user-agent", ""))
    category = verified_category(headers, path)
    if agent is None and category is None and not is_prerender_path(path):
        return None
    if is_hop_path(path) and status >= 500 and headers.get("x-prerender-source"):
        return None
    surface, route, segments = route_of(path)
    assistant, kind = agent if agent is not None else ("other", "unknown")
    return _build(
        source=source_of(headers, path),
        assistant=assistant,
        kind=kind,
        verified_category=category,
        surface=surface,
        route=route,
        host=host_of(headers, path),
        method=method_of(request.method),
        status=status,
        **_served_ids(segments, status),
    )


def write(record: MachineRead) -> None:
    """One JSON object on one stdout line, keys sorted, unknown values left out rather than written as null."""
    logger.info(json.dumps(record.model_dump(mode="json", by_alias=True, exclude_none=True), sort_keys=True))


def record(request: Request, status: int) -> None:
    """`classify` then `write`; never raises, because counting a read must not break it."""
    try:
        line = classify(request, status)
        if line is not None:
            write(line)
    except Exception as exc:
        warn.warning("machine read failed: %s", type(exc).__name__)


# --- MCP ----------------------------------------------------------------------------------

_RPC: dict[str, Rpc] = {
    "initialize": "initialize",
    "tools/list": "tools_list",
    "tools/call": "tools_call",
    "ping": "ping",
}
_TOOLS: dict[str, Tool] = {name: name for name in get_args(Tool) if name != "other"}


_TOOL_IDS: dict[Tool, tuple[tuple[str, str], ...]] = {
    "get_spec_detail": (("spec_id", "spec"),),
    "get_implementation": (("spec_id", "spec"), ("library", "library")),
}
"""The arguments a tool resolves against the catalogue, as (argument, segment). Only these can become ids: a
tool that does not look the id up returns a result for a made-up one too, so its result proves nothing."""


def _tool_call(message: Any) -> tuple[Tool, dict[str, str]]:
    """The tool's name from the closed set, and the arguments it resolves as candidate ids; nothing else of the
    arguments (a search's tags, a list of libraries) is ever read."""
    name = getattr(message, "name", None)
    tool: Tool = _TOOLS.get(name, "other") if isinstance(name, str) else "other"
    arguments = getattr(message, "arguments", None)
    segments: dict[str, str] = {}
    if isinstance(arguments, Mapping):
        for key, segment in _TOOL_IDS.get(tool, ()):
            value = arguments.get(key)
            if isinstance(value, str):
                segments[segment] = value
    return tool, segments


def mcp_line(context: MiddlewareContext[Any], request: Request, status: int) -> MachineRead | None:
    """The line for one JSON-RPC request of an MCP client."""
    headers = request.headers
    user_agent = headers.get("user-agent", "")
    agent = detect_ai_agent(user_agent)
    assistant, kind = agent if agent is not None else ("other", "unknown")
    rpc: Rpc = _RPC.get(context.method or "", "other")
    tool: Tool | None = None
    ids: dict[str, str] = {}
    if rpc == "tools_call":
        tool, segments = _tool_call(context.message)
        # Only a call that returned a result proves the ids are the catalogue's, as `is_served` does for HTTP.
        ids = _served_ids(segments, status)
    return _build(
        source="synthetic" if _is_run_app(headers.get("host") or "") else "live",
        assistant=assistant,
        kind=kind,
        verified_category=verified_category(headers, "/mcp/"),
        client=client_of(user_agent),
        surface="mcp",
        route="mcp",
        host=host_of(headers, "/mcp/"),
        method=method_of(request.method),
        status=status,
        rpc=rpc,
        tool=tool,
        **ids,
    )


class MachineReadMcpMiddleware(Middleware):
    """One line per JSON-RPC request an MCP client sends over HTTP: the method, the tool and its validated ids.

    `on_request` runs once per request, `initialize` and `tools/call` included. Without an HTTP request (an
    in-process client, as in the tests) nothing is written: that is not a machine reading the catalogue over
    the network. Never raises; the tool's own exception is re-raised after the line is written.
    """

    async def on_request(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]) -> Any:
        status = 500
        try:
            result = await call_next(context)
            status = 200
            return result
        finally:
            self._write(context, status)

    @staticmethod
    def _write(context: MiddlewareContext[Any], status: int) -> None:
        try:
            try:
                request = get_http_request()
            except RuntimeError:
                return
            line = mcp_line(context, request, status)
            if line is not None:
                write(line)
                request.scope[WRITTEN_SCOPE_KEY] = True
        except Exception as exc:
            warn.warning("machine read failed: %s", type(exc).__name__)
