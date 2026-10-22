"""The wide-table suggestion: a deterministic `pivot_longer` offered when the spec wants long data.

A box, violin, strip or bar spec wants one category column and one value column
(`category` (string), `value` (numeric)); a pasted table such as
`Sensor_A,Sensor_B,Sensor_C` holds the same quantity side by side instead, so the
default bindings leave the category open and bind only the first column.
`long_suggestion` recognises that shape from the spec's roles and the dataset
profile alone, and returns the one operation that makes the table long:
`pivot_longer` of the measurement columns, the column names into one new column and the
values into another (named by `long_names`). The page offers it as `.to_long()`
(applied by `POST /v1/sessions/{sid}/dataset/to_long`, no model call), and the root's
summary mentions it. No ADK import.

The rule, every condition required:

* **The spec wants long data:** it has exactly one required single (not variadic)
  role whose kinds are categorical or text only, and exactly one required single role
  whose kinds are numeric only (a spec with two required labels, such as box-grouped's
  `category` and `subcategory`, would keep one of them open). A spec with a variadic numeric family (`y1, y2, ...`, which
  takes wide data as it is) or with two required numeric roles (a scatter's `x` and
  `y`) never gets the suggestion.
* **The table is wide:** at least two numeric columns (`integer` or `number`), at
  most `MAX_LONGER_COLUMNS`, and no text or boolean column, which could already be
  the category (a table with a label column is long, or its labels are the user's
  choice to make). A datetime column is a key: it is kept, and so is a column of
  years or of a part of a date (`temporal.time_keys`: `Jahr` beside `CO2` and
  `Bevölkerung`), and so is a first column that numbers the rows (`_numbering_key`:
  `id`, `Nr`, `Stunde` 0 to 3); every other numeric column is pivoted.
* **The result fits:** at most `MAX_ROWS` rows. The new names (`long_names`) never name
  an input column and never decide the offer.

The matrix rule (live test round 7 of 2026-10-16): a heatmap's `x` and `y` (string or
numeric labels) and `value`, or a grouped box's `category`, `subcategory` and `value`,
take a wide matrix such as `Stunde;Mo;Di;...;So` the same way, with one label column
kept. Every condition required:

* **The spec wants a long matrix:** its required single roles are exactly two roles
  that take labels (their kinds include categorical or text; a heatmap's also take
  numbers), both of a grid or grouped chart (`MATRIX_ROLES`: never a flow's `source`
  and `target`, a hierarchy or a party's color), and one numeric-only role, and no
  variadic numeric family.
* **The table is a wide matrix:** one row-label column (`_row_key`: the one text
  column, else the one date column, else a first column of whole numbers that is a
  year or every hour of a range, `Stunde` 0 to 23), with a distinct label in every
  row and none missing, which is kept as the key; at least `MIN_MATRIX_COLUMNS` other
  numeric columns (at most `MAX_LONGER_COLUMNS`); and no other column. Long data such
  as `day, hour, count` (two number columns, the day repeated) stays as it is.
* **The result fits:** as above. The column names go into the column for the second
  label role in spec order (`y`, `subcategory`), the values into the value role's; the
  default bindings give the kept label column to the first (`x`, `category`), as they
  do for the wide table already.

Before this rule the default bindings put a heatmap's `y` on the numbers of `Mo` and
its `value` on `Di`, and the plot drew 14 rows of nonsense; `bindings.label_siblings`
now keeps a label role off the measurement columns of a table this module calls wide.

The new columns' names (`long_names`, live test round 8 of 2026-10-16): words, never
the roles' names, which became the plot's text ("Wert nach Wochentag und Stunde" came
from a column `value`, `Wochentag` only from the root's guess). The names column says
what the melted headers are when every header is a weekday, a month or a year
(`Weekday`, `Month`, `Year`), else `Category`; the values column is `Value`. The words
are generated text, so they follow the session language (`LONG_NAMES`, live round 9 of
2026-10-16: `Weekday` and `Value` became the axis and colorbar titles of a German
heatmap); the user's own headers are never translated. The new columns stay bound to the
roles they were made for whatever their names (`LongSuggestion.bindings`). What the values
measure is the user's to say: the root offers a rename when the notes or the file name tell it.
"""

import itertools
import re
from dataclasses import dataclass
from typing import Any

from core.spec_roles import DataRole

from ..language import DEFAULT_LANGUAGE, canonical
from ..schemas import MAX_ROWS, Binding, ColumnProfile, DatasetProfile
from .months import fold, named_months
from .parse import ID_WORDS
from .prepare import MAX_LONGER_COLUMNS
from .temporal import WORDS, time_keys


_LABEL_KINDS = frozenset({"categorical", "text"})
_NUMERIC_COLUMNS = frozenset({"integer", "number"})
_LABEL_COLUMNS = frozenset({"text", "boolean"})
MIN_MATRIX_COLUMNS = 3
"""The measurement columns a wide matrix has at least (the heatmap specs ask for 5 to 50); two number columns
beside a label column are more often a long table with an integer key."""
MATRIX_ROLES: frozenset[str] = frozenset(
    {
        *("x", "y", "x_category", "y_category", "fill_category", "row_labels", "column_labels"),
        *("category", "subcategory", "group", "component", "series", "split_group"),
        *("angular", "radial", "entity", "period", "season", "cycle"),
    }
)
"""Label roles whose pair makes a grid or a grouped chart, where melting a wide matrix is meaningful (review of
#12204). A pair of other roles is a flow (`source`, `target`), a hierarchy (`name`, `parent`, `level_1`), a
geometry, a color or a code (`party`, `color`, `newick_string`): their wide tables are no matrix of one measure."""


LONG_NAMES: dict[str, dict[str, str]] = {
    "en": {"category": "Category", "weekday": "Weekday", "month": "Month", "year": "Year", "value": "Value"},
    "de": {"category": "Kategorie", "weekday": "Wochentag", "month": "Monat", "year": "Jahr", "value": "Wert"},
    "fr": {"category": "Catégorie", "weekday": "Jour", "month": "Mois", "year": "Année", "value": "Valeur"},
    "es": {"category": "Categoría", "weekday": "Día", "month": "Mes", "year": "Año", "value": "Valor"},
    "it": {"category": "Categoria", "weekday": "Giorno", "month": "Mese", "year": "Anno", "value": "Valore"},
    "pt": {"category": "Categoria", "weekday": "Dia da semana", "month": "Mês", "year": "Ano", "value": "Valor"},
    "nl": {"category": "Categorie", "weekday": "Weekdag", "month": "Maand", "year": "Jaar", "value": "Waarde"},
    "pl": {"category": "Kategoria", "weekday": "Dzień tygodnia", "month": "Miesiąc", "year": "Rok", "value": "Wartość"},
}
"""The `.to_long()` column names (`long_names`) by session language: the names column by what its headers are,
and the values column. Generated text, so in the session language (owner rule: generated text follows the
session language, the user's own column names are never translated; live round 9 of 2026-10-16). A language
outside the table gets the English words. The page's offer card and the route compute the names from the same
session language, and the language route and every turn's `done` return the recomputed offer, so the card and
the applied operation agree when the language changes."""


def long_words(language: str) -> dict[str, str]:
    """The `LONG_NAMES` words for a session language (`de`, `Deutsch` and `German` share them), else English."""
    return LONG_NAMES.get(canonical(language), LONG_NAMES[DEFAULT_LANGUAGE])


_WEEKDAY_WORDS: dict[str, tuple[tuple[str, ...], ...]] = {
    # One tuple per day, Monday first: full names and standard abbreviations, compared folded (`terça` is `terca`).
    "en": (
        ("monday", "mon", "mo"),
        ("tuesday", "tue", "tues", "tu"),
        ("wednesday", "wed", "we"),
        ("thursday", "thu", "thur", "thurs", "th"),
        ("friday", "fri", "fr"),
        ("saturday", "sat", "sa"),
        ("sunday", "sun", "su"),
    ),
    "de": (
        ("montag", "mo", "mon"),
        ("dienstag", "di", "die"),
        ("mittwoch", "mi", "mit"),
        ("donnerstag", "do", "don"),
        ("freitag", "fr", "fre"),
        ("samstag", "sa", "sam", "sonnabend"),
        ("sonntag", "so", "son"),
    ),
    "fr": (
        ("lundi", "lun", "lu"),
        ("mardi", "mar", "ma"),
        ("mercredi", "mer", "me"),
        ("jeudi", "jeu", "je"),
        ("vendredi", "ven", "ve"),
        ("samedi", "sam", "sa"),
        ("dimanche", "dim", "di"),
    ),
    "es": (
        ("lunes", "lun", "lu"),
        ("martes", "mar", "ma"),
        ("miercoles", "mie", "mi"),
        ("jueves", "jue", "ju"),
        ("viernes", "vie", "vi"),
        ("sabado", "sab", "sa"),
        ("domingo", "dom", "do"),
    ),
    "it": (
        ("lunedi", "lun", "lu"),
        ("martedi", "mar", "ma"),
        ("mercoledi", "mer", "me"),
        ("giovedi", "gio", "gi"),
        ("venerdi", "ven", "ve"),
        ("sabato", "sab", "sa"),
        ("domenica", "dom", "do"),
    ),
    "pt": (
        ("segunda", "seg", "2a"),
        ("terca", "ter", "3a"),
        ("quarta", "qua", "4a"),
        ("quinta", "qui", "5a"),
        ("sexta", "sex", "6a"),
        ("sabado", "sab"),
        ("domingo", "dom"),
    ),
    "nl": (
        ("maandag", "ma"),
        ("dinsdag", "di"),
        ("woensdag", "wo"),
        ("donderdag", "do"),
        ("vrijdag", "vr"),
        ("zaterdag", "za"),
        ("zondag", "zo"),
    ),
}
"""Weekday names by language (review of #12206: Portuguese and Dutch had gaps, and the one mixed set read the
country codes `FR`, `ZA`, `MA` as days). The headers must all come from ONE language's set (`_weekdays`)."""
_WEEKDAYS: dict[str, dict[str, int]] = {
    language: {word: day for day, words in enumerate(days) for word in words}
    for language, days in _WEEKDAY_WORDS.items()
}
_FEIRA = re.compile(r"[- ]?feira$")
"""The Portuguese suffix of a weekday (`segunda-feira`), left off before the lookup."""
_YEAR_HEADER = re.compile(r"(?:1[5-9]|2[0-9])[0-9]{2}")
MIN_NAMED_HEADERS = 3
"""The distinct weekdays or years among the melted headers from which the names column is named after them."""
MIN_SHORT_WEEKDAYS = 5
"""The distinct days headers of at most two characters need (`Mo, Di, Mi, Do, Fr`): three such codes are as
likely country or state codes (`FR, SA, SO`, `MO, MI, MA`)."""


def _weekdays(folded: list[str]) -> bool:
    """Whether every header is a weekday of one and the same language, enough distinct days among them."""
    words = [_FEIRA.sub("", column) for column in folded]
    least = MIN_SHORT_WEEKDAYS if all(len(word) <= 2 for word in words) else MIN_NAMED_HEADERS
    for days in _WEEKDAYS.values():
        if all(word in days for word in words) and len({days[word] for word in words}) >= least:
            return True
    return False


def long_names(
    columns: list[str], keys: list[str], roles: tuple[str, str], language: str = DEFAULT_LANGUAGE
) -> tuple[str, str]:
    """The names column's and the values column's name for melting `columns` beside `keys` (`LONG_NAMES`, in the
    session `language`).

    Never a column's name, kept or melted (case-insensitive): pandas' `melt` refuses a `value_name` that names
    an input column (review of #12206: `Value,Other` melted into `Value` was a 500). A taken word gives way to
    the role's name (`roles`: the names and the values role), then to the word numbered (`Value 2`), so the
    names never decide whether a table gets the offer.
    """
    folded = [fold(column).rstrip(".").strip() for column in columns]
    if all(_YEAR_HEADER.fullmatch(column) for column in folded) and len(set(folded)) >= MIN_NAMED_HEADERS:
        kind = "year"
    elif named_months(columns) is not None:
        kind = "month"
    elif _weekdays(folded):
        kind = "weekday"
    else:
        kind = "category"
    words = long_words(language)
    taken = {name.casefold() for name in [*keys, *columns]}
    names_to = _free(words[kind], roles[0], taken)
    values_to = _free(words["value"], roles[1], taken | {names_to.casefold()})
    return names_to, values_to


def _free(word: str, role: str, taken: set[str]) -> str:
    """`word`, else `role`, else `word 2`, `word 3`, ...: the first that no name in `taken` (case-folded) has."""
    candidates = itertools.chain((word, role), (f"{word} {number}" for number in itertools.count(2)))
    return next(name for name in candidates if name.casefold() not in taken)


@dataclass(frozen=True)
class LongSuggestion:
    """The `pivot_longer` that makes a wide table long for the spec's category and value roles."""

    columns: list[str]
    names_to: str
    values_to: str
    keys: list[str]
    rows: int
    names_role: str
    """The role the names column is made for: the category role, or the second label role of a matrix."""
    values_role: str

    def bindings(self) -> list[Binding]:
        """The new columns bound to the roles they are made for, which `.to_long()` keeps whatever their names."""
        return [
            Binding(role=self.names_role, column=self.names_to),
            Binding(role=self.values_role, column=self.values_to),
        ]

    def operation(self) -> dict[str, Any]:
        """The `prepare_data` operation, as `prepare.Operation` validates it."""
        return {
            "op": "pivot_longer",
            "columns": list(self.columns),
            "names_to": self.names_to,
            "values_to": self.values_to,
        }

    def body(self) -> dict[str, Any]:
        """The `suggestion` field of a dataset answer: what the page names and what `.to_long()` applies."""
        return {
            "kind": "to_long",
            "columns": list(self.columns),
            "names_to": self.names_to,
            "values_to": self.values_to,
            "keys": list(self.keys),
            "rows": self.rows,
        }


def takes_labels(role: DataRole) -> bool:
    """Whether a role labels or splits the marks: its kinds include categorical or text (a heatmap's `x` and `y`,
    which also take numbers, included)."""
    return bool(set(role.kinds) & _LABEL_KINDS)


def long_suggestion(
    roles: list[DataRole], profile: DatasetProfile, language: str = DEFAULT_LANGUAGE
) -> LongSuggestion | None:
    """The suggestion for this spec and table, or None when neither rule above holds; the new columns' names
    (`long_names`, in the session `language`) never decide it."""
    single = [role for role in roles if not role.variadic and not role.computed]  # a computed role takes no column
    if any(role.variadic and set(role.kinds) == {"numeric"} for role in roles):
        return None
    values = [role for role in single if role.required and set(role.kinds) == {"numeric"}]
    if len(values) != 1:
        return None
    dtypes = {column.name: column.dtype for column in profile.columns}
    time = time_keys(profile)  # years and parts of a date say where a value sits: keys, never melted
    labels = [role for role in single if role.required and role.kinds and set(role.kinds) <= _LABEL_KINDS]
    if len(labels) == 1 and not any(dtype in _LABEL_COLUMNS for dtype in dtypes.values()):
        # A first column that numbers the rows (`id`, `Nr`, `Stunde` 0 to 3) is a key too, never a measure
        # (review of #12204: melted, it kept `category` off every column of `id,a,b,c`).
        numbering = _numbering_key(profile)
        keys = [name for name, dtype in dtypes.items() if dtype == "datetime" or name in time or name == numbering]
        names_to, least = labels[0].name, 2
    else:
        # The matrix rule: two label roles of a grid or grouped chart, one of them for the kept row labels.
        pair = [role for role in single if role.required and takes_labels(role)]
        required = [role for role in single if role.required]
        if len(pair) != 2 or len(required) != 3 or any(role.name not in MATRIX_ROLES for role in pair):
            return None
        key = _row_key(profile, time)
        # Another year or date-part column besides the row labels is a second key, no measurement to melt.
        if key is None or "boolean" in dtypes.values() or time - {key}:
            return None
        keys = [key]
        names_to, least = pair[1].name, MIN_MATRIX_COLUMNS
    measures = [name for name, dtype in dtypes.items() if dtype in _NUMERIC_COLUMNS and name not in keys]
    if not least <= len(measures) <= MAX_LONGER_COLUMNS or len(measures) + len(keys) != len(dtypes):
        return None
    names_role, values_role = names_to, values[0].name
    names_to, values_to = long_names(measures, keys, (names_role, values_role), language)
    rows = profile.rows * len(measures)
    if rows > MAX_ROWS:
        return None
    return LongSuggestion(measures, names_to, values_to, keys, rows, names_role, values_role)


def _row_key(profile: DatasetProfile, time: set[str]) -> str | None:
    """The row labels of a wide matrix, or None: the one text column, else the one date column, else a first
    column of whole numbers that is a time key or every number of its range (`Stunde` 0 to 23). Each with a
    distinct value in every row and none missing: long data such as `day, hour, count` repeats its labels."""
    columns = profile.columns
    texts = [column for column in columns if column.dtype == "text"]
    dates = [column for column in columns if column.dtype == "datetime"]
    if texts:
        key = texts[0] if len(texts) == 1 and not dates else None
    elif dates:
        key = dates[0] if len(dates) == 1 else None
    else:
        first = columns[0] if columns else None
        key = first if first is not None and first.dtype == "integer" and (first.name in time or _run(first)) else None
    if key is None or key.missing or key.unique != profile.rows:
        return None
    return key.name


def _numbering_key(profile: DatasetProfile) -> str | None:
    """The first column when it numbers the rows: whole numbers, one per row, none missing, and every number of
    its range (`1` to `n`, `100` to `109`, an hour `0` to `3`) or a name that says ids (`id`, `Nr`, `Code`)."""
    first = profile.columns[0] if profile.columns else None
    if first is None or first.dtype != "integer" or first.missing or first.unique != profile.rows:
        return None
    named = bool(set(WORDS.findall(first.name.casefold())) & ID_WORDS)
    return first.name if named or _run(first) else None


def _run(column: ColumnProfile) -> bool:
    """Whole numbers that hold every number of their range, at least three (`0` to `23`): steps, not measures."""
    if not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return False
    return 3 <= column.unique == int(column.max - column.min) + 1
