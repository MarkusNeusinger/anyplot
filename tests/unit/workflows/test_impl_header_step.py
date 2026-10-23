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
