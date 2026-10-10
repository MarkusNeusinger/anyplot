"""Generate the synthetic spike-X fixture cases: 10 specs x matplotlib and seaborn x 6 perturbations.

Every dataset is invented and drawn from a seeded NumPy generator, so a rerun writes
byte-identical files. Run it from the repository root:

    uv run --extra agents python -m agents.evals.make_fixtures          # (re)write the 120 cases
    uv run --extra agents python -m agents.evals.make_fixtures --check  # exit 1 when a file is stale

It writes `agents/evals/fixtures/cases/<spec>-<library>-<perturbation>/` with
`case.json` and `data.csv` and leaves every other case directory alone (the two
hand-written cases `scatter-basic-matplotlib` and `bar-grouped-seaborn` stay as they
are). A NumPy upgrade that changes a random stream makes `--check` and the unit test
fail; rerun the generator and commit the result.

**The ten specs.** Each covers another plot family, and the readiness scan
(`agents/anyplot/code/readiness.py`) marks both its matplotlib and its seaborn file
`clean` or `coupled`, never `blocked` (`tests/unit/agents/evals/test_make_fixtures.py`
asserts it):

| Spec | Family | matplotlib | seaborn |
|---|---|---|---|
| `scatter-basic` | scatter | coupled | coupled |
| `line-basic` | line (numeric x) | coupled | coupled |
| `bar-grouped` | bar (grouped) | coupled | coupled |
| `histogram-basic` | histogram | coupled | coupled |
| `box-basic` | box | coupled | coupled |
| `heatmap-basic` | heatmap | clean | coupled |
| `area-basic` | area | coupled | coupled |
| `violin-basic` | violin | coupled | coupled |
| `pie-basic` | pie | coupled | clean |
| `line-timeseries` | time series | coupled | coupled |

**The six perturbations** (the datasets of the design's spike-X row):

| Id | Dataset |
|---|---|
| `renamed` | the base data with other headers: German with umlauts, units and punctuation, or snake_case |
| `x10` | the base data with every measured value multiplied by 10 (catches literal axis limits) |
| `n12` | 12 rows |
| `n5000` | 5,000 rows; for bar, heatmap and pie these are raw records the plot must aggregate |
| `date` | the base data with a `DD.MM.YYYY` date column and an ISO date column: the plot's own time axis where the spec has one (`line-basic`, `area-basic`, `line-timeseries`), otherwise two unbound columns the adaptation must leave alone |
| `decimal-comma` | the base data as semicolon-separated text with decimal commas and `DD.MM.YYYY` dates |

The base data, which `renamed`, `x10`, `date` and `decimal-comma` share, is not a case
of its own. Every generated case expects `accepted`: each dataset is one a user could
paste for that spec. No real people, organisations or politics: stores, products,
customers and stations are invented.
"""

import argparse
import csv
import io
import itertools
import json
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal

import numpy as np

from agents.anyplot.data.parse import MAX_INPUT_BYTES
from agents.anyplot.schemas import MAX_COLUMN_NAME_CHARS, MAX_ROWS


CASES_DIR = Path(__file__).resolve().parent / "fixtures" / "cases"
LIBRARIES: tuple[str, ...] = ("matplotlib", "seaborn")
PERTURBATIONS: tuple[str, ...] = ("renamed", "x10", "n12", "n5000", "date", "decimal-comma")
SMOKE_TAG = "smoke"
SOURCE = "synthetic: agents/evals/make_fixtures.py"

Value = float | int | str | date | datetime
DateStyle = Literal["iso", "dmy"]


@dataclass(frozen=True)
class Column:
    """One dataset column: its header, values, the spec role it binds (if any) and how it is written."""

    name: str
    values: tuple[Value, ...]
    role: str | None = None
    decimals: int = 1
    measure: bool = False
    """Multiplied by 10 in the `x10` perturbation."""
    date_style: DateStyle = "iso"


Maker = Callable[[np.random.Generator, int], list[Column]]
ToDate = Callable[[Value], date | datetime]


@dataclass(frozen=True)
class SpecFixture:
    """How the cases of one spec are generated."""

    spec_id: str
    family: str
    seed: int
    base_rows: int
    make: Maker
    renamed: dict[str, str]
    date_mode: Literal["extra", "x", "native"]
    """`extra`: two unbound date columns; `x`: the numeric x column becomes a date; `native`: the spec's date column."""
    date_names: tuple[str, str]
    """The `DD.MM.YYYY` column (for `x`, the new x column) and the ISO column of the `date` perturbation."""
    aggregates: bool = False
    """Whether `n5000` holds raw records the plot must aggregate (one mark per group, not per row)."""
    to_date: ToDate | None = None
    """For `date_mode="x"`: the date of one x value."""


# --- Spec data -----------------------------------------------------------------------------


def _floats(values: np.ndarray) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _scatter(rng: np.random.Generator, n: int) -> list[Column]:
    """Advertising spend against revenue of invented stores, r about 0.7."""
    spend = rng.uniform(5, 120, n)
    revenue = np.clip(40 + 2.1 * spend + rng.normal(0, 70, n), 5, None)
    return [
        Column("Store", tuple(f"S{index:04d}" for index in range(1, n + 1))),
        Column("Ad Spend (kCHF)", _floats(spend), role="x", measure=True),
        Column("Revenue (kCHF)", _floats(revenue), role="y", measure=True),
    ]


def _line(rng: np.random.Generator, n: int) -> list[Column]:
    """A tank heating up over two hours: an exponential approach with sensor noise."""
    minutes = np.linspace(0, 120, n)
    temperature = 20 + 65 * (1 - np.exp(-minutes / 35)) + rng.normal(0, 0.6, n)
    return [
        Column("Elapsed Time (min)", _floats(minutes), role="x", decimals=3 if n > 1000 else 2),
        Column("Tank Temperature (°C)", _floats(temperature), role="y", measure=True),
    ]


SUBJECTS = ("Mathematics", "Physics", "Chemistry", "Biology", "History")
SUBJECT_MEANS = (68.0, 64.0, 66.0, 72.0, 75.0)
GRADES = ("Grade 7", "Grade 8", "Grade 9")
GRADE_OFFSETS = (0.0, 3.0, 6.0)


def _bar(rng: np.random.Generator, n: int) -> list[Column]:
    """Test scores by subject and grade: one mean per bar, or (n5000) individual scores to average."""
    if n <= len(SUBJECTS) * len(GRADES):
        cells = list(itertools.product(range(n // len(GRADES)), range(len(GRADES))))
        scores = [SUBJECT_MEANS[s] + GRADE_OFFSETS[g] + rng.normal(0, 2.5) for s, g in cells]
    else:
        subjects, grades = rng.integers(0, len(SUBJECTS), n), rng.integers(0, len(GRADES), n)
        cells = list(zip(subjects.tolist(), grades.tolist(), strict=True))
        scores = np.clip([SUBJECT_MEANS[s] + GRADE_OFFSETS[g] + rng.normal(0, 11) for s, g in cells], 0, 100).tolist()
    return [
        Column("Subject", tuple(SUBJECTS[s] for s, _ in cells), role="category"),
        Column("Grade Level", tuple(GRADES[g] for _, g in cells), role="group"),
        Column("Test Score", tuple(float(score) for score in scores), role="value", measure=True),
    ]


def _histogram(rng: np.random.Generator, n: int) -> list[Column]:
    """Delivery times of an invented shop: right-skewed, with a floor of eight minutes."""
    minutes = 8 + rng.gamma(3.0, 9.0, n)
    return [
        Column("Order ID", tuple(f"O-{10001 + index}" for index in range(n))),
        Column("Delivery Time (min)", _floats(minutes), role="values", measure=True),
    ]


LINES = ("Line A", "Line B", "Line C", "Line D")
LINE_MEANS = (500.4, 501.2, 499.1, 502.0)
LINE_SDS = (1.2, 2.0, 1.5, 0.9)


def _box(rng: np.random.Generator, n: int) -> list[Column]:
    """Fill weights of four bottling lines, with a few outliers."""
    lines = [index % len(LINES) for index in range(n)]
    weights = [rng.normal(LINE_MEANS[line], LINE_SDS[line]) for line in lines]
    outliers = rng.random(n) < 0.02
    shifts = rng.choice([-1.0, 1.0], n) * rng.uniform(6, 9, n)
    weights = [
        weight + (shift if outlier else 0.0) for weight, shift, outlier in zip(weights, shifts, outliers, strict=True)
    ]
    return [
        Column("Production Line", tuple(LINES[line] for line in lines), role="category"),
        Column("Fill Weight (g)", tuple(float(weight) for weight in weights), role="value", measure=True),
    ]


WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _response_profile(day: int, hour: int) -> float:
    """Mean minutes to the first answer of an invented support desk, by weekday and hour."""
    load = 6 + 10 * math.exp(-(((hour - 11) / 3) ** 2)) + 6 * math.exp(-(((hour - 15) / 2.5) ** 2))
    if day >= 5:
        load = load * 0.6 + 2
    if hour < 7 or hour > 20:
        load += 8  # the night shift is thin
    return load


def _heatmap(rng: np.random.Generator, n: int) -> list[Column]:
    """Response times by weekday and hour: one mean per cell, or (n5000) single tickets to average."""
    if n == 12:
        cells = list(itertools.product((0, 2, 4), (8, 12, 16, 20)))
    elif n <= len(WEEKDAYS) * 24:
        cells = list(itertools.product(range(len(WEEKDAYS)), range(24)))
    else:
        hour_weights = np.array([0.4 if hour < 7 or hour > 20 else 2.0 for hour in range(24)])
        days = rng.integers(0, len(WEEKDAYS), n)
        hours = rng.choice(24, n, p=hour_weights / hour_weights.sum())
        cells = list(zip(days.tolist(), hours.tolist(), strict=True))
        times = [rng.gamma(2.0, _response_profile(day, hour) / 2.0) for day, hour in cells]
        return _heatmap_columns(cells, times)
    times = [max(0.5, _response_profile(day, hour) + rng.normal(0, 0.8)) for day, hour in cells]
    return _heatmap_columns(cells, times)


def _heatmap_columns(cells: list[tuple[int, int]], times: list[float]) -> list[Column]:
    return [
        Column("Weekday", tuple(WEEKDAYS[day] for day, _ in cells), role="y"),
        Column("Hour", tuple(hour for _, hour in cells), role="x"),
        Column("Response Time (min)", tuple(float(time) for time in times), role="value", measure=True),
    ]


def _area(rng: np.random.Generator, n: int) -> list[Column]:
    """Daily energy use of an invented district: a yearly and a weekly cycle on a slow trend."""
    day = np.arange(1, n + 1)
    energy = (
        120
        + 25 * np.sin(2 * np.pi * day / 365 + 1.2)
        + 6 * np.sin(2 * np.pi * day / 7)
        + 0.01 * day
        + rng.normal(0, 4, n)
    )
    return [
        Column("Day", tuple(int(value) for value in day), role="x"),
        Column("Energy Use (MWh)", _floats(energy), role="y", measure=True),
    ]


SEGMENTS = ("Students", "Families", "Retirees", "Professionals")


def _basket(rng: np.random.Generator, segment: int) -> float:
    if segment == 0:
        return float(rng.lognormal(math.log(22), 0.45))
    if segment == 1:
        return float(max(10.0, rng.normal(85, 18)))
    if segment == 2:
        return float(rng.normal(34, 7) if rng.random() < 0.55 else rng.normal(72, 9))
    return float(20 + rng.gamma(2.2, 18))


def _violin(rng: np.random.Generator, n: int) -> list[Column]:
    """Basket values of four customer segments with distinct shapes (skewed, normal, bimodal, long tail)."""
    segments = [index % len(SEGMENTS) for index in range(n)]
    values = [max(1.0, _basket(rng, segment)) for segment in segments]
    return [
        Column("Customer Segment", tuple(SEGMENTS[segment] for segment in segments), role="category"),
        Column("Basket Value (EUR)", tuple(values), role="value", decimals=2, measure=True),
    ]


EXPENSES = ("Housing", "Food", "Transport", "Leisure", "Health", "Savings")
EXPENSE_AMOUNTS = (1850.0, 720.0, 410.0, 330.0, 260.0, 600.0)
MORE_EXPENSES = ("Insurance", "Education", "Clothing", "Utilities", "Gifts", "Other")
MORE_AMOUNTS = (380.0, 150.0, 120.0, 210.0, 60.0, 90.0)
RECORD_MEANS = (925.0, 38.0, 24.0, 45.0, 65.0, 300.0)
"""Mean amount of one booking per category in the raw records of `n5000`."""


def _pie(rng: np.random.Generator, n: int) -> list[Column]:
    """A household budget: one amount per category, or (n5000) single bookings to sum up."""
    if n <= len(EXPENSES) + len(MORE_EXPENSES):
        names = (EXPENSES + MORE_EXPENSES)[:n]
        amounts = [base * rng.uniform(0.9, 1.1) for base in (EXPENSE_AMOUNTS + MORE_AMOUNTS)[:n]]
    else:
        weights = np.array(EXPENSE_AMOUNTS) / np.array(RECORD_MEANS)
        picks = rng.choice(len(EXPENSES), n, p=weights / weights.sum())
        names = tuple(EXPENSES[pick] for pick in picks)
        amounts = [max(1.0, rng.gamma(2.0, RECORD_MEANS[pick] / 2.0)) for pick in picks]
    return [
        Column("Expense Category", tuple(names), role="category"),
        Column("Amount (CHF)", tuple(float(amount) for amount in amounts), role="value", decimals=2, measure=True),
    ]


def _timeseries(rng: np.random.Generator, n: int) -> list[Column]:
    """Fine dust at an invented station: daily means, or (n5000) hourly readings with a daily cycle."""
    if n <= 400:
        stamps: list[date | datetime] = [date(2025, 1, 1) + timedelta(days=index) for index in range(n)]
        values = [14 + 9 * math.cos(2 * math.pi * index / 365) + rng.normal(0, 3) for index in range(n)]
    else:
        start = datetime(2025, 1, 1)
        stamps = [start + timedelta(hours=index) for index in range(n)]
        values = [
            14
            + 9 * math.cos(2 * math.pi * index / 8760)
            + 4 * math.sin(2 * math.pi * (index % 24 - 6) / 24)
            + rng.normal(0, 2.5)
            for index in range(n)
        ]
    return [
        Column("Date", tuple(stamps), role="date"),
        Column("PM2.5 (µg/m³)", tuple(max(1.0, float(value)) for value in values), role="value", measure=True),
    ]


def _minutes_to_timestamp(value: Value) -> datetime:
    assert isinstance(value, float | int)
    return datetime(2026, 3, 14, 6, 0) + timedelta(minutes=round(float(value)))


def _day_to_date(value: Value) -> date:
    assert isinstance(value, int)
    return date(2026, 1, 1) + timedelta(days=value - 1)


SPECS: tuple[SpecFixture, ...] = (
    SpecFixture(
        "scatter-basic",
        "scatter",
        101,
        150,
        _scatter,
        {"Store": "Filiale", "Ad Spend (kCHF)": "Werbebudget in Tsd. CHF", "Revenue (kCHF)": "Umsatz in Tsd. CHF"},
        "extra",
        ("Campaign Start", "Reported On"),
    ),
    SpecFixture(
        "line-basic",
        "line",
        202,
        61,
        _line,
        {"Elapsed Time (min)": "t [min]", "Tank Temperature (°C)": "T_tank [°C]"},
        "x",
        ("Timestamp", "Logged At"),
        to_date=_minutes_to_timestamp,
    ),
    SpecFixture(
        "bar-grouped",
        "bar",
        303,
        15,
        _bar,
        {"Subject": "Fach", "Grade Level": "Jahrgangsstufe", "Test Score": "Punkte (Ø)"},
        "extra",
        ("Exam Date", "Graded On"),
        aggregates=True,
    ),
    SpecFixture(
        "histogram-basic",
        "histogram",
        404,
        400,
        _histogram,
        {"Order ID": "Bestellnummer", "Delivery Time (min)": "Lieferzeit / Minuten"},
        "extra",
        ("Order Date", "Delivered On"),
    ),
    SpecFixture(
        "box-basic",
        "box",
        505,
        240,
        _box,
        {"Production Line": "Abfülllinie", "Fill Weight (g)": "Füllgewicht [g]"},
        "extra",
        ("Shift Date", "Checked On"),
    ),
    SpecFixture(
        "heatmap-basic",
        "heatmap",
        606,
        168,
        _heatmap,
        {"Weekday": "Wochentag", "Hour": "Stunde", "Response Time (min)": "Antwortzeit Ø (min)"},
        "extra",
        ("Week Of", "Exported On"),
        aggregates=True,
    ),
    SpecFixture(
        "area-basic",
        "area",
        707,
        90,
        _area,
        {"Day": "tag_nr", "Energy Use (MWh)": "energieverbrauch_mwh"},
        "x",
        ("Date", "Metered On"),
        to_date=_day_to_date,
    ),
    SpecFixture(
        "violin-basic",
        "violin",
        808,
        400,
        _violin,
        {"Customer Segment": "segment", "Basket Value (EUR)": "basket_eur"},
        "extra",
        ("Purchase Date", "Synced On"),
    ),
    SpecFixture(
        "pie-basic",
        "pie",
        909,
        6,
        _pie,
        {"Expense Category": "Ausgabenposten", "Amount (CHF)": "Betrag CHF"},
        "extra",
        ("Booking Date", "Imported On"),
        aggregates=True,
    ),
    SpecFixture(
        "line-timeseries",
        "time-series",
        1010,
        365,
        _timeseries,
        {"Date": "Messdatum", "PM2.5 (µg/m³)": "Feinstaub PM2,5 (µg/m³)"},
        "native",
        ("Date", "Validated On"),
    ),
)


# --- Perturbations --------------------------------------------------------------------------


def _rng(spec: SpecFixture, stream: int) -> np.random.Generator:
    """An independent generator per spec and data stream, so no case depends on the generation order."""
    return np.random.default_rng([spec.seed, stream])


def _base(spec: SpecFixture) -> list[Column]:
    return spec.make(_rng(spec, 0), spec.base_rows)


def _with_dates(spec: SpecFixture, columns: list[Column]) -> list[Column]:
    """The `date` perturbation: a `DD.MM.YYYY` column and an ISO column, placed by the spec's date mode."""
    rng = _rng(spec, 99)
    rows = len(columns[0].values)
    dmy_name, iso_name = spec.date_names
    if spec.date_mode == "extra":
        start = date(2026, 1, 5)
        dmy = tuple(start + timedelta(days=int(offset)) for offset in rng.integers(0, 180, rows))
        lag = rng.integers(0, 5, rows)
        iso = tuple(day + timedelta(days=int(days)) for day, days in zip(dmy, lag, strict=True))
        return [*columns, Column(dmy_name, dmy, date_style="dmy"), Column(iso_name, iso, date_style="iso")]
    out: list[Column] = []
    for column in columns:
        if spec.date_mode == "x" and column.role == "x":
            assert spec.to_date is not None
            stamps = tuple(spec.to_date(value) for value in column.values)
            out.append(Column(dmy_name, stamps, role="x", date_style="dmy"))
            out.append(Column(iso_name, tuple(_shift(stamp, 1) for stamp in stamps), date_style="iso"))
        elif spec.date_mode == "native" and column.role == "date":
            out.append(replace(column, date_style="dmy"))
            out.append(Column(iso_name, tuple(_shift(stamp, 2) for stamp in column.values), date_style="iso"))
        else:
            out.append(column)
    return out


def _times_ten(value: Value) -> float:
    if not isinstance(value, float | int):
        raise TypeError("only numeric columns are measures")
    return float(value) * 10


def _shift(value: Value, days: int) -> date | datetime:
    assert isinstance(value, date)  # datetime is a date subclass
    return value + timedelta(days=days)


def perturbed(spec: SpecFixture, perturbation: str) -> tuple[list[Column], str]:
    """The columns of one perturbation and its delimiter."""
    if perturbation == "renamed":
        return [replace(column, name=spec.renamed.get(column.name, column.name)) for column in _base(spec)], ","
    if perturbation == "x10":
        scaled = [
            replace(column, values=tuple(_times_ten(value) for value in column.values)) if column.measure else column
            for column in _base(spec)
        ]
        return scaled, ","
    if perturbation == "n12":
        return spec.make(_rng(spec, 12), 12), ","
    if perturbation == "n5000":
        return spec.make(_rng(spec, 5000), 5000), ","
    if perturbation == "date":
        return _with_dates(spec, _base(spec)), ","
    if perturbation == "decimal-comma":
        return [replace(column, date_style="dmy") for column in _base(spec)], ";"
    raise ValueError(f"unknown perturbation {perturbation!r}")


# --- Writing ---------------------------------------------------------------------------------


def cell(value: Value, column: Column, *, decimal_comma: bool) -> str:
    """One value as text: fixed decimals for floats, ISO or `DD.MM.YYYY` for dates and timestamps."""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M") if column.date_style == "dmy" else value.strftime("%Y-%m-%dT%H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y") if column.date_style == "dmy" else value.isoformat()
    if isinstance(value, float):
        text = f"{value:.{column.decimals}f}"
        return text.replace(".", ",") if decimal_comma else text
    return str(value)


def to_csv(columns: list[Column], delimiter: str) -> str:
    """The dataset as delimited text with `\\n` line ends, quoted only where a field needs it."""
    decimal_comma = delimiter == ";"
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow([column.name for column in columns])
    for row in zip(*(column.values for column in columns), strict=True):
        writer.writerow(
            [cell(value, column, decimal_comma=decimal_comma) for value, column in zip(row, columns, strict=True)]
        )
    return buffer.getvalue()


def _tags(spec: SpecFixture, perturbation: str, columns: list[Column], smoke: bool) -> list[str]:
    tags = [spec.family, perturbation, "synthetic"]
    if perturbation == "renamed":
        tags.append("renamed-headers")
        if any(not column.name.isascii() for column in columns):
            tags.append("non-ascii-headers")
    elif perturbation == "x10":
        tags.append("scaled-values")
    elif perturbation == "n12":
        tags.append("small")
    elif perturbation == "n5000":
        tags.append("large")
        if spec.aggregates:
            tags.append("aggregation")
    elif perturbation == "date":
        tags += ["dd.mm.yyyy", "iso-date", "unbound-dates" if spec.date_mode == "extra" else "date-axis"]
    elif perturbation == "decimal-comma":
        tags.append("semicolon")
        if any(isinstance(column.values[0], date) for column in columns):
            tags.append("dd.mm.yyyy")
    if smoke:
        tags.append(SMOKE_TAG)
    return tags


def _is_smoke(index: int, library: str, perturbation: str) -> bool:
    """One smoke case per spec, cycling through the perturbations and alternating the library."""
    return perturbation == PERTURBATIONS[index % len(PERTURBATIONS)] and library == LIBRARIES[index % len(LIBRARIES)]


def case_id(spec_id: str, library: str, perturbation: str) -> str:
    return f"{spec_id}-{library}-{perturbation}"


def render_cases() -> dict[str, str]:
    """Every generated file as `{"<case-id>/<file>": text}`, built in memory."""
    files: dict[str, str] = {}
    for index, spec in enumerate(SPECS):
        for perturbation in PERTURBATIONS:
            columns, delimiter = perturbed(spec, perturbation)
            data = to_csv(columns, delimiter)
            _check_limits(spec, perturbation, columns, data)
            bindings = [{"role": column.role, "column": column.name} for column in columns if column.role]
            for library in LIBRARIES:
                case = {
                    "spec_id": spec.spec_id,
                    "library": library,
                    "locale": "de" if perturbation in ("renamed", "decimal-comma") else "en",
                    "perturbation": perturbation,
                    "bindings": bindings,
                    "expected": "accepted",
                    "tags": _tags(spec, perturbation, columns, _is_smoke(index, library, perturbation)),
                    "source": f"{SOURCE} (seed {spec.seed}, {perturbation})",
                }
                directory = case_id(spec.spec_id, library, perturbation)
                files[f"{directory}/case.json"] = json.dumps(case, indent=2, ensure_ascii=False) + "\n"
                files[f"{directory}/data.csv"] = data
    return files


def _check_limits(spec: SpecFixture, perturbation: str, columns: list[Column], data: str) -> None:
    """Every dataset fits the parser's limits, so a case never fails on its own size."""
    where = f"{spec.spec_id}/{perturbation}"
    if len(data.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError(f"{where}: {len(data.encode('utf-8'))} bytes is over the parser's {MAX_INPUT_BYTES}")
    if len(columns[0].values) > MAX_ROWS:
        raise ValueError(f"{where}: more than {MAX_ROWS} rows")
    if any(len(column.name) > MAX_COLUMN_NAME_CHARS for column in columns):
        raise ValueError(f"{where}: a header is longer than {MAX_COLUMN_NAME_CHARS} characters")


def write_cases(target: Path = CASES_DIR) -> list[Path]:
    """Write every generated file under `target`; other case directories are left alone."""
    written = []
    for relative, text in render_cases().items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
        written.append(path)
    return written


def stale_files(target: Path = CASES_DIR) -> list[str]:
    """The generated files that are missing under `target` or differ from what the generator writes."""
    stale = []
    for relative, text in render_cases().items():
        path = target / relative
        if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
            stale.append(relative)
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when a committed file differs from the generator")
    parser.add_argument("--out", type=Path, default=CASES_DIR, help="target directory (default: the fixture cases)")
    args = parser.parse_args(argv)
    if args.check:
        stale = stale_files(args.out)
        for relative in stale:
            print(f"stale: {relative}", file=sys.stderr)
        if stale:
            print("rerun: uv run --extra agents python -m agents.evals.make_fixtures", file=sys.stderr)
        return 1 if stale else 0
    written = write_cases(args.out)
    print(f"wrote {len(written)} files for {len(written) // 2} cases under {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
