"""Plain helpers for the renderer tests: jobs, unsigned ID tokens, a fake launcher script and a fake executor."""

import asyncio
import base64
import json
import time
from typing import Any

from agents.anyplot.render.backends.fake import fixture_png
from agents.renderer.executor import Unavailable
from agents.renderer.wire import RenderRequest, Theme, ThemeRun


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
os.execve(command[0], command, env)
"""
"""A stand-in for `/usr/local/gcp/bin/sandbox`: logs every call, emulates `do` by
changing into the `/work` mount and exec-ing the command with exactly the `--env`
values (so the launcher process is the harness, like a real sandbox's `do`), answers
`delete` with 0 like the real one, and fails `do` without starting anything while
the counter file in `FAKE_SANDBOX_FAIL` is positive (the S2 launcher failure)."""


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
        self.calls: list[tuple[str, Theme]] = []
        self.active = 0
        self.max_active = 0
        self.gate: asyncio.Event | None = None
        self.error: Unavailable | None = None
        self.stuck = 0
        self.available = True

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
