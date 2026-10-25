"""The renderer's command table (agents/renderer/commands.py): one fixed command per language, pinned to the catalogue."""

import pytest

from agents.renderer import commands
from agents.renderer.commands import (
    EXEC_FLAG,
    LANGUAGES,
    LIBRARY_LANGUAGES,
    RuntimeCommand,
    code_file,
    command_for,
    toolchains,
)
from core.constants import LIBRARY_LANGUAGES as CATALOGUE_LANGUAGES
from core.constants import SUPPORTED_LANGUAGES, SUPPORTED_LIBRARIES, library_file_extension


class TestTable:
    def test_the_table_is_the_catalogue(self) -> None:
        """The renderer image has no `core`, so the table keeps its own copy of the catalogue's filing."""
        assert dict(LIBRARY_LANGUAGES) == CATALOGUE_LANGUAGES
        assert set(LIBRARY_LANGUAGES) == SUPPORTED_LIBRARIES
        assert set(LANGUAGES) == SUPPORTED_LANGUAGES

    @pytest.mark.parametrize("library", sorted(SUPPORTED_LIBRARIES))
    def test_every_library_has_a_row_with_the_catalogue_file_extension(self, library: str) -> None:
        row = command_for(LIBRARY_LANGUAGES[library], library)
        assert isinstance(row, RuntimeCommand)
        assert row.code_file == f"plot{library_file_extension(library)}"
        assert code_file(row.language, library) == row.code_file

    def test_python_runs_in_process_and_keeps_every_limit(self) -> None:
        row = command_for("python", "matplotlib")
        assert row.in_process and row.argv == () and row.toolchain == ()
        assert row.rlimit_as and row.rlimit_nproc and row.render_p95_s == 15.0

    def test_the_other_languages_run_the_ci_command_through_exec_mode(self) -> None:
        js = command_for("javascript", "chartjs")
        assert js.argv == ("node", commands.JS_HARNESS, "--library=chartjs") and js.toolchain == ("node",)
        assert not js.rlimit_as and not js.rlimit_nproc  # V8 reservations; 77 tasks per render (spike 2026-10-24)
        assert command_for("javascript", "muix").code_file == "plot.tsx"
        r = command_for("r", "ggplot2")
        assert r.argv == ("Rscript",) and r.toolchain == ("Rscript",) and r.rlimit_as and r.rlimit_nproc
        julia = command_for("julia", "makie")
        assert julia.argv == ("julia", f"--project={commands.JULIA_PROJECT}") and julia.toolchain == ("julia",)
        assert not julia.rlimit_as and julia.rlimit_nproc  # LLVM dies under 1 GiB of address space
        assert julia.env["JULIA_DEPOT_PATH"].startswith("/tmp/depot:") and julia.env["JULIA_PKG_OFFLINE"] == "true"
        assert EXEC_FLAG == "--exec"

    def test_a_pair_outside_the_table_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no runtime command"):
            command_for("python", "excel")
        with pytest.raises(ValueError, match="python library, not r"):
            command_for("r", "matplotlib")
        with pytest.raises(ValueError, match="javascript library, not python"):
            command_for("python", "chartjs")

    def test_toolchains_name_one_binary_set_per_language(self) -> None:
        needed = toolchains()
        assert set(needed) == set(LANGUAGES)
        assert needed["python"] == () and needed["r"] == ("Rscript",)
        assert needed["javascript"] == ("node",) and needed["julia"] == ("julia",)

    def test_rows_are_frozen(self) -> None:
        row = command_for("r", "ggplot2")
        with pytest.raises(AttributeError):
            row.argv = ("sh",)  # type: ignore[misc]
        with pytest.raises(TypeError):
            row.env["PATH"] = "/x"  # type: ignore[index]
