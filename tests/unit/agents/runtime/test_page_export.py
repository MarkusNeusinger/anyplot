"""The downloadable `plot.html` (JS-4b): the wrapper of `agents/anyplot/render/page.py` and `page_export.page_download`.

The wrapper's policy and background are copies of the harness's constants
(`automation/js-render/render.mjs`), which own them; these tests read them from there. The
probe (`agents/renderer/page_probe.mjs`, `tests/unit/agents/code/test_profile_javascript_page_image.py`)
loads a wrapper in Chromium; here the wrapper is read with Python's HTML parser.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

from agents.anyplot.page_export import NoPage, PageTooLarge, page_download, page_title
from agents.anyplot.render.backends.fake import FakeBackend, fixture_page
from agents.anyplot.render.contract import PageFailed, PageJob
from agents.anyplot.render.page import (
    BACKGROUNDS,
    DEVICE_SCALE_FACTOR,
    FRAME_SANDBOX,
    MARGIN_PX,
    PAGE_POLICY,
    SCALES,
    WRAPPER_POLICY,
    frame_source,
    sizing_css,
    wrap_page,
)
from agents.anyplot.schemas import PlotResult
from agents.anyplot.services import CodeVersion, Services
from agents.anyplot.settings import AgentSettings


REPO_ROOT = Path(__file__).resolve().parents[4]
HARNESS = (REPO_ROOT / "automation" / "js-render" / "render.mjs").read_text(encoding="utf-8")
NASTY = "<p>it's &amp; \"quoted\" </iframe><script>top.location='x'</script>   &#39; ü</p>\n"


def harness_policy() -> str:
    """`CONTENT_SECURITY_POLICY` as `render.mjs` writes it: string literals joined with `+`."""
    # A literal, then `+ literal` as often as it comes: one way to match, so no backtracking blow-up (CodeQL py/redos).
    match = re.search(r"const CONTENT_SECURITY_POLICY =\s*(\"[^\"]*\"(?:\s*\+\s*\"[^\"]*\")*)\s*;", HARNESS)
    assert match is not None, "render.mjs no longer defines CONTENT_SECURITY_POLICY as string literals"
    return "".join(re.findall(r"\"([^\"]*)\"", match.group(1)))


class Wrapper(HTMLParser):
    """The wrapper as a browser's tokenizer reads it: its tags, and the frame's attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.frames: list[dict[str, str | None]] = []
        self.policies: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        values = dict(attrs)
        if tag == "iframe":
            self.frames.append(values)
        if tag == "meta" and values.get("http-equiv") == "Content-Security-Policy":
            self.policies.append(values.get("content"))


def parsed(document: str) -> Wrapper:
    wrapper = Wrapper()
    wrapper.feed(document)
    wrapper.close()
    return wrapper


class TestWrapper:
    def test_the_policy_is_the_harnesss_plus_frame_src_none(self) -> None:
        """One owner: the harness. The wrapper's policy is exactly its policy and `frame-src 'none'`, because a `srcdoc`
        frame inherits the wrapper's policy (Fable measured a stricter one blanking the plot)."""
        assert harness_policy() == PAGE_POLICY
        assert WRAPPER_POLICY == f"{harness_policy()}; frame-src 'none'"

    def test_the_background_is_the_pages(self) -> None:
        match = re.search(r'const pageBg = light \? "(#[0-9A-F]{6})" : "(#[0-9A-F]{6})";', HARNESS)
        assert match is not None
        assert BACKGROUNDS == {"light": match.group(1), "dark": match.group(2)}

    def test_the_frame_gets_the_page_character_for_character(self) -> None:
        """Python's parser applies no input-stream normalisation (a browser turns CR LF into LF, NUL into U+FFFD, as
        on any load of the page), so the page comes back exactly; NASTY holds neither."""
        document = wrap_page(NASTY, theme="dark", canvas=(3200, 1800), title="t")
        wrapper = parsed(document)

        assert len(wrapper.frames) == 1
        assert wrapper.frames[0]["srcdoc"] == NASTY
        assert frame_source("a'b&c") == "a&#39;b&amp;c"

    def test_the_wrapper_runs_nothing_and_the_frame_only_its_scripts(self) -> None:
        wrapper = parsed(wrap_page(NASTY, theme="light", canvas=(3200, 1800), title='<b x="y">'))

        assert "script" not in wrapper.tags and "base" not in wrapper.tags and "form" not in wrapper.tags
        assert wrapper.tags.count("iframe") == 1 and wrapper.policies == [WRAPPER_POLICY]
        frame = wrapper.frames[0]
        assert frame["sandbox"] == FRAME_SANDBOX == "allow-scripts"
        assert set(frame) == {"sandbox", "title", "srcdoc"}  # no src, no allow, no name the page could target

    def test_the_frame_keeps_the_canvas_and_scales_down_by_the_window(self) -> None:
        landscape = sizing_css(1600, 900)
        square = sizing_css(1200, 1200)

        assert ".frame { width: 1600px; height: 900px; }" in landscape
        assert "iframe { width: 1600px; height: 900px; transform-origin: 0 0; }" in landscape
        # A 1440x900 laptop's window (about 1440x790) shows the plot at 0.8, 1280x720, without a scroll bar.
        assert (
            "@media (max-width: 1471px), (max-height: 841px) { .frame { width: 1280px; height: 720px; } "
            "iframe { transform: scale(0.8); } }"
        ) in landscape
        assert "@media (max-width: 1231px), (max-height: 1231px) { .frame { width: 1080px; height: 1080px; }" in square
        assert landscape.count("@media") == len(SCALES) - 1
        document = wrap_page("<p>", theme="light", canvas=(2400, 2400), title="t")
        assert ".frame { width: 1200px; height: 1200px; }" in document

    def test_the_wrapper_is_deterministic(self) -> None:
        first = wrap_page(NASTY, theme="dark", canvas=(3200, 1800), title="scatter-basic · d3 · v2")
        assert first == wrap_page(NASTY, theme="dark", canvas=(3200, 1800), title="scatter-basic · d3 · v2")
        assert f"background: {BACKGROUNDS['dark']}" in first

    def test_the_cards_preview_frame_is_the_wrappers_size_at_scale_one(self) -> None:
        """JS-4b-2: the chat frames the relay at the wrapper's own size, the canvas and the margin around it
        (`PAGE_FRAME_SIZES` in `app/src/lib/agent.ts`), which lies just past the first media query, so the wrapper
        shows the plot at scale 1 and the card scales the whole frame."""
        source = (REPO_ROOT / "app" / "src" / "lib" / "agent.ts").read_text(encoding="utf-8")
        sizes = {
            name: (int(width), int(height))
            for name, width, height in re.findall(r"(landscape|square): \{ width: (\d+), height: (\d+) \}", source)
        }
        for name, canvas in (("landscape", (3200, 1800)), ("square", (2400, 2400))):
            width, height = (side // DEVICE_SCALE_FACTOR + 2 * MARGIN_PX for side in canvas)
            assert sizes[name] == (width, height), name
            css = sizing_css(width - 2 * MARGIN_PX, height - 2 * MARGIN_PX)
            assert f"(max-width: {width - 1}px), (max-height: {height - 1}px)" in css, name


SQUARE_RUN_FORM = (
    "//# anyplot-orientation: square\nconst t = window.ANYPLOT_TOKENS;\nconst data = window.ANYPLOT_DATA;\n"
    'd3.select("#container").append("svg");\n'
)


def version(*, code_artifact: str = "plot.js", data_json: str | None = '{"columns":[],"data":[]}') -> CodeVersion:
    return CodeVersion(
        number=3,
        working="",
        run_form=SQUARE_RUN_FORM,
        export="",
        data_csv="x\n",
        render_id="r1",
        result=PlotResult(status="ok", attempts=1, artifacts=["plot-light.png", code_artifact, "data.csv"]),  # type: ignore[list-item]
        library="d3" if code_artifact == "plot.js" else "matplotlib",
        code_artifact=code_artifact,  # type: ignore[arg-type]
        data_json=data_json,
    )


@pytest.fixture
def settings() -> AgentSettings:
    return AgentSettings()


class TestPageDownload:
    async def test_the_page_is_built_from_the_version_and_wrapped(self, settings: AgentSettings) -> None:
        backend = FakeBackend()
        services = Services(backend_factory=lambda: backend)

        content = await page_download(services, settings, version(), "dark", spec_id="scatter-basic")

        [job] = backend.page_jobs
        assert (job.library, job.source, job.data_json, job.theme) == (
            "d3",
            SQUARE_RUN_FORM,
            '{"columns":[],"data":[]}',
            "dark",
        )
        assert job.timeout_s == settings.render_timeout_s
        text = content.decode("utf-8")
        assert parsed(text).frames[0]["srcdoc"] == fixture_page(job)
        assert ".frame { width: 1200px; height: 1200px; }" in text  # the square directive of the run form
        assert f"<title>{page_title(version(), 'scatter-basic')}</title>" in text
        assert page_title(version(), "scatter-basic") == "scatter-basic · d3 · v3 · anyplot.ai"

    @pytest.mark.parametrize(
        "without", [{"code_artifact": "plot.py", "data_json": None}, {"data_json": None}], ids=["python", "no table"]
    )
    async def test_a_version_without_a_page_has_none(self, settings: AgentSettings, without: dict[str, object]) -> None:
        backend = FakeBackend()
        services = Services(backend_factory=lambda: backend)

        with pytest.raises(NoPage):
            await page_download(services, settings, version(**without), "light", spec_id="s")  # type: ignore[arg-type]
        assert backend.page_jobs == []

    async def test_a_failed_build_is_logged_by_its_summary_only(
        self, settings: AgentSettings, caplog: pytest.LogCaptureFixture
    ) -> None:
        def failing(job: PageJob) -> str:
            raise PageFailed(exit_code=1, stderr_tail="render: error: page TypeError plot.js:4: SECRET-CELL\n")

        services = Services(backend_factory=lambda: FakeBackend(page_script=failing))

        with pytest.raises(PageFailed):
            await page_download(services, settings, version(), "light", spec_id="s")
        assert "TypeError" in caplog.text and "SECRET" not in caplog.text

    async def test_a_page_too_large_to_answer_is_refused(
        self, settings: AgentSettings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from agents.anyplot import page_export

        monkeypatch.setattr(page_export, "MAX_WRAPPED_PAGE_BYTES", 100)
        services = Services(backend_factory=lambda: FakeBackend())

        with pytest.raises(PageTooLarge) as refused:
            await page_download(services, settings, version(), "light", spec_id="s")
        assert refused.value.reason == "output_rejected"
