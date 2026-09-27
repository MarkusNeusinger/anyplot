"""Tests for automation.scripts.spec_characteristics_lint.

The lint guards the closing "What a good version looks like" section of every
spec: ``contract`` is the shape the regen gate parses as C1..Cn (blocking in
CI), ``style`` the house rules (warnings; hard failures under ``--strict``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from automation.scripts import spec_characteristics_lint as lint
from automation.scripts.spec_characteristics_lint import (
    ERROR,
    WARNING,
    Finding,
    annotation,
    check_contract,
    check_style,
    main,
)


PLOTS_DIR = Path(__file__).resolve().parents[4] / "plots"
SEEDED_SPECS = [
    "bubble-basic",
    "scatter-basic",
    "line-basic",
    "bar-basic",
    "heatmap-basic",
    "heatmap-correlation",
    "violin-basic",
    "network-force-directed",
]

S = "A good version shows: "
E = "Expected, not a defect: "

GOOD = [
    S + "every mark at its exact (x, y) value, so the cloud's shape reads at a glance.",
    E + "overlapping marks in dense regions.",
    S + "where marks overlap, translucency keeps each one distinguishable.",
    S + "the basic variant's x and y only, with one color for all marks.",
]


def _spec(
    bullets: list[str] | None = None,
    *,
    spec_id: str = "demo-basic",
    notes: tuple[str, ...] = ("Use translucency so overlapping marks stay readable",),
    body: str | None = None,
    tail: str = "",
) -> str:
    """A spec with the four standard sections and a characteristic section."""
    head = (
        f"# {spec_id}: Demo Chart\n\n"
        "## Description\n\nA demo chart of 3 measurements.\n\n"
        "## Applications\n\n- Demo use\n\n"
        "## Data\n\n- `x` (numeric) - horizontal values\n- `y` (numeric) - vertical values\n\n"
        "## Notes\n\n" + "".join(f"- {n}\n" for n in notes) + "\n"
        "## What a good version looks like\n\n"
    )
    if body is None:
        body = "".join(f"- {b}\n" for b in (GOOD if bullets is None else bullets))
    return head + body + tail


def _rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


class TestContract:
    def test_good_section_passes(self):
        assert check_contract(_spec()) == []

    def test_spec_without_section_passes_unless_required(self):
        text = "# demo: Demo\n\n## Notes\n\n- a\n"
        assert check_contract(text) == []
        assert _rules(check_contract(text, require_section=True)) == ["K0"]

    def test_indented_continuation_is_allowed(self):
        body = f"- {GOOD[0]}\n  still the first bullet\n- {GOOD[1]}\n- {GOOD[2]}\n"
        assert check_contract(_spec(body=body)) == []

    def test_prefix_phrase_without_colon_is_not_a_second_prefix(self):
        body = f"- {GOOD[0]}\n- {E}overlap, which is expected, not a defect, in dense regions.\n- {GOOD[2]}\n"
        assert check_contract(_spec(body=body)) == []

    @pytest.mark.parametrize(
        ("body", "rule"),
        [
            pytest.param(
                "".join(f"- {b}\n" for b in GOOD) + "\n## What a good version looks like\n\n- " + S + "more.\n",
                "K1",
                id="duplicate-heading",
            ),
            pytest.param("".join(f"- {b}\n" for b in GOOD) + "\n## Later\n\n- not this\n", "K2", id="section-not-last"),
            pytest.param(f"- {GOOD[0]}\n### Sub\n- {GOOD[1]}\n- {GOOD[2]}\n", "K2", id="sub-heading"),
            pytest.param(f"- {GOOD[0]}\nA stray paragraph.\n- {GOOD[1]}\n", "K3", id="stray-paragraph"),
            pytest.param(f"- {GOOD[0]}\n* {GOOD[1]}\n- {GOOD[2]}\n", "K3", id="star-bullet"),
            pytest.param(f"- {GOOD[0]}\n+ {GOOD[1]}\n- {GOOD[2]}\n", "K3", id="plus-bullet"),
            pytest.param(f"- {GOOD[0]}\n1. {GOOD[1]}\n- {GOOD[2]}\n", "K3", id="numbered-bullet"),
            pytest.param(f"  {GOOD[0]}\n- {GOOD[1]}\n- {GOOD[2]}\n", "K3", id="indented-before-any-bullet"),
            pytest.param(f"- {GOOD[0]}\n- \n- {GOOD[1]}\n", "K3", id="empty-bullet"),
            pytest.param(f"- {GOOD[0]}\n", "K4", id="one-bullet"),
            pytest.param("".join(f"- {S}property number {i}.\n" for i in range(9)), "K4", id="nine-bullets"),
            pytest.param(
                f"- {GOOD[0]}\n- {GOOD[1]}\n- {GOOD[0].upper().replace(S.upper(), S)}   \n", "K5", id="duplicate-bullet"
            ),
            pytest.param(f"- {GOOD[0]}\n- Overlap in dense regions is fine.\n", "K6", id="missing-prefix"),
            pytest.param(f"- {GOOD[0]}\n- A good version show: legend.\n", "K6", id="misspelled-prefix"),
            pytest.param(f"- {GOOD[0]}\n- expected, not a defect: overlap.\n", "K6", id="prefix-wrong-case"),
            pytest.param(f"- {GOOD[0]}\n- **Expected, not a defect:** overlap.\n", "K6", id="bold-prefix"),
            pytest.param(f"- {GOOD[0]}\n- {E.strip()}\n", "K6", id="prefix-without-text"),
            pytest.param(f"- {GOOD[0]}\n- {S}translucency. {E}overlap.\n", "K6", id="two-prefixes"),
            pytest.param(
                f"- {GOOD[0]}\n- {S}translucency; expected, not a defect: overlap.\n", "K6", id="second-prefix-lower-case"
            ),
            pytest.param(
                f"- {GOOD[0]}\n- {E}overlap. **A good version shows**: outlines.\n", "K6", id="second-prefix-bold"
            ),
        ],
    )
    def test_violation(self, body: str, rule: str):
        assert rule in _rules(check_contract(_spec(body=body)))

    @pytest.mark.parametrize(
        "heading",
        ["## What a Good Version Looks Like", "##  What a good version looks like", "### What a good version looks like"],
    )
    def test_near_miss_heading(self, heading: str):
        text = _spec().replace("## What a good version looks like", heading)
        assert "K1" in _rules(check_contract(text))

    def test_crlf_line_endings(self):
        assert "K8" in _rules(check_contract(_spec().replace("\n", "\r\n")))

    def test_prefix_messages_name_the_fix(self):
        body = f"- {GOOD[0]}\n- a good version shows: legend.\n- Legend visible.\n"
        messages = [f.message for f in check_contract(_spec(body=body)) if f.rule == "K6"]
        assert any("exactly as 'A good version shows: '" in m for m in messages)
        assert any("start the bullet with" in m for m in messages)

    def test_parity_with_the_gate_parser(self, monkeypatch):
        """K7: the lint and the gate must never disagree on the bullet count."""
        real = lint.parse_characteristics
        monkeypatch.setattr(lint, "parse_characteristics", lambda text: real(text)[:-1])
        assert "K7" in _rules(check_contract(_spec()))

    def test_findings_carry_line_numbers(self):
        text = _spec(body=f"- {GOOD[0]}\n- no prefix here\n- {GOOD[1]}\n")
        (finding,) = [f for f in check_contract(text) if f.rule == "K6"]
        assert text.splitlines()[finding.line - 1] == "- no prefix here"


class TestStyle:
    def test_good_section_is_clean_even_strict(self):
        assert check_style(_spec(), "demo-basic", strict=True) == []

    def test_spec_without_section_has_no_findings(self):
        assert check_style("# demo\n\n## Notes\n\n- a\n", "demo", strict=True) == []

    def test_hard_rules_warn_by_default_and_fail_when_strict(self):
        text = _spec([*GOOD, S + "a clean design."])
        assert {f.severity for f in check_style(text, "demo-basic") if f.rule == "S5"} == {WARNING}
        assert {f.severity for f in check_style(text, "demo-basic", strict=True) if f.rule == "S5"} == {ERROR}

    def test_soft_rules_never_fail(self):
        text = _spec([*GOOD, S + "a `size` legend."])
        assert {f.severity for f in check_style(text, "demo-basic", strict=True) if f.rule == "W2"} == {WARNING}

    @pytest.mark.parametrize(
        ("bullets", "rule"),
        [
            pytest.param(GOOD[:2], "S1", id="two-bullets"),
            pytest.param([*GOOD, *(S + f"property {w}." for w in ("one", "two", "three"))], "S1", id="seven-bullets"),
            pytest.param([GOOD[0], GOOD[2], GOOD[3]], "S4", id="no-expected-bullet"),
            pytest.param([GOOD[1], E + "a dominant bar.", E + "uneven gaps."], "S4", id="no-shows-bullet"),
            pytest.param([*GOOD, S + "a clean design throughout."], "S5", id="generic-clean-design"),
            pytest.param([*GOOD, S + "a publication-quality finish."], "S5", id="generic-hyphenated"),
            pytest.param([*GOOD, S + "a modern look."], "S5", id="generic-modern"),
            pytest.param([*GOOD, S + "markers of 12 px."], "S6", id="numeral-px"),
            pytest.param([*GOOD, S + "at least 3 labels."], "S6", id="numeral-comparator-words"),
            pytest.param([*GOOD, S + "fewer than <5 labels."], "S6", id="numeral-comparator-sign"),
            pytest.param([*GOOD, S + "labels covering 50% of the width."], "S6", id="numeral-percent"),
            pytest.param([*GOOD, S + "marks with alpha 0.5."], "S7", id="alpha-value"),
            pytest.param([*GOOD, S + "marks at 0.6 opacity."], "S7", id="opacity-value"),
            pytest.param([*GOOD, S + "a title with font size 3."], "S7", id="font-size-value"),
            pytest.param([*GOOD, S + "a matplotlib-style frame."], "S8", id="library-name"),
            pytest.param([*GOOD, S + "a legend from ax.legend() on top."], "S8", id="call-syntax"),
            pytest.param([*GOOD, S + "a D3 force layout."], "S8", id="library-short-name"),
            pytest.param([*GOOD, S + "marks in #009E73."], "S9", id="hex-color"),
            pytest.param([*GOOD, S + "x" * 380 + "."], "S10", id="over-400-chars"),
            pytest.param([*GOOD, S + "x" * 320 + "."], "W3", id="over-320-chars"),
            pytest.param([*GOOD, S + "a legend with 7 entries."], "W1", id="numeral-not-in-spec"),
            pytest.param([*GOOD, S + "the `y` values on the vertical axis."], "W2", id="backticks"),
            pytest.param([*GOOD, E + "overlap, which must stay readable."], "W6", id="expected-with-requirement"),
            pytest.param([*GOOD, E + "overlap; translucency keeps it apart."], "W6", id="expected-with-keep"),
            pytest.param([*GOOD, S + "overlap in dense regions is fine."], "W6", id="shows-with-permission"),
            pytest.param([*GOOD, S + "a dominant bar, not an imbalance."], "W6", id="shows-not-an-imbalance"),
        ],
    )
    def test_violation(self, bullets: list[str], rule: str):
        assert rule in _rules(check_style(_spec(bullets), "demo-basic"))

    @pytest.mark.parametrize(
        ("bullet", "rule"),
        [
            pytest.param(S + "no overlapping labels.", "S5", id="no-overlapping-is-not-no-overlap"),
            pytest.param(S + "a modern portfolio theory frontier.", "S5", id="allowlisted-domain-term"),
            pytest.param(S + "the 3 measurements as separate marks.", "W1", id="numeral-in-spec"),
            pytest.param(S + "r = 3 on the diagonal.", "S6", id="bare-equals-is-not-a-comparator"),
            pytest.param(S + "moderate transparency.", "S7", id="transparency-without-value"),
            pytest.param(S + "each value(s) label readable.", "S8", id="plural-s-is-not-a-call"),
            pytest.param(S + "marks at their (x, y) values.", "S8", id="parenthesis-after-space"),
            pytest.param(E + "overlap in dense regions, so marks pile up.", "W6", id="so-without-that"),
            pytest.param(S + "where marks overlap, translucency.", "W6", id="shows-without-permission-words"),
        ],
    )
    def test_no_false_positive(self, bullet: str, rule: str):
        assert rule not in _rules(check_style(_spec([*GOOD, bullet]), "demo-basic"))

    def test_continuation_lines(self):
        body = "".join(f"- {b}\n" for b in GOOD) + "  wrapped onto a second line\n"
        assert "S2" in _rules(check_style(_spec(body=body), "demo-basic"))

    @pytest.mark.parametrize("ending", ["", "\n\n"])
    def test_file_ends_with_exactly_one_newline(self, ending: str):
        text = _spec().rstrip("\n") + ending
        assert "S3" in _rules(check_style(text, "demo-basic"))

    def test_basic_variant_bullet(self):
        bullets = GOOD[:3]
        assert "W4" in _rules(check_style(_spec(bullets), "demo-basic"))
        assert "W4" not in _rules(check_style(_spec(bullets, spec_id="demo-annotated"), "demo-annotated"))
        assert "W4" not in _rules(check_style(_spec(), "demo-basic"))

    def test_negation_against_notes(self):
        notes = ("Include a size legend to explain the scaling",)
        text = _spec([*GOOD, S + "no size legend, because the axis names the quantity."], notes=notes)
        (finding,) = [f for f in check_style(text, "demo-basic") if f.rule == "W5"]
        assert "no size legend" in finding.message
        assert "Include a size legend" in finding.message

    def test_negation_needs_a_trigger_word(self):
        # The Data line names "horizontal values" but asks for nothing.
        text = _spec([*GOOD, S + "without horizontal values on any axis."])
        assert "W5" not in _rules(check_style(text, "demo-basic"))
        text = _spec([*GOOD, S + "without horizontal values."], notes=("Show horizontal values on the x axis",))
        assert "W5" in _rules(check_style(text, "demo-basic"))

    def test_negation_needs_the_same_phrase(self):
        notes = ("Color can optionally distinguish categories",)
        text = _spec([*GOOD, S + "no color scale driven by a further variable."], notes=notes)
        assert "W5" not in _rules(check_style(text, "demo-basic"))

    def test_optional_against_must(self):
        notes = ("A size legend must explain the scaling",)
        text = _spec([*GOOD, S + "an optional size legend."], notes=notes)
        assert "W5" in _rules(check_style(text, "demo-basic"))

    def test_include_against_optional(self):
        notes = ("Markers are optional",)
        text = _spec([*GOOD, S + "a line that includes markers at every value."], notes=notes)
        assert "W5" in _rules(check_style(text, "demo-basic"))


class TestRepository:
    """The seeds set the bar the backfill is calibrated against."""

    @pytest.mark.parametrize("spec_id", SEEDED_SPECS)
    def test_seed_passes_contract_and_strict_style(self, spec_id: str):
        text = (PLOTS_DIR / spec_id / "specification.md").read_text(encoding="utf-8")
        assert check_contract(text) == []
        assert check_style(text, spec_id, strict=True) == []

    @pytest.mark.parametrize("spec_id", SEEDED_SPECS)
    def test_seed_has_both_kinds(self, spec_id: str):
        text = (PLOTS_DIR / spec_id / "specification.md").read_text(encoding="utf-8")
        kinds = {lint.exact_kind(item) for item in lint.parse_characteristics(text)}
        assert kinds == {"shows", "expected"}

    def test_every_spec_passes_the_contract(self):
        """What CI's `contract --all` enforces on every PR and every push to main."""
        failures = {
            path.parent.name: _rules(check_contract(path.read_text(encoding="utf-8")))
            for path in sorted(PLOTS_DIR.glob("*/specification.md"))
        }
        assert {k: v for k, v in failures.items() if v} == {}


class TestCli:
    def _write(self, root: Path, spec_id: str, text: str) -> Path:
        path = root / "plots" / spec_id / "specification.md"
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_annotation_format(self):
        assert annotation("p.md", Finding("K3", "bad line", 4)) == "::error file=p.md,line=4,title=K3::bad line"
        assert annotation("p.md", Finding("W4", "100% sure", None, WARNING)) == "::warning file=p.md,title=W4::100%25 sure"

    def test_contract_exit_codes(self, tmp_path, capsys):
        good = self._write(tmp_path, "good-basic", _spec())
        bad = self._write(tmp_path, "bad-basic", _spec(body=f"- {GOOD[0]}\n"))
        assert main(["contract", str(good)]) == 0
        assert main(["contract", str(good), str(bad)]) == 1
        out = capsys.readouterr().out
        assert "::error file=" in out and "title=K4" in out
        assert "2 file(s), 2 with the section, 1 error(s)" in out

    def test_contract_without_files_is_a_usage_error(self, capsys):
        assert main(["contract"]) == 2

    def test_contract_all_reads_plots_from_the_working_directory(self, tmp_path, monkeypatch, capsys):
        self._write(tmp_path, "a-basic", _spec())
        self._write(tmp_path, "b-basic", "# b\n\n## Notes\n\n- no section\n")
        monkeypatch.chdir(tmp_path)
        assert main(["contract", "--all"]) == 0
        assert "2 file(s), 1 with the section, 0 error(s)" in capsys.readouterr().out
        assert main(["contract", "--all", "--require-section"]) == 1

    def test_style_warns_and_strict_fails(self, tmp_path, capsys):
        path = self._write(tmp_path, "demo-basic", _spec([*GOOD, S + "a clean design."]))
        assert main(["style", str(path)]) == 0
        assert "::warning" in capsys.readouterr().out
        assert main(["style", "--strict", str(path)]) == 1
        assert "::error" in capsys.readouterr().out

    def test_style_derives_the_spec_id_from_the_path(self, tmp_path, capsys):
        path = self._write(tmp_path, "demo-basic", _spec(GOOD[:3]))
        main(["style", str(path)])
        assert "title=W4" in capsys.readouterr().out

    def test_unreadable_file_is_an_error(self, tmp_path, capsys):
        assert main(["contract", str(tmp_path / "missing.md")]) == 1
        assert "title=K0" in capsys.readouterr().out
