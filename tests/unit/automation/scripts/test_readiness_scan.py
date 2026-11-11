"""automation/scripts/readiness_scan.py: what the agent chat's validator refuses in a new file but not in its predecessor.

The sources are synthetic: a catalogue file changes with every regeneration,
so a test that reads `plots/` would pin a verdict that moves.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from automation.scripts import readiness_scan
from automation.scripts.readiness_scan import build_record, log_line, scan_side, summary_line


SCRIPT = Path(readiness_scan.__file__)
ROOT = SCRIPT.parents[2]
SPEC, LIB = "scatter-basic", "matplotlib"

CLEAN = '''""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: matplotlib 3.11.0 | Python 3.14.9
Quality: pending | Created: 2026-11-10
"""

import os

import matplotlib.pyplot as plt
import pandas as pd

THEME = os.getenv("ANYPLOT_THEME", "light")

# Data
df = pd.DataFrame({"hours": [1, 2, 3, 4], "score": [52, 61, 70, 84]})
X = "hours"
Y = "score"

fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
ax.scatter(df[X], df[Y], color="#009E73")
ax.set_title("scatter-basic · python · matplotlib · anyplot.ai")
plt.savefig(f"plot-{THEME}.png")
'''
BANNED_IMPORT = CLEAN.replace("import pandas as pd", "import json\nimport pandas as pd")
BANNED_NAME = CLEAN.replace("fig, ax", 'open("notes.txt", "w").write("x")\nfig, ax')
FIXED_SAVE = CLEAN.replace('f"plot-{THEME}.png"', '"plot-light.png"')
NO_THEME = CLEAN.replace('THEME = os.getenv("ANYPLOT_THEME", "light")', 'THEME = "light"')
BROKEN = CLEAN + "\nif (:\n"
# More than the five findings the scan's reasons list, over five different rules.
MANY = (
    CLEAN.replace(
        "import pandas as pd", "import pandas as pd\nimport socket\nimport subprocess\nimport json\nimport csv"
    )
    + '\neval("1")\nopen("a")\n__import__("os")\nURL = "https://example.com/a.csv"\n'
)


def _side(code: str, spec_id: str = SPEC, library: str = LIB) -> dict:
    return scan_side(code, spec_id=spec_id, library=library)


def _record(new: str | None, prev: str | None, spec_id: str = SPEC, library: str = LIB) -> dict:
    return build_record(new, prev, spec_id=spec_id, library=library)


# --- one side ------------------------------------------------------------------------------------


def test_an_accepted_file_has_no_refusal_key():
    side = _side(CLEAN)
    assert side == {"status": "clean", "refusals": [], "spec_refused": False, "coupled": []}


@pytest.mark.parametrize(
    ("code", "keys"),
    [
        (BANNED_IMPORT, ["security:banned-import"]),
        (BANNED_NAME, ["security:banned-name"]),
        (FIXED_SAVE, ["savefig-target", "security:savefig-target"]),
        (NO_THEME, ["no-theme", "security:savefig-target"]),
        (BROKEN, ["syntax"]),
    ],
    ids=["banned-import", "banned-name", "fixed-save", "no-theme", "syntax"],
)
def test_a_refused_file_names_why(code, keys):
    side = _side(code)
    assert side["status"] == "blocked" and side["refusals"] == keys
    assert side["spec_refused"] is False


def test_every_broken_security_rule_is_a_key_not_only_the_first_five():
    """The scan's reasons stop at five findings and add `N more findings`; the keys come from the validator itself."""
    side = _side(MANY)
    assert side["refusals"] == [
        "security:banned-import",
        "security:banned-name",
        "security:dunder",
        "security:url-literal",
    ]
    assert not [key for key in side["refusals"] if "more" in key]


def test_a_coupled_file_is_accepted_and_lists_its_categories():
    coupled = CLEAN.replace(
        'df = pd.DataFrame({"hours": [1, 2, 3, 4], "score": [52, 61, 70, 84]})',
        'import numpy as np\n\nrng = np.random.default_rng(1)\ndf = pd.DataFrame({"hours": rng.normal(size=20), "score": rng.normal(size=20)})',
    )
    side = _side(coupled)
    assert side["status"] == "coupled" and side["refusals"] == []
    assert "synthetic-data" in side["coupled"]


def test_a_map_spec_is_refused_whatever_the_code_holds():
    side = _side(CLEAN.replace("scatter-basic", "choropleth-basic"), spec_id="choropleth-basic")
    assert side["status"] == "blocked" and side["spec_refused"] is True
    assert side["refusals"] == []  # map-spec is no key: the code did nothing


def test_a_library_without_a_python_profile_is_unsupported():
    assert _side(CLEAN, library="ggplot2")["status"] == "unsupported"


# --- the record ----------------------------------------------------------------------------------


def test_a_file_the_chat_accepted_and_now_refuses_is_a_regression():
    record = _record(BANNED_IMPORT, CLEAN)
    assert record["verdict"] == "regression"
    assert record["added"] == ["security:banned-import"] and record["removed"] == []
    assert record["new"]["status"] == "blocked" and record["prev"]["status"] == "clean"
    assert summary_line(record) == (
        "**Readiness (record-only):** regression: security:banned-import (new blocked, predecessor clean)"
    )
    assert log_line(record) == (
        "::warning::readiness_scan spec=scatter-basic lib=matplotlib verdict=regression new=blocked prev=clean "
        "added=security:banned-import removed=none"
    )


def test_a_new_key_counts_also_when_the_predecessor_was_refused_for_another():
    record = _record(BANNED_NAME, BANNED_IMPORT)
    assert record["verdict"] == "regression"
    assert record["added"] == ["security:banned-name"] and record["removed"] == ["security:banned-import"]


@pytest.mark.parametrize(
    ("new", "prev", "removed"),
    [
        (CLEAN, CLEAN, []),
        (CLEAN, BANNED_IMPORT, ["security:banned-import"]),  # the new file is better
        (BANNED_IMPORT, BANNED_IMPORT.replace("import json", "import json\nimport csv"), []),  # same rule, fewer hits
        (BANNED_IMPORT, MANY, ["security:banned-name", "security:dunder", "security:url-literal"]),
    ],
    ids=["both-accepted", "refusal-gone", "same-rule", "fewer-rules"],
)
def test_no_new_key_is_no_regression(new, prev, removed):
    record = _record(new, prev)
    assert record["verdict"] == "none" and record["added"] == []
    assert record["removed"] == removed
    assert summary_line(record).startswith("**Readiness (record-only):** no new refusal (new ")
    assert log_line(record).startswith("::notice::readiness_scan ")


def test_a_first_generation_has_no_verdict_on_its_refusals():
    record = _record(BANNED_IMPORT, None)
    assert record["verdict"] == "first_generation" and record["prev"] is None
    assert record["added"] == [] and record["new"]["refusals"] == ["security:banned-import"]
    assert summary_line(record) == "**Readiness (record-only):** first generation (new blocked)"
    assert "verdict=first_generation new=blocked prev=n/a added=none removed=none" in log_line(record)


def test_a_map_spec_is_excluded_even_with_a_new_refusal():
    old = CLEAN.replace("scatter-basic", "choropleth-basic")
    record = _record(BANNED_IMPORT.replace("scatter-basic", "choropleth-basic"), old, spec_id="choropleth-basic")
    assert record["verdict"] == "excluded" and record["added"] == []
    assert record["new"]["refusals"] == ["security:banned-import"]  # still recorded
    assert summary_line(record).startswith("**Readiness (record-only):** excluded")


@pytest.mark.parametrize(("new", "library"), [(None, LIB), (CLEAN, "ggplot2")], ids=["no-file", "no-profile"])
def test_nothing_to_scan_is_unreadable(new, library):
    record = _record(new, CLEAN, library=library)
    assert record["verdict"] == "unreadable" and record["added"] == []
    assert summary_line(record).startswith("**Readiness (record-only):** unreadable")
    assert "verdict=unreadable" in log_line(record)


def test_a_record_holds_identifiers_only():
    """Reasons and hints quote code; the record must not, because it is staged in a public bucket."""
    record = _record(MANY, BANNED_NAME)
    text = json.dumps(record)
    assert "example.com" not in text and "notes.txt" not in text and "socket" not in text
    assert set(record) == {"version", "spec_id", "library", "language", "verdict", "new", "prev", "added", "removed"}


# --- the command, as the workflows run it ----------------------------------------------------------


def _bare_tree(tmp_path: Path) -> Path:
    """What the workflow step extracts from its ref: the validator and core, without any `agents/__init__.py`."""
    tree = tmp_path / "readiness-tools"
    shutil.copytree(ROOT / "agents" / "anyplot" / "code", tree / "agents" / "anyplot" / "code")
    for name in ("schemas.py", "language.py"):
        shutil.copy(ROOT / "agents" / "anyplot" / name, tree / "agents" / "anyplot" / name)
    shutil.copytree(ROOT / "core", tree / "core", ignore=shutil.ignore_patterns("__pycache__"))
    (tree / "automation" / "scripts").mkdir(parents=True)
    shutil.copy(SCRIPT, tree / "automation" / "scripts" / "readiness_scan.py")
    return tree


def _run(tree: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(tree / "automation" / "scripts" / "readiness_scan.py"), "scan", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin", "GITHUB_STEP_SUMMARY": str(cwd / "summary")},
    )


def test_the_bare_copy_scans_without_the_agent_runtime(tmp_path):
    """No `agents/__init__.py` and no `agents/anyplot/__init__.py`: the ADK import of the package never runs.

    The workspace holds a hostile `core` and `agents`, as a generator could leave them; `-I` keeps the working
    directory off the import path, so the copy's own tree is what gets imported.
    """
    tree = _bare_tree(tmp_path)
    assert not (tree / "agents" / "__init__.py").exists() and not (tree / "agents" / "anyplot" / "__init__.py").exists()
    workspace = tmp_path / "ws"
    for package in ("core", "agents"):
        (workspace / package).mkdir(parents=True)
        (workspace / package / "__init__.py").write_text('raise SystemExit("the workspace was imported")\n')
    (workspace / "new.py").write_text(BANNED_IMPORT, encoding="utf-8")
    (workspace / "prev.py").write_text(CLEAN, encoding="utf-8")
    result = _run(
        tree, workspace, "--new", "new.py", "--prev", "prev.py", "--spec-id", SPEC, "--library", LIB, "--out", "r.json"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == (
        "::warning::readiness_scan spec=scatter-basic lib=matplotlib verdict=regression new=blocked prev=clean "
        "added=security:banned-import removed=none"
    )
    assert (workspace / "summary").read_text(encoding="utf-8").startswith("**Readiness (record-only):** regression: ")
    record = json.loads((workspace / "r.json").read_text(encoding="utf-8"))
    assert record["version"] == 1 and record["verdict"] == "regression"


def test_a_missing_file_is_recorded_not_raised(tmp_path):
    tree = _bare_tree(tmp_path)
    result = _run(tree, tmp_path, "--new", "absent.py", "--prev", "absent-too.py", "--spec-id", SPEC, "--library", LIB)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verdict=unreadable new=missing prev=n/a" in result.stdout
