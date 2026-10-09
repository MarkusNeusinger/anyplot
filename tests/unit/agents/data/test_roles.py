"""Tests for agents/anyplot/data/roles.py: the `## Data` bullet grammar and a sweep over the catalogue."""

import re
from pathlib import Path

import pytest

from agents.anyplot.data.roles import MAX_ROLE_NAME_CHARS, MAX_VARIADIC_NAME_CHARS, DataRole, parse_roles, type_words
from agents.anyplot.schemas import ROLE_PATTERN


REPO_ROOT = Path(__file__).resolve().parents[4]
PLOTS = REPO_ROOT / "plots"


def one(bullet: str) -> DataRole:
    roles = parse_roles([bullet])
    assert len(roles) == 1, roles
    return roles[0]


class TestBullets:
    def test_plain_role(self) -> None:
        assert one("`x` (numeric) - Independent variable values") == DataRole(
            name="x", kinds=("numeric",), required=True, variadic=False, description="Independent variable values"
        )

    def test_alternative_kinds_keep_their_order(self) -> None:
        assert one("`x` (datetime/numeric) - continuous axis values").kinds == ("datetime", "numeric")
        assert one("`x` (numeric or categorical) - axis").kinds == ("numeric", "categorical")

    @pytest.mark.parametrize(
        ("type_text", "kinds"),
        [
            ("float", ("numeric",)),
            ("int, optional", ("numeric",)),
            ("string", ("text",)),
            ("str", ("text",)),
            ("categorical/ordinal", ("categorical",)),
            ("date", ("datetime",)),
            ("binary", ("boolean",)),
            ("bool, optional", ("boolean",)),
            ("numeric array", ("numeric",)),
            ("float[]", ("numeric",)),
            ("string[] or int[], optional", ("text", "numeric")),
            ("numeric, mV", ("numeric",)),
            ("categorical: decision/chance/terminal", ("categorical",)),
            ("list of dicts", ("text",)),
            ("dict or list", ("text",)),
            ("geometry", ("text",)),
            ("2D array, 9×9", ()),
            ("optional, list", ()),
            ("`event_date`, `event_label`", ()),
            ("", ()),
        ],
    )
    def test_kinds_from_the_type_parentheses(self, type_text: str, kinds: tuple[str, ...]) -> None:
        assert one(f"`v` ({type_text}) - something").kinds == kinds

    def test_unknown_type_words_are_reported(self) -> None:
        assert type_words("list of tuples/dicts") == (("text",), ["tuples", "dicts"])
        assert type_words("numeric, degrees 0-360") == (("numeric",), [])

    def test_a_bullet_without_type_parentheses_is_untyped(self) -> None:
        role = one("`weights` - Edge weights")

        assert role.kinds == ()
        assert role.description == "Edge weights"

    @pytest.mark.parametrize(
        "bullet",
        [
            "`series` (categorical) - Optional grouping variable if data is in long format",
            "`size` (numeric, optional) - bubble area",
            "`label` (str) - point labels; optional",
            "`gene` (categorical, required for gene-track rows, optional elsewhere) - track",
        ],
    )
    def test_optional_roles(self, bullet: str) -> None:
        assert one(bullet).required is False

    @pytest.mark.parametrize(
        ("separator", "description"), [(" - ", "values"), (" — ", "values"), (": ", "values"), (" ", "values")]
    )
    def test_separators(self, separator: str, description: str) -> None:
        assert one(f"`y` (numeric){separator}values").description == description

    def test_several_names_share_type_and_description(self) -> None:
        roles = parse_roles(["`start_name`, `end_name` (string) - location names"])

        assert [role.name for role in roles] == ["start_name", "end_name"]
        assert all(role.kinds == ("text",) and role.description == "location names" for role in roles)

    def test_three_named_leads(self) -> None:
        roles = parse_roles(["`lead_I`, `lead_II`, `lead_III` (numeric, mV) - limb leads"])

        assert [role.name for role in roles] == ["lead_I", "lead_II", "lead_III"]
        assert not any(role.variadic for role in roles)

    def test_alternatives_are_one_role_named_by_the_first(self) -> None:
        role = one("`price` or `value` (numeric) - Asset price, portfolio value, or cumulative returns")

        assert role.name == "price"
        assert role.variadic is False

    def test_names_keep_digits_and_capitals(self) -> None:
        roles = parse_roles(
            [
                "`log2_fold_change` (numeric) - effect size",
                "`lower_95` (numeric) - lower bound",
                "`temperature_K` (numeric) - temperature in kelvin",
            ]
        )

        assert [role.name for role in roles] == ["log2_fold_change", "lower_95", "temperature_K"]

    def test_names_are_made_to_fit_the_role_pattern(self) -> None:
        roles = parse_roles(["`bad-name` (numeric) - x", "`2x` (numeric) - y", "`" + "n" * 40 + "` (numeric) - z"])

        assert [role.name for role in roles] == ["bad_name", "_2x", "n" * MAX_ROLE_NAME_CHARS]
        assert all(re.fullmatch(ROLE_PATTERN, role.name) for role in roles)

    def test_a_repeated_name_keeps_the_first_bullet(self) -> None:
        roles = parse_roles(["`x` (numeric) - first", "`x` (datetime) - second"])

        assert roles == [DataRole(name="x", kinds=("numeric",), required=True, variadic=False, description="first")]

    @pytest.mark.parametrize(
        "bullet",
        [
            "Size: 10-100 time points, 2-8 series",
            "Example: monthly revenue by product category over two years",
            "Note: Notch reliability improves with larger sample sizes",
            "Constraint: All three components must sum to 100%",
            "Derived `cumulative_quantity` (numeric) - Running sum of quantity",
            "**Note**: values should sum to 100",
            "",
            "`",
            "``",
            "`(` (",
            "((((",
            "`...` (numeric) - only an ellipsis",
            "`---` (numeric) - nothing usable",
        ],
    )
    def test_bullets_that_are_not_roles(self, bullet: str) -> None:
        assert parse_roles([bullet]) == []


class TestVariadic:
    def test_numbered_list_with_ellipsis(self) -> None:
        role = one("`y1, y2, y3, ...` (numeric) - values for each series to be stacked")

        assert role == DataRole(
            name="y",
            kinds=("numeric",),
            required=True,
            variadic=True,
            description="values for each series to be stacked",
        )
        assert role.member(2) == "y2"

    def test_separate_backticks_with_a_trailing_ellipsis(self) -> None:
        role = one("`y_1`, `y_2`, ... (numeric) - Multiple series to distinguish with different line styles")

        assert (role.name, role.variadic, role.member(1)) == ("y_", True, "y_1")

    @pytest.mark.parametrize(
        ("bullet", "name"),
        [
            ("`variable_1` through `variable_n` (numeric) - Multiple numeric attributes", "variable_"),
            ("`dimension_1` through `dimension_n` (categorical) - categorical variables", "dimension_"),
            ("`lead_V1` through `lead_V6` (numeric, mV) - precordial leads", "lead_V"),
            ("`percentile_3` through `percentile_97` (numeric) - reference percentiles", "percentile_"),
        ],
    )
    def test_through_ranges(self, bullet: str, name: str) -> None:
        role = one(bullet)

        assert (role.name, role.variadic) == (name, True)

    def test_an_index_inside_the_name_moves_to_the_end(self) -> None:
        roles = parse_roles(["`y1_lower, y1_upper, ...` (numeric) - lower and upper bounds for each series"])

        assert [(role.name, role.variadic) for role in roles] == [("y_lower", True), ("y_upper", True)]

    def test_numbered_names_without_an_ellipsis_are_fixed_roles(self) -> None:
        roles = parse_roles(["`y1`, `y2` (numeric) - exactly two series"])

        assert [(role.name, role.variadic) for role in roles] == [("y1", False), ("y2", False)]

    def test_variadic_names_leave_room_for_member_numbers(self) -> None:
        role = one("`" + "v" * 40 + "1, " + "v" * 40 + "2, ...` (numeric) - many")

        assert len(role.name) == MAX_VARIADIC_NAME_CHARS
        assert re.fullmatch(ROLE_PATTERN, role.member(50))

    def test_the_description_may_mention_through_or_ellipses(self) -> None:
        role = one("`period` (integer) - Number of periods since signup (0, 1, 2, ...), through the end")

        assert (role.name, role.variadic) == ("period", False)


class TestBoldBullets:
    def test_bold_variable_labels_become_roles(self) -> None:
        roles = parse_roles(
            [
                "**X variable**: Continuous variable (often time)",
                "**Y variable**: Single numeric variable",
                "**Category variable**: Categorical grouping variable",
            ]
        )

        assert [(role.name, role.kinds) for role in roles] == [
            ("x", ("numeric", "datetime")),
            ("y", ("numeric",)),
            ("category", ("categorical",)),
        ]
        assert all(role.required and not role.variadic for role in roles)


class TestRealSpecs:
    def test_area_stacked(self) -> None:
        roles = parse_roles(AREA_STACKED)

        assert roles == [
            DataRole("x", ("datetime", "numeric"), True, False, "continuous axis values, typically time periods"),
            DataRole("y", ("numeric",), True, True, "values for each series to be stacked"),
            DataRole("category", ("categorical",), True, False, "labels identifying each series"),
        ]

    def test_line_multi(self) -> None:
        roles = parse_roles(LINE_MULTI)

        assert [(role.name, role.kinds, role.required, role.variadic) for role in roles] == [
            ("x", ("numeric", "datetime"), True, False),
            ("y", ("numeric",), True, True),
            ("series", ("categorical",), False, False),
        ]


def _catalogue_data_bullets() -> list[tuple[str, list[str]]]:
    from automation.scripts.sync_to_postgres import _parse_markdown_section

    specs = []
    for path in sorted(PLOTS.glob("*/specification.md")):
        bullets = _parse_markdown_section(path.read_text(encoding="utf-8"), "Data", as_bullets=True)
        assert isinstance(bullets, list)
        specs.append((path.parent.name, bullets))
    return specs


@pytest.mark.skipif(not PLOTS.is_dir(), reason="plots/ is not checked out")
def test_every_catalogue_spec_parses() -> None:
    """The stored `## Data` bullets of every spec: never an exception, always valid unique names."""
    specs = _catalogue_data_bullets()
    typed = 0
    for spec_id, bullets in specs:
        roles = parse_roles(bullets)
        names = [role.name for role in roles]
        assert len(names) == len(set(names)), spec_id
        for role in roles:
            assert re.fullmatch(ROLE_PATTERN, role.name), (spec_id, role.name)
            if role.variadic:
                assert re.fullmatch(ROLE_PATTERN, role.member(50)), (spec_id, role.name)
        typed += any(role.kinds for role in roles)

    assert specs
    assert typed >= 0.95 * len(specs)


AREA_STACKED = [
    "`x` (datetime/numeric) - continuous axis values, typically time periods",
    "`y1, y2, y3, ...` (numeric) - values for each series to be stacked",
    "`category` (categorical) - labels identifying each series",
    "Size: 10-100 time points, 2-8 series",
    "Example: monthly revenue by product category over two years",
]

LINE_MULTI = [
    "`x` (numeric/datetime) - Shared sequential or time values for alignment",
    "`y1, y2, ...` (numeric) - Multiple continuous series to compare",
    "`series` (categorical) - Optional grouping variable if data is in long format",
    "Size: 10-200 points per series, 2-6 series recommended",
    "Example: Monthly sales for 3 product lines, daily stock prices for 4 companies",
]
