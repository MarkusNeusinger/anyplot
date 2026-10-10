"""Tests for `sub_agents.adapter.schema_guard`: mend a formal miss, blank the rest, log rules but never content."""

import json
import logging
from dataclasses import dataclass
from typing import Any, cast

import pytest
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import ValidationError

from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger
from agents.anyplot.schemas import MAX_DEFECT_TEXT_CHARS, AdaptPlan, Verdict, repair_plan, repair_verdict
from agents.anyplot.sub_agents.adapter import schema_errors, schema_guard


CANARY = "CANARY-ANSWER-41d9"


@dataclass
class FakeCallbackContext:
    agent_name: str = "reviewer"
    invocation_id: str = "inv-guard"


@pytest.fixture
def ledger() -> Any:
    current = RequestLedger(request_id="req-guard", user_id="adm_1", session_id="s1")
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


def answer(payload: Any, finish: str = "STOP") -> LlmResponse:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=text)]), finish_reason=types.FinishReason[finish]
    )


def text_of(response: LlmResponse) -> str:
    assert response.content is not None and response.content.parts
    return "".join(part.text or "" for part in response.content.parts)


def schema_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == "anyplot.agents.attribution"]
    return [line for line in lines if line["hook"] == "answer_schema"]


def defect(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "VQ-02",
        "theme": "light",
        "observed": "legend covers the last bars",
        "target": "legend outside the axes",
        "likely_cause": "ax.legend loc",
        **overrides,
    }


async def guard(schema: type[Verdict] | type[AdaptPlan], repair: Any, response: LlmResponse, agent: str) -> None:
    context = cast(CallbackContext, FakeCallbackContext(agent_name=agent))
    result = await schema_guard(schema, repair)(context, response)
    assert result is None  # the guard edits the response in place and never replaces it


@pytest.mark.usefixtures("ledger")
class TestSchemaGuard:
    async def test_a_valid_answer_is_untouched_and_not_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
        valid = {"ok": False, "defects": [defect()]}
        response = answer(valid)

        await guard(Verdict, repair_verdict, response, "reviewer")

        assert json.loads(text_of(response)) == valid
        assert schema_lines(caplog) == []

    async def test_a_long_observed_is_mended_and_its_rule_logged_without_content(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
        observed = f"{CANARY} " + "the legend covers the last two bars of the chart " * 6
        response = answer({"ok": True, "defects": [defect(observed=observed)]})

        await guard(Verdict, repair_verdict, response, "reviewer")

        verdict = Verdict.model_validate_json(text_of(response))
        assert verdict.ok is False and len(verdict.defects[0].observed) == MAX_DEFECT_TEXT_CHARS
        (line,) = schema_lines(caplog)
        assert (line["agent"], line["outcome"]) == ("reviewer", "repaired")
        # The ok/defects rule runs after the field rules, so a field miss hides it.
        assert line["errors"] == ["defects.0.observed:string_too_long"]
        assert not any(CANARY in record.getMessage() for record in caplog.records)

    async def test_a_rejection_without_a_usable_defect_is_blanked(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
        response = answer({"ok": False, "defects": [defect(id="VQ-05", observed=CANARY)]})

        await guard(Verdict, repair_verdict, response, "reviewer")

        assert text_of(response) == ""  # ADK's output becomes None: an unread review
        (line,) = schema_lines(caplog)
        assert (line["outcome"], line["errors"]) == ("refused", ["defects.0.id:literal_error"])
        assert not any(CANARY in record.getMessage() for record in caplog.records)

    async def test_text_that_is_not_json_is_blanked(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
        response = answer(f"I think the plot is fine. {CANARY}")

        await guard(Verdict, repair_verdict, response, "reviewer")

        assert text_of(response) == ""
        (line,) = schema_lines(caplog)
        assert (line["outcome"], line["errors"]) == ("refused", ["answer:json_invalid"])
        assert not any(CANARY in record.getMessage() for record in caplog.records)

    async def test_a_fenced_answer_is_mended_too(self) -> None:
        fenced = "```json\n" + json.dumps({"ok": True, "defects": [defect()]}) + "\n```"
        response = answer(fenced)

        await guard(Verdict, repair_verdict, response, "reviewer")

        assert Verdict.model_validate_json(text_of(response)).ok is False

    async def test_a_plan_with_six_changes_keeps_five(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
        plan = {"edits": [{"find": "a", "replace": "b"}], "changes": [f"{CANARY} {n}" for n in range(6)]}
        response = answer(plan)

        await guard(AdaptPlan, repair_plan, response, "adapter_matplotlib")

        assert len(AdaptPlan.model_validate_json(text_of(response)).changes) == 5
        (line,) = schema_lines(caplog)
        assert (line["agent"], line["outcome"], line["errors"]) == (
            "adapter_matplotlib",
            "repaired",
            ["changes:too_long"],
        )
        assert not any(CANARY in record.getMessage() for record in caplog.records)

    async def test_a_cut_off_answer_is_blanked_without_a_repair(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="anyplot.agents.attribution")
        response = answer({"edits": [{"find": "a", "replace": "b"}], "changes": ["x"] * 6}, finish="MAX_TOKENS")

        await guard(AdaptPlan, repair_plan, response, "adapter_matplotlib")

        assert text_of(response) == ""
        assert schema_lines(caplog) == []


class TestSchemaErrors:
    def test_locations_are_field_names_and_indices(self) -> None:
        with pytest.raises(ValidationError) as caught:
            Verdict.model_validate({"ok": False, "defects": [defect(theme="sepia", target="")]})

        assert schema_errors(caught.value) == ["defects.0.theme:literal_error", "defects.0.target:string_too_short"]

    def test_a_non_validation_error_names_its_class(self) -> None:
        assert schema_errors(ValueError(CANARY)) == ["answer:ValueError"]
