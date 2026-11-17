"""The plot memory and the library switch that carries it (owner decisions of 2026-11-02).

Pure checks of `memory.py` and `switch.py` first, then whole turns through `/v1` with scripted
models: a change hands its lasting decisions over with the run and the memory keeps them only once
the plot ships; a switch keeps the memory and writes the carry, which the first run in the new
library takes from that library's catalogue code; `.start_over()` stays fresh and starts the memory
over; switching back counts the decisions the older plot misses; the page lists and removes entries.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Iterator, Sequence
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from agents.anyplot import telemetry
from agents.anyplot.grounding import DrawnTexts, drawn_texts
from agents.anyplot.memory import (
    MAX_ENTRIES,
    MEMORY,
    MEMORY_SEQ,
    MemoryEntry,
    MemoryRefused,
    Planned,
    decision_lines,
    expected_texts,
    forget,
    kind_counts,
    memory_delta,
    memory_written,
    newer_than,
    next_seq,
    not_drawn,
    plan,
    read_memory,
    remember,
    replace_drawn,
)
from agents.anyplot.opening import assess
from agents.anyplot.pipeline import (
    DECISIONS_HEADING,
    EARLIER_REQUESTS_HEADING,
    EXPECTED_HEADING,
    Candidate,
    Run,
    memory_ids,
    settle_memory,
)
from agents.anyplot.render import harness
from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome
from agents.anyplot.schemas import AdaptPlan, PipelineArgs, PlotResult, RememberItem
from agents.anyplot.services import CodeVersion, Services, get_services
from agents.anyplot.session_state import PENDING_EXPECTED_TEXTS, PENDING_REMEMBER, PENDING_REQUEST, PLOT_LANGUAGE
from agents.anyplot.settings import get_settings
from agents.anyplot.switch import CARRY, Carry, SourcePlot, Target, carry_for, read_carry, summary
from agents.main import ActiveRun, Runtime, app, get_runtime

from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_service_flow import (
    HEADERS,
    USER,
    _session_state,
    adapter_inputs,
    create_plot,
    open_session,
    parse_sse,
    permissive_queue,
    snapshot_body,
)


LINE = RememberItem(kind="reference_line", text="horizontal reference line at y = 7")
FORMULA = RememberItem(kind="annotation", text="annotation top left: the formula $y = ax^2 + b$ typeset as LaTeX")
STARS = RememberItem(kind="marker", text="outliers as red star markers")
LABEL = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (h)'", expected_text="Zeit (h)")
LIMITS = RememberItem(kind="limits", target="x", text="x limits 0 to 100")
OWNER_EXAMPLES = [LINE, FORMULA, STARS, LABEL, LIMITS]
"""The owner's own examples of tuning the memory must hold (2026-11-02)."""


def entries(*items: RememberItem, turn: int = 1) -> list[MemoryEntry]:
    return plan([], items, seq=1, turn=turn).entries


# --- memory.py ------------------------------------------------------------------------------


class TestRemember:
    def test_a_single_valued_kind_replaces_the_entry_of_its_kind_and_target(self) -> None:
        before = entries(LABEL, RememberItem(kind="axis_label", target="y", text="y-axis label: 'Wert'"))
        relabelled = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (min)'")

        after = remember(before, relabelled, seq=3, turn=2)

        assert [(entry.id, entry.target, entry.text) for entry in after] == [
            ("m2", "y", "y-axis label: 'Wert'"),  # another target stays
            ("m3", "x", "x-axis label: 'Zeit (min)'"),
        ]

    def test_a_multi_valued_kind_adds_beside_the_others(self) -> None:
        second = RememberItem(kind="reference_line", text="vertical reference line at x = 50")

        after = remember(entries(LINE), second, seq=2, turn=2)

        assert [entry.text for entry in after] == [LINE.text, second.text]

    def test_a_correction_replaces_the_entry_it_names(self) -> None:
        """A second reference line is added beside the first; one that `replaces` it takes its place (Copilot on
        #12520)."""
        moved = RememberItem(kind="reference_line", text="horizontal reference line at y = 8", replaces="m1")

        after = remember(entries(LINE, STARS), moved, seq=3, turn=2)

        assert [(entry.id, entry.text) for entry in after] == [("m2", STARS.text), ("m3", moved.text)]
        assert remember(entries(STARS), moved, seq=2, turn=2)[-1].text == moved.text  # m1 gone already: just added
        with pytest.raises(ValueError):
            RememberItem(kind="marker", text="x", replaces="title")

    def test_the_same_decision_twice_is_one_entry(self) -> None:
        once = entries(LINE)

        assert remember(once, LINE, seq=2, turn=3) == once
        assert plan(once, [LINE], seq=2, turn=3).seq == 2  # the id counter does not move either

    @pytest.mark.parametrize("held", [LINE, FORMULA, STARS])
    def test_a_multi_valued_decision_in_other_case_spacing_or_closing_mark_is_one_entry(
        self, held: RememberItem
    ) -> None:
        once = entries(held)
        reworded = held.model_copy(update={"text": "  " + held.text.upper().replace(" ", "  ") + "."})

        assert remember(once, reworded, seq=2, turn=3) == once
        assert plan(once, [reworded], seq=2, turn=3).seq == 2

    def test_other_words_for_a_multi_valued_kind_still_add_beside(self) -> None:
        """Code sets aside only case, spacing and a closing mark; a paraphrase is the root's to leave out (root.md)."""
        reworded = RememberItem(kind="marker", text="outliers drawn as red stars")

        after = remember(entries(STARS), reworded, seq=2, turn=3)

        assert [entry.text for entry in after] == [STARS.text, reworded.text]

    def test_a_single_valued_decision_reworded_alike_stays_and_a_new_one_replaces(self) -> None:
        once = entries(LABEL)
        alike = LABEL.model_copy(update={"text": "X-axis label: 'Zeit (h)'!"})
        assert remember(once, alike, seq=2, turn=3) == once

        renamed = RememberItem(
            kind="axis_label", target="x", text="x-axis label: 'Zeit (min)'", expected_text="Zeit (min)"
        )
        assert [(entry.id, entry.text) for entry in remember(once, renamed, seq=2, turn=3)] == [("m2", renamed.text)]

    def test_a_shown_text_in_other_capitals_is_another_decision(self) -> None:
        """The text the plot shows is the user's verbatim: `Umsatz` and `UMSATZ` are two titles."""
        title = RememberItem(kind="title", text="title: 'Umsatz'", expected_text="Umsatz")
        shouted = RememberItem(kind="title", text="title: 'UMSATZ'", expected_text="UMSATZ")

        after = remember(entries(title), shouted, seq=2, turn=3)

        assert [(entry.id, entry.expect) for entry in after] == [("m2", "UMSATZ")]

    def test_the_caps_refuse_rather_than_drop_an_old_entry(self) -> None:
        full = plan([], [RememberItem(kind="other", text=f"decision {n}") for n in range(MAX_ENTRIES)], seq=1, turn=1)
        assert len(full.entries) == MAX_ENTRIES and full.refused == 0

        with pytest.raises(MemoryRefused) as refused:
            remember(full.entries, LINE, seq=full.seq, turn=2)
        assert refused.value.code == "memory_full"
        long = [RememberItem(kind="other", text=f"{n:02d}" + "x" * 198) for n in range(16)]  # 3,200 characters
        planned = plan([], long, seq=1, turn=1)
        assert (len(planned.entries), planned.refused) == (15, 1)

    def test_forget_removes_by_id_and_refuses_an_unknown_one(self) -> None:
        held = entries(LINE, STARS)

        assert [entry.id for entry in forget(held, "m1")] == ["m2"]
        with pytest.raises(MemoryRefused):
            forget(held, "m9")

    def test_a_text_is_one_line_without_control_characters(self) -> None:
        assert RememberItem(kind="title", text="  Title:\n'A'  ").text == "Title: 'A'"
        with pytest.raises(ValueError):
            RememberItem(kind="title", text="bad\x00text")
        with pytest.raises(ValueError):
            RememberItem.model_validate({"kind": "unknown", "text": "a"})


class TestReadMemory:
    def test_a_corrupt_item_never_reaches_a_prompt(self) -> None:
        good = entries(LINE)[0].model_dump()
        state = {MEMORY: [good, {"id": "m2", "kind": "title"}, "text", dict(good), {**good, "id": "x"}]}

        assert [entry.id for entry in read_memory(state)] == ["m1"]  # the second copy of m1 is dropped too

    def test_ids_are_never_reused(self) -> None:
        held = entries(LINE, STARS)

        assert next_seq({MEMORY_SEQ: 7}, held) == 7
        assert next_seq({MEMORY_SEQ: 1}, held) == 3  # never below one past the highest id in use
        assert next_seq({}, []) == 1


class TestForgetTool:
    """`forget` refuses before it writes: no session, a run in flight, a malformed or unknown id."""

    @staticmethod
    def context(state: dict[str, Any], invocation_id: str) -> Any:
        from types import SimpleNamespace

        return SimpleNamespace(state=state, invocation_id=invocation_id, session=SimpleNamespace(id="s1"))

    @staticmethod
    def opened(**extra: Any) -> dict[str, Any]:
        from agents.anyplot.dev_fixture import snapshot_from_repo
        from agents.anyplot.session_state import initial_state

        state = initial_state(
            spec_id="scatter-basic",
            library="matplotlib",
            locale="en",
            snapshot=snapshot_from_repo("scatter-basic", "matplotlib"),
            normalised="x = 1",
            readiness={},
        )
        return {**state, **extra}

    async def test_each_refusal_leaves_the_memory_as_it_was(self) -> None:
        from agents.anyplot.plugins.ledger import ledger_for
        from agents.anyplot.tools.session import forget as forget_tool

        held = memory_delta(entries(LINE, STARS), 3)
        assert await forget_tool("m1", self.context({}, "inv-forget-1")) == {
            "status": "error",
            "code": "session_not_open",
        }
        state = self.opened(**held)
        for entry_id, code in (("title", "invalid_arguments"), ("m9", "unknown_entry")):
            assert await forget_tool(entry_id, self.context(state, "inv-forget-2")) == {"status": "error", "code": code}
        ledger_for("inv-forget-3").pipeline_active = True
        try:
            refused = await forget_tool("m1", self.context(state, "inv-forget-3"))
        finally:
            ledger_for("inv-forget-3").pipeline_active = False
        assert refused == {"status": "error", "code": "run_active"}
        assert state[MEMORY] == held[MEMORY]

        assert await forget_tool("m1", self.context(state, "inv-forget-4")) == {"status": "ok", "entries": 1}
        assert [entry.id for entry in read_memory(state)] == ["m2"]


def test_stored_values_that_fail_their_checks_are_dropped() -> None:
    from agents.anyplot.pipeline import merged_remember, take_carried_texts

    assert merged_remember([{"kind": "title"}, LINE.model_dump(), "x"], [STARS]) == [LINE, STARS]
    assert merged_remember("not a list", []) == []
    carry = Carry(source=MATPLOTLIB, target=SEABORN)
    assert take_carried_texts(PipelineArgs(change_request="c"), carry) == PipelineArgs(change_request="c")
    assert read_carry({CARRY: "text"}, SEABORN.pair()) is None
    assert read_carry({CARRY: {"source": {"spec_id": "x"}}}, SEABORN.pair()) is None
    with pytest.raises(ValueError):
        Target(spec_id="scatter-basic", library="excel")
    with pytest.raises(ValueError):
        RememberItem(kind="title", text=" \n ")  # nothing left once the whitespace is collapsed


class TestPlotTargetSynonym:
    """The target `plot` is the same as none, for every kind: a plot-wide entry has one replace key."""

    TITLE = RememberItem(kind="title", text="title: 'Harbour arrivals'", expected_text="Harbour arrivals")

    def test_a_title_filed_with_plot_replaces_one_filed_without(self) -> None:
        moved = RememberItem(
            kind="title", target="plot", text="title: 'Ferry traffic 2031'", expected_text="Ferry traffic 2031"
        )

        after = remember(entries(self.TITLE, LINE), moved, seq=3, turn=2)

        assert [(entry.id, entry.kind, entry.target) for entry in after] == [
            ("m2", "reference_line", None),
            ("m3", "title", "plot"),
        ]
        assert [entry.id for entry in remember(after, self.TITLE, seq=4, turn=3)] == ["m2", "m4"]  # and back

    def test_the_same_decision_under_the_synonym_is_no_new_one(self) -> None:
        once = entries(self.TITLE)
        filed = self.TITLE.model_copy(update={"target": "plot"})

        assert remember(once, filed, seq=2, turn=2) == once
        line = entries(LINE)
        assert remember(line, LINE.model_copy(update={"target": "plot"}), seq=2, turn=2) == line

    def test_a_legend_title_stays_apart_from_the_plot_title(self) -> None:
        legend = RememberItem(kind="title", target="color", text="legend title: 'Vessel class'")

        after = remember(entries(self.TITLE), legend, seq=2, turn=2)

        assert [(entry.id, entry.target) for entry in after] == [("m1", None), ("m2", "color")]

    def test_reading_keeps_the_newest_entry_per_key(self) -> None:
        """A memory written before the synonym was folded holds both titles; the newer one stands."""
        old = entries(self.TITLE)[0]
        newer = MemoryEntry(id="m3", kind="title", target="plot", text="title: 'Pier 4'", expect="Pier 4", turn=2)
        legend = MemoryEntry(id="m4", kind="title", target="color", text="legend title: 'Vessel class'", turn=2)
        lines = [
            MemoryEntry(id="m2", kind="reference_line", text=LINE.text, turn=1),
            MemoryEntry(id="m5", kind="reference_line", target="plot", text="vertical line at x = 3", turn=2),
        ]
        stored = [old, lines[0], newer, legend, lines[1]]

        held = read_memory(memory_delta(stored, 6))

        assert [entry.id for entry in held] == ["m2", "m3", "m4", "m5"]  # several lines stand side by side


def drawn(*labels: tuple[str, str], complete: bool = True) -> DrawnTexts:
    probe: dict[str, Any] = {"labels": [{"kind": kind, "text": text} for kind, text in labels]}
    if not complete:
        probe["labels_truncated"] = True
    texts = drawn_texts(probe)
    assert texts is not None
    return texts


HARBOUR_TITLE = RememberItem(kind="title", text="bold title: 'Harbour arrivals'", expected_text="Harbour arrivals")
ENERGY_LABEL = RememberItem(
    kind="axis_label", target="y", text="y-axis label: 'Energy use per day'", expected_text="Energy use per day"
)


def standing(*items: RememberItem) -> Planned:
    """A memory of `items` written in turn 1, as a run of turn 2 plans it before its own items (none here)."""
    held = entries(*items)
    return plan(held, [], seq=len(held) + 1, turn=2)


class TestReplaceDrawn:
    """After a shipped run, a standing title or axis label the render replaced with a text the user wrote is replaced
    in the memory; nothing else changes, and nothing is ever created."""

    def test_a_title_the_render_replaced_replaces_the_entry(self) -> None:
        before = standing(HARBOUR_TITLE, LINE)

        after = replace_drawn(
            before, ["Ferry traffic 2031"], drawn(("title", "Ferry traffic 2031")), standing_below=3, turn=2
        )

        assert [(entry.id, entry.kind, entry.target, entry.expect, entry.turn) for entry in after.entries] == [
            ("m2", "reference_line", None, None, 1),
            ("m3", "title", None, "Ferry traffic 2031", 2),
        ]
        assert after.entries[-1].text == "bold title: 'Ferry traffic 2031'"  # the rest of the decision stands
        assert (after.seq, after.refused) == (4, 0)

    def test_an_instruction_without_its_text_once_takes_the_plain_form(self) -> None:
        loose = RememberItem(kind="axis_label", target="x", text="label the x axis as asked", expected_text="Time")

        after = replace_drawn(
            standing(loose), ["Hour of day"], drawn(("x axis label", "Hour of day")), standing_below=2, turn=2
        )

        assert [(entry.text, entry.expect) for entry in after.entries] == [
            ("x-axis label: 'Hour of day'", "Hour of day")
        ]

    def test_an_instruction_that_points_into_its_old_text_takes_the_plain_form(self) -> None:
        """The rest of the instruction names a word of the old title, which the new title need not have."""
        tide = RememberItem(
            kind="title", text="title: 'Tide table 2030' with 2030 in bold", expected_text="Tide table 2030"
        )

        after = replace_drawn(
            standing(tide), ["Moon phases 2031"], drawn(("title", "Moon phases 2031")), standing_below=2, turn=2
        )

        assert [(entry.text, entry.expect) for entry in after.entries] == [
            ("title: 'Moon phases 2031'", "Moon phases 2031")
        ]

    def test_the_whole_text_is_compared_as_grounding_reads_it(self) -> None:
        after = replace_drawn(
            standing(ENERGY_LABEL),
            ["Daily load “kWh”"],
            drawn(("y axis label", "DAILY  LOAD kWh")),  # case, spacing and quotes aside
            standing_below=2,
            turn=2,
        )

        assert [entry.expect for entry in after.entries] == ["Daily load “kWh”"]

    def test_a_unit_drawn_inside_a_longer_label_leaves_the_entry_alone(self) -> None:
        """The user's `kWh` stands in the new label, which is no label the user wrote out whole."""
        before = standing(ENERGY_LABEL)

        after = replace_drawn(before, ["kWh"], drawn(("y axis label", "Daily load (kWh)")), standing_below=2, turn=2)

        assert after == before

    def test_a_number_format_is_never_a_whole_label(self) -> None:
        before = standing(ENERGY_LABEL)

        after = replace_drawn(before, ["12,5 %"], drawn(("y axis label", "12,5 %")), standing_below=2, turn=2)

        assert after == before

    def test_an_old_text_the_render_still_draws_as_its_part_stays(self) -> None:
        """The old title is still the whole title: a text of the user's drawn elsewhere replaces nothing."""
        before = standing(HARBOUR_TITLE)
        render = drawn(("title", "Harbour arrivals"), ("annotation", "Ferry traffic 2031"))

        assert replace_drawn(before, ["Ferry traffic 2031"], render, standing_below=2, turn=2) == before

    def test_an_old_text_drawn_whole_outside_its_part_stays(self) -> None:
        """The old title drawn whole as another text (a free text above the axes, a legend entry, an annotation) is
        still drawn: the user's text that fills the title role then is another part, such as a subtitle."""
        before = standing(HARBOUR_TITLE)

        for kind in ("text", "legend text", "annotation"):
            render = drawn((kind, "HARBOUR  arrivals"), ("title", "Evening runs"))  # case and spacing aside
            assert replace_drawn(before, ["Evening runs"], render, standing_below=2, turn=2) == before

    def test_a_title_the_user_lengthened_replaces_the_entry(self) -> None:
        """The old text stands inside the new title, which is no longer the old title: the user's whole one replaces
        it, so a later change never draws the shorter title again."""
        before = standing(HARBOUR_TITLE)
        render = drawn(("title", "Harbour arrivals 2031"))

        after = replace_drawn(before, ["Harbour arrivals 2031"], render, standing_below=2, turn=2)

        assert [(entry.id, entry.text, entry.expect) for entry in after.entries] == [
            ("m2", "bold title: 'Harbour arrivals 2031'", "Harbour arrivals 2031")
        ]
        # A title the plot lengthened by itself is no text the user wrote: the entry stays.
        assert replace_drawn(before, ["Ferry traffic 2031"], render, standing_below=2, turn=2) == before

    def test_a_number_format_entry_is_never_replaced(self) -> None:
        """A number-format example stands for tick labels, never for a part's whole text, so a label the user wrote
        never takes its place, whether the render draws the format or another decimal mark."""
        share = RememberItem(kind="axis_label", target="y", text="y-axis ticks as '12,5 %'", expected_text="12,5 %")
        before = standing(share)

        for tick in ("87,5 %", "87.5 %"):
            render = drawn(("y axis label", "Share of trips"), ("y tick label", tick))
            assert replace_drawn(before, ["Share of trips"], render, standing_below=2, turn=2) == before

    def test_nothing_changes_without_a_complete_report(self) -> None:
        before = standing(HARBOUR_TITLE)
        texts = ["Ferry traffic 2031"]

        assert replace_drawn(before, texts, None, standing_below=2, turn=2) == before
        truncated = drawn(("title", "Ferry traffic 2031"), complete=False)
        assert replace_drawn(before, texts, truncated, standing_below=2, turn=2) == before

    def test_an_empty_memory_stays_empty(self) -> None:
        empty = plan([], [], seq=1, turn=2)

        after = replace_drawn(
            empty, ["Ferry traffic 2031"], drawn(("title", "Ferry traffic 2031")), standing_below=1, turn=2
        )

        assert after == empty and not memory_written(memory_delta(after.entries, after.seq))

    def test_only_entries_from_before_the_run_of_a_part_it_names(self) -> None:
        legend = RememberItem(kind="title", target="color", text="legend title: 'Vessel class'", expected_text="Class")
        own = plan(entries(legend), [HARBOUR_TITLE], seq=2, turn=2)  # the run's own item, m2, is no standing one

        after = replace_drawn(
            own, ["Ferry traffic 2031"], drawn(("title", "Ferry traffic 2031")), standing_below=2, turn=2
        )

        assert after == own

    def test_a_replacement_past_the_cap_leaves_the_old_entry(self) -> None:
        fill = [RememberItem(kind="other", text=f"{n:02d}" + "x" * 143) for n in range(20)]  # 2,900 characters
        crowded = standing(HARBOUR_TITLE, *fill)
        long_title = "Ferry traffic " + "y" * 100  # its entry would take the memory past 3,000 characters

        after = replace_drawn(crowded, [long_title], drawn(("title", long_title)), standing_below=crowded.seq, turn=2)

        assert after == crowded

    def test_two_texts_that_fill_one_role_replace_nothing(self) -> None:
        """matplotlib reports a figure title and an axes title both as `title`: which one is the entry's is unknown."""
        before = standing(HARBOUR_TITLE)
        render = drawn(("suptitle", "Ferry traffic 2031"), ("title", "Weekday crossings"))

        both = replace_drawn(before, ["Weekday crossings", "Ferry traffic 2031"], render, standing_below=2, turn=2)
        one = replace_drawn(before, ["Ferry traffic 2031"], render, standing_below=2, turn=2)

        assert both == before
        assert [entry.expect for entry in one.entries] == ["Ferry traffic 2031"]  # the figure title the user wrote

    def test_a_role_of_several_texts_takes_only_the_figure_title(self) -> None:
        """Of a role that holds several texts, only a figure title the user wrote stands for the plot's title: an axes
        title under it, one of several panel titles or one of several axis labels may be any panel's or the subtitle."""
        before = standing(HARBOUR_TITLE, ENERGY_LABEL)
        # The plot language changed: the figure title is the old title translated, the axes title a subtitle the user
        # wrote. That text fills the title role alone, yet it is no title.
        translated = drawn(("suptitle", "Arrivées au port"), ("title", "Evening runs"))
        panels = drawn(("title", "North quay"), ("title", "South quay"))
        labels = drawn(("y axis label", "Load north"), ("y axis label", "Load south"))

        assert replace_drawn(before, ["Evening runs"], translated, standing_below=3, turn=2) == before
        assert replace_drawn(before, ["North quay"], panels, standing_below=3, turn=2) == before
        assert replace_drawn(before, ["Load north"], labels, standing_below=3, turn=2) == before

    @staticmethod
    def probe_of(fig: Figure) -> DrawnTexts:
        """The drawn texts matplotlib's own probe reports for `fig`."""
        FigureCanvasAgg(fig)
        render = drawn_texts(harness.probe(fig, 100))
        assert render is not None and render.complete
        return render

    @classmethod
    def probed(cls, *, figure_title: str, axes_title: str) -> DrawnTexts:
        """The drawn texts matplotlib's own probe reports for a figure title above an axes title and two axis labels."""
        fig = Figure(figsize=(16, 9))
        ax = fig.subplots()
        ax.plot([1, 2, 3], [4.0, 5.5, 5.0])
        fig.suptitle(figure_title)
        ax.set_title(axes_title)
        ax.set_xlabel("Hour of day")
        ax.set_ylabel("Daily load (kWh)")
        return cls.probe_of(fig)

    def test_a_real_matplotlib_probe_names_the_parts(self) -> None:
        """The roles the replacement reads are the ones matplotlib's probe writes."""
        render = self.probed(figure_title="Ferry traffic 2031", axes_title="Weekday crossings")
        time = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Time'", expected_text="Time")
        before = standing(HARBOUR_TITLE, ENERGY_LABEL, time)

        after = replace_drawn(before, ["Ferry traffic 2031", "kWh", "Hour of day"], render, standing_below=4, turn=2)

        assert [(entry.kind, entry.target, entry.expect) for entry in after.entries] == [
            ("axis_label", "y", "Energy use per day"),  # `kWh` stands inside the label, never as all of it
            ("title", None, "Ferry traffic 2031"),
            ("axis_label", "x", "Hour of day"),
        ]

    def test_a_real_matplotlib_axes_title_under_a_figure_title_never_replaces_the_title(self) -> None:
        """matplotlib's probe reports the axes title as `title` too; the user's new subtitle drawn there, under the old
        title translated into the figure title, leaves the title entry as it is."""
        render = self.probed(figure_title="Arrivées au port", axes_title="Evening runs")
        before = standing(HARBOUR_TITLE)

        assert replace_drawn(before, ["Evening runs"], render, standing_below=2, turn=2) == before
        lengthened = self.probed(figure_title="Harbour arrivals 2031", axes_title="Evening runs")
        assert replace_drawn(before, ["Evening runs"], lengthened, standing_below=2, turn=2) == before

    @pytest.mark.parametrize("free_text_on", ["figure", "axes"])
    def test_a_real_matplotlib_title_drawn_as_a_free_text_stays_the_title(self, free_text_on: str) -> None:
        """A title drawn with `fig.text` or `ax.text` is no title to matplotlib's probe, so the user's subtitle drawn as
        the axes title fills the title role alone; the old title is still drawn whole, so it stays the title."""
        fig = Figure(figsize=(16, 9))
        ax = fig.subplots()
        ax.plot([1, 2, 3], [4.0, 5.5, 5.0])
        if free_text_on == "figure":
            fig.text(0.05, 0.95, "Harbour arrivals", fontsize=20, weight="bold")
        else:
            ax.text(0.0, 1.08, "Harbour arrivals", transform=ax.transAxes, fontsize=20)
        ax.set_title("Evening runs", loc="left")
        render = self.probe_of(fig)
        before = standing(HARBOUR_TITLE)

        assert replace_drawn(before, ["Evening runs"], render, standing_below=2, turn=2) == before
        # The run's own item files the subtitle: the memory holds it beside the title, never as the title too.
        subtitle = RememberItem(kind="subtitle", text="subtitle: 'Evening runs'", expected_text="Evening runs")
        own = plan(before.entries, [subtitle], seq=before.seq, turn=2)
        after = replace_drawn(own, ["Evening runs"], render, standing_below=2, turn=2)
        assert [(entry.id, entry.kind, entry.expect) for entry in after.entries] == [
            ("m1", "title", "Harbour arrivals"),
            ("m2", "subtitle", "Evening runs"),
        ]

    def test_a_real_matplotlib_figure_y_label_stays_beside_a_panel_label(self) -> None:
        """A y label drawn as the figure's (`supylabel`) is still drawn when the label the user wrote names one panel."""
        fig = Figure(figsize=(16, 9))
        panels = fig.subplots(1, 2)
        for ax in panels:
            ax.plot([1, 2, 3], [4.0, 5.5, 5.0])
        fig.supylabel("Energy use per day")
        panels[0].set_ylabel("Load north")
        before = standing(ENERGY_LABEL)

        assert replace_drawn(before, ["Load north"], self.probe_of(fig), standing_below=2, turn=2) == before


class TestNotDrawn:
    """An entry from before the run whose verbatim text a complete report does not draw is listed, not dropped."""

    def test_an_undrawn_text_is_listed_and_everything_else_is_kept(self) -> None:
        held = entries(HARBOUR_TITLE, LINE, ENERGY_LABEL)
        render = drawn(("title", "Harbour arrivals"), ("y axis label", "Load"))

        assert not_drawn(held, render, standing_below=4, language="en", written_in={1: "en"}) == ["m3"]

    def test_a_text_drawn_inside_a_longer_one_is_still_used(self) -> None:
        """Unlike the replacement, which reads a part's whole text, an entry's text drawn anywhere counts as used."""
        held = entries(HARBOUR_TITLE)
        lengthened = drawn(("title", "Harbour arrivals 2031"))

        assert not_drawn(held, lengthened, standing_below=2, language="en", written_in={1: "en"}) == []

    def test_a_missing_or_incomplete_report_lists_nothing(self) -> None:
        held = entries(HARBOUR_TITLE)

        assert not_drawn(held, None, standing_below=2, language="en", written_in={1: "en"}) == []
        truncated = drawn(("title", "Other"), complete=False)
        assert not_drawn(held, truncated, standing_below=2, language="en", written_in={1: "en"}) == []

    def test_an_entry_written_in_another_plot_language_or_an_unknown_one_counts_as_kept(self) -> None:
        """A language change rewrites the title, so the verbatim text the entry holds is gone for a reason."""
        held = entries(HARBOUR_TITLE)
        translated = drawn(("title", "Arrivées au port"))

        assert not_drawn(held, translated, standing_below=2, language="fr", written_in={1: "English"}) == []
        assert not_drawn(held, translated, standing_below=2, language="fr", written_in={}) == []
        assert not_drawn(held, translated, standing_below=2, language="en", written_in={1: "English"}) == ["m1"]

    def test_an_entry_the_run_added_is_never_listed(self) -> None:
        assert (
            not_drawn(
                entries(HARBOUR_TITLE), drawn(("title", "Other")), standing_below=1, language="en", written_in={1: "en"}
            )
            == []
        )


def shipped_run(library: str, planned: Planned, render: DrawnTexts | None, *, written: Sequence[str] = ()) -> Run:
    """A run of turn 2 that shipped a render with `render`'s drawn texts, its memory planned before it ran."""
    view = SimpleNamespace(library=library, target=("scatter-basic", library))
    run = Run(view=cast(Any, view), dataset=cast(Any, None), language="en")
    run.memory_plan, run.memory_seq, run.written_texts = planned, planned.seq, list(written)
    run.best = Candidate(working="w", run_form="r", pngs={}, plan=AdaptPlan(), attempt=1, drawn=render)
    return run


class TestSettledMemoryIds:
    """What the `plot` event names once the memory is settled with the version."""

    def test_a_replaced_title_is_in_no_list_and_its_replacement_is_added(self) -> None:
        state: dict[str, Any] = {}
        run = shipped_run(
            "matplotlib",
            standing(HARBOUR_TITLE, LINE),
            drawn(("title", "Ferry traffic 2031")),
            written=["Ferry traffic 2031"],
        )

        settle_memory(state, run, True, turn=2)

        assert [(entry.id, entry.expect) for entry in read_memory(state)] == [
            ("m2", None),
            ("m3", "Ferry traffic 2031"),
        ]
        assert state[MEMORY_SEQ] == 4
        assert memory_ids(run, {1: "en"}) == {"kept": ["m2"], "added": ["m3"], "unused": []}

    def test_a_title_the_render_does_not_draw_is_not_used(self) -> None:
        state: dict[str, Any] = {}
        run = shipped_run("matplotlib", standing(HARBOUR_TITLE, LINE), drawn(("title", "Pier 4 at night")))

        settle_memory(state, run, True, turn=2)

        assert state == {}  # nothing to store: the entry stays as it is
        assert memory_ids(run, {1: "en"}) == {"kept": ["m2"], "added": [], "unused": ["m1"]}
        assert memory_ids(run, {}) == {"kept": ["m1", "m2"], "added": [], "unused": []}  # written in no known language

    def test_where_the_reviewer_checks_the_texts_every_entry_counts_as_kept(self) -> None:
        """plotly's probe grounds the reply but never claims a text missing; a whole title it reports still replaces."""
        idle = shipped_run("plotly", standing(HARBOUR_TITLE, LINE), drawn(("title", "Pier 4 at night")))
        assert memory_ids(idle, {1: "en"}) == {"kept": ["m1", "m2"], "added": [], "unused": []}

        state: dict[str, Any] = {}
        renamed = shipped_run(
            "plotly",
            standing(HARBOUR_TITLE, LINE),
            drawn(("title", "Ferry traffic 2031")),
            written=["Ferry traffic 2031"],
        )
        settle_memory(state, renamed, True, turn=2)
        assert memory_ids(renamed, {1: "en"}) == {"kept": ["m2"], "added": ["m3"], "unused": []}

    def test_a_run_that_shipped_nothing_changes_nothing(self) -> None:
        state: dict[str, Any] = {}
        before = standing(HARBOUR_TITLE)
        run = shipped_run("matplotlib", before, drawn(("title", "Ferry traffic 2031")), written=["Ferry traffic 2031"])

        settle_memory(state, run, False, turn=2)

        assert state == {} and run.memory_plan == before


def test_the_owner_examples_become_decisions_and_texts() -> None:
    held = entries(*OWNER_EXAMPLES)

    assert decision_lines(held) == [item.text for item in OWNER_EXAMPLES]
    assert expected_texts(held) == ["Zeit (h)"]  # the formula is no verbatim text
    assert kind_counts(held) == {"annotation": 1, "axis_label": 1, "limits": 1, "marker": 1, "reference_line": 1}
    assert newer_than(held, None) == 5 and newer_than(held, 1) == 0 and newer_than(held, 0) == 5


# --- switch.py ------------------------------------------------------------------------------

MATPLOTLIB = Target(spec_id="scatter-basic", library="matplotlib")
SEABORN = Target(spec_id="scatter-basic", library="seaborn")
PLOTLY = Target(spec_id="scatter-basic", library="plotly")


class TestCarry:
    def test_a_plot_carries_its_asked_theme_its_requests_and_the_memory_texts(self) -> None:
        plot = SourcePlot(theme="dark", theme_asked=True, expected_texts=["Old"], requests=["add a line at 7"])

        carry = carry_for(source=MATPLOTLIB, target=SEABORN, plot=plot, pending=None, memory=entries(LABEL))

        assert carry is not None and carry.from_plot
        assert (carry.theme, carry.expected_texts, carry.requests) == ("dark", ["Zeit (h)"], ["add a line at 7"])

    def test_without_memory_the_versions_own_texts_carry_and_a_site_theme_does_not(self) -> None:
        plot = SourcePlot(theme="dark", theme_asked=False, expected_texts=["Zeit (h)", "\x00"], requests=[])

        carry = carry_for(source=MATPLOTLIB, target=SEABORN, plot=plot, pending=None, memory=[])

        assert carry is not None and (carry.theme, carry.expected_texts) == (None, ["Zeit (h)"])

    def test_a_carry_not_run_yet_moves_on_to_the_next_target(self) -> None:
        pending = Carry(source=MATPLOTLIB, target=SEABORN, from_plot=True, theme="dark", requests=["r"])

        carry = carry_for(source=SEABORN, target=PLOTLY, plot=None, pending=pending, memory=[])

        assert carry is not None and carry.source == MATPLOTLIB and carry.target == PLOTLY and carry.theme == "dark"
        assert read_carry({CARRY: carry.model_dump(mode="json")}, PLOTLY.pair()) == carry
        assert read_carry({CARRY: carry.model_dump(mode="json")}, SEABORN.pair()) is None  # made for another pair

    def test_nothing_carries_without_a_plot_a_pending_carry_or_memory(self) -> None:
        assert carry_for(source=MATPLOTLIB, target=SEABORN, plot=None, pending=None, memory=[]) is None

    def test_the_offer_needs_something_to_carry_and_a_target_that_misses_it(self) -> None:
        carry = Carry(source=MATPLOTLIB, target=SEABORN, from_plot=True)
        held = entries(LINE, turn=4)

        assert summary(carry, held, None).offer  # no plot in the target yet
        assert summary(carry, held, 3).body() == {
            "decisions": 1,
            "newer": 1,
            "target_has_plot": True,
            "from_plot": True,
            "offer": True,
        }
        assert not summary(carry, held, 4).offer  # the target's plot already has every decision
        assert not summary(None, [], None).offer

    def test_the_raw_requests_count_only_while_the_memory_was_never_written(self) -> None:
        carry = Carry(source=MATPLOTLIB, target=SEABORN, from_plot=True, requests=["add a line at 7"])

        assert summary(carry, [], None).decisions == 1
        assert summary(carry, [], None, written=True).decisions == 0  # the user removed every entry
        assert summary(carry, [], None, written=True).offer  # the plot itself still carries (its theme)
        assert memory_written({MEMORY_SEQ: 3}) and not memory_written({MEMORY_SEQ: 1}) and not memory_written({})


# --- Turns through /v1 ----------------------------------------------------------------------


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


KEEP_PLAN: dict[str, Any] = {"edits": [], "title": "Exam Score by Study Hours", "changes": ["Kept the plot"]}
CHANGE = {
    "change_request": "add a horizontal reference line at y = 7 and label the x axis 'Zeit (h)'",
    "base": "previous",
    "expected_texts": ["Zeit (h)"],
    "remember": [LINE.model_dump(exclude_none=True), LABEL.model_dump(exclude_none=True)],
}


def seaborn_plan() -> dict[str, Any]:
    """An adaptation of seaborn's scatter-basic: its generated data block replaced by the user's columns."""
    _, normalised = assess(snapshot_body_model("seaborn"), "seaborn", get_settings())
    start = normalised.index("np.random.seed(42)")
    end = normalised.index("\n", normalised.index("df = pd.DataFrame(", start))
    replace = (
        "df = load_user_data()\n"
        'marketing_spend = df["Study Hours"].to_numpy(dtype=float)\n'
        'sales_revenue = df["Exam Score"].to_numpy(dtype=float)\n'
        'df = pd.DataFrame({"Marketing Spend ($ thousands)": marketing_spend, '
        '"Quarterly Revenue ($ thousands)": sales_revenue})'
    )
    return {"edits": [{"find": normalised[start:end], "replace": replace}], "changes": ["Used your columns"]}


def snapshot_body_model(library: str) -> Any:
    from agents.anyplot.dev_fixture import snapshot_from_repo

    return snapshot_from_repo("scatter-basic", library)


async def say(client: httpx.AsyncClient, sid: str, body: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json=body)
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


async def switch(client: httpx.AsyncClient, sid: str, library: str, **extra: Any) -> httpx.Response:
    body = {"library": library, "snapshot": snapshot_body(library=library), **extra}
    return await client.post(f"/v1/sessions/{sid}/library", headers=HEADERS, json=body)


async def seed_memory(sid: str, held: list[MemoryEntry]) -> None:
    runtime = app.dependency_overrides[get_runtime]()
    seq = max((int(entry.id[1:]) for entry in held), default=0) + 1
    await runtime.write_state(await runtime.session(USER, sid), memory_delta(held, seq))


def plot_of(events: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    return next(data for name, data in events if name == "plot")


async def test_a_change_hands_its_decisions_over_and_the_memory_keeps_them_once_it_ships(
    client: httpx.AsyncClient, swap_models
) -> None:
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here it is."},
                {"call": "plot_pipeline", "args": CHANGE},
                {"text": "Line and label added."},
                {"text": "It shows two decisions."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)

    events = await say(client, sid, {"text": "add a line at 7 and call the x axis 'Zeit (h)'"})

    # The fake render draws no 'Zeit (h)', so the plot ships with that note: shipped all the same.
    assert plot_of(events)["status"] == "needs_attention"
    change = adapter_inputs(fake)[1]
    assert DECISIONS_HEADING in change and EARLIER_REQUESTS_HEADING not in change  # what stands once it ships
    assert LINE.text in change and LABEL.text in change
    memory = (await client.get(f"/v1/sessions/{sid}/memory", headers=HEADERS)).json()
    assert memory["max_entries"] == MAX_ENTRIES
    assert [
        (entry["id"], entry["kind"], entry["target"], entry["expect"], entry["turn"]) for entry in memory["entries"]
    ] == [("m1", "reference_line", None, None, 2), ("m2", "axis_label", "x", "Zeit (h)", 2)]
    version = get_services().versions.latest_rendered(sid)
    assert version is not None and (version.spec_id, version.library, version.turn) == (
        "scatter-basic",
        "matplotlib",
        2,
    )
    assert version.expected_texts == ["Zeit (h)"]

    await say(client, sid, {"text": "what do you keep for me?"})
    system = json.dumps([request.config.system_instruction for request in fake.requests][-1], default=str)
    assert "Plot memory: 2 entries" in system and "m2 axis_label/x: x-axis label: 'Zeit (h)'" in system


async def test_a_change_that_ships_nothing_is_never_remembered(client: httpx.AsyncClient, swap_models) -> None:
    broken = {"edits": [{"find": "no such line", "replace": "x"}], "changes": ["Tried"]}
    swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": CHANGE},
            ]
            + [{"text": "That failed."}],
            "adapter": [{"json": SCATTER_PLAN}] + [{"json": broken}] * 6,
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)

    events = await say(client, sid, {"text": "add a line at 7"})

    assert plot_of(events)["status"] == "failed"
    assert (await client.get(f"/v1/sessions/{sid}/memory", headers=HEADERS)).json()["entries"] == []


async def test_the_switch_carries_the_memory_and_the_theme_into_the_new_library(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {"theme": "dark"}},
                {"text": "Dark plot."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "The plot in seaborn, with your decisions."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": seaborn_plan()}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(*OWNER_EXAMPLES, turn=1))

    switched = await switch(client, sid, "seaborn")

    assert switched.status_code == 200, switched.text
    assert switched.json()["target"] == {"spec_id": "scatter-basic", "library": "seaborn"}
    assert switched.json()["carry"] == {
        "decisions": 5,
        "newer": 5,
        "target_has_plot": False,
        "from_plot": True,
        "offer": True,
    }
    state = await _session_state(client, sid)
    assert state[CARRY]["theme"] == "dark" and state[CARRY]["expected_texts"] == ["Zeit (h)"]
    assert len(read_memory(state)) == 5  # the memory stays

    events = await say(client, sid, {"action": "carry_plot"})

    plot = plot_of(events)
    assert (plot["status"], plot["version"]) == ("needs_attention", 2), plot
    # The carried label went to the render's check: the fake render draws no texts, so the check says so.
    assert any("the requested texts could not be checked" in line for line in plot["residual_defects"])
    carried = adapter_inputs(fake)[1]
    assert "Library: seaborn" in carried and "sns." in carried  # the new library's catalogue code, no previous
    assert DECISIONS_HEADING in carried and all(item.text in carried for item in OWNER_EXAMPLES)
    assert EXPECTED_HEADING in carried and "Zeit (h)" in carried
    assert backend.jobs[-1].themes == ("dark",)  # the theme the user asked for in matplotlib
    version = get_services().versions.latest_rendered(sid, target=("scatter-basic", "seaborn"))
    assert version is not None and version.expected_texts == ["Zeit (h)"] and version.theme_asked
    state = await _session_state(client, sid)
    assert state.get(CARRY) is None and len(read_memory(state)) == 5  # taken; the memory goes on
    switch_line = next(line for line in telemetry_lines(caplog) if line["event"] == "plot_switch")
    assert switch_line["memory_kinds"] == kind_counts(entries(*OWNER_EXAMPLES))
    assert (switch_line["carried_count"], switch_line["offered"], switch_line["switch_source"]) == (5, True, "menu")
    runs = [line for line in telemetry_lines(caplog) if line["event"] == "pipeline_run"]
    assert [(run["carried"], run["fresh"], run["memory_entries"]) for run in runs] == [
        (False, True, 0),  # the first `.create_plot()`
        (True, False, 5),
    ]


async def test_start_over_keeps_the_memory_and_applies_it(client: httpx.AsyncClient, swap_models) -> None:
    """Owner decision of 2026-11-02: `.start_over()` is the way out of broken code, not a blank start. It starts from
    the catalogue code and hands the visible memory on; nothing but the user clears it."""
    fake = swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}] * 2,
            "adapter": [{"json": SCATTER_PLAN}, {"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    held = entries(LINE, STARS)
    await seed_memory(sid, held)

    events = await create_plot(client, sid)  # `.start_over()` sends the same action

    assert plot_of(events)["status"] == "ok"  # SCATTER_PLAN applies to the catalogue code only
    start_over = adapter_inputs(fake)[1]
    assert DECISIONS_HEADING in start_over and LINE.text in start_over and STARS.text in start_over
    state = await _session_state(client, sid)
    assert read_memory(state) == held and state[MEMORY_SEQ] == 3  # kept as it was


async def test_start_over_stays_fresh_when_the_root_asks_for_the_previous_version(
    client: httpx.AsyncClient, swap_models
) -> None:
    """`create_plot` is the catalogue plot whatever `base` the root passes (Flash review, 2026-11-02)."""
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": {"base": "previous"}},
                {"text": "Here again."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(LINE))

    events = await create_plot(client, sid)

    assert plot_of(events)["status"] == "ok"  # SCATTER_PLAN applies to the catalogue code only
    assert LINE.text in adapter_inputs(fake)[1]  # with the memory
    assert len(read_memory(await _session_state(client, sid))) == 1


CHANGE_WITHOUT_MEMORY = {"change_request": "add a horizontal reference line at y = 7", "base": "previous"}


async def test_a_session_that_never_remembered_carries_its_raw_requests(client: httpx.AsyncClient, swap_models) -> None:
    """The raw lineage requests are the fallback while the memory was never written: the carry run hands them on."""
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": CHANGE_WITHOUT_MEMORY},
                {"text": "Line added."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "In seaborn."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}, {"json": seaborn_plan()}],
            "reviewer": [{"json": VERDICT_OK}] * 3,
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await say(client, sid, {"text": "add a line at 7"})

    switched = await switch(client, sid, "seaborn")

    assert switched.json()["carry"]["decisions"] == 1  # the request behind the matplotlib plot
    await say(client, sid, {"action": "carry_plot"})
    carried = adapter_inputs(fake)[2]
    assert EARLIER_REQUESTS_HEADING in carried and CHANGE_WITHOUT_MEMORY["change_request"] in carried


async def test_what_the_user_removed_never_comes_back_through_the_raw_requests(
    client: httpx.AsyncClient, swap_models
) -> None:
    """Owner decision of 2026-11-02: once the memory held a decision, the visible memory alone travels. The user
    removes every entry after the switch: the carry run gets no decision, no raw request and no carried label."""
    remembered = {**CHANGE, "remember": [LINE.model_dump(exclude_none=True), LABEL.model_dump(exclude_none=True)]}
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": remembered},
                {"text": "Line and label added."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "In seaborn."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}, {"json": seaborn_plan()}],
            "reviewer": [{"json": VERDICT_OK}] * 3,
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await say(client, sid, {"text": "add a line at 7 and call the x axis 'Zeit (h)'"})
    switched = await switch(client, sid, "seaborn")
    assert switched.json()["carry"]["decisions"] == 2

    forgot = await client.delete(f"/v1/sessions/{sid}/memory", headers=HEADERS)
    assert forgot.json() == {"entries": [], "max_entries": MAX_ENTRIES, "written": True}
    after = await switch(client, sid, "matplotlib")
    assert after.json()["carry"]["decisions"] == 0  # nothing travels any more
    assert (await switch(client, sid, "seaborn")).json()["carry"]["decisions"] == 0

    await say(client, sid, {"action": "carry_plot"})

    carried = adapter_inputs(fake)[2]
    assert DECISIONS_HEADING not in carried and EARLIER_REQUESTS_HEADING not in carried
    assert CHANGE["change_request"] not in carried and "Zeit (h)" not in carried


async def test_a_note_of_decisions_alone_is_kept_for_the_first_plot() -> None:
    from agents.anyplot.pipeline import hold_request, settle_pending_request, take_pending_request
    from agents.anyplot.schemas import KeepRequestArgs

    state: dict[str, Any] = {}
    kept = KeepRequestArgs(remember=[LINE])  # no request text: still something to keep
    hold_request(state, PipelineArgs(**kept.model_dump()))
    assert state[PENDING_REMEMBER] == [LINE.model_dump(mode="json")]

    taken = take_pending_request(state, PipelineArgs())
    assert taken.remember == [LINE]
    settle_pending_request(state, taken, shipped=False)  # a failed first plot keeps it
    assert state[PENDING_REMEMBER] == [LINE.model_dump(mode="json")]
    settle_pending_request(state, taken, shipped=True)
    assert state[PENDING_REMEMBER] is None


async def test_a_carry_run_that_ships_nothing_keeps_the_carry(client: httpx.AsyncClient, swap_models) -> None:
    broken = {"edits": [{"find": "no such line", "replace": "x"}], "changes": ["Tried"]}
    swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}] * 2,
            "adapter": [{"json": SCATTER_PLAN}] + [{"json": broken}] * 6,
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(LINE, LABEL))
    assert (await switch(client, sid, "seaborn")).status_code == 200

    events = await say(client, sid, {"action": "carry_plot"})

    assert plot_of(events)["status"] == "failed"
    state = await _session_state(client, sid)
    assert read_carry(state, ("scatter-basic", "seaborn")) is not None and len(read_memory(state)) == 2
    # The carried label fed the run's checks only: it never became a text of the user's kept note (Copilot on #12520).
    assert state.get(PENDING_EXPECTED_TEXTS) is None and state.get(PENDING_REQUEST) is None


async def test_switching_back_counts_the_decisions_the_older_plot_misses(
    client: httpx.AsyncClient, swap_models
) -> None:
    swap_models(
        "gemini",
        {"root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}]}
        | {"adapter": [{"json": SCATTER_PLAN}], "reviewer": [{"json": VERDICT_OK}]},
    )
    sid = await open_session(client)
    await create_plot(client, sid)  # matplotlib's version 1, turn 1
    assert (await switch(client, sid, "seaborn")).status_code == 200

    await seed_memory(sid, entries(LINE, turn=1))
    back = await switch(client, sid, "matplotlib")
    assert back.json()["carry"]["newer"] == 0 and not back.json()["carry"]["offer"]  # its plot is current

    assert (await switch(client, sid, "seaborn")).status_code == 200
    await seed_memory(sid, [*entries(LINE, turn=1), *plan([], [STARS], seq=2, turn=3).entries])
    back = await switch(client, sid, "matplotlib")
    assert back.json()["carry"] == {
        "decisions": 2,
        "newer": 1,
        "target_has_plot": True,
        "from_plot": True,  # the carry seaborn never ran moved on, with matplotlib's plot behind it
        "offer": True,
    }


async def test_another_spec_stays_refused_until_the_plot_type_switch(client: httpx.AsyncClient) -> None:
    sid = await open_session(client)
    body = {"library": "matplotlib", "snapshot": snapshot_body(spec_id="bar-basic")}

    response = await client.post(f"/v1/sessions/{sid}/library", headers=HEADERS, json=body)

    assert response.status_code == 422 and response.json()["detail"] == "invalid"


async def test_the_page_lists_and_removes_entries(client: httpx.AsyncClient, runtime: Runtime) -> None:
    sid = await open_session(client)
    assert (await client.get(f"/v1/sessions/{sid}/memory", headers=HEADERS)).json() == {
        "entries": [],
        "max_entries": MAX_ENTRIES,
        "written": False,  # never held an entry: the raw requests are still the fallback
    }
    await seed_memory(sid, entries(LINE, STARS))

    removed = await client.delete(f"/v1/sessions/{sid}/memory/m1", headers=HEADERS)

    assert removed.status_code == 200
    assert [entry["id"] for entry in removed.json()["entries"]] == ["m2"]
    assert (await client.delete(f"/v1/sessions/{sid}/memory/m1", headers=HEADERS)).status_code == 404
    assert (await client.delete(f"/v1/sessions/{sid}/memory/x1", headers=HEADERS)).status_code == 422
    runtime.active[sid] = ActiveRun(abort=asyncio.Event(), user=USER, started=runtime.now())  # a turn in flight
    try:
        assert (await client.delete(f"/v1/sessions/{sid}/memory/m2", headers=HEADERS)).status_code == 409
    finally:
        runtime.active.pop(sid, None)


async def test_forget_removes_an_entry_before_the_run(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", {"root": [{"call": "forget", "args": {"entry_id": "m1"}}, {"text": "Forgotten."}]})
    sid = await open_session(client)
    await seed_memory(sid, entries(LINE, STARS))

    await say(client, sid, {"text": "no reference line after all"})

    assert [entry.id for entry in read_memory(await _session_state(client, sid))] == ["m2"]


async def test_a_kept_first_plot_note_brings_its_decisions_to_the_memory(
    client: httpx.AsyncClient, swap_models
) -> None:
    swap_models(
        "gemini",
        {
            "root": [
                {
                    "call": "keep_plot_request",
                    "args": {
                        "change_request": "title 'Lernzeit'",
                        "expected_texts": ["Lernzeit"],
                        "remember": [{"kind": "title", "text": "title: 'Lernzeit'", "expected_text": "Lernzeit"}],
                    },
                },
                {"text": "Kept for the first plot."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await say(client, sid, {"text": "Titel 'Lernzeit' bitte"})
    assert (await _session_state(client, sid))[PENDING_REMEMBER] == [
        {"kind": "title", "text": "title: 'Lernzeit'", "target": None, "expected_text": "Lernzeit", "replaces": None}
    ]

    await create_plot(client, sid)

    state = await _session_state(client, sid)
    assert [(entry.kind, entry.expect) for entry in read_memory(state)] == [("title", "Lernzeit")]
    assert state[PENDING_REMEMBER] is None


FERRY_PROBE = {"texts": [], "labels": [{"kind": "title", "text": "Ferry traffic 2031"}]}


async def test_a_title_kept_without_remember_replaces_the_remembered_one(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend
) -> None:
    """A title the user wrote reached the plot through a kept note alone, with no `remember` item: the render draws
    it as the title, so it replaces the remembered title, and the next change no longer hands the old one on."""
    keep = {
        "call": "keep_plot_request",
        "args": {"change_request": "title: Ferry traffic 2031", "expected_texts": ["Ferry traffic 2031"]},
    }
    change = {"call": "plot_pipeline", "args": {"change_request": "larger markers", "base": "previous"}}
    fake = swap_models(
        "gemini",
        {
            "root": [
                keep,
                {"text": "Kept for the first plot."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                change,
                {"text": "Larger markers."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    backend.script = lambda job, theme: FakeOutcome(probe=FERRY_PROBE)
    sid = await open_session(client)
    await seed_memory(sid, entries(HARBOUR_TITLE, LINE))
    await say(client, sid, {"text": "title: Ferry traffic 2031"})

    events = await create_plot(client, sid)

    assert "Harbour arrivals" in adapter_inputs(fake)[0]  # the run still had the old title as a decision
    assert plot_of(events)["memory"] == {"kept": ["m2"], "added": ["m3"], "unused": []}
    held = read_memory(await _session_state(client, sid))
    assert [(entry.id, entry.kind, entry.expect) for entry in held] == [
        ("m2", "reference_line", None),
        ("m3", "title", "Ferry traffic 2031"),
    ]

    await say(client, sid, {"text": "larger markers"})

    following = adapter_inputs(fake)[1]
    assert "bold title: 'Ferry traffic 2031'" in following and "Harbour arrivals" not in following


async def test_a_remembered_title_the_plot_does_not_draw_is_listed_as_not_used(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, runtime: Runtime
) -> None:
    """The entry stays in the memory, and the plot event lists it apart from the kept ones; once the plot language
    changed, the entry's text may have been translated, so it counts as kept."""
    change = {"call": "plot_pipeline", "args": {"change_request": "larger markers", "base": "previous"}}
    swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}]
            + [change, {"text": "Larger markers."}] * 2,
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}] * 3,
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)  # turn 1, in English
    await seed_memory(sid, entries(HARBOUR_TITLE, LINE, turn=1))
    backend.script = lambda job, theme: FakeOutcome(probe=FERRY_PROBE)

    events = await say(client, sid, {"text": "larger markers"})

    assert plot_of(events)["memory"] == {"kept": ["m2"], "added": [], "unused": ["m1"]}
    assert [entry.id for entry in read_memory(await _session_state(client, sid))] == ["m1", "m2"]

    await runtime.write_state(await runtime.session(USER, sid), {PLOT_LANGUAGE: "fr"})
    translated = await say(client, sid, {"text": "larger markers"})

    assert plot_of(translated)["memory"] == {"kept": ["m1", "m2"], "added": [], "unused": []}


async def test_a_carried_text_never_replaces_a_remembered_one(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend
) -> None:
    """A switch's carry run checks the memory's own texts, which the user did not write for that run: a render that
    draws the remembered axis label as its whole title leaves the remembered title as it is."""
    swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}] * 2,
            # The render misses the remembered title, so the run repairs once before it ships.
            "adapter": [{"json": SCATTER_PLAN}, {"json": seaborn_plan()}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}] * 3,
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    held = entries(HARBOUR_TITLE, ENERGY_LABEL, turn=1)
    await seed_memory(sid, held)
    assert (await switch(client, sid, "seaborn")).status_code == 200
    title_only = {"texts": [], "labels": [{"kind": "title", "text": "Energy use per day"}]}
    backend.script = lambda job, theme: FakeOutcome(probe=title_only)

    events = await say(client, sid, {"action": "carry_plot"})

    plot = plot_of(events)
    assert plot["version"] == 2 and plot["memory"]["added"] == [], plot
    state = await _session_state(client, sid)
    assert read_memory(state) == held and state[MEMORY_SEQ] == 3


async def test_the_bundle_names_each_versions_spec_and_library(client: httpx.AsyncClient, swap_models) -> None:
    from .fakes import default_script

    swap_models("gemini", default_script())
    sid = await open_session(client)
    await create_plot(client, sid)

    bundle = (await client.get(f"/v1/sessions/{sid}/bundle", headers=HEADERS)).json()

    assert [(item["spec_id"], item["library"]) for item in bundle["versions"]] == [("scatter-basic", "matplotlib")]


def test_a_full_memory_is_reported_on_the_result() -> None:
    result = PlotResult(status="ok", attempts=1, artifacts=["plot.py"], memory_full=True)
    assert result.memory_full is True
    assert PipelineArgs(remember=OWNER_EXAMPLES).remember == OWNER_EXAMPLES
    with pytest.raises(ValueError):
        PipelineArgs(remember=[*OWNER_EXAMPLES, LINE])  # at most five per run


def test_a_version_is_filed_under_its_pair() -> None:
    version = CodeVersion(
        number=1,
        working="w",
        run_form="r",
        export="e",
        data_csv="a\n1\n",
        render_id="r1",
        result=PlotResult(status="ok", attempts=1, artifacts=["plot.py"]),
        library="seaborn",
        spec_id="scatter-basic",
    )
    assert version.target == ("scatter-basic", "seaborn")


def telemetry_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
