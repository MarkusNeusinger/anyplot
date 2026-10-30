"""The toolchain image's inputs and tag (agents/renderer/toolchain.py, toolchain.Dockerfile, toolchain/)."""

from __future__ import annotations

import importlib.util
import json
import os
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
            "agents/renderer/toolchain/import_allowlist.py",
            "agents/renderer/toolchain/js-fonts.conf",
            "agents/renderer/toolchain/smoke.js",
            "agents/renderer/toolchain/smoke.tsx",
            "Project.toml",
            "Manifest.toml",
            "package.json",
            "package-lock.json",
            "automation/js-render/render.mjs",
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
        assert {"Project.toml", "Manifest.toml", "package.json", "package-lock.json", "automation/js-render/"} <= set(
            sources
        )
        uncovered = [
            source
            for source in sources
            if not any(source == name or source.startswith(f"{name}/") for name in toolchain.INPUTS)
        ]
        assert not uncovered, uncovered

    def test_every_input_reaches_the_ci_jobs_change_filter(self) -> None:
        """A change to an input that `RENDERER_CHANGES` misses would skip the image job, and its first build would be
        the deploy's (finding 8 of the second opinion on step 3)."""
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci-image.yml").read_text(encoding="utf-8")
        match = re.search(r"RENDERER_CHANGES=\$\(echo \"\$CHANGED_FILES\" \| grep -E '([^']+)'", workflow)
        assert match, "ci-image.yml filters the renderer job's changes with one grep -E"
        pattern = re.compile(match.group(1))
        files = [path.relative_to(REPO_ROOT).as_posix() for path in toolchain.input_files()]
        assert not [path for path in files if not pattern.search(path)]
        assert not pattern.search("app/package.json") and not pattern.search("automation/scripts/x.py")

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
        for name in ("R_RUNTIME_LIBS", "NODE_RUNTIME_LIBS"):
            libs = re.search(rf'ARG {name}="([^"]+)"', text)
            assert libs and "pango" not in libs.group(1), name
            assert not re.search(r"(^|\s)(fontconfig|libgbm1|mesa\S*|libllvm\S*)(\s|$)", libs.group(1)), name
        # Every apt line of the final stage installs one of the two lists and nothing else.
        installs = re.findall(r"apt-get install -y --no-install-recommends (.+?) \\", final)
        assert installs == ["${R_RUNTIME_LIBS}", "${NODE_RUNTIME_LIBS}"]


def _node_stage() -> str:
    return _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))["node"]


class TestNode:
    """The Node stage (JS-1 of step 3) installs what the JavaScript row runs: the pipeline's Node major, the
    repository's lock, the headless shell alone, the row's fonts, and the import allowlist."""

    def test_the_node_major_is_the_pipelines(self) -> None:
        action = yaml.safe_load((REPO_ROOT / ".github" / "actions" / "setup-node" / "action.yml").read_text())
        major = str(action["inputs"]["node-version"]["default"])
        (version,) = re.findall(r"^ARG NODE_VERSION=(\S+)$", TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"), re.M)
        assert version.split(".")[0] == major
        engines = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))["engines"]["node"]
        assert engines == ">=22" and int(version.split(".")[0]) >= 22

    def test_the_download_is_the_official_tarball_checked_against_its_sha256(self) -> None:
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        node = _node_stage()
        (version,) = re.findall(r"^ARG NODE_VERSION=(\S+)$", node, re.M)
        assert re.search(r"^ARG NODE_SHA256=[0-9a-f]{64}$", node, re.MULTILINE)
        assert f"https://nodejs.org/dist/v{version}/SHASUMS256.txt" in text  # where the checksum came from
        assert "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" in node
        assert 'echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c -' in node
        assert f"{commands.NODE_HOME}" in node and commands.NODE_BINARY == "/opt/node/bin/node"

    def test_the_stage_stays_independent_of_r_and_julia(self) -> None:
        stages = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))
        node = stages["node"]
        assert node.startswith("FROM base AS node\n") and "--from=" not in node
        assert "node" not in stages["r"].lower() and "node" not in stages["julia"].lower()
        assert re.findall(r"^COPY (?!--from=)(.+)$", node, re.MULTILINE) == [
            "package.json package-lock.json /opt/anyplot/",
            "agents/renderer/toolchain/import_allowlist.py /opt/anyplot/toolchain/import_allowlist.py",
        ]
        final = stages["final"]
        assert final.index("COPY --from=julia /opt/julia-depot") < final.index("COPY --from=node")

    def test_the_install_is_the_locks_and_runs_no_install_script(self) -> None:
        node = _node_stage()
        assert 'PATH="/opt/node/bin:$PATH" npm ci --ignore-scripts' in node
        assert "--omit" not in node  # the harness's esbuild and playwright are devDependencies of the lock
        dev = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))["devDependencies"]
        assert {"esbuild", "playwright"} <= set(dev)
        assert "playwright/cli.js install --only-shell chromium" in node
        assert f"PLAYWRIGHT_BROWSERS_PATH={commands.PLAYWRIGHT_BROWSERS}" in node
        assert "/opt/node/lib/node_modules" in node and "/opt/node/bin/npm" in node  # npm leaves the install
        assert "/opt/pw-browsers/ffmpeg-*" in node

    def test_libgbm_is_unpacked_without_mesa(self) -> None:
        """libgbm1's package depends on Mesa's drivers and LLVM (about 200 MB); the library alone links libdrm and
        libexpat, which NODE_RUNTIME_LIBS installs."""
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        node = _node_stage()
        assert "apt-get download libgbm1" in node and "dpkg-deb -x libgbm1_*.deb" in node
        assert "libgbm.so.1*" in node and "dri_gbm" not in node
        libs = re.search(r'ARG NODE_RUNTIME_LIBS="([^"]+)"', text)
        assert libs and {"libdrm2", "libexpat1", "libnss3"} <= set(libs.group(1).split())
        assert "COPY --from=node /opt/gbm/lib/ /usr/lib/x86_64-linux-gnu/" in text

    def test_the_liberation_fonts_stay_out_of_the_system_font_directories(self) -> None:
        """Installed system-wide they changed pygal's and altair's renders of files that name Arial (2026-10-30)."""
        text = TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8")
        node = _node_stage()
        assert "cp /usr/share/doc/fonts-liberation/copyright /opt/anyplot/js-fonts/doc/" in node
        final = _stages(text)["final"]
        assert "fonts-liberation" not in final.split("COPY --from=node", 1)[0]
        assert "/usr/share/fonts" not in final.split("COPY --from=node", 1)[1].split("RUN ldconfig", 1)[0]

    def test_the_build_checks_the_libraries_and_renders_as_the_row(self) -> None:
        """The final stage resolves every library of Node and the shell and renders through the harness with the
        row's binary and environment, so a missing library or a broken bundle fails the build, not a render."""
        final = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))["final"]
        assert 'for f in /opt/node/bin/node "$shell/chrome-headless-shell" "$shell"/*.so*' in final
        smoke = final[final.index("RUN smoke() {") :]
        assert "&& smoke chartjs smoke.js" in smoke and "&& smoke muix smoke.tsx" in smoke
        row = commands.command_for("javascript", "chartjs")
        assert f'{commands.NODE_BINARY} {commands.JS_HARNESS} "--library=$1"' in smoke
        for key, value in row.env.items():
            assert f"{key}={value}" in smoke, key
        assert "env -i PATH=/usr/bin:/bin HOME=/tmp ANYPLOT_THEME=light" in smoke
        assert "(3200, 1800)" in smoke
        for name in ("smoke.js", "smoke.tsx"):
            assert (TOOLCHAIN_DIR / name).is_file(), name
        assert '"@mui/x-charts/BarChart"' in (TOOLCHAIN_DIR / "smoke.tsx").read_text(encoding="utf-8")
        assert "&& test ! -e plot-light.html" in smoke  # the row's ANYPLOT_NO_HTML

    def test_ci_renders_through_the_sandbox_mode_in_the_built_image(self) -> None:
        """JS-2: the image's CI step renders through the row, whose environment switches the sandbox mode on, and
        checks the data injection, the route and the import plugin there, where no host test can."""
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci-image.yml").read_text(encoding="utf-8")
        step = workflow[workflow.index("- name: Render Chart.js and MUI X plots through the harness in exec mode") :]
        step = step[: step.index("\n      - name:", 1)]
        assert 'test ! -e "work-js/$library/plot-light.html"' in step
        assert "-e ANYPLOT_DATA_JSON=/work/data.json" in step and "window.ANYPLOT_DATA" in step
        assert "grep -qxF 'render: refused 1 request(s) and 0 WebSocket(s)'" in step
        assert 'import text from "/etc/os-release";' in step
        assert "render: error: import ImportRefused plot.tsx:1:" in step


def _allowlist_module():
    spec = importlib.util.spec_from_file_location("import_allowlist", TOOLCHAIN_DIR / "import_allowlist.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _package(root: Path, name: str, version: str, exports: object) -> None:
    folder = root / name
    folder.mkdir(parents=True)
    manifest: dict[str, object] = {"name": name, "version": version}
    if exports is not None:
        manifest["exports"] = exports
    (folder / "package.json").write_text(json.dumps(manifest), encoding="utf-8")


class TestImportAllowlist:
    """The import allowlist (finding 1 of the second opinion on step 3): one JSON file, generated at image build from
    the installed packages' exports maps, which the bundle step's resolve plugin (JS-2) and the validator (JS-3)
    read. Its shape is pinned here."""

    def test_the_shape(self, tmp_path: Path) -> None:
        module = _allowlist_module()
        _package(
            tmp_path,
            "react",
            "19.3.1",
            {
                ".": {"default": "./index.js"},
                "./package.json": "./package.json",
                "./jsx-runtime": {"default": "./jsx-runtime.js"},
            },
        )
        _package(tmp_path, "react-dom", "19.3.1", {".": "./index.js", "./client": "./client.js"})
        _package(tmp_path, "@mui/material", "9.5.0", {".": "./index.js", "./Box": "./Box/index.js", "./internal": None})
        _package(tmp_path, "@mui/x-charts", "9.16.0", {"./BarChart": "./BarChart/index.js", ".": "./index.js"})
        result = module.allowlist(tmp_path)
        assert result == {
            "schema": 1,
            "packages": {"@mui/material": "9.5.0", "@mui/x-charts": "9.16.0", "react": "19.3.1", "react-dom": "19.3.1"},
            "specifiers": [
                "@mui/material",
                "@mui/material/Box",
                "@mui/x-charts",
                "@mui/x-charts/BarChart",
                "react",
                "react-dom",
                "react-dom/client",
                "react/jsx-runtime",
            ],
        }
        assert module.PACKAGES == ("@mui/material", "@mui/x-charts", "react", "react-dom")

    @pytest.mark.parametrize(
        ("exports", "expected"),
        [
            pytest.param("./index.js", ["pkg"], id="a string"),
            pytest.param({"import": "./index.mjs", "require": "./index.cjs"}, ["pkg"], id="conditions only"),
            pytest.param({".": "./index.js", "./package.json": "./package.json"}, ["pkg"], id="package.json is data"),
        ],
    )
    def test_one_entry_point(self, exports: object, expected: list[str]) -> None:
        assert _allowlist_module().specifiers("pkg", {"exports": exports}) == expected

    def test_a_subpath_blocked_under_every_condition_is_not_importable(self) -> None:
        """A `null` target, or conditions and fallback arrays whose every branch is `null`, resolve to nothing."""
        exports = {
            ".": "./index.js",
            "./internal": None,
            "./hidden": {"default": None},
            "./nested": {"import": {"default": None}, "require": None},
            "./fallback": [None, {"default": None}],
            "./node-only": {"node": "./node.js", "default": None},
        }
        assert _allowlist_module().specifiers("pkg", {"exports": exports}) == ["pkg", "pkg/node-only"]

    @pytest.mark.parametrize(
        ("manifest", "message"),
        [
            pytest.param({}, "no exports map", id="no exports map"),
            pytest.param({"exports": {"./*": "./*.js"}}, "pattern", id="a pattern"),
            pytest.param({"exports": {".": "./a.js", "import": "./b.js"}}, "mixes", id="paths and conditions"),
            pytest.param({"exports": {".x": "./a.js"}}, "malformed", id="a malformed key"),
        ],
    )
    def test_an_open_or_malformed_map_fails_the_build(self, manifest: dict, message: str) -> None:
        module = _allowlist_module()
        with pytest.raises(module.AllowlistError, match=message):
            module.specifiers("pkg", manifest)

    def test_a_missing_package_fails_and_the_command_line(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        module = _allowlist_module()
        assert module.main([str(tmp_path)]) == 1
        assert "is not installed" in capsys.readouterr().err
        assert module.main([]) == 2

    def test_the_build_writes_it_next_to_the_harness(self) -> None:
        node = _node_stage()
        assert (
            "python3 -I /opt/anyplot/toolchain/import_allowlist.py /opt/anyplot/node_modules"
            " > /opt/anyplot/js-render/import-allowlist.json" in node
        )
        final = _stages(TOOLCHAIN_DOCKERFILE.read_text(encoding="utf-8"))["final"]
        assert (
            "COPY --from=node /opt/anyplot/js-render/import-allowlist.json /opt/anyplot/js-render/import-allowlist.json"
            in final
        )

    def test_the_installed_packages_when_present(self) -> None:
        """Against a real install (`ANYPLOT_NODE_MODULES`, or the checkout's node_modules after `npm ci`): the counts
        of 2026-10-30 (Fable's second opinion counted the same keys, `./package.json` included)."""
        root = Path(os.environ.get("ANYPLOT_NODE_MODULES", REPO_ROOT / "node_modules"))
        if not (root / "@mui" / "x-charts" / "package.json").is_file():
            pytest.skip("no installed node_modules")
        result = _allowlist_module().allowlist(root)
        lock = json.loads((REPO_ROOT / "package-lock.json").read_text(encoding="utf-8"))["packages"]
        if result["packages"] != {name: lock[f"node_modules/{name}"]["version"] for name in result["packages"]}:
            pytest.skip("the installed node_modules is not the lock's")
        assert "@mui/x-charts/BarChart" in result["specifiers"] and "react/jsx-runtime" in result["specifiers"]
        assert len(result["specifiers"]) == len(set(result["specifiers"]))
