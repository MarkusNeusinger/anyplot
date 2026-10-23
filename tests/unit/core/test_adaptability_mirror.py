"""The single-file mirror `automation/scripts/adaptability_check.py` against `core/adaptability.py`.

The workflow runner runs the checker from a copy with its system Python, where `core`
is not importable (the pattern of `automation/scripts/regen_gate.py` and
`tests/unit/core/test_defects.py`). The mirror is generated (`core/adaptability_mirror.py`):
these tests pin the file to the build, keep it standard-library only, run it with `core`
out of reach, and compare its records with the module's on a catalogue sample.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from core import adaptability, spec_roles
from core.adaptability_mirror import MIRROR, ROOT, SOURCES, build_mirror


MIRROR_PATH = ROOT / MIRROR
PLOTS = ROOT / "plots"


def _load_mirror() -> ModuleType:
    spec = importlib.util.spec_from_file_location("adaptability_check_mirror", MIRROR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their annotations through sys.modules
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mirror() -> ModuleType:
    return _load_mirror()


def test_the_mirror_is_the_build() -> None:
    """A change to core/spec_roles.py or core/adaptability.py needs `uv run python -m core.adaptability_mirror`."""
    assert MIRROR_PATH.read_text(encoding="utf-8") == build_mirror(), (
        "automation/scripts/adaptability_check.py is stale: run `uv run python -m core.adaptability_mirror`"
    )


def test_the_mirror_imports_only_the_standard_library() -> None:
    tree = ast.parse(MIRROR_PATH.read_text(encoding="utf-8"))
    modules = {
        (node.module if isinstance(node, ast.ImportFrom) else alias.name).split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom) and (not isinstance(node, ast.ImportFrom) or node.level == 0)
        for alias in node.names
    }
    assert modules <= set(sys.stdlib_module_names) | {"__future__"}, modules - set(sys.stdlib_module_names)


def _top_level_names(path: Path) -> list[str]:
    names: list[str] = []
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef | ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names.extend(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    return names


def test_every_definition_of_both_modules_is_in_the_mirror(mirror: ModuleType) -> None:
    for module in (spec_roles, adaptability):
        missing = [name for name in _top_level_names(Path(module.__file__ or "")) if not hasattr(mirror, name)]
        assert not missing, (module.__name__, missing)


def test_the_two_modules_share_no_top_level_name() -> None:
    """The mirror concatenates them: a shared name would silently shadow the first module's definition."""
    shared = set(_top_level_names(Path(spec_roles.__file__ or ""))) & set(
        _top_level_names(Path(adaptability.__file__ or ""))
    )
    assert not shared, shared


def test_the_sources_are_the_two_modules() -> None:
    assert [source.as_posix() for source in SOURCES] == ["core/spec_roles.py", "core/adaptability.py"]


@pytest.mark.skipif(not PLOTS.is_dir(), reason="plots/ is not checked out")
def test_the_mirror_agrees_with_the_module_on_the_catalogue(mirror: ModuleType) -> None:
    paths = sorted(PLOTS.glob("*/implementations/python/*.py"))[::7]
    assert len(paths) > 300
    for path in paths:
        ours = adaptability.check_file(path).to_dict()
        theirs = mirror.check_file(path).to_dict()
        assert ours == theirs, path


def test_the_mirror_runs_without_core(tmp_path: Path) -> None:
    """`python -I` from a directory without `core`: the runner's situation."""
    copy = tmp_path / "adaptability_check.py"
    copy.write_text(MIRROR_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    impl = PLOTS / "bar-grouped/implementations/python/matplotlib.py"
    result = subprocess.run(
        [sys.executable, "-I", str(copy), "check", str(impl)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    record = json.loads(result.stdout.splitlines()[0])
    assert record == adaptability.check_file(impl).to_dict()
    assert any(line.startswith("CQ-01 (code):") for line in result.stdout.splitlines()[1:])
