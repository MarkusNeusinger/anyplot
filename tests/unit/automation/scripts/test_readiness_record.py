"""The readiness-regression gate (rule step P2b): the record's reader and the regen gate's keep.

`automation/scripts/readiness_record.py` reads the staged record of
`readiness_scan.py` against the code under review, and `regen_gate.py decide
--readiness` keeps the live implementation when that verdict is a regression.
The two files share no import (the gate runs as a single file), so the last
section holds their statuses and their key grammar together.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from automation.scripts import adapt_record, readiness_record, regen_gate, regen_pick_pairs
from automation.scripts.readiness_record import Verdict, assess, check, code_sha256, file_sha256
from automation.scripts.regen_gate import (
    KEEP,
    MERGE,
    REASON_CODES,
    Readiness,
    build_record,
    decide,
    load_readiness,
    main,
    parse_record_markers,
    readiness_record_errors,
    render_record_marker,
    render_summary,
    validate_record,
)
from core import smoke_run
from tests.unit.automation.scripts.test_regen_gate import (
    NEW_CHECKLIST,
    _adapt,
    _adapt_inp,
    _checklist_json,
    _inp,
    _outputs,
    _regen,
)


SPEC, LIB = "scatter-basic", "altair"
HEADER = '""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nQuality: {quality} | Created: 2026-11-10\n"""\n\n'
NEW = (HEADER.format(quality="pending") + "chart.save('plot.png')\nimage.thumbnail((3200, 1800))\n").encode()
PREV = (HEADER.format(quality="87/100") + "chart.save('plot.png')\n").encode()
KEY = "security:banned-attribute"


def _side(status: str, refusals: list[str] | None = None, *, spec_refused: bool = False) -> dict:
    """One side as `readiness_scan._side` writes it."""
    return {"status": status, "refusals": refusals or [], "spec_refused": spec_refused, "coupled": [], "findings": {}}


def _record(**overrides: Any) -> dict:
    """A regeneration the validator accepted before and refuses now, as the scanner records it."""
    record = {
        "version": 2,
        "spec_id": SPEC,
        "library": LIB,
        "language": "python",
        "new_sha256": file_sha256(NEW),
        "prev_sha256": file_sha256(PREV),
        "verdict": "regression",
        "new": _side("blocked", [KEY]),
        "prev": _side("coupled"),
        "added": [KEY],
        "removed": [],
    }
    record.update(overrides)
    return record


def _assess(record: Any, *, head: bytes | None = NEW, main: bytes | None = PREV) -> Verdict:
    return assess(record, spec_id=SPEC, library=LIB, head=head, main=main)


# --- the verdict -----------------------------------------------------------------------------------


def test_a_refusal_only_the_new_file_has_is_a_regression():
    verdict = _assess(_record())
    assert verdict == Verdict("regression", new="blocked", prev="coupled", added=(KEY,))


def test_the_regression_is_recomputed_and_the_records_own_verdict_is_never_read():
    """A record that hides its regression, and one that claims a regression its sides do not show."""
    hidden = _assess(_record(verdict="none", added=[]))
    assert hidden.status == "regression" and hidden.added == (KEY,)
    claimed = _assess(_record(prev=_side("blocked", [KEY])))
    assert claimed.status == "none" and claimed.added == ()


def test_a_key_the_predecessor_had_is_not_new_and_a_dropped_one_is_listed():
    record = _record(new=_side("blocked", [KEY]), prev=_side("blocked", [KEY, "security:banned-import"]))
    assert _assess(record) == Verdict("none", new="blocked", prev="blocked", removed=("security:banned-import",))


def test_a_side_the_validator_accepts_has_no_keys_whatever_it_lists():
    """Only a refused file has refusals: keys listed under an accepted predecessor cannot hide a regression."""
    assert _assess(_record(prev=_side("clean", [KEY]))).status == "regression"
    assert _assess(_record(new=_side("coupled", [KEY]))) == Verdict("none", new="coupled", prev="coupled")


def test_a_file_the_normaliser_could_not_take_counts_like_a_refused_one():
    record = _record(new=_side("error", ["error:valueerror"]))
    assert _assess(record).added == ("error:valueerror",)


def test_a_first_generation_has_no_predecessor_on_either_side():
    record = _record(prev=None, prev_sha256=None)
    assert _assess(record, main=None) == Verdict("first_generation", new="blocked")


def test_a_map_spec_is_excluded_whatever_the_code_holds():
    record = _record(new=_side("blocked", [KEY], spec_refused=True))
    assert _assess(record).status == "excluded"


@pytest.mark.parametrize("record", [_record(new=None), _record(new=_side("unsupported"))], ids=["no-file", "library"])
def test_a_scan_without_a_verdict_is_unreadable(record):
    assert _assess(record).status == "unreadable"


# --- the record must be of this code ---------------------------------------------------------------


def test_the_reviews_header_commit_never_makes_a_record_stale():
    """impl-review rewrites the header when it stores a review (title, library line, score, date).

    A re-review of the same code reads the head after that commit, and must still find the regression.
    """
    stored = b'""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nLibrary: altair 6.1.0 | Python 3.14.9\n'
    stored += b'Quality: 91/100 | Updated: 2026-11-15\n"""\n\n'
    head = stored + NEW.split(b'"""\n\n', 1)[1]
    main = PREV.replace(b"Quality: 87/100", b"Quality: pending")
    assert head != NEW and main != PREV
    assert _assess(_record(), head=head, main=main).status == "regression"


def test_the_hash_is_the_adapt_records_rule():
    """One rule in three files that cannot import each other; the header goes, every other byte counts."""
    samples = [NEW.decode(), PREV.decode(), "x = 1\n", '"""unclosed\nx = 1\n', "\n\n" + NEW.decode(), ""]
    for text in samples:
        assert code_sha256(text) == smoke_run.code_sha256(text) == adapt_record.code_sha256(text)
    assert code_sha256(NEW.decode()) == code_sha256(NEW.decode().replace("pending", "91/100"))
    assert code_sha256(NEW.decode()) != code_sha256(NEW.decode() + "x = 1\n")


def test_the_file_hash_is_of_bytes():
    r"""`git show` and the scanner both hand over bytes, so a `\r\n` file hashes as it is stored."""
    assert file_sha256(NEW) == code_sha256(NEW.decode())
    assert file_sha256(NEW.replace(b"\n", b"\r\n")) != file_sha256(NEW)
    assert file_sha256(None) is None and file_sha256(b"\xff\xfe not utf-8") is None


@pytest.mark.parametrize(
    ("head", "main", "why"),
    [
        (NEW + b"x = 1\n", PREV, "head"),  # a push after the scan
        (None, PREV, "head"),  # no file at the head
        (b"\xff\xfe not utf-8", PREV, "head"),  # a head the scanner could not have read
        (NEW, PREV + b"x = 1\n", "main"),  # main moved since the scan
        (NEW, None, "main"),  # the record has a predecessor, main has none
    ],
    ids=["head-changed", "no-head", "head-not-utf-8", "main-changed", "no-main"],
)
def test_a_record_of_other_code_is_stale(head, main, why):
    verdict = _assess(_record(), head=head, main=main)
    assert (verdict.status, verdict.why, verdict.added) == ("stale", why, ())


def test_a_first_generation_record_is_stale_once_main_holds_the_file():
    verdict = _assess(_record(prev=None, prev_sha256=None))
    assert (verdict.status, verdict.why) == ("stale", "main")


# --- the record must be the scanner's --------------------------------------------------------------


@pytest.mark.parametrize(
    ("record", "why"),
    [
        (["not", "an", "object"], "shape"),
        (_record(version=1), "version"),
        (_record(version=True), "version"),
        (_record(version="2"), "version"),
        (_record(spec_id="line-basic"), "pair"),
        (_record(library="bokeh"), "pair"),
        (_record(language="r"), "pair"),
        (_record(new=_side("refused", [KEY])), "side"),
        (_record(new={**_side("blocked"), "refusals": KEY}), "side"),
        (_record(new=_side("blocked", ["open('notes.txt')"])), "side"),
        (_record(new=_side("blocked", ["banned--name"])), "side"),
        (_record(new=_side("blocked", [f"security:rule-{n}" for n in range(65)])), "side"),
        (_record(new={**_side("blocked", [KEY]), "spec_refused": "no"}), "side"),
        (_record(prev="coupled"), "side"),
        (_record(new_sha256=None), "hash"),
        (_record(new_sha256="abc"), "hash"),
        (_record(prev_sha256=None), "hash"),
    ],
)
def test_anything_else_is_invalid(record, why):
    verdict = _assess(record)
    assert (verdict.status, verdict.why, verdict.added) == ("invalid", why, ())


def test_the_record_file_may_be_absent_empty_or_broken(tmp_path):
    path = tmp_path / "readiness.json"
    arguments = {"spec_id": SPEC, "library": LIB, "head": NEW, "main": PREV}
    assert check(str(path), **arguments) == Verdict("missing")
    path.write_text("", encoding="utf-8")
    assert check(str(path), **arguments) == Verdict("missing")
    path.write_text("{not json", encoding="utf-8")
    assert check(str(path), **arguments) == Verdict("invalid", why="unparsable")
    path.write_text(json.dumps(_record()) + " " * readiness_record.RECORD_LIMIT, encoding="utf-8")
    assert check(str(path), **arguments) == Verdict("invalid", why="unparsable")
    path.write_text(json.dumps(_record()), encoding="utf-8")
    assert check(str(path), **arguments).status == "regression"


# --- the command -----------------------------------------------------------------------------------


def _files(tmp_path: Path, record: Any = None) -> list[str]:
    (tmp_path / "head.py").write_bytes(NEW)
    (tmp_path / "main.py").write_bytes(PREV)
    if record is not None:
        (tmp_path / "readiness.json").write_text(json.dumps(record), encoding="utf-8")
    arguments = ["check", "--record", str(tmp_path / "readiness.json"), "--new", str(tmp_path / "head.py")]
    return [*arguments, "--prev", str(tmp_path / "main.py"), "--spec-id", SPEC, "--library", LIB]


def test_check_prints_the_line_and_writes_the_summary_the_output_and_the_verdict(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    code = readiness_record.main([*_files(tmp_path, _record()), "--out", str(tmp_path / "verdict.json")])
    assert code == 0
    assert capsys.readouterr().out.strip() == (
        "::warning::readiness_check spec=scatter-basic lib=altair status=regression new=blocked prev=coupled "
        "added=security:banned-attribute removed=none"
    )
    assert (tmp_path / "summary").read_text(encoding="utf-8") == (
        "**Readiness check:** regression: security:banned-attribute (new blocked, predecessor coupled)\n"
    )
    assert (tmp_path / "output").read_text(encoding="utf-8") == "status=regression\n"
    assert json.loads((tmp_path / "verdict.json").read_text(encoding="utf-8")) == {
        "version": 1,
        "status": "regression",
        "new": "blocked",
        "prev": "coupled",
        "added": [KEY],
        "removed": [],
    }


def test_check_without_a_record_or_a_predecessor_still_exits_0(tmp_path, monkeypatch, capsys):
    """No summary file, no output file, no --out and no --prev: the line alone."""
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    arguments = ["check", "--record", str(tmp_path / "absent.json"), "--new", str(tmp_path / "absent.py")]
    assert readiness_record.main([*arguments, "--spec-id", SPEC, "--library", LIB]) == 0
    assert capsys.readouterr().out.strip() == (
        "::notice::readiness_check spec=scatter-basic lib=altair status=missing new=n/a prev=n/a "
        "added=none removed=none"
    )
    assert list(tmp_path.iterdir()) == []


def test_a_stale_record_says_why_in_fixed_words(tmp_path, capsys):
    record = _record(new_sha256="0" * 64)
    assert readiness_record.main(_files(tmp_path, record)) == 0
    assert (
        capsys.readouterr()
        .out.strip()
        .endswith("status=stale new=blocked prev=coupled added=none removed=none why=head")
    )


@pytest.mark.parametrize(
    ("verdict", "line"),
    [
        (Verdict("none", new="blocked", prev="blocked"), "no new refusal (new blocked, predecessor blocked)"),
        (Verdict("first_generation", new="clean"), "first generation (new clean)"),
        (Verdict("excluded"), "excluded (a map spec, which the chat refuses whatever the code holds)"),
        (Verdict("unreadable"), "unreadable (the scan had no new file, or the library has no Python profile)"),
        (Verdict("missing"), "missing (no readiness record is staged)"),
        (Verdict("stale", why="main"), "stale (the record's predecessor is not the implementation on origin/main)"),
        (Verdict("invalid", why="version"), "invalid (the record has another version than this reader knows)"),
    ],
)
def test_every_status_has_a_summary_line(verdict, line):
    assert readiness_record.summary_line(verdict) == f"**Readiness check:** {line}"


def test_every_reason_has_its_words():
    reasons = {"unparsable", "shape", "version", "pair", "side", "hash", "head", "main"}
    assert set(readiness_record.WHY_TEXT) == reasons


# --- the gate: only a regression keeps -------------------------------------------------------------

REGRESSION = Readiness(status="regression", new="blocked", prev="coupled", added=(KEY,))


def test_a_readiness_regression_turns_a_merge_into_keep():
    result = decide(_inp(readiness=REGRESSION))
    assert (result.verdict, result.code) == (KEEP, "readiness_regression")
    assert result.reason == (
        "readiness regression: the agent chat's validator refuses the new source for security:banned-attribute, "
        "which it did not refuse the predecessor for, so the live implementation stays (without it: merge)"
    )
    assert result.readiness == REGRESSION


@pytest.mark.parametrize("status", [s for s in regen_gate.READINESS_STATUSES if s != "regression"])
def test_no_other_status_changes_the_decision(status):
    """A lost upload, a stale or a malformed record and a scan that could not run never refuse anything."""
    result = decide(_inp(readiness=Readiness(status=status)))
    assert (result.verdict, result.code) == (MERGE, "merge")
    assert result.readiness.status == status


def test_without_a_verdict_the_gate_decides_as_before():
    result = decide(_inp())
    assert (result.verdict, result.code, result.readiness) == (MERGE, "merge", Readiness())


def test_a_keep_keeps_its_own_code():
    result = decide(_inp(score=None, readiness=REGRESSION))
    assert (result.verdict, result.code) == (KEEP, "no_score")


def test_the_adapt_routes_merge_is_kept_too():
    """The review-free route merges without a review; a file the chat would refuse still does not go live."""
    assert decide(_adapt_inp()).code == "adapt_identity"
    result = decide(_adapt_inp(readiness=REGRESSION))
    assert (result.verdict, result.code) == (KEEP, "readiness_regression")
    assert result.reason.endswith("(without it: adapt_identity)")


def test_the_adapt_regression_comes_first_when_both_hold():
    inp = _adapt_inp(regen=_regen(), adapt=_adapt(prev="pass", new="fail"), readiness=REGRESSION)
    assert decide(inp).code == "adapt_regression"


def test_the_keep_returns_within_a_window_like_a_regression():
    """Without it the pair would queue behind the whole catalogue for a construct a second try rarely adds."""
    assert "readiness_regression" in REASON_CODES
    assert "readiness_regression" in regen_pick_pairs.RETURN_CODES
    assert "adapt_regression" not in regen_pick_pairs.RETURN_CODES


# --- the gate: its verdict file --------------------------------------------------------------------


def _verdict_file(tmp_path: Path, **overrides: Any) -> str:
    verdict = {"version": 1, "status": "regression", "new": "blocked", "prev": "coupled", "added": [KEY], "removed": []}
    verdict.update(overrides)
    path = tmp_path / "readiness-verdict.json"
    path.write_text(json.dumps(verdict), encoding="utf-8")
    return str(path)


def test_the_gate_loads_what_the_reader_wrote(tmp_path):
    assert load_readiness(_verdict_file(tmp_path)) == REGRESSION
    quiet = load_readiness(_verdict_file(tmp_path, status="none", added=[], removed=["no-theme", KEY]))
    assert quiet == Readiness(status="none", new="blocked", prev="coupled", removed=("no-theme", KEY))


def test_no_file_is_missing_and_never_a_keep(tmp_path):
    assert load_readiness("") == Readiness()
    assert load_readiness(str(tmp_path / "absent.json")) == Readiness()
    assert not Readiness().regression


@pytest.mark.parametrize(
    "overrides",
    [
        {"version": 2},
        {"version": True},
        {"status": "worse"},
        {"new": "refused"},
        {"prev": None},
        {"added": KEY},
        {"added": []},  # a regression names its keys
        {"status": "none"},  # and only a regression has added keys
        {"added": ["open('notes.txt')"]},
        {"added": ["banned--name"]},
        {"added": [f"security:rule-{n}" for n in range(65)]},
        {"removed": None},
    ],
    ids=lambda overrides: ",".join(f"{key}={str(value)[:24]}" for key, value in overrides.items()),
)
def test_a_verdict_that_is_not_the_readers_is_invalid_and_never_a_keep(tmp_path, overrides):
    readiness = load_readiness(_verdict_file(tmp_path, **overrides))
    assert readiness == Readiness(status="invalid") and not readiness.regression


def test_a_broken_verdict_file_is_invalid(tmp_path):
    path = tmp_path / "readiness-verdict.json"
    path.write_text("[1, 2]", encoding="utf-8")
    assert load_readiness(str(path)) == Readiness(status="invalid")
    path.write_text("{not json", encoding="utf-8")
    assert load_readiness(str(path)) == Readiness(status="invalid")


# --- the gate: record and comment ------------------------------------------------------------------


def _gate_record(readiness: Readiness | None = None) -> dict:
    inp = _inp() if readiness is None else _inp(readiness=readiness)
    return build_record(decide(inp), spec_id="scatter-annotated", library="altair", score=85, prev_stored=80)


def test_the_gate_record_carries_the_verdict_as_plain_tokens():
    two = Readiness(status="regression", new="blocked", prev="clean", added=("no-theme", KEY), removed=("syntax",))
    record = _gate_record(two)
    assert (record["verdict"], record["code"]) == ("keep", "readiness_regression")
    assert record["readiness"] == {
        "status": "regression",
        "new": "blocked",
        "prev": "clean",
        "added": "no-theme/security:banned-attribute",
        "removed": "syntax",
    }
    assert validate_record(record) == []
    assert parse_record_markers(render_record_marker(record)) == [record]


def test_a_gate_without_the_check_records_missing():
    record = _gate_record()
    assert record["readiness"] == {"status": "missing", "new": "n/a", "prev": "n/a", "added": "", "removed": ""}
    assert validate_record(record) == []


def test_a_record_written_before_the_check_still_validates():
    record = _gate_record()
    del record["readiness"]
    assert validate_record(record) == []


@pytest.mark.parametrize(
    ("block", "error"),
    [
        ("regression", "record.readiness must be an object with status, new, prev, added, removed"),
        ({"status": "none"}, "record.readiness must be an object with status, new, prev, added, removed"),
        ({**REGRESSION.to_record(), "status": "worse"}, "record.readiness.status is not one of READINESS_STATUSES"),
        ({**REGRESSION.to_record(), "new": "refused"}, "record.readiness.new is not a known status"),
        (
            {**REGRESSION.to_record(), "added": "banned--name"},
            "record.readiness.added must be refusal keys joined by '/'",
        ),
        (
            {**REGRESSION.to_record(), "removed": ["syntax"]},
            "record.readiness.removed must be refusal keys joined by '/'",
        ),
        (
            {**REGRESSION.to_record(), "added": ""},
            "record.readiness.added must name keys exactly when the status is regression",
        ),
        (
            {**Readiness(status="none").to_record(), "added": KEY},
            "record.readiness.added must name keys exactly when the status is regression",
        ),
    ],
)
def test_a_malformed_readiness_block_is_rejected(block, error):
    assert error in readiness_record_errors(block)
    assert error in validate_record({**_gate_record(), "readiness": block})


def test_the_comment_says_what_the_validator_refuses():
    result = decide(_inp(readiness=REGRESSION))
    summary = render_summary(result, "80", 85)
    assert (
        "**Readiness:** regression: the agent chat's validator refuses the new source for "
        "security:banned-attribute, which it did not refuse the predecessor for, so the live implementation stays"
    ) in summary
    assert "**Reason:** readiness regression: " in summary


@pytest.mark.parametrize(
    ("readiness", "line"),
    [
        (
            Readiness(status="none", new="blocked", prev="blocked"),
            "**Readiness:** no new refusal by the agent chat's validator (new blocked, predecessor blocked)",
        ),
        (Readiness(status="stale", new="blocked", prev="coupled"), "**Readiness:** not judged (stale)"),
        (Readiness(status="first_generation", new="clean"), "**Readiness:** not judged (first_generation)"),
    ],
)
def test_the_comment_names_every_verdict_it_was_given(readiness, line):
    assert line in render_summary(decide(_inp(readiness=readiness)), "80", 85).splitlines()


def test_a_gate_without_the_check_prints_the_old_comment():
    assert "Readiness" not in render_summary(decide(_inp()), "80", 85)


# --- the gate: the command -------------------------------------------------------------------------


def _decide(tmp_path, monkeypatch, capsys, extra: list[str]) -> tuple[str, dict[str, str], dict, str]:
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "gh_output"))
    (tmp_path / "review_regen.json").write_text(json.dumps(_regen()), encoding="utf-8")
    (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(NEW_CHECKLIST)), encoding="utf-8")
    (tmp_path / "weaknesses.json").write_text(json.dumps([{"id": "W2", "text": "legend", "class": "defect"}]))
    arguments = ["decide", "--spec-id", "scatter-annotated", "--library", "altair", "--score", "85"]
    arguments += ["--prev-stored", "80", "--regen-json", str(tmp_path / "review_regen.json")]
    arguments += ["--weaknesses-json", str(tmp_path / "weaknesses.json"), "--prev-renders", "available"]
    arguments += ["--record-out", str(tmp_path / "record.json"), "--summary-out", str(tmp_path / "summary.md")]
    assert main([*arguments, *extra]) == 0
    notice = next(line for line in capsys.readouterr().out.splitlines() if line.startswith("::notice::regen_gate"))
    record = json.loads((tmp_path / "record.json").read_text(encoding="utf-8"))
    return notice, _outputs(tmp_path / "gh_output"), record, (tmp_path / "summary.md").read_text(encoding="utf-8")


def test_decide_keeps_on_the_readers_regression(tmp_path, monkeypatch, capsys):
    notice, outputs, record, summary = _decide(tmp_path, monkeypatch, capsys, ["--readiness", _verdict_file(tmp_path)])
    assert " verdict=keep code=readiness_regression readiness=regression reason=readiness regression: " in notice
    assert (outputs["verdict"], outputs["code"], outputs["readiness"]) == ("keep", "readiness_regression", "regression")
    assert record["readiness"]["added"] == KEY and validate_record(record) == []
    assert "**Readiness:** regression: " in summary


def test_decide_merges_on_a_stale_verdict_and_says_so(tmp_path, monkeypatch, capsys):
    stale = _verdict_file(tmp_path, status="stale", added=[])
    notice, outputs, record, summary = _decide(tmp_path, monkeypatch, capsys, ["--readiness", stale])
    assert " verdict=merge code=merge readiness=stale reason=" in notice
    assert (outputs["verdict"], outputs["readiness"]) == ("merge", "stale")
    assert record["readiness"]["status"] == "stale"
    assert "**Readiness:** not judged (stale)" in summary


def test_decide_without_the_flag_prints_the_old_line(tmp_path, monkeypatch, capsys):
    notice, outputs, record, summary = _decide(tmp_path, monkeypatch, capsys, [])
    assert " verdict=merge code=merge reason=" in notice and "readiness=" not in notice
    assert outputs["readiness"] == "missing" and record["readiness"]["status"] == "missing"
    assert "Readiness" not in summary


# --- reader and gate stay together -----------------------------------------------------------------


def test_the_gate_knows_the_readers_statuses_and_keys():
    assert regen_gate.READINESS_STATUSES == readiness_record.STATUSES
    assert regen_gate.READINESS_SIDE_STATUSES == (*readiness_record.SIDE_STATUSES, readiness_record.NO_SIDE)
    assert regen_gate.READINESS_KEY_RE.pattern == readiness_record.KEY_RE.pattern
    assert regen_gate.READINESS_KEY_LIMIT == readiness_record.KEY_LIMIT
    assert regen_gate.READINESS_VERDICT_VERSION == readiness_record.VERDICT_VERSION
    assert regen_gate.READINESS_MISSING == Verdict("missing").status == Readiness().status


def test_the_reader_knows_the_scanners_record():
    from automation.scripts import readiness_scan

    assert readiness_record.RECORD_VERSION == readiness_scan.RECORD_VERSION
    sides = {readiness_scan._side(status)["status"] for status in readiness_record.SIDE_STATUSES}
    assert sides == set(readiness_record.SIDE_STATUSES)
    assert set(_side("clean")) == set(readiness_scan._side("clean"))


@pytest.mark.parametrize(
    "verdict",
    [
        Verdict("regression", new="blocked", prev="coupled", added=(KEY, "no-theme")),
        Verdict("none", new="blocked", prev="blocked", removed=("error:valueerror",)),
        Verdict("first_generation", new="clean"),
        Verdict("excluded", new="blocked", prev="blocked"),
        Verdict("unreadable"),
        Verdict("stale", new="coupled", prev="clean", why="head"),
        Verdict("invalid", why="side"),
        Verdict("missing"),
    ],
    ids=lambda verdict: verdict.status,
)
def test_every_verdict_the_reader_writes_loads_in_the_gate(tmp_path, verdict):
    path = tmp_path / "readiness-verdict.json"
    path.write_text(json.dumps(verdict.to_json()), encoding="utf-8")
    loaded = load_readiness(str(path))
    assert (loaded.status, loaded.new, loaded.prev) == (verdict.status, verdict.new, verdict.prev)
    assert (loaded.added, loaded.removed) == (tuple(sorted(verdict.added)), tuple(sorted(verdict.removed)))
    assert readiness_record_errors(loaded.to_record()) == []
