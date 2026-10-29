"""The toolchain image's inputs and tag (agents/renderer/toolchain.py, toolchain.Dockerfile, toolchain/)."""

from __future__ import annotations

import re
import shutil
import tomllib
from pathlib import Path

import pytest
import yaml

from agents.renderer import commands, toolchain


REPO_ROOT = Path(__file__).resolve().parents[4]
SETUP_R = REPO_ROOT / ".github" / "actions" / "setup-r" / "action.yml"
TOOLCHAIN_DIR = REPO_ROOT / "agents" / "renderer" / "toolchain"
WARMUP_DIR = TOOLCHAIN_DIR / "AnyplotWarmup"
TOOLCHAIN_DOCKERFILE = REPO_ROOT / "agents" / "renderer" / "toolchain.Dockerfile"
PROJECT = REPO_ROOT / "Project.toml"
MANIFEST = REPO_ROOT / "Manifest.toml"


def _stages(text: str) -> dict[str, str]:
    """Each stage's instructions by its name (`AS <name>`, the unnamed last stage as `final`), the FROM line included
    and the comments left out (a stage's own comment stands above its FROM, inside the stage before)."""
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    parts = re.split(r"^(?=FROM )", code, flags=re.MULTILINE)[1:]
    named: dict[str, str] = {}
    for part in parts:
        header = part.splitlines()[0]
        match = re.search(r" AS (\S+)$", header)
        named[match.group(1) if match else "final"] = part
    return named


def _manifest_version(package: str) -> str:
    entries = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["deps"][package]
    return entries[0]["version"]


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
            "agents/renderer/toolchain/smoke.jl",
            "agents/renderer/toolchain/warmup.jl",
            "agents/renderer/toolchain/AnyplotWarmup/Project.toml",
            "agents/renderer/toolchain/AnyplotWarmup/src/AnyplotWarmup.jl",
            "agents/renderer/execdeny/execdeny.c",
            "Project.toml",
            "Manifest.toml",
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

    def test_every_file_the_dockerfile_copies_from_the_context_is_an_input(self) -> None:
        """A COPY from the build context that no input covers would change the image without changing its tag, and
        the deploy would keep serving the old toolchain."""
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        sources = [
            source for line in re.findall(r"^COPY (?!--from=)(.+)$", text, re.MULTILINE) for source in line.split()[:-1]
        ]
        assert {"Project.toml", "Manifest.toml"} <= set(sources)
        uncovered = [
            source
            for source in sources
            if not any(source == name or source.startswith(f"{name}/") for name in toolchain.INPUTS)
        ]
        assert not uncovered, uncovered

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


class TestJulia:
    """The Julia stage (step 5) builds what the renderer's Julia row runs: the same version, project, depot, CPU
    target, flags and environment, and the pipeline's own Project.toml and Manifest.toml."""

    def test_the_julia_version_is_the_manifests_and_the_rows(self) -> None:
        manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["julia_version"]
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        assert re.findall(r"^ARG JULIA_VERSION=(\S+)$", text, re.MULTILINE) == [manifest]
        assert commands.JULIA_HOME == f"/opt/julia-{manifest}"
        assert commands.JULIA_BINARY == f"{commands.JULIA_HOME}/bin/julia"

    def test_the_cpu_target_is_the_rows(self) -> None:
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        assert re.findall(r'^ARG JULIA_CPU_TARGET="([^"]+)"$', text, re.MULTILINE) == [commands.JULIA_CPU_TARGET]

    def test_the_download_is_the_official_tarball_checked_against_its_sha256(self) -> None:
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        julia = _stages(text)["julia"]
        assert re.search(r"^ARG JULIA_SHA256=[0-9a-f]{64}$", julia, re.MULTILINE)
        assert "https://julialang-s3.julialang.org/bin/checksums/julia-1.13.2.sha256" in text  # where it came from
        assert "julialang-s3.julialang.org/bin/linux/x64/" in julia and "linux-x86_64.tar.gz" in julia
        assert 'echo "${JULIA_SHA256}  /tmp/julia.tar.gz" | sha256sum -c -' in julia

    def test_the_stages_stay_independent(self) -> None:
        """A Julia change must not rebuild R's packages, and an R change must not rerun Julia's precompile."""
        stages = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))
        assert stages["julia"].startswith("FROM base AS julia\n") and stages["r"].startswith("FROM base AS r\n")
        assert "--from=" not in stages["julia"] and "julia" not in stages["r"].lower()
        assert re.findall(r"^COPY (?!--from=)(.+)$", stages["julia"], re.MULTILINE) == [
            f"Project.toml Manifest.toml {commands.JULIA_PROJECT}/",
            f"agents/renderer/toolchain/AnyplotWarmup {commands.JULIA_PROJECT}/AnyplotWarmup",
        ]
        assert f"JULIA_DEPOT_PATH={commands.JULIA_DEPOT}" in stages["julia"]
        assert "Pkg.precompile(strict = true" in stages["julia"]
        final = stages["final"]
        copies = [
            line
            for line in re.findall(r"^COPY --from=(\S+ \S+)", final, re.MULTILINE)
            if line.startswith(("julia ", "r "))
        ]
        assert copies == [
            "r /opt/R",
            "r /opt/anyplot/toolchain",
            "julia /opt/julia-${JULIA_VERSION}",
            "julia /opt/julia-project",
            "julia /opt/julia-depot",
        ]

    def test_the_build_smoke_runs_the_rows_launcher_flags_and_environment(self) -> None:
        """The build's smoke loads every package the way a render will, so a depot that would not load under
        `--compiled-modules=strict` with the row's environment fails the build, not the first render."""
        final = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))["final"]
        smoke = final[final.rindex('RUN j="/opt/julia-${JULIA_VERSION}"') :]
        assert "run() {" in smoke
        row = commands.command_for("julia", "makie")
        assert 'j="/opt/julia-${JULIA_VERSION}"' in smoke and '"$j/bin/julia"' in smoke
        for flag in row.argv[1:]:
            assert flag in smoke, flag
        for key, value in row.env.items():
            expected = '"JULIA_CPU_TARGET=${JULIA_CPU_TARGET}"' if key == "JULIA_CPU_TARGET" else f"{key}={value}"
            assert expected in smoke, expected
        assert "LD_PRELOAD=/opt/anyplot/libexecdeny.so ANYPLOT_DENY_EXEC=required" in smoke
        assert "/opt/anyplot/toolchain/smoke.jl" in smoke and "JULIA_DEBUG=loading" in smoke
        assert "ldd \"$j/bin/julia\" | grep 'libc\\.so'" in final  # a static launcher would ignore LD_PRELOAD

    def test_the_precompile_workload_is_a_hashed_input(self) -> None:
        """J1.1: a change to the workload must change the toolchain's tag, or the deploy would keep the old image."""
        files = {path.relative_to(REPO_ROOT).as_posix() for path in toolchain.input_files()}
        assert {
            "agents/renderer/toolchain/warmup.jl",
            "agents/renderer/toolchain/AnyplotWarmup/Project.toml",
            "agents/renderer/toolchain/AnyplotWarmup/src/AnyplotWarmup.jl",
        } <= files

    def test_the_workload_joins_the_images_project_never_the_repositorys(self) -> None:
        """The catalogue pipeline shares the root Project.toml and Manifest.toml (`.github/actions/setup-julia`):
        the workload is developed into the image's copy after the catalogue's precompile, offline and with
        PRESERVE_ALL, so it moves no version, and the registries go only after that `develop` has resolved."""
        package = tomllib.loads((WARMUP_DIR / "Project.toml").read_text(encoding="utf-8"))
        assert package["name"] == "AnyplotWarmup"
        assert "AnyplotWarmup" not in PROJECT.read_text(encoding="utf-8")
        assert package["uuid"] not in MANIFEST.read_text(encoding="utf-8")
        julia = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))["julia"]
        develop = julia.index(
            f'Pkg.develop(path = "{commands.JULIA_PROJECT}/AnyplotWarmup"; preserve = Pkg.PRESERVE_ALL)'
        )
        assert julia.index("Pkg.precompile(strict = true") < julia.index("COPY agents/renderer/toolchain/AnyplotWarmup")
        assert julia.index("COPY agents/renderer/toolchain/AnyplotWarmup") < develop
        assert develop < julia.index("rm -rf /opt/julia-depot/registries") and julia.count("registries") == 1
        assert "JULIA_PKG_OFFLINE=true" in julia[julia.rindex("\nRUN ", 0, develop) : develop]

    def test_the_workloads_dependencies_are_the_manifests(self) -> None:
        """Every package the workload loads is already in the catalogue's Manifest under the same UUID, so the
        `develop` adds one entry and resolves nothing else."""
        deps = tomllib.loads((WARMUP_DIR / "Project.toml").read_text(encoding="utf-8"))["deps"]
        manifest = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["deps"]
        assert {name: manifest[name][0]["uuid"] for name in deps if name in manifest} == deps
        assert {"CairoMakie", "CSV", "DataFrames", "TimeZones", "PrecompileTools"} <= set(deps)

    def test_the_row_loads_the_workload_the_image_carries(self) -> None:
        """`warmup.jl` imports the package, and the final stage puts it where the row's `-L` names it."""
        assert "import AnyplotWarmup" in (TOOLCHAIN_DIR / "warmup.jl").read_text(encoding="utf-8")
        assert commands.JULIA_WARMUP == "/opt/anyplot/toolchain/warmup.jl"
        final = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))["final"]
        assert (
            "COPY agents/renderer/toolchain/smoke.jl agents/renderer/toolchain/warmup.jl /opt/anyplot/toolchain/"
            in final
        )
        workload = (WARMUP_DIR / "src" / "AnyplotWarmup.jl").read_text(encoding="utf-8")
        assert "@compile_workload" in workload and "agents/anyplot/code/profiles/julia/loader.py" in workload

    def test_the_smoke_loads_every_package_and_sees_a_program_start_refused(self) -> None:
        script = (TOOLCHAIN_DIR / "smoke.jl").read_text(encoding="utf-8")
        assert "@assert isdefined(Main, :AnyplotWarmup)" in script  # `-L warmup.jl` ran before the program
        assert 'TOML.parsefile(Base.active_project())["deps"]' in script
        assert "@assert !success(`true`)" in script
        assert "ZonedDateTime(" in script and "DateTime(zoned, UTC)" in script

    def test_timezones_is_a_direct_dependency_at_the_manifests_version(self) -> None:
        """Owner decision of 2026-10-29: datetimes with offsets go to UTC through TimeZones.jl, which the toolchain
        precompiles only as a direct dependency of the project."""
        project = tomllib.loads(PROJECT.read_text(encoding="utf-8"))
        entry = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["deps"]["TimeZones"][0]
        assert project["deps"]["TimeZones"] == entry["uuid"]
        assert project["compat"]["TimeZones"] == _manifest_version("TimeZones") == "1.22.3"


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
