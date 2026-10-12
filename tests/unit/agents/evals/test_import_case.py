"""`agents/evals/import_case.py`: a saved bundle or a stored feedback case becomes a promoted eval case.

Every test writes into a temporary promoted directory; none touches `agents/evals/.cases/`
or the committed fixtures.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agents.evals import import_case
from agents.evals.cases import MAX_CHANGE_REQUEST_CHARS, load_case
from agents.evals.import_case import (
    CREATE_PLOT_MESSAGE,
    EXPECTED_BY_REACTION,
    AmbiguousRequest,
    ImportRefused,
    build_case,
    change_request,
    main,
    plot_turns,
    read_bundle_file,
    read_case_dir,
    write_case,
)


BUNDLE_FILE = Path(__file__).with_name("session_bundle.json")
DATA = "Stunden,Punkte\n1.5,52\n2.0,58\n3.5,71\n"


@pytest.fixture
def promoted(tmp_path, monkeypatch) -> Path:
    """The promoted directory and the committed fixtures, both in `tmp_path`."""
    directory = tmp_path / ".cases"
    fixtures = tmp_path / "fixtures"
    (fixtures / "scatter-basic-matplotlib").mkdir(parents=True)
    monkeypatch.setattr(import_case, "PROMOTED_DIR", directory)
    monkeypatch.setattr(import_case, "FIXTURES_DIR", fixtures)
    return directory


def _bundle() -> dict:
    return json.loads(BUNDLE_FILE.read_text(encoding="utf-8"))


def _bundle_file(tmp_path: Path, bundle: dict, name: str = "anyplot-session-AbCdEf12.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return path


def _case_dir(tmp_path: Path, *, reaction: str = "thumbs_down", version: int = 2, include_data: bool = True) -> Path:
    """A case directory exactly as the BFF's feedback route stores it (`api/agent_cases.py`)."""
    from api.agent_cases import Submission
    from api.agent_cases import build_case as build_stored_case

    bundle = _bundle()
    bundle["versions"] = [item for item in bundle["versions"] if item["number"] == version]
    if not include_data:
        for item in bundle["versions"]:
            item["data_csv"] = None
    case = build_stored_case(
        json.dumps(bundle).encode(),
        Submission(
            reaction=reaction, message="the legend hides points", include_data=include_data, result_version=version
        ),
        case_id="20261012T143005Z-1a2b3c4d",
        created_at=datetime(2026, 10, 12, 14, 30, 5, tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )
    directory = tmp_path / "download" / case.case_id
    directory.mkdir(parents=True)
    for item in case.files:
        (directory / item.name).write_bytes(item.data)
    return directory


def _written(directory: Path) -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(directory.iterdir())}


class TestFromABundleFile:
    def test_the_newest_version_with_its_change_request(self, tmp_path, promoted, capsys) -> None:
        source = _bundle_file(tmp_path, _bundle())

        assert main([str(source)]) == 0

        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:8]
        target = promoted / f"session-{digest}-v2"
        files = _written(target)
        assert set(files) == {"case.json", "data.csv", "change_request.txt"}
        assert json.loads(files["case.json"]) == {
            "spec_id": "scatter-basic",
            "library": "matplotlib",
            "locale": "de",
            "bindings": [{"role": "x", "column": "Stunden"}, {"role": "y", "column": "Punkte"}],
            "expected": "unknown",
            "tags": ["imported"],
            "source": "saved session anyplot-session-AbCdEf12.json, version 2",
        }  # no `language`: the bundle predates the session language, so the replay keeps the default
        assert files["data.csv"] == DATA
        assert files["change_request.txt"] == "log scale on y\n"
        case = load_case(target, "promoted")
        assert (case.change_request, case.expected, case.origin) == ("log scale on y", "unknown", "promoted")
        out = capsys.readouterr().out
        assert "change request: log scale on y" in out
        assert f"--cases session-{digest}-v2" in out

    def test_version_one_came_from_create_plot_and_has_no_change_request(self, tmp_path, promoted) -> None:
        source = _bundle_file(tmp_path, _bundle())
        assert main([str(source), "--version", "1", "--id", "first-plot", "--expected", "accepted"]) == 0
        files = _written(promoted / "first-plot")
        assert set(files) == {"case.json", "data.csv"}
        assert json.loads(files["case.json"])["expected"] == "accepted"

    def test_refuses_a_bundle_without_the_data(self, tmp_path, promoted, capsys) -> None:
        bundle = _bundle()
        for item in bundle["versions"]:
            item["data_csv"] = None
        assert main([str(_bundle_file(tmp_path, bundle))]) == 1
        assert "holds no data.csv" in capsys.readouterr().err
        assert not promoted.exists()

    def test_refuses_a_version_the_bundle_lacks_and_a_file_that_is_no_bundle(self, tmp_path, promoted, capsys) -> None:
        assert main([str(_bundle_file(tmp_path, _bundle())), "--version", "7"]) == 1
        assert "no version 7 (the source holds 1, 2)" in capsys.readouterr().err
        assert main([str(_bundle_file(tmp_path, {"transcript": []}, "other.json"))]) == 1
        assert "not a session bundle" in capsys.readouterr().err
        assert not promoted.exists()

    def test_the_library_is_the_versions_after_a_library_switch(self, tmp_path) -> None:
        bundle = _bundle()
        bundle["session"]["library"] = "seaborn"
        source = read_bundle_file(_bundle_file(tmp_path, bundle), 2)
        assert build_case(source, None).case["library"] == "matplotlib"

    def test_a_detected_session_language_is_chosen_by_the_case(self, tmp_path, promoted) -> None:
        """The replay sends its first plot as `create_plot`, which detects nothing, so the case chooses the language."""
        bundle = _bundle()
        bundle["session"].update(plot_language="de", plot_language_source="detected")
        for item in bundle["versions"]:
            item["language"] = "de"

        assert main([str(_bundle_file(tmp_path, bundle)), "--id", "german"]) == 0

        case_json = json.loads(_written(promoted / "german")["case.json"])
        assert case_json["language"] == "de" and case_json["locale"] == "de"
        assert load_case(promoted / "german", "promoted").language == "de"

    def test_the_case_takes_the_language_its_version_was_written_in(self, tmp_path) -> None:
        """A version made before the user chose another language keeps its own, and so does its replay."""
        bundle = _bundle()
        bundle["session"].update(plot_language="Klingon", plot_language_source="chosen")
        bundle["versions"][0]["language"] = "en"
        bundle["versions"][1]["language"] = "Klingon"

        first = build_case(read_bundle_file(_bundle_file(tmp_path, bundle), 1), None, no_request=True)
        second = build_case(read_bundle_file(_bundle_file(tmp_path, bundle), 2), None)

        assert (first.case["language"], second.case["language"]) == ("en", "Klingon")

    @pytest.mark.parametrize(
        ("session", "version", "expected"),
        [
            ({}, {}, None),  # a bundle saved before the session language existed
            ({"plot_language": "de", "plot_language_source": "default"}, {"language": "de"}, None),
            ({"plot_language": "de", "plot_language_source": "chosen"}, {}, "de"),
            ({"plot_language": "de", "plot_language_source": "guessed"}, {"language": "de"}, None),
            ({"plot_language": "de", "plot_language_source": "chosen"}, {"language": "de; drop"}, None),
            ({"plot_language": "a/b", "plot_language_source": "detected"}, {}, None),
        ],
    )
    def test_the_language_needs_a_set_source_and_a_valid_value(self, session, version, expected) -> None:
        assert import_case.session_language(session, version) == expected

    def test_a_first_plot_from_a_typed_note_makes_the_note_version_ones_request(self, tmp_path, promoted) -> None:
        """Step 2's composer sends a note as a typed message, so the session never holds `create_plot`."""
        bundle = _bundle()
        bundle["transcript"][2]["text"] = "use larger markers"
        source = str(_bundle_file(tmp_path, bundle))

        assert main([source, "--version", "1", "--id", "note-v1"]) == 0
        assert main([source, "--version", "2", "--id", "note-v2"]) == 0

        assert (promoted / "note-v1" / "change_request.txt").read_text() == "use larger markers\n"
        assert (promoted / "note-v2" / "change_request.txt").read_text() == "log scale on y\n"

    def test_refuses_to_guess_when_a_question_has_no_version(self, tmp_path, promoted, capsys) -> None:
        bundle = _bundle()
        bundle["transcript"][4:4] = [
            {"role": "user", "text": "what does the y axis show?"},
            {"role": "assistant", "text": "The exam score."},
        ]
        source = str(_bundle_file(tmp_path, bundle))

        assert main([source, "--version", "2", "--id", "asked"]) == 1
        err = capsys.readouterr().err
        assert "3 plot turns for 2 versions" in err
        assert "1. .create_plot()\n  2. what does the y axis show?\n  3. log scale on y" in err
        assert not promoted.exists()

        assert main([source, "--version", "2", "--id", "asked", "--change-request", " log scale on y "]) == 0
        assert (promoted / "asked" / "change_request.txt").read_text() == "log scale on y\n"
        assert main([source, "--version", "1", "--id", "first", "--no-change-request"]) == 0
        assert set(_written(promoted / "first")) == {"case.json", "data.csv"}

    def test_refuses_bindings_the_versions_data_lacks(self, tmp_path, promoted, capsys) -> None:
        """The bundle's bindings are the session's when it was saved; a later data change renamed a column."""
        bundle = _bundle()
        bundle["bindings"] = [{"role": "x", "column": "Stunden"}, {"role": "y", "column": "Wert"}]

        assert main([str(_bundle_file(tmp_path, bundle)), "--version", "1"]) == 1
        err = capsys.readouterr().err
        assert "the bindings name 'Wert', which version 1's data.csv lacks" in err
        assert not promoted.exists()

    def test_a_quoted_header_with_a_byte_order_mark_still_binds(self, tmp_path, promoted) -> None:
        bundle = _bundle()
        bundle["versions"][1]["data_csv"] = '﻿"Stunden","Punkte"\n1.5,52\n'
        assert main([str(_bundle_file(tmp_path, bundle)), "--id", "bom"]) == 0

    @pytest.mark.parametrize(
        ("flag", "message"),
        [("   ", "--change-request is empty"), ("x" * (MAX_CHANGE_REQUEST_CHARS + 1), "at most 600")],
    )
    def test_refuses_an_unusable_change_request(self, tmp_path, promoted, capsys, flag, message) -> None:
        assert main([str(_bundle_file(tmp_path, _bundle())), f"--change-request={flag}"]) == 1
        assert message in capsys.readouterr().err

    def test_the_two_request_flags_exclude_each_other(self, tmp_path) -> None:
        with pytest.raises(SystemExit) as exit_info:
            main([str(_bundle_file(tmp_path, _bundle())), "--change-request", "x", "--no-change-request"])
        assert exit_info.value.code == 2


class TestFromAStoredCase:
    def test_the_manifest_decides_the_version_reaction_and_outcome(self, tmp_path, promoted) -> None:
        assert main([str(_case_dir(tmp_path))]) == 0

        target = promoted / "case-20261012t143005z-1a2b3c4d"
        files = _written(target)
        case = json.loads(files["case.json"])
        assert case["expected"] == "rejected"
        assert case["tags"] == ["imported", "thumbs_down"]
        assert case["source"] == "feedback case 20261012T143005Z-1a2b3c4d, version 2"
        assert files["data.csv"] == DATA
        assert files["change_request.txt"] == "log scale on y\n"

    @pytest.mark.parametrize(("reaction", "expected"), [("thumbs_up", "accepted"), ("thumbs_down", "rejected")])
    def test_the_thumbs_map_to_an_outcome(self, tmp_path, promoted, reaction, expected) -> None:
        assert main([str(_case_dir(tmp_path, reaction=reaction)), "--id", "mapped"]) == 0
        case = json.loads((promoted / "mapped" / "case.json").read_text())
        assert (case["expected"], case["tags"]) == (expected, ["imported", reaction])

    @pytest.mark.parametrize("reaction", ["bug", "idea"])
    def test_bug_and_idea_need_expected(self, tmp_path, promoted, capsys, reaction) -> None:
        """The triage's rule: those reactions imply no outcome, so the owner chooses."""
        assert main([str(_case_dir(tmp_path, reaction=reaction)), "--id", "undecided"]) == 1
        assert f"the reaction {reaction} implies no outcome" in capsys.readouterr().err
        assert not promoted.exists()

    def test_expected_overrides_the_reaction(self, tmp_path, promoted) -> None:
        assert main([str(_case_dir(tmp_path, reaction="bug")), "--id", "chosen", "--expected", "accepted"]) == 0
        assert json.loads((promoted / "chosen" / "case.json").read_text())["expected"] == "accepted"

    def test_refuses_a_case_sent_without_the_data(self, tmp_path, promoted, capsys) -> None:
        assert main([str(_case_dir(tmp_path, include_data=False))]) == 1
        assert "holds no data.csv" in capsys.readouterr().err

    def test_refuses_another_version_than_the_cases(self, tmp_path, promoted) -> None:
        with pytest.raises(ImportRefused, match="about version 2, not 1"):
            read_case_dir(_case_dir(tmp_path), 1)

    def test_a_case_sent_on_an_older_version_needs_its_request_named(self, tmp_path, promoted, capsys) -> None:
        """A case holds only its own version: one more plot turn means it was not the newest."""
        directory = _case_dir(tmp_path, version=1)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        assert [turn["text"] for turn in manifest["bundle"]["transcript"]][-2] == "log scale on y"

        assert main([str(directory), "--id", "older"]) == 1
        assert "2 plot turns for 1 versions" in capsys.readouterr().err
        assert main([str(directory), "--id", "older", "--no-change-request"]) == 0
        assert set(_written(promoted / "older")) == {"case.json", "data.csv"}


class TestWhereItWrites:
    def test_an_existing_case_needs_force(self, tmp_path, promoted, capsys) -> None:
        source = str(_bundle_file(tmp_path, _bundle()))
        assert main([source, "--id", "again"]) == 0
        (promoted / "again" / "stale.txt").write_text("old")

        assert main([source, "--id", "again", "--version", "1"]) == 1
        assert "pass --force" in capsys.readouterr().err
        assert main([source, "--id", "again", "--version", "1", "--force"]) == 0
        assert set(_written(promoted / "again")) == {"case.json", "data.csv"}

    def test_a_failed_copy_keeps_the_existing_case_and_leaves_no_partial_directory(
        self, tmp_path, promoted, capsys, monkeypatch
    ) -> None:
        source = str(_bundle_file(tmp_path, _bundle()))
        assert main([source, "--id", "kept"]) == 0
        before = _written(promoted / "kept")

        def failing_copytree(src, dst, **kwargs):
            Path(dst).mkdir()
            (Path(dst) / "case.json").write_text("partial")
            raise OSError("disk full")

        monkeypatch.setattr(import_case.shutil, "copytree", failing_copytree)

        assert main([source, "--id", "kept", "--version", "1", "--force"]) == 1
        assert "could not write" in capsys.readouterr().err
        assert _written(promoted / "kept") == before
        assert [path.name for path in promoted.iterdir()] == ["kept"]
        assert not [path for path in promoted.parent.iterdir() if path.name.startswith(".import-")]

    def test_never_takes_a_committed_fixture_id(self, tmp_path, promoted, capsys) -> None:
        source = str(_bundle_file(tmp_path, _bundle()))
        assert main([source, "--id", "scatter-basic-matplotlib", "--force"]) == 1
        assert "committed fixture case" in capsys.readouterr().err

    @pytest.mark.parametrize("case_id", ["../escape", "Upper", "-dash", "a" * 81, ".cases"])
    def test_refuses_an_id_that_is_no_case_id(self, tmp_path, promoted, case_id) -> None:
        assert main([str(_bundle_file(tmp_path, _bundle())), f"--id={case_id}"]) == 1
        assert not promoted.exists()
        assert not (tmp_path / "escape").exists()

    def test_a_case_the_harness_would_refuse_leaves_nothing(self, tmp_path, promoted) -> None:
        source = read_bundle_file(_bundle_file(tmp_path, _bundle()), 2)
        imported = build_case(source, None)
        broken = type(imported)(case={**imported.case, "bindings": "x"}, data_csv=DATA, change_request=None, notes=[])
        with pytest.raises(ImportRefused, match="would refuse"):
            write_case("broken", broken)
        assert not (promoted / "broken").exists()

    def test_a_gs_source_is_not_supported(self, capsys) -> None:
        with pytest.raises(SystemExit) as exit_info:
            main(["gs://anyplot-agent-cases/cases/x"])
        assert exit_info.value.code == 2
        err = capsys.readouterr().err
        assert "gs:// source is not supported here" in err
        assert "python -m agents.evals.sync_cases" in err

    def test_writes_into_the_git_ignored_promoted_directory_by_default(self) -> None:
        assert import_case.PROMOTED_DIR == Path(import_case.__file__).parent / ".cases"
        ignored = (Path(import_case.__file__).parents[2] / ".gitignore").read_text()
        assert "agents/evals/.cases/" in ignored.splitlines()


class TestChangeRequest:
    def _turns(self, *texts: str) -> list[dict]:
        return [{"role": "user", "text": text} for text in texts]

    def test_counts_the_plot_turns_from_the_first_create_plot(self) -> None:
        transcript = self._turns(
            "read Punkte as numbers",  # step 1: about the data, before any plot
            CREATE_PLOT_MESSAGE,
            "log scale on y",
            "[message withheld by scope policy]",
            "[action] Summarize the dataset for the user.",
            "bigger markers",
        )
        assert plot_turns(transcript) == [CREATE_PLOT_MESSAGE, "log scale on y", "bigger markers"]
        assert change_request(transcript, 1, 3) is None
        assert change_request(transcript, 2, 3) == "log scale on y"
        assert change_request(transcript, 3, 3) == "bigger markers"

    def test_without_create_plot_every_typed_message_is_a_plot_turn(self) -> None:
        transcript = self._turns("[action] Summarize the dataset for the user.", "use larger markers", "log scale on y")
        assert change_request(transcript, 1, 2) == "use larger markers"
        assert change_request(transcript, 2, 2) == "log scale on y"

    @pytest.mark.parametrize(
        ("transcript", "number", "versions", "match"),
        [
            # A question made no version: the counts differ.
            ([CREATE_PLOT_MESSAGE, "what does y show?", "log scale on y"], 2, 2, "3 plot turns for 2 versions"),
            # A version beyond the session's, or none at all.
            ([CREATE_PLOT_MESSAGE, "log scale on y"], 3, 2, "2 plot turns for 2 versions"),
            ([CREATE_PLOT_MESSAGE, "log scale on y"], 0, 2, "2 plot turns for 2 versions"),
            (None, 1, 1, "0 plot turns for 1 versions"),
        ],
    )
    def test_refuses_to_match_when_the_counts_differ(self, transcript, number, versions, match) -> None:
        turns = self._turns(*transcript) if transcript else transcript
        with pytest.raises(AmbiguousRequest, match=match):
            change_request(turns, number, versions)

    def test_a_long_request_is_left_out_with_a_note(self, tmp_path) -> None:
        bundle = _bundle()
        bundle["transcript"][4]["text"] = "x" * (MAX_CHANGE_REQUEST_CHARS + 1)
        imported = build_case(read_bundle_file(_bundle_file(tmp_path, bundle), 2), None)
        assert imported.change_request is None
        assert any("left out a change request" in note for note in imported.notes)


def test_the_copied_constants_match_their_sources() -> None:
    from agents.anyplot.plugins.scope_guard import WITHHELD
    from agents.main import ACTION_MESSAGES
    from core.database import FEEDBACK_REACTIONS

    assert ACTION_MESSAGES["create_plot"] == CREATE_PLOT_MESSAGE
    assert all(text.startswith(import_case.ACTION_PREFIX) for text in ACTION_MESSAGES.values())
    assert WITHHELD == import_case.WITHHELD
    assert import_case.MAX_CHANGE_REQUEST_CHARS == MAX_CHANGE_REQUEST_CHARS
    assert import_case.REACTIONS == set(FEEDBACK_REACTIONS)
    assert set(EXPECTED_BY_REACTION) == {"thumbs_up", "thumbs_down"}
