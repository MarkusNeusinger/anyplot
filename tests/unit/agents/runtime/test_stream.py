"""Tests for the anyplot/1 translator (agents/stream.py) and the caller check (agents/main.py)."""

import base64
import json

import pytest
from google.adk.events.event import Event
from google.genai import types

from agents.anyplot.plugins.ledger import RequestLedger
from agents.main import AgentsError, check_caller, decode_claims
from agents.stream import CODE_OMITTED, MAX_MESSAGE_CHARS, Translator, sanitize


def parse(chunk: str) -> tuple[str, dict]:
    lines = dict(line.split(": ", 1) for line in chunk.strip().splitlines())
    return lines["event"], json.loads(lines["data"])


def text_event(author: str, text: str, **extra: object) -> Event:
    return Event(author=author, content=types.Content(role="model", parts=[types.Part(text=text)]), **extra)


@pytest.fixture
def translator() -> Translator:
    return Translator(
        RequestLedger(request_id="req-7", llm_calls=3, tokens=900), run_id="run-1", spec_id="scatter-basic"
    )


class TestTranslator:
    def test_ready_and_done(self, translator: Translator) -> None:
        assert parse(translator.ready()) == ("ready", {"v": "anyplot/1", "run_id": "run-1"})
        assert parse(translator.done()) == ("done", {"llm_calls": 3, "tokens": 900})

    def test_queued_status(self, translator: Translator) -> None:
        assert parse(translator.queued(2, 5)) == ("status", {"step": "queued", "position": 2, "waiting": 5})

    def test_a_pipeline_event_cannot_claim_the_queued_step(self, translator: Translator) -> None:
        """`queued` comes only from the route; a pipeline status with that step is dropped."""
        forged = Event(author="plot_pipeline", custom_metadata={"anyplot_status": {"step": "queued", "attempt": 1}})

        assert translator.translate(forged) == []

    def test_status_from_custom_metadata_only(self, translator: Translator) -> None:
        status = Event(author="plot_pipeline", custom_metadata={"anyplot_status": {"step": "rendering", "attempt": 2}})
        unknown = Event(author="plot_pipeline", custom_metadata={"anyplot_status": {"step": "exfiltrating"}})

        assert [parse(chunk) for chunk in translator.translate(status)] == [
            ("status", {"step": "rendering", "attempt": 2})
        ]
        assert translator.translate(unknown) == []

    def test_plot_once_with_allowlisted_fields(self, translator: Translator) -> None:
        output = {"status": "ok", "attempts": 1, "artifacts": [], "changes": [], "residual_defects": [], "secret": 1}
        event = Event(author="plot_pipeline", output=output)

        chunks = translator.translate(event)
        assert [parse(chunk)[0] for chunk in chunks] == ["plot"]
        assert "secret" not in parse(chunks[0])[1]
        assert translator.translate(event) == []

    def test_messages_only_from_the_root(self, translator: Translator) -> None:
        assert [parse(c) for c in translator.translate(text_event("anyplot", "Done."))] == [
            ("message", {"text": "Done."})
        ]
        assert translator.translate(text_event("adapter_matplotlib", '{"edits": []}')) == []
        assert translator.translate(text_event("reviewer", '{"ok": true}')) == []
        assert translator.translate(text_event("plot_pipeline", "adapting")) == []

    def test_partials_thoughts_and_function_calls_are_dropped(self, translator: Translator) -> None:
        partial = text_event("anyplot", "Do", partial=True)
        thought = Event(
            author="anyplot", content=types.Content(role="model", parts=[types.Part(text="secret plan", thought=True)])
        )
        call = Event(
            author="anyplot",
            content=types.Content(
                role="model", parts=[types.Part(function_call=types.FunctionCall(name="plot_pipeline", args={}))]
            ),
        )
        response = Event(
            author="anyplot",
            content=types.Content(
                role="user",
                parts=[
                    types.Part(function_response=types.FunctionResponse(name="get_dataset_profile", response={"x": 1}))
                ],
            ),
        )
        assert all(translator.translate(event) == [] for event in (partial, thought, call, response))

    def test_refusal_replaces_the_message(self) -> None:
        ledger = RequestLedger(request_id="r")
        ledger.refuse("out_of_scope", "I can only help with this plot.")
        translator = Translator(ledger, "run")

        chunks = translator.translate(text_event("model", "I can only help with this plot."))

        assert [parse(chunk) for chunk in chunks] == [
            ("refusal", {"code": "out_of_scope", "text": "I can only help with this plot."})
        ]

    def test_guard_unavailable_is_an_error_once(self) -> None:
        ledger = RequestLedger(request_id="r-9")
        ledger.fail("guard_unavailable")
        translator = Translator(ledger, "run")

        first = translator.translate(text_event("model", "could not check"))
        assert [parse(chunk) for chunk in first] == [("error", {"code": "guard_unavailable", "ref": "r-9"})]
        assert translator.error("guard_unavailable") == []


class TestSanitize:
    def test_strips_urls_html_images_and_links(self) -> None:
        text = (
            "See <b>this</b> ![x](https://evil/x.png) [docs](https://evil/docs) and www.evil.com or data:text/html,hi"
        )

        assert sanitize(text) == "See this  docs and  or"

    def test_long_code_blocks_are_omitted_short_ones_kept(self) -> None:
        short = "```python\nax.set_title('x')\n```"
        long = "```python\n" + "\n".join(f"line{i}" for i in range(12)) + "\n```"

        assert sanitize(short) == short
        assert sanitize("Here:\n" + long) == "Here:\n" + CODE_OMITTED

    @pytest.mark.parametrize(
        ("opening", "closing"), [("~~~python", "~~~"), ("````", "````"), ("  ```py", "```"), ("~~~~", "~~~~")]
    )
    def test_every_fence_style_is_omitted_when_long(self, opening: str, closing: str) -> None:
        body = "\n".join(f"v{i} = {i}" for i in range(20))

        assert sanitize(f"Here is the code:\n{opening}\n{body}\n{closing}\nand more") == (
            f"Here is the code:\n{CODE_OMITTED}\nand more"
        )

    def test_a_block_of_exactly_ten_lines_is_kept(self) -> None:
        block = "```\n" + "\n".join(f"v{i} = {i}" for i in range(10)) + "\n```"

        assert sanitize(block) == block

    def test_long_indented_code_is_omitted(self) -> None:
        indented = "\n".join(f"    v{i} = {i}" for i in range(12))
        tabbed = "\n".join(f"\tv{i} = {i}" for i in range(12))

        assert sanitize(f"Code:\n{indented}\nend") == f"Code:\n{CODE_OMITTED}\nend"
        assert sanitize(f"Code:\n{tabbed}") == f"Code:\n{CODE_OMITTED}"
        assert sanitize("    short = 1\n    two = 2") == "short = 1\n    two = 2"

    def test_more_link_and_tag_forms(self) -> None:
        assert sanitize("see //evil.example/x now") == "see  now"
        assert sanitize("write mailto:a@b.c today") == "write  today"
        assert sanitize("hi <img src=x onerror=alert(1) ") == "hi"
        assert sanitize("keep a // b and x < 5") == "keep a // b and x < 5"

    def test_plot_changes_and_defects_are_plain_lines(self, translator: Translator) -> None:
        output = {
            "status": "needs_attention",
            "attempts": 1,
            "artifacts": [],
            "changes": [
                "Get the fixed file at https://evil.example/x <img src=x onerror=alert(1)> ![p](http://e/p.png)",
                "```\n" + "\n".join("x" for _ in range(12)) + "\n```",
            ],
            "residual_defects": ["VQ-03 (both): small markers → s=250 (+120). Likely cause: [size](//e/x)."],
        }

        _, plot = parse(translator.translate(Event(author="plot_pipeline", output=output))[0])

        assert plot["changes"] == ["Get the fixed file at"]
        assert plot["residual_defects"] == ["VQ-03 (both): small markers → s=250 (+120). Likely cause: size."]

    def test_spec_tokens_only_for_the_session_spec(self) -> None:
        assert sanitize("[[spec:scatter-basic]] [[spec:other]]", spec_id="scatter-basic") == "[[spec:scatter-basic]]"

    def test_cap(self) -> None:
        assert len(sanitize("a" * 5000)) == MAX_MESSAGE_CHARS


def token(claims: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"Bearer eyJhbGciOiJSUzI1NiJ9.{body}.SIGNATURE_REMOVED_BY_GOOGLE"


class FakeRequest:
    def __init__(self, authorization: str | None) -> None:
        self.headers = {"authorization": authorization} if authorization else {}


class TestCallerCheck:
    def test_decode_without_verification(self) -> None:
        assert decode_claims(token({"aud": "a", "email": "e"})) == {"aud": "a", "email": "e"}
        assert decode_claims("Bearer nonsense") is None
        assert decode_claims(None) is None

    def test_skipped_in_development(self) -> None:
        check_caller(FakeRequest(None))

    def test_production_requires_audience_and_caller(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from agents.anyplot.settings import get_settings

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("AGENT_SERVICE_URLS", "https://anyplot-agents.run.app")
        monkeypatch.setenv("AGENT_ALLOWED_CALLERS", "api@anyplot.iam.gserviceaccount.com")
        get_settings.cache_clear()
        good = {"aud": "https://anyplot-agents.run.app", "email": "api@anyplot.iam.gserviceaccount.com"}

        check_caller(FakeRequest(token(good)))
        for claims, status in (
            (None, 401),
            ({**good, "aud": "https://other.run.app"}, 403),
            ({**good, "email": "attacker@example.com"}, 403),
        ):
            with pytest.raises(AgentsError) as caught:
                check_caller(FakeRequest(token(claims) if claims else None))
            assert caught.value.status == status
