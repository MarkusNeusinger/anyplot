"""anyplot-agents: the private `/v1` API in front of the ADK runner.

The service is called only by the BFF (`api/routers/agent.py`, `/debug/agent/*` for admins, and
`api/routers/agent_public.py`, `/agent/*` for everyone) through Cloud Run IAM. It never exposes ADK's own server (`adk web`,
`get_fast_api_app`): the client cannot choose a user id or write state, events or
artifacts. Sessions, datasets, renders and versions live in memory for one instance
lifetime (`max-instances=1`), so a restart answers `404 session_expired`.

| Route | Body | Result | Errors |
|---|---|---|---|
| `GET /v1/status` | | `{libraries, model, location, version, provider, waiting, in_flight, user_max_runs, tier, paused, resets_at}` (`waiting` and `in_flight`: every lane of the run queue; `user_max_runs`: the caller's own cap, `AGENT_USER_MAX_RUNS` or, for an admin, `AGENT_ADMIN_USER_MAX_RUNS`; `tier`: `admin` or `public`, as the request was served; `paused`: the service's day budget is spent, so every turn gets `service_paused` until `resets_at`, the next 00:00 UTC) | |
| `GET /v1/budget` | | `{date, since, started_at, resets_at, paused, model, tokens, budget_tokens, usd, budget_usd, users, users_at_limit, limits}`: the admin's live view of the day from the usage book (`UsageBook.snapshot`), counts only, never a user id: the service's weighted tokens against `AGENT_GLOBAL_DAILY_TOKEN_BUDGET`, both in USD at the main model's list price (`ledger.weighted_usd`, null for a model without one), the users seen today, how many are at one or more of their own day caps, and how many at each (`limits`: `tokens`, `runs`, `data_runs`, `messages`, `pastes`, `conversions`, `locked_out`; an admin counts only at `pastes`, `conversions` and `locked_out`, the caps that bind every tier). In memory: `since` is when today's counts began, the instance's start or 00:00 UTC | |
| `GET /v1/eligibility?spec=&library=` | | `{eligible, status, reasons}` | |
| `POST /v1/sessions` | `{user, spec_id, library, locale, snapshot, source?}` (`source`: `fanout` for a session the admin's "plot in all libraries" opens; its telemetry lines carry that source) | `{session_id, eligibility, roles}` (`roles`: the spec's data roles as the dataset route names them, at most `MAX_DONE_ROLES`, so the page can say which columns the plot expects before any data) | `422 not_eligible`, `429 session_limit` (an anonymous caller's network already holds `AGENT_IP_MAX_SESSIONS` live sessions) |
| `POST /v1/sessions/{sid}/library` | `{library, snapshot, source?}` (`source`: `menu`, the default, or `chat`, for the telemetry) | `{session_id, eligibility, target, carry}`: `target` the new `{spec_id, library}`; `carry` `{decisions, newer, target_has_plot, from_plot, offer}` (`switch.SwitchSummary`), with `offer` true when the page should offer the carry run (`carry_plot`): the data, bindings, confirmation, language, kept note, versions and plot memory stay, and the switch's carry (`switch.Carry`) waits for the first run in the new target | `422 not_eligible`, `422 invalid` (another spec), `409 run_active` |
| `GET /v1/sessions/{sid}/memory` | | `{entries, max_entries, written}`: the plot memory, oldest first, each `{id, kind, target, text, expect, turn}` (`memory.py`); `written` once it ever held an entry, from then on its entries alone travel | |
| `DELETE /v1/sessions/{sid}/memory` | | the GET's shape with no entries: forget all, a blank start | `409 run_active` |
| `DELETE /v1/sessions/{sid}/memory/{entry_id}` | | the GET's shape after the removal | `404 not_found`, `409 run_active` |
| `POST /v1/sessions/{sid}/dataset` | `{text, confirmed?, source?, table?}` (`source`: the name of the file the page read the text from, at most 1,024 characters; screened on its own, never a note; `table`: 1 to 10, which of several tables in the text to read, from the previous answer's `tables`) | `{preview, profile, bindings, warnings, context_lines, roles, suggestion, version, can_undo, original_version, columns_changed, language, file_name?, tables?, table?}` (`columns_changed`: the data replaces data, and a column a binding of the replaced data used is not in it, so the page shows the remembered decisions on the new data's line; `file_name`: the dropped file's name as the session keeps it, `(name withheld)` when the screen refused it; `tables`: one label per table, its header names and its row count, when the text held two or more tables each under its own header after a blank line, and `table` the one read, see `data/parse.py` `_one_table`;`suggestion`: the wide-table offer of `data/shape.py` with `siblings`, the columns a role that takes labels should not take (`bindings.label_siblings`), or null; `context_lines`: the notes pasted above or below the table that passed the pre-filter and the scope judge, which the root gets with the next `summarize_data` turn; `language`: the session language as `{language, source}`, with `offer: {language, basis: "data"}` when the notes or the column names are in another language the page has not been offered yet and the user picked none, which the page offers once, `language.data_offer`), stored as the first version of new data under the session's next number (`version`, also `original_version`; `can_undo` false: the undo history of an earlier paste is dropped); or, for free text, `{transcribed, text, preview, profile, warnings, note}`, not stored (`confirmed: true` skips that fallback and keeps every row) | `413 too_long`, `422 unparseable` (both with `cause`, the parser's sentence naming what the data fails on, at most 300 characters), `422 formula` (text of at most 2,000 characters that asks for a formula, which the chat's `generate_data` computes; never transcribed), `422 code` (a program that generates data, which the chat's `run_data_code` runs), `422 data_request` (text of at most 2,000 characters that asks for data instead of holding it, such as "Beispieldaten": found by `data/classify.py` before any model, or by the transcriber's `asks_for_data`; the page sends it to the chat, where the root generates example data), `403 data_refused`, `403 session_closed` (the scope judge closed the session), `409 run_active` (a turn, a theme toggle or another paste in flight in this session), `429 rate_limited` / `429 daily_limit` (`AGENT_USER_PASTES_PER_MINUTE` / `_PER_DAY`, or the user's daily token budget for `daily_limit`), `429 service_paused` (the service's day budget), `429 locked_out` (the day's `attack` strikes), `503 guard_unavailable` |
| `POST /v1/sessions/{sid}/dataset/convert` | `{data_base64, sheet?}` (a dropped Excel, OpenDocument, Parquet, Feather, Arrow or NumPy file, at most 5 MiB; `sheet` a sheet or `.npz` array the previous answer named) | `{text, format, kind, rows, columns, sheet, sheets, sheet_count, warnings, dropped}`: the file read in the renderer's sandbox (`harness.py --convert`) into the text the paste box takes (CSV, or JSON records for a table with list columns, `format`), every value with the precision it came with, the sheet read and at most 10 visible ones with cells (`sheet_count` all of them), `warnings` counts (`formulas_without_value`, `hidden_sheets`, `dropped_columns`, `list_columns`, `utc_timestamps`, `renamed_columns`), `dropped` the names of the columns left out; nothing stored, no model call | `413 too_long`, `422 invalid`, `422 file_<refusal>` (`wire.CONVERT_REASONS`, with `measured` and `limit` for a broken cap) and `file_timeout`, `file_too_complex` (also a reader that died without its `status.json`), `file_too_large`, `file_unreadable`, `403 session_closed`, `409 run_active` (another conversion in flight in this session), `429 rate_limited` / `429 daily_limit` (`AGENT_USER_CONVERSIONS_PER_MINUTE` / `_PER_DAY`, or the user's daily token budget), `429 service_paused`, `429 locked_out`, `503 capacity` (no render slot within `AGENT_CONVERT_SLOT_WAIT_S`), `503 convert_unavailable` (no renderer, one without `/convert`, or a sandbox without the harness's required exec filter) |
| `PUT /v1/sessions/{sid}/bindings` | `[{role, column}]` | `{bindings, complete, missing_roles, warnings}`: `warnings` names a role that needs values of 0 or more bound to a column with a negative value, or left open for that reason (`data/signs.py`); never a refusal | `409 run_active`, `422 invalid` (with `errors`, at most 20 lines) |
| `PUT /v1/sessions/{sid}/language` | `{language, via?}` (a short name or code, `^[A-Za-z][A-Za-z -]{0,39}$`; `via`: `header`, the chip and the default, or `offer`, the button on an offer line) | `{language, source, suggestion?}`: the session language in its stored form (`English` is `en`), and the plot's; source `chosen` from the chip, which ends every offer, `offer` from an offer while the user picked none, with the content-free `language_offer` telemetry line (`via`, the language as a closed code); `suggestion`, when the session has data, the `.to_long()` offer (or null) with its new column names in that language | `409 run_active`, `422` (the pattern, or another `via`) |
| `POST /v1/sessions/{sid}/dataset/confirm` | | `{confirmed, rows, columns}`: step 1 of two, the user confirmed the dataset with its bindings; the pipeline runs only then | `409 run_active`, `422 no_dataset` |
| `POST /v1/sessions/{sid}/dataset/undo` | | `{preview, profile, bindings, warnings, context_lines, roles, suggestion, version, can_undo, original_version}`: the dataset version before the root's last `prepare_data` or `generate_data` is the current one again, under its own number (`version`: the session numbers every stored version once, so paste, change, undo, change is 1, 2, 1, 3), its bindings carried over (`dataset_versions.py`); `can_undo` whether another undo has a version to restore, `original_version` the number of the current data's first version; unconfirmed, like any version the user has not confirmed | `409 run_active`, `422 nothing_to_undo` |
| `POST /v1/sessions/{sid}/dataset/to_long` | | The undo route's shape plus `changes`: the page's `.to_long()` applies the wide-table suggestion, recomputed on the server, as the next dataset version with the new columns bound to the roles they were made for; no model call | `409 run_active`, `422 no_suggestion` |
| `POST /v1/sessions/{sid}/dataset/copy` | `{from_session}` | The paste route's dataset shape (the target's first version, numbered 1) plus `confirmed: true`, `complete`, `missing_roles`, `copied_from` (the source's version number) and `carry` (the switch answer's shape: the plot memory and a carry of the source's latest plot come along, so the fan-out sends `carry_plot` on `offer`): the admin fan-out's copy of the confirmed current data version of `from_session`, a session of the same user and spec, into this fan-out session, byte for byte, with its bindings, their confirmation and the session language; nothing parsed or judged, no model call, no paste counted | `404 session_expired` (either session, also another user's), `409 run_active` (either session), `409 has_dataset` (the target has data), `422 no_dataset`, `422 unconfirmed`, `422 invalid` (the same session, a target that is no fan-out session, another spec, refused bindings), `429 rate_limited` / `429 daily_limit` (`COPIES_PER_MINUTE` / `_PER_DAY`; never for an admin), `503 capacity` |
| `GET /v1/sessions/{sid}/dataset/data.csv` | | the current dataset version's canonical CSV as stored (at most 4 MiB, `parse.MAX_CANONICAL_BYTES`), for the data panel's full view; no model call, no state write | `422 no_dataset` |
| `POST /v1/sessions/{sid}/messages?theme=` | `{text}` or `{action}` (`create_plot`, the fresh plot; `carry_plot`, the plot with the switch's carry and the plot memory; `plot_new_data`, "plot the new data": from the library's latest version while it drew the same paste with the same bindings, else the fresh plot; `summarize_data`; `example_data`, the page's `.example_data()`, which leaves the session language as it is); `theme` (`light`, `dark`, optional) is the site theme the page shows, which a plot run of the turn renders unless the user asked for a theme (`pipeline.run_theme`) | SSE `anyplot/1`, every event with the id `<run_id>.<n>` (`agents/turn_log.py`) and a `: ping` comment after every 15 s without one; the `done` event carries `dataset` (with `roles` and `changes`) after a turn whose `prepare_data` or `generate_data` changed the data, or whose summary of a paste made its `certain` conversions (`paste_conversions.py`), in the dataset shape with `version`, `can_undo` (false when `generate_data` made the session's first data) and `original_version`, and `language` (`{language, source}`, with `offer: {language, basis: "message"}` when the scope judge named another language for the typed message that the page has not been offered yet and the user picked none) after every run, and `suggestion` (the `.to_long()` offer in the session language, or null) after every run on a session with data, and `switch` (`{library, plot}`) after a turn whose root asked for a library switch the user wanted in the chat (`switch_plot`), which the page carries out | `413 too_long`, `409 run_active`, `422` for a `theme` other than `light` or `dark` |
| `POST /v1/sessions/{sid}/cancel` | | `204` | |
| `GET /v1/sessions/{sid}/turn` | header `Last-Event-ID: <run_id>.<n>` | SSE `anyplot/1`: the session's latest turn from its event `n + 1` on, as the turn's stream sent it, live until that stream ends; for a page that lost the stream (`agents/turn_log.py`); a read, which never holds or stops the run | `404 not_found` (another turn is the latest, or none), `422` (an id of another form) |
| `POST /v1/sessions/{sid}/outcome` | `{action, version?, reaction?}` (closed sets: `telemetry.OutcomeAction`, `telemetry.Reaction`, the latter with `feedback` only) | `204`: the content-free `outcome` telemetry line (`anyplot/telemetry.py`) | `422`, `429 rate_limited` / `429 daily_limit` (`OUTCOMES_PER_MINUTE` / `_PER_DAY`) |
| `POST /v1/sessions/{sid}/versions/{version}/render` | `{theme}` | `{status, reason?, artifacts}` | `404 not_found`, `409 run_active`, `503 capacity` (no render slot in time, or the render store is full) |
| `GET /v1/sessions/{sid}/artifacts/{name}?v=&theme=` | | the file; `plot.html` (a JavaScript version only) is the self-contained interactive page in `theme` (default: the version's), built on demand and answered as an attachment | `404`; for `plot.html` also `409 run_active`, `503 capacity`, `503 page_unavailable` (a renderer without `POST /page`), `500 page_failed` |
| `GET /v1/sessions/{sid}/bundle?version=&include_data=` | | the feedback case bundle: every version, or the one numbered `version`, or with `version=0` the conversation alone (no version; `data_csv`, the current data, with `include_data`); `session.versions` (how many versions the session holds) and `session.last_run` (`schemas.LastRun`: how the latest plot run ended, content-free) in every form, and `turns` (`{records, dropped}`: the record of each of the session's latest turns, its root tool calls and guard verdicts as closed codes, `anyplot/turn_record.py`) in every form too; with `AGENT_KEEP_REFUSALS` also `refusals`, the session's refused messages `[{verdict, lang, text, at}]` | `404` |
| `DELETE /v1/sessions/{sid}` | | `204` | |

Every `/v1` route needs `X-Anyplot-User` (the BFF's opaque user id); sessions are
owned by that id, so another user's session id is `404 session_expired`. Outside
development the caller check decodes the IAM-forwarded ID token (Cloud Run has
already verified it and replaced the signature) and requires its `aud` in
`AGENT_SERVICE_URLS` and its `email` in `AGENT_ALLOWED_CALLERS`. It reads
`X-Serverless-Authorization` whenever that header is present, because Cloud Run then
checks only that one and passes `Authorization` through unverified.

`X-Anyplot-Tier: admin` puts the request in the admin tier (owner decision of 2026-11-01):
its sandbox runs go into the run queue's admin lane, which shares the instance's
concurrency and start rate with everyone's and allows five runs per admin
(`AGENT_ADMIN_USER_MAX_RUNS`), and it is exempt from the per-user day caps and the chat
turns' minute (`plugins/ledger.py`); the global day budget binds it like everyone. The BFF sets the
header from the identity its admin gate verified, and only an allowed caller gets past the
caller check, so nobody else can claim the tier. A missing or other value is the public
tier, never an error: a BFF deployed before the header keeps today's limits for everyone.
A header, not the `adm_` prefix of the user id: the id stays opaque, the tier stays one
explicit assertion in one place of the BFF (`agent_context`), and a later tier (`premium`)
needs no new id format.

The public BFF (`api/routers/agent_public.py`, launch package of 2026-11-02) sends
`X-Anyplot-Anon`, its page's random tab id, instead of `X-Anyplot-User`, plus
`X-Anyplot-Network`, the client's IPv4 address or IPv6 /64. Such a caller is always `public`.
`require_user` keys it on the tab id salted with this process's salt (`pub_` + 16 hex digits,
`ledger.anonymous_user`), and binds it for the day to the salted network
(`ledger.network_key`), which the per-IP caps count: `AGENT_IP_MAX_RUNS` in the run queue,
`AGENT_IP_DAILY_TOKEN_BUDGET` and `AGENT_IP_DAILY_PIPELINE_RUNS` in the usage book. Neither
header is stored or logged as sent, and the salt dies with the process, so nothing outlives
the instance that could map an id back to a tab or an address. `POST /v1/sessions` checks its
body's `user` against the id as sent (`named_user`).

A `/messages` turn starts at once: the stream sends `ready` and the run begins, so a
plain answer, a refusal, `prepare_data` or `generate_data` never waits (owner decision
of 2026-10-14). Only sandbox work goes through the run queue (`anyplot/run_queue.py`):
the turn's first `plot_pipeline` or `run_data_code` call takes the queue's slot and the
turn's start in the rate window (`TurnSlot`, the ledger's `run_slot`), and the stream
sends `status{step:"queued", position, waiting}` while it waits, mid-turn, then once
`status{step:"started"}` as the wait ends, then the run's own events. The request deadline is paused while the turn waits and resumes
with the time it had left when the slot comes, so queued time never counts. A full queue, or a
wait of `AGENT_QUEUE_MAX_WAIT_S`, ends the turn with `error{code:"capacity"}`.

Every exclusion is per session (owner decision of 2026-10-21): the page opens one session per
browser window, and a user's windows work in parallel. A session runs one thing at a time, so
a second turn while its turn runs is `409 run_active`, and a paste in flight blocks the
session's turns, its theme toggle and its data routes; the user's other sessions never block
it. What the sessions of one user share is the run queue: a user may have at most
`AGENT_USER_MAX_RUNS` sandbox runs (an admin `AGENT_ADMIN_USER_MAX_RUNS`) queued or running at
the same time, across sessions, and the
turn whose sandbox run would be one more ends with `error{code:"run_limit"}` (`TurnSlot`),
before the queue's length is looked at. The per-user rate limits and daily budgets stay per
user.

Before the scope judge runs, and before any model call, the route answers with a fixed
refusal right after `ready`: `locked_out` for a user past the day's `attack` strikes
(`AGENT_ATTACK_STRIKES`), `budget` for a user over the daily token budget,
`service_paused` for everyone else once the service's day budget is spent
(`AGENT_GLOBAL_DAILY_TOKEN_BUDGET`; a paste or a conversion `429 service_paused`),
`session_closed` in a session the scope judge closed (`AGENT_SESSION_REFUSALS`
refusals of type `attack`), and `rate_limited` or `daily_limit` past
the user's message limits (`AGENT_USER_MESSAGES_PER_MINUTE`,
`AGENT_USER_MESSAGES_PER_DAY`, counted in the usage book; actions count too). An admin is
exempt from the user's daily token budget and both message limits; the strikes, the global
budget and a closed session bind every tier.

The theme toggle (`/versions/{version}/render`) renders the other theme of a finished
version outside the queue, because it costs no tokens, but behind waiting pipeline
renders in the render slot (`render/serial.py`); while it renders it holds the
session's registry entry, so a session has one run or toggle in flight at a time (the
user's other sessions are not blocked).
`adk web` runs the agents without this service, so its runs bypass the queue; its
renders still go through the one render slot.

Before a dataset is stored, a deterministic pre-filter reads every header and cell
for text addressed to an AI, then the dataset judge reads the judged view (every
header, the five rows and top values the root and the adapter get, cells in full) in
parts of about 4,000 characters, four at a time (`opening.py`). Both look for
injection only: names, addresses, e-mail addresses, phone numbers and web addresses
are the user's data and pass. A pre-filter hit or any refusing part is
`403 data_refused` (the `data_judge` attribution line tells `prefilter` and the
judge's verdict apart); a part the judge cannot answer is `503 guard_unavailable`.
The notes pasted around the table (`context_lines`) go through the same pre-filter and
then the scope judge (`_screen_notes`); any refusal or outage there drops only the notes,
with a warning, never the table, and is never a strike. A dropped file's name (`source`) is
never a note and never part of the text: sanitised (`opening.source_name`), it goes through
the same pre-filter and then its own scope-judge call (`_screen_file_name`), and the session
keeps it as `StoredDataset.file_name` (`(name withheld)` after a refusal or an outage, no
strike, the notes untouched). The root reads it fenced as data, never as a request; its
judge's `lang` never sets the session language; it is never logged.

The dataset answer lists the spec's data roles as `roles`, each
`{name, kinds, required, variadic, description, non_negative}`, so a client can offer a column
choice for every role: a single role binds under its own name, a variadic family
`y` binds its members `y1`, `y2`, ... (`data/bindings.py`). `non_negative` marks a
role that needs values of 0 or more (`data/signs.py`): the defaults never give it a
column with a negative value, and the page warns when one is chosen by hand.

The PNG artifacts and the bundle's images carry the footer strip ("made with
any.plot()", "anyplot.ai/<spec-id>", `render/watermark.py`), so a 3200x1800 render
is served as 3200x1864. It is composed from the raw render on the first request and
cached in the render store; `AGENT_WATERMARK=false` serves the raw renders. The
gates, the reviewer and the exported `plot.py` never see the strip.

Run locally with `uv run uvicorn agents.main:app --port 8001`.
"""

import asyncio
import base64
import binascii
import contextlib
import importlib.metadata
import json
import logging
import os
import re
import secrets
import sys
import time
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Collection, Sequence
from dataclasses import asdict, dataclass, field, replace
from typing import Annotated, Any, Literal, TextIO, get_args

from fastapi import Body, Depends, FastAPI, Header, Path, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from google.adk import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator
from starlette.background import BackgroundTask

from agents.anyplot import agent as agent_module
from agents.anyplot import telemetry, turn_record
from agents.anyplot.code import treesitter
from agents.anyplot.data.bindings import check_bindings, label_siblings
from agents.anyplot.data.classify import classify_paste, request_for_chat
from agents.anyplot.data.layouts import MIN_PAIRS_WITH_DATA, MIN_ROWS
from agents.anyplot.data.parse import (
    CONSTANT_NOTE_SUFFIX,
    MAX_COMPUTED_BYTES,
    MAX_INPUT_BYTES,
    MAX_TABLES,
    ParsedDataset,
    ParseError,
    parse_dataset,
    with_warning,
    without_context,
)
from agents.anyplot.data.prepare import Operation, PrepareError, apply_operations, with_date_notes
from agents.anyplot.data.shape import long_suggestion
from agents.anyplot.data.store import StoreFull
from agents.anyplot.data.transcribe import (
    category_header_warning,
    looks_like_free_text,
    near_transcribe_cap,
    table_to_csv,
    transcribe_refusal,
)
from agents.anyplot.dataset_context import FILE_NAME_WITHHELD
from agents.anyplot.dataset_guard import DataRefused, GuardUnavailable, check_dataset
from agents.anyplot.dataset_versions import dataset_payload, original_number, push_version, undo_version
from agents.anyplot.dev_fixture import FixtureError, load_case
from agents.anyplot.language import (
    DEFAULT_LANGUAGE,
    LANGUAGE_PATTERN,
    MAX_LANGUAGE_CHARS,
    LanguageSource,
    data_offer,
    english_name,
    is_valid,
    normalise,
    refusal_lang,
    same_language,
)
from agents.anyplot.memory import (
    ENTRY_ID_PATTERN,
    MemoryRefused,
    kind_counts,
    memory_delta,
    memory_written,
    next_seq,
    public_entries,
    read_memory,
)
from agents.anyplot.memory import MAX_ENTRIES as MAX_MEMORY_ENTRIES
from agents.anyplot.memory import forget as forget_entry
from agents.anyplot.models import JudgeFailure, JudgeUnavailable, model_busy
from agents.anyplot.opening import (
    INSTRUCTION_LIKE,
    MAX_SOURCE_RAW_CHARS,
    NOTES_INSTRUCTION_WARNING,
    NOTES_REFUSED_WARNING,
    NOTES_UNCHECKED_WARNING,
    Eligibility,
    assess,
    file_name_judge_input,
    notes_instruction_like,
    notes_judge_input,
    opening_state,
    source_name,
    store_dataset,
)
from agents.anyplot.page_export import NoPage, page_download
from agents.anyplot.pipeline import hold_request
from agents.anyplot.plugins.ledger import (
    ATTRIBUTION_LOGGER,
    CURRENT_LEDGER,
    RequestLedger,
    Tier,
    anonymous_user,
    attribution,
    budget_allows,
    day_refusal,
    judge_budget_tokens,
    network_key,
    next_reset,
    session_hash,
    utc_stamp,
    weighted_usd,
)
from agents.anyplot.plugins.scope_guard import (
    LOCKED_OUT,
    SESSION_CLOSED,
    paste_table_line,
    scope_refusals,
    served_library_request,
)
from agents.anyplot.policy import fence, file_name_block, refusal, scope_rubric, transcribe_rubric, user_notes_block
from agents.anyplot.render.contract import ConvertJob, PageFailed, PageUnsupported, RendererUnavailable
from agents.anyplot.render.serial import RenderBusy
from agents.anyplot.render.store import RenderStoreFull
from agents.anyplot.render.watermark import add_footer
from agents.anyplot.run_queue import (
    HEARTBEAT_S,
    Lane,
    QueueFull,
    QueuePosition,
    QueueTimeout,
    QueueUserLimit,
    QueueWithdrawn,
    RunQueue,
    Ticket,
)
from agents.anyplot.schemas import (
    CODE_ARTIFACTS,
    MAX_COLUMNS,
    MAX_MESSAGE_CHARS,
    PAGE_ARTIFACT,
    Binding,
    DatasetProfile,
    Theme,
)
from agents.anyplot.services import CodeVersion, Services, get_services
from agents.anyplot.session_state import (
    BINDINGS,
    CONFIRMED,
    DATASET_COPIED_FROM,
    DATASET_HISTORY,
    DATASET_ID,
    DATASET_ORIGINAL,
    DATASET_TOP,
    DATASET_VERSION,
    LANGUAGE_OFFERED,
    PENDING_BASE,
    PENDING_BINDINGS,
    PENDING_CLEARED,
    PENDING_EXPECTED_TEXTS,
    PENDING_REMEMBER,
    PENDING_REQUEST,
    PLOT_LANGUAGE,
    SUMMARY_PENDING,
    TELEMETRY_SOURCE,
    USER_BOUND,
    CatalogueSnapshot,
    SessionView,
    apply_bindings,
    confirm_delta,
    confirmation_fingerprint,
    language_delta,
    offered_delta,
    plot_language,
    read_session,
)
from agents.anyplot.settings import AgentSettings, get_settings
from agents.anyplot.switch import CARRY, Target, carry_for, read_carry, source_plot
from agents.anyplot.switch import summary as switch_summary
from agents.anyplot.telemetry import SwitchSource
from agents.anyplot.theme_render import RenderGone, render_theme
from agents.renderer.wire import (
    CONVERT_DAMAGES,
    CONVERT_EXEC_DENY_EXIT,
    CONVERT_HARNESS_EXITS,
    MAX_CONVERT_BASE64_CHARS,
    MAX_CONVERT_INPUT_BYTES,
    MAX_SHEET_NAME_CHARS,
)
from agents.stream import MAX_DONE_ROLES, Translator, turn_outcome
from agents.turn_log import EVENT_ID_PATTERN, PING, TurnLog, logged, parse_event_id
from core.constants import MAX_AGENT_VERSION, SUPPORTED_LIBRARIES
from core.spec_roles import MAP_SPECS, DataRole


logger = logging.getLogger("anyplot.agents")

APP_NAME = agent_module.APP_NAME
USER_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
SESSION_PATTERN = r"^[A-Za-z0-9_-]{1,128}$"
SPEC_PATTERN = r"^[a-z0-9-]{1,100}$"
LOCALE_PATTERN = r"^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$"
Action = Literal["create_plot", "carry_plot", "plot_new_data", "summarize_data", "example_data"]
ACTION_MESSAGES: dict[str, str] = {
    "create_plot": "[action] Create the plot from my dataset and bindings.",
    "carry_plot": "[action] Create the plot from my dataset and bindings, with the decisions I made so far.",
    "plot_new_data": "[action] Create the plot from my changed dataset and bindings.",
    "summarize_data": "[action] Summarize the dataset for the user.",
    "example_data": "[action] Make example data to try this plot.",
}
"""The fixed user message of each structured action; the scope judge is skipped for them (`ledger.kind`).
`summarize_data` also carries the notes the user pasted with the data, when the stored dataset kept any
(`user_notes_block`): the dataset route ran the pre-filter and the scope judge on them at the paste.
`example_data` is the page's `.example_data()`: the root makes example data as for a typed request (root.md,
"Example data"). An action, not the words "example data": an action skips the judge, so it neither costs a judge
call nor makes an offer of a language (`language.py`), and it leaves the session language as it was.
`create_plot` (`.create_plot()`, `.start_over()`) starts from the catalogue code (`RequestLedger.fresh_start`): its
run takes no switch's carry but applies the plot memory, which only the user clears. `carry_plot` (2026-11-02) is
the page's "plot in <library> with your
decisions" after a switch: its run takes the carry and the memory (`switch.py`). `plot_new_data` (2026-11-08) is the
page's "plot the new data" after a data change or a paste: its run starts from the library's latest version while
that version drew the same paste with the same bindings, else as `create_plot` does (`RequestLedger.new_data`,
`pipeline.new_data_base`); the root calls the same bare `plot_pipeline` for all three."""
PLOT_ACTIONS: frozenset[str] = frozenset({"create_plot", "carry_plot", "plot_new_data"})
"""The actions of the page's plot buttons: the click confirmed the data and bindings as shown, so the turn plots them
as they are (`RequestLedger.plot_action`, the guard in `plugins/tool_safety.py`)."""
ACTION_LANGUAGE_LINE = "Reply in {name}, the session language."
"""Appended to an action message when the session language is a known one other than English (`english_name`)."""
ACTION_MESSAGE = ACTION_MESSAGES["create_plot"]
SWEEP_INTERVAL_S = 300
ARTIFACT_TYPES: dict[str, str] = {
    "plot-light.png": "image/png",
    "plot-dark.png": "image/png",
    "plot.py": "text/x-python; charset=utf-8",
    "plot.R": "text/plain; charset=utf-8",
    "plot.jl": "text/plain; charset=utf-8",
    "plot.js": "text/javascript; charset=utf-8",
    "plot.tsx": "text/plain; charset=utf-8",
    "plot.html": "text/html; charset=utf-8",
    "data.csv": "text/csv; charset=utf-8",
}
"""Every artifact name a version can have (`schemas.ArtifactName`) with its media type; a version serves its
exported code under its runtime's name only (`CodeVersion.code_artifact`), the other code names are `404`, and
`plot.html` only for a JavaScript version."""
PAGE_HEADERS: dict[str, str] = {
    "Content-Disposition": 'attachment; filename="plot.html"',
    "Content-Security-Policy": "sandbox",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "private, no-store",
    "Referrer-Policy": "no-referrer",
}
"""The headers of `plot.html`, which the BFF sets the same (`api/routers/agent.py`, pinned by a test): a download,
never a page of this origin. A browser that renders it anyway gives it an opaque origin without scripts; the file
opened from disk carries its own policy and frame (`render/page.py`)."""
_USER = re.compile(USER_PATTERN)
ANON_PATTERN = r"^[A-Za-z0-9_-]{22,64}$"
"""An anonymous caller's tab id (`X-Anyplot-Anon`): the public BFF's `ANON_ID_PATTERN`, copied, because neither
image ships the other's package."""
NETWORK_PATTERN = r"^[0-9a-f.:/]{1,64}$|^unknown$"
"""The client network the public BFF forwards (`X-Anyplot-Network`): an IPv4 address, an IPv6 /64 in its compressed
form, or `unknown` for a client address the BFF could not read (`api/routers/agent_public.py` `client_network`)."""
_ANON = re.compile(ANON_PATTERN)
_NETWORK = re.compile(NETWORK_PATTERN)
_NO_STORE = {"Cache-Control": "private, no-store"}
OPERATIONS = TypeAdapter(list[Operation])

CONTENT_LOGGERS = ("google_adk", "google.adk", "google_genai", "anthropic", "httpx")


def disable_content_capture() -> None:
    """No content in logs or spans.

    Debug logging of ADK and the model SDKs prints request and response content, ADK
    puts message content into its spans unless told otherwise (`telemetry/context.py`
    reads the variable on every span), and the OpenTelemetry GenAI instrumentation
    does the same when its capture variable is set.
    """
    for name in CONTENT_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    os.environ["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"] = "false"
    os.environ.pop("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", None)


disable_content_capture()


class _AttributionHandler(logging.StreamHandler[TextIO]):
    """The stdout handler of the attribution lines, a class of its own so `enable_attribution_log` finds it."""


def enable_attribution_log() -> None:
    """The content-free attribution lines (`plugins/ledger.attribution`) on stdout at INFO, where Cloud Run's
    log agent reads them (owner decision of 2026-10-16).

    Without a handler the logging module drops INFO, so not one `pipeline_*` line of live test round 7 reached
    Cloud Logging and no run could be explained. Only this logger: every other one keeps its level, and the
    model SDKs stay at WARNING (`disable_content_capture`). The lines carry ids, counts, verdicts and rule ids,
    never text, code or data. It still propagates, so a test's log capture sees it; the root has no handler of
    its own in the service. Idempotent: a second call adds no second handler.

    The usage telemetry's logger (`telemetry.TELEMETRY_LOGGER`) gets the same treatment with a handler of its
    own: its lines carry `log_type: "agent_telemetry"`, which the Cloud Logging sink selects
    (`docs/reference/agent-telemetry.md`), and never the user id the attribution lines carry.
    """
    for name in (ATTRIBUTION_LOGGER, telemetry.TELEMETRY_LOGGER):
        named = logging.getLogger(name)
        named.setLevel(logging.INFO)
        if not any(isinstance(handler, _AttributionHandler) for handler in named.handlers):
            handler = _AttributionHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            named.addHandler(handler)


enable_attribution_log()


MAX_CAUSE_CHARS = 300
"""The longest `cause` an error answer carries (`AgentsError`); the BFF applies the same cap."""


def clip_cause(cause: str) -> str:
    """The cause within `MAX_CAUSE_CHARS`, a longer one cut at a word boundary with `…` (never mid-word)."""
    if len(cause) <= MAX_CAUSE_CHARS:
        return cause
    head = cause[: MAX_CAUSE_CHARS - 1]
    space = head.rfind(" ")
    return (head[:space] if space >= MAX_CAUSE_CHARS // 2 else head).rstrip(" ,;:") + "…"


class AgentsError(Exception):
    """A `/v1` error answered as `{"detail": code}`, plus `"cause"` when the refusal names one; never an exception text.

    `cause` is a sentence the service wrote for the user about their own data, such as the
    parser's `ParseError.message` ("the header has 3 fields, but line 3 has 4"): owner rule
    of 2026-10-16, a paste that is refused says what it fails on. It never carries an
    exception's text, a stack or a model's words.
    """

    def __init__(self, status: int, code: str, cause: str | None = None) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.cause = cause


def _version() -> str:
    try:
        return importlib.metadata.version("anyplot")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


# --- Runtime -----------------------------------------------------------------------------


STALE_RUN_MARGIN_S = 30
"""Seconds past the request deadline (or the queue's maximum wait) after which an entry counts as abandoned."""


@dataclass
class ActiveRun:
    """A `/messages` request from its registration to the end of its stream, or a theme toggle while it renders.

    `started` is the registration time on the queue's clock, and the end of the turn's
    queue wait once a sandbox run waited for the slot (`RunDeadline.arm`). `ticket` is
    the turn's queue entry, set by its first sandbox run (`TurnSlot`); the ticket's own
    times decide the stale check when there is one, so a run that just left a long
    wait is not mistaken for an old run. A toggle has no ticket, and its abort signal
    is never read: it ends within the request deadline on its own (a bounded slot wait
    plus one render).
    """

    abort: asyncio.Event
    user: str = ""
    started: float = field(default_factory=time.monotonic)
    deadline_hit: bool = False
    ticket: Ticket | None = None

    def stale(self, now: float, deadline_s: float, max_wait_s: float) -> bool:
        """An entry past the queue's maximum wait, or a run past the hard deadline, plus a margin, was abandoned."""
        if self.ticket is not None and self.ticket.waiting:
            return now - self.ticket.enqueued_at > max_wait_s + STALE_RUN_MARGIN_S
        began = self.started
        if self.ticket is not None and self.ticket.started_at is not None:
            began = max(began, self.ticket.started_at)
        return now - began > deadline_s + STALE_RUN_MARGIN_S


@dataclass
class RunDeadline:
    """A turn's request deadline: armed when the turn starts, paused while it waits in the run queue, and resumed
    with the time it had left when it leaves the queue. Queued time never counts, and the time before the wait is
    never granted twice, so a turn's active time stays within `seconds` and the whole turn within `seconds` plus the
    queue's maximum wait, below the BFF's turn cap and both services' Cloud Run timeouts."""

    run: ActiveRun
    seconds: float
    handle: asyncio.TimerHandle | None = None
    elapsed: float = 0.0  # active time spent before the last pause
    armed_at: float | None = None

    def arm(self, now: float) -> None:
        self.cancel()
        self.run.started = now - self.elapsed
        self.armed_at = now
        self.handle = asyncio.get_running_loop().call_later(max(self.seconds - self.elapsed, 0.0), self._hit)

    def pause(self, now: float) -> None:
        if self.armed_at is not None:
            self.elapsed += now - self.armed_at
            self.armed_at = None
        self.cancel()

    def cancel(self) -> None:
        if self.handle is not None:
            self.handle.cancel()
            self.handle = None

    def _hit(self) -> None:
        self.run.deadline_hit = True
        self.run.abort.set()


StreamNote = (
    tuple[Literal["queued"], QueuePosition]
    | tuple[Literal["started"], None]
    | tuple[Literal["event"], Event]
    | tuple[Literal["end"], None]
)
"""What the stream's outbox carries: a queue position of a waiting sandbox run, that run's start once it waited,
an ADK event, or the run's end."""

QueueOutcome = Literal["started", "expired", "withdrawn"]
"""How a turn's wait in the run queue ended, the `queue` line's verdict besides `run_limit` and `full`, which the
turn's record closes (`turn_record.HOOK_VERDICTS`, pinned equal by a test)."""
TIER_LANES: dict[Tier, Lane] = {"admin": "admin", "public": "normal"}
"""The run queue's lane of each tier (`run_queue.py`): an admin's runs share the concurrency and the rate with
everyone's and have a per-user cap of their own."""


@dataclass
class TurnSlot:
    """A `/messages` turn's claim on the run queue: taken by its first sandbox run, held until the turn ends.

    `take` is the ledger's `run_slot`, awaited by `plot_pipeline` and `run_data_code`
    inside the ADK run. The first call submits the turn's queue entry (a start in the rate
    window and the run slot), pauses the deadline while the entry waits, puts every
    position into the stream's outbox as it changes (the stream sends it as
    `status{step:"queued"}`), and resumes the deadline with the time it had left when the entry starts; an
    entry that waited then puts its start into the outbox (`status{step:"started"}`).
    A later call in the same turn answers at once: one start per turn. The entry goes into
    the lane of the turn's tier (`TIER_LANES`), and its position at submit and its wait go into
    the ledger for the run's usage telemetry (`RequestLedger.queue_position`, `queue_wait_s`). A full queue,
    a public lane at `AGENT_PUBLIC_QUEUE_MAX_WAITING`, or
    an expired wait fails the turn with `capacity` and aborts the run, so the stream ends
    with `error{code:"capacity"}` and the root spends no further call; a user who already
    holds their lane's cap of entries (`AGENT_USER_MAX_RUNS`, `AGENT_ADMIN_USER_MAX_RUNS`) in
    other sessions, or an anonymous user whose network holds `AGENT_IP_MAX_RUNS`,
    fails it the same way with `run_limit` (`QueueUserLimit`); a cancelled
    wait ends the run like any cancel. The entry is released with the turn (`Runtime.finish`).
    """

    runtime: "Runtime"
    run: ActiveRun
    session_id: str
    ledger: RequestLedger
    deadline: RunDeadline
    outbox: "asyncio.Queue[StreamNote]"

    async def take(self) -> bool:
        if self.run.ticket is not None:
            return self.run.ticket.running
        if self.run.abort.is_set():
            return False
        # A run of the user whose stream vanished mid-turn would still count toward their cap. The request's
        # start already swept (`_active`); this catches a run that went stale during this turn's root call.
        self.runtime.drop_stale(get_settings())
        queue = self.runtime.run_queue()
        lane = TIER_LANES[self.ledger.tier]
        # An anonymous user's network (`require_user`) counts toward `AGENT_IP_MAX_RUNS`; None for everyone else.
        network = get_services().usage.network_of(self.run.user)
        try:
            ticket = queue.submit(self.run.user, self.session_id, lane, network=network)
        except QueueUserLimit:  # the user's or their network's runs fill their share: not `capacity`
            attribution("queue", self.ledger, verdict="run_limit", waited_s=0.0, lane=lane)
            self._fail("run_limit")
            return False
        except QueueFull:
            logger.info("run queue full (ref %s): %d waiting", self.ledger.request_id, queue.waiting_count)
            attribution("queue", self.ledger, verdict="full", waited_s=0.0, lane=lane)
            self._fail("capacity")
            return False
        self.run.ticket = ticket
        outcome: QueueOutcome = "started"
        waited = False
        try:
            async with contextlib.aclosing(queue.wait(ticket, heartbeat_s=HEARTBEAT_S)) as positions:
                async for position in positions:
                    if not waited:
                        waited = True
                        self.deadline.pause(self.runtime.now())  # queued time never counts
                    self.outbox.put_nowait(("queued", position))
        except QueueTimeout:  # waited the maximum: the same answer as a full queue
            outcome = "expired"
        except QueueWithdrawn:  # cancelled or purged while it waited: nothing to report
            outcome = "withdrawn"
        waited_s = round(self.runtime.now() - ticket.enqueued_at, 1)
        attribution("queue", self.ledger, verdict=outcome, waited_s=waited_s, lane=lane)
        if ticket.waited_s is not None:  # it started: what the run's telemetry line reports, never who waited
            self.ledger.queue_position, self.ledger.queue_wait_s = ticket.submitted_position, ticket.waited_s
        if outcome == "expired":
            self._fail("capacity")
        if outcome != "started":
            return False
        if waited:
            self.deadline.arm(self.runtime.now())
            # The wait is over: a turn without pipeline steps has no other event that says so before its reply.
            self.outbox.put_nowait(("started", None))
        return True

    def _fail(self, code: Literal["capacity", "run_limit"]) -> None:
        self.ledger.fail(code)
        self.run.abort.set()


@dataclass
class Runtime:
    """The runner, the run queue and the run registry for this process.

    `active` is the run registry: one entry per session with a queued or running
    `/messages` turn or a theme toggle in flight, which is what `409 run_active`
    checks. `pasting` holds the sessions with a dataset paste in flight, so a session has
    one paste at a time (`409 run_active` for a second one). `active`, `pasting` and `converting`
    are keyed by session, never by user (owner decision of 2026-10-21): a user's other sessions never
    block a session, and only the run queue counts a user's runs across sessions
    (`AGENT_USER_MAX_RUNS`). A user may therefore hold several entries here at once, one per
    session; `drop_stale`, `finish` and the idle sweep work per entry and release each
    entry's own ticket. The queue is built from the settings on first use; its clock is the
    registry's clock too.
    """

    session_service: InMemorySessionService = field(default_factory=InMemorySessionService)
    artifact_service: InMemoryArtifactService = field(default_factory=InMemoryArtifactService)
    active: dict[str, ActiveRun] = field(default_factory=dict)
    pasting: set[str] = field(default_factory=set)
    """The sessions with a dataset paste in flight."""
    converting: set[str] = field(default_factory=set)
    """The sessions with a file conversion in flight: one per session at a time (`409 run_active` for a second)."""
    eligibility_cache: dict[tuple[str, str], Eligibility] = field(default_factory=dict)
    turns: dict[str, TurnLog] = field(default_factory=dict)
    """The latest turn's numbered events per session (`agents/turn_log.py`), which `GET .../turn` reads to the end
    for a page that lost the turn's stream; replaced by the session's next turn, dropped with the session."""
    runner: Runner | None = None
    queue: RunQueue | None = None
    clock: Callable[[], float] = time.monotonic

    def run_queue(self) -> RunQueue:
        if self.queue is None:
            self.queue = RunQueue.from_settings(get_settings(), clock=self.clock)
        return self.queue

    def now(self) -> float:
        return self.run_queue().now()

    def get_runner(self) -> Runner:
        if self.runner is None:
            self.runner = Runner(
                app=agent_module.app, session_service=self.session_service, artifact_service=self.artifact_service
            )
        return self.runner

    async def session(self, user: str, sid: str) -> Session:
        session = await self.session_service.get_session(app_name=APP_NAME, user_id=user, session_id=sid)
        if session is None:
            raise AgentsError(404, "session_expired")
        return session

    async def write_state(self, session: Session, delta: dict[str, Any]) -> None:
        # Authored "user" like ADK's own state-only events, so the agent router does not
        # look for an agent of that name; it has no content, so no model ever reads it.
        event = Event(invocation_id=f"route-{secrets.token_hex(6)}", author="user")
        event.actions = EventActions(state_delta=delta)
        await self.session_service.append_event(session=session, event=event)

    def start_turn(self, sid: str, run_id: str) -> TurnLog:
        """The log of the session's new turn, in place of its previous turn's."""
        log = TurnLog(run_id)
        self.turns[sid] = log
        return log

    async def purge(self, user: str, sid: str, services: Services) -> None:
        run = self.active.pop(sid, None)
        if run is not None:
            self.stop(run)
        log = self.turns.pop(sid, None)
        if log is not None:
            log.end()  # a reader still following the turn ends with the session, not at its own deadline
        await self.session_service.delete_session(app_name=APP_NAME, user_id=user, session_id=sid)
        services.purge_session(sid)
        telemetry.forget(sid)

    def stop(self, run: ActiveRun) -> None:
        """Abort a run and take it out of the queue if it still waits; a running one keeps its slot until it ends."""
        run.abort.set()
        if run.ticket is not None:
            self.run_queue().withdraw(run.ticket)

    def drop_stale(self, settings: AgentSettings) -> None:
        """Forget entries whose stream never ran its cleanup (a client gone before the first byte), and free their slot."""
        now = self.now()
        max_wait_s = self.run_queue().max_wait_s
        for sid, run in list(self.active.items()):
            if run.stale(now, settings.request_deadline_s, max_wait_s):
                run.abort.set()
                if run.ticket is not None:
                    self.run_queue().release(run.ticket)
                del self.active[sid]

    def finish(self, sid: str, run: ActiveRun) -> None:
        """The stream ended: free the run's queue slot, and forget `run` if it is still the session's entry."""
        if run.ticket is not None:
            self.run_queue().release(run.ticket)
        if self.active.get(sid) is run:
            del self.active[sid]

    async def sweep(self, idle_s: float, services: Services) -> int:
        """Drop sessions idle for longer than `idle_s`, with their stores."""
        self.drop_stale(get_settings())
        self.run_queue().pump()
        listing = await self.session_service.list_sessions(app_name=APP_NAME)
        now = time.time()
        removed = 0
        for session in listing.sessions:
            if session.id in self.active or now - session.last_update_time <= idle_s:
                continue
            await self.purge(session.user_id, session.id, services)
            removed += 1
        services.datasets.sweep(idle_s)
        services.renders.sweep(idle_s)
        return removed


RUNTIME = Runtime()


def get_runtime() -> Runtime:
    return RUNTIME


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # A missing tree-sitter grammar stops the start, never a request: the service does not download one.
    treesitter.check_grammars()

    async def sweeper() -> None:
        while True:
            await asyncio.sleep(SWEEP_INTERVAL_S)
            try:
                await get_runtime().sweep(get_settings().session_idle_s, get_services())
            except Exception as exc:
                logger.warning("session sweep failed: %s", type(exc).__name__)

    task = asyncio.create_task(sweeper())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="anyplot-agents", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.exception_handler(AgentsError)
async def _agents_error(_: Request, exc: AgentsError) -> JSONResponse:
    content: dict[str, Any] = {"detail": exc.code}
    if exc.cause:
        # Backstop: a cause that names the user's text must never turn a refusal into a 500 on encoding.
        content["cause"] = clip_cause(exc.cause).encode("utf-8", "replace").decode("utf-8")
    return JSONResponse(status_code=exc.status, content=content, headers=_NO_STORE)


# --- Caller and user ---------------------------------------------------------------------


def decode_claims(authorization: str | None) -> dict[str, Any] | None:
    """The claims of a bearer JWT, decoded without verifying the signature (Cloud Run IAM did)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    parts = authorization[7:].strip().split(".")
    if len(parts) != 3:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except ValueError, binascii.Error:
        return None
    return claims if isinstance(claims, dict) else None


def checked_token(request: Request) -> str | None:
    """The header Cloud Run IAM verified: `X-Serverless-Authorization` when present, else `Authorization`.

    With both headers present Cloud Run checks only `X-Serverless-Authorization`, so an
    invoker could otherwise add an unsigned `Authorization` that names an allowed email.
    """
    serverless = request.headers.get("x-serverless-authorization")
    return serverless if serverless is not None else request.headers.get("authorization")


def check_caller(request: Request) -> None:
    """Outside development: an IAM-forwarded ID token whose `aud` and `email` are allowed."""
    settings = get_settings()
    if settings.is_development:
        return
    claims = decode_claims(checked_token(request))
    if claims is None:
        raise AgentsError(401, "unauthenticated")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if not any(isinstance(item, str) and item in settings.service_urls for item in audiences):
        raise AgentsError(403, "forbidden")
    if claims.get("email") not in settings.allowed_callers:
        raise AgentsError(403, "forbidden")


def named_user(
    x_anyplot_user: Annotated[str | None, Header()] = None, x_anyplot_anon: Annotated[str | None, Header()] = None
) -> str:
    """The caller's id as the BFF sent it: `X-Anyplot-User` (the admin's keyed id, or a test's), or the anonymous
    tab id of `X-Anyplot-Anon` (the public BFF), never both. `POST /v1/sessions` checks its body's `user` against it."""
    if x_anyplot_anon is not None:
        if x_anyplot_user is not None or not _ANON.fullmatch(x_anyplot_anon):
            raise AgentsError(400, "user_required")
        return x_anyplot_anon
    if not x_anyplot_user or not _USER.fullmatch(x_anyplot_user):
        raise AgentsError(400, "user_required")
    return x_anyplot_user


def require_user(
    named: Annotated[str, Depends(named_user)],
    x_anyplot_anon: Annotated[str | None, Header()] = None,
    x_anyplot_network: Annotated[str | None, Header()] = None,
) -> str:
    """The user id every session, limit and attribution line is keyed on.

    `X-Anyplot-User` is taken as sent. An anonymous public caller (`X-Anyplot-Anon`, its page's random tab id) gets
    `ledger.anonymous_user`: the id salted with this process's salt, so nothing that outlives the process can map it
    back, and every anyplot-api instance reaches the same user. Its `X-Anyplot-Network` (the client's IPv4 address
    or IPv6 /64, which the public BFF always sends with the tab id) is required, salted at once (`network_key`) and
    bound to the user in the usage book for the day (`UsageBook.bind_network`), so the per-IP caps count it; neither
    header is ever stored or logged as sent.
    """
    if x_anyplot_anon is None:
        return named
    if x_anyplot_network is None or not _NETWORK.fullmatch(x_anyplot_network):
        raise AgentsError(400, "network_required")
    user = anonymous_user(named)
    get_services().usage.bind_network(user, network_key(x_anyplot_network))
    return user


def caller_tier(
    x_anyplot_tier: Annotated[str | None, Header()] = None, x_anyplot_anon: Annotated[str | None, Header()] = None
) -> Tier:
    """The caller's tier as the BFF asserts it: `admin` only for exactly `X-Anyplot-Tier: admin`, else `public`.

    Trusted because only an allowed caller reaches a `/v1` route (`check_caller`); the browser never talks to this
    service, and the BFF sets the header from the identity its admin gate verified, never from a request field.
    A missing or unknown value is `public`, never an error, so a BFF deployed before the header keeps every user
    in the public lane. An anonymous caller (`X-Anyplot-Anon`) is `public` whatever the tier header says.
    """
    return "admin" if x_anyplot_tier == "admin" and x_anyplot_anon is None else "public"


def request_id(x_request_id: Annotated[str | None, Header()] = None) -> str:
    if x_request_id and re.fullmatch(r"^[A-Za-z0-9-]{1,64}$", x_request_id):
        return x_request_id
    return secrets.token_hex(8)


User = Annotated[str, Depends(require_user)]
NamedUser = Annotated[str, Depends(named_user)]
CallerTier = Annotated[Tier, Depends(caller_tier)]
RequestId = Annotated[str, Depends(request_id)]
SessionId = Annotated[str, Path(pattern=SESSION_PATTERN)]
RuntimeDep = Annotated[Runtime, Depends(get_runtime)]
v1_dependencies = [Depends(check_caller)]


# --- Bodies ------------------------------------------------------------------------------


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateSessionBody(_Body):
    user: str = Field(pattern=USER_PATTERN)
    spec_id: str = Field(pattern=SPEC_PATTERN)
    library: str
    locale: str = Field(max_length=16, pattern=LOCALE_PATTERN)
    snapshot: CatalogueSnapshot
    source: Literal["fanout"] | None = None
    """`fanout`: the admin's "plot in all libraries" opened the session, and every usage-telemetry line of it carries
    that source instead of `live` (`session_state.TELEMETRY_SOURCE`). A closed set: any other value is `422`."""


class SwitchLibraryBody(_Body):
    library: str
    snapshot: CatalogueSnapshot
    source: SwitchSource = "menu"
    """Where the switch came from, for the `plot_switch` telemetry line only: the page's library menu, or the chat
    (the root's `switch_plot`, which the page carries out with this route)."""


class LanguageBody(_Body):
    """A pick of the session language: a short language name or code (`de`, `English`, `Swedish`), and where.

    `via` is `header` for the chat header's chip (the default) and `offer` for the button on the line that offered
    a language the judge named for a message or a paste.
    """

    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_CHARS, pattern=LANGUAGE_PATTERN)
    via: Literal["header", "offer"] = "header"


class DatasetBody(_Body):
    text: str = Field(min_length=1)
    confirmed: bool = False
    """The text is a table the user confirmed (the page's `.use()` on a transcription): the
    route never hands it to the transcriber again, so a one-column reading can be stored,
    and the parse keeps every row of it (no `table_block` narrowing: the user has seen the
    table row by row); the pre-filter, the judge and the store run as for any paste."""
    source: str | None = Field(default=None, min_length=1, max_length=MAX_SOURCE_RAW_CHARS)
    """The name of the file the page read `text` from (a drop, `.open()` or a pasted file), as the browser
    gave it. Screened on its own (`_screen_file_name`) and kept as `StoredDataset.file_name`, never as a
    note; the text itself is the file's, unchanged. Never logged."""
    table: int | None = Field(default=None, strict=True, ge=1, le=MAX_TABLES)
    """Which table to read when the text holds several (the page's table picker, from the previous answer's
    `tables`, 1-based); None reads the first. A number past the tables found is `422 unparseable`."""


class CopyDatasetBody(_Body):
    """The admin fan-out's copy: the session whose confirmed data the fan-out session in the path takes."""

    from_session: str = Field(pattern=SESSION_PATTERN)


class ConvertBody(_Body):
    """A dropped binary data file as base64 (the BFF's CSRF guard takes JSON only), and the sheet the page chose."""

    data_base64: str = Field(min_length=4, max_length=MAX_CONVERT_BASE64_CHARS)
    sheet: str | None = Field(default=None, min_length=1, max_length=MAX_SHEET_NAME_CHARS)
    """A sheet of a workbook or an array of an `.npz`, as the previous answer named it; None reads the first."""


class BindingBody(_Body):
    role: str = Field(min_length=1, max_length=32)
    column: str | None = Field(default=None, max_length=64)


class MessageBody(_Body):
    text: str | None = None
    action: Action | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "MessageBody":
        if (self.text is None) == (self.action is None):
            raise ValueError("send exactly one of text or action")
        return self


def _library(library: str, settings: AgentSettings) -> str:
    if library not in SUPPORTED_LIBRARIES:
        raise AgentsError(422, "invalid")
    return library


def _stamp(ledger: RequestLedger, view: SessionView | None, session: Session) -> RequestLedger:
    """The ledger with the session's spec, library, user turns so far and whether the fan-out opened it: the usage
    telemetry's envelope (`telemetry.py`), set once per request from session state, never per call site."""
    if view is not None:
        ledger.spec_id, ledger.library = view.spec_id, view.library
    ledger.turn = telemetry.user_turns(session.events)
    ledger.fanout = session.state.get(TELEMETRY_SOURCE) == "fanout"
    if ledger.tier == "admin":  # the usage book holds no tier: its live view reads it from here
        get_services().usage.mark_admin(ledger.user_id)
    return ledger


# --- Routes ------------------------------------------------------------------------------


@app.get("/v1/status", dependencies=v1_dependencies)
async def status(runtime: RuntimeDep, tier: CallerTier) -> dict[str, Any]:
    """The service's configuration, plus the run queue: `waiting` entries and runs `in_flight`, in every lane.

    `user_max_runs` is the caller's own cap in their tier's lane (`AGENT_USER_MAX_RUNS`, or
    `AGENT_ADMIN_USER_MAX_RUNS` for an admin), which the admin chat's fan-out over every library keeps to; `tier` is
    the tier the request was served as. `paused` says the service's day budget is spent, so every turn gets
    `service_paused` until `resets_at` (the next 00:00 UTC): the chat frame's tab shows it as its mood before the
    user types, read again after each run and every 60 s while the tab is visible.
    """
    settings = get_settings()
    queue = runtime.run_queue()
    queue.pump()
    return {
        "libraries": list(settings.libraries),
        "model": settings.model,
        "location": settings.location,
        "provider": settings.provider,
        "version": _version(),
        "waiting": queue.waiting_count,
        "in_flight": queue.in_flight,
        "user_max_runs": queue.user_cap(TIER_LANES[tier]),
        "tier": tier,
        "paused": get_services().usage.paused(settings),
        "resets_at": utc_stamp(next_reset()),
    }


@app.get("/v1/budget", dependencies=v1_dependencies)
async def day_budget() -> dict[str, Any]:
    """The admin's live view of the day (the BFF's `/debug/agent/budget`, behind its admin gate): the service's spend
    against `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` and how many users are at their own day caps. Counts only, never a user
    id. The counts live in this instance's memory: `since` is when they began today, and a redeploy or a
    scale-to-zero starts them again at zero (`ledger.UsageBook.snapshot`)."""
    settings = get_settings()
    usage = get_services().usage
    day = usage.snapshot(settings)
    budget_tokens = settings.global_daily_token_budget
    return {
        "date": day.date,
        "since": utc_stamp(day.since),
        "started_at": utc_stamp(day.started_at),
        "resets_at": utc_stamp(next_reset()),
        "paused": usage.paused(settings),
        "model": settings.model,
        "tokens": day.global_tokens,
        "budget_tokens": budget_tokens,
        "usd": _usd(weighted_usd(day.global_tokens, settings.model, settings.location)),
        "budget_usd": _usd(weighted_usd(budget_tokens, settings.model, settings.location)),
        "users": day.users,
        "users_at_limit": day.at_limit,
        "limits": day.limits,
    }


def _usd(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


@app.get("/v1/eligibility", dependencies=v1_dependencies)
async def eligibility(
    runtime: RuntimeDep,
    _: NamedUser,
    spec: Annotated[str, Query(pattern=SPEC_PATTERN)],
    library: Annotated[str, Query()],
) -> dict[str, Any]:
    """Without a snapshot the service knows the static rules and the pairs it has already scanned. The caller is
    checked as named (`NamedUser`), never bound to a network: the plot page asks on every visit, and nothing here is
    booked."""
    settings = get_settings()
    _library(library, settings)
    cached = runtime.eligibility_cache.get((spec, library))
    if cached is not None:
        return cached.public()
    reasons = []
    if spec in MAP_SPECS:
        reasons.append("map-spec")
    if library not in settings.libraries:
        reasons.append("library-disabled")
    if reasons:
        return {"eligible": False, "status": "blocked", "reasons": reasons}
    return {"eligible": True, "status": "unchecked", "reasons": []}


def _assess(runtime: Runtime, snapshot: CatalogueSnapshot, library: str) -> tuple[Eligibility, str]:
    eligibility_result, normalised = assess(snapshot, library, get_settings())
    runtime.eligibility_cache[(snapshot.spec_id, library)] = eligibility_result
    return eligibility_result, normalised


@app.post("/v1/sessions", dependencies=v1_dependencies)
async def create_session(body: CreateSessionBody, user: User, named: NamedUser, runtime: RuntimeDep) -> JSONResponse:
    settings = get_settings()
    # The body names the caller as the BFF sent it; an anonymous caller's session is owned by the salted id.
    if body.user != named or body.snapshot.spec_id != body.spec_id:
        raise AgentsError(422, "invalid")
    library = _library(body.library, settings)
    result, normalised = _assess(runtime, body.snapshot, library)
    if not result.eligible:
        raise AgentsError(422, "not_eligible")
    services = get_services()
    # An anonymous caller's network holds at most `AGENT_IP_MAX_SESSIONS` live sessions: tab ids cost nothing. The
    # place is taken here, with no `await` between the check and the binding, so parallel requests cannot all pass
    # the check; it is given back if the session is never created.
    network = services.usage.network_of(user)
    if network is not None and services.network_sessions(network) >= settings.ip_max_sessions:
        raise AgentsError(429, "session_limit")
    session_id = secrets.token_urlsafe(24)
    if network is not None:
        services.bind_session(session_id, network)
    try:
        state = opening_state(
            spec_id=body.spec_id,
            library=library,
            locale=body.locale,
            snapshot=body.snapshot,
            normalised=normalised,
            eligibility=result,
        )
        state.update(_fixture_seed(body.spec_id, library, session_id, body.snapshot, settings))
        if body.source is not None:
            state[TELEMETRY_SOURCE] = body.source
        await runtime.session_service.create_session(
            app_name=APP_NAME, user_id=user, state=state, session_id=session_id
        )
    except BaseException:
        services.session_networks.pop(session_id, None)
        raise
    # The roles, so the page's header names the columns the plot expects as the data card's dropdowns will.
    roles = _page_roles(body.snapshot.roles())[:MAX_DONE_ROLES]
    return JSONResponse({"session_id": session_id, "eligibility": result.public(), "roles": roles}, headers=_NO_STORE)


def _fixture_seed(
    spec_id: str, library: str, session_id: str, snapshot: CatalogueSnapshot, settings: AgentSettings
) -> dict[str, Any]:
    """Development only: the fixture case's dataset and bindings when it matches the opened pair."""
    if not settings.dev_fixture or not settings.is_development:
        return {}
    try:
        case = load_case(settings.dev_fixture)
    except FixtureError as exc:
        logger.warning("fixture seed skipped: %s", exc)
        return {}
    if (case.spec_id, case.library) != (spec_id, library):
        return {}
    ingested = store_dataset(get_services().datasets, session_id, parse_dataset(case.data_text), snapshot)
    delta = ingested.state_delta()
    if case.bindings is not None:
        delta[BINDINGS] = [binding.model_dump() for binding in case.bindings]
    # A fixture is the developer's own, confirmed data: its bindings (the case's or the defaults) count.
    bindings = case.bindings if case.bindings is not None else ingested.bindings
    delta[CONFIRMED] = confirmation_fingerprint(ingested.dataset_id, bindings)
    return delta


def _active(runtime: Runtime, sid: str, *, paste: bool = True) -> None:
    """409 while the session has a queued or running turn or a theme toggle in flight (`Runtime.active`), or, with
    `paste`, a dataset paste in flight (`Runtime.pasting`).

    Per session only (owner decision of 2026-10-21): a turn, a paste, a theme toggle and the data routes (library,
    bindings, confirm, undo, to_long) exclude each other within the session, and the user's other sessions (other
    browser windows) never block them; their sandbox runs meet only in the run queue (`TurnSlot`). The exclusion
    guards the session's own data: a paste holds the view it read before its judges ran and writes the next dataset
    from it, so a version stored meanwhile in the same session (a data route, a turn's `prepare_data`) would be
    dropped silently. Every guard is keyed by the session id, so it holds whoever sends the request, also two tabs
    that share one session id; the page opens a session per window and keeps its id in memory only, so its tabs
    never share one. Sessions never share data: the stores are keyed by session id, and no state is user-scoped; the
    one copy between sessions is the admin fan-out's (`/dataset/copy`), between two sessions of the same user only.
    The language chip passes `paste=False`: the paste reads the session again before it writes the language, so a
    choice that lands while the judges run is kept.
    """
    runtime.drop_stale(get_settings())
    if sid in runtime.active or (paste and sid in runtime.pasting):
        raise AgentsError(409, "run_active")


@app.post("/v1/sessions/{sid}/library", dependencies=v1_dependencies)
async def switch_library(
    sid: SessionId, body: SwitchLibraryBody, user: User, tier: CallerTier, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    """Switch the session's target, the (spec, library) pair, keeping the data, the bindings, their confirmation, the
    language, the kept first-plot note, the versions and the plot memory (owner decision of 2026-11-02).

    Another spec is `422 invalid` until the plot-type switch; the target is a pair already, so that switch only lifts
    the refusal. The switch writes the carry (`switch.carry_for`) that the first run in the new target takes, and
    answers what would carry: `carry` (`switch.SwitchSummary`) with `offer` true when the page should offer the carry
    run (`carry_plot`). Nothing runs here: from the menu the run waits for the user's click.
    """
    settings = get_settings()
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None or body.snapshot.spec_id != view.spec_id:
        raise AgentsError(422, "invalid")
    library = _library(body.library, settings)
    result, normalised = _assess(runtime, body.snapshot, library)
    if not result.eligible:
        raise AgentsError(422, "not_eligible")
    source = Target(spec_id=view.spec_id, library=view.library)
    target = Target(spec_id=body.snapshot.spec_id, library=library)
    memory = read_memory(session.state)
    if target.pair() == source.pair():
        carry = read_carry(session.state, target.pair())  # the same target again: a carry made for it stays
    else:
        # A plot of earlier data carries only its asked theme to the current data (`source_plot`).
        plot = source_plot(services.versions.latest_rendered(sid, target=source.pair()), view.dataset_version)
        pending = read_carry(session.state, source.pair())
        carry = carry_for(source=source, target=target, plot=plot, pending=pending, memory=memory)
    target_latest = services.versions.latest_rendered(sid, target=target.pair())
    carried = switch_summary(
        carry, memory, target_latest.turn if target_latest is not None else None, written=memory_written(session.state)
    )
    delta = opening_state(
        spec_id=view.spec_id,
        library=library,
        locale=view.locale,
        snapshot=body.snapshot,
        normalised=normalised,
        eligibility=result,
    )
    delta[CARRY] = carry.model_dump(mode="json") if carry is not None else None
    await runtime.write_state(session, delta)
    ledger = _stamp(
        RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action", tier=tier), view, session
    )
    ledger.library = library  # the envelope names the target; `from_library` the library before
    telemetry.write(
        telemetry.PlotSwitch,
        ledger,
        attempt=f"switch:{rid}",
        switch_source=body.source,
        from_library=view.library,
        spec_changed=target.spec_id != source.spec_id,
        library_changed=target.library != source.library,
        carried_count=carried.decisions,
        newer_count=carried.newer,
        target_has_plot=carried.target_has_plot,
        offered=carried.offer,
        memory_kinds=kind_counts(memory),
    )
    return JSONResponse(
        {"session_id": sid, "eligibility": result.public(), "target": target.model_dump(), "carry": carried.body()},
        headers=_NO_STORE,
    )


def _memory_answer(state: Any, entries: list[Any]) -> JSONResponse:
    """The memory routes' answer: the entries, the cap, and `written`, whether the session's memory ever held an
    entry (`memory.memory_written`): then its entries alone travel with a switch, also none, which the page's count
    follows."""
    body = {"entries": public_entries(entries), "max_entries": MAX_MEMORY_ENTRIES, "written": memory_written(state)}
    return JSONResponse(body, headers=_NO_STORE)


@app.get("/v1/sessions/{sid}/memory", dependencies=v1_dependencies)
async def get_memory(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """The plot memory as the page lists it ("Gemerkt"): `{entries, max_entries, written}`, oldest first, each
    `{id, kind, target, text, expect, turn}`. No model call, no state write."""
    session = await runtime.session(user, sid)
    return _memory_answer(session.state, read_memory(session.state))


@app.delete("/v1/sessions/{sid}/memory", dependencies=v1_dependencies)
async def forget_all_memory(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """Forget every entry of the plot memory (the page's forget-all, a blank start): the answer is the memory after
    it, as the GET answers it. Only the user clears the memory; no run ever does (owner decision of 2026-11-02). The
    id counter goes on, so `written` stays true and the raw requests never come back. `409 run_active` while a turn
    runs."""
    session = await runtime.session(user, sid)
    _active(runtime, sid, paste=False)
    await runtime.write_state(session, memory_delta([]))
    return _memory_answer(session.state, [])


@app.delete("/v1/sessions/{sid}/memory/{entry_id}", dependencies=v1_dependencies)
async def delete_memory_entry(
    sid: SessionId, entry_id: Annotated[str, Path(pattern=ENTRY_ID_PATTERN)], user: User, runtime: RuntimeDep
) -> JSONResponse:
    """Remove one entry of the plot memory (the page's remove button): the answer is the memory after it, as the GET
    answers it. The plot is not changed: the next run no longer hands the entry on. `404 not_found` for an id the
    memory does not hold, `409 run_active` while a turn runs, whose root may be writing the memory."""
    session = await runtime.session(user, sid)
    _active(runtime, sid, paste=False)
    try:
        entries = forget_entry(read_memory(session.state), entry_id)
    except MemoryRefused:
        raise AgentsError(404, "not_found") from None
    await runtime.write_state(session, memory_delta(entries))
    return _memory_answer(session.state, entries)


@app.post("/v1/sessions/{sid}/dataset", dependencies=v1_dependencies)
async def upload_dataset(
    sid: SessionId, body: DatasetBody, user: User, tier: CallerTier, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    services = get_services()
    settings = get_settings()
    session = await runtime.session(user, sid)
    # A closed session takes no paste either: each one spends judge calls, and the chat it would feed is closed.
    if scope_refusals(session.events) >= settings.session_refusals:
        raise AgentsError(403, SESSION_CLOSED)
    _active(runtime, sid)  # one paste per session at a time; the user's other sessions may paste meanwhile
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    ledger = _stamp(
        RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action", tier=tier), view, session
    )
    size = len(body.text.encode("utf-8", errors="surrogatepass"))
    facts = telemetry.InputFacts.for_paste(sid, size=size, source=body.source is not None, confirmed=body.confirmed)
    clock = telemetry.Clock()
    try:
        if size > MAX_INPUT_BYTES:
            raise AgentsError(413, "too_long")
        # The limits stay per user while the user's sessions paste in parallel (2026-10-21). The paste count is
        # checked here and booked in `_ingest_paste` (`add_paste`) before its first suspending `await`, so no paste
        # of another session slips in between and the counts never overshoot. The daily token budget is checked here,
        # before the judges, and booked after each judge call: pastes in several sessions at once can overshoot it
        # by the judge calls they have in flight, a few thousand tokens each.
        _paste_budget(services, user, settings, tier)
        limit = services.usage.paste_limit(user, settings)
        if limit is not None:
            attribution("paste_limit", ledger, verdict=limit)
            raise AgentsError(429, limit)
        telemetry.clear_converted(sid)  # past the limits: this paste is the converted file's one
        runtime.pasting.add(sid)  # no await since the check above, so no second paste slipped in between
        try:
            return await _ingest_paste(services, runtime, body, user, sid, ledger, view, facts)
        finally:
            runtime.pasting.discard(sid)
    except AgentsError as exc:
        facts.refused(exc.code)
        raise
    finally:
        facts.write(ledger, clock, settings.judge_model)


CONVERT_FAILURES: dict[str, str] = {
    "timeout": "file_timeout",
    "memory": "file_too_complex",
    "disk_budget": "file_too_complex",
    "file_budget": "file_too_complex",
    "output_rejected": "file_too_large",
}
"""A conversion the renderer stopped, by its run reason, as the route's refusal code; any other failure (the reader
raised, the guard refused an operation) is `file_unreadable`."""


@app.post("/v1/sessions/{sid}/dataset/convert", dependencies=v1_dependencies)
async def convert_dataset_file(
    sid: SessionId, body: ConvertBody, user: User, tier: CallerTier, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    """A dropped binary data file read in the renderer's sandbox into the text the paste box takes.

    Nothing is stored and no model reads anything: the page puts the text into the box and
    the user presses `.parse()`, which goes through the ordinary paste route (its limits, the
    pre-filter, the judges) with the file's name and sheet as `source`. The conversion has its
    own counter (`AGENT_USER_CONVERSIONS_PER_MINUTE` / `_PER_DAY`, counted when the file goes to
    the sandbox), checked after the paste route's daily budget and strikes, so a user who may
    not paste spends no sandbox time; the paste that follows counts as one paste (owner
    decision of 2026-10-15). One conversion per session at a time (`Runtime.converting`); the
    user's other sessions may convert meanwhile (owner decision of 2026-10-21), and each one waits
    for the render slot behind every pipeline render, at most `AGENT_CONVERT_SLOT_WAIT_S`, so
    parallel conversions queue in the slot and the per-user counter still bounds them. The
    counter is checked and booked with no suspending `await` between, so parallel sessions never
    overshoot it. The attribution line
    carries the kind, the outcome, the byte count and the time, never the file, its text or its
    sheet names.
    """
    services = get_services()
    settings = get_settings()
    session = await runtime.session(user, sid)
    if scope_refusals(session.events) >= settings.session_refusals:
        raise AgentsError(403, SESSION_CLOSED)
    if sid in runtime.converting:
        raise AgentsError(409, "run_active")
    try:
        data = base64.b64decode(body.data_base64, validate=True)
    except ValueError, binascii.Error:
        raise AgentsError(422, "invalid") from None
    if not data:
        raise AgentsError(422, "invalid")
    ledger = _stamp(
        RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action", tier=tier),
        read_session(session.state),
        session,
    )
    clock = telemetry.Clock()
    try:
        return await _convert(services, settings, runtime, body, data, user, sid, ledger, clock)
    except AgentsError as exc:
        telemetry.file_refusal(sid, ledger, size=len(data), kind=None, code=exc.code, clock=clock)
        raise


async def _convert(
    services: Services,
    settings: AgentSettings,
    runtime: Runtime,
    body: ConvertBody,
    data: bytes,
    user: str,
    sid: str,
    ledger: RequestLedger,
    clock: telemetry.Clock,
) -> JSONResponse:
    """The conversion route past its decode: its limits, the sandbox run, the answer; the route writes the
    `data_input` line of a refusal raised here, this function the one of a file the converter refused."""
    if len(data) > MAX_CONVERT_INPUT_BYTES:
        raise AgentsError(413, "too_long")
    _paste_budget(services, user, settings, ledger.tier)
    limit = services.usage.convert_limit(user, settings)
    if limit is not None:
        attribution("convert_limit", ledger, verdict=limit)
        raise AgentsError(429, limit)
    runtime.converting.add(sid)  # no await since the check above, so no second conversion slipped in between
    try:
        services.usage.add_conversion(user)
        job = ConvertJob(
            job_id=f"c{secrets.token_hex(8)}", data=data, sheet=body.sheet, timeout_s=settings.convert_timeout_s
        )
        try:
            output = await services.backend.convert(job, wait_s=settings.convert_slot_wait_s)
        except RenderBusy:
            attribution("data_convert", ledger, outcome="capacity", bytes=len(data))
            raise AgentsError(503, "capacity") from None
        except RendererUnavailable, NotImplementedError:
            attribution("data_convert", ledger, outcome="unavailable", bytes=len(data))
            raise AgentsError(503, "convert_unavailable") from None
    finally:
        runtime.converting.discard(sid)
    if output.exit_code == CONVERT_EXEC_DENY_EXIT:
        # The sandbox could not install the harness's kernel filter against program starts, which every run requires:
        # the reader never ran on the file, and none will until the renderer can (`RENDERER_EXEC_DENY`).
        attribution("data_convert", ledger, outcome="unavailable", reason="exec_deny", bytes=len(data))
        raise AgentsError(503, "convert_unavailable")
    kind = output.meta.kind if output.meta is not None else None
    if output.exit_code == 0 and output.text is not None and output.meta is not None:
        meta = output.meta
        attribution(
            "data_convert",
            ledger,
            outcome="ok",
            kind=kind,
            format=meta.format,
            rows=meta.rows,
            columns=meta.columns,
            sheets=meta.sheet_count,
            bytes=len(data),
            wall_s=round(output.wall_s, 3),
        )
        # The paste that follows with the file's name is this kind of file: its `data_input` line says so.
        telemetry.converted(sid, kind=meta.kind, sheets=meta.sheet_count)
        return JSONResponse(
            {
                "text": output.text,
                "format": meta.format,
                "kind": meta.kind,
                "rows": meta.rows,
                "columns": meta.columns,
                "sheet": meta.sheet,
                "sheets": meta.sheets,
                "sheet_count": meta.sheet_count,
                "warnings": dict(meta.warnings),
                "dropped": list(meta.dropped),
            },
            headers=_NO_STORE,
        )
    if output.refusal is not None:
        code = f"file_{output.refusal}"
    elif output.timed_out:
        code = "file_timeout"
    elif output.reason is not None:
        code = CONVERT_FAILURES.get(output.reason, "file_unreadable")
    elif output.exit_code is None or output.exit_code not in CONVERT_HARNESS_EXITS:
        # A process that died without its `status.json` (a native reader's SIGABRT on an allocation it could not
        # make; security review of #12194): the file was too much for the sandbox, not unreadable.
        code = "file_too_complex"
    else:
        code = "file_unreadable"
    attribution(
        "data_convert",
        ledger,
        outcome=code,
        exit_code=output.exit_code,
        reason=output.reason,
        damage=output.damage,
        bytes=len(data),
        wall_s=round(output.wall_s, 3),
    )
    telemetry.file_refusal(sid, ledger, size=len(data), kind=kind, code=code, clock=clock)
    content: dict[str, Any] = {"detail": code}
    if output.refusal is not None:
        content.update(
            {key: value for key, value in (("measured", output.measured), ("limit", output.limit)) if value is not None}
        )
    if output.refusal == "corrupt" and output.damage in CONVERT_DAMAGES:
        content["damage"] = output.damage  # which part is broken, a closed name the page words (owner, 2026-10-16)
    return JSONResponse(status_code=422, content=content, headers=_NO_STORE)


def _paste_budget(services: Services, user: str, settings: AgentSettings, tier: Tier) -> None:
    """`429 locked_out` past the day's `attack` strikes, `429 daily_limit` past the user's daily token budget, and
    `429 service_paused` when only the service's is spent, always for an admin (`ledger.day_refusal`)."""
    if services.usage.daily_ok(user, settings, tier=tier):
        return
    code = day_refusal(services.usage, user, settings, tier=tier)
    raise AgentsError(429, "daily_limit" if code == "budget" else code)


async def _ingest_paste(
    services: Services,
    runtime: Runtime,
    body: DatasetBody,
    user: str,
    sid: str,
    ledger: RequestLedger,
    view: SessionView,
    facts: telemetry.InputFacts,
) -> JSONResponse:
    """The paste route past its limits: classify, parse or transcribe, judge, screen the notes, store.

    `facts` collects the paste's content-free facts for its `data_input` telemetry line, which the route writes.
    """
    if not body.confirmed:  # a confirmed transcription is the service's own CSV
        _refuse_for_chat(ledger, body.text)
    try:
        # A confirmed transcription is the service's own CSV, which the user has seen row by row: no row is left out.
        # A dropped `.jsonl` or `.ndjson` file is JSON Lines by its name, so a file of one record is one row.
        json_lines = body.source is not None and body.source.lower().rstrip().endswith((".jsonl", ".ndjson"))
        # A short list of pairs over data the session holds is as often a change request in words (`layouts.py`).
        min_pairs = MIN_PAIRS_WITH_DATA if view.dataset_id else MIN_ROWS
        parsed = parse_dataset(
            body.text, find_table=not body.confirmed, table=body.table or 1, json_lines=json_lines, min_pairs=min_pairs
        )
    except ParseError as exc:
        facts.cause = exc.code
        if exc.code == "too_long":
            raise AgentsError(413, "too_long", exc.message) from None
        # Text with no table in it (prose, a list on one line) is the transcriber's; a broken
        # table (ragged rows, bad quoting, an over-long cell, invalid JSON) stays the parser's refusal,
        # which names its cause (owner rule of 2026-10-16).
        refusal = transcribe_refusal(body.text)
        if exc.code == "no_table" and refusal is None:
            return await _transcribe(services, ledger, body.text, facts)
        cause = exc.message
        if exc.code == "no_table":
            cause = f"{cause}, and {refusal}"
        raise AgentsError(422, "unparseable", cause) from None
    facts.parsed(parsed)
    if not body.confirmed and looks_like_free_text(parsed):
        # One column of prose, `label value` lines or names: the transcriber's, or a refusal that says why
        # not. Never stored as it parsed: its first line would be a column name nobody wrote (review of #12202).
        refusal = transcribe_refusal(body.text)
        if refusal is None:
            return await _transcribe(services, ledger, body.text, facts)
        facts.cause = "free_text_one_column"
        attribution("data_transcribe", ledger, outcome="too_large")
        raise AgentsError(
            422,
            "unparseable",
            "no table found: the text is one column without separators between columns that holds neither numbers, "
            f"dates nor repeating categories, and {refusal}; paste the data with a separator between columns (CSV or TSV)",
        )
    if not body.confirmed and (header_warning := category_header_warning(parsed)) is not None:
        parsed = with_warning(parsed, header_warning)  # its first line may be a category: said, never silent
        facts.parsed(parsed)
    services.usage.add_paste(user)  # the first model call of this paste: only a paste that reaches one counts
    try:
        header_lang = await check_dataset(services, ledger, parsed)
    except DataRefused:
        raise AgentsError(403, "data_refused") from None
    except GuardUnavailable:
        raise AgentsError(503, "guard_unavailable") from None
    notes_lang = None
    if parsed.context_lines:
        parsed, notes_lang = await _screen_notes(services, ledger, parsed)
    # The name is screened apart from the notes and its `lang` is not read: neither can cost the other.
    file_name = await _screen_file_name(services, ledger, body.source) if body.source is not None else None
    try:
        ingested = store_dataset(
            services.datasets,
            sid,
            parsed,
            view.snapshot,
            previous_id=view.dataset_id,
            history=view.earlier_datasets,  # the undo history and the original kept past it
            notes_screened=True,  # `_screen_notes` above kept only the notes that passed
            file_name=file_name,
            # Data that replaces data keeps what its columns meant: the plot keeps its axes (`carry_by_name`).
            carried=view.bindings if view.dataset_id else (),
            number=view.next_version,  # the session's numbering goes on: no number of the old data names this one
        )
    except StoreFull:
        raise AgentsError(503, "capacity") from None
    roles = view.snapshot.roles()
    facts.stored(
        ingested.parsed,
        complete=check_bindings(ingested.bindings, roles, ingested.parsed.profile).complete,
        bound=len(ingested.bindings),
        reshape=long_suggestion(roles, ingested.parsed.profile) is not None,
        file_name=file_name is not None,
    )
    delta = ingested.state_delta()
    # The root has not read this paste yet: the first turn on it summarizes it, the summary action or the note the
    # user typed with it (`SUMMARY_PENDING`).
    delta[SUMMARY_PENDING] = ingested.dataset_id
    # Read again: the chip's choice may have landed while the judges ran, and no offer comes after a choice.
    # From this read to the append below nothing suspends: `InMemorySessionService.get_session` and
    # `append_event` (ADK 2.13) contain no `await` that yields, and the code between them is synchronous,
    # so on the one event loop no `PUT /language` can land in between; the read and the conditional
    # write are atomic. A persistent session service with I/O in either call would need a
    # compare-and-set instead. Keep any new `await` out of this block.
    session = await runtime.session(user, sid)
    current = read_session(session.state) or view
    # The data's language never sets the session's: the page offers it once, and a click sets it.
    offered = data_offer(current.language, current.language_source, current.language_offered, notes_lang, header_lang)
    if offered is not None:
        delta.update(offered_delta(current.language_offered, offered))
        attribution("data_language", ledger, lang=offered, basis="notes" if offered == notes_lang else "headers")
    await runtime.write_state(session, delta)
    language = _language_body(current, (offered, "data") if offered is not None else None)
    _telemetry_offer(ledger, language)
    return JSONResponse(
        {
            "preview": parsed.preview,
            "profile": parsed.profile.model_dump(mode="json"),
            "bindings": [binding.model_dump() for binding in ingested.bindings],
            "warnings": parsed.warnings,
            "context_lines": parsed.context_lines,
            "roles": _page_roles(view.snapshot.roles()),
            # In the session language: `.to_long()`'s new column names are generated text.
            "suggestion": _suggestion(view, parsed.profile, current.language),
            # A paste is the first version of its data: nothing before it to undo (`dataset_payload`).
            "version": ingested.number,
            "can_undo": False,
            "original_version": ingested.number,
            # A column the replaced data was plotted by is not in this data: the page shows the remembered decisions,
            # which every next plot still applies, on the new data's line with `.forget_all()` (owner decision of
            # 2026-11-08). Only the user clears them.
            "columns_changed": ingested.columns_changed,
            "language": language,
            **({"file_name": file_name} if file_name is not None else {}),
            **({"tables": parsed.tables, "table": parsed.table} if parsed.tables else {}),
        },
        headers=_NO_STORE,
    )


async def _screen_file_name(services: Services, ledger: RequestLedger, raw: str) -> str | None:
    """A dropped file's name as the session keeps it: sanitised, then screened like a note, on its own.

    None when nothing readable is left (`source_name`). The pre-filter (`INSTRUCTION_LIKE`) runs on
    the name alone, then the scope judge on one `source file: <name>` line (`file_name_judge_input`),
    always, also for a name that looks harmless (owner decision of 2026-10-15). A hit, a verdict
    other than `in_scope` or no verdict keeps `FILE_NAME_WITHHELD` instead: the notes and the table
    are untouched, and it is never a strike, as for the notes (a file's name is often someone
    else's). The judge's `lang` is ignored: a name such as `datos_2025.csv` must not set the session
    language of a German table. Kept names still reach the root only fenced as data with a preamble
    that says a name is never a request (`policy.file_name_block`), because the scope judge passes
    plot wishes, and a name that reads like one ("drop rows where…") was not written to the root.
    The judge's tokens are the user's; the `file_name_judge` attribution line carries the verdict
    and the length, never the name.
    """
    name = source_name(raw)
    if name is None:
        return None
    chars = len(name)
    if notes_instruction_like([name]):
        attribution("file_name_judge", ledger, verdict="prefilter", chars=chars)
        return FILE_NAME_WITHHELD
    try:
        answer = await services.judge.judge(file_name_judge_input(name), scope_rubric())
    except JudgeUnavailable:
        attribution("file_name_judge", ledger, verdict="guard_unavailable", chars=chars)
        return FILE_NAME_WITHHELD
    ledger.book_judge(answer.input_tokens, answer.output_tokens, answer.tokens)
    services.usage.add_tokens(
        ledger.user_id,
        judge_budget_tokens(answer.tokens, answer.input_tokens, answer.output_tokens, get_settings().judge_model),
    )
    attribution("file_name_judge", ledger, verdict=answer.verdict, judge_tokens=answer.tokens, chars=chars)
    return name if answer.verdict == "in_scope" else FILE_NAME_WITHHELD


async def _screen_notes(
    services: Services, ledger: RequestLedger, parsed: ParsedDataset
) -> tuple[ParsedDataset, str | None]:
    """The notes pasted around the table, kept only when the pre-filter and the scope judge pass them.

    Returns the dataset and, for kept notes, the judge's `lang` for them, which the page may be
    offered (`language.data_offer`); None when the notes were dropped.

    `parsed.context_lines` (a title, an export's metadata, a source line, "values in
    Fahrenheit, make it a line chart") reach the root as the user's words, so they are
    checked like a chat message: first the deterministic pre-filter (`INSTRUCTION_LIKE`),
    then the scope judge with the scope rubric on the lines inside `<user_notes>`; an
    `other_library` for notes that name only libraries served here goes on as `in_scope`,
    as in the chat (`scope_guard.served_library_request`). It runs
    after the dataset judge, so a refused table spends no call on its notes. A hit, a
    verdict other than `in_scope` or no verdict (`JudgeUnavailable`: fail closed) drops
    every note with a warning (`without_context`), and the table is stored all the same.
    No verdict on notes is a strike: a hidden injection in a copied web table is not the
    user's doing, and the notes never reach a model. The judge's tokens are booked to the
    user like the dataset judge's, and the `notes_judge` attribution line carries the
    verdict and the counts, never the text.
    """
    lines = parsed.context_lines
    counts = {"lines": len(lines), "chars": len("\n".join(lines))}  # as the cap and the judge input count them
    if notes_instruction_like(lines):
        attribution("notes_judge", ledger, verdict="prefilter", **counts)
        return without_context(parsed, NOTES_INSTRUCTION_WARNING), None
    try:
        answer = await services.judge.judge(notes_judge_input(lines), scope_rubric())
    except JudgeUnavailable:
        attribution("notes_judge", ledger, verdict="guard_unavailable", **counts)
        return without_context(parsed, NOTES_UNCHECKED_WARNING), None
    ledger.book_judge(answer.input_tokens, answer.output_tokens, answer.tokens)
    services.usage.add_tokens(
        ledger.user_id,
        judge_budget_tokens(answer.tokens, answer.input_tokens, answer.output_tokens, get_settings().judge_model),
    )
    attribution(
        "notes_judge",
        ledger,
        verdict=answer.verdict,
        judge_tokens=answer.tokens,
        judge_input=answer.input_tokens,
        judge_output=answer.output_tokens,
        **counts,
    )
    if answer.verdict == "other_library" and served_library_request("\n".join(lines), get_settings().libraries):
        # "please do this in d3" around a table asks for a library the user may switch to (`served_library_request`).
        attribution("notes_judge", ledger, verdict="served_library_in_scope", **counts)
        answer = answer.model_copy(update={"verdict": "in_scope"})
    if answer.verdict != "in_scope":
        return without_context(parsed, NOTES_REFUSED_WARNING), None
    return parsed, answer.lang


def _refuse_for_chat(ledger: RequestLedger, text: str) -> None:
    """`422 code`, `422 data_request` or `422 formula` for attached text (a paste the page routed as data, or a file)
    that is a program, asks for data or asks for a formula, before any parser or model reads it (`data/classify.py`).

    A snippet such as `np.linspace(0, 10, 100)` would parse as a one-row table, and the
    transcriber would compute a formula's rows, which is the one thing no model may do:
    code is the root's `run_data_code` and a formula its `generate_data`, asked for in
    the chat, where the server computes the table. A request for example data
    ("Beispieldaten") holds no table: the page sends it to the chat as the user's turn,
    where the root's `run_data_code` runs the code it writes for it. A formula or a data
    request is refused only within the chat's cap (`MAX_MESSAGE_CHARS`), because the
    page sends the refused text to the chat as a turn; a longer formula goes on to the
    transcriber, whose rubric computes nothing. Code is refused at any length, because it
    is never a table; the page asks to shorten what the chat cannot take. Writes a
    `data_transcribe` attribution line with the outcome `code`, `data_request` or
    `formula` (no text, no tokens); none of them counts as a paste.
    """
    kind = classify_paste(text)
    if kind is not None:
        attribution("data_transcribe", ledger, outcome=kind)
        raise AgentsError(422, kind)


def _transcribe_failure_cause(failure: JudgeFailure, text: str) -> str:
    """What a transcription that timed out or was cut off fails on, with the text's size and the way out."""
    lines = sum(1 for line in text.splitlines() if line.strip())
    size = f"{lines:,} {'line' if lines == 1 else 'lines'}, {len(text.strip()):,} characters"
    if failure == "timeout":
        what = "did not finish in the time it has"
    else:
        what = "would have to write a longer table than it may"
    return (
        f"no table found: the text has no separators between columns, and the model that reads free text as a table "
        f"{what} for this text ({size}); paste the data with a separator between columns (CSV or TSV), or a shorter part"
    )


async def _transcribe(
    services: Services, ledger: RequestLedger, text: str, facts: telemetry.InputFacts
) -> JSONResponse:
    """Read free text as a table with the transcriber and answer with it, storing nothing.

    The answer carries `transcribed: true` and the table's CSV in `text`; the user
    confirms the preview, and the confirmation posts that CSV through the ordinary path
    (parse, pre-filter, judge, store). The model reads the raw text, so the pre-filter runs
    on it first; its answer is bound to `TranscribedTable`, then parsed like any paste, so
    a reading that is no table (one column of prose) is `422 unparseable` here too. Text
    the transcriber says asks for data (`asks_for_data`: "monthly sales for 4 regions", a
    request in a language `classify._REQUEST` does not read) is `422 data_request`, which
    the page sends to the chat, when the chat takes it and the transcriber found no table
    in it or it holds no values of its own (`classify.request_for_chat`); whatever table
    came with that answer is not the text's and is dropped. A table read from text with
    values of its own stays a transcription for the user to check, the flag or not. The call books its tokens like a judge call and writes a
    `data_transcribe` attribution line.
    """
    user = ledger.user_id
    facts.format = "transcribed"  # free text the transcriber reads: the input's format, whatever it parsed as
    services.usage.add_paste(user)  # a paste counts against `paste_limit` when it reaches a model (or its pre-filter)
    if INSTRUCTION_LIKE.search(text):
        facts.cause = "prefilter"
        attribution("data_transcribe", ledger, outcome="prefilter")
        raise AgentsError(403, "data_refused")
    try:
        reading = await services.judge.transcribe(fence("user_text", text), transcribe_rubric())
    except JudgeUnavailable as exc:
        # A cut-off answer is the text's size, and so is running out of time on a text of at least half
        # the transcriber's limits; the user can change either. A short text that times out met a
        # stalled endpoint, and an error, a quota or an unparseable answer is an outage too.
        sized = exc.failure == "cut_off" or (exc.failure == "timeout" and near_transcribe_cap(text))
        facts.cause = exc.failure if exc.failure in ("cut_off", "timeout") else "other"
        if not sized:
            attribution("data_transcribe", ledger, outcome="guard_unavailable", failure=exc.failure)
            raise AgentsError(503, "guard_unavailable") from None
        attribution("data_transcribe", ledger, outcome=exc.failure)
        raise AgentsError(422, "unparseable", _transcribe_failure_cause(exc.failure, text)) from None
    ledger.book_judge(reading.input_tokens, reading.output_tokens, reading.tokens)
    services.usage.add_tokens(
        user,
        judge_budget_tokens(reading.tokens, reading.input_tokens, reading.output_tokens, get_settings().judge_model),
    )
    if reading.table.asks_for_data and request_for_chat(text, without_table=reading.table.columns == ["text"]):
        facts.cause = "transcribed_data_request"
        attribution("data_transcribe", ledger, outcome="data_request", judge_tokens=reading.tokens)
        raise AgentsError(422, "data_request")
    csv_text = table_to_csv(reading.table)
    try:
        parsed = parse_dataset(csv_text, find_table=False)
    except ParseError as exc:
        facts.cause = "transcribed_unparseable"
        attribution("data_transcribe", ledger, outcome="unparseable", judge_tokens=reading.tokens)
        raise AgentsError(
            422, "unparseable", f"the model read the text as a table, but that table was refused: {exc.message}"
        ) from None
    if looks_like_free_text(parsed) and parsed.profile.columns[0].name == "text":
        # The rubric's answer for text that holds no table: one column named `text`.
        facts.cause = "transcribed_no_table"
        attribution("data_transcribe", ledger, outcome="no_table", judge_tokens=reading.tokens)
        raise AgentsError(
            422,
            "unparseable",
            "no table found: the text has no separators between columns, and the model that reads free text found "
            "no rows and columns in it",
        )
    attribution(
        "data_transcribe",
        ledger,
        outcome="ok",
        rows=parsed.profile.rows,
        columns=len(parsed.profile.columns),
        judge_tokens=reading.tokens,
        judge_input=reading.input_tokens,
        judge_output=reading.output_tokens,
    )
    facts.transcribed(parsed)
    return JSONResponse(
        {
            "transcribed": True,
            "text": csv_text,
            "preview": parsed.preview,
            "profile": parsed.profile.model_dump(mode="json"),
            "warnings": parsed.warnings,
            "note": reading.table.note,
        },
        headers=_NO_STORE,
    )


MAX_ROLE_DESCRIPTION_CHARS = 200


def _role_body(role: DataRole) -> dict[str, Any]:
    """One spec data role for the binding controls; the description is the spec's own text, capped."""
    description = role.description
    if len(description) > MAX_ROLE_DESCRIPTION_CHARS:
        description = description[: MAX_ROLE_DESCRIPTION_CHARS - 1].rstrip() + "…"
    return {
        "name": role.name,
        "kinds": list(role.kinds),
        # A role the plot can compute is never missing: the page marks it optional (`data/computed.py`).
        "required": role.required and not role.computed,
        "variadic": role.variadic,
        "description": description,
        # The page warns at the dropdown when the bound column has a negative value (`data/signs.py`).
        "non_negative": role.non_negative,
        # Left open, the plot computes the role from the data: the dropdown's empty choice says so.
        "computed": role.computed,
    }


def _page_roles(roles: list[DataRole]) -> list[dict[str, Any]]:
    """The roles the page offers a dropdown for, every one: a role the plot can compute shows "computed by
    the plot" as its empty choice (`computed`, owner decision of 2026-10-15, "both allowed")."""
    return [_role_body(role) for role in roles]


def _binding_pairs(bindings: list[dict[str, Any]]) -> set[tuple[Any, Any]]:
    """Bindings as a set of (role, column) pairs, so their order never reads as a change."""
    return {(item.get("role"), item.get("column")) for item in bindings}


def _hand_bound(noted: object, before: Sequence[Binding], after: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """`USER_BOUND` after a `PUT /bindings` that changed something: of the bindings in force after it (`after`), the
    pairs noted since the root's last turn (`noted`) and the pairs this PUT set, which the session did not hold
    (`before`). A pair the user has since taken back is in neither, so it leaves the note."""
    held = _binding_pairs([binding.model_dump() for binding in before])
    known = _binding_pairs([item for item in noted if isinstance(item, dict)]) if isinstance(noted, list) else set()
    return [
        {"role": role, "column": column}
        for role, column in ((item.get("role"), item.get("column")) for item in after)
        if (role, column) in known or (role, column) not in held
    ]


async def _hand_bound_seen(runtime: Runtime, user: str, sid: str) -> None:
    """Drop the note of the bindings the user set by hand (`USER_BOUND`) after a turn that ended well: its root read
    them in the session block. Never raises: the turn's answer stands, and the note shows once more."""
    try:
        session = await runtime.session(user, sid)
        if session.state.get(USER_BOUND) is not None:
            await runtime.write_state(session, {USER_BOUND: None})
    except Exception as exc:
        logger.warning("hand-bound note not dropped: %s", type(exc).__name__)


@app.put("/v1/sessions/{sid}/bindings", dependencies=v1_dependencies)
async def put_bindings(
    sid: SessionId,
    user: User,
    runtime: RuntimeDep,
    bindings: Annotated[list[BindingBody], Body(max_length=MAX_COLUMNS)],
) -> JSONResponse:
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    if stored is None:
        raise AgentsError(422, "no_dataset")
    try:
        parsed = [Binding(role=item.role, column=item.column) for item in bindings if item.column]
    except ValueError:
        raise AgentsError(422, "invalid") from None
    check, delta = apply_bindings(parsed, view.snapshot.roles(), stored.profile)
    if not delta:
        return JSONResponse(
            status_code=422, content={"detail": "invalid", "errors": check.errors[:20]}, headers=_NO_STORE
        )
    # The page also PUTs the parse's own defaults after every paste (to learn `complete`), which changes nothing: only
    # a PUT whose bindings differ from the ones the session held counts, so that echo never reads as a manual change.
    by_hand = _binding_pairs(delta[BINDINGS]) != _binding_pairs([binding.model_dump() for binding in view.bindings])
    if by_hand:
        # For the root's next turn: which pairs the user set, so it reads them as the user's choice (`USER_BOUND`).
        delta = {**delta, USER_BOUND: _hand_bound(session.state.get(USER_BOUND), view.bindings, delta[BINDINGS])}
    # Other bindings than the user confirmed leave the confirmation's fingerprint behind: step 1 again.
    await runtime.write_state(session, delta)
    if by_hand:
        # The next `chat_turn` line says the user changed a binding by hand, and the warnings' closed codes.
        telemetry.marks(sid).manual_binding_changed = True
    telemetry.note_binding_warnings(sid, check.warnings)
    return JSONResponse(
        {
            "bindings": delta[BINDINGS],
            "complete": check.complete,
            "missing_roles": check.missing_roles,
            "warnings": check.warnings,
        },
        headers=_NO_STORE,
    )


@app.put("/v1/sessions/{sid}/language", dependencies=v1_dependencies)
async def put_language(
    sid: SessionId, body: LanguageBody, user: User, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    """The user's pick: the session language and the plot's, from the chip (`via: header`) or an offer (`via: offer`).

    The chip sets the source `chosen`, which is final: no language is offered after it, and the root's
    `set_language` tool makes the same change. An accepted offer sets the source `offer`, so a later message
    in another language may still offer that one. The write is the same either way: the next reply and the next
    plot version use it; earlier versions keep their text, and a plot the library has gets its text rewritten
    by the next version (`pipeline.LANGUAGE_REWRITE_REQUEST`). The pattern runs before `normalise` (a leading
    space is a `422`), and the answer carries the stored form, which the page shows: `English` comes back as
    `en`, `Swedish` as typed. `409 run_active` while a turn or a theme render is in flight in the session, so a
    pick never races the scope guard's offer inside a run; a paste in flight does not block it, because the paste
    reads the session again before it records an offer.
    """
    session = await runtime.session(user, sid)
    _active(runtime, sid, paste=False)
    current = read_session(session.state)
    if current is None:
        raise AgentsError(404, "session_expired")
    value = normalise(body.language)
    if not is_valid(value):
        raise AgentsError(422, "invalid")
    # An offer accepted after a pick (a button another tab still showed) sets the language and keeps the pick final.
    source: LanguageSource = "offer" if body.via == "offer" and current.language_source != "chosen" else "chosen"
    await runtime.write_state(session, {**language_delta(value, source), PLOT_LANGUAGE: value})
    telemetry.write(
        telemetry.LanguageOffer,
        _stamp(RequestLedger(request_id=rid, user_id=user, session_id=sid), current, session),
        attempt=f"{body.via}:{rid}",
        via=body.via,
        language=telemetry.plot_language(value),
    )
    answer: dict[str, Any] = {"language": value, "source": source}
    view = read_session(session.state)
    stored = get_services().datasets.get(view.dataset_id, sid) if view is not None and view.dataset_id else None
    if view is not None and stored is not None:
        # The `.to_long()` offer with its new column names in the new language, so the page's card follows.
        answer["suggestion"] = _suggestion(view, stored.profile, value)
    return JSONResponse(answer, headers=_NO_STORE)


@app.post("/v1/sessions/{sid}/dataset/confirm", dependencies=v1_dependencies)
async def confirm_dataset(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """Step 1 of two: the user confirms that the stored dataset and its bindings fit (owner rule of 2026-10-11).

    The plot pipeline runs only on a confirmed dataset (`not_ready: data_unconfirmed`
    otherwise). A new dataset or a binding change drops the confirmation; a library switch
    keeps it, because the data and the bindings stay.
    """
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    if stored is None:
        raise AgentsError(422, "no_dataset")
    await runtime.write_state(session, confirm_delta(view))
    return JSONResponse(
        {"confirmed": True, "rows": stored.profile.rows, "columns": len(stored.profile.columns)}, headers=_NO_STORE
    )


@app.post("/v1/sessions/{sid}/dataset/undo", dependencies=v1_dependencies)
async def undo_dataset(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """The user's undo of the root's last `prepare_data` or `generate_data`: the version before it is current again.

    The session keeps the last five versions (`dataset_versions.MAX_DATASET_HISTORY`);
    the bindings are carried over like after a `prepare_data`, and the restored version
    is unconfirmed, because the user confirms every version they see. `422
    nothing_to_undo` for a paste that was never prepared (or whose history is spent),
    and for data that `generate_data` made in a session without data (its first version).
    """
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    restored = undo_version(services.datasets, sid, view, view.snapshot)
    if restored is None:
        raise AgentsError(422, "nothing_to_undo")
    await runtime.write_state(session, restored.delta)
    telemetry.marks(sid).undo = True  # the next `chat_turn` line's `undo`
    return JSONResponse(
        {
            **restored.payload(),
            "roles": _page_roles(view.snapshot.roles()),
            "suggestion": _suggestion(view, restored.stored.profile),
        },
        headers=_NO_STORE,
    )


@app.post("/v1/sessions/{sid}/dataset/to_long", dependencies=v1_dependencies)
async def dataset_to_long(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """The page's `.to_long()`: apply the wide-table suggestion to the current dataset, without a model call.

    The server recomputes the suggestion (`data/shape.py`) from the session's spec and
    current profile, so the client never names an operation; `422 no_suggestion` when
    the table is not wide for this spec (any more). The result is stored as the next
    dataset version like a `prepare_data` (undo, history), with the new columns bound to the
    roles they were made for and the defaults for the rest (`LongSuggestion.bindings`),
    unconfirmed, and the answer is the undo route's shape plus
    `changes`, the operation's change line.
    """
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    suggestion = long_suggestion(view.snapshot.roles(), stored.profile, view.language) if stored is not None else None
    if stored is None or suggestion is None:
        raise AgentsError(422, "no_suggestion")
    try:
        operations = OPERATIONS.validate_python([suggestion.operation()])
        prepared = apply_operations(stored.as_parsed(), operations)
        parsed = parse_dataset(
            prepared.csv,
            text_columns=prepared.text_columns,
            find_table=False,
            max_bytes=MAX_COMPUTED_BYTES,
            canonical=True,
        )
        parsed = with_date_notes(parsed, prepared)
    except PrepareError, ParseError, ValidationError:
        raise AgentsError(422, "no_suggestion") from None
    try:
        # The new columns go to the roles they were made for, whatever their names (`LongSuggestion.bindings`).
        version = push_version(
            services.datasets, sid, view, parsed, view.snapshot, pinned=suggestion.bindings(), changes=prepared.changes
        )
    except StoreFull:
        raise AgentsError(503, "capacity") from None
    await runtime.write_state(session, version.delta)
    telemetry.marks(sid).to_long = True  # the next `chat_turn` line's `to_long`
    return JSONResponse(
        {
            **version.payload(),
            "roles": _page_roles(view.snapshot.roles()),
            "suggestion": _suggestion(view, version.stored.profile),
            "changes": prepared.changes,
        },
        headers=_NO_STORE,
    )


@app.post("/v1/sessions/{sid}/dataset/copy", dependencies=v1_dependencies)
async def copy_dataset(
    sid: SessionId, body: CopyDatasetBody, user: User, tier: CallerTier, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    """The admin fan-out's copy: the confirmed current data version of `from_session` becomes this session's data.

    Owner decision of 2026-11-01: `.plot_all()` plots exactly the data the user confirmed, whether it was pasted,
    opened, computed or changed by the assistant, so the server copies that version instead of the page posting
    the paste again. Both sessions must be the caller's: each one is looked up under the caller's user id, so
    another user's session id is `404 session_expired` as on every route, and no data ever crosses users. The
    target must be a fan-out session (`source: fanout` at its opening) of the same spec without data
    (`409 has_dataset`); the source another session with data (`422 no_dataset`) that the user confirmed with its
    current bindings (`422 unconfirmed`). `422 invalid` for the same session twice, a target that is no fan-out
    session, another spec, or bindings the target's roles refuse. Neither session may have a turn, a theme render
    or a paste in flight (`409 run_active`), since the source's data would be about to change.

    The copy is the stored version as it is (`DatasetStore.copy`): the same canonical CSV, dtypes, column order,
    notes, file name, source and code, nothing parsed or judged again, so it costs no model call and counts as no
    paste; its own counter (`COPIES_PER_MINUTE`, `_PER_DAY`) bounds what one user puts in the store, except for an
    admin, whose fan-outs in several windows copy more at once and whom only the store's byte cap bounds. The bindings,
    their confirmation, the session language and the plot language come along. The copy is the target's first version
    under its next number (1, since the target has no data) with no undo history, and `DATASET_COPIED_FROM` records the
    source's version number. The answer is the paste route's
    dataset shape plus `confirmed`, `complete`, `missing_roles` and `copied_from`. The `dataset_copy` attribution
    line carries the counts, the version number and the source session's salted hash, never data; a copy writes
    no `data_input` telemetry line, because no input reached the dataset route.
    """
    services = get_services()
    if body.from_session == sid:
        raise AgentsError(422, "invalid")
    session = await runtime.session(user, sid)
    source = await runtime.session(user, body.from_session)  # another user's session is not found either
    _active(runtime, sid)
    _active(runtime, body.from_session)
    view = read_session(session.state)
    origin = read_session(source.state)
    if view is None or origin is None:
        raise AgentsError(404, "session_expired")
    if session.state.get(TELEMETRY_SOURCE) != "fanout" or origin.spec_id != view.spec_id:
        raise AgentsError(422, "invalid")
    if view.dataset_id:
        raise AgentsError(409, "has_dataset")
    stored = services.datasets.get(origin.dataset_id, body.from_session) if origin.dataset_id else None
    if stored is None:
        raise AgentsError(422, "no_dataset")
    if not origin.data_confirmed:
        raise AgentsError(422, "unconfirmed")
    roles = view.snapshot.roles()
    check = check_bindings(origin.bindings, roles, stored.profile)
    if check.errors:
        raise AgentsError(422, "invalid")
    ledger = _stamp(
        RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action", tier=tier), view, session
    )
    limit = services.usage.copy_limit(user, tier)  # never a limit for an admin; the store's byte cap still binds
    if limit is not None:
        attribution("dataset_copy", ledger, outcome=limit)
        raise AgentsError(429, limit)
    try:
        dataset_id = services.datasets.copy(stored.dataset_id, body.from_session, sid, number=view.next_version)
    except StoreFull:
        attribution("dataset_copy", ledger, outcome="capacity")
        raise AgentsError(503, "capacity") from None
    copied = services.datasets.get(dataset_id, sid) if dataset_id else None
    if copied is None:  # read above with no `await` in between: only a store emptied behind the state
        raise AgentsError(422, "no_dataset")
    services.usage.add_copy(user)
    bindings = origin.bindings
    # The page's plot language, which can differ from its reply language: its user's choice for the plot, else the
    # language its latest plot shows. Without either the page's plot would follow its session language, which the
    # copy carries anyway, so no choice is made up for the target.
    origin_latest = services.versions.latest_language(body.from_session)
    shown: dict[str, Any] = {}
    if origin.plot_language_choice is not None or origin_latest is not None:
        shown[PLOT_LANGUAGE] = plot_language(origin, origin_latest)
    # `.plot_all()` plots the user's tuned plot in every library (2026-11-02): the memory comes along, and a carry for
    # this session's library from the page session's latest plot, so the fan-out's `carry_plot` takes both. A plot of
    # data before the copied version carries only its asked theme to it (`source_plot`), as "plot the new data" keeps
    # the theme too.
    memory = read_memory(source.state)
    carry = carry_for(
        source=Target(spec_id=origin.spec_id, library=origin.library),
        target=Target(spec_id=view.spec_id, library=view.library),
        plot=source_plot(
            services.versions.latest_rendered(body.from_session, target=origin.target), origin.dataset_version
        ),
        pending=read_carry(source.state, origin.target),
        memory=memory,
    )
    carried = switch_summary(carry, memory, None, written=memory_written(source.state))
    shown.update(memory_delta(memory, next_seq(source.state, memory)))
    shown[CARRY] = carry.model_dump(mode="json") if carry is not None else None
    # From the reads above to this write nothing suspends (see `_ingest_paste`): the source's state cannot change
    # between the confirmation check and the copy.
    await runtime.write_state(
        session,
        {
            DATASET_ID: copied.dataset_id,
            BINDINGS: [binding.model_dump() for binding in bindings],
            DATASET_HISTORY: [],
            DATASET_VERSION: copied.number,
            DATASET_ORIGINAL: copied.dataset_id,  # the copy is the original of the versions made from it here
            DATASET_TOP: copied.number,
            DATASET_COPIED_FROM: origin.dataset_version,
            CONFIRMED: confirmation_fingerprint(copied.dataset_id, bindings),
            **language_delta(origin.language, origin.language_source),
            # The page session's offers stand for its copies: a fan-out session never offers one again.
            LANGUAGE_OFFERED: list(origin.language_offered),
            **shown,
            **PENDING_CLEARED,
        },
    )
    attribution(
        "dataset_copy",
        ledger,
        outcome="ok",
        rows=copied.profile.rows,
        columns=len(copied.profile.columns),
        version=origin.dataset_version,
        from_session=session_hash(body.from_session),
    )
    return JSONResponse(
        {
            **dataset_payload(copied, bindings, can_undo=False, original_version=copied.number),
            "roles": _page_roles(roles),
            "suggestion": _suggestion(view, copied.profile, origin.language),
            "language": _language_body(origin),
            "confirmed": True,
            "complete": check.complete,
            "missing_roles": check.missing_roles,
            "copied_from": origin.dataset_version,
            # What the fan-out's run takes over: with `offer`, it sends `carry_plot` instead of `create_plot`.
            "carry": carried.body(),
        },
        headers=_NO_STORE,
    )


@app.get("/v1/sessions/{sid}/dataset/data.csv", dependencies=v1_dependencies)
async def dataset_csv(sid: SessionId, user: User, runtime: RuntimeDep) -> Response:
    """The current dataset version's canonical `data.csv` as stored: the data panel's full view (`.view_all()`).

    The bytes the next plot run reads (`StoredDataset.csv`, at most `parse.MAX_CANONICAL_BYTES`), never formatted
    again, so the page shows every value as the data holds it. A version's `GET .../artifacts/data.csv` is the data
    a plot was made from; this is the data the panel shows now, also in step 1 before any plot. A read with no model
    call and no state write, so no `_active` check: it neither races nor blocks a turn, and when a turn stores a
    new version meanwhile, the page fetches again. `422 no_dataset` without data, as on the other dataset routes.
    """
    services = get_services()
    session = await runtime.session(user, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    if stored is None:
        raise AgentsError(422, "no_dataset")
    return Response(
        stored.csv.encode("utf-8"),
        media_type=ARTIFACT_TYPES["data.csv"],
        headers={**_NO_STORE, "X-Content-Type-Options": "nosniff"},
    )


def _suggestion(view: SessionView, profile: DatasetProfile, language: str | None = None) -> dict[str, Any] | None:
    """The wide-table suggestion for a dataset answer (`data/shape.py`), or None.

    Its new column names are in the session language (`language`, else the view's), as the `.to_long()` route
    computes them. `siblings` are the columns no role that takes labels should be bound to
    (`bindings.label_siblings`): the page warns under such a dropdown, as the session block warns the root.
    """
    roles = view.snapshot.roles()
    suggestion = long_suggestion(roles, profile, language or view.language)
    if suggestion is None:
        return None
    return {**suggestion.body(), "siblings": label_siblings(roles, profile)}


def _language_body(view: SessionView, offer: tuple[str, str] | None = None) -> dict[str, Any]:
    """The session language as the page reads it, `{language, source}`, and the language to offer, if any.

    `offer` is `(language, basis)`, the basis `message` (a typed message) or `data` (a paste's notes or column
    names); the body carries it as `offer: {language, basis}` only while it still holds: never after a pick, which
    the root's `set_language` may have made in the same turn, and never for the language the session has now.
    """
    body: dict[str, Any] = {"language": view.language, "source": view.language_source}
    if offer is not None and view.language_source != "chosen" and not same_language(offer[0], view.language):
        body["offer"] = {"language": offer[0], "basis": offer[1]}
    return body


def _telemetry_offer(ledger: RequestLedger | None, body: dict[str, Any]) -> None:
    """The `language_offer` line (`via: shown`) for a language body that carries an offer to the page: content-free,
    the language as a closed code. One per offer, since each language is offered once per session."""
    offer = body.get("offer")
    if ledger is None or not isinstance(offer, dict):
        return
    telemetry.write(
        telemetry.LanguageOffer,
        ledger,
        attempt=f"shown:{ledger.request_id}",
        via="shown",
        language=telemetry.plot_language(offer["language"]),
    )


async def _session_sync(
    runtime: Runtime, user: str, sid: str, *, dataset_before: str | None = None, ledger: RequestLedger | None = None
) -> dict[str, Any]:
    """The `done` event's sync fields after a turn: the bindings, whether the data is confirmed, a changed dataset,
    the session language and the wide-table offer in it (`suggestion`, whenever the session has data).

    The root's `set_bindings` tool may have changed the bindings (and dropped the
    confirmation) during the turn, and its `prepare_data` or `generate_data` tool the
    dataset itself: when the dataset id differs from `dataset_before`, `dataset` carries
    the new version as the dataset route would answer it (`roles` included, because a
    `generate_data` in a session without data stores its first version, and the page
    learns the spec's roles only from a dataset answer), plus the turn's change lines
    from the ledger. The page learns both from `done`. The root's `set_language` may have set
    the session language, so `language` carries it as `{language, source}` after every run,
    for the page's chip, with `offer` when the scope guard offered the message's language
    (`_language_body`). Empty when the session is gone, so the stream still closes.
    """
    try:
        session = await runtime.session(user, sid)
    except Exception:  # expired or purged while the turn ran: the page's next request learns it
        return {}
    view = read_session(session.state)
    if view is None:
        return {}
    payload: dict[str, Any] = {
        "bindings": [binding.model_dump() for binding in view.bindings],
        "data_confirmed": view.data_confirmed,
        "language": _language_body(view, ledger.language_offer if ledger is not None else None),
    }
    _telemetry_offer(ledger, payload["language"])
    stored = get_services().datasets.get(view.dataset_id, sid) if view.dataset_id else None
    if stored is not None:
        # The wide-table offer in the session language after the turn: `set_language` may have changed it, and the
        # page's card must name what `.to_long()` applies.
        payload["suggestion"] = _suggestion(view, stored.profile)
        if view.dataset_id != dataset_before:
            changes = list(ledger.dataset_changes) if ledger is not None else []
            original_version = original_number(get_services().datasets, sid, view)
            payload["dataset"] = {
                **dataset_payload(stored, view.bindings, can_undo=view.can_undo, original_version=original_version),
                "roles": _page_roles(view.snapshot.roles())[:MAX_DONE_ROLES],
                "suggestion": payload["suggestion"],
                "changes": changes,
            }
    return payload


@dataclass(frozen=True)
class TurnFacts:
    """What the `chat_turn` telemetry line needs from the route besides the ledger: the action, the session
    language and its source (read before the turn, and again after its run, `_after_turn`), and the turn's
    stopwatch."""

    action: Action | None
    language_source: str | None
    language: str | None = None
    clock: telemetry.Clock = field(default_factory=telemetry.Clock)


async def _summarized(runtime: Runtime, user: str, sid: str, dataset_ids: Collection[str]) -> None:
    """Clear `SUMMARY_PENDING` for the dataset the turn started on, or the version of the conversions the server
    made on it (`paste_conversions.py`), which the flag names then; never raises.

    Only while the state still names one of them: a turn's own `prepare_data` keeps the flag off already (a new
    version is no paste), and nothing else can store data while the run is active. A session gone meanwhile has
    nothing to clear.
    """
    try:
        session = await runtime.session(user, sid)
        if session.state.get(SUMMARY_PENDING) in dataset_ids:
            await runtime.write_state(session, {SUMMARY_PENDING: None})
    except Exception as exc:  # the turn's answer stands; the next turn is the note path once more
        logger.warning("summary flag not cleared: %s", type(exc).__name__)


async def _settle_kept_note(runtime: Runtime, user: str, sid: str, ledger: RequestLedger) -> None:
    """Hold the first-plot note this turn kept for the bindings and data the turn ends with; never raises.

    The root acts on one note in one turn, and in any order: it may keep the plot wish first and then bind the
    columns the note names or sum the data. The note was written for the turn's end, so its bindings are those
    (`PENDING_BINDINGS`, which the run judges, `pipeline.pending_fate`), and a data version the turn made, which
    drops a kept note, gets it back. A turn whose plot shipped took the note already.
    """
    note = ledger.kept_note
    if note is None or ledger.shipped_in_turn:
        return
    try:
        session = await runtime.session(user, sid)
        state = dict(session.state)
        if not any(state.get(key) is not None for key in (PENDING_REQUEST, PENDING_EXPECTED_TEXTS, PENDING_REMEMBER)):
            hold_request(state, note)  # a data version of this turn dropped it
        bindings = state.get(BINDINGS)
        state[PENDING_BINDINGS] = list(bindings) if isinstance(bindings, list) else []
        keys = (PENDING_REQUEST, PENDING_EXPECTED_TEXTS, PENDING_REMEMBER, PENDING_BINDINGS, PENDING_BASE)
        await runtime.write_state(session, {key: state.get(key) for key in keys})
    except Exception as exc:  # the turn's answer stands; the note holds for the bindings it was kept with
        logger.warning("kept note not settled: %s", type(exc).__name__)


async def _after_turn(runtime: Runtime, user: str, sid: str, facts: TurnFacts) -> TurnFacts:
    """`facts` with the session language and its source as the turn left them.

    The root's `set_language` sets them inside the run (`_produce`), so the turn that switches the language
    records the new value, not the one it started with. The values from before the turn stay when the session is
    gone.
    """
    try:
        view = read_session((await runtime.session(user, sid)).state)
    except Exception:  # expired or purged while the turn ran: the line keeps what the turn started with
        return facts
    if view is None:
        return facts
    return replace(facts, language=view.language, language_source=view.language_source)


def _telemetry_turn(ledger: RequestLedger, facts: TurnFacts, failure: str | None = None) -> None:
    """The usage telemetry's `chat_turn` line (`telemetry.py`): kinds, flags, closed names and counts, never text.

    The request id goes into the idempotency key only (hashed), so two turns of the same number, such as a turn
    refused before the judge and the turn sent after it, stay two rows.
    """
    codes = telemetry.turn_codes(ledger, failure)  # the turn's record (`_keep_turn`) writes the same three
    telemetry.write(
        telemetry.ChatTurn,
        ledger,
        attempt=f"turn:{ledger.request_id}",
        kind=codes.kind,
        action=facts.action or "text",
        asked_question=ledger.reply_question and ledger.refusal is None,
        tools=sorted({tool for tool in ledger.tools if tool in telemetry.TOOL_NAMES}),
        prep_ops=sorted({op for op in ledger.prep_ops if op in telemetry.PREP_OPS}),
        prep_calls=ledger.tools.count("prepare_data"),
        capability_gap=telemetry.closed_set(ledger.capability_gaps, telemetry.CAPABILITY_GAPS),
        refusal=codes.refusal,
        error=codes.error,
        reply_reasked=ledger.reply_reasked,
        language_source=telemetry.closed(facts.language_source, get_args(telemetry.LanguageSource), "default"),
        plot_language=telemetry.plot_language(facts.language),
        llm_calls=ledger.llm_calls,
        steps=telemetry.step_tokens(
            ledger.steps, steps=("root", "adapter", "reviewer", "judge"), judge_model=get_settings().judge_model
        ),
        latency_ms=facts.clock.ms(),
        **telemetry.take_turn_marks(ledger.session_id),
    )


def _keep_turn(runtime: Runtime, ledger: RequestLedger, facts: TurnFacts, failure: str | None = None) -> None:
    """The turn's record for the feedback case (`turn_record.py`), kept next to its `chat_turn` line at each of the
    turn's ends with the same `failure`: the root's tool calls and the guards' verdicts, closed codes only. A session
    purged while the turn ran (its turn log is gone, `Runtime.purge`) keeps nothing, so no ring outlives its session.
    Never raises, and logs the exception's class only: the record must never cost the turn."""
    try:
        if ledger.session_id not in runtime.turns:
            return
        get_services().turns.add(ledger.session_id, turn_record.build(ledger, facts.action, failure))
    except Exception as exc:
        logger.warning("turn record failed: %s", type(exc).__name__)


async def _refused(
    runtime: Runtime, translator: Translator, ledger: RequestLedger, facts: TurnFacts
) -> AsyncGenerator[str, None]:
    """A turn the ledger refused before the scope judge and any model call: `ready`, the refusal, `done`."""
    yield translator.ready()
    for chunk in translator.refusal():
        yield chunk
    attribution("run", ledger, model_versions=[], kind=ledger.kind)
    _telemetry_turn(ledger, facts)
    _keep_turn(runtime, ledger, facts)
    yield translator.done()


def _turn_stream(
    chunks: AsyncGenerator[str, None], log: TurnLog, background: BackgroundTask | None = None
) -> StreamingResponse:
    """A turn's SSE response: `chunks` with every event numbered and kept in the session's turn log."""
    return StreamingResponse(
        logged(chunks, log),
        media_type="text/event-stream",
        headers={**_NO_STORE, "X-Accel-Buffering": "no"},
        background=background,
    )


def _refuse_now(
    runtime: Runtime,
    translator: Translator,
    ledger: RequestLedger,
    facts: TurnFacts,
    log: TurnLog,
    code: str,
    hook: str,
    **fields: Any,
) -> StreamingResponse:
    """The fixed refusal `code` as the whole turn, sent before the judge: no model call, no queue, no message counted."""
    ledger.refuse(code, refusal(code, ledger.lang))
    attribution(hook, ledger, verdict=code, **fields)
    return _turn_stream(_refused(runtime, translator, ledger, facts), log)


async def _produce(
    runtime: Runtime, user: str, sid: str, message: types.Content, run: ActiveRun, outbox: "asyncio.Queue[StreamNote]"
) -> None:
    """The ADK run in a task of its own, its events into the stream's outbox.

    The stream reads the outbox, so the queue positions a sandbox run's `TurnSlot.take`
    puts there while the run is blocked in that tool reach the client meanwhile. An
    exception ends the outbox like the run's end and is raised in the stream.
    """
    settings = get_settings()
    try:
        events = runtime.get_runner().run_async(
            user_id=user,
            session_id=sid,
            new_message=message,
            run_config=RunConfig(max_llm_calls=settings.max_llm_calls, streaming_mode=StreamingMode.NONE),
            abort_signal=run.abort,
        )
        async with contextlib.aclosing(events) as iterator:
            async for event in iterator:
                outbox.put_nowait(("event", event))
    finally:
        outbox.put_nowait(("end", None))


def ended_well(ledger: RequestLedger, run: ActiveRun, failure: str | None) -> bool:
    """Whether a turn ended without an error, a refusal or the user's stop: only such a turn's `done` says what it
    changed (`turn`), since the page marks no refused, failed or stopped turn. A run the deadline cut after its plot
    shipped ended well; the user's `.stop()` (`POST .../cancel`) aborts it without the deadline."""
    stopped = run.abort.is_set() and not run.deadline_hit
    return failure is None and ledger.refusal is None and not stopped


def _error_code(exc: BaseException) -> str:
    if model_busy(exc):  # a model quota or overload after the SDK's retries: busy, like a full queue
        return "capacity"
    if type(exc).__name__ == "LlmCallsLimitExceededError":
        return "capacity"
    return "internal"


@app.post("/v1/sessions/{sid}/messages", dependencies=v1_dependencies)
async def post_message(
    sid: SessionId,
    body: MessageBody,
    user: User,
    tier: CallerTier,
    runtime: RuntimeDep,
    rid: RequestId,
    theme: Theme | None = None,
) -> StreamingResponse:
    """One chat turn as SSE. `theme` is the site theme the page shows, the theme a plot run of the turn renders
    unless the user asked for one (`pipeline.run_theme`). A query parameter, not a body field: the strict bodies of
    this service and the BFF would refuse it from a page deployed before them, while an unknown parameter is ignored.
    """
    if body.text is not None and len(body.text) > MAX_MESSAGE_CHARS:
        raise AgentsError(413, "too_long")
    session = await runtime.session(user, sid)
    _active(runtime, sid)  # one turn per session; the user's other sessions run their turns in parallel
    settings = get_settings()
    services = get_services()
    view = read_session(session.state)
    ledger = RequestLedger(
        request_id=rid,
        user_id=user,
        session_id=sid,
        kind="action" if body.action else "text",
        tier=tier,
        # The refusals sent before the judge (the budget, unsupported content) follow the
        # session language, never the browser's locale, and so do the ones after the judge.
        lang=refusal_lang(view.language) if view else DEFAULT_LANGUAGE,
        site_theme=theme,
        fresh_start=body.action == "create_plot",
        new_data=body.action == "plot_new_data",
        plot_action=body.action in PLOT_ACTIONS,
    )
    _stamp(ledger, view, session)
    ledger.turn += 1  # this turn's number: the user turns before it, plus one
    facts = TurnFacts(
        action=body.action,
        language_source=view.language_source if view else None,
        language=view.language if view else None,
    )
    translator = Translator(ledger, run_id=secrets.token_hex(8), spec_id=view.spec_id if view else None)
    # Every turn, a refused one too, is the session's latest: a page that lost its stream reads the rest from here.
    log = runtime.start_turn(sid, translator.run_id)
    # The fixed refusals sent before the scope judge, so none of these turns costs a model call.
    # A closed session answers `session_closed` first: its third `attack` refusal also reaches the strike lockout,
    # which would otherwise mask the closure behind `budget` here (the lockout still covers the user's other sessions).
    # The limits stay per user while the user's sessions run turns in parallel (2026-10-21), and may overlap:
    # - messages: checked and counted below with no suspending `await` between, so they never overshoot;
    # - the daily token budget: checked here and before every model call (`plugins/budget.py`), booked after each
    #   call, so parallel turns overshoot it by at most the model calls they have in flight;
    # - daily pipeline runs: checked and counted in one step (`BudgetPlugin.before_tool_callback`), no overshoot;
    # - daily data runs: checked before the queue wait and counted after it (`tools/session.run_data_code`), so the
    #   user's runs waiting in other sessions, at most `AGENT_USER_MAX_RUNS` - 1, can overshoot it by as many.
    # An admin is exempt from all but the strikes and the global budget (`plugins/ledger.py`, the ledger's tier).
    refused = scope_refusals(session.events)
    if refused >= settings.session_refusals:
        return _refuse_now(runtime, translator, ledger, facts, log, SESSION_CLOSED, "session_closed", refusals=refused)
    if services.usage.locked_out(user, settings):
        # Past the day's `attack` strikes: its own refusal, never the misleading "usage limit" text (2026-10-14).
        return _refuse_now(runtime, translator, ledger, facts, log, LOCKED_OUT, "budget_halt", agent="route")
    if not budget_allows(ledger, services.usage, settings):
        # The refusal the root would send, sent now: a user over the daily budget spends nothing. When only the
        # service's day budget is spent, every user gets `service_paused`, which says their own limit is untouched.
        code = day_refusal(services.usage, user, settings, tier=tier)
        return _refuse_now(runtime, translator, ledger, facts, log, code, "budget_halt", agent="route")
    limit = services.usage.message_limit(user, settings, tier)
    if limit is not None:
        return _refuse_now(runtime, translator, ledger, facts, log, limit, "message_limit")
    services.usage.add_message(user)
    run = ActiveRun(abort=asyncio.Event(), user=user, started=runtime.now())
    # Registered here so a second request cannot slip in before the stream starts; the
    # stream's finally and the background task both clear it and free its queue slot,
    # and an entry neither reached (a client gone before the first byte) goes stale
    # after the deadline (or, while a sandbox run waits, the queue's maximum wait).
    runtime.active[sid] = run
    dataset_before = view.dataset_id if view is not None else None
    if view is not None and view.dataset_id:
        # A hit counts as use: the idle sweep must not take the dataset while the run waits.
        services.datasets.get(view.dataset_id, sid)
    text = ACTION_MESSAGES[body.action] if body.action else (body.text or "")
    reply_language = english_name(view.language) if view is not None else None
    if body.action and reply_language is not None and reply_language != "English":
        # The page's English action line is the turn's only user text: it names the reply language itself
        # (live case of 2026-10-14, a German CSV paste answered in English). The name is the server's own word.
        text = f"{text} {ACTION_LANGUAGE_LINE.format(name=reply_language)}"
    # The first turn on a paste summarizes it: the summary action, or the note the user typed with the paste, which
    # the scope judge reads as typed text (and whose language the page may be offered). A summary action afterwards
    # still carries the notes, so a refused note's summary has them too.
    summary_pending = view is not None and view.summary_pending
    first_turn = body.action == "summarize_data" or (summary_pending and body.text is not None)
    # The summary of a paste not summarized yet: the root's before-agent callback makes its `certain` conversions
    # (`paste_conversions.py`). A summary action on data already summarized makes none, nor does any later turn.
    ledger.summary_turn = first_turn and summary_pending
    # The note came with the data, so while that table is stored (`paste_table` below) the scope judge's `needs_data`
    # and, within the user's day of `AGENT_PASTE_NOTE_RESCUES`, `out_of_scope` go on (`ScopeGuardPlugin._judge`).
    ledger.paste_note = summary_pending and body.text is not None
    # What the user wrote, which a text the plot is checked for must stand in (`pipeline.in_users_words`): the typed
    # message, and the notes pasted with the data, on any turn ("the title from my notes" may come later). A line the
    # parser made from a column with one value (`CONSTANT_NOTE_SUFFIX`) is a cell of the table, not the user's words;
    # a pasted note that happens to end the same way only goes unchecked in the render.
    words = [body.text] if body.text else []
    stored = services.datasets.get(view.dataset_id, sid) if view is not None and view.dataset_id else None
    if stored is not None:
        words += [line for line in stored.context_lines if not line.endswith(CONSTANT_NOTE_SUFFIX)]
    if ledger.paste_note and view is not None and stored is not None:
        # The judge reads the note as notes that came with this table: the spec's title and the column names, no cell.
        ledger.paste_table = paste_table_line(view.snapshot.title, [column.name for column in stored.profile.columns])
    if first_turn and stored is not None:
        blocks: list[str] = []
        if stored.context_lines:
            # The notes pasted with the table, judged at the paste (`_screen_notes`): the root sees them with the
            # first turn on every paste, so it can act on a request in them at once.
            blocks.append(user_notes_block(stored.context_lines))
        if stored.file_name:
            # A dropped file's name, screened at the paste (`_screen_file_name`): fenced as data, never a note.
            blocks.append(file_name_block(stored.file_name))
        if blocks and body.action:
            # The scope judge skips an action, so the blocks follow its fixed line.
            text = "\n\n".join([text, *blocks])
        elif blocks:
            # A typed note is judged: the judge, the language detection, a strike and the stored user turn take the
            # note alone, never the notes judged at the paste again or the preambles' English words.
            ledger.paste_context = "\n\n".join(blocks)
    ledger.user_words = "\n".join(words)
    message = types.Content(role="user", parts=[types.Part(text=text)])

    async def stream() -> AsyncGenerator[str, None]:
        token = CURRENT_LEDGER.set(ledger)
        deadline = RunDeadline(run, settings.request_deadline_s)
        outbox: asyncio.Queue[StreamNote] = asyncio.Queue()
        # Only a sandbox run takes the queue's slot, mid-turn: everything before it answers at once.
        ledger.run_slot = TurnSlot(runtime, run, sid, ledger, deadline, outbox).take
        producer: asyncio.Task[None] | None = None
        failure: str | None = None
        closed_early = False
        try:
            yield translator.ready()
            deadline.arm(runtime.now())
            producer = asyncio.create_task(_produce(runtime, user, sid, message, run, outbox))
            while True:
                try:
                    # A model call or a render sends nothing for a minute or more: a comment every heartbeat keeps
                    # bytes on the BFF's hop, as the BFF's own pings do on the browser's. The timeout wraps the
                    # wait only, never a yield (PEP 789).
                    async with asyncio.timeout(HEARTBEAT_S):
                        note = await outbox.get()
                except TimeoutError:
                    yield PING
                    continue
                if note[0] == "queued":
                    yield translator.queued(note[1].position, note[1].waiting)
                elif note[0] == "started":
                    yield translator.started()
                elif note[0] == "event":
                    for chunk in translator.translate(note[1]):
                        yield chunk
                else:
                    await producer  # raises the run's exception, if it ended with one
                    break
        except Exception as exc:  # the stream always ends with error + done, never a traceback
            logger.warning("run failed (ref %s): %s", rid, type(exc).__name__)
            failure = _error_code(exc)
        except BaseException:  # the generator is closed or cancelled (the client went): release the run now
            closed_early = True
            runtime.finish(sid, run)
            raise
        finally:
            deadline.cancel()
            if producer is not None and not producer.done():
                producer.cancel()
                with contextlib.suppress(BaseException):
                    await producer
            CURRENT_LEDGER.reset(token)
            if closed_early:
                # The client went: the turn's line still books what it spent, once, after the producer stopped.
                after = facts
                with contextlib.suppress(BaseException):  # the original exit goes on after the line
                    after = await _after_turn(runtime, user, sid, facts)
                _telemetry_turn(ledger, after, "cancelled")
                _keep_turn(runtime, ledger, after, "cancelled")
        try:
            if ledger.error is not None:
                failure = ledger.error
            elif run.deadline_hit and not translator.plot_sent:
                failure = "deadline"
            attribution("run", ledger, model_versions=sorted(ledger.model_versions), kind=ledger.kind)
            # Written before anything else is yielded: a client that goes during the error event loses no line.
            after = await _after_turn(runtime, user, sid, facts)
            _telemetry_turn(ledger, after, failure)
            _keep_turn(runtime, ledger, after, failure)
            if failure is not None:
                for chunk in translator.error(failure):
                    yield chunk
            if summary_pending and failure is None and ledger.refusal is None:
                # The root answered on the paste: summarized. A refused or failed turn leaves it pending, a turn whose
                # root wrote no reply too (`no_reply`, `plugins/empty_reply.py`), so the page's summary action, or the
                # next typed message, still gets the paste's notes.
                started_on = view.dataset_id if view is not None else None
                summarized = {dataset_id for dataset_id in (started_on, ledger.conversions_made) if dataset_id}
                await _summarized(runtime, user, sid, summarized)
            await _settle_kept_note(runtime, user, sid, ledger)
            if failure is None and ledger.refusal is None:
                # The root ran and answered: it has read which bindings the user set by hand.
                await _hand_bound_seen(runtime, user, sid)
            # Read while the run is still active: no undo or paste can slip in between the run's end
            # and the `done` that reports its dataset, so the version and the change lines agree.
            sync = await _session_sync(runtime, user, sid, dataset_before=dataset_before, ledger=ledger)
        finally:
            runtime.finish(sid, run)
        # A switch the root asked for goes to the page only with a turn that ended well: after a failure the page
        # shows the error and the user asks again.
        switch = ledger.switch_request if failure is None else None
        turn = turn_outcome(ledger) if ended_well(ledger, run, failure) else None
        yield translator.done(**sync, switch=switch, turn=turn)

    return _turn_stream(stream(), log, BackgroundTask(runtime.finish, sid, run))


@app.post("/v1/sessions/{sid}/cancel", status_code=204, dependencies=v1_dependencies)
async def cancel(sid: SessionId, user: User, runtime: RuntimeDep) -> Response:
    """Abort the session's run; a run that still waits leaves the queue at once. A theme toggle runs to its end."""
    await runtime.session(user, sid)
    run = runtime.active.get(sid)
    if run is not None:
        runtime.stop(run)
    return Response(status_code=204, headers=_NO_STORE)


@app.get("/v1/sessions/{sid}/turn", dependencies=v1_dependencies)
async def get_turn(
    sid: SessionId,
    user: User,
    runtime: RuntimeDep,
    last_event_id: Annotated[str, Header(alias="Last-Event-ID", pattern=EVENT_ID_PATTERN)],
) -> StreamingResponse:
    """The rest of the session's latest turn as SSE, for a page that lost the turn's stream (`agents/turn_log.py`).

    `Last-Event-ID` names the turn and the last event the page read (`<run_id>.<n>`): the events after it, as the
    turn's stream sent them, then each new one until the turn's stream ends, with a ping every heartbeat. A read
    only: it never holds, starts or stops the run, and a turn whose stream ended without `done` (its client went,
    which cancels it) ends the read the same way. `404 not_found` when the session's latest turn is another one
    (or none: a turn of a restarted instance) or the page claims more events than the turn has.
    """
    await runtime.session(user, sid)
    named = parse_event_id(last_event_id)
    log = runtime.turns.get(sid)
    if named is None or log is None or log.run_id != named[0] or named[1] > len(log.events):
        raise AgentsError(404, "not_found")
    return StreamingResponse(
        log.follow(named[1], heartbeat_s=HEARTBEAT_S),
        media_type="text/event-stream",
        headers={**_NO_STORE, "X-Accel-Buffering": "no"},
    )


class RenderThemeBody(_Body):
    theme: Theme


@app.post("/v1/sessions/{sid}/versions/{version}/render", dependencies=v1_dependencies)
async def render_version_theme(
    sid: SessionId,
    version: Annotated[int, Path(ge=0, le=MAX_AGENT_VERSION)],
    body: RenderThemeBody,
    user: User,
    runtime: RuntimeDep,
) -> JSONResponse:
    """The theme toggle: render `theme` of a finished version from its stored run form, with no model call.

    Version 0 is the latest. Synchronous (a render takes seconds): it renders in the
    render slot's `toggle` lane, behind waiting pipeline renders, but not through the
    run queue. It is registered in the run registry while it renders, so it and a turn
    of the same session refuse each other with `409 run_active` in both directions, and a
    session has one run or toggle in flight at a time; it holds only this session's entry,
    so the user's other sessions go on meanwhile (owner decision of 2026-10-21). `503
    capacity` when no render slot came free in time or the render store is full.
    """
    await runtime.session(user, sid)
    _active(runtime, sid)
    services = get_services()
    stored = services.versions.get(sid, version or None)
    if stored is None:
        raise AgentsError(404, "not_found")
    toggle = ActiveRun(abort=asyncio.Event(), user=user, started=runtime.now())
    runtime.active[sid] = toggle  # no await since the check above, so nothing slipped in between
    try:
        result = await render_theme(services, get_settings(), sid, stored, body.theme)
    except RenderGone:
        raise AgentsError(404, "not_found") from None
    except RenderBusy, RenderStoreFull:
        raise AgentsError(503, "capacity") from None
    finally:
        runtime.finish(sid, toggle)
    return JSONResponse(result.public(), headers=_NO_STORE)


async def _served_png(services: Services, sid: str, render_id: str, theme: Theme, spec_id: str) -> bytes | None:
    """One theme's PNG as a user gets it: with the footer strip (`render/watermark.py`) unless `AGENT_WATERMARK` is off.

    The strip is composed in a worker thread on the first request and cached next to
    the raw render (`RenderStore.shown_png`); the raw PNG itself never changes.
    """
    if not get_settings().watermark:
        stored = services.renders.get(render_id, sid)
        return stored.pngs.get(theme) if stored else None

    async def compose(raw: bytes) -> bytes:
        return await asyncio.to_thread(add_footer, raw, theme=theme, spec_id=spec_id)

    return await services.renders.shown_png(render_id, sid, theme, compose)


@app.get("/v1/sessions/{sid}/artifacts/{name}", dependencies=v1_dependencies)
async def artifact(
    sid: SessionId,
    name: str,
    user: User,
    runtime: RuntimeDep,
    v: Annotated[int | None, Query(ge=0, le=MAX_AGENT_VERSION)] = None,
    theme: Theme | None = None,
) -> Response:
    """One artifact of a version; the PNGs carry the footer strip (`AGENT_WATERMARK`), the code and data do not.

    `plot.html` (a JavaScript version only) is built on demand in `theme` (default: the version's own) and answered
    as an attachment (`PAGE_HEADERS`); see `_page`. `theme` is read for it alone.
    """
    media_type = ARTIFACT_TYPES.get(name)
    if media_type is None:
        raise AgentsError(404, "not_found")
    session = await runtime.session(user, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    services = get_services()
    version = services.versions.get(sid, v or None)
    if version is None:
        raise AgentsError(404, "not_found")
    if name == PAGE_ARTIFACT:
        return await _page(runtime, services, user, sid, version, theme or version.theme, view.spec_id)
    content: bytes | None
    if name in CODE_ARTIFACTS:
        content = version.export.encode("utf-8") if name == version.code_artifact else None
    elif name == "data.csv":
        content = version.data_csv.encode("utf-8")
    elif version.render_id:
        png_theme: Theme = "light" if name == "plot-light.png" else "dark"
        content = await _served_png(services, sid, version.render_id, png_theme, view.spec_id)
    else:
        content = None
    if content is None:
        raise AgentsError(404, "not_found")
    return Response(content, media_type=media_type, headers={**_NO_STORE, "X-Content-Type-Options": "nosniff"})


async def _page(
    runtime: Runtime, services: Services, user: str, sid: str, version: CodeVersion, theme: Theme, spec_id: str
) -> Response:
    """A JavaScript version's `plot.html` in `theme`, built now (`page_export.page_download`), never stored.

    Like the theme toggle it builds in the render slot's `toggle` lane and holds the session's
    registry entry while it builds, so it and a turn, a paste or a toggle of the same session
    refuse each other with `409 run_active`. `404 not_found` for a version without a page,
    `503 capacity` when no slot came free in time, `503 page_unavailable` when the renderer
    builds no pages (one deployed before `POST /page`, or none reachable), `500 page_failed`
    when the build left none (its kind, class and line are logged, never its message).
    """
    if PAGE_ARTIFACT not in version.artifacts():
        raise AgentsError(404, "not_found")
    _active(runtime, sid)
    build = ActiveRun(abort=asyncio.Event(), user=user, started=runtime.now())
    runtime.active[sid] = build  # no await since the check above, so nothing slipped in between
    try:
        content = await page_download(services, get_settings(), version, theme, spec_id=spec_id)
    except NoPage:
        raise AgentsError(404, "not_found") from None
    except RenderBusy:
        raise AgentsError(503, "capacity") from None
    except PageUnsupported, RendererUnavailable:
        raise AgentsError(503, "page_unavailable") from None
    except PageFailed:
        raise AgentsError(500, "page_failed") from None
    finally:
        runtime.finish(sid, build)
    return Response(content, media_type=ARTIFACT_TYPES[PAGE_ARTIFACT], headers=PAGE_HEADERS)


def _prompt_hashes() -> dict[str, str]:
    """The version stamp of every static instruction (`policy.prompt_hash`), for the feedback case's config.

    Both reviewer modes have a key: `reviewer` is the checklist instruction, `reviewer_catalogue` the catalogue one
    (the live mode). Before 2026-10-30 only `reviewer` was there, so a change of the catalogue rubric changed no
    hash; adding the key shifted every case's combined `prompt_hash` once.
    """
    from agents.anyplot import policy

    texts = {
        "root": policy.root_instruction(),
        "reviewer": policy.reviewer_instruction(),
        "reviewer_catalogue": policy.catalogue_reviewer_instruction(),
        **{f"adapter_{library}": policy.adapter_instruction(library) for library in agent_module.ADAPTERS},
    }
    return {name: policy.prompt_hash(text) for name, text in texts.items()}


@app.get("/v1/sessions/{sid}/bundle", dependencies=v1_dependencies)
async def bundle(
    sid: SessionId,
    user: User,
    runtime: RuntimeDep,
    version: Annotated[int | None, Query(ge=0, le=MAX_AGENT_VERSION)] = None,
    include_data: bool = False,
) -> JSONResponse:
    """The feedback case: transcript, code versions, plans, results, profile, bindings, PNGs, config.

    Without `version` every version; with a number above 0 that version only (`404 not_found`
    when the session lacks it); with `version=0` the conversation alone, the feedback on a chat
    that made no plot: no version, and with `include_data` the session's current `data.csv` as
    the top-level `data_csv`. A fan-out session whose data is a copy names the source's data version
    as `session.dataset_copied_from`. `session.versions` counts the versions the session holds and
    `session.last_run` says how its latest plot run ended, in every form, also `version=0`; so does `turns`, the
    record of the session's latest turns (`turn_record.py`: `records`, the root's tool calls and the guards'
    verdicts per turn as closed codes, and `dropped`, the older turns the ring no longer holds). A record's `turn` is
    the ordinal of its user line in `transcript`; a turn refused before the scope judge stores no line and shares the
    number of the next turn's.
    """
    session = await runtime.session(user, sid)
    services = get_services()
    settings = get_settings()
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    versions = services.versions.all(sid)
    held = len(versions)
    if version == 0:
        versions = []
    elif version is not None:
        versions = [item for item in versions if item.number == version]
        if not versions:
            raise AgentsError(404, "not_found")
    transcript = []
    for event in session.events:
        if event.author not in ("user", agent_module.ROOT_NAME) or not event.content or not event.content.parts:
            continue
        if event.get_function_calls() or event.get_function_responses():
            continue
        text = "".join(part.text or "" for part in event.content.parts if part.text and not part.thought)
        if text.strip():
            transcript.append({"role": "user" if event.author == "user" else "assistant", "text": text})
    dataset = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    items = []
    for item in versions:
        images: dict[Theme, str] = {}
        stored = services.renders.get(item.render_id, sid) if item.render_id else None
        if stored is not None:
            for theme in list(stored.pngs):  # a copy: a theme toggle may add a theme during an await
                png = await _served_png(services, sid, stored.render_id, theme, view.spec_id)
                if png is not None:
                    images[theme] = base64.b64encode(png).decode()
        items.append(
            {
                "number": item.number,
                "title": item.title,
                "working": item.working,
                "run_form": item.run_form,
                "plot_py": item.export,
                "code_artifact": item.code_artifact,
                # A session can switch its target, so each version names the spec and library it was made in.
                "spec_id": item.spec_id,
                "library": item.library,
                "plan": item.plan.model_dump(mode="json") if item.plan else None,
                "result": item.result.model_dump(mode="json"),
                "theme": item.theme,
                "language": item.language,
                "themes": {
                    theme: {"status": record.status, "reason": record.reason} for theme, record in item.themes.items()
                },
                "images": images,
                "data_csv": item.data_csv if include_data else None,
            }
        )
    payload: dict[str, Any] = {
        "session": {
            "spec_id": view.spec_id,
            "library": view.library,
            # The browser's locale (the feedback manifest's `language`); the session language is its own pair.
            "locale": view.locale,
            "plot_language": view.language,
            "plot_language_source": view.language_source,
            # Content-free, so a case on one version or on the chat (no version) still says what the session held:
            # how many versions, and how the latest plot run ended (a plot the page missed, or a run that failed).
            "versions": held,
            "last_run": view.last_run.model_dump(mode="json") if view.last_run is not None else None,
        },
        "snapshot": {"spec_id": view.snapshot.spec_id, "library_version": view.snapshot.library_version},
        "transcript": transcript,
        # Content-free like `last_run`, in every form: what each turn called and what its guards said.
        "turns": services.turns.bundle(sid),
        "versions": items,
        "profile": dataset.profile.model_dump(mode="json") if dataset else None,
        "bindings": [binding.model_dump() for binding in view.bindings],
        "config": {
            "provider": settings.provider,
            "model": settings.model,
            "judge_model": settings.judge_model,
            "location": settings.location,
            "adk_version": importlib.metadata.version("google-adk"),
            "service_version": _version(),
            "prompt_hashes": _prompt_hashes(),
        },
    }
    copied_from = session.state.get(DATASET_COPIED_FROM)
    if isinstance(copied_from, int):
        # A fan-out session's data is a copy of the page session's version of this number (`/dataset/copy`).
        payload["session"]["dataset_copied_from"] = copied_from
    if version == 0 and include_data:
        # The chat's case has no version to carry the data: the session's current dataset, or none yet.
        payload["data_csv"] = dataset.csv if dataset else None
    if settings.keep_refusals:
        # The transcript holds only the placeholder of a refused message; the ring holds its text.
        payload["refusals"] = [asdict(item) for item in services.refusals.all(sid)]
    return JSONResponse(payload, headers=_NO_STORE)


class OutcomeBody(_Body):
    """The page's outcome beacon: what the user did with a result, never what it held."""

    action: telemetry.OutcomeAction
    version: int = Field(default=0, strict=True, ge=0, le=MAX_AGENT_VERSION)
    """The result version the action was on; 0 for a session-level action (`saved_session`, feedback on the chat)."""
    reaction: telemetry.Reaction | None = None

    @model_validator(mode="after")
    def _reaction_with_feedback(self) -> "OutcomeBody":
        if self.reaction is not None and self.action != "feedback":
            raise ValueError("reaction goes with the feedback action only")
        return self


@app.post("/v1/sessions/{sid}/outcome", status_code=204, dependencies=v1_dependencies)
async def post_outcome(sid: SessionId, body: OutcomeBody, user: User, runtime: RuntimeDep, rid: RequestId) -> Response:
    """The usage telemetry's `outcome` line for one beacon of the page (`telemetry.py`).

    The page sends it after a copy, a download, a session save or a feedback send; the BFF forwards it, so every
    telemetry line comes from this one writer with the same salted session hash. Content-free by its schema
    (closed `action` and `reaction`, a version number). `429 rate_limited` / `daily_limit` past
    `OUTCOMES_PER_MINUTE` / `_PER_DAY` per user, which the page ignores; `404 session_expired` as everywhere, and
    `404 not_found` for a version the session does not have. A version's line carries that version's library,
    so a card made before a library switch counts for its own library; version 0 carries the session's.
    No model call, no state write: the session's events are untouched.
    """
    session = await runtime.session(user, sid)
    services = get_services()
    version = services.versions.get(sid, body.version) if body.version else None
    if body.version and version is None:
        raise AgentsError(404, "not_found")
    limit = services.usage.outcome_limit(user)
    if limit is not None:
        raise AgentsError(429, limit)
    services.usage.add_outcome(user)
    ledger = _stamp(RequestLedger(request_id=rid, user_id=user, session_id=sid), read_session(session.state), session)
    if version is not None:
        # A result card of an earlier library stays usable after a switch: its outcome counts for its own library.
        ledger.library = version.library
    telemetry.write(
        telemetry.Outcome,
        ledger,
        # Every click is its own row (the request id, hashed into the key only); a line delivered twice still repeats it.
        attempt=f"{body.action}:{body.version}:{rid}",
        action=body.action,
        version=body.version,
        reaction=body.reaction,
    )
    return Response(status_code=204, headers=_NO_STORE)


@app.delete("/v1/sessions/{sid}", status_code=204, dependencies=v1_dependencies)
async def delete_session(sid: SessionId, user: User, runtime: RuntimeDep) -> Response:
    await runtime.session(user, sid)
    await runtime.purge(user, sid, get_services())
    return Response(status_code=204, headers=_NO_STORE)
