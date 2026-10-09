"""Tests for agents/anyplot/code/export.py: the attribution header over the unchanged run form."""

import pytest

from agents.anyplot.code.export import export_code


RUN_FORM = 'import os\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n'


def test_header_then_the_run_form_byte_for_byte() -> None:
    exported = export_code(RUN_FORM, spec_id="scatter-basic", library="matplotlib", library_version="3.11.2")

    assert exported == (
        "# Adapted by anyplot.ai from scatter-basic (matplotlib 3.11.2) for your data.csv;\n"
        "# run: ANYPLOT_THEME=light python plot.py\n"
        "\n" + RUN_FORM
    )


def test_version_is_optional() -> None:
    exported = export_code(RUN_FORM, spec_id="area-basic", library="seaborn", library_version=None)
    assert exported.startswith("# Adapted by anyplot.ai from area-basic (seaborn) for your data.csv;\n")


@pytest.mark.parametrize("run_form", [RUN_FORM, "\n\nx = 1\n", "", "# a comment first\n"])
def test_idempotent(run_form: str) -> None:
    once = export_code(run_form, spec_id="scatter-basic", library="matplotlib", library_version="3.11.2")
    twice = export_code(once, spec_id="scatter-basic", library="matplotlib", library_version="3.11.2")

    assert twice == once
    assert once.endswith(run_form)


def test_re_export_replaces_the_header() -> None:
    first = export_code(RUN_FORM, spec_id="scatter-basic", library="matplotlib", library_version="3.11.2")
    second = export_code(first, spec_id="line-basic", library="seaborn", library_version="0.13.2")

    assert second.count("# Adapted by anyplot.ai") == 1
    assert "line-basic (seaborn 0.13.2)" in second and second.endswith(RUN_FORM)


@pytest.mark.parametrize(
    ("spec_id", "library", "version"),
    [
        ("scatter-basic\nimport os", "matplotlib", None),
        ("Scatter", "matplotlib", None),
        ("scatter-basic", "mat plot", None),
        ("scatter-basic", "matplotlib", "3.11\n"),
        ("scatter-basic", "matplotlib", ""),
    ],
)
def test_values_that_become_source_are_checked(spec_id: str, library: str, version: str | None) -> None:
    with pytest.raises(ValueError):
        export_code(RUN_FORM, spec_id=spec_id, library=library, library_version=version)
