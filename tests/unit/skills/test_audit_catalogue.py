"""The catalogue audit skill's scripts: pairs and git reading, candidate reasons, the vote count, the fix check, the page.

No test opens the production database, the bucket or GitHub: the vote query runs on the in-memory SQLite session of
`tests/conftest.py`, the git tests build a throwaway repository under `tmp_path`, and the page is built without
thumbnails. The rows and files are invented.
"""

from __future__ import annotations

import importlib
import json
import os
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
            for name in ("catalogue", "select_candidates", "check_fix", "build_page", "verify_merged")
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


def test_a_plain_number_beside_the_categories_is_skipped(mods) -> None:
    meta = _metadata()
    meta["review"]["criteria_checklist"]["total"] = 84

    assert [i["id"] for i in mods["catalogue"].checklist_items(meta)] == ["VQ-01", "SC-01", "DE-01"]


def test_round_files_stay_outside_checkouts_and_private(mods, tmp_path: Path) -> None:
    catalogue = mods["catalogue"]
    (tmp_path / "checkout" / ".git").mkdir(parents=True)

    assert not catalogue.outside_repository(tmp_path / "checkout" / "round" / "x.json")
    assert catalogue.outside_repository(tmp_path / "round" / "x.json")
    target = tmp_path / "round" / "deep" / "x.json"
    catalogue.write_private(target, "{}")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700
    target.chmod(0o644)  # a file an earlier run or another tool left readable
    catalogue.write_private(target, "[]")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600 and target.read_text(encoding="utf-8") == "[]"


def test_the_pins_come_from_the_ref_not_the_working_tree(mods, repo: Path) -> None:
    """A worktree whose lock lags or leads the ref must not move the version a round compares against."""
    catalogue = mods["catalogue"]
    lock = {"packages": {"node_modules/@mui/x-charts": {"version": "9.17.0"}}}
    uv_lock = 'version = 1\n\n[[package]]\nname = "matplotlib"\nversion = "3.10.7"\n'
    _commit(repo, {".python-version": "3.14.0\n", "package-lock.json": json.dumps(lock), "uv.lock": uv_lock}, "pins")
    lock["packages"]["node_modules/@mui/x-charts"]["version"] = "7.29.1"
    (repo / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")  # not committed

    libraries, errors = catalogue.pinned_libraries(catalogue.GitTree(repo, "HEAD"))
    assert libraries["muix"] == "9.17.0" and libraries["matplotlib"] == "3.10.7"
    assert "makie" not in libraries and any(error.startswith("makie:") for error in errors)


def test_every_pin_file_the_reader_needs_is_read_from_the_ref(mods) -> None:
    """When `core.library_versions` starts reading another file, `PIN_FILES` must name it, or a pin goes missing."""
    from core.constants import LIBRARY_LANGUAGES

    catalogue = mods["catalogue"]
    libraries, errors = catalogue.pinned_libraries(catalogue.GitTree(REPO_ROOT, "HEAD"))

    assert errors == []
    assert set(libraries) == set(LIBRARY_LANGUAGES)


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
    weaknesses = ["DE-01 (both): a flat hierarchy", "VQ-01 (dark): fine at full marks", "Suggestion: DE-01 again"]
    kept = sc.score_reasons(_metadata(score=17, weaknesses=weaknesses), below=10)
    assert _codes(kept) == ["residual_defects"] and "1 defect line" in kept[0].detail and "DE-01" in kept[0].detail
    # a defect line on no item that lost points is the usual case, and no reason
    assert sc.score_reasons(_metadata(score=17, weaknesses=["DQ-01 (code): r is 0.84"]), below=10) == []


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


def _heads(answer, **overrides) -> dict:
    """A HEAD answer for every render of `catalogue.RENDERS`, by file name, with some replaced."""
    names = ("plot-light.png", "plot-dark.png", "plot-light_800.webp", "plot-dark_800.webp")
    return {name: overrides.get(name.removeprefix("plot-").replace(".", "_"), answer) for name in names}


def test_gcs_reasons(mods) -> None:
    sc = mods["select_candidates"]
    fresh = UPDATED + timedelta(minutes=5)

    assert sc.RENDER_NAMES == ("plot-light.png", "plot-dark.png", "plot-light_800.webp", "plot-dark_800.webp")
    assert sc.gcs_reasons(_heads((200, fresh)), UPDATED) == []
    # within the clock slack
    assert sc.gcs_reasons(_heads((200, fresh), light_png=(200, UPDATED - timedelta(seconds=30))), UPDATED) == []
    old = datetime(2026, 8, 4, tzinfo=UTC)
    stale = sc.gcs_reasons(_heads((200, fresh), light_png=(200, old), dark_png=(404, None)), UPDATED)
    assert _codes(stale) == ["render_stale", "render_missing"]
    assert _codes(sc.gcs_reasons({}, UPDATED)) == ["render_unchecked"] * 4
    # a 200 without Last-Modified proves nothing about freshness
    assert _codes(sc.gcs_reasons(_heads((200, fresh), dark_png=(200, None)), UPDATED)) == ["render_unchecked"]


def test_a_fresh_png_next_to_an_old_webp_is_stale(mods) -> None:
    """The site shows the `_800.webp`; a promotion that refreshed only the PNG still leaves the old image up."""
    sc = mods["select_candidates"]
    fresh, old = UPDATED + timedelta(minutes=5), datetime(2026, 8, 4, tzinfo=UTC)

    reasons = sc.gcs_reasons(_heads((200, fresh), light_800_webp=(200, old), dark_800_webp=(404, None)), UPDATED)
    assert _codes(reasons) == ["render_stale", "render_missing"]
    assert reasons[0].detail.startswith("plot-light_800.webp modified 2026-08-04")
    assert reasons[1].detail == "plot-dark_800.webp: HTTP 404"


def test_the_render_check_heads_both_pngs_and_both_webps_with_a_cache_buster(mods, monkeypatch) -> None:
    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    asked: list[str] = []

    def fake_head(url: str, *, attempts: int = 3):
        asked.append(url)
        return 200, UPDATED

    monkeypatch.setattr(sc, "head", fake_head)
    pair = Pair.parse("scatter-basic/muix")
    heads = sc.check_renders([pair], 1731000000)

    base = "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/javascript/muix"
    assert sorted(asked) == sorted(
        f"{base}/{name}?cb=1731000000"
        for name in ("plot-light.png", "plot-dark.png", "plot-light_800.webp", "plot-dark_800.webp")
    )
    assert set(heads[pair]) == set(sc.RENDER_NAMES)


def test_votes_split_at_the_last_update(mods) -> None:
    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    pair = Pair.parse("scatter-basic/muix")
    before, after = datetime(2026, 11, 1), datetime(2026, 11, 8, 6)  # naive UTC, as the table stores them
    rows = [
        ("scatter-basic", "muix", "javascript", "thumbs_down", before, None),
        ("scatter-basic", "muix", None, "thumbs_down", after, None),  # no language: the library's
        ("scatter-basic", "muix", "javascript", "thumbs_up", before, None),
        ("scatter-basic", "muix", "javascript", "thumbs_down", after, None),
        ("gone-spec", "muix", "javascript", "thumbs_down", after, None),  # not in the catalogue
    ]

    counts = sc.aggregate_votes(rows, {pair: UPDATED})
    assert list(counts) == [pair]
    assert counts[pair] == sc.VoteCounts(up=1, down=3, up_since_update=0, down_since_update=2)
    assert _codes(sc.vote_reasons(counts[pair], min_down=1)) == ["thumbs_down"]
    # two of the three thumbs down are on this version: no split side reaches three
    assert sc.vote_reasons(counts[pair], min_down=3) == []
    assert sc.vote_reasons(sc.VoteCounts(up=2, down=2), min_down=1) == []
    assert sc.vote_reasons(None, min_down=1) == []


def test_a_session_counts_once_on_each_side_of_the_update(mods) -> None:
    """A visitor who rated an older version may rate the new one: each vote counts on its own version, and of two
    votes on the same side only the newer one."""
    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    pair = Pair.parse("scatter-basic/muix")
    older, old, new = datetime(2026, 10, 30), datetime(2026, 11, 1), datetime(2026, 11, 8, 6)
    later = new + timedelta(minutes=1)
    rows = [
        # one session: two votes on older versions, then one on this version
        ("scatter-basic", "muix", "javascript", "thumbs_up", older, old),
        ("scatter-basic", "muix", "javascript", "thumbs_down", old, new),
        ("scatter-basic", "muix", "javascript", "thumbs_up", new, None),
        # another session voted twice on this version (rows from before the guard)
        ("scatter-basic", "muix", "javascript", "thumbs_up", new, later),
        ("scatter-basic", "muix", "javascript", "thumbs_down", later, None),
    ]

    assert sc.aggregate_votes(rows, {pair: UPDATED})[pair] == sc.VoteCounts(
        up=1, down=2, up_since_update=1, down_since_update=1
    )
    # without an `updated` there is one version, and each session's newest vote alone counts
    assert sc.aggregate_votes(rows, {pair: None})[pair] == sc.VoteCounts(
        up=1, down=1, up_since_update=1, down_since_update=1
    )


def test_a_pair_without_updated_has_one_version_for_the_votes(mods, repo: Path, tmp_path: Path, monkeypatch) -> None:
    """The vote boundary is `updated` alone, as the API's `impls.updated`: `created` is no version start, so a vote
    on a pair without `updated` is on its one version."""
    sc = mods["select_candidates"]
    _commit(repo, {"plots/a-spec/metadata/javascript/muix.yaml": "created: '2026-11-01T00:00:00Z'\n"}, "pair")

    async def votes():
        return [("a-spec", "muix", "javascript", "thumbs_down", datetime(2026, 10, 1), None)]

    monkeypatch.setattr(sc, "use_database_url", lambda env: True)
    monkeypatch.setattr(sc, "read_votes", votes)
    out = tmp_path / "round" / "candidates.json"

    assert sc.main(["--out", str(out), "--votes", "--repo", str(repo), "--ref", "HEAD"]) == 0
    (candidate,) = json.loads(out.read_text(encoding="utf-8"))["candidates"]
    assert candidate["votes"] == {"up": 0, "down": 1, "up_since_update": 0, "down_since_update": 1}
    assert [reason["code"] for reason in candidate["reasons"]] == ["thumbs_down"]


def test_old_version_votes_count_only_while_this_version_draws_no_net_thumbs_up(mods) -> None:
    sc = mods["select_candidates"]

    old = sc.vote_reasons(sc.VoteCounts(up=0, down=2), min_down=1)
    assert _codes(old) == ["thumbs_down_old_version"]
    assert old[0].detail.startswith("2 down, 0 up before the last update") and "0 down, 0 up since" in old[0].detail
    # three thumbs down before the update, one thumbs up after it: the update may have fixed it
    assert sc.vote_reasons(sc.VoteCounts(up=1, down=3, up_since_update=1, down_since_update=0), min_down=1) == []
    # one thumbs down since the update is below the threshold, so the three before it still count
    mixed = sc.VoteCounts(up=0, down=4, up_since_update=0, down_since_update=1)
    assert _codes(sc.vote_reasons(mixed, min_down=2)) == ["thumbs_down_old_version"]


async def test_the_vote_query_counts_as_the_repository_does(mods, test_session) -> None:
    """One vote per session and image, the newest; a session-less row counts once; page feedback never counts; a row
    without a language is the same image, so its session still counts once."""
    base = datetime(2026, 11, 8, 10, 0, 0)
    rows = [
        Feedback(
            reaction="thumbs_down",
            spec_id="a-spec",
            library_id="d3",
            language=None,
            session_id="s1",
            created_at=base + timedelta(minutes=5),
        ),
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

    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    votes = await sc.vote_rows(test_session)
    repository = FeedbackRepository(test_session)
    pairs = {library: Pair.parse(f"a-spec/{library}") for library in ("muix", "d3")}
    counts = sc.aggregate_votes(votes, dict.fromkeys(pairs.values()))
    for library, pair in pairs.items():
        theirs = await repository.reaction_counts("a-spec", library)
        assert {"thumbs_up": counts[pair].up, "thumbs_down": counts[pair].down} == theirs
    # spec, library, language, reaction, time and the next newer time: no session id
    assert all(len(vote) == 6 and isinstance(vote[5], datetime | None) for vote in votes)
    # s1's newest d3 row has no language: it replaces the older thumbs up, and still lands on the JavaScript pair
    assert counts[pairs["d3"]] == sc.VoteCounts(up=0, down=1, up_since_update=0, down_since_update=1)


async def test_the_split_at_the_update_counts_as_the_repository_does(mods, test_session) -> None:
    """Each side of the update counts the newest vote per session, as `reaction_counts(since=…)` and `(before=…)` do: a
    session that rated the old version and the new one counts on both, a repeat on one side once, and a vote cast in
    the second the version began is on it."""
    sc, Pair = mods["select_candidates"], mods["catalogue"].Pair
    start = datetime(2026, 11, 8, 12, 0, 0)  # naive UTC, as `impls.updated` stores it
    plan = [
        ("s1", "thumbs_down", -120, "javascript"),
        ("s1", "thumbs_up", -60, "javascript"),  # replaces s1's older vote on the old version
        ("s1", "thumbs_down", 60, "javascript"),  # s1 rates the new version too
        ("s2", "thumbs_up", -60, "javascript"),  # the old version only
        ("s3", "thumbs_down", 0, "javascript"),  # in the second the version began: on it
        ("s3", "thumbs_up", 120, "javascript"),  # a repeat from before the guard: the newest counts
        (None, "thumbs_down", -180, "javascript"),
        (None, "thumbs_down", 180, "javascript"),
        ("s4", "thumbs_up", 60, None),  # no language: still the JavaScript pair
    ]
    test_session.add_all(
        Feedback(
            reaction=reaction,
            spec_id="a-spec",
            library_id="muix",
            language=language,
            session_id=session,
            created_at=start + timedelta(minutes=minutes),
        )
        for session, reaction, minutes, language in plan
    )
    await test_session.commit()

    pair = Pair.parse("a-spec/muix")
    count = sc.aggregate_votes(await sc.vote_rows(test_session), {pair: start.replace(tzinfo=UTC)})[pair]
    repository = FeedbackRepository(test_session)
    current = await repository.reaction_counts("a-spec", "muix", since=start)
    earlier = await repository.reaction_counts("a-spec", "muix", before=start)

    assert current == {"thumbs_up": 2, "thumbs_down": 2}
    assert earlier == {"thumbs_up": 2, "thumbs_down": 1}
    assert {"thumbs_up": count.up_since_update, "thumbs_down": count.down_since_update} == current
    assert {"thumbs_up": count.up - count.up_since_update, "thumbs_down": count.down - count.down_since_update} == (
        earlier
    )


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


def test_a_render_inherits_no_secret_of_the_shell(mods, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("GH_TOKEN", "t")
    monkeypatch.setenv("UV_INDEX_PASSWORD", "p")
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "/base/.venv")
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "/pw")

    env = mods["check_fix"].render_env("dark", "python")
    assert "DATABASE_URL" not in env and "GH_TOKEN" not in env and "UV_INDEX_PASSWORD" not in env
    assert env["UV_PROJECT_ENVIRONMENT"] == "/base/.venv" and env["PLAYWRIGHT_BROWSERS_PATH"] == "/pw"
    assert (env["ANYPLOT_THEME"], env["MPLBACKEND"], env["PYTHON_DOTENV_DISABLED"]) == ("dark", "Agg", "1")
    assert "MPLBACKEND" not in mods["check_fix"].render_env("light", "javascript")


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
        ("F03", "d-spec", "unverified"),
        ("F04", "e-spec", "low"),
        ("F05", "c-spec", "refuted"),
    ]
    first = model["findings"][0]
    assert (first["cause"], first["quality_score"], first["reasons"]) == ("rubric", 84, ["plot_type_below_max"])
    lost = model["findings"][2]
    assert lost["skeptic"].startswith("no skeptic verdict") and lost["severity"] == "high"
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
    # the unverified high finding is a card of its own section, between the confirmed ones and the low notes
    confirmed, unverified, low = (page.index(h) for h in ("<h2>confirmed", "<h2>unverified", "<h2>low notes"))
    assert confirmed < page.index('id="F03"') and unverified < page.index('id="F03"') < low
    assert page.index('id="F02"') < unverified


def test_build_page_refuses_a_round_inside_a_checkout(mods, tmp_path: Path) -> None:
    (tmp_path / "co" / ".git").mkdir(parents=True)
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_audit()), encoding="utf-8")

    assert mods["build_page"].main(["--round", str(tmp_path / "co" / "r"), "--audit", str(audit), "--no-images"]) == 2
    assert mods["build_page"].main(["--round", str(tmp_path / "r"), "--audit", str(audit), "--no-images"]) == 0
    written = json.loads((tmp_path / "r" / "findings.json").read_text(encoding="utf-8"))
    assert [f["id"] for f in written["findings"]] == ["F01", "F02", "F03", "F04", "F05"]
    assert (tmp_path / "r" / "page" / "audit.html").is_file()


def test_a_named_page_keeps_the_rounds_findings_and_ids(mods, tmp_path: Path) -> None:
    """The re-audit gets a page and a findings file of its own, so the ids the owner picked from stay valid."""
    main = mods["build_page"].main
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_audit()), encoding="utf-8")
    round_dir = tmp_path / "r"
    assert main(["--round", str(round_dir), "--audit", str(audit), "--no-images"]) == 0
    before = (round_dir / "findings.json").read_text(encoding="utf-8")

    args = ["--round", str(round_dir), "--audit", str(audit), "--no-images", "--name", "reaudit", "--id-prefix", "R"]
    assert main(args) == 0
    assert (round_dir / "findings.json").read_text(encoding="utf-8") == before
    again = json.loads((round_dir / "findings-reaudit.json").read_text(encoding="utf-8"))
    assert [f["id"] for f in again["findings"]][:2] == ["R01", "R02"]
    page = (round_dir / "page" / "reaudit.html").read_text(encoding="utf-8")
    assert page.startswith("<title>Catalogue reaudit r</title>")
    assert main(["--round", str(round_dir), "--audit", str(audit), "--name", "../x"]) == 2
    assert main(["--round", str(round_dir)]) == 2  # neither --audit nor --fixes


def test_the_fixes_gallery_shows_production_next_to_the_local_render(mods, tmp_path: Path) -> None:
    from PIL import Image

    bp, Pair = mods["build_page"], mods["catalogue"].Pair
    model = bp.collect([_audit()], {})
    groups, unknown = bp.picked(model["findings"], ["F02", "F01", "F99", "F01"])
    assert unknown == ["F99"]
    assert [(key.split("/")[0], [e["id"] for e in entries]) for key, entries in groups] == [
        ("b-spec", ["F02"]),
        ("a-spec", ["F01"]),
    ]

    renders = tmp_path / "renders"
    for package in ("muix-1", "muix-1b"):
        target = renders / package / "a-spec" / "muix"
        target.mkdir(parents=True)
        Image.new("RGB", (3200, 1800), "white").save(target / "plot-light.png")
    newest = renders / "muix-1b" / "a-spec" / "muix" / "plot-light.png"
    os.utime(renders / "muix-1" / "a-spec" / "muix" / "plot-light.png", (1, 1))  # the package before the re-cut
    pair = Pair.parse("a-spec/muix")
    assert bp.local_render(renders, pair, "light") == newest
    assert bp.local_render(renders, pair, "dark") is None
    uri = bp.scaled(newest)
    assert uri and uri.startswith("data:image/webp;base64,") and len(uri) < 20_000

    page = bp.render_fixes_html(
        [*groups, ("a-spec/r/ggplot2", [model["findings"][0]])],
        {"a-spec/javascript/muix": {"light": "data:image/webp;base64,PROD"}},
        {"a-spec/javascript/muix": {"light": uri}},
        round_name="2026-11-08",
        cache_buster=7,
    )
    assert page.startswith("<title>Catalogue fixes 2026-11-08</title>") and "<script" not in page
    assert "data:image/webp;base64,PROD" in page and uri in page and "plot-light.png?cb=7" in page
    assert "the pipeline renders the regeneration" in page  # R has no local render
    assert "renders in the pipeline" in page  # the muix pair's dark theme and b-spec have none
    hosts = {part.split("/")[2] for part in page.split('"') if part.startswith("https://")}
    assert hosts <= {"fonts.googleapis.com", "anyplot.ai", "github.com", "storage.googleapis.com"}


def test_the_fixes_gallery_needs_known_ids(mods, tmp_path: Path, capsys) -> None:
    main = mods["build_page"].main
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_audit()), encoding="utf-8")
    round_dir = tmp_path / "r"

    assert main(["--round", str(round_dir), "--fixes", "F01"]) == 2  # no findings.json yet
    assert main(["--round", str(round_dir), "--audit", str(audit), "--no-images"]) == 0
    assert main(["--round", str(round_dir), "--fixes", "F01", "F42", "--no-images"]) == 2
    assert "F42" in capsys.readouterr().err
    assert main(["--round", str(round_dir), "--fixes", "F01", "F02", "--no-images"]) == 0
    assert (round_dir / "page" / "fixes.html").is_file()


def test_the_fixes_gallery_takes_the_re_audits_r_ids(mods, tmp_path: Path, capsys) -> None:
    """The owner may pick a re-audit finding (SKILL.md, step 9); its R id lives in findings-reaudit.json."""
    main = mods["build_page"].main
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps(_audit()), encoding="utf-8")
    reaudit = tmp_path / "reaudit.json"
    lost = _finding("h-spec/javascript/muix", "medium", "the repair brought the overlap back")
    verdict = {"refuted": False, "severity": "medium", "cause": "implementation", "reason": "still there"}
    reaudit.write_text(
        json.dumps(
            [
                {
                    "group": "reaudit",
                    "pairs": [],
                    "checked": [],
                    "findings": [lost],
                    "verified": [{**lost, "verdict": verdict}],
                }
            ]
        ),
        encoding="utf-8",
    )
    round_dir = tmp_path / "r"
    assert main(["--round", str(round_dir), "--audit", str(audit), "--no-images"]) == 0
    named = ["--round", str(round_dir), "--audit", str(reaudit), "--no-images", "--name", "reaudit", "--id-prefix", "R"]
    assert main(named) == 0

    assert main(["--round", str(round_dir), "--fixes", "F01", "R01", "--no-images"]) == 0
    page = (round_dir / "page" / "fixes.html").read_text(encoding="utf-8")
    assert "h-spec/javascript/muix" in page and "the repair brought the overlap back" in page and ">R01<" in page
    assert "a-spec/javascript/muix" in page and ">F01<" in page
    assert main(["--round", str(round_dir), "--fixes", "R02", "--no-images"]) == 2
    assert "findings.json, findings-reaudit.json" in capsys.readouterr().err

    # a second named page that reuses the F prefix makes F01 ambiguous, and leaves the R ids alone
    assert main([*named[:2], "--audit", str(audit), "--no-images", "--name", "other", "--id-prefix", "F"]) == 0
    assert main(["--round", str(round_dir), "--fixes", "F01", "--no-images"]) == 2
    assert "F01 in findings.json, findings-other.json" in capsys.readouterr().err
    assert main(["--round", str(round_dir), "--fixes", "R01", "--no-images"]) == 0


# --- the shell scripts ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("script", ["dispatch.sh", "pkg_status.sh", "resume_paused.sh"])
def test_the_shell_scripts_parse(script: str) -> None:
    subprocess.run(["bash", "-n", str(SKILL_DIR / script)], check=True)


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(SKILL_DIR / script), *args], capture_output=True, text=True, check=False)


def test_the_dispatcher_refuses_without_a_queue(tmp_path: Path) -> None:
    result = _run("dispatch.sh", str(tmp_path))

    assert result.returncode == 2 and "no " in result.stderr


def test_the_dispatcher_executes_only_the_approved_plan(tmp_path: Path) -> None:
    """The OK is bound to the dry run's token: no token, no plan, or a queue changed since, and nothing goes out."""
    (tmp_path / "queue.txt").write_text("regen ggplot2 a-spec Use the periods the spec names.\n", encoding="utf-8")

    assert "--approved" in _run("dispatch.sh", str(tmp_path), "--execute").stderr
    assert "dry run first" in _run("dispatch.sh", str(tmp_path), "--execute", "--approved", "abc").stderr
    (tmp_path / "queue.plan").write_text("# dispatch.sh plan: <line key> <the adopt line's SHA>\n", encoding="utf-8")
    token = subprocess.run(
        f"cat {tmp_path}/queue.txt {tmp_path}/queue.plan | sha1sum | cut -c1-12",
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    with (tmp_path / "queue.txt").open("a", encoding="utf-8") as queue:
        queue.write("regen makie b-spec A line added after the OK.\n")
    result = _run("dispatch.sh", str(tmp_path), "--execute", "--approved", token)
    assert result.returncode == 2 and "changed since the approved dry run" in result.stderr
    assert not (tmp_path / "dispatch.state").exists()


@pytest.mark.parametrize("script", ["dispatch.sh", "resume_paused.sh"])
def test_the_shell_scripts_refuse_a_round_inside_a_checkout(script: str, tmp_path: Path) -> None:
    round_dir = tmp_path / "co" / "rounds" / "2026-11-08"
    round_dir.mkdir(parents=True)
    (tmp_path / "co" / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")  # a worktree's .git is a file
    (round_dir / "queue.txt").write_text("regen ggplot2 a-spec Use the periods the spec names.\n", encoding="utf-8")
    (round_dir / "dispatch.state").write_text("k4 regen ggplot2 - 2026-11-08T10:03:00Z 1 a-spec\n", encoding="utf-8")

    runs = [_run(script, str(round_dir))]
    if script == "dispatch.sh":
        runs.append(_run(script, str(round_dir), "--execute", "--approved", "abc"))
    for result in runs:
        assert result.returncode == 2 and "inside a git checkout" in result.stderr
    assert not (round_dir / "dispatch.log").exists() and not (round_dir / "resume.log").exists()


def test_resuming_needs_this_rounds_dispatches_or_all_open(tmp_path: Path) -> None:
    result = _run("resume_paused.sh", str(tmp_path), "--repairs")

    assert result.returncode == 2 and "--all-open" in result.stderr
    # a state with only refused lines dispatched nothing, so it covers no resume
    (tmp_path / "dispatch.state").write_text("k1 refused - - 2026-11-08T10:00:00Z 0\n", encoding="utf-8")
    result = _run("resume_paused.sh", str(tmp_path), "--repairs")
    assert result.returncode == 2 and "no dispatched pair" in result.stderr


# --- verify_merged.py -------------------------------------------------------------------------------------------


def test_line_keys_match_the_dispatchers(mods) -> None:
    vm = mods["verify_merged"]
    line = "adopt  muix\tclaude/audit-2026-11-08-muix-1 claude-opus-5-5 a-spec b-spec  # the first package"
    bash = subprocess.run(
        [
            "bash",
            "-c",
            'line=${1%%#*}; read -r -a f <<< "$line"; printf %s "${f[*]}" | sha1sum | cut -c1-12',
            "-",
            line,
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert vm.line_key(vm.line_fields(line)) == bash
    models = vm.queue_models(f"{line}\nrerender d3 gemini-4-argon c-spec\nregen ggplot2 d-spec A hint.\n# a note\n")
    assert sorted(models.values()) == ["claude-opus-5-5", "gemini-4-argon"]


def test_the_state_yields_what_went_out(mods) -> None:
    vm = mods["verify_merged"]
    state = "\n".join(
        [
            "k1 adopt muix " + "a" * 40 + " 2026-11-08T10:00:00Z 2 a-spec b-spec",
            "k2 refused - - 2026-11-08T10:01:00Z 0",
            "k3 failed - - 2026-11-08T10:02:00Z 0",
            "k4 regen ggplot2 - 2026-11-08T10:03:00Z 1 d-spec",
        ]
    )

    sent = vm.read_state(state, {"k1": "claude-opus-5-5"})
    assert [(e.key, e.kind, e.specs, e.model) for e in sent] == [
        ("k1", "adopt", ("a-spec", "b-spec"), "claude-opus-5-5"),
        ("k4", "regen", ("d-spec",), None),
    ]
    assert sent[0].sha == "a" * 40 and sent[1].sha is None and sent[0].when == datetime(2026, 11, 8, 10, tzinfo=UTC)


def test_the_code_check_ignores_the_header_and_keeps_a_repair_that_kept_the_fix(mods) -> None:
    vm = mods["verify_merged"]
    head = "// anyplot.ai\n// Library: muix 7.29.1\n// Quality: 92/100 | Created: 2026-09-02\n"
    start = head + "axis({\n  label: X,\n});\n"
    fix = head.replace("92/100", "84/100") + "axis({\n  label: X,\n  height: 64,\n});\n"
    merged = fix.replace("7.29.1", "9.17.0").replace("84/100", "88/100")

    assert vm.code_check(merged, fix, start) == ([], [])
    # impl-repair added a line on top of the fix: every line the fix added is still in
    repaired = merged.replace("  height: 64,\n", "  height: 64,\n  disableTicks: true,\n")
    problems, notes = vm.code_check(repaired, fix, start)
    assert problems == [] and notes[0].startswith("code: changed after the fix") and "all 1 line(s)" in notes[0]
    # a later change dropped the fix's line: the pair is marked for a re-audit, not failed
    problems, _ = vm.code_check(merged.replace("  height: 64,\n", ""), fix, start)
    assert problems[0].startswith(f"{vm.MARKED} 1 of the 1 line(s) the fix added are not on main")
    assert "height: 64" in problems[0]
    assert vm.code_check(None, fix, start)[0][0].startswith("code:")
    assert vm.code_check(merged, None, start)[0][0].startswith("code:")


def _merged_meta() -> dict:
    return {"quality_score": 91, "updated": "2026-11-08T12:00:00Z", "generated_by": "claude-opus-5-5"}


def test_stored_copies_must_match_the_metadata(mods) -> None:
    vm = mods["verify_merged"]
    meta = _merged_meta()

    row = {"quality_score": 91.0, "updated": datetime(2026, 11, 8, 12, 0, 0), "generated_by": "claude-opus-5-5"}
    assert vm.stored_problems("database", row, meta) == []
    api = {"quality_score": 91.0, "updated": "2026-11-08T12:00:00", "generated_by": "claude-opus-5-5"}
    assert vm.stored_problems("api", api, meta) == []
    stale = {**row, "quality_score": 84.0, "updated": datetime(2026, 11, 1)}
    assert [p.split(":")[1].split()[0] for p in vm.stored_problems("database", stale, meta)] == [
        "quality_score",
        "updated",
    ]
    assert vm.stored_problems("api", None, meta) == ["api: no entry for the pair"]
    assert vm.metadata_problems(meta, model="gemini-4-argon")[0].startswith("metadata: generated_by")
    assert vm.metadata_problems({"updated": "x"}, model=None) == [
        "metadata: no quality_score",
        "metadata: no generated_by",
    ]


def test_a_library_version_behind_the_pin_is_a_metadata_problem(mods) -> None:
    """A migration round's merge must also carry the new library version (the header gets it only at the merge)."""
    vm = mods["verify_merged"]
    meta = {**_merged_meta(), "library_version": "7.29.1"}

    assert vm.metadata_problems(meta, model="claude-opus-5-5", pinned="9.17.0") == [
        "metadata: library_version 7.29.1, pinned 9.17.0 (an older API level)"
    ]
    assert vm.metadata_problems({**meta, "library_version": "9.16.0"}, model=None, pinned="9.17.0") == []
    assert vm.metadata_problems(meta, model=None, pinned=None) == []  # no pin known: nothing to compare


def test_a_pair_is_pending_until_merged_and_then_checked_end_to_end(mods) -> None:
    vm, Pair = mods["verify_merged"], mods["catalogue"].Pair
    when = datetime(2026, 11, 8, 10, tzinfo=UTC)
    entry = vm.Dispatched("k1", "adopt", "muix", "a" * 40, when, ("a-spec",), "claude-opus-5-5")
    pair = Pair.parse("a-spec/muix")
    meta = _merged_meta()
    good = _good_inputs(meta)
    old = datetime(2026, 8, 1, tzinfo=UTC)

    assert vm.evaluate(entry, pair, **good).status == "ok"
    pending = vm.evaluate(entry, pair, **{**good, "metadata": {**meta, "updated": "2026-11-07T00:00:00Z"}})
    assert pending.status == "pending" and not pending.route
    stale = vm.evaluate(
        entry, pair, **{**good, "heads": _heads((200, FRESH), light_png=(200, old), dark_png=(404, None))}
    )
    assert stale.status == "failed" and stale.route == "queue line: rerender muix claude-opus-5-5 a-spec"
    old_webp = vm.evaluate(entry, pair, **{**good, "heads": _heads((200, FRESH), dark_800_webp=(200, old))})
    assert old_webp.status == "failed" and old_webp.problems[0].startswith("renders: plot-dark_800.webp modified")
    r_entry = vm.Dispatched("k4", "regen", "ggplot2", None, when, ("a-spec",))
    r_stale = vm.evaluate(
        r_entry, Pair.parse("a-spec/ggplot2"), **{**good, "heads": _heads((200, FRESH), dark_png=(200, old))}
    )
    assert r_stale.route.startswith("queue line: regen ggplot2 a-spec ")
    unsynced = vm.evaluate(entry, pair, **{**good, "row": None})
    assert unsynced.problems == ["database: no entry for the pair"] and "sync" in unsynced.route
    assert vm.evaluate(entry, pair, **{**good, "row": None, "check_db": False}).status == "ok"
    silent = vm.evaluate(entry, pair, **{**good, "api_entry": None, "api_answered": False})
    assert silent.problems == ["api: no answer"] and "again" in silent.route
    gone = vm.evaluate(entry, pair, **{**good, "on_main": None})
    assert gone.status == "failed" and gone.route.startswith("read the merged PR")
    behind = vm.evaluate(entry, pair, **{**good, "metadata": {**meta, "library_version": "7.29.1"}, "pinned": "9.17.0"})
    assert behind.status == "failed" and behind.problems[0].startswith("metadata: library_version 7.29.1")
    kept = vm.evaluate(entry, pair, **{**good, "on_main": "x();\nrepaired();\n"})
    assert kept.status == "ok" and kept.notes and not kept.problems


FRESH = datetime(2026, 11, 8, 12, 5, tzinfo=UTC)


def _good_inputs(meta: dict) -> dict:
    """evaluate()'s inputs for a merged adopt pair that passes every check."""
    return {
        "metadata": meta,
        "on_main": "x();\n",
        "fix": "x();\n",
        "start": "w();\n",
        "row": {**meta, "updated": datetime(2026, 11, 8, 12)},
        "api_entry": {**meta, "updated": "2026-11-08T12:00:00"},
        "heads": _heads((200, FRESH)),
        "check_db": True,
    }


def test_a_fix_a_repair_changed_is_marked_for_a_re_audit_never_passed(mods) -> None:
    """When lines the fix added are gone from main, the pair neither passes nor fails: a skeptic re-audits it."""
    vm, Pair = mods["verify_merged"], mods["catalogue"].Pair
    entry = vm.Dispatched("k1", "adopt", "muix", "a" * 40, datetime(2026, 11, 8, 10, tzinfo=UTC), ("a-spec",))
    pair = Pair.parse("a-spec/muix")
    good = _good_inputs(_merged_meta())

    marked = vm.evaluate(entry, pair, **{**good, "on_main": "y();\n"})
    assert marked.status == "marked" and marked.route == vm.REAUDIT
    assert marked.problems[0].startswith(f"{vm.MARKED} 1 of the 1 line(s)")
    assert "never merge by hand" in marked.route and "?cb=" in marked.route
    # marked and stale: the render comes first, the re-audit after it
    both = vm.evaluate(
        entry, pair, **{**good, "on_main": "y();\n", "heads": _heads((200, FRESH), light_png=(404, None))}
    )
    assert both.status == "failed" and both.route.startswith("queue line: rerender muix")
    assert both.route.endswith("then the re-audit of its marked lines")
    assert vm.route(pair, [marked.problems[0]], {}) == vm.REAUDIT


def test_the_re_audit_claims_carry_the_pairs_findings_or_one_of_their_own(mods) -> None:
    vm = mods["verify_merged"]
    mark = f"{vm.MARKED} 2 of the 3 line(s) the fix added are not on main"
    marked = vm.PairResult("a-spec/javascript/muix", "k1", "adopt", status="marked", problems=[mark])
    lone = vm.PairResult("b-spec/javascript/muix", "k1", "adopt", status="marked", problems=[mark])
    fine = vm.PairResult("c-spec/javascript/muix", "k1", "adopt")
    first = {
        "id": "F01",
        "pair": "a-spec/javascript/muix",
        "status": "confirmed",
        "severity": "high",
        "what": "a cartogram",
        "fix": "draw symbols",
        "defect_class": "wrong-plot-type",
        "cause": "implementation",
        "evidence": "SC-01 3/5",
        "pr": 1,
    }
    findings = [
        first,
        {"id": "F07", "pair": "a-spec/javascript/muix", "status": "refuted", "what": "a refuted claim"},
        {"id": "F02", "pair": "c-spec/javascript/muix", "status": "confirmed", "what": "not marked"},
    ]

    claims = vm.reaudit_claims([marked, marked, lone, fine], findings)
    assert [(c["pair"].split("/")[0], c["finding_id"]) for c in claims] == [("a-spec", "F01"), ("b-spec", None)]
    assert claims[0]["what"] == "a cartogram" and claims[0]["fix"] == "draw symbols" and claims[0]["mark"] == mark
    assert claims[1]["severity"] == "medium" and claims[1]["evidence"] == mark
    assert vm.read_findings(Path("/nonexistent/findings.json")) == []


def test_a_running_sync_leaves_a_database_difference_pending(mods) -> None:
    """impl-merge triggers one sync per merge and the workflow queues them, so the row can lag the merge by minutes."""
    vm, Pair = mods["verify_merged"], mods["catalogue"].Pair
    merged_at = datetime(2026, 11, 8, 12, tzinfo=UTC)
    runs = [
        {"status": "completed", "createdAt": "2026-11-08T12:01:00Z"},
        {"status": "queued", "createdAt": "2026-11-08T12:03:00Z"},
    ]

    assert vm.sync_pending(runs, merged_at)
    assert not vm.sync_pending(runs[:1], merged_at)  # the one after the merge is done
    assert not vm.sync_pending([{"status": "in_progress", "createdAt": "2026-11-08T11:00:00Z"}], merged_at)
    assert vm.sync_pending([{"status": "in_progress", "createdAt": "2026-11-08T11:59:30Z"}], merged_at)  # clock slack
    assert not vm.sync_pending(None, merged_at)  # gh failed: no known run

    entry = vm.Dispatched("k1", "adopt", "muix", "a" * 40, datetime(2026, 11, 8, 10, tzinfo=UTC), ("a-spec",))
    pair = Pair.parse("a-spec/muix")
    good = _good_inputs(_merged_meta())
    waiting = vm.evaluate(entry, pair, **{**good, "row": None, "api_entry": None, "sync_active": True})
    assert waiting.status == "pending" and waiting.route == vm.SYNC_WAIT
    assert waiting.problems == ["database: no entry for the pair", "api: no entry for the pair"]
    assert vm.evaluate(entry, pair, **{**good, "row": None}).status == "failed"
    # a running sync does not excuse a stale render
    stale = vm.evaluate(entry, pair, **{**good, "row": None, "sync_active": True, "heads": _heads((404, None))})
    assert stale.status == "failed"


def test_a_pr_closed_without_a_merge_returns_the_finding_to_the_plan(mods) -> None:
    vm, Pair = mods["verify_merged"], mods["catalogue"].Pair
    since = datetime(2026, 11, 8, 10, tzinfo=UTC)

    def pr(number: int, spec: str, state: str, created: str) -> dict:
        return {"number": number, "title": f"feat(muix): implement {spec}", "state": state, "createdAt": created}

    prs = [
        pr(12700, "a-spec", "CLOSED", "2026-11-08T10:04:00Z"),
        pr(12650, "a-spec", "MERGED", "2026-11-07T10:00:00Z"),  # before the dispatch
        pr(12701, "b-spec", "OPEN", "2026-11-08T10:05:00Z"),
    ]

    assert vm.pr_outcome(prs, library="muix", spec="a-spec", since=since) == "closed"
    assert vm.pr_outcome(prs, library="muix", spec="b-spec", since=since) == "open"
    assert vm.pr_outcome(prs, library="muix", spec="c-spec", since=since) is None
    assert vm.pr_outcome(None, library="muix", spec="a-spec", since=since) is None
    superseded = [*prs, {**prs[0], "number": 12710, "state": "OPEN"}]
    assert vm.pr_outcome(superseded, library="muix", spec="a-spec", since=since) == "open"

    entry = vm.Dispatched("k1", "adopt", "muix", "a" * 40, since, ("a-spec",))
    not_merged = {**_good_inputs(_merged_meta()), "metadata": {**_merged_meta(), "updated": "2026-11-07T00:00:00Z"}}
    closed = vm.evaluate(entry, Pair.parse("a-spec/muix"), **not_merged, pr_state="closed")
    assert closed.status == "closed" and closed.route == vm.CLOSED and "never a hand merge" in closed.route
    assert vm.evaluate(entry, Pair.parse("a-spec/muix"), **not_merged, pr_state="open").status == "pending"


async def test_the_impl_rows_come_from_the_impls_table(mods, test_session) -> None:
    from core.database import Impl

    test_session.add_all(
        [
            Impl(
                spec_id="a-spec",
                library_id="muix",
                language_id="javascript",
                quality_score=91.0,
                updated=datetime(2026, 11, 8, 12),
                generated_by="claude-opus-5-5",
            ),
            Impl(spec_id="b-spec", library_id="muix", language_id="javascript", quality_score=70.0),
        ]
    )
    await test_session.commit()

    rows = await mods["verify_merged"].impl_rows(test_session, {"a-spec"})
    assert rows == {
        ("a-spec", "javascript", "muix"): {
            "quality_score": 91.0,
            "updated": datetime(2026, 11, 8, 12),
            "generated_by": "claude-opus-5-5",
        }
    }


def test_the_verifier_refuses_before_reading_anything(mods, tmp_path: Path, capsys) -> None:
    main = mods["verify_merged"].main
    (tmp_path / "co" / ".git").mkdir(parents=True)

    assert main(["--round", str(tmp_path / "co" / "r"), "--no-db"]) == 2  # inside a checkout
    assert main(["--round", str(tmp_path / "r"), "--no-db"]) == 2  # nothing dispatched
    assert "nothing was dispatched" in capsys.readouterr().err


def _reaudit_result(rows: list[tuple[dict, dict | None]]) -> str:
    """The audit workflow's re-audit return value, as the caller saves it: each claim next to its verdict."""
    return json.dumps(
        [{"group": "reaudit", "reaudit": [{"claim": claim, "verdict": verdict} for claim, verdict in rows]}]
    )


def _clean(clean: bool, reason: str = "seen") -> dict:
    return {"clean": clean, "severity": "medium", "cause": "implementation", "reason": reason}


def test_the_merged_state_changes_with_the_code_or_the_update(mods) -> None:
    state = mods["verify_merged"].merged_state
    meta = _merged_meta()

    assert state(meta, "x();\n") == state({**meta, "updated": "2026-11-08T12:00:00+00:00"}, "x();\n")
    assert state(meta, "x();\n") != state(meta, "y();\n")
    assert state(meta, "x();\n") != state({**meta, "updated": "2026-11-09T12:00:00Z"}, "x();\n")


def test_the_re_audit_results_are_read_per_pair_and_merged_state(mods, tmp_path: Path) -> None:
    vm = mods["verify_merged"]
    a, b, c, d = (f"{spec}/javascript/muix" for spec in ("a-spec", "b-spec", "c-spec", "d-spec"))
    first = [
        ({"pair": a, "merged": "s1", "finding_id": "F01"}, _clean(True, "boundary smooth")),
        ({"pair": a, "merged": "s1", "finding_id": "F02"}, _clean(True, "label clear")),
        ({"pair": b, "merged": "s1"}, _clean(True)),
        ({"pair": b, "merged": "s1"}, None),  # no verdict came back: no judgment of b in this file
        ({"pair": c, "merged": "s1"}, _clean(True)),
        ({"pair": d}, _clean(True)),  # a claim bound to no state
    ]
    (tmp_path / "audit-reaudit-20261108T120000Z.json").write_text(_reaudit_result(first), encoding="utf-8")
    later = [({"pair": c, "merged": "s1"}, _clean(False, "the overlap is back"))]
    (tmp_path / "audit-reaudit-20261108T130000Z.json").write_text(_reaudit_result(later), encoding="utf-8")
    (tmp_path / "audit-reaudit-20261108T140000Z.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "audit-run1.json").write_text(_reaudit_result(first), encoding="utf-8")  # not a re-audit result

    judged, notes = vm.reaudit_results(tmp_path)
    assert set(judged) == {(a, "s1"), (c, "s1")}
    assert judged[(a, "s1")].clean and judged[(a, "s1")].reason == "boundary smooth; label clear"
    assert judged[(a, "s1")].source == "audit-reaudit-20261108T120000Z.json"
    # a later finding wins over the earlier clean verdict: a second skeptic run never undoes a finding
    assert not judged[(c, "s1")].clean and judged[(c, "s1")].reason == "the overlap is back"
    assert notes == ["audit-reaudit-20261108T140000Z.json is not readable JSON, skipped"]


def test_a_re_audit_settles_a_marked_pair_at_the_state_it_judged(mods, tmp_path: Path) -> None:
    """Round trip: the verifier's claims go through the workflow and come back; clean passes, not clean waits for the
    owner and gets no new claim, and a later change to the pair needs a new re-audit."""
    vm, Pair = mods["verify_merged"], mods["catalogue"].Pair
    entry = vm.Dispatched("k1", "adopt", "muix", "a" * 40, datetime(2026, 11, 8, 10, tzinfo=UTC), ("a-spec",))
    pair = Pair.parse("a-spec/muix")
    meta = _merged_meta()
    marked_inputs = {**_good_inputs(meta), "on_main": "y();\n"}
    state = vm.merged_state(meta, "y();\n")
    finding = {"id": "F01", "pair": pair.key, "status": "confirmed", "severity": "high", "what": "a staircase"}

    marked = vm.evaluate(entry, pair, **marked_inputs, merged=state)
    assert marked.status == "marked" and marked.merged == state and not marked.reaudit
    claims = vm.reaudit_claims([marked], [finding])
    assert [(c["finding_id"], c["merged"]) for c in claims] == [("F01", state)]

    result_file = tmp_path / "audit-reaudit-20261108T120000Z.json"
    result_file.write_text(_reaudit_result([(claims[0], _clean(True, "the mesh is smooth"))]), encoding="utf-8")
    judged, _ = vm.reaudit_results(tmp_path)
    passed = vm.evaluate(entry, pair, **marked_inputs, merged=state, reaudit=judged.get((pair.key, state)))
    assert passed.status == "ok" and not passed.problems and passed.reaudit == "clean"
    assert passed.notes[-1].startswith("re-audit: a skeptic judged the merged pair clean (audit-reaudit-")
    assert "the mesh is smooth" in passed.notes[-1]

    # a later merge changed the pair: the clean verdict was for another state
    moved = vm.merged_state(meta, "z();\n")
    again = vm.evaluate(
        entry, pair, **{**marked_inputs, "on_main": "z();\n"}, merged=moved, reaudit=judged.get((pair.key, moved))
    )
    assert again.status == "marked" and again.route == vm.REAUDIT and vm.reaudit_claims([again], [finding])

    found = vm.Reaudit(False, result_file.name, "the staircase is back")
    held = vm.evaluate(entry, pair, **marked_inputs, merged=state, reaudit=found)
    assert held.status == "marked" and held.reaudit == "not clean" and held.route == vm.REAUDIT_FOUND
    assert "page/reaudit.html" in held.route and "never a hand merge" in held.route
    assert vm.reaudit_claims([held], [finding]) == []
    stale = vm.evaluate(
        entry,
        pair,
        **{**marked_inputs, "heads": _heads((200, FRESH), light_png=(404, None))},
        merged=state,
        reaudit=found,
    )
    assert stale.status == "failed" and stale.route.endswith("then the owner's pick of its re-audit finding")
    # a re-audit verdict lifts only a mark: a pair with no marked lines keeps its own status
    assert vm.evaluate(entry, pair, **_good_inputs(meta), merged=state, reaudit=found).status == "ok"
