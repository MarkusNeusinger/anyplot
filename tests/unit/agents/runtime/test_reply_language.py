"""Tests for the reply-language check: the offline detector and the plugin's one re-ask."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.anyplot import policy
from agents.anyplot.language_detect import DETECTABLE, detect, expected_code, mismatch
from agents.anyplot.plugins import reply_language as plugin_module
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger
from agents.anyplot.plugins.reply_language import REASK_LINE, ReplyLanguagePlugin, reply_text
from agents.anyplot.services import Services
from agents.anyplot.session_state import LANGUAGE, LANGUAGE_SOURCE


# Replies of the kind the root writes, one per language: a data summary with column names in backticks.
REPLIES: dict[str, str] = {
    "en": "The table has 6 rows and 3 columns: `Jahr`, `Staatsangehörigkeit` and `Bestand`. No values are missing. "
    "The bindings propose `Jahr` for the x axis and `Bestand` for the values. Should the two groups be separate lines?",
    "de": "Die Tabelle hat 6 Zeilen und 3 Spalten: `Year`, `Origin` und `Population`. Es fehlen keine Werte. Die "
    "Zuordnung schlägt `Year` für die x-Achse vor. Sollen die beiden Gruppen als eigene Linien erscheinen?",
    "fr": "Le tableau contient 6 lignes et 3 colonnes. Aucune valeur ne manque. Les liaisons proposent `Jahr` pour "
    "l'axe x et `Bestand` pour les valeurs. Voulez-vous que les deux groupes soient des lignes séparées ?",
    "es": "La tabla tiene 6 filas y 3 columnas. No falta ningún valor. Las asignaciones proponen `Jahr` para el eje x "
    "y `Bestand` para los valores. ¿Quieres que los dos grupos sean líneas separadas?",
    "it": "La tabella ha 6 righe e 3 colonne. Non mancano valori. Le associazioni propongono `Jahr` per l'asse x e "
    "`Bestand` per i valori. Vuoi che i due gruppi siano linee separate?",
    "pt": "A tabela tem 6 linhas e 3 colunas. Não falta nenhum valor. As associações propõem `Jahr` para o eixo x e "
    "`Bestand` para os valores. Você quer que os dois grupos sejam linhas separadas?",
    "nl": "De tabel heeft 6 rijen en 3 kolommen. Er ontbreken geen waarden. De koppelingen stellen `Jahr` voor de "
    "x-as en `Bestand` voor de waarden voor. Wil je dat de twee groepen aparte lijnen worden?",
    "pl": "Tabela ma 6 wierszy i 3 kolumny. Nie brakuje żadnych wartości. Powiązania proponują `Jahr` dla osi x i "
    "`Bestand` dla wartości. Czy chcesz, żeby obie grupy były osobnymi liniami?",
    "ru": "Таблица содержит 6 строк и 3 столбца. Пропущенных значений нет.",
    "zh": "表格有6行3列。没有缺失值。",
    "ja": "表には6行3列があります。欠損値はありません。",
    "vi": "Bảng có 6 hàng và 3 cột. Không có giá trị nào bị thiếu.",
}


class TestDetect:
    @pytest.mark.parametrize("code", sorted(REPLIES))
    def test_each_known_language(self, code: str) -> None:
        assert detect(REPLIES[code]) == code

    def test_every_known_language_has_a_sample(self) -> None:
        assert set(REPLIES) == DETECTABLE

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "Done.",
            "Fertig, der Plot ist da.",  # too short to be sure
            "`Jahr`, `Bestand`, `Staatsangehörigkeit`, `Kanton`, `Geschlecht`, `Wert`",  # only quoted names
            "12 rows, 3 columns, 2024-01-01 to 2024-12-31.",
        ],
    )
    def test_unsure_is_none(self, text: str) -> None:
        assert detect(text) is None

    def test_quoted_column_names_do_not_decide(self) -> None:
        """German column names in an English reply: the backticks and quotes keep them out of the count."""
        text = (
            'The column `Staatsangehörigkeit der Person` has two values, "Schweiz und Ausland", and the bindings put '
            "it on the color. Each year has one row per group, so the plot shows two lines."
        )
        assert detect(text) == "en"

    def test_expected_code_takes_names_and_endonyms(self) -> None:
        assert expected_code("Deutsch") == expected_code("German") == expected_code("de") == "de"
        assert expected_code("Swedish") is None and expected_code("Klingon") is None

    def test_mismatch_only_when_sure_and_different(self) -> None:
        assert mismatch(REPLIES["en"], "de") == "en"
        assert mismatch(REPLIES["de"], "Deutsch") is None
        assert mismatch("Done.", "de") is None
        assert mismatch(REPLIES["en"], "Swedish") is None  # a language the detector does not know is never checked


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


@dataclass
class FakeModel:
    """Answers each `generate_content_async` with the next scripted text and records the requests."""

    answers: list[str]
    requests: list[LlmRequest] = field(default_factory=list)

    async def generate_content_async(self, request: LlmRequest, stream: bool = False) -> AsyncIterator[LlmResponse]:
        self.requests.append(request)
        text = self.answers.pop(0)
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=100, candidates_token_count=20
            ),
        )


@pytest.fixture
def ledger() -> Any:
    current = RequestLedger(request_id="req-1", user_id="adm_1", session_id="s1")
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


def response(text: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]))


def german_session(source: str = "pasted") -> FakeContext:
    return FakeContext(session=FakeSession(state={LANGUAGE: "de", LANGUAGE_SOURCE: source}))


async def run(context: FakeContext, reply: LlmResponse) -> LlmResponse | None:
    plugin = ReplyLanguagePlugin()
    request = LlmRequest(
        model="m",
        contents=[types.Content(role="user", parts=[types.Part(text="[action] Summarize the dataset for the user.")])],
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=[types.FunctionDeclaration(name="get_dataset_profile")])]
        ),
    )
    await plugin.before_model_callback(callback_context=context, llm_request=request)  # type: ignore[arg-type]
    return await plugin.after_model_callback(callback_context=context, llm_response=reply)  # type: ignore[arg-type]


class TestPlugin:
    async def test_a_wrong_language_reply_is_asked_again_once(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        model = FakeModel([REPLIES["de"]])
        monkeypatch.setattr(plugin_module, "root_model", lambda: model)

        result = await run(german_session(), response(REPLIES["en"]))

        assert result is not None and reply_text(result) == REPLIES["de"]
        (asked,) = model.requests
        assert asked.contents[-2].parts[0].text == REPLIES["en"]
        assert asked.contents[-1].parts[0].text == REASK_LINE.format(name="German")
        assert asked.config.tools is None and asked.tools_dict == {}
        assert ledger.reply_reasked and ledger.llm_calls == 1 and ledger.tokens == 120
        # A second final reply in the same turn is not asked again.
        assert await run(german_session(), response(REPLIES["en"])) is None and len(model.requests) == 1

    async def test_a_reask_still_in_the_wrong_language_keeps_the_first_reply(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(plugin_module, "root_model", lambda: FakeModel([REPLIES["fr"]]))

        assert await run(german_session(), response(REPLIES["en"])) is None

    @pytest.mark.parametrize(
        ("context", "reply"),
        [
            (german_session(), response(REPLIES["de"])),  # the right language
            (german_session(), response("Fertig.")),  # unsure
            (german_session("default"), response(REPLIES["en"])),  # the default is no signal
            (
                FakeContext(session=FakeSession(state={LANGUAGE: "Swedish", LANGUAGE_SOURCE: "chosen"})),
                response(REPLIES["en"]),
            ),
            (german_session(), response(policy.refusal("out_of_scope", "en"))),  # a fixed refusal is the service's own
            (
                german_session(),
                LlmResponse(
                    content=types.Content(
                        role="model", parts=[types.Part(function_call=types.FunctionCall(name="get_dataset_profile"))]
                    )
                ),
            ),
            (FakeContext(agent_name="adapter_matplotlib", session=german_session().session), response(REPLIES["en"])),
        ],
    )
    async def test_no_reask(
        self,
        context: FakeContext,
        reply: LlmResponse,
        ledger: RequestLedger,
        services: Services,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        model = FakeModel([REPLIES["de"]])
        monkeypatch.setattr(plugin_module, "root_model", lambda: model)

        assert await run(context, reply) is None
        assert model.requests == []

    async def test_log_only_when_reask_is_off(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        model = FakeModel([REPLIES["de"]])
        monkeypatch.setattr(plugin_module, "root_model", lambda: model)
        monkeypatch.setattr(plugin_module, "REASK", False)

        assert await run(german_session(), response(REPLIES["en"])) is None
        assert model.requests == []

    async def test_a_failing_model_keeps_the_reply(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def broken() -> Any:
            raise RuntimeError("down")

        monkeypatch.setattr(plugin_module, "root_model", broken)

        assert await run(german_session(), response(REPLIES["en"])) is None
