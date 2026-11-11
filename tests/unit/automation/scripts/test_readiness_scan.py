"""automation/scripts/readiness_scan.py: what the agent chat's validator refuses in a new file but not in its predecessor.

The sources are synthetic: a catalogue file changes with every regeneration,
so a test that reads `plots/` would pin a verdict that moves.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

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
    assert side == {"status": "clean", "refusals": [], "spec_refused": False, "coupled": [], "findings": {}}


def test_a_rule_that_fires_more_often_is_counted_but_is_no_new_key():
    twice = BANNED_IMPORT.replace("import json", "import json\nimport socket")
    assert _side(BANNED_IMPORT)["findings"] == {"banned-import": 1}
    assert _side(twice)["findings"] == {"banned-import": 2}
    record = _record(twice, BANNED_IMPORT)
    assert record["verdict"] == "none" and record["added"] == []
    assert (record["new"]["findings"], record["prev"]["findings"]) == ({"banned-import": 2}, {"banned-import": 1})


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


def test_a_file_the_normaliser_cannot_take_is_an_error_and_a_map_spec_stays_excluded(monkeypatch):
    from agents.anyplot.code import normalise as normalise_module

    def boom(code: str, *, library: str) -> str:
        raise ValueError("cannot normalise")

    monkeypatch.setattr(normalise_module, "normalise", boom)
    side = _side(CLEAN)
    assert (side["status"], side["refusals"], side["spec_refused"]) == ("error", ["error:valueerror"], False)
    assert _record(CLEAN, None)["verdict"] == "first_generation"
    on_map = _side(CLEAN, spec_id="choropleth-basic")
    assert (on_map["status"], on_map["spec_refused"]) == ("error", True)
    assert _record(CLEAN, None, spec_id="choropleth-basic")["verdict"] == "excluded"


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


PACKAGE_FILES = ("agents/__init__.py", "agents/anyplot/__init__.py")


def _step_script(workflow: str) -> str:
    document = yaml.safe_load((ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8"))
    steps = [step for job in document["jobs"].values() for step in job.get("steps", [])]
    (script,) = [str(step["run"]) for step in steps if step.get("name") == "Readiness scan (record-only)"]
    return script


def _archived_paths(workflow: str) -> list[str]:
    """The paths the workflow's own `git archive "$GITHUB_SHA" … | tar` line names, read from the step script."""
    match = re.search(
        r'git archive "\$GITHUB_SHA" (.+?) \| tar ', _step_script(workflow).replace("\\\n", " "), re.DOTALL
    )
    assert match, "the step no longer extracts the validator with git archive"
    return match.group(1).split()


def _bare_tree(tmp_path: Path, workflow: str = "impl-generate.yml", *, package_files: bool = True) -> Path:
    """What the workflow step builds, path for path: the archived paths, then the two empty package files."""
    tree = tmp_path / "readiness-tools"
    for relative in _archived_paths(workflow):
        source, target = ROOT / relative, tree / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy(source, target)
    assert not any((tree / relative).exists() for relative in PACKAGE_FILES)  # the archive never brings the real ones
    if package_files:
        assert ': > "$TOOLS/agents/__init__.py"; : > "$TOOLS/agents/anyplot/__init__.py"' in _step_script(workflow)
        for relative in PACKAGE_FILES:
            (tree / relative).touch()
    return tree


def _run(tree: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(tree / "automation" / "scripts" / "readiness_scan.py"), "scan", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin", "GITHUB_STEP_SUMMARY": str(cwd / "summary")},
    )


@pytest.mark.parametrize("workflow", ["impl-generate.yml", "impl-repair.yml"])
def test_the_bare_copy_scans_without_the_agent_runtime(tmp_path, workflow):
    """The package files of the copy are empty, so the ADK import of the real `agents/anyplot/__init__.py` never runs.

    The tree holds exactly the paths the workflow's `git archive` line names, so a path the validator needs and
    the step forgets fails here. The workspace holds a hostile `core` and `agents`, as a generator could leave
    them; `-I` keeps the working directory off the import path, so the copy's own tree is what gets imported.
    """
    tree = _bare_tree(tmp_path, workflow)
    assert [(tree / relative).read_text() for relative in PACKAGE_FILES] == ["", ""]
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


HOSTILE = 'raise SystemExit("a foreign agents package was imported")\n'
# Runs the copy's scanner with one more directory at the END of the import path, where site-packages sits.
DRIVER = (
    "import runpy, sys\n"
    "sys.path.append(sys.argv.pop(1))\n"
    "script = sys.argv.pop(1)\n"
    "sys.argv[0] = script\n"
    "runpy.run_path(script, run_name='__main__')\n"
)


def _run_with_site_packages(tree: Path, site: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    (cwd / "new.py").write_text(CLEAN, encoding="utf-8")
    script = str(tree / "automation" / "scripts" / "readiness_scan.py")
    return subprocess.run(
        [sys.executable, "-I", "-c", DRIVER, str(site), script, "scan", "--new", "new.py"]
        + ["--spec-id", SPEC, "--library", LIB],
        capture_output=True,
        text=True,
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin"},
    )


def test_a_regular_agents_package_in_site_packages_does_not_win_the_import(tmp_path):
    """`openai-agents` installs a top-level `agents`; a session could leave one too. The copy's package files win."""
    site = tmp_path / "site-packages"
    (site / "agents").mkdir(parents=True)
    (site / "agents" / "__init__.py").write_text(HOSTILE, encoding="utf-8")
    result = _run_with_site_packages(_bare_tree(tmp_path), site, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verdict=first_generation new=clean" in result.stdout


def test_without_its_package_files_the_copy_would_lose_the_import(tmp_path):
    """Why the step writes them: as namespace packages the extracted directories lose to a regular package."""
    site = tmp_path / "site-packages"
    (site / "agents").mkdir(parents=True)
    (site / "agents" / "__init__.py").write_text(HOSTILE, encoding="utf-8")
    result = _run_with_site_packages(_bare_tree(tmp_path, package_files=False), site, tmp_path)
    assert result.returncode != 0
    assert "a foreign agents package was imported" in result.stderr


def test_a_validator_from_outside_the_scripts_tree_stops_the_scan(tmp_path, monkeypatch):
    """A scan by another validator than this ref's would be a wrong record; no record is the honest answer."""
    monkeypatch.setattr(readiness_scan, "TREE", tmp_path)
    monkeypatch.setattr(sys, "path", list(sys.path))  # scan_side puts TREE on the path
    with pytest.raises(ImportError, match="was imported from outside"):
        scan_side(CLEAN, spec_id=SPEC, library=LIB)


def test_a_missing_file_is_recorded_not_raised(tmp_path):
    tree = _bare_tree(tmp_path)
    result = _run(tree, tmp_path, "--new", "absent.py", "--prev", "absent-too.py", "--spec-id", SPEC, "--library", LIB)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verdict=unreadable new=missing prev=n/a" in result.stdout


# --- the command, in this process ------------------------------------------------------------------


def test_scan_prints_the_line_and_writes_the_summary_and_the_record(tmp_path, monkeypatch, capsys):
    (tmp_path / "new.py").write_text(BANNED_NAME, encoding="utf-8")
    (tmp_path / "prev.py").write_text(CLEAN, encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    arguments = ["scan", "--new", str(tmp_path / "new.py"), "--prev", str(tmp_path / "prev.py")]
    code = readiness_scan.main([*arguments, "--spec-id", SPEC, "--library", LIB, "--out", str(tmp_path / "r.json")])
    assert code == 0
    assert capsys.readouterr().out.strip() == (
        "::warning::readiness_scan spec=scatter-basic lib=matplotlib verdict=regression new=blocked prev=clean "
        "added=security:banned-name removed=none"
    )
    assert (tmp_path / "summary").read_text(encoding="utf-8") == (
        "**Readiness (record-only):** regression: security:banned-name (new blocked, predecessor clean)\n"
    )
    record = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert record["added"] == ["security:banned-name"] and record["new"]["findings"] == {"banned-name": 1}


@pytest.mark.parametrize("content", [None, b"\xff\xfe not utf-8"], ids=["missing", "not-utf-8"])
def test_scan_reads_an_unreadable_file_as_no_file(tmp_path, monkeypatch, capsys, content):
    """No summary file and no --out: the line alone, and still exit 0."""
    if content is not None:
        (tmp_path / "new.py").write_bytes(content)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    code = readiness_scan.main(["scan", "--new", str(tmp_path / "new.py"), "--spec-id", SPEC, "--library", LIB])
    assert code == 0
    assert "verdict=unreadable new=missing prev=n/a added=none removed=none" in capsys.readouterr().out
    assert sorted(path.name for path in tmp_path.iterdir()) == ([] if content is None else ["new.py"])


def test_a_validator_that_crashes_is_a_key_of_its_own(monkeypatch):
    """The scan blocks a file whose validator fails; the key says so instead of naming no rule at all."""
    from agents.anyplot.code import validate

    def boom(code: str, *, library: str) -> list:
        raise RuntimeError("validator down")

    monkeypatch.setattr(validate, "validate_security", boom)
    side = _side(BANNED_IMPORT)  # the scan keeps its own reference, so it still reports the finding
    assert side["status"] == "blocked"
    assert side["refusals"] == ["security:validator-failed"] and side["findings"] == {}


def test_a_name_that_is_no_identifier_never_reaches_the_record():
    assert readiness_scan._token("banned-import") == "banned-import"
    assert readiness_scan._token("Not an identifier: x = 1") == "other"
