"""Tests for core/perturbation.py: the perturbed tables and the source the smoke run executes."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.adaptability import check_source
from core.perturbation import MAX_GROUPS, ROW_FACTOR, SCALE, SHIFT, perturbations, single_group_allowed, smoke_source
from core.spec_roles import parse_roles


FIXTURES = Path(__file__).parent / "fixtures" / "adaptability"
ROLES = parse_roles(
    [
        "`category` (categorical) - Labels for each group of bars on the x-axis",
        "`group` (categorical) - The different series being compared (creates side-by-side bars)",
        "`value` (numeric) - Heights of the bars",
    ]
)
COLUMNS = {"category": "Quarter", "group": "Product line", "value": "Sales (thousand USD)"}


@pytest.fixture
def sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Quarter": ["Q1", "Q2", "Q3", "Q4"] * 3,
            "Product line": ["Electronics"] * 4 + ["Clothing"] * 4 + ["Home & Garden"] * 4,
            "Sales (thousand USD)": [245, 312, 287, 425, 178, 195, 285, 310, 125, 210, 195, 165],
        }
    )


class TestTablePerturbations:
    def test_the_set_and_its_order(self, sample: pd.DataFrame) -> None:
        names = [item.name for item in perturbations(sample, COLUMNS, ROLES, "table", "group")]
        assert names == [
            "renamed",
            "more_categories",
            "fewer_categories",
            "single_group",
            "fewer_rows",
            "more_rows",
            "scaled",
        ]

    def test_the_sample_is_never_changed(self, sample: pd.DataFrame) -> None:
        before = sample.copy()
        perturbations(sample, COLUMNS, ROLES, "table", "group")
        pd.testing.assert_frame_equal(sample, before)

    def test_renamed(self, sample: pd.DataFrame) -> None:
        item = perturbations(sample, COLUMNS, ROLES, "table", "group")[0]
        names = list(item.df.columns)
        assert not set(names) & set(sample.columns)
        assert any(" " in name and "." in name and "(" in name for name in names)  # spaces, a unit and a dot
        assert set(item.columns) == set(COLUMNS)
        assert all(item.columns[role] in names for role in COLUMNS)
        assert item.retired == frozenset({"Q1", "Q2", "Q3", "Q4", "Electronics", "Clothing", "Home & Garden"})
        assert not set(item.df[item.columns["category"]]) & item.retired
        assert len(item.df) == len(sample)

    def test_more_and_fewer_categories_stay_within_eight(self, sample: pd.DataFrame) -> None:
        items = {item.name: item for item in perturbations(sample, COLUMNS, ROLES, "table", "group")}
        more, fewer = items["more_categories"].df, items["fewer_categories"].df
        assert more["Quarter"].nunique() == 5 and more["Product line"].nunique() == 4
        assert fewer["Quarter"].nunique() == 3 and fewer["Product line"].nunique() == 2
        eight = pd.DataFrame(
            {
                "Quarter": [f"Q{i}" for i in range(MAX_GROUPS)],
                "Product line": ["A"] * 8,
                "Sales (thousand USD)": range(8),
            }
        )
        grown = {i.name: i for i in perturbations(eight, COLUMNS, ROLES, "table", "group")}["more_categories"].df
        assert grown["Quarter"].nunique() == MAX_GROUPS

    def test_an_ordered_categorical_gains_a_label(self, sample: pd.DataFrame) -> None:
        sample["Quarter"] = pd.Categorical(sample["Quarter"], ordered=True)
        more = {i.name: i for i in perturbations(sample, COLUMNS, ROLES, "table", "group")}["more_categories"].df
        assert more["Quarter"].nunique() == 5

    def test_single_group(self, sample: pd.DataFrame) -> None:
        single = {i.name: i for i in perturbations(sample, COLUMNS, ROLES, "table", "group")}["single_group"].df
        assert set(single["Product line"]) == {"Electronics"} and len(single) == 4

    def test_fewer_rows_keeps_every_group(self, sample: pd.DataFrame) -> None:
        fewer = {i.name: i for i in perturbations(sample, COLUMNS, ROLES, "table", "group")}["fewer_rows"].df
        assert len(fewer) < len(sample)
        assert set(fewer["Product line"]) == set(sample["Product line"])

    def test_more_rows_continues_dates_and_numbers(self) -> None:
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
                "Price": [1.0, 2.0, 3.0, 4.0, 5.0],
                "Group": ["a"] * 5,
            }
        )
        roles = parse_roles(["`date` (datetime) - day", "`price` (numeric) - price", "`series` (categorical) - line"])
        columns = {"date": "Date", "price": "Price", "series": "Group"}
        more = {i.name: i for i in perturbations(df, columns, roles, "table", "series")}["more_rows"].df
        assert len(more) == ROW_FACTOR * len(df)
        assert more["Date"].is_unique and more["Date"].is_monotonic_increasing
        assert more["Price"].is_monotonic_increasing
        assert set(more["Group"]) == {"a"}  # the colour-driving role keeps its values

    def test_scaled(self, sample: pd.DataFrame) -> None:
        scaled = {i.name: i for i in perturbations(sample, COLUMNS, ROLES, "table", "group")}["scaled"].df
        assert scaled["Sales (thousand USD)"].tolist() == [v * SCALE + SHIFT for v in sample["Sales (thousand USD)"]]

    def test_no_category_perturbations_without_categorical_columns(self) -> None:
        df = pd.DataFrame({"x": np.arange(10.0), "y": np.arange(10.0) ** 2})
        roles = parse_roles(["`x` (numeric) - x", "`y` (numeric) - y"])
        names = [item.name for item in perturbations(df, {"x": "x", "y": "y"}, roles, "table")]
        assert names == ["renamed", "fewer_rows", "more_rows", "scaled"]

    def test_generated_excluded_and_network_specs_have_none(self, sample: pd.DataFrame) -> None:
        """A network block may bind `nodes` beside the edges; its smoke run waits for network eligibility (Copilot)."""
        assert perturbations(sample, COLUMNS, ROLES, "generated") == []
        assert perturbations(sample, COLUMNS, ROLES, "excluded") == []
        assert perturbations(sample, COLUMNS, ROLES, "network", "group") == []

    def test_a_fixed_two_group_column_keeps_its_groups(self) -> None:
        """violin-split's binary halves stay two in every perturbation; the axis categories still vary (Copilot)."""
        roles = parse_roles(
            [
                "`category` (string) - group labels for the x-axis",
                "`value` (numeric) - values",
                "`split_group` (string/binary) - binary grouping variable for left/right halves",
            ]
        )
        df = pd.DataFrame(
            {"Dept": ["A", "A", "B", "B", "C", "C"], "Salary": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], "Gender": ["F", "M"] * 3}
        )
        columns = {"category": "Dept", "value": "Salary", "split_group": "Gender"}
        items = {item.name: item for item in perturbations(df, columns, roles, "table", "split_group")}
        assert "single_group" not in items
        for item in items.values():
            assert item.df[item.columns["split_group"]].nunique() == 2, item.name
        assert items["more_categories"].df["Dept"].nunique() == 4
        assert items["fewer_categories"].df["Dept"].nunique() == 2

    def test_numeric_group_codes_stay_groups_in_more_rows(self) -> None:
        """Groups coded 0 and 1 are a valid binding; ten copies must not make twenty groups (Copilot)."""
        roles = parse_roles(["`x` (numeric) - x", "`y` (numeric) - y", "`group` (categorical) - series"])
        df = pd.DataFrame({"x": [1.0, 2.0, 1.0, 2.0], "y": [3.0, 4.0, 5.0, 6.0], "g": [0, 0, 1, 1]})
        more = {i.name: i for i in perturbations(df, {"x": "x", "y": "y", "group": "g"}, roles, "table", "group")}
        assert set(more["more_rows"].df["g"]) == {0, 1}
        assert more["more_rows"].df["x"].nunique() == 2 * ROW_FACTOR


class TestSingleGroupRule:
    def test_a_free_group_role(self) -> None:
        assert single_group_allowed(ROLES, "table", "group")

    @pytest.mark.parametrize(
        "bullet",
        [
            "`split_group` (string/binary) - binary grouping variable for left/right halves",
            "`group` (categorical) - the two samples being compared",
            "`group` (boolean) - treated or not",
        ],
    )
    def test_a_role_that_fixes_its_groups(self, bullet: str) -> None:
        roles = parse_roles(["`value` (numeric) - v", bullet])
        assert not single_group_allowed(roles, "table", roles[1].name)

    def test_no_colour_role_or_another_shape(self) -> None:
        assert not single_group_allowed(ROLES, "table", None)
        assert not single_group_allowed(ROLES, "matrix", "group")
        assert not single_group_allowed(ROLES, "network", "group")


class TestMatrix:
    def test_matrix_perturbations_keep_it_square_without_a_fill(self) -> None:
        labels = ["a", "b", "c"]
        df = pd.DataFrame(np.eye(3), index=labels, columns=labels)
        items = {item.name: item for item in perturbations(df, {}, [], "matrix")}
        assert set(items) == {"renamed", "more_categories", "fewer_categories", "scaled"}
        assert items["renamed"].retired == frozenset(labels)
        assert items["more_categories"].df.shape == (4, 4)
        assert not items["more_categories"].df.isna().to_numpy().any()
        assert items["fewer_categories"].df.shape == (2, 2)


class TestSmokeSource:
    def test_the_block_is_replaced_and_the_constants_rewritten(self) -> None:
        source = (FIXTURES / "bar_grouped_matplotlib.py").read_text(encoding="utf-8")
        item = perturbations(
            pd.DataFrame({"Quarter": ["Q1"], "Product line": ["A"], "Sales (thousand USD)": [1]}),
            COLUMNS,
            ROLES,
            "table",
            "group",
        )[0]
        code = smoke_source(source, item, "/tmp/table.pkl")
        ast.parse(code)
        assert "df = pd.read_pickle('/tmp/table.pkl')" in code
        assert "Electronics" not in code
        record = check_source(code, ROLES, "table", library="matplotlib")
        assert record.findings == []
        constants = _string_constants(code)
        assert {constants[name] for name in record.constants.values()} == set(item.columns.values())

    def test_extra_columns_follow_the_renames(self) -> None:
        """`# role: extra` constants are not role-keyed; the renamed run must still rename them (Copilot)."""
        source = (FIXTURES / "bar_grouped_matplotlib.py").read_text(encoding="utf-8")
        source = source.replace(
            'SALES = "Sales (thousand USD)"  # role: value\n',
            'SALES = "Sales (thousand USD)"  # role: value\nNOTE = "Note"  # role: extra\nRANK = "Rank"  # role: extra\n',
        )
        sample = pd.DataFrame(
            {"Quarter": ["Q1"], "Product line": ["A"], "Sales (thousand USD)": [1], "Note": ["n"], "Rank": [1]}
        )
        item = perturbations(sample, COLUMNS, ROLES, "table", "group")[0]
        constants = _string_constants(smoke_source(source, item, "/tmp/table.pkl"))
        assert {constants["NOTE"], constants["RANK"]} <= set(item.df.columns)
        assert {constants["QUARTER"], constants["PRODUCT_LINE"], constants["SALES"]} <= set(item.df.columns)


def _string_constants(code: str) -> dict[str, str]:
    return {
        node.targets[0].id: node.value.value
        for node in ast.parse(code).body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
