"""The plot draws every row: the repeated-key warning on the binding answers and in the session block, and the
server's line for rows without a value to draw in the shipped plot's "what changed" (`data/fidelity.py`).

Owner decision of 2026-11-08, after the persona round of 2026-11-06, where a line chart of 27 measurements over 9
lengths came out as 9 averaged points and nobody said so. The sessions are opened through the real `/v1` routes;
every table is invented.
"""

import json
import re
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest

from agents.anyplot.agent import REPEATED_KEY_LINE, session_context
from agents.anyplot.data.fidelity import LEFT_OUT_HEAD
from agents.anyplot.services import Services
from agents.anyplot.tools.session import set_bindings
from agents.main import Runtime, app, get_runtime

from .conftest import CASES
from .fakes import SCATTER_PLAN, default_script
from .test_from_version import context_for
from .test_paste_conversions import open_spec, paste
from .test_service_flow import HEADERS, create_plot, permissive_queue


LENGTHS = "Length,Reading\n" + "".join(f"{10 + 5 * (i % 9)},{20 + (i * 7) % 13}.5\n" for i in range(27))
"""27 invented readings over 9 lengths, three per length."""
WARNING = (
    "x: column 'Length' holds 9 values in 27 rows; the plot draws one value per x, so rows with the same x need an "
    "aggregate first"
)


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=permissive_queue())
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


def fenced_lines(block: str, tag: str) -> list[list[str]]:
    return [match.splitlines() for match in re.findall(rf"<{tag}>\n(.*?)\n</{tag}>", block, re.DOTALL)]


class TestRepeatedKey:
    async def test_the_session_block_names_the_key_and_its_counts(self, client: httpx.AsyncClient) -> None:
        sid = await open_spec(client, "line-styled")
        await paste(client, sid, LENGTHS)
        context = await context_for(client, sid, "inv-rk-1")

        block = await session_context(context)  # type: ignore[arg-type]

        line = REPEATED_KEY_LINE.format(fact="x has 9 values in 27 rows", per="x")
        assert line in block.splitlines()
        assert "Length" not in line  # the column names stay inside the fenced warnings
        assert [WARNING] in fenced_lines(block, "user_data")

    async def test_the_bindings_route_and_set_bindings_answer_the_warning(self, client: httpx.AsyncClient) -> None:
        sid = await open_spec(client, "line-styled")
        await paste(client, sid, LENGTHS)

        response = await client.put(
            f"/v1/sessions/{sid}/bindings",
            headers=HEADERS,
            json=[{"role": "x", "column": "Length"}, {"role": "y_1", "column": "Reading"}],
        )
        assert response.status_code == 200, response.text
        assert (response.json()["complete"], response.json()["warnings"]) == (True, [WARNING])

        context = await context_for(client, sid, "inv-rk-2")
        result = await set_bindings(
            [{"role": "x", "column": "Length"}, {"role": "y_1", "column": "Reading"}],
            context,  # type: ignore[arg-type]
        )
        assert result["status"] == "ok" and result["complete"] is True
        assert [WARNING] in [json.loads(lines[0]) for lines in fenced_lines(result["warnings"], "user_data")]

    async def test_unique_keys_add_no_line(self, client: httpx.AsyncClient) -> None:
        sid = await open_spec(client, "bar-basic")
        await paste(client, sid, "Fruit,Sold\nApples,12\nPears,7\nPlums,9\nCherries,15\n")
        context = await context_for(client, sid, "inv-rk-3")

        block = await session_context(context)  # type: ignore[arg-type]

        assert "- Repeated key:" not in block and "Binding warnings" not in block


class TestRowsWithoutAValue:
    async def test_the_shipped_plot_counts_the_rows_it_cannot_draw_first_and_stays_ok(
        self, client: httpx.AsyncClient, swap_models
    ) -> None:
        """Two invented students without an exam score: the run's "what changed" says so with the count, first, and
        the status stays the render's (the server's notes never become residual ones)."""
        swap_models("gemini", default_script())
        header, *rows = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text().splitlines()
        for index in (3, 7):  # `Student,Study Hours,Exam Score`: the score of two rows left empty
            rows[index] = rows[index].rsplit(",", 1)[0] + ","
        sid = await open_spec(client, "scatter-basic")
        await paste(client, sid, "\n".join([header, *rows]) + "\n")
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200, confirmed.text

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["residual_defects"] == []
        assert plot["changes"] == [f"{LEFT_OUT_HEAD}2 rows without y ('Exam Score')", *SCATTER_PLAN["changes"]]

    async def test_complete_rows_add_no_line(self, client: httpx.AsyncClient, swap_models) -> None:
        swap_models("gemini", default_script())
        sid = await open_spec(client, "scatter-basic")
        await paste(client, sid, (CASES / "scatter-basic-matplotlib" / "data.csv").read_text())
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200, confirmed.text

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["changes"] == SCATTER_PLAN["changes"]
