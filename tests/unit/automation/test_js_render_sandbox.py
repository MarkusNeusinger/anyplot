"""The JavaScript render harness's sandbox mode (`automation/js-render/render.mjs`, JS-2 of step 3 in
agentic/specs/261024-agent-all-libraries.md), run through Node and Chromium.

Each test renders a small fixture with the real harness, the lock's packages and Playwright's
browser, so the module runs where all three are present (`node` on `PATH`, the packages in
`ANYPLOT_NODE_MODULES` or the checkout's `node_modules` after `npm ci`, the browser that
Playwright's `install` put in its cache) and is skipped elsewhere; the renderer image's CI step
(`ci-image.yml`) renders through the sandbox mode in the built image. The harness is copied into
a checkout's layout (`automation/js-render/render.mjs` beside `node_modules`), so its own imports
resolve to those packages, as in the pipeline.
"""

import http.server
import importlib.util
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from agents.anyplot.data.kinds import read_kinds
from agents.anyplot.data.typed_json import typed_json


REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "automation" / "js-render" / "render.mjs"
ALLOWLIST_BUILDER = REPO_ROOT / "agents" / "renderer" / "toolchain" / "import_allowlist.py"
SANDBOX_ENV = {"ANYPLOT_SANDBOX": "1", "ANYPLOT_NO_HTML": "1"}
ERROR_LINE = re.compile(
    r"^render: error: (page|import|build|draw|crash|data|timeout|harness) ([A-Za-z_$][\w$]*) (\S+:\d+|-): (.*)$"
)
"""The final error line's grammar (the harness's header), which JS-3's error profile reads."""
CANVAS = 'const canvas = document.createElement("canvas");\ndocument.getElementById("container").appendChild(canvas);\n'


def _node_modules() -> Path | None:
    root = Path(os.environ.get("ANYPLOT_NODE_MODULES", REPO_ROOT / "node_modules"))
    needed = (
        "chart.js/dist/chart.umd.js",
        "@mui/x-charts/package.json",
        "playwright/package.json",
        "esbuild/package.json",
    )
    return root if all((root / name).is_file() for name in needed) else None


@dataclass
class Run:
    returncode: int
    stdout: str
    stderr: str
    work: Path

    @property
    def last_line(self) -> str:
        lines = self.stderr.strip().splitlines()
        return lines[-1] if lines else ""

    def png_size(self, theme: str = "light") -> tuple[int, int]:
        png = (self.work / f"plot-{theme}.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        return struct.unpack(">II", png[16:24])


@dataclass
class Harness:
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
        env: dict[str, str] | None = None,
        files: dict[str, str] | None = None,
    ) -> Run:
        work = tmp_path / "work"
        work.mkdir(parents=True, exist_ok=True)
        code_file = "plot.tsx" if library == "muix" else "plot.js"
        (work / code_file).write_text(source, encoding="utf-8")
        for name, text in (files or {}).items():
            (work / name).write_text(text, encoding="utf-8")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("ANYPLOT_")}
        environment["ANYPLOT_THEME"] = "light"
        if sandbox:
            environment |= SANDBOX_ENV | {
                "ANYPLOT_NODE_MODULES": str(self.root / "node_modules"),
                "ANYPLOT_IMPORT_ALLOWLIST": str(self.allowlist),
            }
        environment |= env or {}
        done = subprocess.run(
            [self.node, str(self.root / "automation" / "js-render" / "render.mjs"), f"--library={library}", code_file],
            cwd=work,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return Run(done.returncode, done.stdout, done.stderr, work)


@pytest.fixture(scope="module")
def harness(tmp_path_factory: pytest.TempPathFactory) -> Harness:
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
    probe = Harness(root, node, allowlist).render(tmp_path_factory.mktemp("probe"), CANVAS, sandbox=False)
    if probe.returncode != 0:
        pytest.skip(f"the harness cannot render here (no browser?): {probe.stderr.strip()[-300:]}")
    return Harness(root, node, allowlist)


def _assert_final_line(run: Run, kind: str, cls: str, where: str) -> str:
    """The failure's final error line is the last line on stderr, in the grammar; returns its message."""
    assert run.returncode == 1, run.stderr
    match = ERROR_LINE.match(run.last_line)
    assert match, run.stderr
    assert match.group(1, 2, 3) == (kind, cls, where), run.last_line
    return match.group(4)


# --- A clean render, and the pipeline's harness without the variables ---------------------------


def test_a_clean_chartjs_render_in_sandbox_mode(harness: Harness, tmp_path: Path) -> None:
    source = (
        "const t = window.ANYPLOT_TOKENS;\n"
        + CANVAS
        + "new Chart(canvas, { type: 'bar', options: { animation: false },"
        " data: { labels: ['a', 'b'], datasets: [{ data: [1, 2], backgroundColor: t.palette[0] }] } });\n"
    )
    run = harness.render(tmp_path, source)
    assert run.returncode == 0, run.stderr
    assert run.png_size() == (3200, 1800)
    assert not (run.work / "plot-light.html").exists()  # ANYPLOT_NO_HTML
    assert "render: error:" not in run.stderr and "render: wrote" not in run.stdout


def probe_labels(run: Run) -> tuple[list[tuple[str, str]], bool]:
    """The `(kind, text)` pairs of the text probe (`writeTextProbe`) and its `labels_truncated`."""
    probe = json.loads((run.work / "probe-light.json").read_text(encoding="utf-8"))
    assert set(probe) == {"labels", "labels_truncated"}
    return [(label["kind"], label["text"]) for label in probe["labels"]], probe["labels_truncated"]


# --- The text probe: what the plot draws, for the agents' reply (user test of 2026-11-01) --------


def test_a_chartjs_probe_reads_the_charts_model(harness: Harness, tmp_path: Path) -> None:
    source = (
        CANVAS + "new Chart(canvas, { type: 'bar', options: { animation: false, plugins: {"
        " title: { display: true, text: 'Bevölkerung' }, legend: { display: true } },"
        " scales: { y: { title: { display: true, text: 'Personen' } } } },"
        " data: { labels: ['Bern', 'Zürich'], datasets: [{ label: 'Schweizer', data: [1, 2] }] } });\n"
    )
    run = harness.render(tmp_path, source)

    assert run.returncode == 0, run.stderr
    labels, truncated = probe_labels(run)
    assert labels[:3] == [("title", "Bevölkerung"), ("y axis label", "Personen"), ("legend text", "Schweizer")]
    assert ("x tick label", "Zürich") in labels and any(kind == "y tick label" for kind, _ in labels)
    assert truncated is True  # a plugin's own drawing is in no model


def test_a_d3_probe_names_the_ticks_by_axis_and_the_largest_top_text_the_title(
    harness: Harness, tmp_path: Path
) -> None:
    source = (
        "const svg = d3.select('#container').append('svg').attr('width', 1600).attr('height', 900);\n"
        "svg.append('text').attr('x', 800).attr('y', 40).attr('font-size', 32).text('Geburten');\n"
        "svg.append('text').attr('transform', 'rotate(-90)').attr('x', -450).attr('y', 20).text('Anzahl');\n"
        "for (const [x, name] of [[300, 'Nord'], [600, 'Süd']]) svg.append('text').attr('x', x).attr('y', 80).text(name);\n"
        "svg.append('g').attr('transform', 'translate(0,800)').call(d3.axisBottom(d3.scaleBand().domain(['Bern', 'Zug']).range([100, 1500])));\n"
        "svg.append('g').attr('transform', 'translate(100,0)').call(d3.axisLeft(d3.scaleLinear().domain([0, 5]).range([800, 100])));\n"
        "svg.append('text').attr('x', 10).attr('y', 10).attr('opacity', 0).text('unsichtbar');\n"
    )
    run = harness.render(tmp_path, source, library="d3")

    assert run.returncode == 0, run.stderr
    labels, truncated = probe_labels(run)
    assert {("title", "Geburten"), ("y axis label", "Anzahl"), ("x tick label", "Zug"), ("y tick label", "5.0")} <= set(
        labels
    )
    assert {("text", "Nord"), ("text", "Süd")} <= set(labels) and "unsichtbar" not in dict(labels).values()
    assert truncated is False


def test_two_top_texts_of_one_size_are_no_title(harness: Harness, tmp_path: Path) -> None:
    """A legend across the top writes its entries at one size: none of them is taken for the title."""
    source = (
        "const svg = d3.select('#container').append('svg').attr('width', 1600).attr('height', 900);\n"
        "for (const [x, name] of [[300, 'Nord'], [600, 'Süd']]) svg.append('text').attr('x', x).attr('y', 40)"
        ".attr('font-size', 24).text(name);\n"
        "svg.append('g').attr('transform', 'translate(0,800)').call(d3.axisBottom(d3.scaleBand().domain(['Bern']).range([100, 1500])));\n"
    )
    run = harness.render(tmp_path, source, library="d3")

    assert run.returncode == 0, run.stderr
    labels, _ = probe_labels(run)
    assert not any(kind == "title" for kind, _ in labels) and ("text", "Nord") in labels


def test_a_highcharts_probe_reads_its_classes_and_an_outlined_label_once(harness: Harness, tmp_path: Path) -> None:
    source = (
        "Highcharts.chart('container', { chart: { type: 'column', animation: false }, credits: { enabled: false },"
        " title: { text: 'Umsatz' }, xAxis: { categories: ['Bern', 'Zug'], title: { text: 'Filiale' } },"
        " yAxis: { title: { text: 'CHF' } }, plotOptions: { series: { animation: false,"
        " dataLabels: { enabled: true, style: { textOutline: '1px contrast' } } } },"
        " series: [{ name: 'Nord', data: [3, 5] }] });\n"
    )
    run = harness.render(tmp_path, source, library="highcharts")

    assert run.returncode == 0, run.stderr
    labels, truncated = probe_labels(run)
    assert {("title", "Umsatz"), ("x axis label", "Filiale"), ("y axis label", "CHF")} <= set(labels)
    assert {("legend text", "Nord"), ("x tick label", "Zug"), ("annotation", "5")} <= set(labels)
    assert labels.count(("annotation", "5")) == 1 and truncated is False


def test_an_echarts_probe_names_each_text_by_the_view_that_draws_it(harness: Harness, tmp_path: Path) -> None:
    source = (
        "const chart = echarts.init(document.getElementById('container'));\n"
        "chart.setOption({ animation: false, title: { text: 'Umsatz', subtext: 'in CHF' }, legend: {},"
        " xAxis: { type: 'category', name: 'Filiale', data: ['Bern', 'Zug'] }, yAxis: { type: 'value' },"
        " series: [{ type: 'bar', name: 'Nord', data: [3, 5], label: { show: true },"
        " markLine: { data: [{ type: 'average', name: 'Schnitt' }] } }] });\n"
    )
    run = harness.render(tmp_path, source, library="echarts")

    assert run.returncode == 0, run.stderr
    labels, truncated = probe_labels(run)
    assert {("title", "Umsatz"), ("subtitle", "in CHF"), ("x axis label", "Filiale"), ("legend text", "Nord")} <= set(
        labels
    )
    assert {("x tick label", "Zug"), ("annotation", "5")} <= set(labels) and any(k == "y tick label" for k, _ in labels)
    assert truncated is False  # zrender's display list holds every text it draws


def test_a_muix_probe_reads_the_axes_and_an_html_heading_as_the_title(harness: Harness, tmp_path: Path) -> None:
    source = (
        'import { BarChart } from "@mui/x-charts/BarChart";\n\n'
        "export default function Chart() {\n  return (\n    <div>\n"
        "      <h1 style={{ fontSize: 40, margin: 0 }}>Umsatz</h1>\n"
        "      <BarChart width={1500} height={800} skipAnimation"
        ' xAxis={[{ scaleType: "band", data: ["Bern", "Zug"], label: "Filiale" }]}'
        ' series={[{ data: [3, 5], label: "Nord" }]} />\n    </div>\n  );\n}\n'
    )
    run = harness.render(tmp_path, source, library="muix")

    assert run.returncode == 0, run.stderr
    labels, _ = probe_labels(run)
    assert {("title", "Umsatz"), ("x axis label", "Filiale"), ("x tick label", "Zug"), ("legend text", "Nord")} <= set(
        labels
    )


def test_a_page_that_tampers_with_the_model_renders_without_a_probe(harness: Harness, tmp_path: Path) -> None:
    """The snippet shares the page: a model that throws when read leaves no probe, never a failed render."""
    source = (
        CANVAS + "new Chart(canvas, { type: 'bar', options: { animation: false },"
        " data: { labels: ['a'], datasets: [{ data: [1] }] } });\n"
        "Object.defineProperty(Chart, 'instances', { get() { throw new Error('no'); } });\n"
    )
    run = harness.render(tmp_path, source)

    assert run.returncode == 0, run.stderr
    assert run.png_size() == (3200, 1800) and not (run.work / "probe-light.json").exists()


def test_a_probe_that_never_returns_is_given_up_and_the_render_stands(harness: Harness, tmp_path: Path) -> None:
    """A model whose read never ends blocks the page: the probe's own bound gives up, and the browser still closes."""
    source = (
        CANVAS + "new Chart(canvas, { type: 'bar', options: { animation: false },"
        " data: { labels: ['a'], datasets: [{ data: [1] }] } });\n"
        "Object.defineProperty(Chart, 'instances', { get() { for (;;) {} } });\n"
    )
    started = time.monotonic()
    run = harness.render(tmp_path, source)

    assert run.returncode == 0, run.stderr
    assert run.png_size() == (3200, 1800) and not (run.work / "probe-light.json").exists()
    assert "render: error:" not in run.stderr and time.monotonic() - started < 60


def test_without_the_variables_there_is_no_probe(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(tmp_path, "const t = window.ANYPLOT_TOKENS;\n" + CANVAS, sandbox=False)

    assert run.returncode == 0, run.stderr
    assert not (run.work / "probe-light.json").exists()  # the catalogue's output stays as it was


def test_without_the_variables_the_harness_is_the_pipelines(harness: Harness, tmp_path: Path) -> None:
    """No sandbox variable: the interactive page is written and carries none of the sandbox's additions, a MUI X
    snippet may import a file next to it, and a failure prints Node's error with its stack, not the final line."""
    run = harness.render(tmp_path, "const t = window.ANYPLOT_TOKENS;\n" + CANVAS, sandbox=False)
    assert run.returncode == 0, run.stderr
    html = (run.work / "plot-light.html").read_text(encoding="utf-8")
    assert "Content-Security-Policy" not in html and "sourceURL" not in html and "anyplot-data" not in html
    assert "__anyplotConsoleSlot" not in html and "<script>\ntry {\nconst t = window.ANYPLOT_TOKENS;" in html
    assert f"render: wrote {run.work / 'plot-light.html'}" in run.stdout

    helper = "export const LABEL = 'from a file next to the snippet';\n"
    muix = (
        'import { BarChart } from "@mui/x-charts/BarChart";\nimport { LABEL } from "./helper";\n\n'
        "export default function Chart() {\n  return <BarChart width={800} height={400} skipAnimation"
        ' xAxis={[{ scaleType: "band", data: [LABEL] }]} series={[{ data: [1] }]} />;\n}\n'
    )
    relative = harness.render(tmp_path, muix, library="muix", sandbox=False, files={"helper.ts": helper})
    assert relative.returncode == 0, relative.stderr  # the pipeline's esbuild resolves it

    failed = harness.render(tmp_path, CANVAS + "undefined.x;\n", sandbox=False)
    assert failed.returncode == 1
    assert "Error: render: the snippet threw while drawing:" in failed.stderr and "render: error:" not in failed.stderr


def test_without_the_variables_the_page_is_byte_for_byte_the_pipelines(harness: Harness, tmp_path: Path) -> None:
    """The page JS-1's harness wrote for the build smoke's Chart.js file (`fixtures/js-render-page-light.html`, the
    library bundle and the snippet left as placeholders, so a lock bump or a smoke edit does not move it): the harness
    without any variable writes exactly that page."""
    snippet = (REPO_ROOT / "agents" / "renderer" / "toolchain" / "smoke.js").read_text(encoding="utf-8")
    run = harness.render(tmp_path, snippet, sandbox=False)
    assert run.returncode == 0, run.stderr
    bundle = (harness.root / "node_modules" / "chart.js" / "dist" / "chart.umd.js").read_text(encoding="utf-8")
    template = (Path(__file__).parent / "fixtures" / "js-render-page-light.html").read_text(encoding="utf-8")
    expected = template.replace("{{SNIPPET}}", snippet).replace(
        "{{BUNDLE}}", re.sub("</script", lambda _: "<\\/script", bundle, flags=re.IGNORECASE)
    )
    assert (run.work / "plot-light.html").read_bytes() == expected.encode("utf-8")


# --- The page rules ----------------------------------------------------------------------------


class _Recorder(http.server.BaseHTTPRequestHandler):
    hits: list[str]

    def do_GET(self) -> None:
        self.hits.append(self.path)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"x")

    do_POST = do_GET

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture
def listener() -> Iterator[tuple[int, int, list[str]]]:
    """A local HTTP server and a UDP socket that record every connection, request and datagram."""
    hits: list[str] = []

    class Server(http.server.ThreadingHTTPServer):
        def verify_request(self, request: object, client_address: object) -> bool:
            hits.append("tcp")
            return True

    handler = type("Handler", (_Recorder,), {"hits": hits})
    server = Server(("127.0.0.1", 0), handler)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("127.0.0.1", 0))
    udp.settimeout(0.2)
    stop = threading.Event()

    def receive() -> None:
        while not stop.is_set():
            try:
                udp.recv(2048)
                hits.append("udp")
            except TimeoutError:
                continue

    threads = [
        threading.Thread(target=server.serve_forever, daemon=True),
        threading.Thread(target=receive, daemon=True),
    ]
    for thread in threads:
        thread.start()
    yield server.server_address[1], udp.getsockname()[1], hits
    stop.set()
    server.shutdown()
    server.server_close()
    udp.close()


def _channel_probe(http_port: int, udp_port: int) -> str:
    """A snippet that tries every way out of the page and throws one line naming each attempt's outcome."""
    base = f"http://127.0.0.1:{http_port}"
    return (
        CANVAS
        + f"""const base = "{base}";
const tries = [];
// An attempt that neither succeeds nor fails within 1.5 s counts as refused; the server's log is the proof.
const late = () => new Promise((resolve, reject) => setTimeout(reject, 1500));
const note = (name, promise) =>
  tries.push(Promise.race([Promise.resolve(promise), late()]).then(() => name + "=reached", () => name + "=refused"));
const event = (target, ok, ...bad) => new Promise((resolve, reject) => {{
  target[ok] = resolve;
  for (const name of bad) target[name] = reject;
}});
note("fetch", fetch(base + "/fetch"));
const xhr = new XMLHttpRequest(); xhr.open("GET", base + "/xhr"); note("xhr", event(xhr, "onload", "onerror")); xhr.send();
note("websocket", event(new WebSocket("ws://127.0.0.1:{http_port}/ws"), "onopen", "onerror", "onclose"));
const image = new Image(); note("image", event(image, "onload", "onerror")); image.src = base + "/image";
navigator.sendBeacon(base + "/beacon", "x");  // the page cannot see a beacon's fate; the server can
tries.push(new Promise((resolve) => setTimeout(resolve, 300)).then(() => "beacon=sent"));
note("popup", window.open(base + "/popup") === null ? Promise.reject() : Promise.resolve());
note("worker", new Promise((resolve, reject) => {{
  try {{
    const code = "fetch('" + base + "/worker').then(() => postMessage(1), () => postMessage(0))";
    const worker = new Worker(URL.createObjectURL(new Blob([code], {{ type: "text/javascript" }})));
    worker.onmessage = (e) => (e.data ? resolve() : reject());
    worker.onerror = reject;
  }} catch (err) {{ reject(err); }}
}}));
note("eventsource", event(new EventSource(base + "/events"), "onopen", "onerror"));
const style = document.createElement("link"); style.rel = "stylesheet"; style.href = base + "/style";
note("style", event(style, "onload", "onerror")); document.head.appendChild(style);
for (const rel of ["preconnect", "dns-prefetch"]) {{  // no outcome in the page; the closed proxy stops them
  const hint = document.createElement("link"); hint.rel = rel; hint.href = base + "/" + rel; document.head.appendChild(hint);
}}
note("webrtc", new Promise((resolve, reject) => {{
  const pc = new RTCPeerConnection({{ iceServers: [{{ urls: "stun:127.0.0.1:{udp_port}" }},
    {{ urls: "turn:127.0.0.1:{http_port}?transport=tcp", username: "u", credential: "p" }}] }});
  const found = [];
  pc.onicecandidate = (e) => e.candidate && found.push(e.candidate);
  pc.createDataChannel("x");
  pc.createOffer().then((offer) => pc.setLocalDescription(offer));
  setTimeout(() => (found.length ? resolve() : reject()), 1000);
}}));
Promise.all(tries).then((outcomes) => {{
  window.__anyplotReady = true;
  throw new Error("probe " + outcomes.join(" "));
}});
"""
    )


CHANNELS = ("fetch", "xhr", "websocket", "image", "popup", "worker", "eventsource", "style", "webrtc")


def test_no_request_socket_popup_or_peer_connection_leaves_the_page(
    harness: Harness, tmp_path: Path, listener: tuple[int, int, list[str]]
) -> None:
    """Every channel is refused and the local server hears nothing; a blob worker cannot even start (the content
    security policy's worker-src falls back to script-src), and the WebSocket reaches the route, which closes it."""
    http_port, udp_port, hits = listener
    source = _channel_probe(http_port, udp_port)
    run = harness.render(tmp_path, source)
    thrown = next(n for n, line in enumerate(source.splitlines(), 1) if 'throw new Error("probe "' in line)
    message = _assert_final_line(run, "page", "Error", f"plot.js:{thrown}")
    outcomes = message.removeprefix("probe ").split()
    assert sorted(outcomes) == sorted([f"{name}=refused" for name in CHANNELS] + ["beacon=sent"])
    assert hits == []
    assert "render: refused 0 request(s) and 1 WebSocket(s)" in run.stderr


def test_the_probe_reaches_the_server_without_sandbox_mode(
    harness: Harness, tmp_path: Path, listener: tuple[int, int, list[str]]
) -> None:
    """The control: the same probe in the pipeline's harness reaches the local server, so the refusals above are the
    sandbox mode's."""
    http_port, udp_port, hits = listener
    run = harness.render(tmp_path, _channel_probe(http_port, udp_port), sandbox=False)
    assert run.returncode == 1
    assert "fetch=reached" in run.stderr and "worker=reached" in run.stderr and "webrtc=reached" in run.stderr
    # The recorder is no WebSocket server: the handshake's request arrives, the socket then fails.
    assert {"/fetch", "/xhr", "/ws", "/image", "/beacon", "/worker"} <= set(hits) and "udp" in hits


def test_a_top_level_navigation_is_aborted_by_the_route(
    harness: Harness, tmp_path: Path, listener: tuple[int, int, list[str]]
) -> None:
    """The content security policy does not govern navigation; the context's route aborts it, and Chromium puts its
    error page in place of the plot, so the render fails as one that drew nothing. The snippet names
    `window.__anyplotReady` without setting it, so the harness waits out the signal and the error page is in."""
    http_port, _, hits = listener
    source = (
        CANVAS + f'// window.__anyplotReady stays unset\nlocation.href = "http://127.0.0.1:{http_port}/navigate";\n'
    )
    run = harness.render(tmp_path, source)
    _assert_final_line(run, "draw", "NoOutput", "-")
    assert "render: refused 1 request(s) and 0 WebSocket(s)" in run.stderr
    assert hits == []


def test_a_blob_navigation_keeps_the_policy(
    harness: Harness, tmp_path: Path, listener: tuple[int, int, list[str]]
) -> None:
    """Hygiene: a page the snippet writes into a blob: URL and navigates to passes no route, but it inherits the
    content security policy (a local scheme), so its request is refused too; the render draws nothing either way."""
    http_port, _, hits = listener
    page = f"<script>fetch('http://127.0.0.1:{http_port}/blob')<\\/script>"
    source = (
        CANVAS + "// window.__anyplotReady stays unset\n"
        f'location.href = URL.createObjectURL(new Blob(["{page}"], {{ type: "text/html" }}));\n'
    )
    run = harness.render(tmp_path, source)
    assert run.returncode == 0 or ERROR_LINE.match(run.last_line), run.stderr
    assert hits == []


def test_a_page_that_never_settles_times_out(harness: Harness, tmp_path: Path) -> None:
    """A snippet that replaces requestAnimationFrame would hold the render to the job's timeout; the harness's own
    deadline ends it after 15 s with the final line."""
    run = harness.render(tmp_path, CANVAS + "window.requestAnimationFrame = () => 0;\n")
    message = _assert_final_line(run, "timeout", "TimeoutError", "-")
    assert message == "the page did not settle within 15 s"


def test_a_script_that_never_returns_times_out_while_the_page_loads(harness: Harness, tmp_path: Path) -> None:
    """The deadline covers loading the page too: an inline script that never returns holds `setContent`, which would
    otherwise wait for Playwright's 30 s default."""
    start = time.monotonic()
    run = harness.render(tmp_path, CANVAS + "while (true) {}\n")
    took = time.monotonic() - start
    message = _assert_final_line(run, "timeout", "TimeoutError", "-")
    assert message == "the page did not settle within 15 s"
    assert took < 28, took


def test_dates_are_utc_whatever_the_hosts_zone(harness: Harness, tmp_path: Path) -> None:
    source = (
        CANVAS + 'const local = new Date("2026-03-01T00:00").toISOString();\n'
        "const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;\n"
        'if (local !== "2026-03-01T00:00:00.000Z" || zone !== "UTC") throw new Error(local + " " + zone);\n'
    )
    run = harness.render(tmp_path, source, env={"TZ": "Pacific/Auckland"})
    assert run.returncode == 0, run.stderr


def test_the_console_is_capped_in_count_and_size(harness: Harness, tmp_path: Path) -> None:
    """30 errors of 500 characters, and 100,000 lines of console.log: five errors are kept, each cut to 300
    characters, the rest counted, and the logs never leave the page."""
    source = (
        CANVAS + 'for (let i = 0; i < 30; i++) console.error("error " + i + " " + "y".repeat(500));\n'
        'for (let i = 0; i < 100000; i++) console.log("log " + i);\n'
    )
    run = harness.render(tmp_path, source)
    assert run.returncode == 0, run.stderr
    lines = run.stderr.splitlines()
    assert "render: 30 console error(s) during render, the first 5:" in lines
    kept = [line for line in lines if line.startswith("  error ")]
    assert [line.split()[1] for line in kept] == ["0", "1", "2", "3", "4"]
    assert all(len(line) <= 2 + 300 for line in kept) and "log 1" not in run.stderr


def test_no_console_passes_by_the_guard(harness: Harness, tmp_path: Path) -> None:
    """Chromium's console.context() returned a fresh console past the guard (review of JS-2); now it returns the
    guarded one, a child frame's console is guarded too, and a deleted method leaves nothing to call."""
    source = (
        CANVAS + 'if (console.context("x") !== console) throw new Error("console.context escapes the guard");\n'
        'const frame = document.body.appendChild(document.createElement("iframe"));\n'
        'for (let i = 0; i < 20; i++) console.context("x").error("context " + i + " " + "z".repeat(1000000));\n'
        'for (let i = 0; i < 20; i++) frame.contentWindow.console.error("frame " + i + " " + "z".repeat(1000000));\n'
        'delete console.error;\nif (typeof console.error !== "undefined") throw new Error("a console.error survived");\n'
    )
    run = harness.render(tmp_path, source)
    assert run.returncode == 0, run.stderr
    assert "render: 40 console error(s) during render, the first 5:" in run.stderr
    assert len(run.stderr) < 2_000


# --- MUI X's imports ---------------------------------------------------------------------------


def _muix(imports: str, body: str = "") -> str:
    return (
        f'{imports}\nimport {{ BarChart }} from "@mui/x-charts/BarChart";\n\nexport default function Chart() {{\n'
        f"  {body}\n  return <BarChart width={{800}} height={{400}} skipAnimation"
        ' xAxis={[{ scaleType: "band", data: ["a", "b"] }]} series={[{ data: [1, 2] }]} />;\n}\n'
    )


def test_a_muix_render_with_allowlisted_imports(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(
        tmp_path, _muix('import { useState } from "react";', "const [n] = useState(1); void n;"), library="muix"
    )
    assert run.returncode == 0, run.stderr
    assert run.png_size() == (3200, 1800)


@pytest.mark.parametrize(
    ("specifier", "why"),
    [
        ("{secret}", "relative, absolute, node: and URL imports are refused"),
        ("./helper", "relative, absolute, node: and URL imports are refused"),
        ("node:fs", "relative, absolute, node: and URL imports are refused"),
        ("https://example.com/x.js", "relative, absolute, node: and URL imports are refused"),
        ("clsx", "it is not on the image's import allowlist"),
        ("@mui/x-charts/internals/foo", "it is not on the image's import allowlist"),
        ("@mui/x-charts/ChartContainer", "it is not on the image's import allowlist"),  # exported by 7.29, not 9.16
    ],
)
def test_the_import_plugin_refuses_what_the_allowlist_does_not_name(
    harness: Harness, tmp_path: Path, specifier: str, why: str
) -> None:
    """An absolute path bundles any file of the image without the plugin (`import x from "/etc/os-release"`, the
    second opinion); with it, only the allowlist's bare specifiers resolve, and the refusal names the import line."""
    secret = tmp_path / "secret.js"
    secret.write_text('export default "TOPSECRET";\n', encoding="utf-8")
    specifier = specifier.replace("{secret}", str(secret))
    source = _muix(f'import value from "{specifier}";', "console.log(value);")
    run = harness.render(tmp_path, source, library="muix", files={"helper.ts": "export default 1;\n"})
    message = _assert_final_line(run, "import", "ImportRefused", "plot.tsx:1")
    assert message == f'import "{specifier}" refused: {why}'
    if specifier == str(secret):
        bundled = harness.render(tmp_path, source, library="muix", sandbox=False)
        assert bundled.returncode == 0 and "TOPSECRET" in (bundled.work / "plot-light.html").read_text(encoding="utf-8")


def test_a_require_and_a_dynamic_import_are_checked_too(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(tmp_path, _muix("", 'void import("/etc/hostname");'), library="muix")
    _assert_final_line(run, "import", "ImportRefused", "plot.tsx:5")
    run = harness.render(tmp_path, _muix('const fs = require("fs");', "console.log(fs);"), library="muix")
    _assert_final_line(run, "import", "ImportRefused", "plot.tsx:1")


def test_an_import_with_a_template_reads_no_file_outside_the_packages(harness: Harness, tmp_path: Path) -> None:
    """``import(`../etc/${name}`)`` makes esbuild match every file of the directory without asking the resolve hook
    (the review read /etc that way, and the build error quoted a file's first word); the load hook refuses each
    such file before esbuild reads it, and the final line quotes nothing of it."""
    secrets = tmp_path / "etc"
    secrets.mkdir()
    (secrets / "README").write_text("SECRETTOKEN first line\n", encoding="utf-8")
    (secrets / "conf.js").write_text('export default "SECRETTOKEN js";\n', encoding="utf-8")
    source = _muix("", 'const name = "README"; void import(`../etc/${name}`);')
    run = harness.render(tmp_path, source, library="muix")
    message = _assert_final_line(run, "import", "ImportRefused", "plot.tsx:5")
    assert message == "an import refused: it reaches a file outside the image's packages"
    assert "SECRETTOKEN" not in run.stderr + run.stdout


@pytest.mark.parametrize("comment", ["//# sourceMappingURL=/dev/zero", "/*@ sourceMappingURL=/dev/zero */"])
def test_a_source_map_comment_in_the_snippet_is_not_read(harness: Harness, tmp_path: Path, comment: str) -> None:
    """With the bundle's source map on, esbuild reads an input's own map: `/dev/zero` until it died (32 s, review of
    JS-2). The load hook hands esbuild the snippet without such comments, lines kept, so the render is a plain one."""
    run = harness.render(tmp_path, _muix(comment, "const v = (undefined as any).x; void v;"), library="muix")
    _assert_final_line(run, "page", "TypeError", "plot.tsx:5")


def test_a_missing_export_and_a_syntax_error_name_their_line(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(
        tmp_path,
        _muix('import { ChartContainer } from "@mui/x-charts";', "console.log(ChartContainer);"),
        library="muix",
    )
    message = _assert_final_line(run, "import", "ImportNotFound", "plot.tsx:1")
    # The message names the package file, a long path where node_modules is a symlink, and may be cut.
    assert message.startswith('No matching export in "') and "@mui/x-charts/index.mjs" in message
    run = harness.render(tmp_path, _muix("", "const = 3;"), library="muix")
    _assert_final_line(run, "build", "SyntaxError", "plot.tsx:5")


# --- The data ----------------------------------------------------------------------------------


def test_the_typed_data_reaches_the_page_and_no_cell_closes_the_script(harness: Harness, tmp_path: Path) -> None:
    """The service's own JSON (`typed_json`) as `window.ANYPLOT_DATA`: one object per row with `.columns`, a cell
    holding `</script>` and the line separators intact, an integer past 2^53 read as the nearest double."""
    cell = "</script><script>window.__pwned = 1</script> \N{LINE SEPARATOR} \N{PARAGRAPH SEPARATOR} <!--"
    csv_text = f'label,value,big,when,flag\n"{cell}",1.5,9007199254740993,2024-01-31T08:00:00.123456+01:00,True\n,,,,\n'
    dtypes = {"value": "number", "big": "integer", "when": "datetime", "flag": "boolean"}
    data_json = typed_json(csv_text, read_kinds(csv_text, dtypes))
    expected = [
        {"label": cell, "value": 1.5, "big": 9007199254740992, "when": "2024-01-31T07:00:00.123Z", "flag": True},
        {"label": None, "value": None, "big": None, "when": None, "flag": None},
    ]
    source = (
        CANVAS + f"const expected = {json.dumps(expected)};\n"
        "const data = window.ANYPLOT_DATA;\n"
        'if (JSON.stringify(data) !== JSON.stringify(expected)) throw new Error("data " + JSON.stringify(data));\n'
        'if (data.columns.join() !== "label,value,big,when,flag" || window.__pwned) throw new Error("columns");\n'
    )
    env = {"ANYPLOT_DATA_JSON": "data.json", "ANYPLOT_NO_HTML": "0"}
    run = harness.render(tmp_path, source, env=env, files={"data.json": data_json})
    assert run.returncode == 0, run.stderr
    html = (run.work / "plot-light.html").read_text(encoding="utf-8")
    element = html[html.index('<script type="application/json" id="anyplot-data">') :]
    element = element[: element.index("</script>")]
    assert "\\u003c/script>" in element and "<" not in element[1:] and "\N{LINE SEPARATOR}" not in element


def test_a_broken_data_file_fails_before_the_browser(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(tmp_path, CANVAS, env={"ANYPLOT_DATA_JSON": "data.json"}, files={"data.json": "[1, 2]"})
    _assert_final_line(run, "data", "DataError", "-")
    run = harness.render(tmp_path, CANVAS, env={"ANYPLOT_DATA_JSON": "missing.json"})
    _assert_final_line(run, "data", "DataError", "-")


# --- Page-only mode (JS-4b: the downloadable plot.html) -----------------------------------------

PAGE_ONLY = {"ANYPLOT_PAGE_ONLY": "1"}
NO_BROWSER = {"PLAYWRIGHT_BROWSERS_PATH": "/nonexistent/anyplot-no-browsers"}
"""A browser path with no browser in it: a run that tried to start Chromium would fail."""


def test_page_only_writes_the_page_a_render_builds_and_starts_no_browser(harness: Harness, tmp_path: Path) -> None:
    """The page is byte for byte the one the render screenshots, policy and table included, whatever
    `ANYPLOT_NO_HTML` says; no browser starts, so the code does not run (it would throw)."""
    data = '{"columns":["label"],"data":[["</script>"],[null]]}'
    source = (
        "const data = window.ANYPLOT_DATA;\n"
        + CANVAS
        + "new Chart(canvas, { type: 'bar', data: { labels: data.map((r) => r.label), datasets: [] } });\n"
    )
    rendered = harness.render(
        tmp_path / "render",
        source,
        env={"ANYPLOT_DATA_JSON": "data.json", "ANYPLOT_NO_HTML": "0"},
        files={"data.json": data},
    )
    page = harness.render(
        tmp_path / "page",
        source + 'throw new Error("the page ran");\n',
        env={**PAGE_ONLY, **NO_BROWSER, "ANYPLOT_DATA_JSON": "data.json"},
        files={"data.json": data},
    )

    assert rendered.returncode == 0 and page.returncode == 0, (rendered.stderr, page.stderr)
    built = (page.work / "plot-light.html").read_text(encoding="utf-8")
    expected = (rendered.work / "plot-light.html").read_text(encoding="utf-8")
    assert built == expected.replace(source, source + 'throw new Error("the page ran");\n')
    assert 'http-equiv="Content-Security-Policy"' in built and "\\u003c/script>" in built
    assert not (page.work / "plot-light.png").exists()
    assert page.stdout.strip() == f"render: chartjs light landscape page → {page.work / 'plot-light.html'}"


def test_page_only_bundles_muix_through_the_closed_import_plugin(harness: Harness, tmp_path: Path) -> None:
    allowed = _muix('import { useState } from "react";', "const [n] = useState(1); void n;")
    built = harness.render(tmp_path / "ok", allowed, library="muix", env={**PAGE_ONLY, **NO_BROWSER})
    refused = harness.render(
        tmp_path / "refused",
        'import text from "/etc/os-release";\nexport default () => text;\n',
        library="muix",
        env=PAGE_ONLY,
    )

    assert built.returncode == 0, built.stderr
    assert "createRoot" in (built.work / "plot-light.html").read_text(encoding="utf-8")
    _assert_final_line(refused, "import", "ImportRefused", "plot.tsx:1")
    assert not (refused.work / "plot-light.html").exists()


def test_page_only_fails_on_a_broken_data_file_with_the_final_line(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(
        tmp_path, CANVAS, env={**PAGE_ONLY, "ANYPLOT_DATA_JSON": "data.json"}, files={"data.json": "[1]"}
    )
    _assert_final_line(run, "data", "DataError", "-")
    assert not (run.work / "plot-light.html").exists()


def test_page_only_needs_the_sandbox_mode(harness: Harness, tmp_path: Path) -> None:
    """The page leaves the sandbox as a download, so it is only ever the sandbox's page, with its policy."""
    run = harness.render(tmp_path, CANVAS, sandbox=False, env=PAGE_ONLY)
    assert run.returncode == 2 and "ANYPLOT_PAGE_ONLY=1 needs ANYPLOT_SANDBOX=1" in run.stderr
    assert not (run.work / "plot-light.html").exists() and not (run.work / "plot-light.png").exists()


# --- The final error line ----------------------------------------------------------------------


def test_a_runtime_error_names_the_snippets_line(harness: Harness, tmp_path: Path) -> None:
    """The snippet's own <script> starts two lines before it (a line break and `try {`), and its frames are named by
    its `//# sourceURL`, so an error inside the library still names the snippet's line that called it."""
    run = harness.render(
        tmp_path, "const t = window.ANYPLOT_TOKENS;\n\nfunction f() {\n  return undefined.x;\n}\nf();\n"
    )
    message = _assert_final_line(run, "page", "TypeError", "plot.js:4")
    assert message == "Cannot read properties of undefined (reading 'x')"
    run = harness.render(
        tmp_path, "const t = window.ANYPLOT_TOKENS;\n\nconst chart = echarts.init(null);\n", library="echarts"
    )
    _assert_final_line(run, "page", "TypeError", "plot.js:3")


def test_a_syntax_error_names_its_line(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(tmp_path, "const t = window.ANYPLOT_TOKENS;\nconst x = ;\n")
    assert _assert_final_line(run, "page", "SyntaxError", "plot.js:2") == "Unexpected token ';'"


def test_a_muix_runtime_error_names_the_snippets_line_through_the_source_map(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(tmp_path, _muix("", "const v = (undefined as any).x; void v;"), library="muix")
    _assert_final_line(run, "page", "TypeError", "plot.tsx:5")


def test_a_huge_error_record_is_cut_in_the_page(harness: Harness, tmp_path: Path) -> None:
    """The snippet can write the page's own error record; 50 million characters of it leave the page as 10,000 and
    the final line as 200."""
    run = harness.render(tmp_path, CANVAS + 'window.__anyplotError = "x".repeat(50000000);\n')
    message = _assert_final_line(run, "page", "Error", "-")
    assert len(message) == 200 and len(run.stderr) < 2_000


def test_a_huge_thrown_error_is_cut_when_it_reaches_node(harness: Harness, tmp_path: Path) -> None:
    """A thrown error of 20 million characters is cut to 10,000 as Node receives it, before any copy, and its frames
    still name the snippet's line."""
    run = harness.render(tmp_path, CANVAS + 'throw new TypeError("x".repeat(20000000));\n')
    message = _assert_final_line(run, "page", "TypeError", "plot.js:3")
    assert len(message) == 200 and len(run.stderr) < 2_000


def test_nothing_drawn_and_a_long_message(harness: Harness, tmp_path: Path) -> None:
    run = harness.render(tmp_path, "const t = window.ANYPLOT_TOKENS;\n")
    _assert_final_line(run, "draw", "NoOutput", "-")
    run = harness.render(tmp_path, CANVAS + 'throw new RangeError("x".repeat(5000) + "\\nsecond line");\n')
    message = _assert_final_line(run, "page", "RangeError", "plot.js:3")
    assert len(message) == 200 and message.endswith("…")


def test_the_final_line_stays_last_after_a_console_flood(harness: Harness, tmp_path: Path) -> None:
    """The renderer keeps a 2,000-character stderr tail: the summary is bounded, so the line always survives it."""
    source = CANVAS + 'for (let i = 0; i < 1000; i++) console.error("z".repeat(2000));\nundefined.x;\n'
    run = harness.render(tmp_path, source)
    _assert_final_line(run, "page", "TypeError", "plot.js:4")
    assert len(run.stderr) < 2_000
