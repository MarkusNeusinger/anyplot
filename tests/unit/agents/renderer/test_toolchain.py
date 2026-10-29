"""The toolchain image's inputs and tag (agents/renderer/toolchain.py, toolchain.Dockerfile, toolchain/)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml

from agents.renderer import toolchain


REPO_ROOT = Path(__file__).resolve().parents[4]
SETUP_R = REPO_ROOT / ".github" / "actions" / "setup-r" / "action.yml"
TOOLCHAIN_DIR = REPO_ROOT / "agents" / "renderer" / "toolchain"
TOOLCHAIN_DOCKERFILE = REPO_ROOT / "agents" / "renderer" / "toolchain.Dockerfile"


def _setup_r_install_script() -> str:
    action = yaml.safe_load(SETUP_R.read_text(encoding="utf-8"))
    step = next(step for step in action["runs"]["steps"] if step.get("name") == "Install R packages")
    return step["run"]


def _listed(path: Path) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


@pytest.fixture
def inputs(tmp_path: Path) -> Path:
    """A copy of the toolchain's inputs under a root of their own."""
    for name in toolchain.INPUTS:
        source = REPO_ROOT / name
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    return tmp_path


class TestTag:
    def test_the_tag_is_a_valid_docker_tag_and_stable(self) -> None:
        tag = toolchain.toolchain_tag()
        assert re.fullmatch(r"t-[0-9a-f]{16}", tag)
        assert toolchain.toolchain_tag() == tag

    def test_a_copy_of_the_inputs_has_the_same_tag(self, inputs: Path) -> None:
        assert toolchain.toolchain_tag(inputs) == toolchain.toolchain_tag()

    @pytest.mark.parametrize(
        "path",
        [
            "agents/renderer/toolchain.Dockerfile",
            "agents/renderer/toolchain/r-packages.txt",
            "agents/renderer/toolchain/r-repos.txt",
            "agents/renderer/execdeny/execdeny.c",
        ],
    )
    def test_any_changed_input_changes_the_tag(self, inputs: Path, path: str) -> None:
        before = toolchain.toolchain_tag(inputs)
        with (inputs / path).open("a", encoding="utf-8") as handle:
            handle.write("\n")
        assert toolchain.toolchain_tag(inputs) != before

    def test_a_new_file_in_an_input_directory_changes_the_tag(self, inputs: Path) -> None:
        before = toolchain.toolchain_tag(inputs)
        (inputs / "agents/renderer/toolchain/julia.txt").write_text("CairoMakie\n", encoding="utf-8")
        assert toolchain.toolchain_tag(inputs) != before

    def test_a_missing_input_is_an_error(self, inputs: Path) -> None:
        shutil.rmtree(inputs / "agents/renderer/execdeny")
        with pytest.raises(FileNotFoundError, match="execdeny"):
            toolchain.toolchain_tag(inputs)

    def test_the_command_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert toolchain.main(["tag"]) == 0
        tag = capsys.readouterr().out.strip()
        assert toolchain.main(["repository"]) == 0
        repository = capsys.readouterr().out.strip()
        assert toolchain.main(["image"]) == 0
        assert capsys.readouterr().out.strip() == f"{repository}:{tag}"
        assert repository == "europe-west4-docker.pkg.dev/anyplot/anyplot/anyplot-toolchain"
        assert toolchain.main([]) == 2
        assert toolchain.main(["tag", "image"]) == 2


class TestRPackages:
    """The renderer's R must be the pipeline's R: the same packages from the same snapshot."""

    def test_the_package_list_is_setup_rs_plus_readr(self) -> None:
        script = _setup_r_install_script()
        call = re.search(r"install\.packages\(\s*c\(([^)]*)\)", script)
        assert call, "setup-r installs its packages with one install.packages(c(...)) call"
        pipeline = re.findall(r'"([^"]+)"', call.group(1))
        assert _listed(TOOLCHAIN_DIR / "r-packages.txt") == [*pipeline, "readr"]

    def test_the_snapshot_is_setup_rs_for_debian_13(self) -> None:
        pipeline = re.search(
            r"packagemanager\.posit\.co/cran/__linux__/(\w+)/(\d{4}-\d{2}-\d{2})", _setup_r_install_script()
        )
        assert pipeline, "setup-r pins a dated Posit Package Manager snapshot"
        (url,) = _listed(TOOLCHAIN_DIR / "r-repos.txt")
        assert url == f"https://packagemanager.posit.co/cran/__linux__/trixie/{pipeline.group(2)}"

    def test_the_r_version_is_setup_rs(self) -> None:
        action = yaml.safe_load(SETUP_R.read_text(encoding="utf-8"))
        version = action["inputs"]["r-version"]["default"]
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        assert set(re.findall(r"^ARG R_VERSION=(\S+)$", text, re.MULTILINE)) == {version}


class TestDockerfile:
    def test_the_base_is_python_3_14_slim_pinned_by_digest(self) -> None:
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        froms = re.findall(r"^FROM (.+)$", text, re.MULTILINE)
        assert re.fullmatch(r"python:3\.14-slim@sha256:[0-9a-f]{64} AS base", froms[0])
        assert all(line.startswith("base") for line in froms[1:]), froms

    def test_the_build_proves_r_under_the_exec_filter(self) -> None:
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        smoke = text[text.index("smoke.R loads every package") :]
        assert "LD_PRELOAD=/opt/anyplot/libexecdeny.so ANYPLOT_DENY_EXEC=required" in smoke
        assert '"$r/bin/exec/R" --no-echo --no-restore --no-save --file=/opt/anyplot/toolchain/smoke.R' in smoke
        assert "LANG=C.UTF-8" in smoke
        assert "Rscript" not in smoke
        assert "sha256sum -c" in text
        assert "-Werror" in text

    def test_no_compiler_and_no_fontconfig_tools_reach_the_final_stage(self) -> None:
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        final = text[text.rindex("\nFROM base\n") :]
        assert not re.search(r"\b(gcc|make|fontconfig|libpango)\b", final.split("COPY", 1)[0])
        libs = re.search(r'ARG R_RUNTIME_LIBS="([^"]+)"', text)
        assert libs and "pango" not in libs.group(1)
