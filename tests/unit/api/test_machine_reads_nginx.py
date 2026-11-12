"""nginx's half of the machine-read lines, held against the API's half and against a person's browser.

`app/nginx.conf` writes a `machine_read` line for what it answers without the API, with the API's keys and
closed sets (`api/machine_reads.py`). Two writers of one record drift apart quietly: a vendor named one way here
and another way there splits one crawler into two rows, and a map that lets a browser through writes a person
into a dataset that promises to hold none. These tests read the maps out of the shipped file and evaluate them
the way nginx does (exact keys first, then the regexes in order, first match wins, `~*` case-insensitive, `$1`
in a value is the first capture), with Python's `re` standing in for PCRE: the entries use nothing whose meaning
differs between the two. Whether nginx accepts the file is `ci-image.yml`'s job, which boots the real image and
probes it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import get_args

import pytest

from api.analytics import AI_AGENTS
from api.machine_reads import VERIFIED_CATEGORIES, Host, Kind, MachineRead, Method, Route, Source, Surface


NGINX_CONF = Path(__file__).resolve().parents[3] / "app" / "nginx.conf"
CONF = NGINX_CONF.read_text(encoding="utf-8")

BROWSERS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0 Mobile Safari/537.36",
    # Sogou's own browser: the reason the spider is matched by its full token, not by "sogou".
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0 Mobile Safari/537.36 SogouMobileBrowser/5.38.6",
    "",
]


def _map(variable: str) -> tuple[str, list[tuple[str, str]]]:
    """(source, entries) of `map <source> $<variable> { … }`, comments dropped, quotes removed."""
    block = re.search(r"^map (\S+|\"[^\"]*\") \$" + variable + r" \{\n(.*?)^\}", CONF, re.MULTILINE | re.DOTALL)
    assert block, f"app/nginx.conf has no map for ${variable}"
    entries = []
    for line in block.group(2).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert line.endswith(";"), f"map line without a closing semicolon: {line!r}"
        body = line[:-1]
        if body.startswith('"'):
            quoted = re.match(r'"((?:[^"\\]|\\.)*)"\s+(.*)$', body)
            assert quoted, f"unbalanced quotes in map key: {line!r}"
            # nginx's tokenizer unescapes only \", \' and \\ inside a quoted string.
            key, value = re.sub(r"\\([\"'\\])", r"\1", quoted.group(1)), quoted.group(2)
        else:
            # An unquoted key may hold an escaped space (`~*microsoft\ teams`); the value never does.
            key, value = body.rsplit(None, 1)
        if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        entries.append((key, value))
    return block.group(1).strip('"'), entries


def evaluate(variable: str, source_value: str) -> str:
    """The value nginx gives `$<variable>` for one value of the map's source."""
    _, entries = _map(variable)
    default = dict(entries).get("default", "")
    exact = {key.lower(): value for key, value in entries if key != "default" and not key.startswith("~")}
    if source_value.lower() in exact:
        return exact[source_value.lower()]
    for key, value in entries:
        if not key.startswith("~"):
            continue
        pattern, flags = (key[2:], re.IGNORECASE) if key.startswith("~*") else (key[1:], 0)
        match = re.search(pattern, source_value, flags)
        if match:
            for number, group in enumerate(match.groups(), start=1):
                value = value.replace(f"${number}", group or "")
            return value
    return default


def is_bot(user_agent: str) -> str:
    return evaluate("is_bot", user_agent)


def writes_a_line(*, user_agent: str, request_uri: str, category: str = "", upstream_status: str = "") -> bool:
    """`$log_machine_read` for one request, every map in its key evaluated from the request."""
    agent = evaluate("machine_agent", evaluate("machine_who", user_agent))
    key = "|".join(
        [
            upstream_status,
            evaluate("machine_route", request_uri),
            is_bot(user_agent),
            agent,
            evaluate("machine_category", category),
        ]
    )
    return evaluate("log_machine_read", key) == "1"


class TestOneVendorTable:
    def test_the_who_map_is_ai_agents_in_order(self) -> None:
        """Same tokens, same vendors, same purposes, same order: first match wins in both writers."""
        _, entries = _map("machine_who")
        nginx = []
        for key, value in entries:
            if key == "default":
                assert value == "other:unknown"
                continue
            assert key.startswith("~*"), key
            vendor, kind = value.split(":")
            nginx.append((key[2:], vendor, kind))
        assert nginx == list(AI_AGENTS)

    def test_every_purpose_is_one_the_line_accepts(self) -> None:
        """A kind outside the model's set would make the API drop that vendor's lines while nginx keeps writing."""
        assert {kind for *_, kind in AI_AGENTS} <= set(get_args(Kind)) - {"unknown"}

    @pytest.mark.parametrize(
        ("user_agent", "vendor", "kind"),
        [
            ("Mozilla/5.0 (compatible; xAI-SearchBot/1.0)", "grok", "index"),
            ("Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)", "ahrefs", "seo"),
            ("Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)", "sogou", "search"),
            ("Mozilla/5.0 (compatible; Googlebot/2.1)", "google", "search"),
            ("Mozilla/5.0 (compatible; Claude-User/1.0)", "claude", "user_directed"),
            ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ShapBot/0.1.0", "parallel", "index"),
            ("Twitterbot/1.0", "other", "unknown"),
        ],
    )
    def test_the_split_maps_take_vendor_and_kind_apart(self, user_agent: str, vendor: str, kind: str) -> None:
        who = evaluate("machine_who", user_agent)
        assert (evaluate("machine_agent", who), evaluate("machine_kind", who)) == (vendor, kind)

    def test_the_category_map_is_cloudflares_list(self) -> None:
        _, entries = _map("machine_category")
        listed = {key: value for key, value in entries if key not in ("default", "")}
        assert listed == {category: category for category in VERIFIED_CATEGORIES}
        assert dict(entries)["default"] == "other"
        assert dict(entries)[""] == ""
        assert evaluate("machine_category", "search engine crawler") == "Search Engine Crawler"


class TestTheClosedSets:
    def test_route_and_surface_values_are_the_apis(self) -> None:
        routes = {value for _, value in _map("machine_route")[1]} - {"static"}
        assert routes <= set(get_args(Route))
        assert {value for _, value in _map("machine_surface")[1]} <= set(get_args(Surface))
        assert {value for _, value in _map("machine_host")[1]} <= set(get_args(Host))
        assert {value for _, value in _map("machine_source")[1]} <= set(get_args(Source))
        assert {value for _, value in _map("machine_method")[1]} <= set(get_args(Method))

    @pytest.mark.parametrize(
        ("request_uri", "route"),
        [
            ("/", "home"),
            ("/?spec=box-basic", "home"),
            ("/plots?lib=matplotlib", "plots"),
            ("/legal", "legal"),
            ("/mcp", "mcp_page"),
            ("/box-basic", "spec_hub"),
            ("/box-basic/", "spec_hub"),
            ("/box-basic/python", "spec_language"),
            ("/box-basic/python/matplotlib?x=1", "spec_detail"),
            ("/robots.txt", "robots"),
            ("/llms.txt", "llms"),
            ("/llms-full.txt", "llms_full"),
            ("/sitemap.xml", "sitemap"),
            ("/assets/index-abc.js", "static"),
            ("/favicon.ico", "static"),
            ("/fonts/x.woff2?v=1", "static"),
            # A dot in the query string never makes a page static.
            ("/plots?lib=d3.js", "plots"),
            ("/box-basic?x=.png", "spec_hub"),
            ("/api/event", "other"),
            ("/index.html", "other"),
            ("/.well-known/llms.txt", "other"),
            ("/a/b/c/d", "other"),
        ],
    )
    def test_the_route_is_a_name_never_the_path(self, request_uri: str, route: str) -> None:
        assert evaluate("machine_route", request_uri) == route

    def test_the_raw_origin_is_synthetic(self) -> None:
        assert evaluate("machine_source", "anyplot-app-r3tvmejsmq-ez.a.run.app") == "synthetic"
        assert evaluate("machine_source", "anyplot.ai") == "live"

    @pytest.mark.parametrize(
        ("is_bot_value", "route", "surface"),
        [("1", "legal", "page"), ("0", "legal", "shell"), ("1", "robots", "machine_file"), ("0", "other", "other")],
    )
    def test_a_prerender_path_crawler_is_never_called_a_shell_read(self, is_bot_value, route, surface) -> None:
        assert evaluate("machine_surface", f"{is_bot_value}:{route}") == surface


class TestWhoWritesTheLine:
    @pytest.mark.parametrize("user_agent", BROWSERS)
    @pytest.mark.parametrize("request_uri", ["/", "/box-basic", "/plots?lib=x", "/robots.txt", "/legal/", "/api/event"])
    def test_a_browser_never_writes_one(self, user_agent: str, request_uri: str) -> None:
        assert is_bot(user_agent) == "0", user_agent
        assert not writes_a_line(user_agent=user_agent, request_uri=request_uri)
        # Not even when the API behind a proxied path failed.
        assert not writes_a_line(user_agent=user_agent, request_uri=request_uri, upstream_status="502")

    def test_a_shell_served_crawler_writes_one(self) -> None:
        assert writes_a_line(user_agent="Mozilla/5.0 (compatible; AhrefsBot/7.0)", request_uri="/box-basic")

    def test_static_assets_are_never_written(self) -> None:
        assert not writes_a_line(user_agent="Mozilla/5.0 (compatible; AhrefsBot/7.0)", request_uri="/assets/a.js")
        assert not writes_a_line(
            user_agent="Googlebot/2.1", request_uri="/favicon.ico", category="Search Engine Crawler"
        )

    @pytest.mark.parametrize("request_uri", ["/robots.txt", "/llms.txt", "/box-basic/"])
    def test_what_nginx_answers_itself_for_a_prerendered_crawler_is_written(self, request_uri: str) -> None:
        """robots.txt, llms.txt and the trailing-slash 301 never reach the API."""
        assert writes_a_line(user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)", request_uri=request_uri)
        assert writes_a_line(user_agent="Twitterbot/1.0", request_uri=request_uri)

    @pytest.mark.parametrize("upstream_status", ["200", "304", "404", "301", "502, 200", "-"])
    def test_an_answer_the_api_gave_is_the_apis_line(self, upstream_status: str) -> None:
        """`-` is a hop the crawler abandoned (nginx logs 499): the API still answers it and writes the line."""
        assert not writes_a_line(
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)", request_uri="/legal", upstream_status=upstream_status
        )

    @pytest.mark.parametrize("upstream_status", ["502", "504", "503", "200, 502"])
    def test_a_failed_hop_is_nginxs_line(self, upstream_status: str) -> None:
        assert writes_a_line(
            user_agent="Mozilla/5.0 (compatible; Googlebot/2.1)", request_uri="/legal", upstream_status=upstream_status
        )

    def test_a_verdict_alone_makes_a_machine_read(self) -> None:
        assert writes_a_line(user_agent="SomeBot/1.0", request_uri="/box-basic", category="Monitoring & Analytics")


class TestTheLogLine:
    def _format(self) -> str:
        match = re.search(r"^log_format machine_read escape=json '([^']*)';$", CONF, re.MULTILINE)
        assert match, "app/nginx.conf has no `log_format machine_read escape=json '…';` line"
        return match.group(1)

    def test_its_keys_are_the_apis(self) -> None:
        keys = re.findall(r'"([a-z_]+)":', self._format())
        fields = {field.alias or name for name, field in MachineRead.model_fields.items()}
        required = {field.alias or name for name, field in MachineRead.model_fields.items() if field.is_required()}
        assert required <= set(keys) <= fields

    def test_it_names_no_raw_request_value(self) -> None:
        variables = set(re.findall(r"\$([a-z_]+)", self._format()))
        allowed = {"request_id", "status"} | {name for name in variables if name.startswith("machine_")}
        assert variables <= allowed, variables - allowed
        for raw in ("remote_addr", "http_user_agent", "request_uri", "uri", "args", "http_referer"):
            assert raw not in variables

    def test_one_access_log_at_http_level_and_none_in_a_server_block(self) -> None:
        """Same-level access_log directives add up; a server-level one would replace the image's combined log."""
        top_level = [line for line in CONF.splitlines() if line.startswith("access_log ")]
        assert top_level == ["access_log /var/log/nginx/access.log machine_read if=$log_machine_read;"]
        indented = re.findall(r"^\s+access_log\s+([^;]+);", CONF, re.MULTILINE)
        assert set(indented) <= {"off"}, indented

    def test_every_hop_to_the_api_carries_the_line_headers(self) -> None:
        """The API writes the line of what nginx proxies to it, so it needs the edge verdict, source and host."""
        blocks = re.findall(r"^    location ([^{\n]+)\{(.*?)\n    \}", CONF, re.DOTALL | re.MULTILINE)
        hops = [(name.strip(), body) for name, body in blocks if "api.anyplot.ai" in body and "proxy_pass" in body]
        assert {name for name, _ in hops} == {"@seo_proxy", "= /llms-full.txt", "= /sitemap.xml", "@seo_proxy_python"}
        for name, body in hops:
            for header in (
                "proxy_set_header X-Prerender-Bot-Category $machine_category;",
                "proxy_set_header X-Prerender-Source $machine_source;",
                "proxy_set_header X-Forwarded-Host $host;",
            ):
                assert header in body, (name, header)
