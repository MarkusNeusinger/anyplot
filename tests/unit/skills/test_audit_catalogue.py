"""The catalogue audit skill's scripts: pairs and git reading, candidate reasons, the vote count, the fix check, the page.

No test opens the production database, the bucket or GitHub: the vote query runs on the in-memory SQLite session of
`tests/conftest.py`, the git tests build a throwaway repository under `tmp_path`, and the page is built without
thumbnails. The rows and files are invented.
"""

from __future__ import annotations

import importlib
import json
import stat
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core.database import Feedback, FeedbackRepository


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "audit-catalogue"
UPDATED = datetime(2026, 11, 8, 4, 54, 13, tzinfo=UTC)


@pytest.fixture(scope="module")
def mods():
    """The skill's modules, imported as a script run imports its siblings."""
    sys.path.insert(0, str(SKILL_DIR))
    try:
        yield {
            name: importlib.import_module(name)
            for name in ("catalogue", "select_candidates", "check_fix", "build_page")
        }
    finally:
        sys.path.remove(str(SKILL_DIR))


def _metadata(score: float | None = 84, items: dict[str, tuple[int, int]] | None = None, weaknesses=None) -> dict:
    items = items if items is not None else {"VQ-01": (8, 8), "SC-01": (5, 5), "DE-01": (4, 8)}
    checklist = {"all": {"items": [{"id": key, "score": s, "max": m} for key, (s, m) in items.items()]}}
    review = {"criteria_checklist": checklist, "weaknesses": weaknesses or []}
    meta = {"updated": "2026-11-08T04:54:13Z", "library_version": "9.17.0", "review": review}
    if score is not None:
        meta["quality_score"] = score
    return meta


def _git(repo: Path, *args: str) -> str:
    command = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


def _commit(repo: Path, files: dict[str, str], message: str) -> str:
    for path, text in files.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    return path


# --- catalogue.py -----------------------------------------------------------------------------------------------


def test_a_pair_parses_with_or_without_its_language(mods) -> None:
    Pair = mods["catalogue"].Pair

    assert Pair.parse("scatter-basic/muix") == Pair("scatter-basic", "javascript", "muix")
    assert (
        Pair.parse("scatter-basic/python/matplotlib").impl_path
        == "plots/scatter-basic/implementations/python/matplotlib.py"
    )
    assert Pair.parse("scatter-basic/muix").impl_path.endswith("/javascript/muix.tsx")
    assert Pair.parse("scatter-basic/r/ggplot2").metadata_path == "plots/scatter-basic/metadata/r/ggplot2.yaml"
    for bad in ("scatter-basic", "scatter-basic/python/muix", "Scatter/muix", "scatter-basic/unknownlib"):
        with pytest.raises(ValueError):
            Pair.parse(bad)


def test_render_urls_carry_the_cache_buster(mods) -> None:
    pair = mods["catalogue"].Pair.parse("scatter-basic/muix")
    base = "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/javascript/muix"

    assert pair.render_url("dark") == f"{base}/plot-dark.png"
    assert pair.render_url("light", cache_buster=1731000000) == f"{base}/plot-light.png?cb=1731000000"
    assert pair.render_url("light", size=800, ext="webp", cache_buster=5) == f"{base}/plot-light_800.webp?cb=5"
    assert pair.site_url == "https://anyplot.ai/scatter-basic/javascript/muix"


def test_pairs_come_from_metadata_paths_only(mods) -> None:
    paths = [
        "plots/a-spec/metadata/python/matplotlib.yaml",
        "plots/a-spec/metadata/javascript/muix.yaml",
        "plots/a-spec/metadata/python/muix.yaml",  # the wrong language for the library
        "plots/a-spec/implementations/python/seaborn.py",
        "plots/a-spec/specification.yaml",
    ]

    assert [p.key for p in mods["catalogue"].pairs_from_paths(paths)] == [
        "a-spec/javascript/muix",
        "a-spec/python/matplotlib",
    ]


def test_batch_output_splits_per_name(mods) -> None:
    data = b"abc blob 5\nhello\nHEAD:x missing\ndef blob 0\n\n"

    assert mods["catalogue"].parse_batch(data, ["a", "x", "b"]) == {"a": b"hello", "x": None, "b": b""}


def test_the_git_tree_reads_a_commit_not_the_working_tree(mods, repo: Path) -> None:
    first = _commit(repo, {"plots/s/metadata/python/matplotlib.yaml": "quality_score: 80\n"}, "one")
    (repo / "plots/s/metadata/python/matplotlib.yaml").write_text("quality_score: 1\n", encoding="utf-8")
    tree = mods["catalogue"].GitTree(repo, "HEAD")

    assert tree.sha == first
    assert tree.paths() == ["plots/s/metadata/python/matplotlib.yaml"]
    assert tree.read_many(["plots/s/metadata/python/matplotlib.yaml", "plots/none"]) == {
        "plots/s/metadata/python/matplotlib.yaml": "quality_score: 80\n",
        "plots/none": None,
    }
    with pytest.raises(ValueError):
        mods["catalogue"].GitTree(repo, "no-such-ref")


def test_checklist_and_defect_lines(mods) -> None:
    meta = _metadata(weaknesses=["VQ-02 (both): labels collide → move them", "Suggestion: a heavier title"])

    assert [i["id"] for i in mods["catalogue"].checklist_items(meta)] == ["VQ-01", "SC-01", "DE-01"]
    assert mods["catalogue"].defect_lines(meta) == ["VQ-02 (both): labels collide → move them"]
    assert mods["catalogue"].checklist_items({}) == []


def test_round_files_stay_outside_checkouts_and_private(mods, tmp_path: Path) -> None:
    catalogue = mods["catalogue"]
    (tmp_path / "checkout" / ".git").mkdir(parents=True)

    assert not catalogue.outside_repository(tmp_path / "checkout" / "round" / "x.json")
    assert catalogue.outside_repository(tmp_path / "round" / "x.json")
    target = tmp_path / "round" / "deep" / "x.json"
    catalogue.write_private(target, "{}")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700


# --- select_candidates.py ---------------------------------------------------------------------------------------


def _codes(reasons) -> list[str]:
    return [reason.code for reason in reasons]


def test_score_reasons(mods) -> None:
    sc = mods["select_candidates"]

    assert _codes(sc.score_reasons(_metadata(score=None), below=85)) == ["no_score"]
    assert _codes(sc.score_reasons(_metadata(score=17), below=85)) == ["below_threshold"]
    capped = sc.score_reasons(_metadata(score=12, items={"VQ-02": (0, 6), "SC-01": (5, 5), "DE-01": (8, 8)}), below=10)
    assert _codes(capped) == ["capped", "technical_below_max"] and "VQ-02" in capped[0].detail
    assert _codes(sc.score_reasons(_metadata(score=30), below=10)) == ["checklist_mismatch"]
    shortfalls = sc.score_reasons(
        _metadata(score=17, items={"SC-01": (3, 5), "SC-02": (3, 4), "DQ-01": (5, 6), "DE-01": (6, 8)}), below=10
    )
    assert _codes(shortfalls) == ["plot_type_below_max", "spec_compliance_below_max", "technical_below_max"]
    assert shortfalls[0].detail == "SC-01 3/5"
    kept = sc.score_reasons(_metadata(score=17, weaknesses=["DQ-01 (code): r is 0.84", "Suggestion: x"]), below=10)
    assert _codes(kept) == ["residual_defects"] and "1 defect line" in kept[0].detail


def test_library_behind_compares_api_levels(mods) -> None:
    behind = mods["select_candidates"].library_behind

    assert behind("7.29.1", "9.17.0")
    assert behind("0.21.9", "0.22.0")  # before 1.0 the minor is the API level
    assert not behind("9.16.0", "9.17.0")
    assert not behind("9.17.0", "9.17.0")
    assert not behind(None, "9.17.0") and not behind("9.17.0", None)


def test_stale_reasons(mods) -> None:
    sc = mods["select_candidates"]
    now = UPDATED + timedelta(days=200)
    meta = {**_metadata(), "library_version": "7.29.1"}

    reasons = sc.stale_reasons(meta, pinned="9.17.0", now=now, older_than=timedelta(days=180))
    assert _codes(reasons) == ["library_behind", "old_update"]
    assert _codes(sc.stale_reasons(_metadata(), pinned="9.17.0", now=now, older_than=None)) == []


def test_gcs_reasons(mods) -> None:
    sc = mods["select_candidates"]
    fresh = UPDATED + timedelta(minutes=5)

    assert sc.gcs_reasons({"light": (200, fresh), "dark": (200, fresh)}, UPDATED) == []
    assert sc.gcs_reasons({"light": (200, UPDATED - timedelta(seconds=30)), "dark": (200, fresh)}, UPDATED) == []
    stale = sc.gcs_reasons({"light": (200, datetime(2026, 8, 4, tzinfo=UTC)), "dark": (404, None)}, UPDATED)
    assert _codes(stale) == ["render_stale", "render_missing"]
    assert _codes(sc.gcs_reasons({"light": (None, None)}, UPDATED)) == ["render_unchecked", "render_unchecked"]


def test_votes_split_at_the_last_update(mods) -> None:
    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    pair = Pair.parse("scatter-basic/muix")
    before, after = datetime(2026, 11, 1), datetime(2026, 11, 8, 6)  # naive UTC, as the table stores them
    rows = [
        ("scatter-basic", "muix", "javascript", "thumbs_down", before),
        ("scatter-basic", "muix", None, "thumbs_down", after),  # no language: the library's
        ("scatter-basic", "muix", "javascript", "thumbs_up", before),
        ("scatter-basic", "muix", "javascript", "thumbs_down", after),
        ("gone-spec", "muix", "javascript", "thumbs_down", after),  # not in the catalogue
    ]

    counts = sc.aggregate_votes(rows, {pair: UPDATED})
    assert list(counts) == [pair]
    assert counts[pair] == sc.VoteCounts(up=1, down=3, up_since_update=0, down_since_update=2)
    assert _codes(sc.vote_reasons(counts[pair], min_down=1)) == ["thumbs_down"]
    assert _codes(sc.vote_reasons(counts[pair], min_down=3)) == ["thumbs_down_old_version"]
    assert sc.vote_reasons(sc.VoteCounts(up=2, down=2), min_down=1) == []
    assert sc.vote_reasons(None, min_down=1) == []


async def test_the_vote_query_counts_as_the_repository_does(mods, test_session) -> None:
    """One vote per session and image, the newest; a session-less row counts once; page feedback never counts."""
    base = datetime(2026, 11, 8, 10, 0, 0)
    rows = [
        Feedback(
            reaction="thumbs_down",
            spec_id="a-spec",
            library_id="muix",
            language="javascript",
            session_id="s1",
            created_at=base,
        ),
        Feedback(
            reaction="thumbs_up",
            spec_id="a-spec",
            library_id="muix",
            language="javascript",
            session_id="s1",
            created_at=base + timedelta(minutes=1),
        ),
        Feedback(
            reaction="thumbs_down",
            spec_id="a-spec",
            library_id="muix",
            language="javascript",
            session_id="s2",
            created_at=base,
        ),
        Feedback(
            reaction="thumbs_down",
            spec_id="a-spec",
            library_id="muix",
            language="javascript",
            session_id=None,
            created_at=base,
        ),
        Feedback(
            reaction="thumbs_down",
            spec_id="a-spec",
            library_id="muix",
            language="javascript",
            session_id=None,
            created_at=base,
        ),
        Feedback(
            reaction="thumbs_up",
            spec_id="a-spec",
            library_id="d3",
            language="javascript",
            session_id="s1",
            created_at=base,
        ),
        Feedback(
            reaction="thumbs_down", spec_id="a-spec", message="the page is slow", session_id="s3", created_at=base
        ),
        Feedback(
            reaction="idea",
            spec_id="a-spec",
            library_id="muix",
            language="javascript",
            session_id="s4",
            created_at=base,
        ),
    ]
    test_session.add_all(rows)
    await test_session.commit()

    votes = await mods["select_candidates"].vote_rows(test_session)
    repository = FeedbackRepository(test_session)
    for library in ("muix", "d3"):
        mine = [v[3] for v in votes if v[1] == library]
        theirs = await repository.reaction_counts("a-spec", library, "javascript")
        assert {"thumbs_up": mine.count("thumbs_up"), "thumbs_down": mine.count("thumbs_down")} == theirs
    assert all(len(vote) == 5 for vote in votes)  # spec, library, language, reaction, time: no session id


def test_ranked_and_the_universe(mods) -> None:
    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    a, b, c = (sc.Candidate(Pair.parse(text)) for text in ("a-spec/muix", "b-spec/muix", "c-spec/d3"))
    a.reasons = [sc.Reason("scores", "below_threshold", "")]
    b.reasons = [sc.Reason("gcs", "render_stale", ""), sc.Reason("scores", "below_threshold", "")]

    assert [x.pair.spec for x in sc.ranked([a, b, c])] == ["b-spec", "a-spec"]
    assert b.rank == 7 and b.to_json()["reasons"][0]["code"] == "render_stale"
    assert sc.in_universe(c.pair, libraries={"d3"}, languages=set(), specs=set())
    assert not sc.in_universe(c.pair, libraries=set(), languages={"python"}, specs=set())


def test_the_selector_refuses_before_reading_anything(mods, tmp_path: Path, capsys) -> None:
    main = mods["select_candidates"].main
    (tmp_path / "co" / ".git").mkdir(parents=True)

    assert main(["--out", str(tmp_path / "x.json")]) == 2  # no source
    assert main(["--out", str(tmp_path / "co" / "x.json"), "--scores"]) == 2  # inside a checkout
    assert main(["--out", str(tmp_path / "x.json"), "--sweep"]) == 2  # a sweep needs a filter
    assert "--sweep needs" in capsys.readouterr().err


# --- check_fix.py -----------------------------------------------------------------------------------------------


def test_scope_problems(mods) -> None:
    cf = mods["check_fix"]
    named = {"plots/a/implementations/javascript/muix.tsx"}
    changed = [
        "plots/a/implementations/javascript/muix.tsx",
        "plots/b/implementations/javascript/muix.tsx",
        "plots/a/implementations/javascript/plot-light.png",
        "plots/a/metadata/javascript/muix.yaml",
        "node_modules",
        "plots/a/specification.md",
    ]

    problems, unnamed = cf.scope_problems(changed, named)
    assert unnamed == ["plots/b/implementations/javascript/muix.tsx"]
    assert [p.split(":", 1)[1].split(";")[0].strip() for p in problems] == [
        "a render",
        "metadata",
        "the node_modules link",
        "not an implementation file",
    ]


def test_the_header_through_quality_stays(mods) -> None:
    cf = mods["check_fix"]
    head = "// anyplot.ai\n// a: A\n// Library: muix 9.17.0 | JavaScript 22.23.4\n// Quality: 84/100 | Updated: 2026-11-08\n"

    assert cf.header_problems(head + "old();\n", head + "new();\n") == []
    rescored = head.replace("84/100", "90/100") + "new();\n"
    assert "Quality line changed" in cf.header_problems(head + "old();\n", rescored)[0]
    assert "line 1" in cf.header_problems(head, "new();\n" + head)[0]
    assert cf.header_problems(None, head + "x\n") == []  # a new file has no header to keep


def test_validator_problems(mods) -> None:
    cf = mods["check_fix"]
    clean = ("clean", [], [])
    banned = ("blocked", ["security: banned-name at line 66: a key a string builder returns"], [])

    assert cf.reason_key(banned[1][0]) == "security: banned-name"
    assert cf.validator_problems(clean, banned)[0][0].startswith("the agent chat would refuse it")
    assert cf.validator_problems(banned, banned) == ([], [])  # refused before, for the same rule
    assert cf.validator_problems(("blocked", ["map-spec: x is a map spec"], []), ("blocked", ["map-spec: x"], [])) == (
        [],
        [],
    )
    assert cf.validator_problems(("coupled", ["limits: 2 lines"], []), ("coupled", ["deprecated-api: 1 line"], []))[0]
    problems, warnings = cf.validator_problems(clean, ("coupled", ["limits: 2 lines"], []))
    assert problems == [] and warnings[0].startswith("clean before, coupled now")
    assert cf.validator_problems(None, ("error", ["SyntaxError: x"], []))[0]


def test_a_fix_is_read_against_where_it_was_cut(mods, repo: Path) -> None:
    """A fix passes against its own start; once main changes the same file, adopting it would revert that."""
    cf, catalogue = mods["check_fix"], mods["catalogue"]
    path = "plots/scatter-basic/implementations/javascript/chartjs.js"
    original = (REPO_ROOT / path).read_text(encoding="utf-8")
    base = _commit(repo, {path: original}, "base")
    _git(repo, "checkout", "-q", "-b", "fix")
    fixed = _commit(repo, {path: original + "\n// a comment the fix adds\n"}, "fix")
    pair = catalogue.Pair.parse("scatter-basic/chartjs")

    scope, unnamed, results = cf.check(
        [pair], tree=catalogue.GitTree(repo, fixed), base=catalogue.GitTree(repo, base), render_out=None
    )
    assert (scope, unnamed) == ([], [])
    assert results[0].ok and results[0].changed, results[0].problems

    _git(repo, "checkout", "-q", "main")
    moved = _commit(repo, {path: original.replace("anyplot.ai", "anyplot.ai ", 1)}, "main moves")
    _, _, results = cf.check(
        [pair], tree=catalogue.GitTree(repo, fixed), base=catalogue.GitTree(repo, moved), render_out=None
    )
    assert any("main changed this file" in problem for problem in results[0].problems)

    _, _, results = cf.check(
        [pair], tree=catalogue.GitTree(repo, base), base=catalogue.GitTree(repo, base), render_out=None
    )
    assert not results[0].changed


# --- build_page.py ----------------------------------------------------------------------------------------------


def _finding(pair: str, severity: str, what: str) -> dict:
    return {
        "pair": pair,
        "severity": severity,
        "defect_class": "text-over-data",
        "cause": "implementation",
        "what": what,
        "evidence": "seen in both themes",
        "fix": "Move the label.",
        "pr": 12639,
    }


def _audit() -> list[dict]:
    high = _finding("a-spec/javascript/muix", "high", "a map, not a cartogram <b>")
    medium = _finding("b-spec/javascript/muix", "medium", "legend says ahead")
    refuted = _finding("c-spec/javascript/muix", "medium", "dark contrast")
    lost = _finding("d-spec/javascript/muix", "high", "no verdict came back")
    low = _finding("e-spec/javascript/muix", "low", "label touches the path")
    verified = [
        {**high, "verdict": {"refuted": False, "severity": "high", "cause": "rubric", "reason": "plain to see"}},
        {**medium, "verdict": {"refuted": False, "severity": "medium", "cause": "implementation", "reason": "yes"}},
        {
            **refuted,
            "verdict": {"refuted": True, "severity": "low", "cause": "implementation", "reason": "the rim carries it"},
        },
    ]
    checked = [
        {"pair": "f-spec/javascript/muix", "verdict": "clean", "note": "88"},
        {"pair": "g-spec/javascript/muix", "verdict": "unchecked", "note": "no render"},
    ]
    return [
        {
            "group": 0,
            "pairs": [],
            "checked": checked,
            "findings": [high, medium, refuted, lost, low],
            "verified": verified,
        }
    ]


def test_findings_get_ids_in_page_order(mods) -> None:
    candidates = {
        "candidates": [
            {"pair": "a-spec/javascript/muix", "quality_score": 84, "reasons": [{"code": "plot_type_below_max"}]}
        ]
    }
    model = mods["build_page"].collect([_audit()], candidates)

    order = [(f["id"], f["pair"].split("/")[0], f["status"]) for f in model["findings"]]
    assert order == [
        ("F01", "a-spec", "confirmed"),
        ("F02", "b-spec", "confirmed"),
        ("F03", "d-spec", "low"),
        ("F04", "e-spec", "low"),
        ("F05", "c-spec", "refuted"),
    ]
    first = model["findings"][0]
    assert (first["cause"], first["quality_score"], first["reasons"]) == ("rubric", 84, ["plot_type_below_max"])
    assert model["findings"][2]["skeptic"].startswith("no skeptic verdict")
    assert model["clean"] == ["f-spec/javascript/muix"] and model["unchecked"] == ["g-spec/javascript/muix: no render"]


def test_the_page_is_self_contained_and_escaped(mods) -> None:
    bp = mods["build_page"]
    model = bp.collect([_audit()], {})
    page = bp.render_html(
        model,
        {"a-spec/javascript/muix": {"light": "data:image/webp;base64,AAAA"}},
        round_name="2026-11-08",
        cache_buster=7,
    )

    assert page.startswith("<title>Catalogue audit 2026-11-08</title>")
    assert "<script" not in page
    assert "a map, not a cartogram &lt;b&gt;" in page and "cartogram <b>" not in page
    assert 'src="data:image/webp;base64,AAAA"' in page and "plot-light.png?cb=7" in page
    assert "pull/12639" in page
    hosts = {part.split("/")[2] for part in page.split('"') if part.startswith("https://")}
    assert hosts <= {"fonts.googleapis.com", "anyplot.ai", "github.com", "storage.googleapis.com"}
    assert "prefers-color-scheme: dark" in page and ':root[data-theme="dark"]' in page


def test_build_page_refuses_a_round_inside_a_checkout(mods, tmp_path: Path) -> None:
    (tmp_path / "co" / ".git").mkdir(parents=True)
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_audit()), encoding="utf-8")

    assert mods["build_page"].main(["--round", str(tmp_path / "co" / "r"), "--audit", str(audit), "--no-images"]) == 2
    assert mods["build_page"].main(["--round", str(tmp_path / "r"), "--audit", str(audit), "--no-images"]) == 0
    written = json.loads((tmp_path / "r" / "findings.json").read_text(encoding="utf-8"))
    assert [f["id"] for f in written["findings"]] == ["F01", "F02", "F03", "F04", "F05"]
    assert (tmp_path / "r" / "page" / "audit.html").is_file()


# --- the shell scripts ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("script", ["dispatch.sh", "pkg_status.sh", "resume_paused.sh"])
def test_the_shell_scripts_parse(script: str) -> None:
    subprocess.run(["bash", "-n", str(SKILL_DIR / script)], check=True)


def test_the_dispatcher_refuses_without_a_queue(tmp_path: Path) -> None:
    result = subprocess.run(["bash", str(SKILL_DIR / "dispatch.sh"), str(tmp_path)], capture_output=True, text=True)

    assert result.returncode == 2 and "no " in result.stderr
