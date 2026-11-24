"""Example datasets: a hint at eligibility, refused in every form that runs (owner decision of 2026-11-23).

The chat never runs a catalogue original: it runs the adapted working form, after `validate_security` passed it,
with its data from `df = load_user_data()`. So the eligibility scan (`readiness.scan`, through the validator's
`validate_original`) reports an example dataset the original loads (scikit-learn's built-in toy loaders and
generators, and `sns.load_dataset`, which downloads its CSV) as a `built-in-dataset` coupling hint, while the adapted
and the run form are refused for it exactly as before. The pipeline's side, that nothing renders the original, is
`tests/unit/agents/runtime/test_builtin_datasets_flow.py`.
"""

import re

import pytest

from agents.anyplot.code.normalise import normalise
from agents.anyplot.code.readiness import Readiness, scan
from agents.anyplot.code.validate import (
    BUILTIN_DATASET_RULE,
    PLACEHOLDER,
    SKLEARN_BUILTIN_DATASETS,
    Finding,
    validate_original,
    validate_security,
)
from agents.anyplot.render.runtimes import runtime_for
from agents.anyplot.schemas import MAX_NOTE_CHARS
from core.utils import strip_noqa_comments

from .conftest import CATALOGUE_FILES, REPO_ROOT, source


THEME_LINE = 'THEME = os.getenv("ANYPLOT_THEME", "light")'
MATPLOTLIB_SAVE = 'plt.savefig(f"plot-{THEME}.png", dpi=400)\n'


def matplotlib_file(imports: str, data: str) -> str:
    """A minimal catalogue-shaped matplotlib or seaborn file: `imports` after pyplot's, `data` after the theme block,
    and a scatter of `x` against `y`."""
    head = f"import os\n\nimport matplotlib.pyplot as plt\nimport numpy as np\n{imports}\n\n{THEME_LINE}\n"
    plot = "fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)\nax.scatter(x, y)\n"
    return head + data + "\n" + plot + MATPLOTLIB_SAVE


PLOTLY_ORIGINAL = source("""
    import os

    import plotly.graph_objects as go
    import seaborn as sns

    THEME = os.getenv("ANYPLOT_THEME", "light")
    raw = sns.load_dataset("titanic")[["class", "fare"]].dropna()
    fig = go.Figure(go.Bar(x=raw["class"], y=raw["fare"]))
    fig.update_layout(width=1600, height=900).write_json(f"plot-{THEME}.json")
""")
"""parallel-categories-basic's plotly file in miniature: it imports seaborn for `sns.load_dataset` alone, and seaborn
is no import of plotly's profile."""

# (case id, library, original, the lines of the example dataset, the SECURITY rules the strict entry finds there)
ORIGINALS: list[tuple[str, str, str, list[int], set[str]]] = [
    (
        "make_moons",
        "matplotlib",
        matplotlib_file(
            "from sklearn.datasets import make_moons",
            "X, labels = make_moons(n_samples=200, noise=0.25, random_state=42)\nx, y = X[:, 0], X[:, 1]",
        ),
        [5, 8],
        {"banned-import"},
    ),
    (
        "load_iris",
        "matplotlib",
        matplotlib_file(
            "from sklearn.datasets import load_iris",
            'iris = load_iris(as_frame=True).frame\nx, y = iris["sepal length (cm)"], iris["petal length (cm)"]',
        ),
        [5, 8],
        {"banned-import", "banned-call"},
    ),
    (
        "sns.load_dataset-seaborn",
        "seaborn",
        matplotlib_file(
            "import seaborn as sns",
            'penguins = sns.load_dataset("penguins").dropna()\nx, y = penguins["flipper_length_mm"], penguins["bill_depth_mm"]',
        ),
        [8],
        {"banned-call"},
    ),
    ("sns.load_dataset-plotly", "plotly", PLOTLY_ORIGINAL, [4, 7], {"banned-import", "banned-call"}),
]
ORIGINAL_IDS = [case[0] for case in ORIGINALS]


def working_form(original: str) -> str:
    """The original as an adaptation that kept its loader: the placeholder added after the theme block, nothing else
    changed (what the pipeline checks when the adapter left the data block as it was)."""
    return original.replace(f"{THEME_LINE}\n", f"{THEME_LINE}\n{PLACEHOLDER}\n", 1)


def rules_by_line(findings: list[Finding]) -> dict[int | None, set[str]]:
    lines: dict[int | None, set[str]] = {}
    for finding in findings:
        lines.setdefault(finding.line, set()).add(finding.rule)
    return lines


def hint_of(result: Readiness) -> str:
    (hint,) = [hint for hint in result.hints if hint.startswith("Example dataset loaded at")]
    return hint


@pytest.mark.parametrize(("case", "library", "original", "lines", "strict"), ORIGINALS, ids=ORIGINAL_IDS)
def test_an_original_that_loads_a_built_in_dataset_is_eligible_with_the_hint(
    case: str, library: str, original: str, lines: list[int], strict: set[str]
) -> None:
    """The eligibility scan accepts the original, and its hint names the import and every loader line for the adapter."""
    result = scan(original, spec_id="scatter-basic", library=library, enabled_libraries=[library])

    assert result.status == "coupled", result.reasons
    assert not any(reason.startswith("security") for reason in result.reasons)
    count = len(lines)
    assert f"built-in-dataset: {count} line{'s' if count != 1 else ''}" in result.reasons
    hint = hint_of(result)
    assert len(hint) <= MAX_NOTE_CHARS
    assert [int(line) for line in re.findall(r"\bline (\d+) `", hint)] == lines
    assert "df = load_user_data()" in hint and "drop every import that only the loader uses" in hint
    # One hint per line: a `sklearn.datasets` call is no `synthetic-data` line as well.
    assert not any(hint.startswith("Synthetic data generation") and "make_moons" in hint for hint in result.hints)


def test_the_hint_quotes_each_line_as_the_parser_counts_it_without_its_comment() -> None:
    """A string may hold a form feed or U+2028, which `str.splitlines` breaks at and the parser does not: the hint
    still quotes the line its number names, and like every other category it leaves the line's comment out."""
    original = matplotlib_file(
        "from sklearn.datasets import make_moons  # example data",
        'title = "moons and\x0cmore # not a comment"\n'
        "X, labels = make_moons(n_samples=200, random_state=42)  # the moons\n"
        "x, y = X[:, 0], X[:, 1]",
    )

    result = scan(original, spec_id="scatter-basic", library="matplotlib", enabled_libraries=["matplotlib"])

    hint = hint_of(result)
    assert re.findall(r"\bline (\d+) `([^`]*)`", hint) == [
        ("5", "from sklearn.datasets import make_moons"),
        ("9", "X, labels = make_moons(n_samples=200, random_st…"),
    ]


@pytest.mark.parametrize(("case", "library", "original", "lines", "strict"), ORIGINALS, ids=ORIGINAL_IDS)
def test_the_eligibility_entry_differs_from_the_strict_one_only_on_the_dataset_lines(
    case: str, library: str, original: str, lines: list[int], strict: set[str]
) -> None:
    """`validate_original` reports the dataset's lines as `built-in-dataset` and nothing else; `validate_security`
    refuses the same original with the rules it always had (the import the allowlist refuses, the loader name)."""
    assert rules_by_line(validate_original(original, library=library)) == dict.fromkeys(lines, {BUILTIN_DATASET_RULE})
    found = rules_by_line(validate_security(original, library=library))
    assert set(found) <= set(lines)
    assert set().union(*found.values()) == strict


@pytest.mark.parametrize(("case", "library", "original", "lines", "strict"), ORIGINALS, ids=ORIGINAL_IDS)
def test_the_adapted_and_the_run_form_that_keep_the_loader_are_refused_under_security(
    case: str, library: str, original: str, lines: list[int], strict: set[str]
) -> None:
    """What may run is checked by `validate_security` (the runtime's `security`, which the pipeline's `_check` calls):
    a working form that kept the loader is refused for it, and so is its run form, exactly as before the decision."""
    working = working_form(original)
    runtime = runtime_for(library)

    assert {finding.rule for finding in runtime.security(working)} == strict
    assert not any(finding.rule == BUILTIN_DATASET_RULE for finding in validate_security(working, library=library))
    run_form = runtime.loader_block(
        runtime.normalise(working, library), columns=["x"], dtypes={"x": "number"}, parse_dates=[], kinds={}
    )
    assert strict <= {finding.rule for finding in validate_security(run_form, library=library)}


def test_the_plotly_file_that_imports_seaborn_for_its_data_alone() -> None:
    """parallel-categories-basic in plotly: eligible as an original, but adapted code that keeps `import seaborn`, even
    without the loader call, is refused, because seaborn is no import of plotly's profile."""
    assert scan(PLOTLY_ORIGINAL, spec_id="scatter-basic", library="plotly", enabled_libraries=["plotly"]).status == (
        "coupled"
    )
    adapted = (
        working_form(PLOTLY_ORIGINAL)
        .replace('raw = sns.load_dataset("titanic")[["class", "fare"]].dropna()\n', "")
        .replace("raw[", "df[")
    )
    assert "sns.load_dataset" not in adapted and "import seaborn as sns" in adapted

    findings = runtime_for("plotly").security(adapted)

    assert [(finding.rule, finding.line, finding.module) for finding in findings] == [("banned-import", 4, "seaborn")]


@pytest.mark.parametrize(
    "imports_and_data",
    [
        pytest.param(("from sklearn.datasets import fetch_openml", 'd = fetch_openml("iris")'), id="fetch_openml"),
        pytest.param(
            ("from sklearn.datasets import fetch_california_housing", "d = fetch_california_housing()"),
            id="fetch_california_housing",
        ),
        pytest.param(("from sklearn.datasets import load_files", 'd = load_files("texts")'), id="load_files"),
        pytest.param(
            ("from sklearn.datasets import load_svmlight_file", 'd = load_svmlight_file("x.svm")'),
            id="load_svmlight_file",
        ),
        pytest.param(
            ("from sklearn.datasets import load_sample_image", 'd = load_sample_image("china.jpg")'),
            id="load_sample_image",
        ),
    ],
)
def test_a_download_or_a_path_reader_stays_refused_in_the_original(imports_and_data: tuple[str, str]) -> None:
    """scikit-learn's `fetch_*` downloads, and `load_files`, `load_svmlight_file(s)` and the sample images, which read
    a path or a picture: none is an example dataset the exemption names, so the original is refused for it as before."""
    imports, data = imports_and_data
    original = matplotlib_file(imports, data + "\nx = y = np.arange(3)")

    found = validate_original(original, library="matplotlib")

    assert found == validate_security(original, library="matplotlib")
    assert {finding.rule for finding in found} == {"banned-import", "banned-call"}
    result = scan(original, spec_id="scatter-basic", library="matplotlib", enabled_libraries=["matplotlib"])
    assert result.status == "blocked" and result.hints == []


def test_a_mixed_import_exempts_only_its_built_in_name() -> None:
    original = matplotlib_file(
        "from sklearn.datasets import load_iris, fetch_openml",
        'iris = load_iris()\nextra = fetch_openml("x")\nx = y = iris.data[:, 0]',
    )

    found = validate_original(original, library="matplotlib")

    assert {(finding.rule, finding.line) for finding in found} == {
        ("built-in-dataset", 5),
        ("built-in-dataset", 8),
        ("banned-import", 5),
        ("banned-call", 5),
    }
    assert any("fetch_openml" in finding.message for finding in found if finding.rule == "banned-import")
    assert scan(original, spec_id="scatter-basic", library="matplotlib", enabled_libraries=["matplotlib"]).status == (
        "blocked"
    )


@pytest.mark.parametrize(
    ("library", "imports", "data"),
    [
        pytest.param("matplotlib", "from sklearn.datasets import load_iris as li", "x = y = li().data[:, 0]", id="as"),
        pytest.param(
            "matplotlib", "from sklearn import datasets", "x = y = datasets.load_iris().data[:, 0]", id="from"
        ),
        pytest.param(
            "matplotlib", "import sklearn.datasets", "x = y = sklearn.datasets.load_iris().data[:, 0]", id="dotted"
        ),
        pytest.param(
            "matplotlib",
            "from sklearn.datasets import load_iris",
            "loader = load_iris\nx = y = loader().data[:, 0]",
            id="loader-as-a-value",
        ),
        pytest.param(
            "matplotlib",
            "from sklearn.datasets import load_iris",
            "x = y = load_iris().data[:, 0]\nload_iris = None",
            id="second-binding",
        ),
        pytest.param(
            "matplotlib",
            "",
            "def data():\n    from sklearn.datasets import load_iris\n\n    return load_iris().data\n\n\nx = y = data()[:, 0]",
            id="nested-import",
        ),
        pytest.param(
            "seaborn",
            "import seaborn as sns",
            'loader = sns.load_dataset\nd = loader("iris")\nx, y = d["a"], d["b"]',
            id="seaborn-loader-as-a-value",
        ),
        pytest.param(
            "seaborn",
            "import seaborn as sns",
            'd = sns.load_dataset("iris")\nx, y = d["a"], d["b"]\nsns = None',
            id="seaborn-rebound",
        ),
        # Shadows that are no `Name`: every use stays a callee, so only the one-binding rule refuses them.
        pytest.param(
            "matplotlib",
            "from sklearn.datasets import load_iris",
            "def first(load_iris):\n    return load_iris()\n\n\nx = y = load_iris().data[:, 0]",
            id="loader-parameter-shadow",
        ),
        pytest.param(
            "matplotlib",
            "from sklearn.datasets import load_iris",
            "x = y = load_iris().data[:, 0]\n\n\ndef load_iris():\n    return None",
            id="loader-def-shadow",
        ),
        pytest.param(
            "matplotlib",
            "from sklearn.datasets import load_iris\nfrom numpy import ones as load_iris",
            "x = y = load_iris(3)",
            id="loader-import-shadow",
        ),
        pytest.param(
            "seaborn",
            "import seaborn as sns",
            'def frame(sns):\n    return sns.load_dataset("iris")\n\n\nd = sns.load_dataset("iris")\nx, y = d["a"], d["b"]',
            id="seaborn-parameter-shadow",
        ),
        # The module must be seaborn, and the loader seaborn's `load_dataset`: any other `load*` stays a refused read.
        pytest.param(
            "matplotlib",
            "import numpy as sns",
            'd = sns.load_dataset("iris")\nx, y = d["a"], d["b"]',
            id="another-module-named-sns",
        ),
        pytest.param(
            "seaborn", "import seaborn as sns", 'd = sns.load("iris")\nx, y = d["a"], d["b"]', id="seaborn-load"
        ),
        pytest.param(
            "seaborn",
            "import seaborn as sns",
            'd = sns.load_example("iris")\nx, y = d["a"], d["b"]',
            id="seaborn-other-load-attribute",
        ),
    ],
)
def test_no_other_shape_is_exempt(library: str, imports: str, data: str) -> None:
    """Only the exact shapes are an example dataset: an alias, `from sklearn import datasets`, a dotted import, a loader
    reached through a value, a second binding of any kind (a store, a parameter, a `def`, another import), a nested
    import, another module under the alias's name or another loader name leaves the eligibility entry as strict as the
    other."""
    original = matplotlib_file(imports, data)

    found = validate_original(original, library=library)

    assert found and found == validate_security(original, library=library)
    assert scan(original, spec_id="scatter-basic", library=library, enabled_libraries=[library]).status == "blocked"


def test_a_seaborn_import_used_for_more_than_its_data_stays_refused_with_plotly() -> None:
    """The import is exempt only when the loader is its one use: a palette taken from seaborn is seaborn in a plotly
    file, which plotly's profile refuses."""
    original = PLOTLY_ORIGINAL.replace(
        "fig = go.Figure(", 'colors = sns.color_palette("deep").as_hex()\nfig = go.Figure('
    )

    found = validate_original(original, library="plotly")

    assert ("banned-import", 4) in {(finding.rule, finding.line) for finding in found}
    assert scan(original, spec_id="scatter-basic", library="plotly", enabled_libraries=["plotly"]).status == "blocked"


def test_the_sklearn_names_are_the_toy_loaders_and_every_generator() -> None:
    """The set holds every `make_*` scikit-learn has and the six toy loaders that take no path; an upgrade that adds a
    generator fails here until someone reads it."""
    datasets = pytest.importorskip("sklearn.datasets")
    names = set(datasets.__all__)
    generators = {name for name in names if name.startswith("make_")}
    loaders = SKLEARN_BUILTIN_DATASETS - generators

    assert generators <= SKLEARN_BUILTIN_DATASETS <= names
    assert loaders == {"load_breast_cancer", "load_diabetes", "load_digits", "load_iris", "load_linnerud", "load_wine"}
    assert not {name for name in SKLEARN_BUILTIN_DATASETS if name.startswith("fetch_")}


def test_only_the_eligibility_scan_calls_the_eligibility_entry() -> None:
    """`validate_original` never checks code that may run: outside the validator itself, only the readiness scan
    (`readiness.scan`) and its record-only script (`readiness_scan.py`) call it, and no code calls the scan's
    `security(..., original=True)` but the validator."""
    callers: set[str] = set()
    flags: set[str] = set()
    for root in ("agents", "api", "core", "automation", "scripts", "tools"):
        for path in (REPO_ROOT / root).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(REPO_ROOT).as_posix()
            if "validate_original" in text:
                callers.add(relative)
            if "original=True" in text:
                flags.add(relative)

    assert callers == {
        "agents/anyplot/code/validate.py",
        "agents/anyplot/code/readiness.py",
        "automation/scripts/readiness_scan.py",
    }
    assert flags == {"agents/anyplot/code/validate.py"}


def test_over_the_catalogue_the_entries_differ_only_on_built_in_dataset_lines() -> None:
    """Every catalogue file that names scikit-learn's datasets or seaborn (no other file can hold a node the exemption
    marks): the eligibility entry finds what the strict one finds, except a `banned-import` or a `banned-call` on a
    line it reports as `built-in-dataset`. So the exemption is the dataset's nodes and nothing else, in the files the
    generator actually writes."""
    exempt_files = 0
    for path in CATALOGUE_FILES:
        library = path.stem
        text = path.read_text(encoding="utf-8")
        if "sklearn.datasets" not in text and "seaborn" not in text:
            continue
        normalised = normalise(strip_noqa_comments(text) or "", library=library)
        strict = set(validate_security(normalised, library=library))
        eligibility = validate_original(normalised, library=library)
        lines = {finding.line for finding in eligibility if finding.rule == BUILTIN_DATASET_RULE}
        others = {finding for finding in eligibility if finding.rule != BUILTIN_DATASET_RULE}
        assert others <= strict, path
        dropped = strict - others
        assert all(finding.rule in ("banned-import", "banned-call") and finding.line in lines for finding in dropped), (
            path,
            dropped,
        )
        exempt_files += bool(lines)
    # 68 of the 69 files of 2026-11-23 that load an example dataset (the 69th marks its loader but stays refused for
    # `contourpy`); a catalogue change moves the number, so only its order of magnitude is pinned.
    assert exempt_files >= 20


def test_the_hint_reaches_the_adapter_from_a_catalogue_file() -> None:
    """A real file of the 2026-11-23 count (contour-decision-boundary in matplotlib, `make_moons`): eligible, coupled,
    with the hint on its import and its generator call."""
    path = REPO_ROOT / "plots/contour-decision-boundary/implementations/python/matplotlib.py"
    if "make_moons" not in path.read_text(encoding="utf-8"):
        pytest.skip("the catalogue file no longer loads make_moons")
    normalised = normalise(strip_noqa_comments(path.read_text(encoding="utf-8")) or "", library="matplotlib")

    result = scan(
        normalised, spec_id="contour-decision-boundary", library="matplotlib", enabled_libraries=["matplotlib"]
    )

    assert result.status == "coupled"
    hint = hint_of(result)
    assert "from sklearn.datasets import make_moons" in hint and "make_moons(" in hint
