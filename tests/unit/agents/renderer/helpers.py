"""Plain helpers for the renderer tests: jobs, unsigned ID tokens, a fake launcher script and a fake executor."""

import asyncio
import base64
import json
import time
from typing import Any

from agents.anyplot.render.backends.fake import fixture_png
from agents.renderer.wire import (
    ConvertMeta,
    ConvertRequest,
    ConvertRun,
    DataRun,
    DataRunRequest,
    PageRequest,
    PageRun,
    RenderRequest,
    Theme,
    ThemeRun,
)


URL = "https://anyplot-renderer-239660669828.europe-west4.run.app"
AGENTS_SA = "anyplot-agents@anyplot.iam.gserviceaccount.com"

PLOT = """\
import os

import matplotlib.pyplot as plt

THEME = os.getenv("ANYPLOT_THEME", "light")
fig, ax = plt.subplots(figsize=(4, 2), dpi=50)
ax.plot([1, 2, 3], [1, 3, 2])
fig.savefig(f"plot-{THEME}.png")
"""
"""A tiny matplotlib plot: 200x100 pixels, a probe, a few tenths of a second."""

CANVAS_PLOT = """\
import os

import matplotlib.pyplot as plt

THEME = os.getenv("ANYPLOT_THEME", "light")
fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
fig.patch.set_facecolor("#FAF8F1" if THEME == "light" else "#1A1A17")
ax.bar(["a", "b", "c", "d"], [3, 1, 4, 2], color="#009E73")
fig.savefig(f"plot-{THEME}.png")
"""
"""A plot on the 3200x1800 catalogue canvas, which the host gates accept."""

SLEEPER = "import time\ntime.sleep(60)\n"
"""Code that runs until the renderer stops it."""

FAKE_LAUNCHER = """\
import json
import os
import sys

args = sys.argv[1:]
log = os.environ.get("FAKE_SANDBOX_LOG")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(args) + "\\n")
if args[:1] == ["delete"]:
    sys.exit(0)
if args[:1] != ["do"]:
    print("unknown subcommand", file=sys.stderr)
    sys.exit(125)
mounts, env, workdir, index = {}, {}, None, 1
while args[index] != "--":
    flag, value = args[index], args[index + 1]
    if flag == "--mount":
        spec = dict(part.split("=", 1) for part in value.split(","))
        mounts[spec["destination"]] = spec["source"]
    elif flag == "-w":
        workdir = value
    elif flag == "--env":
        key, _, item = value.partition("=")
        env[key] = item
    elif flag != "--sandbox-name":
        print(f"unknown flag {flag}", file=sys.stderr)
        sys.exit(125)
    index += 2
command = args[index + 1 :]
failures = os.environ.get("FAKE_SANDBOX_FAIL")
if failures and os.path.exists(failures):
    with open(failures, encoding="utf-8") as handle:
        left = int(handle.read() or 0)
    if left > 0:
        with open(failures, "w", encoding="utf-8") as handle:
            handle.write(str(left - 1))
        print("Error: failed to exec in container: cmd.Wait(exec) failed: exit status 137", file=sys.stderr)
        sys.exit(1)
os.chdir(mounts[workdir])
if os.environ.get("FAKE_SANDBOX_SIGPIPE"):
    import signal
    import subprocess

    code = subprocess.run(command, env=env).returncode
    if code != 0:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGPIPE)
    sys.exit(code)
os.execve(command[0], command, env)
"""
"""A stand-in for `/usr/local/gcp/bin/sandbox`: logs every call, emulates `do` by
changing into the `/work` mount and exec-ing the command with exactly the `--env`
values (so the launcher process is the harness, like a real sandbox's `do`), answers
`delete` with 0 like the real one, and fails `do` without starting anything while
the counter file in `FAKE_SANDBOX_FAIL` is positive (the S2 launcher failure). With
`FAKE_SANDBOX_SIGPIPE` set it runs the command as a child instead and dies of SIGPIPE
when the child exits non-zero, as Cloud Run's launcher does (exit code -13)."""


def job(source: str = PLOT, *, themes: tuple[Theme, ...] = ("light",), timeout_s: float = 30.0) -> RenderRequest:
    return RenderRequest(
        job_id="job123",
        language="python",
        library="matplotlib",
        source=source,
        data_csv="x,y\n1,2\n",
        themes=list(themes),
        timeout_s=timeout_s,
    )


def id_token(**claims: Any) -> str:
    """An ID token as Cloud Run forwards it: readable claims, the signature replaced."""

    def part(value: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")

    payload = {"iss": "https://accounts.google.com", "exp": int(time.time()) + 3600, **claims}
    return f"{part({'alg': 'RS256', 'typ': 'JWT'})}.{part(payload)}.SIGNATURE_REMOVED_BY_GOOGLE"


class FakeExecutor:
    """Fixture runs without a sandbox; records calls and the most runs at once."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.active = 0
        self.max_active = 0
        self.gate: asyncio.Event | None = None
        self.error: Exception | None = None
        self.stuck = 0
        self.available = True
        self.toolchains: dict[str, bool] = {"python": True, "javascript": False, "r": False, "julia": False}
        self.page: PageRun | None = None
        """A page build's answer; None builds a small page that names the library and the theme."""

    def languages(self) -> dict[str, bool]:
        return dict(self.toolchains)

    async def run_theme(self, job: RenderRequest, theme: Theme) -> ThemeRun:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            if self.error is not None:
                raise self.error
            if self.gate is not None:
                await self.gate.wait()
            await asyncio.sleep(0.01)
            self.calls.append((job.job_id, theme))
            return ThemeRun(
                theme=theme,
                exit_code=0,
                png_base64=base64.b64encode(fixture_png(theme)).decode(),
                probe={"texts": [], "tick_overlaps": 0, "points": 0},
                stderr_tail="",
                wall_s=0.5,
                max_rss_mb=150.0,
            )
        finally:
            self.active -= 1

    async def run_data(self, job: DataRunRequest) -> DataRun:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            if self.error is not None:
                raise self.error
            if self.gate is not None:
                await self.gate.wait()
            await asyncio.sleep(0.01)
            self.calls.append((job.job_id, "data"))
            return DataRun(exit_code=0, csv_text="x,y\n1,2\n", wall_s=0.2)
        finally:
            self.active -= 1

    async def run_convert(self, job: ConvertRequest) -> ConvertRun:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            if self.error is not None:
                raise self.error
            if self.gate is not None:
                await self.gate.wait()
            await asyncio.sleep(0.01)
            self.calls.append((job.job_id, "convert"))
            meta = ConvertMeta(kind="xlsx", rows=2, columns=2, sheet="S", sheets=["S"], sheet_count=1)
            return ConvertRun(exit_code=0, text="x,y\n1,2\n", meta=meta, wall_s=0.2)
        finally:
            self.active -= 1

    async def run_page(self, job: PageRequest) -> PageRun:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            if self.error is not None:
                raise self.error
            if self.gate is not None:
                await self.gate.wait()
            await asyncio.sleep(0.01)
            self.calls.append((job.job_id, f"page-{job.theme}"))
            if self.page is not None:
                return self.page
            return PageRun(exit_code=0, html=f"<!doctype html><p>{job.library} {job.theme} ü</p>", wall_s=0.2)
        finally:
            self.active -= 1


PAGE_SNIPPET = 'const data = window.ANYPLOT_DATA;\nnew Chart(document.createElement("canvas"), {});\n'


def page_job(*, theme: Theme = "light", job_id: str = "page123", source: str = PAGE_SNIPPET) -> PageRequest:
    return PageRequest(
        job_id=job_id,
        language="javascript",
        library="chartjs",
        source=source,
        data_json='{"columns":["x"],"data":[[1]]}',
        theme=theme,
        timeout_s=30.0,
    )


def convert_job(
    data: bytes = b"PK\x05\x06" + b"\0" * 18, *, sheet: str | None = None, job_id: str = "conv123"
) -> ConvertRequest:
    return ConvertRequest(job_id=job_id, data_base64=base64.b64encode(data).decode(), sheet=sheet, timeout_s=10.0)


DATA_SNIPPET = "import pandas as pd\ndf = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})\n"
"""A data snippet the harness turns into a two-row `out.csv`."""


def data_job(source: str = DATA_SNIPPET, *, timeout_s: float = 20.0, job_id: str = "data123") -> DataRunRequest:
    return DataRunRequest(job_id=job_id, source=source, timeout_s=timeout_s)
