"""Tests for automation.scripts.canvas_gate_report log parser + aggregator.

Locks the structured-log contract between the gate step in
.github/workflows/impl-review.yml and the monitoring script: if either side
drifts the regex breaks and these tests fail.
"""

from automation.scripts.canvas_gate_report import LINE_RE, LibStats, aggregate, parse_lines, render_table


class TestLineRegex:
    """The structured-log contract from impl-review.yml's gate step."""

    def test_parses_pass_line(self):
        line = (
            "2026-05-20T14:42:01Z ::notice::canvas_gate library=ggplot2 status=pass "
            "actual=3200x1800 target=3200x1800 delta=+0x+0 attempt=1"
        )
        m = LINE_RE.search(line)
        assert m is not None
        assert m.group("lib") == "ggplot2"
        assert m.group("status") == "pass"
        assert m.group("aw") == "3200"
        assert m.group("dw") == "+0"
        assert m.group("attempt") == "1"

    def test_parses_fail_with_negative_delta(self):
        line = (
            "::notice::canvas_gate library=highcharts status=fail actual=3200x1661 "
            "target=3200x1800 delta=+0x-139 attempt=1"
        )
        m = LINE_RE.search(line)
        assert m is not None
        assert m.group("lib") == "highcharts"
        assert m.group("status") == "fail"
        assert m.group("dh") == "-139"

    def test_unsigned_delta_is_accepted(self):
        # The gate emits signed ints but some int formatters may drop the +.
        line = (
            "::notice::canvas_gate library=matplotlib status=fail actual=2325x2323 "
            "target=2400x2400 delta=-75x-77 attempt=2"
        )
        m = LINE_RE.search(line)
        assert m is not None
        assert m.group("dw") == "-75"
        assert m.group("dh") == "-77"

    def test_ignores_non_matching_notice_lines(self):
        line = "::notice::Found both theme renders — proceeding to review"
        assert LINE_RE.search(line) is None


class TestParseLines:
    def test_extracts_multiple_records(self):
        lines = [
            "::notice::canvas_gate library=ggplot2 status=pass actual=3200x1800 target=3200x1800 delta=+0x+0 attempt=1",
            "noise line",
            "::notice::canvas_gate library=altair status=fail actual=3404x2120 target=3200x1800 delta=+204x+320 attempt=1",
        ]
        records = parse_lines(lines)
        assert len(records) == 2
        assert records[0]["library"] == "ggplot2"
        assert records[0]["status"] == "pass"
        assert records[1]["library"] == "altair"
        assert records[1]["delta"] == (204, 320)


class TestAggregate:
    def test_first_attempt_only(self):
        records = [
            # First attempts: 1 pass + 1 fail for matplotlib
            {
                "library": "matplotlib",
                "status": "pass",
                "delta": (0, 0),
                "attempt": 1,
                "actual": (3200, 1800),
                "target": (3200, 1800),
            },
            {
                "library": "matplotlib",
                "status": "fail",
                "delta": (-40, -40),
                "attempt": 1,
                "actual": (3160, 1760),
                "target": (3200, 1800),
            },
            # Repair attempts: must be ignored
            {
                "library": "matplotlib",
                "status": "pass",
                "delta": (0, 0),
                "attempt": 2,
                "actual": (3200, 1800),
                "target": (3200, 1800),
            },
            # First attempt for altair: 1 fail
            {
                "library": "altair",
                "status": "fail",
                "delta": (204, 320),
                "attempt": 1,
                "actual": (3404, 2120),
                "target": (3200, 1800),
            },
        ]
        stats = aggregate(records)
        assert set(stats.keys()) == {"matplotlib", "altair"}
        assert stats["matplotlib"].runs == 2
        assert stats["matplotlib"].first_pass == 1
        assert stats["matplotlib"].first_fail == 1
        assert stats["matplotlib"].fail_rate == 0.5
        # Only failing deltas are recorded
        assert stats["matplotlib"].deltas == [(-40, -40)]
        assert stats["altair"].first_fail == 1
        assert stats["altair"].fail_rate == 1.0

    def test_empty_records_returns_no_stats(self):
        assert aggregate([]) == {}


class TestRenderTable:
    def test_returns_no_data_message_when_empty(self):
        out = render_table({})
        assert "no canvas_gate" in out.lower()

    def test_flags_libraries_over_threshold(self):
        stats = {
            "altair": LibStats(runs=10, first_pass=2, first_fail=8, deltas=[(200, 300)] * 8),
            "ggplot2": LibStats(runs=10, first_pass=10, first_fail=0, deltas=[]),
        }
        table = render_table(stats)
        assert "altair" in table
        assert "prompt still leaking" in table
        # ggplot2's 0% should NOT be flagged
        ggplot_line = [line for line in table.splitlines() if line.startswith("ggplot2")][0]
        assert "prompt still leaking" not in ggplot_line


class TestLibStatsProperties:
    def test_fail_rate_with_zero_runs(self):
        assert LibStats().fail_rate == 0.0

    def test_avg_delta_handles_empty(self):
        assert LibStats().avg_delta == (0.0, 0.0)

    def test_avg_delta_computes_mean(self):
        s = LibStats(deltas=[(100, 200), (200, 400)])
        assert s.avg_delta == (150.0, 300.0)
