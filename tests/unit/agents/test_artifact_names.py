"""The code artifact's name follows the runtime's language (agents/anyplot/schemas.py, services.py)."""

from typing import get_args

import pytest
from pydantic import ValidationError

from agents.anyplot.schemas import CODE_ARTIFACTS, DEFAULT_CODE_ARTIFACT, ArtifactName, PlotResult, artifact_names
from agents.anyplot.services import CodeVersion


def test_every_copy_of_the_name_table_agrees() -> None:
    """The artifact names live in five places (the wire schema, the agents service, the BFF route, the case files and
    the case store); a name added to one must reach them all (review of PR #12404)."""
    from agents.main import ARTIFACT_TYPES
    from api.agent_cases import CASE_MEDIA_TYPES
    from api.routers.agent import ARTIFACT_MEDIA_TYPES
    from core.agent_cases import CASE_FILE_NAMES, CODE_FILE_NAMES, MANIFEST_NAME

    names = set(get_args(ArtifactName))
    assert set(ARTIFACT_TYPES) == names == set(ARTIFACT_MEDIA_TYPES)
    assert ARTIFACT_TYPES == ARTIFACT_MEDIA_TYPES
    assert set(CODE_FILE_NAMES) == CODE_ARTIFACTS
    assert set(CASE_FILE_NAMES) == names | {MANIFEST_NAME} == set(CASE_MEDIA_TYPES)
    assert {name: CASE_MEDIA_TYPES[name] for name in names} == ARTIFACT_TYPES


class TestArtifactNames:
    def test_python_stays_plot_py(self) -> None:
        assert DEFAULT_CODE_ARTIFACT == "plot.py"
        assert artifact_names(["light"]) == ["plot-light.png", "plot.py", "data.csv"]
        assert artifact_names(["dark", "light"]) == ["plot-light.png", "plot-dark.png", "plot.py", "data.csv"]

    def test_another_language_names_its_own_code_file(self) -> None:
        assert artifact_names(["light"], "plot.R") == ["plot-light.png", "plot.R", "data.csv"]
        assert CODE_ARTIFACTS == {"plot.py", "plot.R", "plot.jl", "plot.js", "plot.tsx"}

    def test_a_result_accepts_every_code_artifact_and_nothing_else(self) -> None:
        for name in sorted(CODE_ARTIFACTS):
            result = PlotResult(status="ok", attempts=1, artifacts=["plot-light.png", name, "data.csv"])
            assert name in result.artifacts
        with pytest.raises(ValidationError):
            PlotResult(status="ok", attempts=1, artifacts=["plot.html"])

    def test_a_version_lists_its_code_under_its_runtime_name(self) -> None:
        version = CodeVersion(
            number=1,
            working="",
            run_form="",
            export="",
            data_csv="",
            render_id=None,
            result=PlotResult(status="ok", attempts=1, artifacts=["plot-light.png", "plot.js", "data.csv"]),
            code_artifact="plot.js",
        )
        assert version.artifacts() == ["plot-light.png", "plot.js", "data.csv"]
        assert CodeVersion(
            number=2, working="", run_form="", export="", data_csv="", render_id=None, result=version.result
        ).artifacts() == ["plot-light.png", "plot.py", "data.csv"]
