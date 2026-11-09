"""The machine-read line (`api/machine_reads.py`): when it is written, what it holds, and what it never holds."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import mcp_types as mt
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from fastmcp.server.middleware import MiddlewareContext
from starlette.requests import Request

from api import machine_reads
from api.machine_reads import (
    AUDIENCE_SQL,
    VERIFIED_CATEGORIES,
    MachineRead,
    MachineReadMcpMiddleware,
    classify,
    record,
    route_of,
)
from api.main import app, fastapi_app
from api.mcp.server import mcp_server


ROOT = Path(__file__).resolve().parents[3]
CLAUDE_USER = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; +Claude-User@anthropic.com)"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0 Safari/537.36"


def _request(
    path: str,
    headers: dict[str, str] | None = None,
    *,
    host: str = "api.anyplot.ai",
    method: str = "GET",
    query: str = "",
) -> Request:
    raw = [(b"host", host.encode())] + [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "raw_path": path.encode(),
            "query_string": query.encode(),
            "headers": raw,
            "scheme": "https",
            "server": (host, 443),
        }
    )


def _line(path: str, headers: dict[str, str] | None = None, status: int = 200, **kwargs: Any) -> dict[str, Any] | None:
    line = classify(_request(path, headers, **kwargs), status)
    return None if line is None else line.model_dump(mode="json", by_alias=True, exclude_none=True)


class TestRouteTable:
    """A closed route name per path, never the path."""

    @pytest.mark.parametrize(
        ("path", "surface", "route"),
        [
            ("/seo-proxy/", "page", "home"),
            ("/seo-proxy", "page", "home"),
            ("/seo-proxy/plots", "page", "plots"),
            ("/seo-proxy/specs", "page", "specs"),
            ("/seo-proxy/libraries", "page", "libraries"),
            ("/seo-proxy/legal", "page", "legal"),
            ("/seo-proxy/mcp", "page", "mcp_page"),
            ("/seo-proxy/about", "page", "about"),
            ("/seo-proxy/palette", "page", "palette"),
            ("/seo-proxy/map", "page", "map"),
            ("/seo-proxy/stats", "page", "stats"),
            ("/seo-proxy/box-basic", "page", "spec_hub"),
            # nginx's map names the slashed form alike; FastAPI redirects it, so it carries no id.
            ("/seo-proxy/box-basic/", "page", "spec_hub"),
            ("/seo-proxy/legal/", "page", "legal"),
            ("/mcp/", "mcp", "mcp"),
            ("/seo-proxy/box-basic/python", "page", "spec_language"),
            ("/seo-proxy/box-basic/python/matplotlib", "page", "spec_detail"),
            ("/seo-proxy/a/b/c/d", "page", "other"),
            ("/og/home.png", "og", "og_home"),
            ("/og/plots.png", "og", "og_plots"),
            ("/og/box-basic.png", "og", "og_spec"),
            ("/og/box-basic/python/matplotlib.png", "og", "og_detail"),
            ("/specs", "api", "specs_list"),
            ("/specs/map", "api", "specs_map"),
            ("/specs/box-basic", "spec", "spec"),
            ("/specs/box-basic/seaborn/code", "code", "code"),
            ("/specs/box-basic/images", "api", "spec_images"),
            ("/plots/filter", "api", "plots_filter"),
            ("/libraries", "api", "libraries"),
            ("/libraries/matplotlib/images", "api", "library_images"),
            ("/languages", "api", "languages"),
            ("/stats", "api", "stats"),
            ("/insights/dashboard", "api", "insights"),
            ("/download/box-basic/matplotlib", "api", "download"),
            ("/preview/relay", "api", "preview"),
            ("/openapi.json", "api", "openapi"),
            ("/robots.txt", "machine_file", "robots"),
            ("/sitemap.xml", "machine_file", "sitemap"),
            ("/llms.txt", "machine_file", "llms"),
            ("/llms-full.txt", "machine_file", "llms_full"),
            ("/", "other", "other"),
            ("/wp-login.php", "other", "other"),
            ("/specs/box-basic/seaborn/code/", "other", "other"),
        ],
    )
    def test_names_the_route(self, path: str, surface: str, route: str) -> None:
        assert route_of(path)[:2] == (surface, route)

    # Routes a reader of the catalogue never needs: the API's own plumbing, the admin and agent routes, and
    # the in-app relays. Everything else the API serves must have a name, or its reads land as `other`.
    UNNAMED = ("/health", "/hello/", "/debug/", "/agent/", "/feedback", "/proxy/", "/docs", "/redoc", "/")

    def test_every_public_get_route_has_a_name(self) -> None:
        samples = {"spec_id": "box-basic", "language": "python", "library": "matplotlib", "library_id": "matplotlib"}
        unnamed = []
        for api_route in fastapi_app.routes:
            if not isinstance(api_route, APIRoute) or "GET" not in api_route.methods:
                continue
            path = re.sub(r"\{(\w+)\}", lambda m: samples.get(m.group(1), "x"), api_route.path)
            if path == "/" or any(path.startswith(prefix) for prefix in self.UNNAMED if prefix != "/"):
                continue
            if route_of(path)[1] == "other":
                unnamed.append(api_route.path)
        assert not unnamed, f"GET routes without a machine-read route name: {unnamed}"


class TestWhenALineIsWritten:
    def test_a_browser_writes_nothing(self) -> None:
        assert _line("/specs/box-basic", {"User-Agent": BROWSER}) is None

    def test_a_crawler_without_a_verdict_is_written_unverified(self) -> None:
        line = _line("/specs/box-basic", {"User-Agent": CLAUDE_USER})
        assert line is not None
        assert (line["assistant"], line["kind"]) == ("claude", "user_directed")
        assert "verified_category" not in line

    def test_the_edge_verdict_counts_on_any_path(self) -> None:
        line = _line("/specs/box-basic", {"User-Agent": "SomeVerifiedBot/1.0", "X-Verified-Bot-Category": "AI Crawler"})
        assert line is not None
        assert (line["assistant"], line["kind"], line["verified_category"]) == ("other", "unknown", "AI Crawler")

    def test_the_copied_verdict_counts_on_a_hop_path_only(self) -> None:
        copy = {"User-Agent": BROWSER, "X-Prerender-Bot-Category": "Search Engine Crawler"}
        # Off the hop it is a header anyone can send: ignored, and a browser stays a browser.
        assert _line("/specs/box-basic", copy) is None
        for hop in ("/seo-proxy/legal", "/sitemap.xml", "/llms-full.txt"):
            line = _line(hop, copy)
            assert line is not None
            assert line["verified_category"] == "Search Engine Crawler"

    def test_an_unknown_category_is_other_and_an_empty_one_is_absent(self) -> None:
        line = _line("/specs/box-basic", {"User-Agent": GOOGLEBOT, "X-Verified-Bot-Category": "Brand New Thing"})
        assert line is not None
        assert line["verified_category"] == "other"
        assert _line("/specs/box-basic", {"User-Agent": BROWSER, "X-Verified-Bot-Category": ""}) is None

    def test_the_category_match_ignores_case_but_writes_cloudflares_spelling(self) -> None:
        line = _line("/stats", {"X-Verified-Bot-Category": "search engine crawler"})
        assert line is not None
        assert line["verified_category"] == "Search Engine Crawler"

    def test_every_prerendered_page_is_a_machine_read(self) -> None:
        """nginx sends only crawlers to /seo-proxy, so a previewer AI_AGENTS does not name still counts."""
        line = _line("/seo-proxy/box-basic", {"User-Agent": "Twitterbot/1.0"})
        assert line is not None
        assert (line["assistant"], line["kind"], line["surface"], line["route"]) == (
            "other",
            "unknown",
            "page",
            "spec_hub",
        )

    def test_mcp_is_left_to_the_mcp_middleware(self) -> None:
        assert _line("/mcp/", {"User-Agent": CLAUDE_USER}) is None
        assert _line("/mcp", {"User-Agent": CLAUDE_USER}) is None

    def test_a_refused_mcp_transport_request_is_written_for_a_crawler_only(self) -> None:
        """A 4xx before any JSON-RPC request ran never reaches the MCP middleware."""
        line = _line("/mcp/", {"User-Agent": GOOGLEBOT}, status=406)
        assert line is not None
        assert (line["surface"], line["route"], line["status"]) == ("mcp", "mcp", 406)
        # A person who opens the MCP URL in a browser carries no sign.
        assert _line("/mcp/", {"User-Agent": BROWSER}, status=405) is None

    def test_a_failed_hop_is_left_to_nginx(self) -> None:
        """nginx also sees the hop fail when the API never answered, so it writes every 5xx of a hop it made."""
        hop = {"User-Agent": GOOGLEBOT, "X-Prerender-Source": "live"}
        assert _line("/seo-proxy/legal", hop, status=503) is None
        line = _line("/specs/box-basic", {"User-Agent": GOOGLEBOT}, status=503)
        assert line is not None
        assert line["status"] == 503

    def test_a_direct_callers_5xx_on_a_hop_path_is_still_written(self) -> None:
        """No nginx in front, no nginx line: without nginx's hop header the API writes the 5xx itself."""
        line = _line("/seo-proxy/legal", {"User-Agent": GOOGLEBOT}, status=503)
        assert line is not None
        assert line["status"] == 503

    def test_on_the_hop_the_copy_wins_over_the_edges_verdict_about_nginx(self) -> None:
        both = {
            "User-Agent": GOOGLEBOT,
            "X-Prerender-Bot-Category": "Search Engine Crawler",
            "X-Verified-Bot-Category": "Monitoring & Analytics",
        }
        line = _line("/seo-proxy/legal", both)
        assert line is not None
        assert line["verified_category"] == "Search Engine Crawler"


class TestCatalogueIdsOnlyForAServedAnswer:
    @pytest.mark.parametrize("status", [200, 304])
    def test_a_served_page_carries_its_ids(self, status: int) -> None:
        line = _line("/seo-proxy/box-basic/python/matplotlib", {"User-Agent": GOOGLEBOT}, status=status)
        assert line is not None
        assert (line["spec_id"], line["language"], line["library"]) == ("box-basic", "python", "matplotlib")

    @pytest.mark.parametrize("status", [404, 301, 307, 400])
    def test_a_miss_or_a_redirect_carries_none(self, status: int) -> None:
        """A 404's id is whatever the caller typed; FastAPI's slash redirect answers 307 before any lookup."""
        line = _line("/seo-proxy/wp-login/python/matplotlib", {"User-Agent": GOOGLEBOT}, status=status)
        assert line is not None
        assert {"spec_id", "language", "library"}.isdisjoint(line)
        assert line["route"] == "spec_detail"

    def test_values_outside_their_sets_are_left_out(self) -> None:
        line = _line("/specs/box-basic/mui-x-charts/code", {"User-Agent": CLAUDE_USER})
        assert line is not None
        assert line["spec_id"] == "box-basic"
        assert "library" not in line
        line = _line("/seo-proxy/Box_Basic/cobol/matplotlib", {"User-Agent": CLAUDE_USER})
        assert line is not None
        assert {"spec_id", "language"}.isdisjoint(line)
        assert line["library"] == "matplotlib"

    def test_an_overlong_spec_id_is_left_out(self) -> None:
        line = _line("/specs/" + "a" * 81, {"User-Agent": CLAUDE_USER})
        assert line is not None
        assert "spec_id" not in line


class TestSourceAndHost:
    def test_the_raw_run_app_origin_is_synthetic(self) -> None:
        line = _line("/specs/box-basic", {"User-Agent": GOOGLEBOT}, host="anyplot-api-r3tvmejsmq-ez.a.run.app")
        assert line is not None
        assert (line["source"], line["host"]) == ("synthetic", "other")

    def test_through_the_edge_it_is_live(self) -> None:
        line = _line("/specs/box-basic", {"User-Agent": GOOGLEBOT})
        assert line is not None
        assert (line["source"], line["host"]) == ("live", "api.anyplot.ai")

    def test_on_the_hop_nginx_says_where_the_crawler_came_from(self) -> None:
        hop = {"User-Agent": GOOGLEBOT, "X-Prerender-Source": "synthetic", "X-Forwarded-Host": "anyplot.ai"}
        line = _line("/seo-proxy/legal", hop)
        assert line is not None
        assert (line["source"], line["host"]) == ("synthetic", "anyplot.ai")

    def test_off_the_hop_those_headers_are_ignored(self) -> None:
        forged = {"User-Agent": GOOGLEBOT, "X-Prerender-Source": "synthetic", "X-Forwarded-Host": "anyplot.ai"}
        line = _line("/specs/box-basic", forged)
        assert line is not None
        assert (line["source"], line["host"]) == ("live", "api.anyplot.ai")

    def test_an_unknown_site_host_is_other(self) -> None:
        line = _line("/seo-proxy/legal", {"User-Agent": GOOGLEBOT, "X-Forwarded-Host": "evil.example"})
        assert line is not None
        assert line["host"] == "other"

    @pytest.mark.parametrize(("method", "expected"), [("GET", "GET"), ("POST", "POST"), ("PROPFIND", "other")])
    def test_the_method_is_a_closed_set(self, method: str, expected: str) -> None:
        line = _line("/specs/box-basic", {"User-Agent": GOOGLEBOT}, method=method)
        assert line is not None
        assert line["method"] == expected


class TestTheWrittenLine:
    def test_one_json_object_with_the_models_keys(self, machine_lines) -> None:
        record(_request("/seo-proxy/box-basic", {"User-Agent": GOOGLEBOT}), 200)
        assert len(machine_lines.raw) == 1
        raw = machine_lines.raw[0]
        assert "\n" not in raw
        line = json.loads(raw)
        fields = {field.alias or name for name, field in MachineRead.model_fields.items()}
        required = {field.alias or name for name, field in MachineRead.model_fields.items() if field.is_required()}
        assert required <= set(line) <= fields
        assert list(line) == sorted(line)
        assert (line["log_type"], line["schema"], line["severity"], line["writer"]) == (
            "machine_read",
            1,
            "INFO",
            "api",
        )
        assert re.fullmatch(r"[0-9a-f]{16}", line["line_id"])

    def test_never_an_address_a_user_agent_a_query_or_the_path(self, machine_lines) -> None:
        secret_ua = "Mozilla/5.0 (compatible; ClaudeBot/1.0; +unique-ua-marker)"
        request = _request(
            "/specs/box-basic",
            {
                "User-Agent": secret_ua,
                "X-Forwarded-For": "84.75.12.9, 172.68.0.1",
                "CF-Connecting-IP": "84.75.12.9",
                "Referer": "https://example.com/referer-marker",
            },
            query="q=query-marker",
        )
        record(request, 200)
        raw = machine_lines.raw[0]
        for leaked in (
            "84.75.12.9",
            "172.68.0.1",
            "unique-ua-marker",
            "ClaudeBot",
            "referer-marker",
            "query-marker",
            "/specs",
        ):
            assert leaked not in raw, leaked

    def test_the_line_ids_differ(self, machine_lines) -> None:
        for _ in range(3):
            record(_request("/stats", {"User-Agent": GOOGLEBOT}), 200)
        assert len({line["line_id"] for line in machine_lines.lines}) == 3

    def test_a_value_outside_its_set_drops_the_line_and_names_the_field_only(self, machine_lines, caplog) -> None:
        with caplog.at_level(logging.WARNING, logger="api.machine_reads"):
            line = machine_reads._build(
                source="live",
                assistant="not-a-vendor-marker",
                kind="index",
                surface="api",
                route="stats",
                host="api.anyplot.ai",
                method="GET",
                status=200,
            )
        assert line is None
        assert "assistant" in caplog.text
        assert "not-a-vendor-marker" not in caplog.text
        assert machine_lines.raw == []

    def test_a_failure_never_breaks_the_request(self, caplog) -> None:
        with patch.object(machine_reads, "classify", side_effect=KeyError("boom-marker")):
            with caplog.at_level(logging.WARNING, logger="api.machine_reads"):
                record(_request("/stats"), 200)
        assert "KeyError" in caplog.text
        assert "boom-marker" not in caplog.text


class TestTheMiddleware:
    """Through the app: the position inside the origin gate is pinned in test_origin_gate.py."""

    def test_a_crawler_read_writes_one_line_and_a_browser_none(self, machine_lines) -> None:
        client = TestClient(app)
        client.get("/seo-proxy/legal", headers={"User-Agent": GOOGLEBOT})
        client.get("/seo-proxy/legal", headers={"User-Agent": BROWSER})
        client.get("/libraries", headers={"User-Agent": BROWSER})
        assert [(line["surface"], line["route"]) for line in machine_lines.lines[:1]] == [("page", "legal")]
        # The browser on /seo-proxy is a machine read by definition (nginx sends none there); the one on
        # /libraries is a person's.
        assert len(machine_lines.lines) == 2
        assert machine_lines.lines[1]["assistant"] == "other"

    def test_a_head_request_is_recorded_as_the_get_it_becomes(self, machine_lines) -> None:
        TestClient(app).head("/seo-proxy/legal", headers={"User-Agent": GOOGLEBOT})
        assert [line["method"] for line in machine_lines.lines] == ["GET"]

    def test_a_handler_that_raises_still_writes_its_500(self, machine_lines) -> None:
        """The registered handler's 500 is built outside the stack; the line is written on the way out."""
        client = TestClient(app, raise_server_exceptions=False)
        with patch("api.routers.stats.StatsResponse", side_effect=RuntimeError("boom")):
            response = client.get("/stats", headers={"User-Agent": GOOGLEBOT})
        assert response.status_code == 500
        assert [(line["route"], line["status"]) for line in machine_lines.lines] == [("stats", 500)]


def _context(method: str, message: Any = None) -> MiddlewareContext[Any]:
    return MiddlewareContext(message=message, method=method)


class TestMcpMiddleware:
    @pytest.fixture
    def http(self):
        """Patch the HTTP request the middleware reads its headers from."""

        def use(headers: dict[str, str], host: str = "api.anyplot.ai"):
            return patch.object(
                machine_reads, "get_http_request", return_value=_request("/mcp/", headers, host=host, method="POST")
            )

        return use

    async def _call(self, context: MiddlewareContext[Any], result: Any = "ok") -> Any:
        async def call_next(_: MiddlewareContext[Any]) -> Any:
            if isinstance(result, Exception):
                raise result
            return result

        return await MachineReadMcpMiddleware().on_request(context, call_next)

    def test_it_is_registered_on_the_server(self) -> None:
        assert any(isinstance(middleware, MachineReadMcpMiddleware) for middleware in mcp_server.middleware)

    @pytest.mark.asyncio
    async def test_a_tool_call_writes_the_tool_and_its_ids(self, machine_lines, http) -> None:
        message = mt.CallToolRequestParams(
            name="get_implementation", arguments={"spec_id": "box-basic", "library": "seaborn"}
        )
        with http({"User-Agent": "Claude-User/1.0"}):
            assert await self._call(_context("tools/call", message)) == "ok"
        [line] = machine_lines.lines
        assert (line["surface"], line["route"], line["rpc"], line["tool"]) == (
            "mcp",
            "mcp",
            "tools_call",
            "get_implementation",
        )
        assert (line["spec_id"], line["library"], line["status"]) == ("box-basic", "seaborn", 200)
        assert (line["assistant"], line["kind"], line["client"]) == ("claude", "user_directed", "claude")

    @pytest.mark.asyncio
    async def test_a_python_client_is_named_by_its_family_only(self, machine_lines, http) -> None:
        with http({"User-Agent": "python-httpx/0.28.1"}):
            await self._call(_context("initialize"))
        [line] = machine_lines.lines
        assert (line["rpc"], line["client"], line["assistant"], line["kind"]) == (
            "initialize",
            "python",
            "other",
            "unknown",
        )
        assert "httpx" not in machine_lines.raw[0]

    @pytest.mark.asyncio
    async def test_free_text_arguments_never_land(self, machine_lines, http) -> None:
        message = mt.CallToolRequestParams(
            name="search_specs_by_tags", arguments={"plot_type": ["tag-marker"], "spec_id": "not an id marker"}
        )
        with http({"User-Agent": "node"}):
            await self._call(_context("tools/call", message))
        raw = machine_lines.raw[0]
        assert "tag-marker" not in raw
        assert "marker" not in raw
        assert json.loads(raw)["tool"] == "search_specs_by_tags"

    @pytest.mark.asyncio
    async def test_only_a_tool_that_looks_the_id_up_writes_it(self, machine_lines, http) -> None:
        """A pattern-valid made-up id passed to a tool that never resolves it proves nothing about the catalogue."""
        for name in ("list_specs", "search_specs_by_tags", "list_libraries", "get_tag_values"):
            message = mt.CallToolRequestParams(name=name, arguments={"spec_id": "made-up-spec", "library": "seaborn"})
            with http({"User-Agent": "Claude-User/1.0"}):
                await self._call(_context("tools/call", message))
        message = mt.CallToolRequestParams(
            name="get_spec_detail", arguments={"spec_id": "box-basic", "library": "seaborn"}
        )
        with http({"User-Agent": "Claude-User/1.0"}):
            await self._call(_context("tools/call", message))
        *others, detail = machine_lines.lines
        assert all({"spec_id", "library"}.isdisjoint(line) for line in others)
        assert (detail["spec_id"], detail.get("library")) == ("box-basic", None)

    @pytest.mark.asyncio
    async def test_a_failed_call_is_a_500_without_ids_and_still_raises(self, machine_lines, http) -> None:
        message = mt.CallToolRequestParams(
            name="get_implementation", arguments={"spec_id": "made-up", "library": "seaborn"}
        )
        with http({"User-Agent": "curl/8.5.0"}), pytest.raises(ValueError):
            await self._call(_context("tools/call", message), ValueError("Spec 'made-up' not found"))
        [line] = machine_lines.lines
        assert (line["status"], line["client"]) == (500, "curl")
        assert {"spec_id", "library"}.isdisjoint(line)

    @pytest.mark.asyncio
    async def test_an_unknown_tool_and_method_are_other(self, machine_lines, http) -> None:
        with http({"User-Agent": "x"}):
            await self._call(_context("tools/call", mt.CallToolRequestParams(name="drop_tables", arguments={})))
            await self._call(_context("resources/list"))
        assert [(line["rpc"], line.get("tool")) for line in machine_lines.lines] == [
            ("tools_call", "other"),
            ("other", None),
        ]

    @pytest.mark.asyncio
    async def test_the_raw_origin_is_synthetic_and_a_verdict_is_kept(self, machine_lines, http) -> None:
        with http({"User-Agent": "Claude-User/1.0", "X-Verified-Bot-Category": "AI Assistant"}, host="x.a.run.app"):
            await self._call(_context("ping"))
        [line] = machine_lines.lines
        assert (line["source"], line["verified_category"], line["rpc"]) == ("synthetic", "AI Assistant", "ping")

    @pytest.mark.asyncio
    async def test_without_an_http_request_nothing_is_written(self, machine_lines) -> None:
        """An in-process client is not a machine reading the catalogue over the network."""
        assert await self._call(_context("tools/list")) == "ok"
        assert machine_lines.raw == []


MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def _rpc(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}


class TestThroughTheMountedMcpApp:
    """The real app with the MCP app mounted: one JSON-RPC request is one line, whichever writer owns it."""

    @pytest.fixture
    def client(self):
        # The context manager runs the lifespan, which starts the MCP session manager.
        with TestClient(app) as test_client:
            yield test_client

    def test_a_tool_that_raises_writes_only_the_mcp_line(self, client, machine_lines) -> None:
        """The SDK answers the tool's error as a JSON-RPC error with HTTP 200, so the HTTP writer stays out."""
        response = client.post(
            "/mcp/",
            headers=MCP_HEADERS | {"User-Agent": GOOGLEBOT},
            json=_rpc(
                "tools/call",
                {"name": "get_implementation", "arguments": {"spec_id": "box-basic", "library": "seaborn"}},
            ),
        )
        assert response.status_code == 200
        [line] = machine_lines.lines
        assert (line["surface"], line["rpc"], line["tool"], line["status"]) == (
            "mcp",
            "tools_call",
            "get_implementation",
            500,
        )
        assert {"spec_id", "library"}.isdisjoint(line)

    def test_a_refused_transport_request_writes_only_the_http_line(self, client, machine_lines) -> None:
        response = client.get("/mcp/", headers={"Accept": "text/html", "User-Agent": GOOGLEBOT})
        assert response.status_code >= 400
        [line] = machine_lines.lines
        assert (line["surface"], line["route"], line["status"]) == ("mcp", "mcp", response.status_code)
        assert "rpc" not in line

    def test_a_successful_tool_call_writes_one_line(self, client, machine_lines) -> None:
        session = AsyncMock()
        libraries = AsyncMock()
        libraries.get_all.return_value = []
        with (
            patch("api.mcp.server.is_db_configured", return_value=True),
            patch("api.mcp.server.get_mcp_db_session", AsyncMock(return_value=session)),
            patch("api.mcp.server.LibraryRepository", return_value=libraries),
        ):
            response = client.post(
                "/mcp/",
                headers=MCP_HEADERS | {"User-Agent": "Claude-User/1.0"},
                json=_rpc("tools/call", {"name": "list_libraries", "arguments": {}}),
            )
        assert response.status_code == 200
        [line] = machine_lines.lines
        assert (line["rpc"], line["tool"], line["status"], line["assistant"]) == (
            "tools_call",
            "list_libraries",
            200,
            "claude",
        )

    def test_the_mcp_apps_mark_reaches_the_outer_middleware(self, client, machine_lines) -> None:
        """The HTTP writer reads the mark from its own request's scope; that only works if it is the same dict."""
        seen: list[dict[str, Any]] = []
        real_record = machine_reads.record

        def keep_scope(request: Request, status: int) -> None:
            seen.append(request.scope)
            real_record(request, status)

        with patch.object(machine_reads, "record", side_effect=keep_scope):
            client.post("/mcp/", headers=MCP_HEADERS | {"User-Agent": GOOGLEBOT}, json=_rpc("tools/list"))
        assert len(machine_lines.lines) == 1
        [outer_scope] = seen
        assert outer_scope.get(machine_reads.WRITTEN_SCOPE_KEY) is True


class TestTheViews:
    def test_the_daily_view_folds_the_audience_with_the_same_case(self) -> None:
        daily = (ROOT / "api" / "telemetry" / "views" / "02_daily.sql").read_text(encoding="utf-8")
        assert AUDIENCE_SQL in daily, "api/telemetry/views/02_daily.sql no longer carries AUDIENCE_SQL verbatim"

    def test_the_base_view_types_every_field_of_the_line(self) -> None:
        reads = (ROOT / "api" / "telemetry" / "views" / "01_reads.sql").read_text(encoding="utf-8")
        for name, field in MachineRead.model_fields.items():
            key = field.alias or name
            if key in ("log_type", "severity"):
                # The filter's key, and Cloud Logging moves `severity` out of jsonPayload into the entry.
                continue
            assert f"json_payload.{key})" in reads, key

    def test_every_category_is_folded_or_deliberately_other(self) -> None:
        folded = set(re.findall(r"'([A-Z][^']+)'", AUDIENCE_SQL))
        assert folded <= set(VERIFIED_CATEGORIES)
