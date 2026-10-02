"""Tests for automation.scripts.regen_writeback — a kept regeneration stores its re-score.

The write-back path: `check` (review_prev.json against review_regen.json's
prev_checklist), `apply` (the metadata writer's YAML, and the score in the
Quality header), `verify-diff` (only the pair's review keys and header number
change), `check-pr` (the PR is the bot's and its score is the kept PR's gate
record) and `check-fresh` (main still holds the files the re-score judged).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import regen_writeback as wb
from automation.scripts.regen_gate import CRITERIA, GateInput, build_record, decide, render_record_marker
from core import constants


SPEC, LIB = "count-basic", "ggplot2"
META, IMPL = "plots/count-basic/metadata/r/ggplot2.yaml", "plots/count-basic/implementations/r/ggplot2.R"
# The re-score deducts a few items; the new render is irrelevant here.
PREV_CHECKLIST = {
    **CRITERIA,
    "VQ-02": 4,
    "VQ-07": 1,
    "DE-01": 5,
    "DE-02": 4,
    "DE-03": 3,
    "DQ-02": 4,
    "LM-01": 4,
    "LM-02": 3,
}
PREV_RESCORED = sum(PREV_CHECKLIST.values())
CATEGORY_KEYS = {
    "VQ": "visual_quality",
    "DE": "design_excellence",
    "SC": "spec_compliance",
    "DQ": "data_quality",
    "CQ": "code_quality",
    "LM": "library_mastery",
}
DEFECT = "VQ-02 (light): the BEAU-001 label overlaps the bubble above it by about 6 px → clear it by 4 px. Likely cause: vjust."
DESCRIPTION = (
    "Light render (plot-light.png):\n  Background: #FAF8F1\n\nDark render (plot-dark.png):\n  Background: #1A1A17"
)


def _checklist_json(scores: dict[str, int]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cid, score in scores.items():
        cat = out.setdefault(CATEGORY_KEYS[cid[:2]], {"score": 0, "max": 0, "items": []})
        top = CRITERIA[cid]
        cat["items"].append(
            {"id": cid, "name": cid, "score": score, "max": top, "passed": score == top, "comment": "c"}
        )
        cat["score"] += score
        cat["max"] += top
    return out


def _prev_review(**overrides: Any) -> dict[str, Any]:
    review = {
        "image_description": DESCRIPTION,
        "criteria_checklist": _checklist_json(PREV_CHECKLIST),
        "strengths": ["Counts come from ggplot2's own stat engine"],
        "weaknesses": [DEFECT, "Suggestion: a slightly larger legend title"],
        "verdict": "REJECTED",
    }
    review.update(overrides)
    return review


def _regen(**overrides: Any) -> dict[str, Any]:
    regen = {
        "prev_rescored": PREV_RESCORED,
        "prev_checklist": dict(PREV_CHECKLIST),
        "prev_weaknesses": [],
        "improvements": [],
        "regressions": [],
        "scenario_changed": False,
        "encodings_added": [],
        "change_request_applied": None,
    }
    regen.update(overrides)
    return regen


def _check(tmp_path: Path, capsys, prev_review: Any, regen: Any | None = None, raw: str | None = None):
    prev = tmp_path / "review_prev.json"
    prev.write_text(raw if raw is not None else json.dumps(prev_review), encoding="utf-8")
    regen_file = tmp_path / "review_regen.json"
    regen_file.write_text(json.dumps(_regen() if regen is None else regen), encoding="utf-8")
    code = wb.main(["check", "--prev-review", str(prev), "--regen-json", str(regen_file)])
    return code, capsys.readouterr().out


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


class TestCheck:
    def test_valid_file(self, tmp_path, capsys):
        code, out = _check(tmp_path, capsys, _prev_review())
        assert (code, out.strip()) == (0, "check: review_prev.json can be stored")

    def test_a_score_key_is_ignored(self, tmp_path, capsys):
        assert _check(tmp_path, capsys, _prev_review(score=91, quality_score=91))[0] == 0

    @pytest.mark.parametrize("key", ["image_description", "criteria_checklist", "strengths", "weaknesses"])
    def test_each_missing_key(self, tmp_path, capsys, key):
        review = _prev_review()
        del review[key]
        code, out = _check(tmp_path, capsys, review)
        assert code == 1
        assert key in out

    def test_a_missing_verdict_is_fine(self, tmp_path, capsys):
        """The reviewer writes no verdict; the write-back sets the stored one."""
        review = _prev_review()
        del review["verdict"]
        assert _check(tmp_path, capsys, review)[0] == 0

    def test_empty_image_description(self, tmp_path, capsys):
        code, out = _check(tmp_path, capsys, _prev_review(image_description="  "))
        assert code == 1
        assert "image_description must be a non-empty string" in out

    def test_a_renamed_category_key(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["visual"] = checklist.pop("visual_quality")
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "criteria_checklist lacks visual_quality" in out
        assert "criteria_checklist has unknown keys visual" in out

    def test_a_wrong_category_maximum(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["code_quality"]["max"] = 12
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "criteria_checklist.code_quality.max must be 10 (got 12)" in out

    def test_a_wrong_item_maximum_and_a_missing_item(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["visual_quality"]["items"][0]["max"] = 10
        checklist["library_mastery"]["items"].pop()
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "(VQ-01) max must be 8 (got 10)" in out
        assert "criteria_checklist.library_mastery lacks the items LM-02" in out

    def test_a_float_score(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["visual_quality"]["items"][1]["score"] = 4.0
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "(VQ-02) score must be an integer from 0 to 6 (got 4.0)" in out

    def test_an_item_in_the_wrong_category(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["visual_quality"]["items"].append({"id": "DE-01", "score": 5, "max": 8})
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "items[8].id 'DE-01' is not a VQ criterion" in out

    @pytest.mark.parametrize(
        ("key", "value", "message"),
        [
            ("name", None, "(VQ-03) name must be a non-empty string (got None)"),
            ("name", " ", "(VQ-03) name must be a non-empty string (got ' ')"),
            ("name", 3, "(VQ-03) name must be a non-empty string (got 3)"),
            ("passed", None, "(VQ-03) passed must be true or false (got None)"),
            ("passed", "true", "(VQ-03) passed must be true or false (got 'true')"),
            ("passed", 1, "(VQ-03) passed must be true or false (got 1)"),
            ("comment", None, "(VQ-03) comment must be a string (got None)"),
            ("comment", ["c"], "(VQ-03) comment must be a string (got ['c'])"),
        ],
    )
    def test_an_item_field_missing_or_mistyped(self, tmp_path, capsys, key, value, message):
        """The stored checklist renders as is: a blank name or a missing passed reads as a failed criterion."""
        for drop in (True, False):
            checklist = _checklist_json(PREV_CHECKLIST)
            item = checklist["visual_quality"]["items"][2]
            if drop:
                del item[key]
            else:
                item[key] = value
            code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
            assert code == 1
            if drop:
                assert f"(VQ-03) {key} must be" in out
            else:
                assert message in out
            # A shape problem is not a score problem: the category total is still summed.
            assert "is not the sum" not in out

    def test_an_empty_comment_is_fine(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["visual_quality"]["items"][2]["comment"] = ""
        assert _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))[0] == 0

    def test_one_item_differs_from_prev_checklist(self, tmp_path, capsys):
        checklist = _checklist_json({**PREV_CHECKLIST, "VQ-02": 5})
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "criteria_checklist differs from prev_checklist at VQ-02 5 vs 4" in out
        assert "change review_prev.json, never prev_checklist" in out

    def test_a_category_score_that_is_not_the_sum_of_its_items(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["design_excellence"]["score"] += 2
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert (
            "criteria_checklist.design_excellence.score 14 is not the sum of its item scores (12): set it to 12" in out
        )

    def test_a_capped_rescore_keeps_the_item_sums(self, tmp_path, capsys):
        """A score cap (step 8) holds prev_rescored below the item total; the categories still sum their items."""
        assert PREV_RESCORED > 49
        assert _check(tmp_path, capsys, _prev_review(), regen=_regen(prev_rescored=49))[0] == 0

    def test_an_incomplete_category_is_not_summed(self, tmp_path, capsys):
        checklist = _checklist_json(PREV_CHECKLIST)
        checklist["library_mastery"]["items"].pop()
        code, out = _check(tmp_path, capsys, _prev_review(criteria_checklist=checklist))
        assert code == 1
        assert "library_mastery lacks the items LM-02" in out
        assert "is not the sum" not in out

    def test_no_prev_checklist_to_compare(self, tmp_path, capsys):
        regen = _regen()
        del regen["prev_checklist"]
        code, out = _check(tmp_path, capsys, _prev_review(), regen=regen)
        assert code == 1
        assert "review_regen.json has no prev_checklist" in out

    def test_a_suggestion_before_a_defect(self, tmp_path, capsys):
        code, out = _check(tmp_path, capsys, _prev_review(weaknesses=["Suggestion: a", DEFECT]))
        assert code == 1
        assert "weakness 2 is a defect line after a 'Suggestion:' line" in out

    def test_four_suggestions(self, tmp_path, capsys):
        code, out = _check(tmp_path, capsys, _prev_review(weaknesses=[f"Suggestion: {i}" for i in range(4)]))
        assert code == 1
        assert "4 'Suggestion:' lines; keep at most 3" in out

    @pytest.mark.parametrize("line", ["P1: " + DEFECT, "Legend too small", ""])
    def test_a_line_in_neither_format(self, tmp_path, capsys, line):
        code, out = _check(tmp_path, capsys, _prev_review(weaknesses=[line]))
        assert code == 1
        assert "weaknesses must be a list of non-empty strings" in out or "is neither a defect line" in out

    def test_no_weaknesses_is_fine(self, tmp_path, capsys):
        assert _check(tmp_path, capsys, _prev_review(weaknesses=[]))[0] == 0

    @pytest.mark.parametrize("verdict", ["OK", "approved", None])
    def test_a_bad_verdict(self, tmp_path, capsys, verdict):
        code, out = _check(tmp_path, capsys, _prev_review(verdict=verdict))
        assert code == 1
        assert "verdict, when present, must be APPROVED or REJECTED" in out

    def test_malformed_json(self, tmp_path, capsys):
        code, out = _check(tmp_path, capsys, None, raw="{not json")
        assert code == 1
        assert "unreadable" in out

    def test_a_list_instead_of_an_object(self, tmp_path, capsys):
        code, out = _check(tmp_path, capsys, [_prev_review()])
        assert code == 1
        assert "review_prev.json is not a JSON object" in out

    def test_missing_file(self, tmp_path, capsys):
        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen()), encoding="utf-8")
        assert wb.main(["check", "--prev-review", str(tmp_path / "no.json"), "--regen-json", str(regen)]) == 1
        assert "no.json missing" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# apply and the header
# ---------------------------------------------------------------------------

METADATA_TEXT = """\
library: ggplot2
language: r
specification_id: count-basic
created: '2026-08-11T06:48:31Z'
updated: '2026-09-28T11:00:18Z'
generated_by: claude-sonnet
workflow_run: 36411971313
issue: 2033
language_version: 4.4.1
library_version: 3.5.1
preview_url_light: https://storage.googleapis.com/anyplot-images/plots/count-basic/r/ggplot2/plot-light.png
preview_url_dark: https://storage.googleapis.com/anyplot-images/plots/count-basic/r/ggplot2/plot-dark.png
preview_html_light: null
preview_html_dark: null
quality_score: 87
review:
  strengths:
  - old strength
  weaknesses:
  - old weakness
  image_description: |-
    Light render: old

    Dark render: old
  criteria_checklist:
    visual_quality:
      score: 30
      max: 30
      items: []
  verdict: APPROVED
  model: claude-sonnet-5
  criteria_version: qc-0000000000.aqr-0000000000.sg-0000000000.lib-0000000000
  rendered_at: '2026-09-28T10:58:01Z'
impl_tags:
  dependencies: []
  techniques:
  - annotations
"""

HEADER_R = "#' anyplot.ai\n#' count-basic: Basic Count Plot\n#' Library: ggplot2 3.5.1 | R 4.4.1\n#' Quality: 87/100 | Updated: 2026-09-28\n\nlibrary(ggplot2)\n"


class TestApply:
    def test_only_the_listed_keys_change(self):
        old = yaml.safe_load(METADATA_TEXT)
        new = wb.apply_review(old, _prev_review(), 80, "claude-opus-5", "qc-a.aqr-b.sg-c.lib-d")
        assert new["quality_score"] == 80
        assert {k: v for k, v in new.items() if k not in ("quality_score", "review")} == {
            k: v for k, v in old.items() if k not in ("quality_score", "review")
        }
        assert list(new) == list(old)
        review = new["review"]
        assert review["image_description"] == DESCRIPTION
        assert review["criteria_checklist"] == _checklist_json(PREV_CHECKLIST)
        assert review["weaknesses"] == [DEFECT, "Suggestion: a slightly larger legend title"]
        # The kept implementation stays live: APPROVED, whatever the file says (REJECTED here).
        assert review["verdict"] == wb.KEPT_VERDICT == "APPROVED"
        assert review["model"] == "claude-opus-5"
        assert review["criteria_version"] == "qc-a.aqr-b.sg-c.lib-d"
        assert review["rendered_at"] == "2026-09-28T10:58:01Z"
        assert list(review) == list(old["review"])

    @pytest.mark.parametrize("value", ["", " ", "n/a"])
    def test_unresolved_provenance_removes_the_key(self, value):
        new = wb.apply_review(yaml.safe_load(METADATA_TEXT), _prev_review(), 80, value, value)
        assert "model" not in new["review"]
        assert "criteria_version" not in new["review"]
        assert new["review"]["rendered_at"] == "2026-09-28T10:58:01Z"

    def test_metadata_without_a_review(self):
        new = wb.apply_review({"library": "x", "quality_score": None}, _prev_review(), 80)
        assert new["quality_score"] == 80
        assert set(new["review"]) == {*wb.REVIEW_FIELDS, "verdict"}

    def test_refuses_an_incomplete_review(self):
        review = _prev_review()
        del review["strengths"]
        with pytest.raises(wb.WritebackError, match="lacks strengths"):
            wb.apply_review({}, review, 80)

    def test_a_review_without_a_verdict_is_stored_as_approved(self):
        review = _prev_review()
        del review["verdict"]
        assert wb.apply_review({}, review, 80)["review"]["verdict"] == "APPROVED"

    def test_cli_writes_the_writer_format(self, tmp_path, capsys):
        meta, impl, prev = tmp_path / "meta.yaml", tmp_path / "impl.R", tmp_path / "review_prev.json"
        meta.write_text(METADATA_TEXT, encoding="utf-8")
        impl.write_text(HEADER_R, encoding="utf-8")
        prev.write_text(json.dumps(_prev_review()), encoding="utf-8")
        args = ["apply", "--metadata", str(meta), "--prev-review", str(prev), "--score", "80"]
        assert wb.main([*args, "--model", "claude-opus-5", "--impl", str(impl)]) == 0
        text = meta.read_text(encoding="utf-8")
        # Timestamps stay quoted strings, multi-line text a literal block.
        assert "created: '2026-08-11T06:48:31Z'" in text
        assert "updated: '2026-09-28T11:00:18Z'" in text
        assert "rendered_at: '2026-09-28T10:58:01Z'" in text
        assert "  image_description: |-\n    Light render (plot-light.png):\n" in text
        data = yaml.safe_load(text)
        assert data["quality_score"] == 80
        assert data["review"]["model"] == "claude-opus-5"
        assert "criteria_version" not in data["review"]
        assert impl.read_text(encoding="utf-8") == HEADER_R.replace("Quality: 87/100", "Quality: 80/100")
        # A second run changes nothing.
        assert wb.main([*args, "--model", "claude-opus-5", "--impl", str(impl)]) == 0
        assert "nothing changed" in capsys.readouterr().out.splitlines()[-1]

    def test_cli_rejects_a_bad_score(self, tmp_path):
        meta, prev = tmp_path / "meta.yaml", tmp_path / "review_prev.json"
        meta.write_text(METADATA_TEXT, encoding="utf-8")
        prev.write_text(json.dumps(_prev_review()), encoding="utf-8")
        assert wb.main(["apply", "--metadata", str(meta), "--prev-review", str(prev), "--score", "n/a"]) == 2
        assert meta.read_text(encoding="utf-8") == METADATA_TEXT


class TestHeader:
    @pytest.mark.parametrize(
        "header",
        [
            '""" anyplot.ai\nscatter-basic: Basic Scatter\nLibrary: altair 5.5 | Python 3.13\nQuality: 92/100 | Updated: 2026-09-01\n"""\n',
            "#' anyplot.ai\n#' scatter-basic: Basic\n#' Library: ggplot2 3.5 | R 4.4\n#' Quality: 88/100 | Created: 2026-05-28\n",
            "# anyplot.ai\n# scatter-basic: Basic\n# Library: makie 0.21 | Julia 1.11\n# Quality: 7/100 | Created: 2026-05-28\n",
            "// anyplot.ai\n// scatter-basic: Basic\n// Library: d3 7.9 | JavaScript 22\n// Quality: 100 / 100 | Updated: 2026-08-24\n",
        ],
    )
    def test_only_the_number_changes(self, header):
        body = "import x\nprint('Quality: 50/100 is data, not a header')\n" * 3
        out = wb.regen_gate.set_header_score(header + body, 80)
        old_lines, new_lines = (header + body).splitlines(), out.splitlines()
        assert len(old_lines) == len(new_lines)
        changed = [(a, b) for a, b in zip(old_lines, new_lines, strict=True) if a != b]
        assert len(changed) == 1
        before, after = changed[0]
        assert "Quality: 80" in after
        assert before.split("Quality:")[0] == after.split("Quality:")[0]
        assert before.split("100")[-1] == after.split("100")[-1]
        assert wb.regen_gate.header_score(out) == 80
        assert wb.header_diff_problems(header + body, out) == []

    def test_only_the_first_of_two_headers_changes(self):
        """Four JavaScript files on main carry a stale second header below a `//#` directive."""
        text = (
            "// anyplot.ai\n// x: y\n// Library: echarts 5.5.1 | JavaScript 22\n// Quality: 84/100 | Created: 2026-06-18\n"
            "//# anyplot-orientation: square\n// anyplot.ai\n// Quality: 78/100 | Created: 2026-06-18\nconst a = 1;\n"
        )
        out = wb.regen_gate.set_header_score(text, 80)
        assert out == text.replace("84/100", "80/100")
        assert wb.regen_gate.header_score(out) == 80
        assert wb.header_diff_problems(text, out) == []
        # The sanitizer still hides both from the reviewer.
        assert "78/100" not in wb.regen_gate.sanitize_source(text)

    def test_a_file_without_a_header_is_left_alone(self):
        text = "library(ggplot2)\nprint('Quality: 50/100')\n"
        assert wb.regen_gate.set_header_score(text, 80) == text
        assert wb.regen_gate.header_score(text) is None

    def test_crlf_line_endings_stay(self):
        text = "#' anyplot.ai\r\n#' Quality: 91/100 | Created: 2026-08-11\r\nx <- 1\r\n"
        assert wb.regen_gate.set_header_score(text, 80) == text.replace("91/100", "80/100")

    @pytest.mark.parametrize("score", [101, -1, True, "80"])
    def test_refuses_a_non_score(self, score):
        with pytest.raises(ValueError):
            wb.regen_gate.set_header_score(HEADER_R, score)


# ---------------------------------------------------------------------------
# verify-diff
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return result.stdout.strip()


OTHER_META = "plots/bar-basic/metadata/r/ggplot2.yaml"


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    for path, text in ((META, METADATA_TEXT), (IMPL, HEADER_R), (OTHER_META, METADATA_TEXT), ("README.md", "x\n")):
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _branch(repo: Path, edits: dict[str, str], name: str = "wb") -> str:
    _git(repo, "checkout", "-q", "-b", name, "main")
    for path, text in edits.items():
        (repo / path).write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-q", "main")
    return head


def _written_back() -> str:
    return wb.dump_metadata(
        wb.apply_review(yaml.safe_load(METADATA_TEXT), _prev_review(), 80, "claude-opus-5", "qc-a.aqr-b.sg-c.lib-d")
    )


class TestVerifyDiff:
    def test_metadata_only(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back()})
        assert wb.verify_diff(repo, "main", head, SPEC, LIB) == []

    def test_metadata_and_the_header_line(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), IMPL: wb.regen_gate.set_header_score(HEADER_R, 80)})
        assert wb.verify_diff(repo, "main", head, SPEC, LIB) == []
        assert (
            wb.main(
                ["verify-diff", "--base", "main", "--head", head, "--spec", SPEC, "--library", LIB, "--repo", str(repo)]
            )
            == 0
        )

    def test_compares_against_the_merge_base(self, tmp_path):
        """main moving on elsewhere is not the branch's change."""
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back()})
        (repo / "README.md").write_text("y\n", encoding="utf-8")
        _git(repo, "commit", "-q", "-am", "main moves")
        assert wb.verify_diff(repo, "main", head, SPEC, LIB) == []

    def test_another_file(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), "README.md": "evil\n"})
        assert any("README.md changed" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    def test_another_pairs_metadata(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), OTHER_META: _written_back()})
        assert any(f"{OTHER_META} changed" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    @pytest.mark.parametrize(
        ("key", "value", "message"),
        [
            ("updated", "2026-10-01T00:00:00Z", "metadata key 'updated' changed"),
            ("impl_tags", {"techniques": []}, "metadata key 'impl_tags' changed"),
            ("generated_by", None, "metadata key 'generated_by' changed"),
        ],
    )
    def test_another_metadata_key(self, tmp_path, key, value, message):
        data = yaml.safe_load(_written_back())
        if value is None:
            del data[key]
        else:
            data[key] = value
        repo = _repo(tmp_path)
        head = _branch(repo, {META: wb.dump_metadata(data)})
        assert any(message in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    def test_another_review_key(self, tmp_path):
        data = yaml.safe_load(_written_back())
        data["review"]["rendered_at"] = "2026-10-01T00:00:00Z"
        repo = _repo(tmp_path)
        head = _branch(repo, {META: wb.dump_metadata(data)})
        assert any("review key 'rendered_at' changed" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    def test_a_second_changed_line_in_the_implementation(self, tmp_path):
        impl = wb.regen_gate.set_header_score(HEADER_R, 80).replace("library(ggplot2)", "library(evil)")
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), IMPL: impl})
        assert any(
            "2 lines of the implementation file changed" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB)
        )

    def test_a_changed_line_that_is_not_the_header(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), IMPL: HEADER_R.replace("library(ggplot2)", "library(evil)")})
        assert any("is not its Quality header line" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    def test_a_header_whose_date_changed(self, tmp_path):
        impl = HEADER_R.replace("Quality: 87/100 | Updated: 2026-09-28", "Quality: 80/100 | Updated: 2026-10-01")
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), IMPL: impl})
        assert any("only the number of the Quality header" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    def test_the_implementation_alone(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {IMPL: wb.regen_gate.set_header_score(HEADER_R, 80)})
        assert any(
            "did not change; there is nothing to write back" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB)
        )

    def test_a_deleted_metadata_file(self, tmp_path):
        repo = _repo(tmp_path)
        _git(repo, "checkout", "-q", "-b", "wb", "main")
        _git(repo, "rm", "-q", META)
        _git(repo, "commit", "-q", "-m", "delete")
        head = _git(repo, "rev-parse", "HEAD")
        assert any("has status D" in p for p in wb.verify_diff(repo, "main", head, SPEC, LIB))

    def test_a_non_integer_score(self):
        data = yaml.safe_load(_written_back())
        data["quality_score"] = "80"
        problems = wb.metadata_diff_problems(METADATA_TEXT, wb.dump_metadata(data))
        assert any("quality_score at the head must be an integer" in p for p in problems)


# ---------------------------------------------------------------------------
# check-pr
# ---------------------------------------------------------------------------

WB_PR = 12001
KEPT_PR = 11955
BRANCH = f"review-writeback/{SPEC}/{LIB}/{KEPT_PR}"
CREATED = "2026-09-28T12:00:00Z"


def _record(**overrides: Any) -> dict[str, Any]:
    result = decide(
        GateInput(
            spec_id=SPEC,
            score=78,
            regen={**_regen(prev_rescored=80), "regressions": [{"what": "legend lost"}]},
            prev_renders=True,
        )
    )
    record = build_record(result, spec_id=SPEC, library=LIB, score=78, prev_stored=87, pr=KEPT_PR)
    record["writeback"] = "opened"
    record.update(overrides)
    return record


def test_the_fixture_record_is_a_valid_marker():
    assert render_record_marker(_record()).startswith("<!-- regen-gate-record:v1 {")


class FakeGh:
    """`gh` by argv: the write-back PR, the kept PR and its comments; records every call."""

    def __init__(self, *, wb_pr: dict | None = None, kept: list[dict] | dict | None = None, comments=None):
        self.wb_pr = {
            "number": WB_PR,
            "state": "OPEN",
            "headRefName": BRANCH,
            "headRefOid": "a" * 40,
            "baseRefName": "main",
            "labels": [{"name": "review-writeback"}],
            "author": {"login": "app/github-actions", "is_bot": True},
            "createdAt": CREATED,
            "isCrossRepository": False,
            **(wb_pr or {}),
        }
        kept_default = {
            "number": KEPT_PR,
            "state": "CLOSED",
            "mergedAt": None,
            "labels": [{"name": "regen"}, {"name": "regen:kept"}],
            "headRefName": f"implementation/{SPEC}/{LIB}",
        }
        states = kept if isinstance(kept, list) else [kept or {}]
        self.kept = [{**kept_default, **k} for k in states]
        self.comments = comments if comments is not None else [self.comment(_record())]
        self.calls: list[list[str]] = []

    @staticmethod
    def comment(record: dict | None, user: str = "github-actions[bot]", at: str = "2026-09-28T12:00:40Z") -> dict:
        """A kept comment; the marker is written raw, so an invalid record can be one too."""
        marker = f"<!-- regen-gate-record:v1 {json.dumps(record, separators=(',', ':'))} -->" if record else ""
        return {"user": user, "created_at": at, "body": "## Kept\n\ntext\n\n" + marker}

    def __call__(self, argv: list[str]) -> str:
        self.calls.append(argv)
        if argv[:3] == ["pr", "view", str(WB_PR)]:
            return json.dumps(self.wb_pr)
        if argv[:3] == ["pr", "view", str(KEPT_PR)]:
            views = sum(1 for c in self.calls if c[:3] == ["pr", "view", str(KEPT_PR)])
            return json.dumps(self.kept[min(views, len(self.kept)) - 1])
        if argv[0] == "api" and f"issues/{KEPT_PR}/comments" in argv[2]:
            return "\n".join(json.dumps(c) for c in self.comments) + "\n"
        raise AssertionError(f"unexpected gh call {argv}")


def _head_files(score: int = 80, header: int | None = 80, review: dict | None = None):
    meta = yaml.safe_dump({"library": LIB, "quality_score": score, **({"review": review} if review else {})})
    impl = wb.regen_gate.set_header_score(HEADER_R, header) if header is not None else "library(ggplot2)\n"

    def read(sha: str, path: str) -> str | None:
        assert sha == "a" * 40
        return {META: meta, IMPL: impl}.get(path)

    return read


def _check_pr(gh: FakeGh, read=None, **kwargs) -> wb.PrCheck:
    sleeps: list[float] = []
    clock = iter(range(0, 10_000, 20))
    result = wb.check_pr(
        WB_PR, gh=gh, read_head=read or _head_files(), sleep=sleeps.append, clock=lambda: next(clock), **kwargs
    )
    result.outputs["_sleeps"] = str(len(sleeps))
    return result


class TestCheckPr:
    def test_ok(self):
        fetched: list[str] = []
        result = _check_pr(FakeGh(), fetch=fetched.append)
        assert result.status == "ok", result.reason
        assert fetched == [BRANCH]
        assert result.outputs["writeback_pr"] == "true"
        assert {k: result.outputs[k] for k in ("spec", "library", "language", "ext", "kept_pr", "score")} == {
            "spec": SPEC,
            "library": LIB,
            "language": "r",
            "ext": ".R",
            "kept_pr": str(KEPT_PR),
            "score": "80",
        }
        assert result.outputs["head_sha"] == "a" * 40

    def test_a_file_without_a_header_needs_only_the_metadata(self):
        assert _check_pr(FakeGh(), read=_head_files(header=None)).status == "ok"

    @pytest.mark.parametrize(
        ("wb_pr", "why"),
        [
            ({"state": "CLOSED"}, "is not OPEN"),
            ({"state": "MERGED"}, "is not OPEN"),
            ({"headRefName": f"implementation/{SPEC}/{LIB}"}, "is not review-writeback/"),
            ({"headRefName": f"review-writeback/{SPEC}/{LIB}/x1"}, "is not review-writeback/"),
            ({"labels": []}, "no review-writeback label"),
            ({"author": {"login": "someone"}}, "author 'someone'"),
            ({"isCrossRepository": True}, "another repository"),
        ],
    )
    def test_not_a_writeback_pr_is_a_noop(self, wb_pr, why):
        result = _check_pr(FakeGh(wb_pr=wb_pr))
        assert result.status == "noop"
        assert why in result.reason
        assert result.outputs["writeback_pr"] == "false"

    @pytest.mark.parametrize(
        ("kwargs", "why"),
        [
            ({"kept": {"state": "MERGED", "mergedAt": "2026-09-28T12:01:00Z"}}, "was merged"),
            ({"kept": {"labels": [{"name": "regen"}]}}, "has no regen:kept label"),
            ({"kept": {"headRefName": "implementation/bar-basic/ggplot2"}}, "not implementation/count-basic/ggplot2"),
            ({"comments": [FakeGh.comment(_record(verdict="merge", code="merge", writeback=None))]}, "no gate record"),
            ({"comments": [FakeGh.comment(_record(verdict="merge", code="merge"))]}, "no gate record"),
            (
                {"comments": [FakeGh.comment(_record(prev_rescored=81))]},
                "differs from the metadata's new quality_score",
            ),
            ({"comments": [FakeGh.comment(_record(writeback="stale"))]}, "writeback 'stale' is not 'opened'"),
            ({"comments": [FakeGh.comment(_record(lib="plotly"))]}, "it names another pair"),
            ({"comments": [FakeGh.comment(_record(pr=11956))]}, "it names PR 11956"),
            ({"comments": [FakeGh.comment(_record(), user="someone")]}, "no gate record by github-actions[bot]"),
            ({"comments": [FakeGh.comment(_record(), at="2026-09-28T11:59:00Z")]}, "no gate record"),
            ({"comments": [FakeGh.comment(None)]}, "no gate record"),
            ({"comments": []}, "no gate record"),
        ],
    )
    def test_each_failure(self, kwargs, why):
        result = _check_pr(FakeGh(**kwargs))
        assert result.status == "fail"
        assert why in result.reason, result.reason
        assert result.outputs["writeback_pr"] == "true"

    @pytest.mark.parametrize("base", ["release/v1", "", None])
    def test_a_writeback_pr_retargeted_away_from_main_fails(self, base):
        """gh pr merge merges into the PR's own base; the checks compare against main."""
        gh = FakeGh(wb_pr={"baseRefName": base})
        result = _check_pr(gh)
        assert (result.status, result.outputs["writeback_pr"]) == ("fail", "true")
        assert f"its base {base!r} is not main" in result.reason
        # It fails before the kept PR is read.
        assert not any(c[:3] == ["pr", "view", str(KEPT_PR)] for c in gh.calls)

    def test_a_record_with_a_merge_verdict_fails_even_when_valid(self):
        """A merge record cannot carry writeback, so it is skipped; without the key it names the verdict."""
        record = _record(verdict="merge", code="merge")
        del record["writeback"]
        result = _check_pr(FakeGh(comments=[FakeGh.comment(record)]))
        assert (result.status, "verdict 'merge' is not keep" in result.reason) == ("fail", True)

    def test_the_header_number_must_match(self):
        result = _check_pr(FakeGh(), read=_head_files(score=80, header=87))
        assert result.status == "fail"
        assert "differs from the header number 87" in result.reason

    PROVENANCE = {"model": "claude-opus-5", "criteria_version": "qc-a.aqr-b.sg-c.lib-d"}

    def test_the_review_provenance_is_the_records(self):
        gh = FakeGh(comments=[FakeGh.comment(_record(**self.PROVENANCE))])
        assert _check_pr(gh, read=_head_files(review=dict(self.PROVENANCE))).status == "ok"

    @pytest.mark.parametrize(
        ("review", "why"),
        [
            (
                {"model": "claude-sonnet-5", "criteria_version": "qc-a.aqr-b.sg-c.lib-d"},
                "model 'claude-opus-5' differs from the metadata's review.model 'claude-sonnet-5'",
            ),
            ({"model": "claude-opus-5"}, "criteria_version 'qc-a.aqr-b.sg-c.lib-d' differs"),
            (None, "model 'claude-opus-5' differs from the metadata's review.model None"),
        ],
    )
    def test_other_review_provenance_fails(self, review, why):
        gh = FakeGh(comments=[FakeGh.comment(_record(**self.PROVENANCE))])
        result = _check_pr(gh, read=_head_files(review=review))
        assert result.status == "fail"
        assert why in result.reason, result.reason

    def test_an_unresolved_model_is_n_a_on_both_sides(self):
        """apply removes an unresolved review.model; the record says n/a."""
        gh = FakeGh(comments=[FakeGh.comment(_record(model="n/a", criteria_version="qc-a.aqr-b.sg-c.lib-d"))])
        read = _head_files(review={"criteria_version": "qc-a.aqr-b.sg-c.lib-d"})
        assert _check_pr(gh, read=read).status == "ok"

    def test_the_metadata_must_carry_an_integer_score(self):
        result = _check_pr(FakeGh(), read=lambda sha, path: yaml.safe_dump({"quality_score": "80"}))
        assert result.status == "fail"
        assert "has no integer quality_score" in result.reason

    def test_the_first_record_after_the_pr_counts(self):
        """A rescue re-run's later record does not replace the one of the run that opened the PR."""
        comments = [
            FakeGh.comment(_record(prev_rescored=70), at="2026-09-27T10:00:00Z"),  # an older run
            FakeGh.comment(_record(), at="2026-09-28T12:00:40Z"),
            FakeGh.comment(_record(prev_rescored=75), at="2026-09-29T10:00:00Z"),
        ]
        assert _check_pr(FakeGh(comments=comments)).status == "ok"

    def test_waits_for_the_kept_pr_to_close(self):
        gh = FakeGh(kept=[{"state": "OPEN"}, {"state": "CLOSED"}])
        result = _check_pr(gh, wait=300)
        assert result.status == "ok", result.reason
        assert result.outputs["_sleeps"] == "1"

    def test_gives_up_after_the_wait(self):
        result = _check_pr(FakeGh(kept={"state": "OPEN"}), wait=60)
        assert result.status == "fail"
        assert "is still 'OPEN' after waiting 60 s" in result.reason

    def test_a_broken_command_after_the_identity_is_a_fail(self):
        def read(sha: str, path: str) -> str | None:
            raise wb.WritebackError("git show failed")

        result = _check_pr(FakeGh(), read=read)
        assert (result.status, result.reason, result.outputs["writeback_pr"]) == ("fail", "git show failed", "true")


# ---------------------------------------------------------------------------
# check-fresh
# ---------------------------------------------------------------------------


class TestCheckFresh:
    def test_fresh(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back()})
        (repo / "README.md").write_text("main moved elsewhere\n", encoding="utf-8")
        _git(repo, "commit", "-q", "-am", "unrelated")
        assert wb.fresh_problems(repo, "main", head, SPEC, LIB) == []

    def test_a_changed_file_outside_the_pair(self, tmp_path):
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back(), "README.md": "branch\n"})
        assert any("README.md changed on the branch" in p for p in wb.fresh_problems(repo, "main", head, SPEC, LIB))

    @pytest.mark.parametrize("path", [META, IMPL])
    def test_main_changed_a_pair_file_after_the_cut(self, tmp_path, path):
        """A non-conflicting change (a promotion rewriting a preview URL, a new line of code)."""
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back()})
        text = (repo / path).read_text(encoding="utf-8")
        (repo / path).write_text(text.replace("plot-dark.png", "plot-dark-v2.png") + "# tail\n", encoding="utf-8")
        _git(repo, "commit", "-q", "-am", "main changes the pair")
        problems = wb.fresh_problems(repo, "main", head, SPEC, LIB)
        assert any(f"main changed {path} after the write-back branch was cut" in p for p in problems)

    def _cli(self, monkeypatch, capsys, tmp_path, base: Any) -> tuple[int, str, list[tuple[str, ...]]]:
        repo = _repo(tmp_path)
        head = _branch(repo, {META: _written_back()}, name=BRANCH)
        _git(repo, "update-ref", "refs/remotes/origin/main", "main")
        view = {"state": "OPEN", "headRefName": BRANCH, "headRefOid": head, "baseRefName": base}
        fetches: list[tuple[str, ...]] = []
        monkeypatch.setattr(wb, "run_gh", lambda argv: json.dumps(view))
        monkeypatch.setattr(wb, "_git_fetch", lambda repo, *refspecs: fetches.append(refspecs))
        code = wb.main(["check-fresh", "--pr", str(WB_PR), "--head", head, "--repo", str(repo)])
        return code, capsys.readouterr().out, fetches

    def test_cli_fresh_on_main(self, monkeypatch, capsys, tmp_path):
        code, out, fetches = self._cli(monkeypatch, capsys, tmp_path, "main")
        assert (code, len(fetches)) == (0, 1), out
        assert "main still holds the pair's files" in out

    def test_cli_refuses_a_pr_retargeted_away_from_main(self, monkeypatch, capsys, tmp_path):
        """Re-checked before every merge attempt: the base can change after check-pr ran."""
        code, out, fetches = self._cli(monkeypatch, capsys, tmp_path, "release/v1")
        assert (code, fetches) == (2, [])
        assert "its base 'release/v1' is not main" in out


class TestLibraries:
    def test_the_map_mirrors_core_constants(self):
        assert wb.LIBRARY_LANGUAGE == constants.LIBRARY_LANGUAGES
        for library in constants.SUPPORTED_LIBRARIES:
            assert wb.ext_of(library) == constants.library_file_extension(library), library

    def test_every_library_name_fits_the_branch_pattern(self):
        for library in constants.SUPPORTED_LIBRARIES:
            assert wb.BRANCH_RE.match(f"review-writeback/scatter-basic/{library}/1"), library

    def test_an_unknown_library(self):
        with pytest.raises(wb.WritebackError, match="unknown library"):
            wb.pair_paths(SPEC, "excel")
