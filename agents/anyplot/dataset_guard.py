"""The checks every dataset passes before it is stored: the instruction pre-filter, then the dataset judge.

One place for both callers: the dataset route (`agents/main.py`, a paste) maps the
refusals to `403 data_refused` and `503 guard_unavailable`; the `run_data_code` tool
(`tools/session.py`, a table computed from the user's snippet, whose cells can be any
text) maps them to its error codes `data_refused` and `guard_unavailable`. Either way
the strikes, the token booking and the attribution lines are the same, written here.

* `instruction_like` (`opening.py`) reads every header and cell for text addressed to an
  AI; a hit is a refusal with a `data_judge` attribution line of verdict `prefilter`.
* The dataset judge reads the judged view (`opening.dataset_judge_inputs`) in parts of
  about 4,000 characters, `DATASET_JUDGE_CONCURRENCY` at a time. Every answered part
  books its cost-weighted tokens to the user and writes its own `data_judge` line; an
  `attack` verdict is one strike against the user, once per distinct canonical CSV; a
  verdict other than `in_scope` refuses (fail closed), a part with no verdict is
  `GuardUnavailable`. The batches stop at the first refusal or outage.

No ADK import.
"""

import asyncio

from .data.parse import ParsedDataset
from .models import JudgeVerdict
from .opening import dataset_judge_inputs, instruction_like
from .plugins.ledger import RequestLedger, attribution, judge_budget_tokens
from .policy import data_rubric, fence
from .services import Services
from .settings import get_settings


DATASET_JUDGE_CONCURRENCY = 4
"""Parts of one dataset judged at the same time; most datasets are one part, the widest about 30."""


class DataRefused(Exception):
    """The pre-filter or the dataset judge refused the dataset."""


class GuardUnavailable(Exception):
    """The dataset judge gave no verdict for a part: nothing is stored (fail closed)."""


async def check_dataset(services: Services, ledger: RequestLedger, parsed: ParsedDataset) -> str | None:
    """The pre-filter, then the dataset judge on every part; raises `DataRefused` or `GuardUnavailable`.

    Returns the language of the headers (`judge_dataset`), which the dataset route uses for the session
    language (#12171) and `run_data_code` ignores.
    """
    if instruction_like(parsed):
        attribution("data_judge", ledger, verdict="prefilter")
        raise DataRefused
    return await judge_dataset(services, ledger, dataset_judge_inputs(parsed), content=parsed.csv)


async def judge_dataset(services: Services, ledger: RequestLedger, parts: list[str], *, content: str) -> str | None:
    """Judge every part of the judged view, a few at a time (module docstring).

    Returns the judge's `lang` for the first part, which holds every column name
    (`dataset_judge_inputs`): the language of the headers, `en` when unclear.
    """
    rubric = data_rubric()
    judge_model = get_settings().judge_model
    header_lang: str | None = None
    for start in range(0, len(parts), DATASET_JUDGE_CONCURRENCY):
        batch = parts[start : start + DATASET_JUDGE_CONCURRENCY]
        answers = await asyncio.gather(
            *(services.judge.judge(fence("dataset", part), rubric) for part in batch), return_exceptions=True
        )
        if any(isinstance(answer, JudgeVerdict) and answer.verdict == "attack" for answer in answers):
            services.usage.add_strike(ledger.user_id, content)  # one strike per dataset, however many parts
        refused = unavailable = False
        for offset, answer in enumerate(answers):
            number = start + offset + 1
            if not isinstance(answer, JudgeVerdict):
                unavailable = True
                attribution("data_judge", ledger, verdict="guard_unavailable", part=number, parts=len(parts))
                continue
            weighted = judge_budget_tokens(answer.tokens, answer.input_tokens, answer.output_tokens, judge_model)
            # Into the request too, like the scope guard: inside a chat turn (`run_data_code`) the root's next
            # budget check must count these tokens (#12172 review).
            ledger.judge_tokens += answer.tokens
            ledger.book_judge(answer.input_tokens, answer.output_tokens, answer.tokens)
            ledger.budget_tokens += weighted
            services.usage.add_tokens(ledger.user_id, weighted)
            attribution(
                "data_judge",
                ledger,
                verdict=answer.verdict,
                part=number,
                parts=len(parts),
                judge_tokens=answer.tokens,
                judge_input=answer.input_tokens,
                judge_output=answer.output_tokens,
            )
            refused = refused or answer.verdict != "in_scope"  # fail closed, like the scope guard
            if number == 1:
                header_lang = answer.lang
        if unavailable:
            raise GuardUnavailable
        if refused:
            raise DataRefused
    return header_lang
