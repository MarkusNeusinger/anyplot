"""impl-review's implementation header writer, run the way the workflow runs it.

The JavaScript header logic is unit-tested in
tests/unit/automation/scripts/test_impl_header.py. These tests pin the
wiring that has no other local loop: "Checkout PR code" saves the writer at
the workflow's ref, and the heredoc of "Update metadata and implementation
header" imports that copy and writes one header whatever shape the file had.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import regen_gate
from automation.scripts.render_hash import code_hash


ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "impl-review.yml"
STEP = "Update metadata and implementation header"


def _step(name: str) -> dict[str, Any]:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    matches = [s for job in workflow["jobs"].values() for s in job.get("steps", []) if s.get("name") == name]
    assert len(matches) == 1, name
    return matches[0]


def _header_script() -> str:
    run = _step(STEP)["run"]
    return run.split("python3 - <<'EOF'\n", 1)[1].split("\nEOF\n", 1)[0]


def _run(tmp_path: Path, language: str, filename: str, content: str) -> str:
    tools = tmp_path / "runner" / "regen-tools"
    tools.mkdir(parents=True)
    shutil.copy(ROOT / "automation" / "scripts" / "impl_header.py", tools / "impl_header.py")
    impl = tmp_path / filename
    impl.write_text(content, encoding="utf-8")
    env = {
        **os.environ,
        "RUNNER_TEMP": str(tmp_path / "runner"),
        "IMPL_FILE": str(impl),
        "LANGUAGE": language,
        "SPEC_ID": "gauge-basic",
        "TITLE": "Basic Gauge Chart",
        "LIBRARY": "d3",
        "LIBRARY_VERSION": "7.9.0",
        "LANGUAGE_VERSION": "22.23.3",
        "SCORE": "93",
        "DATE_INFO": "Updated: 2026-10-24",
    }
    # Run from an empty directory so the repository's automation/ is not on
    # the path: the import must resolve to the RUNNER_TEMP copy.
    work = tmp_path / "work"
    work.mkdir()
    subprocess.run(
        [sys.executable, "-c", _header_script()], cwd=work, env=env, check=True, capture_output=True, text=True
    )
    return impl.read_text(encoding="utf-8")


JS_HEADER = (
    "// anyplot.ai\n"
    "// gauge-basic: Basic Gauge Chart\n"
    "// Library: d3 7.9.0 | JavaScript 22.23.3\n"
    "// Quality: 93/100 | Updated: 2026-10-24\n"
)
SQUARE = "//# anyplot-orientation: square\n"
OLD = "// anyplot.ai\n// gauge-basic: Basic Gauge Chart\n// Library: d3 7.9.0 | JavaScript 22\n// Quality: pending | Created: 2026-06-30\n"
CODE = "\nconst t = window.ANYPLOT_TOKENS;\n"


def test_the_writer_is_saved_at_the_workflow_ref():
    script = _step("Checkout PR code")["run"]
    copy = script[: script.index("git fetch origin")]
    assert "automation/scripts/impl_header.py" in copy
    assert '"$RUNNER_TEMP/regen-tools/"' in copy


def test_the_step_imports_the_saved_copy():
    script = _header_script()
    assert 'os.path.join(os.environ["RUNNER_TEMP"], "regen-tools")' in script
    assert "from impl_header import replace_js_header" in script
    # The old prepend fallback is gone.
    assert "(?!#)" not in script


@pytest.mark.parametrize(
    "before",
    [
        pytest.param(SQUARE + OLD + CODE, id="directive_first"),
        pytest.param(JS_HEADER.replace("93", "90") + SQUARE + CODE, id="header_then_directive"),
        pytest.param(JS_HEADER.replace("93", "90") + SQUARE + OLD + CODE, id="stale_second_block"),
    ],
)
def test_javascript_comes_out_with_one_header(tmp_path, before):
    assert _run(tmp_path, "javascript", "d3.js", before) == JS_HEADER + SQUARE + CODE


def test_python_header_is_unchanged(tmp_path):
    before = '""" anyplot.ai\ngauge-basic: Basic Gauge Chart\nLibrary: x\nQuality: pending\n"""\n\nimport x\n'
    out = _run(tmp_path, "python", "matplotlib.py", before)
    assert out.startswith('""" anyplot.ai\ngauge-basic: Basic Gauge Chart\nLibrary: d3 7.9.0 | Python 22.23.3\n')
    assert out.endswith('Quality: 93/100 | Updated: 2026-10-24\n"""\n\nimport x\n')


# --- the code hash of render_hash.py leaves out exactly what this writer replaces ----------------
#
# impl-review's render-hash check has to match the head after this step's
# commit (a manual re-review), so the hash and the writer must agree on what
# the header is, for every shape of file the writer accepts.

PY_HEADER = '"""anyplot.ai\ngauge-basic: Basic Gauge Chart\nLibrary: x\nQuality: pending | Created: 2026-11-15\n"""\n'
R_HEADER = "#' anyplot.ai\n#' gauge-basic: Basic Gauge Chart\n#' Quality: pending | Created: 2026-11-15\n"
JULIA_HEADER = "# anyplot.ai\n# gauge-basic: Basic Gauge Chart\n# Quality: pending | Created: 2026-11-15\n"
PY_CODE = "\nimport x\n\nx.plot()  # the plot\n"
R_CODE = "\nlibrary(ggplot2)\n# the plot\nggsave('plot.png')\n"
JULIA_CODE = '\nusing CairoMakie\n# the plot\nsave("plot.png", fig)\n'
REWRITES = [
    pytest.param("python", "matplotlib.py", PY_HEADER + PY_CODE, id="python"),
    pytest.param("python", "matplotlib.py", PY_CODE.lstrip("\n"), id="python-no-header"),
    pytest.param("python", "matplotlib.py", "# ruff: noqa\n" + PY_HEADER + PY_CODE, id="python-comment-first"),
    pytest.param("python", "matplotlib.py", "\n" + PY_HEADER + PY_CODE, id="python-blank-line-first"),
    pytest.param("python", "matplotlib.py", PY_HEADER + '"""Notes."""\n' + PY_CODE, id="python-second-docstring"),
    pytest.param("python", "matplotlib.py", (PY_HEADER + PY_CODE).replace("\n", "\r\n"), id="python-crlf"),
    pytest.param("r", "ggplot2.R", R_HEADER + R_CODE, id="r"),
    pytest.param("r", "ggplot2.R", R_CODE.lstrip("\n"), id="r-no-header"),
    pytest.param("r", "ggplot2.R", "# setup\n" + R_HEADER + R_CODE, id="r-comment-first"),
    pytest.param("r", "ggplot2.R", R_HEADER + "#' more roxygen\n" + R_CODE, id="r-longer-block"),
    pytest.param("julia", "makie.jl", JULIA_HEADER + JULIA_CODE, id="julia"),
    pytest.param("julia", "makie.jl", JULIA_CODE.lstrip("\n"), id="julia-no-header"),
    pytest.param("julia", "makie.jl", "#=\nnotes\n=#\n" + JULIA_HEADER + JULIA_CODE, id="julia-block-comment-first"),
    pytest.param("julia", "makie.jl", JULIA_HEADER + "# a comment right below\n" + JULIA_CODE, id="julia-longer-block"),
    pytest.param("javascript", "d3.js", OLD + SQUARE + CODE, id="javascript"),
    pytest.param("javascript", "d3.js", SQUARE + OLD + CODE, id="javascript-directive-first"),
    pytest.param("javascript", "d3.js", JS_HEADER + SQUARE + OLD + CODE, id="javascript-stale-second-block"),
    pytest.param("javascript", "d3.js", SQUARE + CODE, id="javascript-no-header"),
    pytest.param("javascript", "d3.js", CODE.lstrip("\n"), id="javascript-no-header-no-directive"),
]


@pytest.mark.parametrize(("language", "filename", "before"), REWRITES)
def test_the_code_hash_is_the_same_before_and_after_the_header_commit(tmp_path, language, filename, before):
    after = _run(tmp_path / "first", language, filename, before)
    assert after != before  # the writer did rewrite the file
    assert code_hash(after.encode(), language) == code_hash(before.encode(), language)
    # A second review writes the header again, with another score.
    again = _run(tmp_path / "second", language, filename, after.replace("93/100", "88/100"))
    assert code_hash(again.encode(), language) == code_hash(before.encode(), language)


@pytest.mark.parametrize(("language", "filename", "before"), REWRITES)
def test_the_code_hash_still_sees_a_change_below_the_header(tmp_path, language, filename, before):
    after = _run(tmp_path, language, filename, before)
    edited = after.replace("x.plot()", "x.plot(1)").replace("ggsave('plot.png')", "ggsave('p.png')")
    edited = edited.replace('save("plot.png", fig)', 'save("p.png", fig)').replace("ANYPLOT_TOKENS", "ANYPLOT_SIZE")
    assert edited != after
    assert code_hash(edited.encode(), language) != code_hash(before.encode(), language)


# --- the whole way from staging to a re-review, with a score in the file ------------------------
#
# impl-generate stages the hash of the file as the generator left it, and a
# regeneration or an adopted file still carries the stored `Quality: N/100`.
# The commit holds the reset form (`sanitize-source --pending`), and the
# review's header commit follows. When the header is not the block the writer
# replaces, the writer prepends a new one and the old score line stays in the
# code: it must not count with its number on the staged side only.

SCORED_PY = PY_HEADER.replace("pending", "85/100")
SCORED_R = R_HEADER.replace("pending", "85/100")
SCORED_JULIA = JULIA_HEADER.replace("pending", "85/100")
SCORED_JS = OLD.replace("pending", "85/100")
SCORED = [
    pytest.param("python", "matplotlib.py", SCORED_PY + PY_CODE, id="python"),
    pytest.param("python", "matplotlib.py", "#!/usr/bin/env python3\n" + SCORED_PY + PY_CODE, id="python-shebang"),
    pytest.param("python", "matplotlib.py", "# -*- coding: utf-8 -*-\n" + SCORED_PY + PY_CODE, id="python-coding"),
    pytest.param("python", "matplotlib.py", SCORED_PY.replace('"""', "'''") + PY_CODE, id="python-single-quotes"),
    pytest.param("r", "ggplot2.R", SCORED_R + R_CODE, id="r"),
    pytest.param("r", "ggplot2.R", SCORED_R.replace("#' ", "# ") + R_CODE, id="r-hash-header"),
    pytest.param("julia", "makie.jl", SCORED_JULIA + JULIA_CODE, id="julia"),
    pytest.param("julia", "makie.jl", SCORED_JULIA.replace("# ", "#' ") + JULIA_CODE, id="julia-roxygen-header"),
    pytest.param("javascript", "d3.js", SCORED_JS + SQUARE + CODE, id="javascript"),
    pytest.param("javascript", "d3.js", "'use strict';\n" + SCORED_JS + SQUARE + CODE, id="javascript-code-first"),
]


@pytest.mark.parametrize(("language", "filename", "generated"), SCORED)
def test_a_scored_file_matches_after_the_reset_and_the_header_commit(tmp_path, language, filename, generated):
    staged = code_hash(generated.encode(), language)
    committed = regen_gate.reset_header_score(generated)
    assert committed != generated  # the pipeline's reset did change the file
    assert code_hash(committed.encode(), language) == staged
    reviewed = _run(tmp_path, language, filename, committed)
    assert reviewed != committed
    assert code_hash(reviewed.encode(), language) == staged


@pytest.mark.parametrize(("language", "filename", "generated"), SCORED)
def test_a_scored_file_still_shows_a_change_of_its_code(tmp_path, language, filename, generated):
    reviewed = _run(tmp_path, language, filename, regen_gate.reset_header_score(generated))
    edited = reviewed.replace("x.plot()", "x.plot(1)").replace("ggsave('plot.png')", "ggsave('p.png')")
    edited = edited.replace('save("plot.png", fig)', 'save("p.png", fig)').replace("ANYPLOT_TOKENS", "ANYPLOT_SIZE")
    assert edited != reviewed
    assert code_hash(edited.encode(), language) != code_hash(generated.encode(), language)
