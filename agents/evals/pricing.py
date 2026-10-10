"""List prices of the agent network's models, and the cost of one model call at list price.

Prices are USD per million tokens at the `global` endpoint, as of 2026-10-10 (the
owner's brief and docs/concepts/agent-network.md): Claude Haiku 5.5 $0.10 input and
$0.50 output; Gemini 3.8 Flash $1.50 and $7.50; Gemini 3.5 Flash-Lite $0.30 and $2.50.
The `eu` and `us` multi-regions add 10 % (`LOCATION_SURCHARGE`), which gives the eu
prices the design names ($1.65 and $8.25 for Gemini 3.8 Flash, $0.33 and $2.75 for the
judge). The spend cap counts list price, never the 50 % Gemini promotion, so neither
does the harness.

A call is priced from the attribution line's token counts (`plugins/ledger.usage_breakdown`):

* input: `prompt` (which includes cached and cache-write tokens) plus `tool_use_prompt`;
  `cached` tokens at `CACHE_READ_FACTOR` (0.1) of the input price, Anthropic
  `cache_write` tokens at `CACHE_WRITE_FACTOR` (1.25), the rest at the input price;
* output: `candidates` plus `thoughts`, at the output price.

The cache factors are Anthropic's published multipliers; Gemini's implicit cache is
billed at the same 10 %. Not modelled: Claude Haiku 5.5's long-prompt tier ($0.50 input
and $2.50 output above 100,000 prompt tokens), which no call reaches while the request
budget is 80,000 tokens (`AGENT_REQUEST_TOKEN_BUDGET`); raise that budget and this
module must price the tier. Re-check every number here, including Vertex AI's partner
pricing for Claude, before a spend decision: prices change on a monthly cadence.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Price:
    """USD per million tokens at the global endpoint."""

    input: float
    output: float


PRICES: dict[str, Price] = {
    "claude-haiku-5-5": Price(input=0.10, output=0.50),
    "gemini-3.8-flash": Price(input=1.50, output=7.50),
    "gemini-3.5-flash-lite": Price(input=0.30, output=2.50),
}
LOCATION_SURCHARGE: dict[str, float] = {"global": 0.0, "eu": 0.10, "us": 0.10}
CACHE_READ_FACTOR = 0.10
CACHE_WRITE_FACTOR = 1.25
PER_TOKEN = 1e-6

TOKEN_KINDS: tuple[str, ...] = (
    "prompt",
    "candidates",
    "thoughts",
    "cached",
    "cache_write",
    "tool_use_prompt",
    "judge_input",
    "judge_output",
)
"""The token counts a run record keeps; the two `judge_` kinds are the dataset and scope judge's."""


class UnknownPrice(KeyError):
    """No list price is recorded for a model; add it to `PRICES`."""


def price_of(model: str) -> Price:
    try:
        return PRICES[model]
    except KeyError:
        raise UnknownPrice(f"no list price for {model!r}; add it to agents/evals/pricing.py") from None


def surcharge(location: str) -> float:
    """The location's multiplier on the global list price."""
    return 1.0 + LOCATION_SURCHARGE.get(location, 0.0)


def call_cost(model: str, location: str, tokens: dict[str, Any]) -> float:
    """USD at list price of one model call, from its attribution line's token counts."""
    price = price_of(model)

    def count(name: str) -> int:
        value = tokens.get(name, 0)
        return value if isinstance(value, int) and value > 0 else 0

    cached, cache_write = count("cached"), count("cache_write")
    uncached = max(0, count("prompt") + count("tool_use_prompt") - cached - cache_write)
    input_cost = price.input * (uncached + cached * CACHE_READ_FACTOR + cache_write * CACHE_WRITE_FACTOR)
    output_cost = price.output * (count("candidates") + count("thoughts"))
    return (input_cost + output_cost) * PER_TOKEN * surcharge(location)


def judge_cost(model: str, location: str, input_tokens: int, output_tokens: int) -> float:
    """USD at list price of one judge call (no cache)."""
    price = price_of(model)
    return (price.input * max(0, input_tokens) + price.output * max(0, output_tokens)) * PER_TOKEN * surcharge(location)
