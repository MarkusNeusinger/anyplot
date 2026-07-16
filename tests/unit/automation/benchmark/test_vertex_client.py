"""Tests for automation.benchmark.vertex_client provider routing."""

from types import SimpleNamespace

import pytest

from automation.benchmark.vertex_client import (
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENAPI,
    GenerationResult,
    VertexClient,
    _extract_openapi_text,
    resolve_provider,
)


class TestResolveProvider:
    """Model ids route to the Vertex surface that actually serves them."""

    def test_bare_claude_id(self):
        assert resolve_provider("claude-sonnet-4-5@20250929") == (PROVIDER_ANTHROPIC, "claude-sonnet-4-5@20250929")

    def test_anthropic_prefixed_id_is_stripped(self):
        assert resolve_provider("anthropic/claude-opus-4-1@20250805") == (
            PROVIDER_ANTHROPIC,
            "claude-opus-4-1@20250805",
        )

    def test_bare_gemini_id_gets_google_prefix(self):
        assert resolve_provider("gemini-2.5-pro") == (PROVIDER_OPENAPI, "google/gemini-2.5-pro")

    def test_google_prefixed_gemini_id_passes_through(self):
        assert resolve_provider("google/gemini-2.5-flash") == (PROVIDER_OPENAPI, "google/gemini-2.5-flash")

    def test_model_garden_partner_ids_pass_through(self):
        for model in ("meta/llama-3.3-70b-instruct-maas", "mistralai/mistral-large-2411", "qwen/qwen3-coder"):
            assert resolve_provider(model) == (PROVIDER_OPENAPI, model)

    def test_whitespace_is_trimmed(self):
        assert resolve_provider("  gemini-2.5-pro ") == (PROVIDER_OPENAPI, "google/gemini-2.5-pro")

    def test_unroutable_id_raises(self):
        with pytest.raises(ValueError, match="Cannot route model id"):
            resolve_provider("gpt-5")

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            resolve_provider("   ")


class TestOpenapiUrl:
    """The chat-completions URL follows Vertex's regional host scheme."""

    def test_regional_location(self):
        client = VertexClient(project="anyplot", location="us-central1")
        assert client._openapi_url() == (
            "https://us-central1-aiplatform.googleapis.com/v1/projects/anyplot"
            "/locations/us-central1/endpoints/openapi/chat/completions"
        )

    def test_global_location_drops_region_prefix(self):
        client = VertexClient(project="anyplot", location="global")
        assert client._openapi_url() == (
            "https://aiplatform.googleapis.com/v1/projects/anyplot/locations/global/endpoints/openapi/chat/completions"
        )


class TestGenerateRouting:
    """generate() dispatches by provider and stamps wall-clock latency."""

    def _stub_result(self, model):
        return GenerationResult(text="code", model=model, provider="stub", latency_seconds=0.0)

    def test_claude_id_dispatches_to_anthropic(self, monkeypatch):
        client = VertexClient(project="anyplot")
        called = {}

        def fake_anthropic(model, system, prompt, max_tokens, temperature):
            called["args"] = (model, system, prompt, max_tokens, temperature)
            return self._stub_result(model)

        monkeypatch.setattr(client, "_generate_anthropic", fake_anthropic)
        result = client.generate("claude-sonnet-4-5@20250929", "sys", "user", max_tokens=42, temperature=0.5)
        assert called["args"] == ("claude-sonnet-4-5@20250929", "sys", "user", 42, 0.5)
        assert result.latency_seconds >= 0.0

    def test_gemini_id_dispatches_to_openapi_with_publisher_prefix(self, monkeypatch):
        client = VertexClient(project="anyplot")
        called = {}

        def fake_openapi(model, system, prompt, max_tokens, temperature):
            called["model"] = model
            return self._stub_result(model)

        monkeypatch.setattr(client, "_generate_openapi", fake_openapi)
        client.generate("gemini-2.5-pro", "sys", "user")
        assert called["model"] == "google/gemini-2.5-pro"


class TestGenerateAnthropic:
    """Claude on Vertex goes through the Anthropic SDK transport."""

    class _FakeAnthropicVertex:
        last_init = None

        def __init__(self, **kwargs):
            type(self).last_init = kwargs
            self.messages = SimpleNamespace(create=self._create)

        def _create(self, **kwargs):
            self.last_create = kwargs
            return SimpleNamespace(
                content=[
                    SimpleNamespace(type="thinking", text="ignored"),
                    SimpleNamespace(type="text", text="the code"),
                ],
                usage=SimpleNamespace(input_tokens=100, output_tokens=50),
            )

    def test_response_text_and_usage(self, monkeypatch):
        import anthropic

        monkeypatch.setattr(anthropic, "AnthropicVertex", self._FakeAnthropicVertex)
        client = VertexClient(project="anyplot", anthropic_location="europe-west1")
        result = client._generate_anthropic("claude-sonnet-4-5@20250929", "sys", "user", 1000, 0.2)

        assert result.text == "the code"  # non-text blocks are skipped
        assert result.provider == PROVIDER_ANTHROPIC
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert self._FakeAnthropicVertex.last_init["project_id"] == "anyplot"
        assert self._FakeAnthropicVertex.last_init["region"] == "europe-west1"


class TestGenerateOpenapi:
    """Gemini / Model Garden go through the OpenAI-compatible endpoint."""

    def _fake_response(self, status_code=200, body=None, text="err"):
        return SimpleNamespace(status_code=status_code, json=lambda: body, text=text)

    def test_success_parses_text_and_usage(self, monkeypatch):
        from automation.benchmark import vertex_client

        client = VertexClient(project="anyplot")
        monkeypatch.setattr(client, "_access_token", lambda: "tok")
        captured = {}

        def fake_post(url, json=None, headers=None, timeout=None):
            captured.update(url=url, json=json, headers=headers)
            return self._fake_response(
                body={
                    "choices": [{"message": {"content": "gemini code"}}],
                    "usage": {"prompt_tokens": 11, "completion_tokens": 7},
                }
            )

        monkeypatch.setattr(vertex_client.httpx, "post", fake_post)
        result = client._generate_openapi("google/gemini-2.5-pro", "sys", "user", 1000, 0.2)

        assert result.text == "gemini code"
        assert result.provider == PROVIDER_OPENAPI
        assert result.input_tokens == 11
        assert result.output_tokens == 7
        assert captured["headers"]["Authorization"] == "Bearer tok"
        assert captured["json"]["model"] == "google/gemini-2.5-pro"
        assert captured["json"]["messages"][0]["role"] == "system"

    def test_non_200_raises_with_model_and_status(self, monkeypatch):
        from automation.benchmark import vertex_client

        client = VertexClient(project="anyplot")
        monkeypatch.setattr(client, "_access_token", lambda: "tok")
        monkeypatch.setattr(
            vertex_client.httpx, "post", lambda *a, **k: self._fake_response(status_code=404, text="model not found")
        )
        with pytest.raises(RuntimeError, match="HTTP 404.*model not found"):
            client._generate_openapi("meta/nope", "sys", "user", 1000, 0.2)


class TestAccessToken:
    def test_returns_token_from_adc(self, monkeypatch):
        import google.auth

        creds = SimpleNamespace(valid=True, token="adc-token")
        monkeypatch.setattr(google.auth, "default", lambda scopes: (creds, "anyplot"))
        client = VertexClient(project="anyplot")
        assert client._access_token() == "adc-token"

    def test_empty_token_raises(self, monkeypatch):
        import google.auth

        creds = SimpleNamespace(valid=True, token=None)
        monkeypatch.setattr(google.auth, "default", lambda scopes: (creds, "anyplot"))
        client = VertexClient(project="anyplot")
        with pytest.raises(RuntimeError, match="access token"):
            client._access_token()


class TestExtractOpenapiText:
    """Both OpenAI content shapes (string and parts list) are accepted."""

    def test_string_content(self):
        body = {"choices": [{"message": {"content": "hello"}}]}
        assert _extract_openapi_text(body) == "hello"

    def test_parts_list_content(self):
        body = {"choices": [{"message": {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}}]}
        assert _extract_openapi_text(body) == "ab"

    def test_no_choices_raises(self):
        with pytest.raises(RuntimeError, match="no choices"):
            _extract_openapi_text({"choices": []})

    def test_unexpected_content_shape_raises(self):
        with pytest.raises(RuntimeError, match="Unexpected content shape"):
            _extract_openapi_text({"choices": [{"message": {"content": 42}}]})
