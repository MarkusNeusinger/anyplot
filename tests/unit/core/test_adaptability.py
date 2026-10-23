"""Tests for core/adaptability.py: every rule, every ignore class and every false-positive class of the design.

The design is docs/concepts/adaptable-code.md ("The checks"). Each test builds a small
source around a template that passes every rule, changes one thing, and asserts the
rule class that fires (or that nothing does, for a false-positive class).
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import pytest

from core import adaptability
from core.adaptability import (
    CANONICAL_IMPRINT,
    CRITICAL_VALUES,
    RULE_CLASSES,
    SETUP_CALLS,
    Finding,
    Record,
    check_file,
    check_source,
    format_report,
    main,
    replace_block,
    rewrite_columns,
    rewrite_constants,
    run_report,
    sample_findings,
)
from core.defects import DEFECT_RE, defect_ids, defect_target
from core.palette import IMPRINT
from core.spec_roles import Shape, parse_roles


REPO_ROOT = Path(__file__).resolve().parents[3]
PLOTS = REPO_ROOT / "plots"
FIXTURES = Path(__file__).parent / "fixtures" / "adaptability"

BAR_GROUPED = parse_roles(
    [
        "`category` (categorical) - Labels for each group of bars on the x-axis",
        "`group` (categorical) - The different series being compared (creates side-by-side bars)",
        "`value` (numeric) - Heights of the bars representing the measured quantity",
    ]
)
SCATTER = parse_roles(["`x` (numeric) - horizontal", "`y` (numeric) - vertical"])

HEAD = """\
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

QUARTER = "Quarter"  # role: category
PRODUCT_LINE = "Product line"  # role: group
SALES = "Sales (k USD)"  # role: value
"""

BLOCK = """
# Data: quarterly sales
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 3,
        PRODUCT_LINE: ["Electronics"] * 4 + ["Clothing"] * 4 + ["Home & Garden"] * 4,
        SALES: [245, 312, 287, 425, 178, 195, 285, 310, 125, 210, 195, 165],
    }
)

# Plot
"""

PLOT = """\
table = df.pivot_table(index=QUARTER, columns=PRODUCT_LINE, values=SALES, sort=False)
x = np.arange(len(table.index))
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
for i, line in enumerate(table.columns):
    ax.bar(x + i * 0.2, table[line], 0.2, label=line, color=IMPRINT[i])
ax.set_title("bar-grouped · python · matplotlib · anyplot.ai", fontsize=13, color=INK)
"""

TAIL = 'plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)\n'


def source(extra: str = "", *, head: str = HEAD, block: str = BLOCK, plot: str = PLOT) -> str:
    """The passing template with `extra` plot code added before the output."""
    return head + block + plot + textwrap.dedent(extra) + TAIL


def check(code: str, roles=BAR_GROUPED, shape: Shape = "table", library: str | None = "matplotlib") -> Record:
    return check_source(code, roles, shape, library=library)


def found(record: Record, cls: str) -> list[Finding]:
    return [finding for finding in record.findings if finding.cls == cls]


def classes(record: Record) -> set[str]:
    return {finding.cls for finding in record.findings}


class TestTemplate:
    def test_the_template_passes(self) -> None:
        record = check(source())
        assert record.findings == []
        assert record.status == "pass"
        assert record.constants == {"category": "QUARTER", "group": "PRODUCT_LINE", "value": "SALES"}
        assert record.color_role == "group"
        assert record.block == (17, 26)

    @pytest.mark.parametrize(
        ("fixture", "spec_id"), [("bar_grouped_matplotlib", "bar-grouped"), ("line_basic_seaborn", "line-basic")]
    )
    def test_the_converted_examples_pass(self, fixture: str, spec_id: str) -> None:
        record = check_file(FIXTURES / f"{fixture}.py", PLOTS / spec_id / "specification.md", spec_id=spec_id)
        assert record.findings == [], [finding.observed for finding in record.findings]
        assert record.status == "pass"

    def test_imprint_is_the_canonical_palette(self) -> None:
        assert list(CANONICAL_IMPRINT) == IMPRINT

    def test_the_agent_reads_the_same_critical_values(self) -> None:
        from agents.anyplot.code import readiness

        assert readiness.CRITICAL_VALUES is CRITICAL_VALUES


class TestLayout:
    def test_no_data_marker(self) -> None:
        record = check(source(block=BLOCK.replace("# Data: quarterly sales\n", "")))
        assert [f.observed for f in found(record, "layout")] == ["the file has no column-0 # Data marker"]
        assert record.block is None

    def test_no_plot_marker(self) -> None:
        record = check(source(block=BLOCK.replace("# Plot\n", "")))
        assert any("no column-0 # Plot marker" in f.observed for f in found(record, "layout"))
        assert record.block is None

    @pytest.mark.parametrize(
        "marker",
        ["# Data", "# Data:", "# Data: quarterly sales", "# Data - quarterly sales", "# Data — quarterly sales"],
    )
    def test_marker_forms(self, marker: str) -> None:
        assert check(source(block=BLOCK.replace("# Data: quarterly sales", marker))).block == (17, 26)

    @pytest.mark.parametrize("marker", ["# Data points", "# Data-driven callouts", "    # Data", "## Data", "# data"])
    def test_not_a_marker(self, marker: str) -> None:
        assert check(source(block=BLOCK.replace("# Data: quarterly sales", marker))).block is None

    def test_a_marker_inside_a_string_is_no_marker(self) -> None:
        code = source(block='NOTE = """\n# Data\n"""\n' + BLOCK.replace("# Data: quarterly sales\n", ""))
        assert check(code).block is None

    def test_two_data_markers(self) -> None:
        code = source(block=BLOCK.replace("# Plot\n", "# Data: more\nextra = 1\n# Plot\n"))
        assert any("second # Data block" in f.observed for f in found(check(code), "layout"))

    def test_an_empty_block(self) -> None:
        code = source(block="\n# Data\n# Plot\ndf = pd.DataFrame({QUARTER: [], PRODUCT_LINE: [], SALES: []})\n")
        assert any("empty Data block" in f.observed for f in found(check(code), "layout"))

    def test_the_block_must_end_by_binding_df(self) -> None:
        code = source(block=BLOCK.replace("\n# Plot", "top = df[SALES].max()\n\n# Plot"))
        observed = [f.observed for f in found(check(code), "layout")]
        assert observed == ["ends the Data block with `top = df[SALES].max()`, not a statement that binds df"]

    @pytest.mark.parametrize(
        "last",
        [
            "df = df.sort_values(QUARTER)",
            "df[QUARTER] = pd.Categorical(df[QUARTER], ordered=True)",
            "df.loc[:, SALES] = df[SALES].astype(float)",
            "df.reset_index(drop=True, inplace=True)",
            "df: pd.DataFrame = df",
        ],
    )
    def test_statements_that_bind_df(self, last: str) -> None:
        code = source(block=BLOCK.replace("\n# Plot", f"{last}\n\n# Plot"))
        assert found(check(code), "layout") == []

    def test_a_generated_spec_needs_no_df(self) -> None:
        code = source(block="\n# Data: QR content\ncontent = 'https://anyplot.ai'\n\n# Plot\n", plot="")
        record = check(code, roles=parse_roles(["`content` (string) - text"]), shape="generated")
        assert found(record, "layout") == []

    @pytest.mark.parametrize(
        "call", ["ax = plt.gca()", "sns.set_theme(style='white')", "colors = plt.cm.viridis(np.linspace(0, 1, 3))"]
    )
    def test_plotting_styling_and_setup_calls_inside_the_block(self, call: str) -> None:
        head = HEAD.replace("import pandas as pd\n", "import pandas as pd\nimport seaborn as sns\n")
        code = source(head=head, block=BLOCK.replace("df = pd.DataFrame(", f"{call}\ndf = pd.DataFrame(", 1))
        assert any("inside the Data block" in f.observed for f in found(check(code), "layout"))

    def test_a_data_helper_is_allowed_in_the_block(self) -> None:
        head = HEAD.replace("import pandas as pd\n", "import pandas as pd\nimport seaborn as sns\n")
        block = "\n# Data\ndf = sns.load_dataset('tips')\n\n# Plot\n"
        assert found(check(source(head=head, block=block)), "layout") == []

    def test_a_theme_token_inside_the_block(self) -> None:
        code = source(block=BLOCK.replace("df = pd.DataFrame(", "edge = INK\ndf = pd.DataFrame(", 1))
        assert any("theme token `INK`" in f.observed for f in found(check(code), "layout"))

    def test_a_figure_created_above_the_block(self) -> None:
        code = source(
            head=HEAD + "fig, ax = plt.subplots()\n",
            plot=PLOT.replace("fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)\n", ""),
        )
        assert any("above the Data block" in f.observed for f in found(check(code), "layout"))

    def test_a_drawing_call_above_the_block(self) -> None:
        code = source(head=HEAD + "plt.figure()\nplt.axhline(0)\n")
        assert any("calls `plt.figure` above the Data block" in f.observed for f in found(check(code), "layout"))

    def test_the_sys_path_guard_and_seed_are_fine_in_the_head(self) -> None:
        guard = "import sys\n\nsys.path = [p for p in sys.path if p]\nnp.random.seed(1)\n"
        assert found(check(source(head=HEAD + guard)), "layout") == []


SETUP_CASES = [(library, call) for library, calls in SETUP_CALLS.items() for call in calls]
SETUP_IMPORTS = {
    "matplotlib": "import matplotlib\nimport matplotlib.pyplot\n",
    "seaborn": "import seaborn\n",
    "plotly": "import plotly.io\n",
    "altair": "import altair\n",
    "plotnine": "import plotnine\n",
    "bokeh": "import bokeh.io\nimport bokeh.plotting\n",
    "lets_plot": "import lets_plot\n",
}


class TestHeadSetupAllowlist:
    """The false-positive class "head setup calls": every allowlisted call passes in its library's head."""

    @pytest.mark.parametrize(("library", "call"), SETUP_CASES)
    def test_each_entry_is_allowed_in_the_head(self, library: str, call: str) -> None:
        module = call.split(".")[0]
        head = HEAD + SETUP_IMPORTS.get(module, f"import {module}\n") + f"{call}()\n"
        record = check(source(head=head), library=library)
        assert found(record, "layout") == [], (call, [f.observed for f in record.findings])

    @pytest.mark.parametrize(("library", "call"), SETUP_CASES)
    def test_each_entry_is_a_finding_inside_the_block(self, library: str, call: str) -> None:
        module = call.split(".")[0]
        head = HEAD + SETUP_IMPORTS.get(module, f"import {module}\n")
        block = BLOCK.replace("df = pd.DataFrame(", f"{call}()\ndf = pd.DataFrame(", 1)
        assert any(
            "inside the Data block" in f.observed
            for f in found(check(source(head=head, block=block), library=library), "layout")
        )

    def test_lets_plot_setup_html_through_a_star_import(self) -> None:
        head = HEAD + "from lets_plot import *\n\nLetsPlot.setup_html()\n"
        assert found(check(source(head=head), library="letsplot"), "layout") == []

    def test_another_library_s_setup_call_is_a_finding(self) -> None:
        head = HEAD + "import seaborn as sns\n\nsns.set_theme()\n"
        assert found(check(source(head=head), library="matplotlib"), "layout")


class TestColumns:
    def test_missing_constants(self) -> None:
        head = HEAD.replace('SALES = "Sales (k USD)"  # role: value\n', 'SALES = "Sales (k USD)"\n')
        observed = [f.observed for f in found(check(source(head=head)), "columns")]
        assert observed == ["has no column constant for the required role `value`"]

    def test_an_unknown_role(self) -> None:
        head = HEAD + 'REGION = "Region"  # role: region\n'
        assert any("unknown role `region`" in f.observed for f in found(check(source(head=head)), "columns"))

    def test_a_malformed_role_comment(self) -> None:
        head = HEAD.replace("# role: value", "# role: value (sales)")
        observed = [f.observed for f in found(check(source(head=head)), "columns")]
        assert any("writes the role comment" in text for text in observed)

    def test_a_value_that_is_not_a_string(self) -> None:
        head = HEAD.replace('SALES = "Sales (k USD)"', "SALES = 3")
        assert any("not a column-name string" in f.observed for f in found(check(source(head=head)), "columns"))

    def test_a_duplicate_role(self) -> None:
        head = HEAD + 'AMOUNT = "Amount"  # role: value\n'
        assert any("already has" in f.observed for f in found(check(source(head=head)), "columns"))

    def test_a_constant_below_the_marker(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", 'EXTRA = "Note"  # role: extra\ndf = pd.DataFrame(', 1)
        assert any("below the # Data marker" in f.observed for f in found(check(source(block=block)), "columns"))

    def test_extra_columns_are_allowed(self) -> None:
        head = HEAD + 'VOLUME = "Volume"  # role: extra\nNOTE = "Note"  # role: extra\n'
        assert found(check(source(head=head)), "columns") == []

    def test_a_variadic_family_holds_a_list(self) -> None:
        roles = parse_roles(["`x` (numeric) - time", "`y1, y2, ...` (numeric) - series"])
        head = HEAD.split("QUARTER =")[0] + 'TIME = "Time"  # role: x\nSERIES = ["North", "South"]  # role: y\n'
        block = '\n# Data\ndf = pd.DataFrame({TIME: [1, 2], "North": [3, 4], "South": [5, 6]})\n\n# Plot\n'
        assert found(check(source(head=head, block=block, plot=""), roles=roles), "columns") == []
        single = head.replace('["North", "South"]', '"North"')
        assert found(check(source(head=single, block=block, plot=""), roles=roles), "columns")

    def test_annotated_constants_and_palette(self) -> None:
        """`QUARTER: str = "Quarter"  # role: category` is a constant like the plain form (Gemini review)."""
        head = HEAD.replace('QUARTER = "Quarter"', 'QUARTER: str = "Quarter"').replace(
            "IMPRINT = [", "IMPRINT: list[str] = ["
        )
        record = check(source(head=head))
        assert record.findings == []
        assert record.constants["category"] == "QUARTER"
        assert 'QUARTER: str = "Region"  # role: category' in rewrite_constants(
            source(head=head), {"category": "Region"}
        )

    def test_the_comment_may_sit_on_any_line_of_a_list(self) -> None:
        roles = parse_roles(["`x` (numeric) - time", "`y1, y2, ...` (numeric) - series"])
        head = (
            HEAD.split("QUARTER =")[0]
            + 'TIME = "Time"  # role: x\nSERIES = [  # role: y\n    "North",\n    "South",\n]\n'
        )
        block = '\n# Data\ndf = pd.DataFrame({TIME: [1, 2], "North": [3, 4], "South": [5, 6]})\n\n# Plot\n'
        record = check(source(head=head, block=block, plot=""), roles=roles)
        assert record.constants == {"x": "TIME", "y": "SERIES"}

    def test_optional_and_computed_roles_are_not_required(self) -> None:
        roles = parse_roles(
            [
                "`category` (categorical) - labels",
                "`value` (numeric) - values",
                "`label` (string, optional) - text",
                "`rolling` (numeric) - Computed rolling average",
            ]
        )
        head = HEAD.replace('PRODUCT_LINE = "Product line"  # role: group\n', "")
        block = '\n# Data\ndf = pd.DataFrame({QUARTER: ["Q1"], SALES: [1]})\n\n# Plot\n'
        assert found(check(source(head=head, block=block, plot=""), roles=roles), "columns") == []

    def test_a_matrix_needs_no_constants(self) -> None:
        roles = parse_roles(["`variables` (string) - names", "`correlation_matrix` (numeric) - matrix"])
        head = HEAD.split("QUARTER =")[0]
        block = (
            '\n# Data\ndf = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]], index=["a", "b"], columns=["a", "b"])\n\n# Plot\n'
        )
        assert found(check(source(head=head, block=block, plot=""), roles=roles, shape="matrix"), "columns") == []

    def test_a_network_needs_constants_for_attributes_only(self) -> None:
        roles = parse_roles(
            ["`nodes` (list of dicts) - nodes", "`edges` (list of tuples) - edges", "`weight` (numeric)"]
        )
        head = HEAD.split("QUARTER =")[0]
        block = '\n# Data\ndf = pd.DataFrame({"source": ["a"], "target": ["b"], "w": [1.0]})\n\n# Plot\n'
        observed = [
            f.observed
            for f in found(check(source(head=head, block=block, plot=""), roles=roles, shape="network"), "columns")
        ]
        assert observed == ["has no column constant for the required role `weight`"]


class TestInterface:
    def test_a_block_name_read_below(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", 'groups = ["Electronics", "Clothing"]\ndf = pd.DataFrame(', 1)
        observed = [f.observed for f in found(check(source(block=block, extra="print(groups)\n")), "interface")]
        assert observed == ["reads `groups`, which the Data block binds"]

    def test_rebinding_before_reading_is_fine(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", "x = 1\ndf = pd.DataFrame(", 1)
        assert found(check(source(block=block)), "interface") == []  # the template rebinds x below

    def test_loop_targets_parameters_and_comprehensions_shadow(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", "g = 1\nk = 2\nv = 3\ndf = pd.DataFrame(", 1)
        extra = """\
        for g in table.columns:
            print(g)
        labels = [k for k in table.index]
        def fmt(v):
            return f"{v:.0f}"
        """
        assert found(check(source(block=block, extra=extra)), "interface") == []

    def test_a_function_reading_a_block_name(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", "scale = 2\ndf = pd.DataFrame(", 1)
        extra = "def grow(value):\n    return value * scale\n"
        assert [f.observed for f in found(check(source(block=block, extra=extra)), "interface")] == [
            "reads `scale`, which the Data block binds"
        ]

    def test_an_import_inside_the_block_read_below(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", "from scipy import stats\ndf = pd.DataFrame(", 1)
        assert found(check(source(block=block, extra="print(stats.norm)\n")), "interface")

    def test_a_network_may_bind_nodes(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", 'nodes = pd.DataFrame({"id": ["a"]})\ndf = pd.DataFrame(', 1)
        assert found(check(source(block=block, extra="print(nodes)\n"), shape="network"), "interface") == []
        assert found(check(source(block=block, extra="print(nodes)\n")), "interface")

    def test_a_generated_spec_reads_its_parameters(self) -> None:
        block = "\n# Data\nsize = 21\n\n# Plot\n"
        code = source(block=block, plot="print(size)\n")
        assert found(check(code, roles=parse_roles(["`content` (string)"]), shape="generated"), "interface") == []

    SCALE_BLOCK = BLOCK.replace("df = pd.DataFrame(", "scale = 2\ndf = pd.DataFrame(", 1)

    @pytest.mark.parametrize(
        "extra",
        [
            "if len(df) > 3:\n    scale = 1\nprint(scale)\n",  # only one branch rebinds
            "for _ in range(len(df)):\n    scale = 1\nprint(scale)\n",  # the loop may run zero times
            "while len(df) > 99:\n    scale = 1\nprint(scale)\n",
            "try:\n    scale = 1 / len(df)\nexcept ZeroDivisionError:\n    print(scale)\n",  # the handler
            "scale = 1\ndel scale\nprint(scale)\n",
            "match len(df):\n    case 0:\n        scale = 1\nprint(scale)\n",
        ],
    )
    def test_a_rebinding_on_some_paths_only(self, extra: str) -> None:
        """Copilot: a conditional reassignment is no rebinding on the path where it does not run."""
        assert [f.observed for f in found(check(source(block=self.SCALE_BLOCK, extra=extra)), "interface")] == [
            "reads `scale`, which the Data block binds"
        ]

    @pytest.mark.parametrize(
        "extra",
        [
            "if len(df) > 3:\n    scale = 1\nelse:\n    scale = 2\nprint(scale)\n",  # every branch rebinds
            "for _ in range(3):\n    scale = 1\n    print(scale)\n",  # read inside the body, after the rebinding
            "try:\n    scale = 1\nexcept ValueError:\n    scale = 2\nprint(scale)\n",
            "with open(__file__) as scale:\n    print(scale)\n",
        ],
    )
    def test_a_rebinding_on_every_path(self, extra: str) -> None:
        assert found(check(source(block=self.SCALE_BLOCK, extra=extra)), "interface") == []


class TestColumnAndSampleLiterals:
    def test_a_column_name_below_the_block(self) -> None:
        record = check(source(extra='ax.set_xlabel("Quarter")\n'))
        assert [f.observed for f in found(record, "column-literal")] == ["types the column name 'Quarter'"]

    def test_the_constant_is_fine(self) -> None:
        assert found(check(source(extra="ax.set_xlabel(QUARTER)\n")), "column-literal") == []

    def test_auto_labels_are_never_demanded(self) -> None:
        """The false-positive class "auto-labels": no rule asks for set_xlabel when the library titles the axis."""
        assert check(source()).findings == []

    @pytest.mark.parametrize("field", ['"Sales (k USD):Q"', '"Sales (k USD):N"', '"Sales (k USD):O"'])
    def test_an_altair_field_string_counts_as_the_column(self, field: str) -> None:
        assert found(check(source(extra=f"encoding = {field}\n")), "column-literal")

    def test_an_escaped_altair_field_counts_as_the_constant_it_escapes(self) -> None:
        """The false-positive class "Altair field names": `"U\\\\.S\\\\. sales"` is the column `U.S. sales`."""
        head = HEAD.replace('"Sales (k USD)"', '"U.S. sales"')
        assert found(check(source(head=head, extra='y = "U\\\\.S\\\\. sales:Q"\n')), "column-literal")
        escaped = 'y = SALES.replace(".", "\\\\.")\nchart_y = f"{y}:Q"\n'
        assert found(check(source(head=head, extra=escaped)), "column-literal") == []

    def test_a_sample_value_below_the_block(self) -> None:
        record = check(source(extra='q3 = list(table.index).index("Q3")\n'))
        assert [f.observed for f in found(record, "sample-literal")] == [
            "uses the literal 'Q3', a value the Data block defines"
        ]

    def test_category_words_in_prose_are_fine(self) -> None:
        """A label containing a sample value is prose; only an equal string is tied to the sample."""
        extra = 'ax.text(0.5, 0.9, "Electronics led every quarter", transform=ax.transAxes)\n'
        assert found(check(source(extra=extra)), "sample-literal") == []

    @pytest.mark.parametrize("word", ["Total", "Other"])
    def test_prose_words_equal_to_a_sample_value_are_fine(self, word: str) -> None:
        block = BLOCK.replace('["Electronics"] * 4', f'["{word}"] * 4')
        assert found(check(source(block=block, extra=f'ax.set_ylabel("{word}")\n')), "sample-literal") == []

    def test_style_words_and_property_keys_are_fine(self) -> None:
        block = BLOCK.replace(
            "df = pd.DataFrame(", 'align = ["center", "left", "right"]\nstyle = {"size": 3}\ndf = pd.DataFrame(', 1
        )
        extra = 'marker = {"size": 7}\nposition = "center"\n'
        assert found(check(source(block=block, extra=extra)), "sample-literal") == []

    def test_one_character_values_are_fine(self) -> None:
        block = BLOCK.replace('["Q1", "Q2", "Q3", "Q4"]', '["A", "B", "C", "D"]')
        assert found(check(source(block=block, extra='path = "C"\n')), "sample-literal") == []

    def test_style_keywords_are_ignored(self) -> None:
        block = BLOCK.replace('["Q1", "Q2", "Q3", "Q4"]', '["upper left", "center", "o", "-"]')
        extra = 'ax.legend(loc="upper left")\nax.plot([0], [0], marker="o", linestyle="-")\n'
        assert found(check(source(block=block, extra=extra)), "sample-literal") == []

    def test_the_title_and_the_output_are_ignored(self) -> None:
        block = BLOCK.replace('["Q1", "Q2", "Q3", "Q4"]', '["plot-light.png", "Q2", "Q3", "Q4"]')
        extra = 'ax.set_title("Q3 · bar-grouped · anyplot.ai")\nplt.savefig("plot-light.png")\n'
        assert found(check(source(block=block, extra=extra)), "sample-literal") == []

    def test_literals_inside_the_block_are_never_flagged(self) -> None:
        assert check(source()).findings == []  # the template's block is full of literals

    def test_record_field_names_are_fine(self) -> None:
        block = BLOCK.replace("df = pd.DataFrame(", 'meta = {"id": 1, "color": "x"}\ndf = pd.DataFrame(', 1)
        extra = 'rows = [{"id": 2}]\nkey = rows[0]["id"]\n'
        assert found(check(source(block=block, extra=extra)), "sample-literal") == []


class TestStatisticText:
    def test_a_typed_statistic(self) -> None:
        assert found(check(source(extra='ax.text(1, 2, "r = 0.87")\n')), "statistic-text")

    def test_an_f_string_is_computed(self) -> None:
        extra = 'r = df[SALES].corr(df[SALES])\nax.set_xlabel(f"r = {r:.2f}")\n'
        assert found(check(source(extra=extra)), "statistic-text") == []

    def test_it_is_advisory(self) -> None:
        record = check(source(extra='label = "n = 180"\n'))
        assert found(record, "statistic-text") and record.status == "pass"


class TestDataCoordinates:
    @pytest.mark.parametrize(
        "line",
        [
            "ax.set_ylim(0, 500)",
            "ax.set_xticks([1, 2, 3, 4])",
            "ax.axhline(300)",
            "ax.axvspan(1.5, 2.5)",
            "ax.annotate('peak', xy=(3, 425))",
            "ax.text(2, 410, 'note')",
            "ax.set_xlim(0, 410)",
            "ax.set_ylim(5, 80)",
            "ax.set(ylim=(100, 450))",
            "fig.update_layout(yaxis=dict(range=[100, 450]))",
            "fig.update_layout(yaxis_range=[100, 450])",
            "fig.add_hline(y=300)",
            "scale = alt.Scale(domain=[100, 450])",
            "scale = scale_y_continuous(limits=(100, 450))",
            "rng = Range1d(100, 450)",
            "span = Span(location=300)",
            "ax.axvline(pd.Timestamp('2024-03-01'))",
            "levels = ax.contour(table, levels=[100, 200, 300])",
            "ax.hist(df[SALES], bins=[100, 200, 300, 400])",
            "norm = Normalize(vmin=100, vmax=450)",
        ],
    )
    def test_literal_coordinates(self, line: str) -> None:
        assert found(check(source(extra=line + "\n")), "data-coordinate"), line

    def test_an_attribute_assignment(self) -> None:
        assert found(check(source(extra="p = object()\np.y_range.end = 450\n")), "data-coordinate")

    @pytest.mark.parametrize(
        "line",
        [
            "ax.set_ylim(0, df[SALES].max() * 1.1)",
            "ax.set_xlim(-0.5, len(table.index) - 0.5)",
            "ax.set_ylim(0, 1)",
            "ax.set_ylim(0, 100)",
            "ax.set_ylim(-0.05, 1.05)",
            "ax.set_yticks([0, 25, 50, 75, 100])",
            "ax.set_xticks(range(0, 361, 90))",
            "ax.set_ylim(-1, 1)",
            "ax.axhline(0)",
            "ax.axhline(1.96)",
            "ax.set_xticks(x, table.index, fontsize=8)",
            "ax.annotate('peak', xy=(x[0], table.iloc[0, 0]), xytext=(0, 14), textcoords='offset points')",
            "ax.annotate('peak', xy=(0.5, 0.9), xycoords='axes fraction')",
            "ax.set_ylim(0, 105)",
            "ax.set_xlim(-36, 396)",
            "ax.text(0.02, 0.95, 'note', transform=ax.transAxes)",
            "fig.text(0.5, 0.02, 'source')",
            "fig.add_annotation(x=0.5, y=1.1, xref='paper', yref='paper', text='t')",
            "scale = scale_size(range=(2, 12))",
            "scale = alt.Scale(range=[50, 400])",
            "jitter = np.random.default_rng(7).uniform(-0.2, 0.2, len(df))",
            "low = df[SALES].mean() - 1.96 * df[SALES].std()",
        ],
    )
    def test_ignored_positions(self, line: str) -> None:
        """Style keywords, offsets in points, axes fractions, fixed domains, computed values, jitter sized from df."""
        assert found(check(source(extra=line + "\n")), "data-coordinate") == [], line

    def test_hidden_axes_place_a_drawing(self) -> None:
        assert found(check(source(extra="ax.axis('off')\nax.set_xlim(-8.5, 8.5)\n")), "data-coordinate") == []

    def test_it_is_advisory(self) -> None:
        record = check(source(extra="ax.set_ylim(100, 450)\n"))
        assert found(record, "data-coordinate") and record.status == "pass"

    def test_without_a_block_the_whole_file_is_checked(self) -> None:
        record = check(source(block=BLOCK.replace("# Plot\n", ""), extra="ax.set_ylim(100, 450)\n"))
        assert found(record, "data-coordinate")


class TestDfComparison:
    def test_a_literal_selection(self) -> None:
        record = check(source(extra='q3 = df[df[QUARTER] == "Q3"]\n'))
        assert [f.observed for f in found(record, "df-comparison")] == ["compares df with the literal 'Q3'"]
        assert record.status == "fail"

    def test_through_one_alias(self) -> None:
        record = check(source(extra='peak = "Q4"\nq4 = df[df[QUARTER] == peak]\n'))
        assert [f.observed for f in found(record, "df-comparison")] == ["compares df with the literal peak = 'Q4'"]

    def test_through_a_derived_name(self) -> None:
        assert found(
            check(source(extra="hit = [line for line in table.columns if line == 'Clothing']\n")), "df-comparison"
        )

    def test_isin(self) -> None:
        assert found(check(source(extra='part = df[df[QUARTER].isin(["Q1", "Q2"])]\n')), "df-comparison")

    @pytest.mark.parametrize(
        "line",
        [
            "big = df[df[SALES] >= 300]",
            "many = len(df) > 50",
            "pos = df[df[SALES] > 0]",
            "first = [i for i, _ in enumerate(table.columns) if i == 0]",
            'NAMED = "Q3"\n',
        ],
    )
    def test_thresholds_neutral_values_and_constants_are_fine(self, line: str) -> None:
        assert found(check(source(extra=line + "\n")), "df-comparison") == [], line

    def test_a_constants_threshold_is_fine(self) -> None:
        head = HEAD.replace("QUARTER =", "# Constants\nHIGHLIGHT_ABOVE = 300\n\nQUARTER =")
        assert found(check(source(head=head, extra="big = df[df[SALES] == HIGHLIGHT_ABOVE]\n")), "df-comparison") == []


class TestCountLiterals:
    @pytest.mark.parametrize(
        "line",
        ["ticks = range(12)", "ticks = np.arange(1, 13)", "top = df.head(12)[:12]", "grid = np.linspace(0, 1, 12)"],
    )
    def test_a_count_the_block_defines(self, line: str) -> None:
        assert found(check(source(extra=line + "\n")), "count-literal"), line

    @pytest.mark.parametrize(
        "line", ["ticks = range(2)", "grid = np.linspace(0, 1, 200)", "ticks = range(len(df))", "ticks = range(7)"]
    )
    def test_small_resolution_computed_and_coincidental_counts_are_fine(self, line: str) -> None:
        assert found(check(source(extra=line + "\n")), "count-literal") == [], line

    def test_it_is_advisory(self) -> None:
        record = check(source(extra="ticks = range(12)\n"))
        assert found(record, "count-literal") and record.status == "pass"


class TestPalette:
    def test_a_short_palette_with_a_colour_role(self) -> None:
        head = HEAD.replace(', "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"', "")
        observed = [f.observed for f in found(check(source(head=head)), "palette")]
        assert observed == ["`IMPRINT` lists 3 of 8 positions"]

    def test_out_of_order(self) -> None:
        head = HEAD.replace('"#009E73", "#C475FD"', '"#009E73", "#4467A3"', 1).replace(
            '"#4467A3", "#BD8233"', '"#C475FD", "#BD8233"'
        )
        assert [f.observed for f in found(check(source(head=head)), "palette")] == [
            "`IMPRINT` lists the Imprint colors out of canonical order"
        ]

    def test_no_palette_for_a_required_colour_role(self) -> None:
        head = HEAD.replace("IMPRINT = [", "BRANDS = [").replace('"#009E73", ', '"#123456", ', 1)
        code = source(head=head, plot=PLOT.replace("IMPRINT[i]", "BRANDS[i]"))
        assert [f.observed for f in found(check(code), "palette")] == [
            "has no IMPRINT list while the spec's `group` role colors the marks"
        ]

    def test_an_optional_colour_role_may_go_unused(self) -> None:
        roles = parse_roles(
            ["`x` (numeric) - a", "`y` (numeric) - b", "`category` (categorical, optional) - for color coding"]
        )
        head = HEAD.split("IMPRINT =")[0] + 'BRAND = "#009E73"\nX = "x"  # role: x\nY = "y"  # role: y\n'
        block = "\n# Data\ndf = pd.DataFrame({X: [1, 2], Y: [3, 4]})\n\n# Plot\n"
        assert found(check(source(head=head, block=block, plot=""), roles=roles), "palette") == []

    def test_a_single_series_plot_may_use_brand_alone(self) -> None:
        head = HEAD.split("IMPRINT =")[0] + 'BRAND = "#009E73"\nX = "x"  # role: x\nY = "y"  # role: y\n'
        block = "\n# Data\ndf = pd.DataFrame({X: [1, 2], Y: [3, 4]})\n\n# Plot\n"
        record = check(source(head=head, block=block, plot="plt.scatter(df[X], df[Y], color=BRAND)\n"), roles=SCATTER)
        assert record.color_role is None
        assert found(record, "palette") == []

    def test_a_short_palette_without_a_colour_role_is_fine(self) -> None:
        head = HEAD.split("IMPRINT =")[0] + 'IMPRINT = ["#009E73", "#C475FD"]\nX = "x"  # role: x\nY = "y"  # role: y\n'
        block = "\n# Data\ndf = pd.DataFrame({X: [1, 2], Y: [3, 4]})\n\n# Plot\n"
        assert found(check(source(head=head, block=block, plot=""), roles=SCATTER), "palette") == []

    def test_zip_strict_over_the_palette(self) -> None:
        extra = "pairs = dict(zip(table.columns, IMPRINT, strict=True))\n"
        assert [f.observed for f in found(check(source(extra=extra)), "palette")] == [
            "zips the palette with strict=True, which raises for one more group"
        ]

    def test_zip_strict_over_a_slice_sized_from_df_is_fine(self) -> None:
        extra = "pairs = dict(zip(table.columns, IMPRINT[: len(table.columns)], strict=True))\n"
        assert found(check(source(extra=extra)), "palette") == []

    def test_a_literal_slice(self) -> None:
        assert any("fixed size" in f.observed for f in found(check(source(extra="colors = IMPRINT[:3]\n")), "palette"))

    def test_a_slice_counted_from_df_is_fine(self) -> None:
        assert found(check(source(extra="colors = IMPRINT[: len(table.columns)]\n")), "palette") == []


class TestConstantsZone:
    def zone(self, constants: str) -> str:
        return HEAD.replace("QUARTER =", f"# Constants\n{constants}\n\nQUARTER =")

    def test_hoisted_sample_categories(self) -> None:
        record = check(source(head=self.zone('ORDER = ["Q1", "Q2", "Q3", "Q4"]')))
        assert [f.observed for f in found(record, "constants")] == [
            "lists sample values ('Q1', 'Q2', 'Q3', …) in # Constants"
        ]
        assert record.status == "pass"  # advisory

    def test_hoisted_data_numbers(self) -> None:
        assert found(check(source(head=self.zone("HEIGHTS = [245, 312, 287]"))), "constants")

    def test_thresholds_and_semantic_maps_are_fine(self) -> None:
        zone = 'RSI_LOW, RSI_HIGH = 30, 70\nTARGET = 300\nSEMANTIC = {"loss": "#AE3030"}'
        assert found(check(source(head=self.zone(zone))), "constants") == []

    def test_an_ordered_scale_the_block_spells_out_is_reported(self) -> None:
        """The open question of the design: an ordered scale and hoisted categories look alike, so it is advisory."""
        block = BLOCK.replace('["Q1", "Q2", "Q3", "Q4"] * 3', "WEEKDAYS[:4] * 3").replace("QUARTER: ", "QUARTER: ")
        head = self.zone('WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]')
        record = check(
            source(head=head, block=block.replace("df = pd.DataFrame(", 'days = ["Mon", "Tue"]\ndf = pd.DataFrame(', 1))
        )
        assert found(record, "constants") and all(f.advisory for f in found(record, "constants"))


class TestRecord:
    def failing(self) -> Record:
        head = HEAD.replace(', "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"', "")
        return check(
            source(head=head, extra='ax.set_xlabel("Quarter")\nax.set_xlabel("Product line")\nax.set_ylim(100, 450)\n')
        )

    def test_status(self) -> None:
        assert self.failing().status == "fail"
        assert check(source()).status == "pass"
        assert check(source(), shape="excluded").status == "excluded"
        assert check("not python (", shape="excluded").findings == []

    def test_a_syntax_error_is_a_layout_finding(self) -> None:
        record = check("def broken(:\n")
        assert record.status == "fail" and record.classes() == ["layout"]

    def test_one_defect_line_per_class(self) -> None:
        record = self.failing()
        lines = record.defect_lines()
        assert len(lines) == len(record.classes()) == 3
        for line in lines:
            assert DEFECT_RE.match(line), line
            assert defect_ids(line) == ["CQ-01"]
            assert line.startswith("CQ-01 (code): ")
            assert defect_target(line)
            assert "Likely cause:" in line

    def test_a_defect_line_names_the_first_line_and_the_others(self) -> None:
        line = next(line for line in self.failing().defect_lines() if "column name" in line)
        assert re.search(r"line \d+ types the column name 'Quarter'; 1 more at lines \d+ →", line), line

    def test_advisory_lines_are_marked(self) -> None:
        line = next(line for line in self.failing().defect_lines() if "data coordinates" in line)
        assert line.startswith("CQ-01 (code): (advisory) line ")

    def test_to_dict(self) -> None:
        payload = self.failing().to_dict()
        assert set(payload) == {"version", "status", "shape", "color_role", "block", "constants", "findings", "lines"}
        assert payload["block"] == {"start": 17, "end": 26}
        assert json.loads(json.dumps(payload)) == payload
        finding = payload["findings"][0]
        assert set(finding) == {"rule", "class", "line", "observed", "cause", "advisory"}

    def test_every_rule_class_has_a_rule_number_and_target(self) -> None:
        assert sorted({rule.rule for rule in RULE_CLASSES.values()}) == [1, 2, 3, 4, 5, 6]
        advisory = {cls for cls, rule in RULE_CLASSES.items() if rule.advisory}
        assert advisory == {"data-coordinate", "statistic-text", "count-literal", "sample-literal", "constants"}


class TestMutations:
    def test_replace_block_keeps_the_markers(self) -> None:
        code = replace_block(source(), "df = load_user_data()")
        assert "# Data: quarterly sales\ndf = load_user_data()\n\n# Plot\n" in code
        assert "Electronics" not in code
        assert check(code).block is not None

    def test_replace_block_without_a_block(self) -> None:
        with pytest.raises(ValueError, match="no # Data"):
            replace_block(source(block=BLOCK.replace("# Plot\n", "")), "df = 1")

    def test_rewrite_constants(self) -> None:
        code = rewrite_constants(source(), {"category": "Région", "value": 'Revenue "k" (€)', "unknown": "x"})
        assert 'QUARTER = "Région"  # role: category' in code
        assert 'SALES = "Revenue \\"k\\" (€)"  # role: value' in code
        assert 'PRODUCT_LINE = "Product line"  # role: group' in code
        assert check(code).constants == check(source()).constants

    def test_rewrite_a_family(self) -> None:
        code = 'A = "x"  # role: x\nB = ["one", "two"]  # role: y\n'
        assert rewrite_constants(code, {"y": ["North", "South", "East"]}) == (
            'A = "x"  # role: x\nB = ["North", "South", "East"]  # role: y\n'
        )

    def test_a_role_comment_inside_a_multiline_value_survives_twice(self) -> None:
        """Copilot: replacing the whole span used to delete `# role: y` on the opening line."""
        roles = parse_roles(["`x` (numeric) - time", "`y1, y2, ...` (numeric) - series"])
        head = (
            HEAD.split("QUARTER =")[0]
            + 'TIME = "Time"  # role: x\nSERIES = [  # role: y\n    "North",\n    "South",\n]\n'
        )
        block = '\n# Data\ndf = pd.DataFrame({TIME: [1, 2], "North": [3, 4], "South": [5, 6]})\n\n# Plot\n'
        code = source(head=head, block=block, plot="")
        once = rewrite_constants(code, {"y": ["East", "West", "Up"]})
        assert 'SERIES = ["East", "West", "Up"]  # role: y\n' in once
        assert check(once, roles=roles).constants == {"x": "TIME", "y": "SERIES"}
        twice = rewrite_constants(once, {"y": ["A", "B"]})
        assert 'SERIES = ["A", "B"]  # role: y\n' in twice
        assert found(check(twice, roles=roles), "columns") == []

    def test_a_trailing_comment_after_the_moved_role_comment_is_kept(self) -> None:
        code = 'S = [  # role: y\n    "a",\n]  # sample series\n'
        out = rewrite_constants(code, {"y": ["b"]})
        assert out == 'S = ["b"]  # role: y  # sample series\n'
        assert rewrite_constants(out, {"y": ["c"]}) == 'S = ["c"]  # role: y  # sample series\n'

    def test_rewrite_columns_renames_extras_by_their_old_name(self) -> None:
        code = 'A = "Old A"  # role: x\nNOTE = "Note"  # role: extra\nRANK = "Rank"  # role: extra\nB = ["Note", "B"]  # role: y\n'
        out = rewrite_columns(code, {"Old A": "New A", "Note": "Memo", "Rank": "Order"})
        assert out == (
            'A = "New A"  # role: x\nNOTE = "Memo"  # role: extra\nRANK = "Order"  # role: extra\n'
            'B = ["Memo", "B"]  # role: y\n'
        )
        assert rewrite_columns(code, {}) == code


class TestCatalogue:
    def test_the_two_design_examples(self) -> None:
        """docs/concepts/adaptable-code.md, "Two typical files"."""
        bar = check_file(PLOTS / "bar-grouped/implementations/python/matplotlib.py")
        assert {"layout", "columns", "interface", "sample-literal", "palette"} <= set(bar.classes())
        assert any("'Q3'" in f.observed for f in found(bar, "sample-literal"))
        line = check_file(PLOTS / "line-basic/implementations/python/seaborn.py")
        assert {"columns", "interface", "column-literal", "df-comparison"} <= set(line.classes())
        assert any("peak_month = 7" in f.observed for f in found(line, "df-comparison"))

    def test_map_specs_are_excluded(self) -> None:
        assert check_file(PLOTS / "choropleth-basic/implementations/python/plotly.py").status == "excluded"

    def test_every_python_implementation_is_checked_without_an_error(self) -> None:
        results = run_report(PLOTS)
        assert len(results) > 2000
        statuses = {record.status for _, record in results}
        assert statuses <= {"pass", "fail", "excluded"}
        for path, record in results:
            for line in record.defect_lines():
                assert DEFECT_RE.match(line), (path, line)
        report = format_report(results)
        assert "| **all** |" in report and "| 5 | palette |" in report
        sample = sample_findings(results, 3, seed=1, root=REPO_ROOT)
        assert set(sample) == set(RULE_CLASSES)


class TestCli:
    def test_check_exit_codes(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        out = tmp_path / "record.json"
        spec = PLOTS / "bar-grouped" / "specification.md"
        assert main(["check", str(FIXTURES / "bar_grouped_matplotlib.py"), "--spec", str(spec), "--out", str(out)]) == 0
        assert json.loads(out.read_text())["status"] == "pass"
        assert main(["check", str(PLOTS / "bar-grouped/implementations/python/matplotlib.py")]) == 1
        printed = capsys.readouterr().out
        assert "CQ-01 (code):" in printed
        assert main(["check", str(tmp_path / "missing.py"), "--spec", str(spec)]) == 2

    def test_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["report", str(PLOTS), "--library", "pygal", "--sample", "2"]) == 0
        printed = capsys.readouterr().out
        assert "| pygal | 325 |" in printed
        assert "## layout (2 sampled)" in printed

    def test_report_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["report", str(PLOTS), "--library", "pygal", "--json"]) == 0
        rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
        assert len(rows) == 325 and all("status" in row for row in rows)


def test_the_module_imports_only_the_standard_library_and_spec_roles() -> None:
    import ast
    import sys

    tree = ast.parse(Path(adaptability.__file__).read_text(encoding="utf-8"))
    modules = {
        (node.module if isinstance(node, ast.ImportFrom) else alias.name).split(".")[0]
        for node in tree.body
        if isinstance(node, ast.Import | ast.ImportFrom)
        for alias in node.names
    }
    assert modules - set(sys.stdlib_module_names) == {"core"}
