"""The admin fan-out's copy, `POST /v1/sessions/{sid}/dataset/copy`: the page session's confirmed data, byte for byte.

Owner decision of 2026-11-01: `.plot_all()` plots exactly what the user confirmed, whatever its origin, so the
agents service copies the source session's confirmed current version into each fan-out session. Both sessions
must be the caller's; the copy parses and judges nothing again.
"""

import io
import json
import logging
import math
from collections.abc import AsyncIterator, Iterator
from dataclasses import asdict
from typing import Any

import httpx
import pandas as pd
import pytest

from agents.anyplot import telemetry
from agents.anyplot.data.parse import pandas_dtypes, parse_dataset
from agents.anyplot.data.store import StoredDataset
from agents.anyplot.dataset_versions import push_version
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.plugins import ledger
from agents.anyplot.plugins.ledger import ATTRIBUTION_LOGGER
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.schemas import Binding, PlotResult
from agents.anyplot.services import CodeVersion, Services
from agents.anyplot.session_state import (
    BINDINGS,
    CONFIRMED,
    DATASET_COPIED_FROM,
    DATASET_VERSION,
    LANGUAGE,
    LANGUAGE_SOURCE,
    PLOT_LANGUAGE,
    SessionView,
    confirmation_fingerprint,
    language_delta,
    plot_language,
    read_session,
)
from agents.main import APP_NAME, Runtime, app, get_runtime

from .fakes import default_script


USER = "adm_copy000000000001"
OTHER = "adm_copy000000000002"
CELL_CANARY = "CANARY-CELL-c0p1"
FIDELITY_DATA = (
    "Study Hours,Exam Score,Attempts,Student\n"
    f"0.12345678901234568,52.5,3,Zoë 🌍\n"
    f"2.000000000000001,NaN,,{CELL_CANARY}\n"
    "3.25,61.75,7,日本語 “quoted”\n"
)
"""A float with 17 significant digits, a NaN, a nullable integer column with a gap and text beyond ASCII."""
FILE_NAME = "scores.csv"


def headers(user: str = USER) -> dict[str, str]:
    return {"X-Anyplot-User": user, "X-Request-Id": f"req-{user[-4:]}"}


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600))
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://agents") as http:
        yield http


async def open_session(
    client: httpx.AsyncClient,
    *,
    user: str = USER,
    library: str = "matplotlib",
    spec_id: str = "scatter-basic",
    fanout: bool = False,
) -> str:
    body: dict[str, Any] = {
        "user": user,
        "spec_id": spec_id,
        "library": library,
        "locale": "en",
        "snapshot": snapshot_from_repo(spec_id, library).model_dump(),
    }
    if fanout:
        body["source"] = "fanout"
    response = await client.post("/v1/sessions", headers=headers(user), json=body)
    assert response.status_code == 200, response.text
    return str(response.json()["session_id"])


async def paste(client: httpx.AsyncClient, sid: str, *, user: str = USER, confirm: bool = True) -> dict[str, Any]:
    pasted = await client.post(
        f"/v1/sessions/{sid}/dataset", headers=headers(user), json={"text": FIDELITY_DATA, "source": FILE_NAME}
    )
    assert pasted.status_code == 200, pasted.text
    if confirm:
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=headers(user))
        assert confirmed.status_code == 200, confirmed.text
    return dict(pasted.json())


async def copy(client: httpx.AsyncClient, sid: str, from_session: str, *, user: str = USER) -> httpx.Response:
    return await client.post(
        f"/v1/sessions/{sid}/dataset/copy", headers=headers(user), json={"from_session": from_session}
    )


async def view_of(runtime: Runtime, sid: str, user: str = USER) -> tuple[SessionView, dict[str, Any]]:
    session = await runtime.session(user, sid)
    view = read_session(session.state)
    assert view is not None
    return view, dict(session.state)


def stored_of(services: Services, view: SessionView, sid: str) -> StoredDataset:
    assert view.dataset_id is not None
    stored = services.datasets.get(view.dataset_id, sid)
    assert stored is not None
    return stored


def rendered_version(*, language: str) -> CodeVersion:
    """A shipped version whose plot text is in `language`."""
    result = PlotResult(status="ok", attempts=1, artifacts=["plot.py"])
    return CodeVersion(
        number=1,
        working="w",
        run_form="r",
        export="e",
        data_csv="a\n1\n",
        render_id="r1",
        result=result,
        language=language,
    )


def frame(stored: StoredDataset) -> pd.DataFrame:
    """The table as the plot code's loader reads `data.csv` (`code/loader.py`: dtypes, dates, round-trip floats)."""
    return pd.read_csv(
        io.StringIO(stored.csv),
        dtype=pandas_dtypes(stored.column_dtypes),
        parse_dates=stored.parse_dates,
        float_precision="round_trip",
    )


async def test_a_copy_is_the_confirmed_version_byte_for_byte(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    source = await open_session(client)
    pasted = await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["confirmed"] is True and body["complete"] is True and body["missing_roles"] == []
    assert body["version"] == 1 and body["copied_from"] == 1
    for key in ("preview", "profile", "bindings", "warnings", "context_lines", "roles", "file_name"):
        assert body[key] == pasted[key], key
    assert body["language"] == {"language": "en", "source": "default"}

    origin, _ = await view_of(runtime, source)
    copied_view, state = await view_of(runtime, target)
    original, copied = stored_of(services, origin, source), stored_of(services, copied_view, target)
    # Every stored field is the source's: values, dtypes, column order, notes, file name, provenance.
    assert asdict(copied) == {
        **asdict(original),
        "dataset_id": copied.dataset_id,
        "session_id": target,
        "created_at": copied.created_at,
        "last_used_at": copied.last_used_at,
    }
    assert copied.dataset_id != original.dataset_id
    assert copied.csv == original.csv and "0.12345678901234568" in copied.csv
    plotted = frame(copied)
    pd.testing.assert_frame_equal(plotted, frame(original), check_exact=True)
    assert list(plotted.columns) == ["Study Hours", "Exam Score", "Attempts", "Student"]
    assert plotted["Study Hours"][0] == 0.12345678901234568
    assert math.isnan(plotted["Exam Score"][1])
    assert str(plotted["Attempts"].dtype) == "Int64" and plotted["Attempts"].isna().tolist() == [False, True, False]
    assert plotted["Student"].tolist() == ["Zoë 🌍", CELL_CANARY, "日本語 “quoted”"]
    # The bindings and their confirmation came along; the copy is the target's version 1, from the source's 1.
    assert copied_view.bindings == origin.bindings and copied_view.data_confirmed
    assert copied_view.dataset_version == 1 and copied_view.dataset_history == []
    assert state[DATASET_COPIED_FROM] == 1
    # The source is untouched.
    after, _ = await view_of(runtime, source)
    assert after.dataset_id == original.dataset_id and after.data_confirmed


async def test_a_computed_version_is_copied_with_its_code_and_number(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    """Data the assistant computed or changed has no paste to post again: the copy takes the version itself."""
    source = await open_session(client)
    await paste(client, source, confirm=False)
    view, _ = await view_of(runtime, source)
    computed = parse_dataset(
        "Study Hours,Exam Score\n-3.141592653589793,-1.2246467991473532e-16\n0.5,0.479425538604203\n"
    )
    version = push_version(
        services.datasets,
        source,
        view,
        computed,
        view.snapshot,
        rebind=True,
        code="x = np.linspace(-np.pi, np.pi, 2)",
        source="computed by run_data_code",
    )
    await runtime.write_state(await runtime.session(USER, source), version.delta)
    assert (await client.post(f"/v1/sessions/{source}/dataset/confirm", headers=headers())).status_code == 200
    target = await open_session(client, fanout=True)

    response = await copy(client, target, source)

    assert response.status_code == 200, response.text
    assert response.json()["copied_from"] == 2 and response.json()["code"] == "x = np.linspace(-np.pi, np.pi, 2)"
    copied_view, state = await view_of(runtime, target)
    copied = stored_of(services, copied_view, target)
    assert copied.csv == version.stored.csv and "-1.2246467991473532e-16" in copied.csv
    assert (copied.code, copied.source, copied.file_name) == (version.stored.code, version.stored.source, None)
    assert state[DATASET_COPIED_FROM] == 2 and state[DATASET_VERSION] == 1
    assert copied_view.data_confirmed


async def test_the_bindings_and_the_session_language_come_along(client: httpx.AsyncClient, runtime: Runtime) -> None:
    source = await open_session(client)
    await paste(client, source, confirm=False)
    swapped = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
    assert (await client.put(f"/v1/sessions/{source}/bindings", headers=headers(), json=swapped)).status_code == 200
    assert (await client.put(f"/v1/sessions/{source}/language", headers=headers(), json={"language": "de"})).is_success
    assert (await client.post(f"/v1/sessions/{source}/dataset/confirm", headers=headers())).status_code == 200
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert response.status_code == 200, response.text
    assert response.json()["bindings"] == swapped
    assert response.json()["language"] == {"language": "de", "source": "chosen"}
    copied_view, state = await view_of(runtime, target)
    assert [binding.model_dump() for binding in copied_view.bindings] == swapped and copied_view.data_confirmed
    assert (state[LANGUAGE], state[LANGUAGE_SOURCE], state[PLOT_LANGUAGE]) == ("de", "chosen", "de")


async def test_the_page_plots_language_comes_along_when_the_replies_moved_on(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    """The page's plot is German while its replies became English (owner decision of 2026-11-01): the fan-out plots
    in German, the language the page's plot shows."""
    source = await open_session(client)
    await paste(client, source)
    session = await runtime.session(USER, source)
    await runtime.write_state(session, language_delta("en", "detected"))
    services.versions.add(source, rendered_version(language="de"))
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert response.status_code == 200, response.text
    assert response.json()["language"] == {"language": "en", "source": "detected"}
    copied_view, state = await view_of(runtime, target)
    assert (state[LANGUAGE], state[PLOT_LANGUAGE]) == ("en", "de")
    assert plot_language(copied_view, services.versions.latest_language(target)) == "de"


async def test_the_copy_plots_without_a_confirmation_of_its_own(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", default_script())  # its adapter plan edits the matplotlib catalogue code
    source = await open_session(client, library="seaborn")
    await paste(client, source)
    target = await open_session(client, fanout=True)
    assert (await copy(client, target, source)).status_code == 200

    turn = await client.post(f"/v1/sessions/{target}/messages", headers=headers(), json={"action": "create_plot"})

    assert turn.status_code == 200, turn.text
    plot = next(json.loads(block.split("data: ", 1)[1]) for block in turn.text.split("\n\n") if "event: plot" in block)
    assert plot["status"] == "ok", plot


async def test_another_users_session_is_never_found(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    """Both sessions are looked up under the caller's id: no copy crosses users, in either direction."""
    theirs = await open_session(client, user=OTHER)
    await paste(client, theirs, user=OTHER)
    mine = await open_session(client, library="seaborn", fanout=True)
    stored = len(services.datasets)

    response = await copy(client, mine, theirs)
    assert (response.status_code, response.json()) == (404, {"detail": "session_expired"})

    source = await open_session(client)
    await paste(client, source)
    their_target = await open_session(client, user=OTHER, library="seaborn", fanout=True)
    for attempt in (await copy(client, their_target, source), await copy(client, their_target, source, user=OTHER)):
        assert (attempt.status_code, attempt.json()) == (404, {"detail": "session_expired"})

    assert len(services.datasets) == stored + 1  # only my own paste: nothing was copied
    target_view, _ = await view_of(runtime, mine)
    their_view, _ = await view_of(runtime, their_target, user=OTHER)
    assert target_view.dataset_id is None and their_view.dataset_id is None


async def test_an_unconfirmed_source_is_refused(client: httpx.AsyncClient, runtime: Runtime) -> None:
    source = await open_session(client)
    await paste(client, source, confirm=False)
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)
    assert (response.status_code, response.json()) == (422, {"detail": "unconfirmed"})

    # A binding change after the confirmation leaves the data unconfirmed again.
    assert (await client.post(f"/v1/sessions/{source}/dataset/confirm", headers=headers())).status_code == 200
    swapped = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
    assert (await client.put(f"/v1/sessions/{source}/bindings", headers=headers(), json=swapped)).status_code == 200
    response = await copy(client, target, source)
    assert (response.status_code, response.json()) == (422, {"detail": "unconfirmed"})
    target_view, _ = await view_of(runtime, target)
    assert target_view.dataset_id is None


async def test_a_source_without_data_is_refused(client: httpx.AsyncClient) -> None:
    source = await open_session(client)
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert (response.status_code, response.json()) == (422, {"detail": "no_dataset"})


async def test_a_target_with_data_is_refused(client: httpx.AsyncClient, runtime: Runtime, services: Services) -> None:
    source = await open_session(client)
    await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)
    assert (await copy(client, target, source)).status_code == 200
    first, _ = await view_of(runtime, target)
    stored = len(services.datasets)

    again = await copy(client, target, source)
    assert (again.status_code, again.json()) == (409, {"detail": "has_dataset"})

    pasted = await open_session(client, fanout=True)
    await paste(client, pasted, confirm=False)
    response = await copy(client, pasted, source)
    assert (response.status_code, response.json()) == (409, {"detail": "has_dataset"})
    assert len(services.datasets) == stored + 1  # only the paste
    after, _ = await view_of(runtime, target)
    assert after.dataset_id == first.dataset_id


async def test_only_a_fanout_session_of_the_same_spec_takes_a_copy(client: httpx.AsyncClient) -> None:
    source = await open_session(client)
    await paste(client, source)
    plain = await open_session(client, library="seaborn")
    other_spec = await open_session(client, library="seaborn", spec_id="bar-basic", fanout=True)

    for target in (plain, other_spec, source):
        response = await copy(client, target, source)
        assert (response.status_code, response.json()) == (422, {"detail": "invalid"}), target


async def test_a_busy_session_refuses_the_copy(client: httpx.AsyncClient, runtime: Runtime) -> None:
    """A paste in flight in the source is about to change its data; one in the target would race the copy."""
    source = await open_session(client)
    await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)

    for busy in (source, target):
        runtime.pasting.add(busy)
        response = await copy(client, target, source)
        runtime.pasting.discard(busy)
        assert (response.status_code, response.json()) == (409, {"detail": "run_active"})
    assert (await copy(client, target, source)).status_code == 200


@pytest.mark.parametrize(
    ("body", "status"), [({}, 422), ({"from_session": "a/b"}, 422), ({"from_session": "s", "extra": 1}, 422)]
)
async def test_the_body_is_one_session_id(client: httpx.AsyncClient, body: dict[str, Any], status: int) -> None:
    target = await open_session(client, library="seaborn", fanout=True)

    response = await client.post(f"/v1/sessions/{target}/dataset/copy", headers=headers(), json=body)

    assert response.status_code == status


@pytest.mark.parametrize(("cap", "code"), [("COPIES_PER_MINUTE", "rate_limited"), ("COPIES_PER_DAY", "daily_limit")])
async def test_copies_are_counted_per_user(
    client: httpx.AsyncClient, runtime: Runtime, monkeypatch: pytest.MonkeyPatch, cap: str, code: str
) -> None:
    """No parse and no model call, but each copy takes the dataset's size in the store again: a cap of its own."""
    monkeypatch.setattr(ledger, cap, 1)
    source = await open_session(client)
    await paste(client, source)
    first = await open_session(client, library="seaborn", fanout=True)
    second = await open_session(client, fanout=True)

    assert (await copy(client, first, source)).status_code == 200
    response = await copy(client, second, source)

    assert (response.status_code, response.json()) == (429, {"detail": code})
    refused, _ = await view_of(runtime, second)
    assert refused.dataset_id is None


async def test_a_full_store_refuses_the_copy_and_keeps_nothing(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    source = await open_session(client)
    await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)
    services.datasets.max_bytes = services.datasets.used_bytes  # no room for one more byte
    stored = len(services.datasets)

    response = await copy(client, target, source)

    assert (response.status_code, response.json()) == (503, {"detail": "capacity"})
    assert len(services.datasets) == stored
    target_view, state = await view_of(runtime, target)
    assert target_view.dataset_id is None and DATASET_COPIED_FROM not in state


async def test_bindings_the_target_refuses_are_never_copied(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    """Defence in depth: the bindings must hold for the target's roles too. Here the source's state holds a text
    column on the numeric `x`, confirmed as it is, which no route of the service would store."""
    source = await open_session(client)
    await paste(client, source)
    view, _ = await view_of(runtime, source)
    bad = [{"role": "x", "column": "Student"}, {"role": "y", "column": "Exam Score"}]
    assert view.dataset_id is not None
    fingerprint = confirmation_fingerprint(view.dataset_id, [Binding.model_validate(item) for item in bad])
    await runtime.write_state(await runtime.session(USER, source), {BINDINGS: bad, CONFIRMED: fingerprint})
    target = await open_session(client, library="seaborn", fanout=True)
    stored = len(services.datasets)

    response = await copy(client, target, source)

    assert (response.status_code, response.json()) == (422, {"detail": "invalid"})
    assert len(services.datasets) == stored


async def test_a_copy_logs_counts_and_no_data(client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """One content-free attribution line; no `data_input` telemetry line, since no input reached the dataset route."""
    source = await open_session(client)
    await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)
    caplog.set_level(logging.INFO)
    caplog.clear()  # the paste's own lines

    assert (await copy(client, target, source)).status_code == 200

    records = [record for record in caplog.records if record.name in (ATTRIBUTION_LOGGER, telemetry.TELEMETRY_LOGGER)]
    lines = [json.loads(record.getMessage()) for record in records]
    (line,) = [line for line in lines if line.get("hook") == "dataset_copy"]
    assert {key: line[key] for key in ("outcome", "rows", "columns", "version")} == {
        "outcome": "ok",
        "rows": 3,
        "columns": 4,
        "version": 1,
    }
    assert line["from_session"] != line["session"] and source not in json.dumps(line)
    assert not [line for line in lines if line.get("event") == "data_input"]
    for record in caplog.records:
        message = record.getMessage()
        assert CELL_CANARY not in message and FILE_NAME not in message and "Zoë" not in message


async def test_the_bundle_names_the_version_the_data_was_copied_from(
    client: httpx.AsyncClient, runtime: Runtime
) -> None:
    source = await open_session(client)
    await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)
    assert (await copy(client, target, source)).status_code == 200

    copied = (await client.get(f"/v1/sessions/{target}/bundle", headers=headers())).json()
    own = (await client.get(f"/v1/sessions/{source}/bundle", headers=headers())).json()

    assert copied["session"]["dataset_copied_from"] == 1
    assert "dataset_copied_from" not in own["session"]
    session = await runtime.session_service.get_session(app_name=APP_NAME, user_id=USER, session_id=target)
    assert session is not None and session.state[DATASET_COPIED_FROM] == 1
