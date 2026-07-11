"""Tests for automation.benchmark.vertex_client provider routing."""

import pytest

from automation.benchmark.vertex_client import (
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENAPI,
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
