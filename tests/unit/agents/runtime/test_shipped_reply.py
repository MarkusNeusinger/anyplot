"""Tests for the shipped-reply check: after a shipped plot the root's reply never asks for `.confirm()`."""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any, cast

import httpx
import pytest
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.anyplot import policy
from agents.anyplot.plugins import reply_language
from agents.anyplot.plugins import shipped_reply as plugin_module
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger
from agents.anyplot.plugins.reply_language import ReplyLanguagePlugin, reply_text
from agents.anyplot.plugins.shipped_reply import ShippedReplyPlugin, drop_confirm
from agents.anyplot.services import Services
from agents.anyplot.session_state import LANGUAGE, LANGUAGE_SOURCE
from agents.main import Runtime, app, get_runtime

from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_reply_language import REPLIES, FakeModel
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
        callback_context=cast(Any, context or FakeContext()), llm_response=reply
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

    @pytest.mark.parametrize("shipped", [True, False])
    async def test_a_sentence_that_names_the_plot_button_goes_in_any_turn(
        self, shipped: bool, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        """The line at the chat's foot names the plot button; a reply never sends the user to it, before a
        plot (a kept wish, a `data_unconfirmed`) or after one."""
        ledger.shipped_in_turn = shipped
        summary = "48 rows and 4 columns: x is month, y is revenue."
        text = f"{summary} Check the bindings and press `.create_plot()` to draw it."

        reply = await check(response(types.Part(text=text)))

        assert reply_text(reply) == summary
        assert lines == [{"verdict": "dropped", "sentences": 1}]

    @pytest.mark.parametrize(
        ("text", "kept", "dropped"),
        [
            (f"{READY} Type a change and press `.update_plot()`.", READY, 1),
            ("Ich merke mir den Titel. Drück dann .create_plot().", "Ich merke mir den Titel.", 1),
            (f"{READY}\n\n- Use `.plot_all()` for every library.", READY, 1),
            ("Press `.create_plot()`.", "", 1),
        ],
    )
    def test_drops_every_sentence_that_names_the_plot_button(self, text: str, kept: str, dropped: int) -> None:
        assert plugin_module.drop_plot_button(text) == (kept, dropped)

    async def test_a_reply_after_a_shipped_plot_loses_both_asks(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        text = f"{READY} Confirm with `.confirm()`. Then press `.update_plot()` for more."

        reply = await check(response(types.Part(text=text)))

        assert reply_text(reply) == READY
        assert lines == [{"verdict": "dropped", "sentences": 1}, {"verdict": "dropped", "sentences": 1}]

    @pytest.mark.parametrize(
        ("text", "kept", "verdict"),
        [
            # A one-sentence answer to "how do I plot?" is all the reply there is: it stays whole.
            (
                "Press `.create_plot()` beside the message box to draw it.",
                "Press `.create_plot()` beside the message box to draw it.",
                {"verdict": "kept", "sentences": 1},
            ),
            # A mixed reply loses the button's sentence alone.
            (
                "I kept the title for the first plot. Press `.create_plot()` once y has a column. Then it draws.",
                "I kept the title for the first plot. Then it draws.",
                {"verdict": "dropped", "sentences": 1},
            ),
            # A German reply the same: the button's name is the same in every language.
            (
                "Ich habe die Spalte umbenannt: 48 Zeilen. Drück danach `.update_plot()`, um den Plot zu ändern.",
                "Ich habe die Spalte umbenannt: 48 Zeilen.",
                {"verdict": "dropped", "sentences": 1},
            ),
        ],
    )
    async def test_the_plot_button_check_keeps_a_lone_answer_and_drops_the_ask_in_any_language(
        self, text: str, kept: str, verdict: dict[str, Any], ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        ledger.shipped_in_turn = False

        assert reply_text(await check(response(types.Part(text=text)))) == kept
        assert lines == [verdict]

    @pytest.mark.parametrize(
        ("text", "kept"),
        [
            # An abbreviation's dot ends no sentence: the button's sentence goes whole, nothing of it stays.
            ("The data has 6 rows. Press `.create_plot()`, e.g. with a title in the box.", "The data has 6 rows."),
            ("Press `.create_plot()`, i.e. the button. The data has 6 rows.", "The data has 6 rows."),
            (
                "Die Daten haben 6 Zeilen. Drück `.create_plot()`, z. B. mit einem Titel im Feld.",
                "Die Daten haben 6 Zeilen.",
            ),
            (
                "Der Umsatz liegt bei 6,5 Mio. Euro. Drück dann `.update_plot()` für den neuen Plot.",
                "Der Umsatz liegt bei 6,5 Mio. Euro.",
            ),
            ("Ich habe bzw. Spalten umbenannt. Drück ca. jetzt `.create_plot()`.", "Ich habe bzw. Spalten umbenannt."),
        ],
    )
    def test_an_abbreviation_ends_no_sentence(self, text: str, kept: str) -> None:
        assert plugin_module.drop_plot_button(text) == (kept, 1)

    async def test_an_answer_to_a_question_about_the_button_keeps_it(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        """The user asked about the button: the answer names it, and a short filler before it must not be all that
        is left. The tools the turn ran come back as user content without text, after the question."""
        ledger.shipped_in_turn = False
        ledger.root_request = LlmRequest(
            model="m",
            contents=[
                types.Content(role="user", parts=[types.Part(text="what does .update_plot() do?")]),
                types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name="get_spec"))]),
                types.Content(
                    role="user",
                    parts=[types.Part(function_response=types.FunctionResponse(name="get_spec", response={}))],
                ),
            ],
        )
        text = "Sure. `.update_plot() →` redraws the plot with the change in the box."

        assert reply_text(await check(response(types.Part(text=text)))) == text
        assert lines == [{"verdict": "asked", "sentences": 0}]

    @pytest.mark.parametrize(
        "message",
        [
            "add a column z",
            # A mention of the button is no question about it.
            "I already pressed .create_plot(); now add a column z",
            # A question about something else, beside a mention.
            "I pressed .create_plot(), add a column z",
        ],
    )
    async def test_a_message_that_asks_nothing_about_the_button_drops_it_as_ever(
        self, message: str, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        ledger.shipped_in_turn = False
        ledger.root_request = LlmRequest(
            model="m", contents=[types.Content(role="user", parts=[types.Part(text=message)])]
        )
        text = "I added the column. Check the data and press `.create_plot()`."

        assert reply_text(await check(response(types.Part(text=text)))) == "I added the column."
        assert lines == [{"verdict": "dropped", "sentences": 1}]

    async def test_a_german_question_about_the_button_keeps_the_answer(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        ledger.shipped_in_turn = False
        ledger.root_request = LlmRequest(
            model="m", contents=[types.Content(role="user", parts=[types.Part(text="Was macht .create_plot()?")])]
        )
        text = "Klar. `.create_plot()` übernimmt die Daten, wie die Karte sie zeigt, und zeichnet den Plot."

        assert reply_text(await check(response(types.Part(text=text)))) == text
        assert lines == [{"verdict": "asked", "sentences": 0}]

    async def test_two_checks_that_would_leave_nothing_keep_the_reply_as_written(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        """After a shipped plot, `.confirm()` goes first; when the plot button's sentence is all that is left, the
        reply goes out whole, never as what the first check left of it."""
        text = "Confirm with `.confirm()`. Then press `.create_plot()`."

        assert reply_text(await check(response(types.Part(text=text)))) == text
        assert lines == [{"verdict": "kept", "sentences": 1}, {"verdict": "kept", "sentences": 1}]

    async def test_a_reply_that_only_names_the_plot_button_stays_whole(
        self, ledger: RequestLedger, lines: list[dict[str, Any]]
    ) -> None:
        ledger.shipped_in_turn = False
        text = "Press `.create_plot()` once the bindings look right."

        assert reply_text(await check(response(types.Part(text=text)))) == text
        assert lines == [{"verdict": "kept", "sentences": 1}]

    async def test_a_language_reask_gets_the_same_check(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch, lines: list[dict[str, Any]]
    ) -> None:
        """ReplyLanguage's re-ask is a direct model call no plugin sees: its reply is checked before it replaces."""
        german = "Bestätige die Daten bitte noch mit `.confirm()`."
        model = FakeModel([f"{REPLIES['de']} {german}"])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)
        context = FakeContext(session=FakeSession(state={LANGUAGE: "de", LANGUAGE_SOURCE: "offer"}))
        first = response(types.Part(text=f"{REPLIES['en']} Now confirm your data with `.confirm()`."))
        language = ReplyLanguagePlugin()
        request = LlmRequest(model="m", contents=[types.Content(role="user", parts=[types.Part(text="x")])])
        await language.before_model_callback(callback_context=cast(Any, context), llm_request=request)

        # In the App's order: ShippedReply edits the first reply in place, then ReplyLanguage asks again.
        await check(first, context)
        replaced = await language.after_model_callback(callback_context=cast(Any, context), llm_response=first)

        assert reply_text(first) == REPLIES["en"]
        assert model.requests[0].contents[-2].parts[0].text == REPLIES["en"]  # the re-ask sees the edited reply
        assert replaced is not None and reply_text(replaced) == REPLIES["de"]
        assert [line["verdict"] for line in lines] == ["dropped", "dropped"]


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
