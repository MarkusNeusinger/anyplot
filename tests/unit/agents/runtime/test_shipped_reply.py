"""Tests for the shipped-reply check: after a shipped plot the root's reply never asks for `.confirm()`."""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.anyplot import policy
from agents.anyplot.plugins import shipped_reply as plugin_module
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger
from agents.anyplot.plugins.reply_language import reply_text
from agents.anyplot.plugins.shipped_reply import ShippedReplyPlugin, drop_confirm
from agents.anyplot.services import Services
from agents.main import Runtime, app, get_runtime

from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_service_flow import create_plot, open_session, permissive_queue


READY = "Your plot is ready: Exam Score against Study Hours."


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=permissive_queue())
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


@dataclass
class FakeSession:
    id: str = "s1"
    user_id: str = "adm_1"
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeContext:
    invocation_id: str = "inv-1"
    agent_name: str = "anyplot"
    session: FakeSession = field(default_factory=FakeSession)


@pytest.fixture
def ledger() -> Any:
    current = RequestLedger(request_id="req-1", user_id="adm_1", session_id="s1", shipped_in_turn=True)
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


@pytest.fixture
def lines(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    recorded: list[dict[str, Any]] = []
    monkeypatch.setattr(plugin_module, "attribution", lambda hook, ledger, **fields: recorded.append(fields))
    return recorded


def response(*parts: types.Part) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=list(parts)))


async def check(reply: LlmResponse, context: FakeContext | None = None) -> LlmResponse:
    """Run the plugin over `reply`; it edits in place and always returns None, so the next plugin still runs."""
    returned = await ShippedReplyPlugin().after_model_callback(
        callback_context=context or FakeContext(),  # type: ignore[arg-type]
        llm_response=reply,
    )
    assert returned is None
    return reply


class TestDropConfirm:
    @pytest.mark.parametrize(
        ("text", "kept", "dropped"),
        [
            (f"{READY} Your data is not confirmed yet, so press `.confirm()` first.", READY, 1),
            (f"Please confirm the data with `.confirm()`. {READY}", READY, 1),
            ("Der Plot ist fertig. Bestätige die Daten noch mit `.confirm()`.", "Der Plot ist fertig.", 1),
            ("Le graphique est prêt ! Confirme les données avec .confirm() ?", "Le graphique est prêt !", 1),
            ("图表已完成。请用`.confirm()`确认数据。", "图表已完成。", 1),
            (
                f"{READY}\n\n- The x axis is log scaled.\n- Confirm with `.confirm()`.",
                f"{READY}\n\n- The x axis is log scaled.",
                1,
            ),
            (
                f"{READY}\n\nPress `.confirm()` in the data panel.\n\nThe y axis starts at 0.",
                f"{READY}\n\nThe y axis starts at 0.",
                1,
            ),
            ("1. Press `.confirm()`.\n2. " + READY, "2. " + READY, 1),
            ("Press confirm() now. Then `.confirm()` again.", "", 2),
            # A sentence that ends in a quote, a bracket or Markdown still ends there.
            (f'Click ".confirm()." {READY}', READY, 1),
            (f"**Press `.confirm()` first.** {READY}", READY, 1),
            (f"(Confirm with `.confirm()`.) {READY}", READY, 1),
            # A list item keeps its marker when its first sentence goes.
            ("- Press `.confirm()`. Then explore the plot.", "- Then explore the plot.", 1),
            ("2. Press `.confirm()`. Then explore the plot.", "2. Then explore the plot.", 1),
        ],
    )
    def test_drops_every_sentence_that_names_the_button(self, text: str, kept: str, dropped: int) -> None:
        assert drop_confirm(text) == (kept, dropped)

    @pytest.mark.parametrize(
        "text",
        [
            READY,
            "The values run from 3.5 to 7.25, so the axis starts at 3.",  # dots inside numbers end no sentence
            "I would reconfirm() nothing here.",  # another word is no button
        ],
    )
    def test_leaves_other_text_alone(self, text: str) -> None:
        assert drop_confirm(text) == (text, 0)


class TestPlugin:
    async def test_after_a_shipped_plot_the_confirm_sentence_goes(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        thought = types.Part(text="The data was confirmed earlier.", thought=True)
        reply = await check(response(thought, types.Part(text=f"{READY} Now confirm your data with `.confirm()`.")))

        assert reply_text(reply) == READY
        assert reply.content is not None and reply.content.parts is not None
        assert reply.content.parts[0] == thought  # thoughts stay as they were
        assert lines == [{"verdict": "dropped", "sentences": 1}]

    async def test_a_reply_that_is_only_the_ask_stays_whole(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        text = "Please confirm the data with `.confirm()`."

        reply = await check(response(types.Part(text=text)))

        assert reply_text(reply) == text
        assert lines == [{"verdict": "kept", "sentences": 1}]

    async def test_without_a_shipped_plot_the_ask_stays(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        """Example data or a binding change rightly ends with the ask: no plot shipped in that turn."""
        ledger.shipped_in_turn = False
        text = "I generated example data: 15 rows, all made up. Check them and confirm them with `.confirm()`."

        assert reply_text(await check(response(types.Part(text=text)))) == text
        assert lines == []

    @pytest.mark.parametrize(
        ("context", "reply"),
        [
            (FakeContext(agent_name="adapter_matplotlib"), response(types.Part(text=f"{READY} Press `.confirm()`."))),
            (FakeContext(), response(types.Part(function_call=types.FunctionCall(name="get_dataset_profile")))),
            (FakeContext(), response(types.Part(text=policy.refusal("out_of_scope", "en")))),
            (FakeContext(), response(types.Part(text=READY))),
        ],
    )
    async def test_no_edit(
        self, context: FakeContext, reply: LlmResponse, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        before = reply.model_copy(deep=True)

        assert await check(reply, context) == before
        assert lines == []

    async def test_a_failure_keeps_the_reply(self, ledger: RequestLedger, monkeypatch: pytest.MonkeyPatch) -> None:
        def broken(text: str) -> tuple[str, int]:
            raise RuntimeError("broken")

        monkeypatch.setattr(plugin_module, "drop_confirm", broken)
        text = f"{READY} Press `.confirm()`."

        assert reply_text(await check(response(types.Part(text=text)))) == text


async def test_the_streamed_reply_after_a_shipped_plot_drops_the_ask(client: httpx.AsyncClient, swap_models) -> None:
    """The pipeline marks the turn shipped, the Budget plugin spends `plot_shipped` on the closing call, and the
    edited reply is what the page receives."""
    swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": f"{READY} The data is still unconfirmed, so press `.confirm()` in the data panel."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)

    events = await create_plot(client, sid)

    assert next(data for name, data in events if name == "plot")["status"] == "ok"
    assert [data["text"] for name, data in events if name == "message"] == [READY]
