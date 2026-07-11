"""Vertex AI client with provider routing for multi-model benchmarking.

One GCP authentication (Application Default Credentials — locally via
``gcloud auth application-default login``, in GitHub Actions via Workload
Identity Federation) reaches every model family available on Vertex AI:

- **Anthropic Claude** models (``claude-*`` / ``anthropic/claude-*``) go
  through the Anthropic SDK's Vertex transport (``AnthropicVertex``),
  because Claude on Vertex speaks the Anthropic message schema via
  rawPredict rather than the shared chat-completions surface.
- **Everything else** — Google Gemini (``gemini-*`` / ``google/gemini-*``)
  and Model Garden model-as-a-service partners (``meta/*``, ``mistralai/*``,
  ``qwen/*``, ``deepseek-ai/*``, ``openai/*`` …) — goes through Vertex AI's
  OpenAI-compatible chat-completions endpoint, which accepts the
  publisher-prefixed model id directly.

This is what makes the benchmark cheap to extend: adding a model is a new
model id string, not a new integration.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAPI = "openapi"

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


@dataclass
class GenerationResult:
    """One model response plus the accounting the benchmark persists."""

    text: str
    model: str
    provider: str
    latency_seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None


def resolve_provider(model: str) -> tuple[str, str]:
    """Route a model id to its Vertex provider.

    Returns ``(provider, normalized_model)`` where ``normalized_model`` is the
    id the provider endpoint expects:

    - ``anthropic/claude-sonnet-4-5@20250929`` → ``("anthropic", "claude-sonnet-4-5@20250929")``
    - ``claude-sonnet-4-5@20250929``           → ``("anthropic", "claude-sonnet-4-5@20250929")``
    - ``gemini-2.5-pro``                       → ``("openapi", "google/gemini-2.5-pro")``
    - ``google/gemini-2.5-pro``                → ``("openapi", "google/gemini-2.5-pro")``
    - ``meta/llama-3.3-70b-instruct-maas``     → ``("openapi", "meta/llama-3.3-70b-instruct-maas")``

    Any ``publisher/model`` id is accepted and routed to the OpenAI-compatible
    endpoint — Model Garden's publisher list keeps growing, so the prefix is
    deliberately not validated against a fixed set; an unknown publisher fails
    at call time with Vertex's own error. Only bare ids without a recognizable
    family (``claude-*`` / ``gemini-*``) or publisher prefix raise ``ValueError``.
    """
    normalized = model.strip()
    if not normalized:
        raise ValueError("Model id must not be empty")

    if normalized.startswith("anthropic/"):
        return PROVIDER_ANTHROPIC, normalized.removeprefix("anthropic/")
    if normalized.startswith("claude-"):
        return PROVIDER_ANTHROPIC, normalized
    if normalized.startswith("gemini-"):
        return PROVIDER_OPENAPI, f"google/{normalized}"
    if "/" in normalized:
        return PROVIDER_OPENAPI, normalized

    raise ValueError(
        f"Cannot route model id '{model}': use 'claude-*' / 'anthropic/*' for Claude on Vertex, "
        "'gemini-*' / 'google/*' for Gemini, or a publisher-prefixed Model Garden id like "
        "'meta/llama-3.3-70b-instruct-maas'"
    )


class VertexClient:
    """Minimal text-generation client over Vertex AI with provider routing.

    ``location`` serves the OpenAI-compatible endpoint (Gemini + Model Garden);
    ``anthropic_location`` serves Claude, which Google hosts in a different
    set of regions (default ``us-east5``).
    """

    def __init__(
        self, project: str, location: str = "us-central1", anthropic_location: str = "us-east5", timeout: float = 600.0
    ) -> None:
        self.project = project
        self.location = location
        self.anthropic_location = anthropic_location
        self.timeout = timeout
        self._credentials = None

    def generate(
        self, model: str, system: str, prompt: str, max_tokens: int = 16000, temperature: float = 0.2
    ) -> GenerationResult:
        """Send one system+user exchange to ``model`` and return the reply."""
        provider, normalized = resolve_provider(model)
        started = time.monotonic()
        if provider == PROVIDER_ANTHROPIC:
            result = self._generate_anthropic(normalized, system, prompt, max_tokens, temperature)
        else:
            result = self._generate_openapi(normalized, system, prompt, max_tokens, temperature)
        result.latency_seconds = round(time.monotonic() - started, 3)
        return result

    # ------------------------------------------------------------------
    # Anthropic Claude on Vertex (rawPredict via the Anthropic SDK)
    # ------------------------------------------------------------------

    def _generate_anthropic(
        self, model: str, system: str, prompt: str, max_tokens: int, temperature: float
    ) -> GenerationResult:
        from anthropic import AnthropicVertex

        client = AnthropicVertex(project_id=self.project, region=self.anthropic_location, timeout=self.timeout)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return GenerationResult(
            text=text,
            model=model,
            provider=PROVIDER_ANTHROPIC,
            latency_seconds=0.0,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
        )

    # ------------------------------------------------------------------
    # Gemini + Model Garden via the OpenAI-compatible endpoint
    # ------------------------------------------------------------------

    def _openapi_url(self) -> str:
        # The "global" location drops the regional host prefix.
        host = (
            "aiplatform.googleapis.com" if self.location == "global" else f"{self.location}-aiplatform.googleapis.com"
        )
        return f"https://{host}/v1/projects/{self.project}/locations/{self.location}/endpoints/openapi/chat/completions"

    def _access_token(self) -> str:
        try:
            import google.auth
            from google.auth.transport.requests import Request
        except ImportError as exc:  # google-auth ships transitively (google-cloud-storage); guard minimal envs
            raise RuntimeError(
                "google-auth is required for Vertex AI calls but is not installed. "
                'Install it with `uv pip install google-auth` (or `uv pip install -e ".[lib-<library>]" google-auth`).'
            ) from exc

        if self._credentials is None:
            self._credentials, _ = google.auth.default(scopes=[_CLOUD_PLATFORM_SCOPE])
        if not self._credentials.valid:
            self._credentials.refresh(Request())
        token = self._credentials.token
        if not token:
            raise RuntimeError("Could not obtain a GCP access token from Application Default Credentials")
        return str(token)

    def _generate_openapi(
        self, model: str, system: str, prompt: str, max_tokens: int, temperature: float
    ) -> GenerationResult:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }
        response = httpx.post(
            self._openapi_url(),
            json=payload,
            headers={"Authorization": f"Bearer {self._access_token()}", "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Vertex chat-completions call for '{model}' failed with HTTP {response.status_code}: "
                f"{response.text[:2000]}"
            )
        body = response.json()
        text = _extract_openapi_text(body)
        usage = body.get("usage") or {}
        return GenerationResult(
            text=text,
            model=model,
            provider=PROVIDER_OPENAPI,
            latency_seconds=0.0,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )


def _extract_openapi_text(body: dict) -> str:
    """Pull the assistant text out of an OpenAI-style chat-completions body.

    ``content`` is normally a string, but some Model Garden publishers return
    the content-parts list form — accept both.
    """
    choices = body.get("choices") or []
    if not choices:
        raise RuntimeError(f"Vertex chat-completions response contains no choices: {str(body)[:500]}")
    content = (choices[0].get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    raise RuntimeError(f"Unexpected content shape in Vertex chat-completions response: {type(content).__name__}")
