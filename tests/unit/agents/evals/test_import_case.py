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
    ImportRefused,
    build_case,
    change_request,
    main,
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
        }
        assert files["data.csv"] == DATA
        assert files["change_request.txt"] == "log scale on y\n"
        case = load_case(target, "promoted")
        assert (case.change_request, case.expected, case.origin) == ("log scale on y", "unknown", "promoted")
        out = capsys.readouterr().out
        assert "change request (check it): log scale on y" in out
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

    @pytest.mark.parametrize(
        ("reaction", "expected"), [("thumbs_up", "accepted"), ("idea", "accepted"), ("bug", "rejected")]
    )
    def test_each_reaction_maps_to_an_outcome(self, tmp_path, promoted, capsys, reaction, expected) -> None:
        assert main([str(_case_dir(tmp_path, reaction=reaction)), "--id", "mapped"]) == 0
        assert json.loads((promoted / "mapped" / "case.json").read_text())["expected"] == expected
        noted = "pass --expected to choose" in capsys.readouterr().err
        assert noted == (reaction in ("bug", "idea"))

    def test_expected_overrides_the_reaction(self, tmp_path, promoted) -> None:
        assert main([str(_case_dir(tmp_path, reaction="bug")), "--id", "chosen", "--expected", "accepted"]) == 0
        assert json.loads((promoted / "chosen" / "case.json").read_text())["expected"] == "accepted"

    def test_refuses_a_case_sent_without_the_data(self, tmp_path, promoted, capsys) -> None:
        assert main([str(_case_dir(tmp_path, include_data=False))]) == 1
        assert "holds no data.csv" in capsys.readouterr().err

    def test_refuses_another_version_than_the_cases(self, tmp_path, promoted) -> None:
        with pytest.raises(ImportRefused, match="about version 2, not 1"):
            read_case_dir(_case_dir(tmp_path), 1)


class TestWhereItWrites:
    def test_an_existing_case_needs_force(self, tmp_path, promoted, capsys) -> None:
        source = str(_bundle_file(tmp_path, _bundle()))
        assert main([source, "--id", "again"]) == 0
        (promoted / "again" / "stale.txt").write_text("old")

        assert main([source, "--id", "again", "--version", "1"]) == 1
        assert "pass --force" in capsys.readouterr().err
        assert main([source, "--id", "again", "--version", "1", "--force"]) == 0
        assert set(_written(promoted / "again")) == {"case.json", "data.csv"}

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
        assert "gs:// source is not supported" in capsys.readouterr().err

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
        assert change_request(transcript, 1) is None
        assert change_request(transcript, 2) == "log scale on y"
        assert change_request(transcript, 3) == "bigger markers"
        assert change_request(transcript, 4) is None
        assert change_request(None, 1) is None

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
    assert set(EXPECTED_BY_REACTION) == set(FEEDBACK_REACTIONS)
