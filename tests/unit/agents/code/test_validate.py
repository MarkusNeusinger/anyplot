"""Tests for agents/anyplot/code/validate.py.

Three corpora: every rule with a failing snippet and its nearest allowed sibling, every
bypass the design doc names, and the catalogue (never raises, runs under a time budget,
and prints a per-rule summary under `-s`; the catalogue is not clean by design).
"""

import pkgutil
import time
from collections import Counter
from pathlib import Path
from typing import get_args

import pytest

from agents.anyplot.code.validate import (
    BANNED_ATTRIBUTES,
    BANNED_IO,
    ESCAPE_ATTRIBUTES,
    LIBRARY_BANS,
    MAX_LITERAL_NUMBERS,
    MAX_STRING_CHARS,
    MODULE_ESCAPES,
    PLACEHOLDER,
    THEME_BINDING_MESSAGE,
    UNSAFE_HELPERS,
    UNSAFE_SUBMODULES,
    Finding,
    Profile,
    module_label,
    validate_adaptation,
    validate_data_code,
    validate_security,
)
from agents.anyplot.schemas import MAX_CODE_CHARS
from core.palette import IMPRINT

from .conftest import CATALOGUE_FILES, CODE_LIBRARIES


HEADER = """import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

THEME = os.getenv("ANYPLOT_THEME", "light")
df = pd.DataFrame({"a": [1, 2, 3]})
"""
THEME_LINE = 'THEME = os.getenv("ANYPLOT_THEME", "light")'
"""The theme block of every library's minimal file below."""
FOOTER = """
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
plt.savefig(f"plot-{THEME}.png", dpi=400)
"""

ORIGINAL = ["#009E73", "#C475FD", "#4467A3"]
ADAPTED = """import pandas as pd

df = load_user_data()
"""


def plot(body: str = "") -> str:
    """A minimal valid catalogue-shaped file with `body` between the THEME block and the save."""
    return HEADER + body + FOOTER


def security_rules(body: str, library: str = "matplotlib") -> set[str]:
    return {finding.rule for finding in validate_security(plot(body), library=library)}


def adaptation_rules(body: str, original: list[str] | None = None) -> set[str]:
    palette = ORIGINAL if original is None else original
    return {finding.rule for finding in validate_adaptation(ADAPTED + body, original_palette=palette)}


# --- interface -------------------------------------------------------------------------


class TestInterface:
    def test_profile_literal(self) -> None:
        assert get_args(Profile) == ("security", "adaptation", "data")

    def test_finding_is_frozen_and_hashable(self) -> None:
        finding = Finding("banned-name", "'open' is not allowed", 3)
        assert hash(finding) == hash(Finding("banned-name", "'open' is not allowed", 3))
        with pytest.raises(AttributeError):
            finding.rule = "other"  # type: ignore[misc]

    def test_valid_file_has_no_findings_in_either_profile(self) -> None:
        assert validate_security(plot(), library="matplotlib") == []
        assert validate_security(plot("import seaborn as sns\n"), library="seaborn") == []
        assert validate_adaptation(ADAPTED, original_palette=ORIGINAL) == []

    @pytest.mark.parametrize("library", ["plotly", "bokeh", "ggplot2", "d3"])
    def test_library_without_profile_raises(self, library: str) -> None:
        with pytest.raises(ValueError, match="no validator profile"):
            validate_security(plot(), library=library)

    def test_unknown_library_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown library"):
            validate_security(plot(), library="matplotlib2")

    def test_findings_are_sorted_by_line_and_carry_lines(self) -> None:
        findings = validate_security(plot("import sys\nx = open('f')\n"), library="matplotlib")
        assert [f.rule for f in findings] == ["banned-import", "banned-name"]
        assert findings[0].line == HEADER.count("\n") + 1
        assert findings[1].line == HEADER.count("\n") + 2

    def test_messages_are_one_line_and_bounded(self) -> None:
        name = "x" * 500
        findings = validate_security(plot(f"{name}.to_csv('out.csv')\n"), library="matplotlib")
        assert findings and all(len(f.message) <= 300 and "\n" not in f.message for f in findings)
        assert all(name not in f.message for f in findings)


# --- parse: size, encoding, syntax -------------------------------------------------------


class TestParse:
    def test_oversize_code(self) -> None:
        code = "x = 1\n" * (MAX_CODE_CHARS // 6 + 1)
        assert len(code) > MAX_CODE_CHARS
        findings = validate_security(code, library="matplotlib")
        assert [f.rule for f in findings] == ["size"]
        assert validate_adaptation(code, original_palette=[])[0].rule == "size"

    def test_code_at_the_limit_is_parsed(self) -> None:
        padding = "# " + "x" * (MAX_CODE_CHARS - len(plot()) - 3) + "\n"
        code = plot(padding)
        assert len(code) == MAX_CODE_CHARS
        assert validate_security(code, library="matplotlib") == []

    def test_lone_surrogate_is_not_utf8(self) -> None:
        findings = validate_security("x = '\udcff'\n", library="matplotlib")
        assert [f.rule for f in findings] == ["encoding"]

    def test_syntax_error_carries_the_line(self) -> None:
        findings = validate_security("x = 1\ndef (:\n", library="matplotlib")
        assert [(f.rule, f.line) for f in findings] == [("syntax", 2)]
        assert validate_adaptation("def (:", original_palette=[])[0].rule == "syntax"

    def test_null_byte_is_a_syntax_finding(self) -> None:
        assert [f.rule for f in validate_security("x = 1\x00\n", library="matplotlib")] == ["syntax"]

    def test_deep_nesting_never_raises(self) -> None:
        code = "x = " + "(" * 500 + "1" + ")" * 500 + "\n"
        assert validate_security(code, library="matplotlib")[0].rule == "syntax"

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param("return 1\n", id="module-level return"),
            pytest.param("break\n", id="break outside a loop"),
            pytest.param("continue\n", id="continue outside a loop"),
            pytest.param("plt.plot(x=1, x=2)\n", id="repeated keyword"),
            pytest.param("def f(a, a):\n    return a\n", id="repeated parameter"),
        ],
    )
    def test_compiler_level_syntax_error(self, body: str) -> None:
        assert [f.rule for f in validate_security(plot(body), library="matplotlib")] == ["syntax"]
        assert [f.rule for f in validate_adaptation(ADAPTED + body, original_palette=ORIGINAL)] == ["syntax"]

    def test_deep_attribute_chain_never_raises(self) -> None:
        chain = "a" + ".b" * 600 + ".read_x"
        findings = validate_security(plot(f"x = {chain}\n"), library="matplotlib")
        assert [f.rule for f in findings] == ["banned-call"]
        assert ".read_x" in findings[0].message and len(findings[0].message) <= 300

    def test_empty_code_is_a_finding_not_an_error(self) -> None:
        assert [f.rule for f in validate_security("", library="matplotlib")] == ["savefig-target"]
        assert [f.rule for f in validate_adaptation("", original_palette=[])] == ["placeholder-count"]


# --- imports ------------------------------------------------------------------------------


ALLOWED_IMPORTS = [
    "import numpy\n",
    "import math, statistics, datetime, collections, itertools, functools, textwrap, colorsys, re\n",
    "from collections import defaultdict\n",
    "from datetime import datetime, timedelta\n",
    "import matplotlib.patches as mpatches\n",
    "from matplotlib.colors import LinearSegmentedColormap\n",
    "from matplotlib import pyplot\n",
    "import matplotlib.ticker as mticker\n",
    "from scipy.stats import norm\n",
    "from scipy import stats\n",
    "import scipy.stats\n",
    "from scipy.interpolate import make_interp_spline\n",
    "from scipy.signal import savgol_filter\n",
    "from scipy.cluster.hierarchy import linkage\n",
    "from scipy.spatial.distance import pdist\n",
    "from sklearn.ensemble import RandomForestClassifier\n",
    "from sklearn import linear_model\n",
    "import sklearn.preprocessing\n",
    "import statsmodels.api as sm\n",
    "from statsmodels import api\n",
    "from statsmodels.tsa.stattools import acf\n",
    "from statsmodels.nonparametric.smoothers_lowess import lowess\n",
    "from statsmodels.graphics.mosaicplot import mosaic\n",
    "import statsmodels.graphics.tsaplots as tsaplots\n",
    "from scipy.optimize import curve_fit\n",
    "import scipy.optimize\n",
    "from scipy.special import expit\n",
    "from scipy.integrate import solve_ivp\n",
    "from scipy import ndimage\n",
    "from scipy.ndimage import gaussian_filter1d\n",
    "from mpl_toolkits.mplot3d import Axes3D\n",
    "import mpl_toolkits.mplot3d.art3d as art3d\n",
    "from mpl_toolkits.axes_grid1.inset_locator import inset_axes\n",
    "from mpl_toolkits.axes_grid1 import make_axes_locatable\n",
    "import mpl_toolkits.axisartist as axisartist\n",
    "from numpy import random\n",
    "from numpy.lib.stride_tricks import sliding_window_view\n",
    "from pandas.plotting import parallel_coordinates\n",
]
BANNED_IMPORTS = [
    "import sys\n",
    "import os.path\n",
    "from os import getenv\n",
    "import pathlib\n",
    "from pathlib import Path\n",
    "import importlib\n",
    "import subprocess\n",
    "import socket\n",
    "import urllib.request\n",
    "import requests\n",
    "import shutil\n",
    "import ctypes\n",
    "import pickle\n",
    "import string\n",
    "import json\n",
    "import io\n",
    "import random\n",
    "import builtins\n",
    "import scipy\n",
    "import scipy.io\n",
    "from scipy import io\n",
    "import scipy.datasets\n",
    "from scipy.datasets import face\n",
    "import mpl_toolkits\n",
    "from mpl_toolkits import basemap\n",
    "import cartopy.crs as ccrs\n",
    "import PIL.Image\n",
    "from PIL import Image\n",
    "import hashlib\n",
    "import qrcode\n",
    "from wordcloud import WordCloud\n",
    "from matplotlib_venn import venn3\n",
    "import squarify\n",
    "from adjustText import adjust_text\n",
    "from sklearn.datasets import load_iris\n",
    "from sklearn import datasets\n",
    "import sklearn.datasets\n",
    "from statsmodels.formula.api import ols\n",
    "import statsmodels.formula.api as smf\n",
    "import statsmodels\n",
    "import patsy\n",
    "import seaborn as sns\n",
    "import plotly.express as px\n",
]


class TestImports:
    @pytest.mark.parametrize("body", ALLOWED_IMPORTS)
    def test_allowed(self, body: str) -> None:
        assert security_rules(body) == set()

    @pytest.mark.parametrize("body", BANNED_IMPORTS)
    def test_banned(self, body: str) -> None:
        assert "banned-import" in security_rules(body)

    def test_seaborn_profile_allows_seaborn_and_matplotlib(self) -> None:
        assert security_rules("import seaborn as sns\nimport seaborn.objects as so\n", library="seaborn") == set()

    def test_matplotlib_profile_rejects_seaborn(self) -> None:
        assert security_rules("import seaborn as sns\n", library="matplotlib") == {"banned-import"}

    def test_star_import(self) -> None:
        assert security_rules("from numpy import *\n") == {"star-import"}

    @pytest.mark.parametrize("body", ["from . import helper\n", "from .helper import x\n", "from .. import x\n"])
    def test_relative_import(self, body: str) -> None:
        assert security_rules(body) == {"relative-import"}

    def test_import_inside_a_function_is_checked_too(self) -> None:
        # Returning the module is a finding of its own: a module is never a value.
        assert security_rules("def f():\n    import subprocess\n    return subprocess\n") == {
            "banned-import",
            "module-value",
        }

    def test_from_import_of_a_banned_function(self) -> None:
        assert security_rules("from numpy import load\n") == {"banned-call"}
        assert security_rules("from pandas import read_csv\n") == {"banned-call"}
        assert security_rules("from matplotlib.pyplot import show\n") == {"banned-attribute"}
        assert security_rules("from numpy import memmap\n") == {"banned-attribute"}
        assert security_rules("from numpy import linspace\n") == set()

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("import pandas.io\n", {"banned-import"}),
            ("import pandas.io.common as common\n", {"banned-import"}),
            ("from pandas.io import common\n", {"banned-import"}),
            ("from pandas.io.formats.style import Styler\n", {"banned-import"}),
            ("import numpy.lib.format as fmt\n", {"banned-import"}),
            ("from numpy.lib.format import open_memmap\n", {"banned-import", "banned-call"}),
            ("from pandas import io\n", {"banned-attribute"}),
        ],
    )
    def test_import_path_with_a_banned_component(self, body: str, expected: set[str]) -> None:
        assert security_rules(body) == expected

    def test_banned_component_message_names_the_component(self) -> None:
        findings = validate_security(plot("import numpy.lib.format as fmt\n"), library="matplotlib")
        assert [(f.rule, f.message, f.module) for f in findings] == [
            (
                "banned-import",
                "import of 'numpy.lib.format' reaches the banned name 'format' → the data comes only from "
                "df = load_user_data(), and the plot reads and writes no files",
                "numpy.lib.format",
            )
        ]

    @pytest.mark.parametrize(
        ("body", "module", "label", "alternative"),
        [
            ("import locale\n", "locale", "locale", "format numbers with f-strings or matplotlib.ticker.FuncFormatter"),
            ("import io\n", "io", "io", "the data comes only from df = load_user_data()"),
            ("from io import StringIO\n", "io", "io", "the data comes only from df = load_user_data()"),  # banned part
            ("import random\n", "random", "random", "a seeded np.random.default_rng(<int>) is only for jitter"),
            ("from os import getenv\n", "os.getenv", "os", 'os only as THEME = os.getenv("ANYPLOT_THEME", ...)'),
            ("import string\n", "string", "string", "use str methods, f-strings and literals"),
            ("import scipy\n", "scipy", "scipy", "import the scipy submodule itself, such as scipy.stats or scipy.fft"),
            (
                "from sklearn.datasets import load_iris\n",
                "sklearn.datasets.load_iris",
                "sklearn.datasets",
                "the data comes only from df",
            ),
            ("import yaml\n", "yaml", "yaml", "pure standard modules such as math, datetime, collections, re"),
            ("import jane_doe_records\n", "jane_doe_records", "?", "pure standard modules such as math, datetime"),
        ],
    )
    def test_banned_import_message_names_the_module_and_what_to_use(
        self, body: str, module: str, label: str, alternative: str
    ) -> None:
        """The rerun's 17 banned-import repairs got no hint; the line now names the module and the way around it.

        The repair line goes back to the model and quotes the path; the log gets only its label.
        """
        finding = next(f for f in validate_security(plot(body), library="matplotlib") if f.rule == "banned-import")

        assert finding.message.startswith(f"import of '{module}' ")
        assert " → " in finding.message and alternative in finding.message.split(" → ", 1)[1]
        assert finding.module == label

    def test_only_banned_imports_carry_a_module(self) -> None:
        findings = validate_security(plot("import sys\nx = eval('1')\n"), library="matplotlib")

        assert {(f.rule, f.module) for f in findings} == {("banned-import", "sys"), ("banned-name", None)}

    @pytest.mark.parametrize(
        ("path", "label"),
        [
            ("scipy.io.matlab", "scipy.io"),
            ("pandas.io.common", "pandas.io"),
            ("numpy.lib.format", "numpy.lib.format"),
            ("os.path", "os"),
            ("cartopy.crs", "cartopy"),
            ("a" * 45 + ".b", "?"),
            ("möbius", "?"),
            ("data_2024.Q1", "?"),
            ("Patient_Smith_Diagnosis", "?"),
            ("os_jane_doe", "?"),  # a prefix of a component is not a prefix of the path
            ("?", "?"),
        ],
    )
    def test_module_label_is_a_word_of_a_closed_vocabulary(self, path: str, label: str) -> None:
        """A word the model writes as an import path never reaches the log: only known module names do."""
        assert module_label(path) == label
        assert module_label(label) == label  # idempotent, so the eval harness re-checks a logged label with it

    def test_a_reader_call_says_where_the_data_comes_from(self) -> None:
        findings = validate_security(plot("x = pd.read_csv('data.csv')\n"), library="matplotlib")

        assert [f.message for f in findings if f.rule == "banned-call"] == [
            "'pd.read_csv' is not allowed → the data comes only from df = load_user_data(), "
            "and the plot reads and writes no files"
        ]


PURE_MODULE_USES = [
    "import warnings, typing, calendar, decimal, fractions, zoneinfo, enum, dataclasses\n",
    "import operator, bisect, heapq, numbers, cmath\n",
    "import warnings\nwarnings.filterwarnings('ignore', category=UserWarning)\n",
    "import warnings\nwith warnings.catch_warnings():\n    warnings.simplefilter('ignore')\n",
    "from scipy.fft import rfft, rfftfreq\nspectrum = np.abs(rfft(df['a'].to_numpy()))\n",
    "import scipy.fft\nfreqs = scipy.fft.rfftfreq(8, d=1.0)\n",
    "import scipy.linalg as la\nq, r = la.qr(np.eye(2))\n",
    "from scipy import constants\nc = constants.c\n",
    "from zoneinfo import ZoneInfo\ntz = ZoneInfo('Europe/Berlin')\n",
    "from operator import itemgetter\nrows = sorted([(1, 2)], key=itemgetter(1))\n",
    "import heapq\ntop = heapq.nlargest(3, [1, 2, 3])\n",
    "from bisect import bisect_left\ni = bisect_left([1, 2], 2)\n",
    "from decimal import Decimal\nx = Decimal('1.5')\n",
    "from fractions import Fraction\nx = Fraction(1, 3)\n",
    "import calendar\nnames = list(calendar.month_abbr)[1:]\n",
    "from enum import Enum\nLevel = Enum('Level', 'LOW HIGH')\n",
    "from dataclasses import dataclass, field\n",
    "from typing import Any, NamedTuple\nPoint = NamedTuple('Point', [('x', float)])\n",
    "import cmath\nz = cmath.exp(1j)\n",
    "v = df._values\n",  # a private attribute of a value, not of an imported module
    "top = df.main.max()\n",  # a column called main: calendar.main is banned on the calendar module only
    "up = df['close'] >= df['open']\n",  # OHLC columns: a key named like a builtin is data, not a reach for it
]
ESCAPES = [
    ("import warnings\nline = warnings.formatwarning('', UserWarning, 'f', 1)\n", "banned-call"),
    ("import warnings\nwarnings.showwarning('m', UserWarning, 'f', 1)\n", "banned-call"),
    ("import warnings\nwarnings.warn_explicit('m', UserWarning, 'f', 1)\n", "banned-call"),
    ("from warnings import formatwarning\n", "banned-call"),
    ("import zoneinfo\nzoneinfo.reset_tzpath(to=['etc'])\n", "banned-call"),
    ("import zoneinfo\nnames = zoneinfo.available_timezones()\n", "banned-call"),
    ("from zoneinfo import ZoneInfo\nz = ZoneInfo.from_file(None)\n", "banned-call"),
    ("import typing\nhints = typing.get_type_hints(len)\n", "banned-attribute"),
    ("from typing import get_type_hints\n", "banned-attribute"),
    ("import typing\nref = typing.ForwardRef('x')\n", "banned-attribute"),
    # Python 3.14: `dataclasses` re-exports `annotationlib`, and `typing.evaluate_forward_ref` is new; both evaluate.
    ("from dataclasses import annotationlib\n", "banned-attribute"),
    (
        "from dataclasses import annotationlib\ndef f(x: '1 + 1'):\n    return x\n"
        "v = annotationlib.get_annotations(f, eval_str=True)\n",
        "banned-attribute",
    ),
    ("import dataclasses\nv = dataclasses.annotationlib.call_evaluate_function(len, 1)\n", "banned-attribute"),
    ("import typing\nv = typing.evaluate_forward_ref\n", "banned-attribute"),
    ("from typing import evaluate_forward_ref\n", "banned-attribute"),
    ("import typing\nbuild = typing.types.CodeType\n", "banned-attribute"),
    ("import operator\ngetter = operator.attrgetter('real')\n", "banned-attribute"),
    ("from operator import methodcaller\n", "banned-attribute"),
    ("import enum\nb = enum.bltns\n", "banned-attribute"),
    ("import enum\nmark = enum.global_enum\n", "banned-attribute"),
    ("import dataclasses\nsource = dataclasses.inspect\n", "banned-attribute"),
    ("import dataclasses\nbuilder = dataclasses._FuncBuilder\n", "banned-attribute"),
    ("from dataclasses import _FuncBuilder\n", "banned-attribute"),
    ("import calendar\nc = calendar._locale\n", "banned-attribute"),
    ("import scipy.fft\nb = scipy.fft._backend\n", "banned-attribute"),
    # calendar's locale classes set the process locale, which the `locale` ban keeps out.
    ("import calendar\ncal = calendar.LocaleTextCalendar(locale='de_DE')\n", "banned-attribute"),
    ("from calendar import LocaleHTMLCalendar\n", "banned-attribute"),
    (
        "import calendar\nwith calendar.different_locale('de_DE'):\n    names = list(calendar.month_abbr)\n",
        "banned-attribute",
    ),
    ("import calendar\ncalendar.main(['cal', '-L', 'de_DE', '-e', 'utf-8'])\n", "banned-attribute"),
    ("import calendar as cal\nrun = cal.main\n", "banned-attribute"),
    ("from calendar import main\n", "banned-attribute"),
    ("from calendar import main as show_month\n", "banned-attribute"),
    ("import calendar.main\n", "banned-import"),
    # A private or escape component of an import path, which an alias would hide from the attribute check.
    ("import scipy.fft._backend as backend\nbackend.set_global_backend('scipy')\n", "banned-import"),
    ("from scipy.fft._pocketfft import r2c\n", "banned-import"),
    ("import scipy.linalg._decomp\n", "banned-import"),
    ("import collections.sys as s\n", "banned-import"),
    # A module laundered through an expression the resolver cannot follow (second review round).
    ("import calendar\nc = [calendar][0]\nc._locale.setlocale(0, 'de_DE')\n", "module-value"),
    ("import calendar\nc = [calendar][0]\nc._locale.setlocale(0, 'de_DE')\n", "banned-attribute"),
    ("import dataclasses\nd = [dataclasses][0]\nb = d._FuncBuilder\n", "module-value"),
    ("import dataclasses\nd = [dataclasses][0]\nb = d._FuncBuilder\n", "banned-attribute"),
    ("import collections as c\nm = (lambda module: module)(c)\n", "module-value"),
    ("import statistics\ns = statistics\n", "module-value"),
    ("m = [np.lib][0]\nf = m._datasource.open('x')\n", "banned-attribute"),
    ("import statistics\nr = [statistics.mean][0].__globals__\n", "dunder"),
    ("import zoneinfo\nz = [zoneinfo.ZoneInfo][0]\np = z._tzpath\n", "banned-attribute"),
    ("import warnings\nw = [warnings.warn][0]\ng = w._getcategory\n", "banned-attribute"),
    ("from statistics import mean\nr = [mean][0]._random\n", "banned-attribute"),
    # Routes the walk found in modules allowed before (2026-10-10): they passed the validator then.
    ('import collections\nx = collections._sys.modules["builtins"].exec("y = 1")\n', "banned-attribute"),
    ('import statistics\nx = statistics.sys.modules["os"].system("true")\n', "banned-attribute"),
    ("import matplotlib\nrun = matplotlib.subprocess\n", "banned-attribute"),
    ("import matplotlib\nm = matplotlib.os\n", "banned-attribute"),
    ("import warnings\nw = warnings.sys\n", "banned-attribute"),
    # Frame and generator introspection (security review of 2026-10-14): each name alone is refused.
    ("g = (i for i in range(1))\nframe = g.gi_frame\n", "banned-attribute"),
    ("g = (i for i in range(1))\ncode = g.gi_code\n", "banned-attribute"),
    ("names = frame.f_builtins\n", "banned-attribute"),
    ("names = frame.f_globals\n", "banned-attribute"),
    ("caller = frame.f_back\n", "banned-attribute"),
    ("names = frame.f_locals\n", "banned-attribute"),
    ("frame = error.tb_frame\n", "banned-attribute"),
    ("frame = coroutine.cr_frame\n", "banned-attribute"),
    ("values = code.co_consts\n", "banned-attribute"),
    # Native code and raw memory through a value (second opinion of 2026-10-14): these passed before.
    ('lib = np.zeros(1).ctypes._ctypes.CDLL(None)\nlib.system(b"id")\n', "banned-attribute"),
    (
        "state = np.random.default_rng(0).bit_generator.ctypes.state\nx = type(state).from_address(0)\n",
        "banned-attribute",
    ),
    ("ptr = np.zeros(1).ctypes.data_as(None)\n", "banned-attribute"),
    ("view = np.lib.stride_tricks.as_strided(np.zeros(1), shape=(10**6,))\n", "banned-attribute"),
    ('np.zeros(3).dump("f")\n', "banned-attribute"),
    ("compile_c = np.testing.extbuild\n", "banned-attribute"),
    ('import statsmodels.api as sm\nd = sm.datasets.get_rdataset("x")\n', "banned-attribute"),
    ('import statsmodels.api as sm\nd = sm.datasets.webuse("x")\n', "banned-attribute"),
    ('df.to_string("f")\n', "banned-call"),
    ('df.to_string(buf="f")\n', "banned-call"),
    ('df.info(True, "f")\n', "banned-call"),
    ('df.info(buf="f")\n', "banned-call"),
    ("df.info(**{})\n", "banned-call"),
    ("args = []\ndf.to_string(*args)\n", "banned-call"),
    # The method bound to a name would hide the target from the call check (#12167 review).
    ('writer = df.to_string\nwriter("f")\n', "banned-attribute"),
    ('writer = df.info\nwriter(buf="f")\n', "banned-attribute"),
    ('df.agg("to_string", buf="f")\n', "banned-call"),
    ('df.apply("info", buf="f")\n', "banned-call"),
]


class TestPureModules:
    """The owner's 2026-10-10 additions: allowed for computing, with the names that read, write or reflect banned."""

    @pytest.mark.parametrize("body", PURE_MODULE_USES)
    def test_allowed(self, body: str) -> None:
        assert security_rules(body) == set()

    @pytest.mark.parametrize(("body", "rule"), ESCAPES)
    def test_escape_is_caught(self, body: str, rule: str) -> None:
        assert rule in security_rules(body)

    @pytest.mark.parametrize(
        "name",
        [
            *("gi_frame", "gi_code", "gi_yieldfrom", "cr_frame", "cr_code", "cr_await", "cr_origin"),
            *("ag_frame", "ag_code", "ag_await", "f_back", "f_builtins", "f_globals", "f_locals"),
            *("f_code", "f_trace", "f_generator", "tb_frame", "tb_next", "co_code", "co_consts", "co_names"),
        ],
    )
    def test_every_introspection_attribute_is_refused(self, name: str) -> None:
        """Each spelling of the 2026-10-14 frame and generator denylist, so a typo cannot reopen one."""
        assert "banned-attribute" in security_rules(f"value = thing.{name}\n")

    def test_a_private_module_in_an_import_path_is_named_and_logged_by_its_known_prefix(self) -> None:
        findings = validate_security(plot("import scipy.fft._backend as backend\n"), library="matplotlib")

        banned = [finding for finding in findings if finding.rule == "banned-import"]
        assert [finding.module for finding in banned] == ["scipy.fft"]
        assert "reaches the private module '_backend'" in banned[0].message

    @pytest.mark.parametrize(
        "body",
        [
            "import locale\n",
            "import random\n",
            "import sys\n",
            "import pathlib\n",
            "import string\n",
            "import io\n",
            "from os import path\n",
            "from sklearn.datasets import make_blobs\n",
            "import scipy.io\n",
            "import scipy.datasets\n",
            "import statsmodels.formula.api\n",
        ],
    )
    def test_still_banned(self, body: str) -> None:
        assert "banned-import" in security_rules(body)


# --- os ---------------------------------------------------------------------------------


class TestOsUse:
    @pytest.mark.parametrize(
        "body",
        [
            "T = os.getenv('ANYPLOT_THEME', 'light')\n",
            "T = os.getenv('ANYPLOT_THEME')\n",
            "T = os.getenv('ANYPLOT_THEME', default='light')\n",
            "T = os.environ.get('ANYPLOT_THEME', 'light')\n",
            "import os as _os\nT = _os.getenv('ANYPLOT_THEME', 'light')\n",
        ],
    )
    def test_theme_lookup_allowed(self, body: str) -> None:
        assert security_rules(body) == set()

    @pytest.mark.parametrize(
        "body",
        [
            "T = os.getenv('HOME')\n",
            "T = os.environ.get('HOME')\n",
            "T = os.environ['ANYPLOT_THEME']\n",
            "KEY = 'ANYPLOT_THEME'\nT = os.getenv(KEY, 'light')\n",
            "T = os.getenv('ANYPLOT_THEME', 'light', 'extra')\n",
            "T = os.getenv('ANYPLOT_THEME', key='light')\n",
            "T = os.getenv('ANYPLOT_THEME', 'light', default='dark')\n",
            "T = os.environ.get('ANYPLOT_THEME', 'light', default='dark')\n",
            "p = os.path.join('a', 'b')\n",
            "os.system('ls')\n",
            "o = os\n",
            "import os as _os\nd = _os.getcwd()\n",
            "f = os.getenv\n",
        ],
    )
    def test_other_os_use_is_a_finding(self, body: str) -> None:
        assert "os-use" in security_rules(body)

    def test_variable_named_os_without_the_import_is_not_os(self) -> None:
        """Neither `os-use` nor `module-value` sees the variable; the theme block read through the alias is no theme
        block (`regions.is_theme_assignment`), so its THEME is the one finding."""
        code = plot("os = np.ones(3)\ntotal = os.sum()\n").replace("import os\n", "import os as _o\n")
        code = code.replace(
            'THEME = os.getenv("ANYPLOT_THEME", "light")', 'THEME = _o.getenv("ANYPLOT_THEME", "light")'
        )
        findings = validate_security(code, library="matplotlib")
        assert [(f.rule, f.message, f.line) for f in findings] == [
            ("savefig-target", THEME_BINDING_MESSAGE, HEADER.splitlines().index(THEME_LINE) + 1)
        ]


# --- names, calls, attributes ---------------------------------------------------------------


BANNED_NAME_CALLS = [
    "eval('1')",
    "exec('x = 1')",
    "compile('1', 'f', 'eval')",
    "open('f')",
    "__import__('os')",
    "input()",
    "breakpoint()",
    "globals()",
    "locals()",
    "vars()",
    "getattr(ax, 'plot')",
    "setattr(ax, 'x', 1)",
    "delattr(ax, 'x')",
    "memoryview(b'')",
    "exit()",
    "quit()",
]


class TestBannedNames:
    @pytest.mark.parametrize("call", BANNED_NAME_CALLS)
    def test_banned_builtin(self, call: str) -> None:
        assert "banned-name" in security_rules(f"x = {call}\n")

    @pytest.mark.parametrize("body", ["x = len(df)\n", "ok = hasattr(ax, 'plot')\n", "t = type(df)\n", "print(df)\n"])
    def test_allowed_builtin(self, body: str) -> None:
        assert security_rules(body) == set()

    def test_shadowing_a_banned_name_is_a_finding(self) -> None:
        assert security_rules("open = 1\n") == {"banned-name"}
        assert security_rules("def f(open):\n    return open\n") == {"banned-name"}

    @pytest.mark.parametrize("call", ["type('C', (object,), {})", "type(*parts)", "type(name, bases, ns)"])
    def test_type_with_more_than_one_argument(self, call: str) -> None:
        assert "banned-call" in security_rules(f"parts = ()\nname = bases = ns = None\nC = {call}\n")


DUNDER_BODIES = [
    "c = df.__class__\n",
    "b = __builtins__\n",
    "x = plt.plot([1], __x__=1)\n",
    "def __f__():\n    return 1\n",
    "def f(__a__):\n    return __a__\n",
    "s = '__class__'\n",
    "s = 'see __subclasses__ here'\n",
    "s = f'{THEME}__dict__'\n",
    "s = b'__class__'\n",
    "if __name__ == '__main__':\n    pass\n",
    "p = __file__\n",
]


class TestDunders:
    @pytest.mark.parametrize("body", DUNDER_BODIES)
    def test_dunder_is_a_finding(self, body: str) -> None:
        assert "dunder" in security_rules(body)

    @pytest.mark.parametrize("body", ["_private = 1\n", "s = '__init'\n", "s = 'a_b__c'\n", "x = df._mgr\n"])
    def test_single_underscores_and_half_dunders_pass(self, body: str) -> None:
        assert security_rules(body) == set()


BANNED_ATTRIBUTE_BODIES = [
    "s = '{}'.format(THEME)\n",
    "s = 'x'.format_map({})\n",
    "v = pd.eval('1 + 1')\n",
    "v = df.eval('a + 1')\n",
    "v = df.query('a > 1')\n",
    "x = df\nv = x.eval('a')\n",
    "m = np.memmap('f', dtype='f4')\n",
    "c = np.ctypeslib\n",
    "c = np.f2py\n",
    "import matplotlib\nmatplotlib.use('Agg')\n",
    "plt.style.use('ggplot')\n",
    "plt.show()\n",
    "fig.show()\n",
    "h = pd.io.common.get_handle('f', 'r')\n",
]
ALLOWED_ATTRIBUTE_BODIES = [
    "s = 'x'.upper()\n",
    "v = df.loc[df['a'] > 1]\n",
    "v = df[df['a'] > 1]\n",
    "v = df.assign(b=1)\n",
    "ax.set_title('x')\n",
    "f = ax.xaxis.set_major_formatter\n",
]
BANNED_IO_BODIES = [
    "d = pd.read_csv('x.csv')\n",
    "d = pd.read_json('x.json')\n",
    "d = pd.read_pickle('x.pkl')\n",
    "x = pd.ExcelFile('x.xlsx')\n",
    "x = pd.ExcelWriter('x.xlsx')\n",
    "x = pd.HDFStore('x.h5')\n",
    *[f"df.{writer}('out')\n" for writer in ("to_csv", "to_pickle", "to_parquet", "to_excel", "to_sql", "to_hdf")],
    *[f"df.{writer}()\n" for writer in ("to_feather", "to_json", "to_html", "to_clipboard")],
    *[f"df.{writer}('out')\n" for writer in ("to_latex", "to_markdown", "to_xml", "to_stata", "to_orc")],
    "m = fmt.open_memmap('x.npy', mode='r')\n",
    "plt.imsave('x.png', np.zeros((2, 2)))\n",
    "import matplotlib.cbook as cbook\nf = cbook.to_filehandle('x')\n",
    "import matplotlib.cbook as cbook\nf = cbook.open_file_cm('x')\n",
    "import matplotlib as mpl\nr = mpl.rc_params_from_file('x')\n",
    "a = np.load('x.npy')\n",
    "a = np.loadtxt('x.txt')\n",
    "a = np.genfromtxt('x.txt')\n",
    "np.save('x.npy', df)\n",
    "np.savez('x.npz', a=df)\n",
    "np.savez_compressed('x.npz', a=df)\n",
    "np.savetxt('x.txt', df)\n",
    "a = np.fromfile('x.bin')\n",
    "a = np.fromregex('x.txt', r'\\d', np.int64)\n",
    "a = np.DataSource()\n",
    "df.values.tofile('x.bin')\n",
    "img = plt.imread('x.png')\n",
    "import matplotlib.image\nimg = matplotlib.image.imread('x.png')\n",
    "import matplotlib.cbook\nf = matplotlib.cbook.get_sample_data('x')\n",
    "import matplotlib as mpl\nmpl.rc_file('x')\n",
    "import seaborn as sns\nd = sns.load_dataset('tips')\n",
    "from sklearn.datasets import fetch_openml\nd = fetch_openml('x')\n",
    "d = datasets.fetch_openml('x')\n",
    "from urllib.request import urlopen\nr = urlopen('x')\n",
    "import urllib.request\nr = urllib.request.urlopen('x')\n",
    "f = pd.read_csv\n",
    "r = df.read_count\n",
    "df.agg('to_csv')\n",
    "df.agg(['mean', 'to_csv'])\n",
    "df.agg({'a': 'to_csv'})\n",
    "df.apply('eval')\n",
    "df.transform(func='load')\n",
    "df['a'].aggregate('to_pickle')\n",
]
ALLOWED_IO_SIBLINGS = [
    "d = pd.to_datetime(df['a'])\n",
    "v = df.to_numpy()\n",
    "v = df.to_dict()\n",
    "v = df.to_string()\n",
    "v = df.to_string(buf=None, index=False)\n",
    "df.info(False)\n",
    "df.info(verbose=True, buf=None)\n",
    "r = df['read_count']\n",
    "r = df['load']\n",
    "v = df.agg('mean')\n",
    "v = df.apply(np.mean)\n",
    "v = df.transform('sum')\n",
    "import matplotlib as mpl\nmpl.rc_file_defaults()\n",
    "ax.imshow(np.zeros((2, 2)))\n",
    "plt.savefig(f'plot-{THEME}.png')\n",
]


class TestAttributesAndCalls:
    @pytest.mark.parametrize("body", BANNED_ATTRIBUTE_BODIES)
    def test_banned_attribute(self, body: str) -> None:
        assert "banned-attribute" in security_rules(body)

    @pytest.mark.parametrize("body", ALLOWED_ATTRIBUTE_BODIES)
    def test_allowed_attribute(self, body: str) -> None:
        assert security_rules(body) == set()

    @pytest.mark.parametrize("body", BANNED_IO_BODIES)
    def test_banned_io(self, body: str) -> None:
        assert "banned-call" in security_rules(body)

    @pytest.mark.parametrize("body", ALLOWED_IO_SIBLINGS)
    def test_allowed_io_sibling(self, body: str) -> None:
        assert security_rules(body) == set()

    def test_column_hint_only_for_attribute_access_on_a_non_module(self) -> None:
        on_frame = validate_security(plot("r = df.read_count\n"), library="matplotlib")
        assert "subscripted" in on_frame[0].message
        on_module = validate_security(plot("r = pd.read_csv('x')\n"), library="matplotlib")
        assert "subscripted" not in on_module[0].message

    def test_snippet_never_echoes_a_receiver_literal(self) -> None:
        findings = validate_security(plot("r = df['secret_col'].read_count\n"), library="matplotlib")
        assert [f.rule for f in findings] == ["banned-call"]
        assert "secret" not in findings[0].message and "(...).read_count" in findings[0].message


# --- statements, strings ----------------------------------------------------------------------


class TestStatements:
    @pytest.mark.parametrize(
        "body",
        [
            "class A:\n    pass\n",
            "async def f():\n    return 1\n",
            "async def f():\n    await g()\n",
            "def g():\n    yield 1\n",
            "def g():\n    yield from range(3)\n",
            "def g():\n    global THEME\n",
            "def g():\n    x = 1\n    def h():\n        nonlocal x\n    return h\n",
            "async def f():\n    async for i in g():\n        pass\n",
            "async def f():\n    async with g():\n        pass\n",
            "async def f():\n    return [i async for i in g()]\n",
        ],
    )
    def test_banned_statement(self, body: str) -> None:
        assert "banned-statement" in security_rules(body)

    @pytest.mark.parametrize(
        "body",
        [
            "def fmt(value, pos):\n    return f'{value:.0f}'\n",
            "fmt = lambda value, pos: f'{value:.0f}'\n",
            "for i in range(3):\n    pass\n",
            "try:\n    x = 1\nexcept ValueError:\n    x = 2\n",
            "with plt.rc_context({'font.size': 8}):\n    pass\n",
        ],
    )
    def test_functions_and_control_flow_allowed(self, body: str) -> None:
        assert security_rules(body) == set()


class TestStrings:
    @pytest.mark.parametrize(
        "literal",
        [
            "'https://example.com/x'",
            "'http://example.com'",
            "'ftp://example.com'",
            "'file:///etc/passwd'",
            "'data:image/png;base64,AAAA'",
            "'DATA:text/plain,x'",
            "'see HTTPS://x.y'",
            "f'https://{THEME}/x'",
            "b'http://x'",
        ],
    )
    def test_url_literal(self, literal: str) -> None:
        assert "url-literal" in security_rules(f"s = {literal}\n")

    @pytest.mark.parametrize(
        "literal",
        [
            "'Source data: 2024 survey'",
            "'profile: terrain'",
            "'httpx'",
            "'www.example.com'",
            "'data:'",
            "'Data: n = 3'",
        ],
    )
    def test_prose_with_a_colon_passes(self, literal: str) -> None:
        assert security_rules(f"s = {literal}\n") == set()

    def test_string_length(self) -> None:
        assert security_rules(f"s = '{'x' * MAX_STRING_CHARS}'\n") == set()
        assert security_rules(f"s = '{'x' * (MAX_STRING_CHARS + 1)}'\n") == {"string-length"}

    def test_implicit_concatenation_counts_as_one_literal(self) -> None:
        half = "x" * (MAX_STRING_CHARS // 2 + 1)
        assert security_rules(f"s = '{half}' '{half}'\n") == {"string-length"}
        assert security_rules(f"s = '{half}' + '{half}'\n") == set()

    def test_string_contents_are_never_echoed(self) -> None:
        findings = validate_security(plot("s = 'https://secret.example/__class__'\n"), library="matplotlib")
        assert findings and all("secret" not in f.message for f in findings)


# --- savefig -----------------------------------------------------------------------------------


class TestSavefig:
    @pytest.mark.parametrize(
        "save",
        [
            'plt.savefig(f"plot-{THEME}.png", dpi=400)',
            "plt.savefig(f'plot-{THEME}.png')",
            'fig.savefig(f"plot-{THEME}.png", facecolor="#fff")',
            'plt.savefig(fname=f"plot-{THEME}.png")',
        ],
    )
    def test_exact_target_passes(self, save: str) -> None:
        code = plot().replace('plt.savefig(f"plot-{THEME}.png", dpi=400)', save)
        assert validate_security(code, library="matplotlib") == []

    @pytest.mark.parametrize(
        "save",
        [
            'plt.savefig("plot.png")',
            'plt.savefig("plot-light.png")',
            "plt.savefig(path)",
            'plt.savefig(f"plot-{THEME!s}.png")',
            'plt.savefig(f"plot-{THEME:>5}.png")',
            'plt.savefig("plot-" + THEME + ".png")',
            'plt.savefig(f"plot-{theme}.png")',
            'plt.savefig(f"plot-{THEME}.svg")',
            'plt.savefig(f"out/plot-{THEME}.png")',
            "plt.savefig()",
            'plt.savefig(dpi=400, fname="plot.png")',
        ],
    )
    def test_other_target_is_a_finding(self, save: str) -> None:
        code = plot("path = theme = 'x'\n").replace('plt.savefig(f"plot-{THEME}.png", dpi=400)', save)
        assert {f.rule for f in validate_security(code, library="matplotlib")} == {"savefig-target"}

    def test_missing_savefig(self) -> None:
        code = plot().replace('plt.savefig(f"plot-{THEME}.png", dpi=400)', "")
        findings = validate_security(code, library="matplotlib")
        assert [(f.rule, f.line) for f in findings] == [("savefig-target", None)]

    def test_every_savefig_is_checked(self) -> None:
        assert security_rules('plt.savefig("extra.png")\n') == {"savefig-target"}


# --- the design doc's named bypasses --------------------------------------------------------


BYPASSES = [
    pytest.param("b = '__builtins__'\n", {"dunder"}, id="__builtins__ via string"),
    pytest.param("c = getattr(df, '__' + 'class__')\n", {"banned-name"}, id="getattr with a split dunder"),
    pytest.param("import string\nf = string.Formatter()\n", {"banned-import"}, id="string.Formatter"),
    pytest.param("s = '{0.__class__}'.format(df)\n", {"banned-attribute", "dunder"}, id="format with a dunder path"),
    pytest.param("import patsy\n", {"banned-import"}, id="patsy"),
    pytest.param("import statsmodels.formula.api as smf\n", {"banned-import"}, id="statsmodels.formula"),
    pytest.param("v = pd.eval('1')\n", {"banned-attribute"}, id="pd.eval"),
    pytest.param("v = df.query('a > 1')\n", {"banned-attribute"}, id="df.query"),
    pytest.param("a = np.load('x.npy')\n", {"banned-call"}, id="np.load"),
    pytest.param("f = open('/etc/passwd')\n", {"banned-name"}, id="open"),
    pytest.param("m = __import__('os')\n", {"banned-name", "dunder"}, id="__import__"),
    pytest.param("C = type('C', (object,), {})\n", {"banned-call"}, id="three-argument type()"),
    pytest.param("import importlib\nm = importlib.import_module('os')\n", {"banned-import"}, id="importlib"),
    pytest.param("import subprocess\nsubprocess.run(['ls'])\n", {"banned-import"}, id="subprocess"),
    pytest.param("u = 'data:text/plain;base64,AAAA'\n", {"url-literal"}, id="data: URL"),
    pytest.param("u = 'file:///etc/passwd'\n", {"url-literal"}, id="file: URL"),
    pytest.param("import sys\nm = sys.modules['os']\n", {"banned-import"}, id="sys.modules"),
    pytest.param("f = pd.read_csv\nd = f('x.csv')\n", {"banned-call"}, id="reader bound to a name"),
    pytest.param("df.agg('to_csv', 'out.csv')\n", {"banned-call"}, id="method name as a string"),
    pytest.param("x = df\nv = x.eval('a')\n", {"banned-attribute"}, id="frame.eval via a variable"),
    pytest.param("s = df.__class__.__subclasses__()\n", {"dunder"}, id="subclasses walk"),
    pytest.param("import os.path\n", {"banned-import"}, id="os.path import"),
    pytest.param(
        "import pandas.io.common as common\nh = common.get_handle('/etc/passwd', 'r')\n",
        {"banned-import"},
        id="pandas.io behind an alias",
    ),
    pytest.param(
        "import numpy.lib.format as fmt\nm = fmt.open_memmap('x.npy')\n",
        {"banned-import", "banned-call"},
        id="open_memmap behind an alias",
    ),
]


class TestBypasses:
    @pytest.mark.parametrize(("body", "expected"), BYPASSES)
    def test_bypass_is_caught(self, body: str, expected: set[str]) -> None:
        assert expected <= security_rules(body)


# --- ADAPTATION ----------------------------------------------------------------------------


class TestPlaceholder:
    def test_exactly_one(self) -> None:
        assert adaptation_rules("") == set()

    def test_zero(self) -> None:
        findings = validate_adaptation("import pandas as pd\n", original_palette=[])
        assert [(f.rule, f.message, f.line) for f in findings] == [
            ("placeholder-count", f"expected exactly one '{PLACEHOLDER}' statement, found 0", None)
        ]

    def test_two(self) -> None:
        findings = validate_adaptation(ADAPTED + "df = load_user_data()\n", original_palette=[])
        assert [f.rule for f in findings] == ["placeholder-count"]
        assert "found 2" in findings[0].message

    @pytest.mark.parametrize(
        "body",
        [
            "x = load_user_data()\n",
            "df = load_user_data('x.csv')\n",
            "f = load_user_data\n",
            "df2 = df = load_user_data()\n",
        ],
    )
    def test_other_uses_of_the_loader(self, body: str) -> None:
        findings = validate_adaptation("import pandas as pd\n" + body, original_palette=[])
        assert {f.rule for f in findings} == {"placeholder-count", "placeholder-use"}


class TestRng:
    @pytest.mark.parametrize(
        "body",
        [
            "import numpy as np\nrng = np.random.default_rng(42)\nidx = rng.choice(len(df), 50, replace=False)\n",
            "import numpy as np\nrng = np.random.default_rng(seed=7)\norder = rng.permutation(len(df))\n",
            "import numpy as np\nrng = np.random.default_rng(0)\njitter = rng.uniform(-0.1, 0.1, len(df))\n",
            "import numpy as np\njitter = np.random.default_rng(7).uniform(-0.1, 0.1, len(df))\n",
            "from numpy.random import default_rng\nrng = default_rng(1)\nj = rng.uniform(0, 1, 3)\n",
            "import numpy as np\nrng: object = np.random.default_rng(1)\nj = rng.uniform(0, 1, 3)\n",
            "s = df.sample(frac=0.1, random_state=0)\n",
        ],
    )
    def test_seeded_generator_for_jitter_and_subsampling(self, body: str) -> None:
        assert adaptation_rules(body) == set()

    @pytest.mark.parametrize(
        "body",
        [
            "import numpy as np\nnp.random.seed(0)\n",
            "import numpy as np\nx = np.random.randn(10)\n",
            "import numpy as np\nx = np.random.normal(size=10)\n",
            "import numpy as np\nx = np.random.RandomState(0).rand(3)\n",
            "import random\nx = random.random()\n",
            "import random\nx = random.gauss(0, 1)\n",
            "from numpy import random as npr\nx = npr.normal(size=3)\n",
            "from numpy import random\nx = random.normal(size=3)\n",
            "import numpy as np\nrs = np.random\nx = rs.normal(size=3)\n",
            "import numpy as np\nrng = np.random.default_rng()\nx = rng.uniform(0, 1, 3)\n",
            "import numpy as np\nrng = np.random.default_rng(seed=None)\n",
            "import numpy as np\nSEED = 1\nrng = np.random.default_rng(SEED)\n",
            "import numpy as np\nrng = np.random.default_rng(True)\n",
            "import numpy as np\nrng = np.random.default_rng(1)\nx = rng.normal(0, 1, 10)\n",
            "import numpy as np\nrng = np.random.default_rng(1)\nx = rng.integers(0, 9, 10)\n",
            "import numpy as np\nrng = np.random.default_rng(1)\nx = rng.standard_normal(10)\n",
            "import numpy as np\nrng = np.random.default_rng(1)\ng = rng\n",
            "import numpy as np\nrng = np.random.default_rng(1)\nx = helper(rng)\n",
            "import numpy as np\nrng = np.random.default_rng(1)\nrng = 3\n",
            "import numpy as np\nrng = np.random.default_rng(1)\ndef f(rng):\n    return rng.uniform(0, 1)\n",
            "import numpy as np\nx = np.random.default_rng(1).normal(0, 1, 3)\n",
            "import numpy as np\npair = (np.random.default_rng(1), 2)\n",
            "import numpy as np\nrng = np.random.default_rng(1)\nm = rng.uniform\n",
            "from scipy import stats\nx = stats.norm.rvs(size=10)\n",
            "from scipy import stats\nx = stats.norm(0, 1).rvs(5)\n",
        ],
    )
    def test_random_data_is_a_finding(self, body: str) -> None:
        assert "rng" in adaptation_rules(body)

    def test_rng_message_names_the_offending_use(self) -> None:
        body = "import numpy as np\nrng = np.random.default_rng(1)\nx = rng.normal(0, 1, 10)\n"
        findings = validate_adaptation(ADAPTED + body, original_palette=ORIGINAL)
        assert [(f.rule, f.line) for f in findings] == [("rng", 6)]
        assert "rng.choice/.permutation/.uniform" in findings[0].message


class TestLiteralData:
    def test_twenty_numbers_pass(self) -> None:
        values = ", ".join(str(i) for i in range(MAX_LITERAL_NUMBERS))
        assert adaptation_rules(f"x = [{values}]\n") == set()

    @pytest.mark.parametrize(
        "literal",
        [
            "[" + ", ".join(str(i) for i in range(21)) + "]",
            "(" + ", ".join(str(i) for i in range(21)) + ")",
            "{" + ", ".join(str(i) for i in range(21)) + "}",
            "[" + ", ".join(f"{i}.5" for i in range(21)) + "]",
            "[" + ", ".join(f"-{i}" for i in range(21)) + "]",
            "[[1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7]]",
            "[(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16), (17, 18), (19, 20), (21, 22)]",
            "np.array([" + ", ".join(str(i) for i in range(21)) + "])",
            "['a', " + ", ".join(str(i) for i in range(21)) + "]",
        ],
    )
    def test_more_than_twenty_numbers(self, literal: str) -> None:
        findings = validate_adaptation(ADAPTED + f"import numpy as np\nx = {literal}\n", original_palette=ORIGINAL)
        assert [f.rule for f in findings] == ["literal-data"]
        assert "numeric values" in findings[0].message

    @pytest.mark.parametrize(
        "literal",
        [
            "[" + ", ".join(f"'c{i}'" for i in range(30)) + "]",
            "[" + ", ".join("True" for _ in range(30)) + "]",
            "list(range(100))",
            "np.linspace(0, 1, 500)",
        ],
    )
    def test_non_numeric_or_computed_sequences_pass(self, literal: str) -> None:
        assert adaptation_rules(f"import numpy as np\nx = {literal}\n") == set()


class TestPalette:
    @pytest.mark.parametrize(
        "body",
        [
            'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]\n',
            'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]\n',
            'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]\n',
            'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#bd8233"]\n',
            'IMPRINT = ("#009E73", "#C475FD", "#4467A3")\n',
            'IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]\n',
            'IMPRINT: list[str] = ["#009E73", "#C475FD", "#4467A3"]\n',
            "",
        ],
    )
    def test_prefix_kept_or_extended_with_the_next_positions(self, body: str) -> None:
        assert adaptation_rules(body) == set()

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param('IMPRINT = ["#C475FD", "#009E73", "#4467A3"]\n', id="reordered"),
            pytest.param('IMPRINT = ["#009E73", "#C475FD"]\n', id="truncated"),
            pytest.param('IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#AE3030"]\n', id="skips a position"),
            pytest.param('IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#FF0000"]\n', id="foreign colour"),
            pytest.param('IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#2ABCCD"]\n', id="out of order"),
            pytest.param("IMPRINT = [" + ", ".join(f'"{c}"' for c in IMPRINT) + ', "#000000"]\n', id="beyond 8"),
            pytest.param("IMPRINT = sns.color_palette()\n", id="not a literal"),
            pytest.param('IMPRINT = ["#009E73", BRAND, "#4467A3"]\n', id="non-literal entry"),
            pytest.param("IMPRINT = []\n", id="emptied"),
            pytest.param('IMPRINT_PALETTE = ["#009E73", "#C475FD"]\n', id="IMPRINT_PALETTE truncated"),
            pytest.param(
                'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]\nIMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]\n',
                id="assigned twice, both valid",
            ),
            pytest.param(
                'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]\nIMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3"]\n',
                id="both names assigned",
            ),
        ],
    )
    def test_prefix_broken(self, body: str) -> None:
        assert adaptation_rules("import seaborn as sns\nBRAND = '#009E73'\n" + body) == {"palette-prefix"}

    def test_original_without_a_palette_list(self) -> None:
        assert adaptation_rules('IMPRINT = ["#009E73", "#C475FD"]\n', original=[]) == set()
        assert adaptation_rules('IMPRINT = ["#C475FD"]\n', original=[]) == {"palette-prefix"}

    def test_non_canonical_original_extends_with_unused_positions(self) -> None:
        original = ["#009E73", "#AE3030"]
        assert adaptation_rules('IMPRINT = ["#009E73", "#AE3030", "#C475FD"]\n', original=original) == set()
        assert adaptation_rules('IMPRINT = ["#009E73", "#AE3030", "#4467A3"]\n', original=original) == {
            "palette-prefix"
        }

    def test_message_names_the_next_position(self) -> None:
        findings = validate_adaptation(
            ADAPTED + 'IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#AE3030"]\n', original_palette=ORIGINAL
        )
        assert "#BD8233" in findings[0].message

    def test_second_assignment_is_named_and_the_first_still_checked(self) -> None:
        body = 'IMPRINT = ["#C475FD", "#009E73", "#4467A3"]\nIMPRINT = ["#009E73", "#C475FD", "#4467A3"]\n'

        findings = validate_adaptation(ADAPTED + body, original_palette=ORIGINAL)

        assert [f.message for f in findings] == [
            "IMPRINT must keep the 3 original palette entries in order",
            "IMPRINT is assigned again; keep one literal palette list",
        ]

    def test_message_names_the_limit_when_the_list_outgrows_the_palette(self) -> None:
        body = "IMPRINT = [" + ", ".join(f'"{c}"' for c in [*IMPRINT, IMPRINT[0]]) + "]\n"

        findings = validate_adaptation(ADAPTED + body, original_palette=ORIGINAL)

        assert [f.message for f in findings] == ["IMPRINT has 9 entries, more than the 8 colours the palette has"]

    def test_the_muted_other_group_of_the_adapter_prompt_passes(self) -> None:
        """More than eight groups: seven palette colours and INK_MUTED for "Other", as adapter.md asks."""
        body = (
            "IMPRINT = [" + ", ".join(f'"{c}"' for c in IMPRINT) + "]\n"
            'INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"\n'
            "colors = IMPRINT[:7] + [INK_MUTED]\n"
        )
        assert adaptation_rules('import os\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n' + body) == set()

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param("IMPRINT.reverse()\n", id="reverse"),
            pytest.param("IMPRINT.sort()\n", id="sort"),
            pytest.param("IMPRINT.clear()\n", id="clear"),
            pytest.param("IMPRINT.pop()\n", id="pop"),
            pytest.param("IMPRINT.remove('#009E73')\n", id="remove"),
            pytest.param("IMPRINT.append('#BD8233')\n", id="append"),
            pytest.param("IMPRINT.extend(['#BD8233'])\n", id="extend"),
            pytest.param("IMPRINT.insert(0, '#BD8233')\n", id="insert"),
            pytest.param("flip = IMPRINT.reverse\nflip()\n", id="mutator bound to a name"),
            pytest.param("IMPRINT[0] = '#000000'\n", id="item assignment"),
            pytest.param("IMPRINT[:] = []\n", id="slice assignment"),
            pytest.param("IMPRINT[0] += 'x'\n", id="augmented item"),
            pytest.param("del IMPRINT[0]\n", id="item deletion"),
            pytest.param("IMPRINT += ['#BD8233']\n", id="augmented assignment"),
            pytest.param("del IMPRINT\n", id="deletion"),
            pytest.param("for IMPRINT in [[]]:\n    pass\n", id="loop target"),
            pytest.param("IMPRINT, extra = ['#009E73'], 1\n", id="unpacking target"),
            pytest.param("alias = IMPRINT = ['#009E73']\n", id="chained assignment"),
            pytest.param("colors = IMPRINT\ncolors.reverse()\n", id="mutator through an alias"),
            pytest.param("colors = IMPRINT\ncolors[0] = '#000000'\n", id="item write through an alias"),
            pytest.param("IMPRINT_PALETTE = IMPRINT\nIMPRINT_PALETTE.pop()\n", id="IMPRINT_PALETTE"),
        ],
    )
    def test_palette_changed_after_its_assignment(self, body: str) -> None:
        palette = 'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]\n'
        assert adaptation_rules(palette + body) == {"palette-prefix"}

    @pytest.mark.parametrize(
        "body",
        [
            "colors = IMPRINT[:2]\n",
            "colors = list(IMPRINT)\ncolors.reverse()\n",
            "colors = IMPRINT\nfirst = colors[0]\n",
            "ordered = sorted(IMPRINT)\n",
            "position = IMPRINT.index('#009E73')\n",
            "for colour in IMPRINT:\n    pass\n",
            "extended = IMPRINT + ['#BD8233']\n",
        ],
    )
    def test_reading_or_copying_the_palette_passes(self, body: str) -> None:
        palette = 'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]\n'
        assert adaptation_rules(palette + body) == set()

    def test_mutation_message_names_the_mutator(self) -> None:
        code = ADAPTED + 'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]\nIMPRINT.reverse()\n'
        findings = validate_adaptation(code, original_palette=ORIGINAL)
        assert [(f.rule, f.message, f.line) for f in findings] == [
            ("palette-prefix", "'IMPRINT.reverse' would change the palette", 5)
        ]


# --- exec, process and import-by-name routes through allowed modules (review of 2026-10-14) ----------------

MPL = "import matplotlib as mpl\n"
# Each route a survey of the allowed packages found, as the code a model would write; the reported
# case (`np.testing.measure` compiles and execs its string) generalised to every member of its kind.
EXEC_ROUTES = [
    # Fable review of #12181: trace, profile and monitoring callbacks get real frames, as an attribute on any receiver.
    pytest.param("t = df.settrace(None)\n", "banned-attribute", id="settrace on any receiver"),
    pytest.param("p = df.setprofile\n", "banned-attribute", id="setprofile on any receiver"),
    pytest.param("t = df.settrace_all_threads\n", "banned-attribute", id="settrace_all_threads"),
    pytest.param("m = df.monitoring.register_callback\n", "banned-attribute", id="sys.monitoring"),
    pytest.param("from numpy import setprofile\n", "banned-attribute", id="setprofile as a from import"),
    pytest.param('np.testing.measure("import os")\n', "banned-attribute", id="numpy.testing.measure execs a string"),
    pytest.param('np.testing.runstring("x = 1", {})\n', "banned-attribute", id="numpy.testing.runstring"),
    pytest.param("with np.testing.tempdir() as d:\n    pass\n", "banned-attribute", id="numpy.testing.tempdir"),
    pytest.param("pd.testing.assert_frame_equal(df, df)\n", "banned-attribute", id="pandas.testing"),
    pytest.param("import numpy.testing as npt\n", "banned-import", id="import numpy.testing"),
    pytest.param("from numpy.testing import measure\n", "banned-import", id="from numpy.testing import"),
    pytest.param("from numpy import testing\n", "banned-attribute", id="from numpy import testing"),
    pytest.param("from pandas import testing\n", "banned-attribute", id="from pandas import testing"),
    pytest.param("np.ma.testutils.assert_equal(1, 1)\n", "banned-attribute", id="numpy.ma.testutils"),
    pytest.param('np.lib.add_newdoc("os", "system", "")\n', "banned-attribute", id="add_newdoc imports by name"),
    pytest.param("np.test()\n", "banned-attribute", id="numpy test runs pytest"),
    pytest.param("pd.test()\n", "banned-attribute", id="pandas test runs pytest"),
    pytest.param(MPL + "mpl.test()\n", "banned-attribute", id="matplotlib test runs pytest"),
    pytest.param("import matplotlib.testing.compare as c\n", "banned-import", id="matplotlib.testing"),
    pytest.param("import matplotlib.animation as animation\n", "banned-import", id="animation starts ffmpeg"),
    pytest.param("from matplotlib.animation import FuncAnimation\n", "banned-import", id="from animation import"),
    pytest.param("from matplotlib import animation\n", "banned-attribute", id="from matplotlib import animation"),
    pytest.param("import matplotlib.backends.backend_pgf\n", "banned-import", id="backend_pgf starts LaTeX"),
    pytest.param("from matplotlib.backends.backend_pdf import PdfPages\n", "banned-import", id="PdfPages"),
    pytest.param("from matplotlib.texmanager import TexManager\n", "banned-import", id="texmanager"),
    pytest.param("from matplotlib.backend_bases import register_backend\n", "banned-import", id="register_backend"),
    pytest.param("import matplotlib.pylab as pylab\n", "banned-import", id="pylab"),
    pytest.param('plt.switch_backend("module://x")\n', "banned-attribute", id="switch_backend imports by name"),
    pytest.param('fig.canvas.print_figure("x.png")\n', "banned-attribute", id="canvas print_figure"),
    pytest.param('fig.canvas.print_eps("x.eps")\n', "banned-attribute", id="canvas print_eps"),
    pytest.param(MPL + 'mpl.mathtext.math_to_image("$x$", "x.png")\n', "banned-attribute", id="math_to_image"),
    pytest.param(MPL + 'mpl.image.thumbnail("a.png", "b.png")\n', "banned-attribute", id="image.thumbnail"),
    pytest.param(MPL + 'mpl.font_manager.json_dump({}, "x.json")\n', "banned-attribute", id="font_manager.json_dump"),
    pytest.param(MPL + "d = mpl.tempfile.mkdtemp()\n", "banned-attribute", id="re-exported tempfile"),
    pytest.param(MPL + 'h = mpl.logging.FileHandler("x.log")\n', "banned-attribute", id="re-exported logging"),
    pytest.param("x = pd.compat.pickle_compat.pickle.loads(b'')\n", "banned-attribute", id="re-exported pickle"),
    pytest.param("x = pd.core.computation.expr.Expr\n", "banned-attribute", id="pandas eval engine"),
    pytest.param(
        'm = pd.core.apply.import_optional_dependency("os")\n', "banned-attribute", id="import_optional_dependency"
    ),
    pytest.param('pd.options.plotting.backend = "os"\n', "banned-attribute", id="pandas plotting backend option"),
    pytest.param('pd.set_option("plotting.backend", "os")\n', "rc-key", id="pandas plotting backend setting"),
    pytest.param("from sklearn.utils import all_estimators\n", "banned-attribute", id="sklearn all_estimators"),
    pytest.param("from sklearn.utils.discovery import import_module\n", "banned-import", id="sklearn discovery"),
    pytest.param("import sklearn.utils.estimator_checks as checks\n", "banned-import", id="sklearn estimator checks"),
    pytest.param("from sklearn.discriminant_analysis import scipy\n", "banned-attribute", id="re-exported scipy"),
    pytest.param("import statsmodels.api as sm\nsm.webdoc()\n", "banned-attribute", id="statsmodels webdoc"),
    pytest.param(
        "import statsmodels.api as sm\nr = sm.tsa.x13_arima_analysis(df)\n", "banned-attribute", id="x13 runner"
    ),
    pytest.param("from statsmodels.tsa.x13 import run_spec\n", "banned-import", id="statsmodels x13"),
    pytest.param(
        'import statsmodels.api as sm\nm = sm.iolib.smpickle.load_pickle("m")\n', "banned-attribute", id="iolib"
    ),
    pytest.param(
        "import statsmodels.api as sm\nsm.datasets.clear_data_home()\n", "banned-attribute", id="clear_data_home"
    ),
    pytest.param("import scipy.stats\nimg = scipy.datasets.face()\n", "banned-attribute", id="scipy.datasets"),
    pytest.param("import scipy.stats\nm = scipy.sparse.eye(3)\n", "banned-attribute", id="outside the surface"),
    pytest.param(
        "import statsmodels.tsa.api\nx = statsmodels.genmod.families\n", "banned-attribute", id="statsmodels root"
    ),
]
SEABORN_ROUTES = [
    pytest.param("import seaborn as sns\nsns.dogplot()\n", id="dogplot fetches"),
    pytest.param("import seaborn as sns\nnames = sns.get_dataset_names()\n", id="get_dataset_names fetches"),
    pytest.param('import seaborn as sns\nsns.utils.urlretrieve("u", "f")\n', id="urlretrieve"),
    pytest.param('import seaborn as sns\nf = sns.external.docscrape.pydoc.locate("os.system")\n', id="pydoc"),
]
SETTINGS_ROUTES = [
    pytest.param('plt.rcParams["text.usetex"] = True\n', {"rc-key"}, id="usetex starts LaTeX"),
    pytest.param(MPL + 'mpl.rcParams["animation.ffmpeg_path"] = "/bin/sh"\n', {"rc-key"}, id="ffmpeg path"),
    pytest.param(MPL + 'mpl.rcParams["animation.convert_path"] = "x"\n', {"rc-key"}, id="ImageMagick path"),
    pytest.param('plt.rcParams.update({"text.latex.preamble": "x"})\n', {"rc-key"}, id="latex preamble"),
    pytest.param('plt.rcParams.update({"pgf.texsystem": "x"})\n', {"rc-key"}, id="pgf"),
    pytest.param('plt.rcParams.update({"ps.usedistiller": "xpdf"})\n', {"rc-key"}, id="distiller"),
    pytest.param('plt.rcParams.update({"backend": "module://x"})\n', {"rc-key"}, id="bare backend key"),
    pytest.param('plt.rcParamsDefault["text.usetex"] = True\n', {"rc-key"}, id="default settings"),
    pytest.param('plt.rc("text", usetex=True)\n', {"rc-key", "banned-keyword"}, id="rc group and keyword"),
    pytest.param('plt.rc("animation", ffmpeg_path="x")\n', {"rc-key"}, id="rc ffmpeg_path"),
    pytest.param('plt.rc("ps", usedistiller="xpdf")\n', {"rc-key"}, id="rc usedistiller"),
    pytest.param('g = "text"\nplt.rc(g, size=3)\n', {"rc-key"}, id="rc computed group"),
    pytest.param('with plt.rc_context({"text.usetex": True}):\n    pass\n', {"rc-key"}, id="rc_context"),
    pytest.param('with plt.style.context({"pgf.preamble": "x"}):\n    pass\n', {"rc-key"}, id="style.context"),
    pytest.param("s = {}\nwith plt.rc_context(s):\n    pass\n", {"rc-key"}, id="rc_context with a variable"),
    # The #12177 review: a style sheet or settings file loads settings the key rules never see.
    pytest.param('with plt.style.context("data.csv"):\n    pass\n', {"rc-key"}, id="style.context with a path"),
    pytest.param('with plt.style.context("dir/sheet"):\n    pass\n', {"rc-key"}, id="style.context with a dir"),
    pytest.param('with plt.rc_context(None, "data.csv"):\n    pass\n', {"rc-key"}, id="rc_context file positional"),
    pytest.param('with plt.rc_context(fname="data.csv"):\n    pass\n', {"rc-key"}, id="rc_context fname"),
    pytest.param('with plt.rc_context("ggplot"):\n    pass\n', {"rc-key"}, id="rc_context with a string"),
    pytest.param('key = "text.use" + "tex"\nplt.rcParams[key] = True\n', {"rc-key"}, id="computed key"),
    pytest.param('r = plt.rcParams\nr["text.color"] = "k"\n', {"rc-key"}, id="settings as a value"),
    pytest.param("s = {}\nplt.rcParams.update(s)\n", {"rc-key"}, id="update with a variable"),
    pytest.param('plt.rcParams.update(**{"a": 1})\n', {"rc-key"}, id="update unpacked"),
    pytest.param('ax = plt.gca()\nax.text(0, 0, "x", usetex=True)\n', {"banned-keyword"}, id="usetex keyword"),
    pytest.param(
        'ax = plt.gca()\nax.text(0, 0, "x", **{"usetex": True})\n', {"rc-key", "banned-keyword"}, id="usetex unpacked"
    ),
    pytest.param(
        'from matplotlib.textpath import TextPath\np = TextPath((0, 0), "x", ismath="TeX")\n',
        {"rc-key"},
        id="ismath TeX",
    ),
    pytest.param('plt.savefig(f"plot-{THEME}.png", format="ps")\n', {"savefig-target"}, id="savefig format"),
    pytest.param('plt.savefig(f"plot-{THEME}.png", backend="pgf")\n', {"banned-keyword"}, id="savefig backend"),
    pytest.param('o = {}\nplt.savefig(f"plot-{THEME}.png", **o)\n', {"savefig-target"}, id="savefig unpacked"),
]
ALLOWED_NEAR_ROUTES = [
    'plt.rcParams["font.family"] = "DejaVu Sans"\n',
    'plt.rcParams.update({"axes.titlepad": 18, "axes.unicode_minus": True})\n',
    'size = plt.rcParams["axes.titlesize"]\n',
    'size = plt.rcParams.get("font.size")\n',
    'with plt.rc_context({"axes.grid": True}):\n    pass\n',
    'with plt.style.context("seaborn-v0_8-whitegrid"):\n    pass\n',
    'with plt.style.context({"axes.grid": True}):\n    pass\n',
    'plt.rc("font", size=12)\n',
    'labels = ["backend", "frontend", "testing", "latex"]\n',
    'renamed = df.rename(columns={"a": "file_path"})\n',
    'ax = plt.gca()\nax.text(0, 0, r"$\\alpha$")\n',
    'plt.savefig(f"plot-{THEME}.png", format="png")\n',
    "testing_scores = [1, 2]\n",
    'scores = df["test"]\n',
    "from scipy import stats\np = stats.norm.pdf(0)\n",
    "import scipy.stats\np = scipy.stats.norm.pdf(0)\n",
    "windows = np.lib.stride_tricks.sliding_window_view(np.arange(5), 2)\n",
    "import statsmodels.api as sm\nmodel = sm.OLS(df['a'], df['a'])\n",
]
SKLEARN = "from sklearn.preprocessing import StandardScaler\n"
# Keywords and helpers that name a cache or spill directory: the render guard refuses the write in the sandbox, the
# validator keeps it out of the exported code (Fable review of #12177).
CACHE_PATH_ROUTES = [
    pytest.param(
        SKLEARN + 'from sklearn.pipeline import make_pipeline\nm = make_pipeline(StandardScaler(), memory="cache")\n',
        {"banned-keyword"},
        id="make_pipeline memory",
    ),
    pytest.param(
        SKLEARN + 'from sklearn.pipeline import Pipeline\nm = Pipeline([("s", StandardScaler())], memory="cache")\n',
        {"banned-keyword"},
        id="Pipeline memory",
    ),
    pytest.param(
        'from sklearn.cluster import AgglomerativeClustering\nm = AgglomerativeClustering(memory="cache")\n',
        {"banned-keyword"},
        id="AgglomerativeClustering memory",
    ),
    pytest.param(
        'from sklearn.cluster import FeatureAgglomeration\nm = FeatureAgglomeration(memory="cache")\n',
        {"banned-keyword"},
        id="FeatureAgglomeration memory",
    ),
    pytest.param(
        'from sklearn.cluster import OPTICS\nm = OPTICS(memory="cache")\n', {"banned-keyword"}, id="OPTICS memory"
    ),
    pytest.param(
        SKLEARN
        + 'from sklearn.pipeline import make_pipeline\nm = make_pipeline(StandardScaler(), **{"memory": "c"})\n',
        {"banned-keyword"},
        id="memory unpacked from a dict literal",
    ),
    pytest.param(
        SKLEARN
        + 'from sklearn.pipeline import make_pipeline\nm = make_pipeline(StandardScaler(), **{**{"memory": "c"}})\n',
        {"banned-keyword"},
        id="memory unpacked from a nested dict literal",
    ),
    pytest.param(
        'from sklearn.utils.parallel import Parallel\np = Parallel(n_jobs=1, temp_folder="spill")\n',
        {"banned-attribute", "banned-keyword"},
        id="Parallel temp_folder",
    ),
    pytest.param(
        'from sklearn.utils.parallel import Parallel\np = Parallel(1, None, "list", 0, None, "2*n_jobs", "auto", "s")\n',
        {"banned-attribute"},
        id="Parallel temp_folder positional",
    ),
    pytest.param(
        'from sklearn.utils.validation import check_memory\nm = check_memory("cache")\n',
        {"banned-attribute"},
        id="check_memory",
    ),
    pytest.param(
        'import sklearn.utils.validation\nm = sklearn.utils.validation.check_memory("cache")\n',
        {"banned-attribute"},
        id="check_memory as an attribute",
    ),
    pytest.param("f = dict(cachedir='cache')\n", {"banned-keyword"}, id="cachedir"),
]
CACHE_PATH_NEAR_ROUTES = [
    SKLEARN + "from sklearn.pipeline import make_pipeline\nm = make_pipeline(StandardScaler())\n",
    "from sklearn.cluster import AgglomerativeClustering\nm = AgglomerativeClustering(n_clusters=3)\n",
    "fig, ax = plt.subplots()\nim = ax.imshow(np.zeros((2, 2)))\nfig.colorbar(im, ax=ax, location='top')\n",
    "shared = np.shares_memory(np.zeros(2), np.zeros(2))\n",
    'usage = {"memory": 12, "cache": 3}\n',
]


class TestExecAndProcessRoutes:
    @pytest.mark.parametrize(("body", "rule"), EXEC_ROUTES)
    def test_route_is_refused(self, body: str, rule: str) -> None:
        assert rule in security_rules(body)

    @pytest.mark.parametrize("body", SEABORN_ROUTES)
    def test_seaborn_route_is_refused(self, body: str) -> None:
        assert "banned-attribute" in security_rules(body, library="seaborn")

    @pytest.mark.parametrize(("body", "expected"), SETTINGS_ROUTES)
    def test_setting_that_starts_a_program_is_refused(self, body: str, expected: set[str]) -> None:
        assert security_rules(body) == expected

    def test_seaborn_rc_dict_is_checked(self) -> None:
        assert security_rules('import seaborn as sns\nsns.set_theme(rc={"text.usetex": True})\n', "seaborn") == {
            "rc-key"
        }
        assert security_rules('import seaborn as sns\nsns.set_theme(rc={"axes.grid": False})\n', "seaborn") == set()
        assert security_rules("import seaborn as sns\nr = {}\nsns.set_theme(rc=r)\n", "seaborn") == {"rc-key"}

    @pytest.mark.parametrize("body", ALLOWED_NEAR_ROUTES)
    def test_nearest_allowed_sibling_passes(self, body: str) -> None:
        assert security_rules(body) == set()

    def test_the_reported_case_fails_the_data_profile_too(self) -> None:
        code = 'import numpy as np\nimport pandas as pd\nnp.testing.measure("import os")\ndf = pd.DataFrame()\n'
        assert "banned-attribute" in {finding.rule for finding in validate_data_code(code)}

    @pytest.mark.parametrize(("body", "expected"), CACHE_PATH_ROUTES)
    def test_cache_and_spill_directories_are_refused(self, body: str, expected: set[str]) -> None:
        assert security_rules(body) == expected

    @pytest.mark.parametrize("body", CACHE_PATH_NEAR_ROUTES)
    def test_cache_path_siblings_pass(self, body: str) -> None:
        assert security_rules(body) == set()

    def test_messages_never_echo_the_setting(self) -> None:
        findings = validate_security(plot('plt.rcParams["text.latex.preamble"] = "x"\n'), library="matplotlib")
        assert findings and all("preamble" not in finding.message for finding in findings)


# Every public first-level submodule of a package the validator admits whole, as reviewed on 2026-10-14
# (numpy 2.5, pandas 3.0, matplotlib 3.11, seaborn 0.13, scikit-learn 1.9, statsmodels 0.15) and, by the
# import-surface survey of 2026-10-24, plotnine 0.15, mizani 0.14, altair 6.3, pygal 3.1.3, cairosvg 2.9.1 and
# lets-plot 4.11.0: it is either here, reviewed as computing and drawing only, or banned by name in the validator (on
# every receiver, or on its own module in `MODULE_ESCAPES`). A library upgrade that adds a submodule fails
# `test_every_submodule_is_reviewed` until someone looks at it.
REVIEWED_SUBMODULES: dict[str, frozenset[str]] = {
    "numpy": frozenset(
        "char core dtypes exceptions fft lib linalg ma matlib matrixlib polynomial random rec strings typing "
        "version".split()
    ),
    "pandas": frozenset("api arrays core errors plotting tseries util".split()),
    "matplotlib": frozenset(
        "artist axes axis bezier category cbook cm collections colorbar colorizer colors container contour dates "
        "figure font_manager ft2font gridspec hatch image inset layout_engine legend legend_handler lines markers "
        "mathtext mlab offsetbox patches path patheffects projections pyplot quiver rcsetup sankey scale spines "
        "stackplot streamplot style table text textpath ticker transforms tri typing units widgets".split()
    ),
    "seaborn": frozenset(
        "algorithms axisgrid categorical cm colors distributions matrix miscplot objects palettes rcmod regression "
        "relational utils widgets".split()
    ),
    "sklearn": frozenset(
        "base calibration callback cluster compose covariance cross_decomposition decomposition "
        "discriminant_analysis dummy ensemble exceptions experimental feature_extraction feature_selection frozen "
        "gaussian_process impute inspection isotonic kernel_approximation kernel_ridge linear_model manifold "
        "metrics mixture model_selection multiclass multioutput naive_bayes neighbors neural_network pipeline "
        "preprocessing random_projection semi_supervised svm tree utils".split()
    ),
    "mpl_toolkits.mplot3d": frozenset("art3d axes3d axis3d proj3d".split()),
    "mpl_toolkits.axes_grid1": frozenset(
        "anchored_artists axes_divider axes_grid axes_rgb axes_size inset_locator mpl_axes parasite_axes".split()
    ),
    "mpl_toolkits.axisartist": frozenset(
        "angle_helper axes_divider axis_artist axisline_style axislines floating_axes grid_finder "
        "grid_helper_curvelinear parasite_axes".split()
    ),
    "statsmodels.tsa": frozenset(
        "adfvalues api ar_model ardl arima arima_model arima_process base coint_tables descriptivestats "
        "deterministic exponential_smoothing filters forecasting holtwinters innovations interp mlemodel "
        "regime_switching seasonal statespace stattools stl tsatools varma_process vector_ar".split()
    ),
    "statsmodels.graphics": frozenset(
        "agreement api boxplots correlation dotplots factorplots functional gofplots mosaicplot plot_grids "
        "plottools regressionplots tsaplots tukeyplot utils".split()
    ),
    "statsmodels.nonparametric": frozenset(
        "api bandwidths kde kdetools kernel_density kernel_regression kernels kernels_asymmetric linbin "
        "smoothers_lowess smoothers_lowess_old".split()
    ),
    # `animation` and `watermark` are banned by name. `data` reads plotnine's bundled CSVs: the name is too common
    # to ban, so the validator refuses the module by its path (`DENIED_IMPORTS`, `TestPlotnineProfile`).
    "plotnine": frozenset(
        "composition coords data doctools exceptions facets geoms ggplot guides helpers iapi labels layer mapping "
        "options positions scales stats themes typing".split()  # qplot is banned by name (it evaluates its arguments)
    ),
    "mizani": frozenset("bounds breaks formatters labels palettes scale transforms typing utils".split()),
    # `datasets` (fetches over the network) and `jupyter` (re-exports `find_spec`) are banned by name.
    "altair": frozenset("expr theme typing utils vegalite".split()),
    # Surveys of 2026-10-24 (pygal 3.1.3, cairosvg 2.9.1, lets-plot 4.11.0). pygal's `etree` (its ElementTree
    # proxy) and `test` are banned by name; cairosvg's `css`, `features`, `image`, `parser`, `surface`, `url` and
    # `test_api` on their module (`MODULE_ESCAPES`); lets-plot's `frontend_context`, `geo_data`, `settings_utils`,
    # `tilesets` and the plot package's `geom_livemap_` by name. `lets_plot.plot` is pinned too: it holds the livemap.
    "pygal": frozenset(
        "adapters colors config formatters graph interpolate maps serie state stats style svg table util view".split()
    ),
    "cairosvg": frozenset("bounding_box colors defs helpers path shapes svg text".split()),
    "lets_plot": frozenset("bistro export geo_data_internals mapping plot".split()),
    "lets_plot.plot": frozenset(
        "annotation coord core expand_limits_ facet font_features geom geom_extras geom_function_ geom_imshow_ "
        "ggbunch_ ggdeck_ gggrid_ ggtb_ guide label marginal_layer plot pos sampling sandbox_ scale "
        "scale_colormap_mpl scale_convenience scale_identity_ scale_position series_meta stat subplots "
        "subplots_util theme_ theme_set tooltip util".split()
    ),
}


@pytest.mark.parametrize("root", sorted(REVIEWED_SUBMODULES))
def test_every_submodule_is_reviewed(root: str) -> None:
    """A public submodule is reviewed as safe, or the validator bans its name on every receiver or on its module."""
    package = pytest.importorskip(root)
    on_module = {path.rpartition(".")[2] for path in MODULE_ESCAPES if path.rpartition(".")[0] == root}
    banned = ESCAPE_ATTRIBUTES | UNSAFE_SUBMODULES | UNSAFE_HELPERS | BANNED_ATTRIBUTES | BANNED_IO | on_module
    found = {info.name for info in pkgutil.iter_modules(package.__path__) if not info.name.startswith("_")}
    unreviewed = sorted(found - REVIEWED_SUBMODULES[root] - banned)
    assert not unreviewed, f"review these {root} submodules and add them to REVIEWED_SUBMODULES or ban them"
    assert not REVIEWED_SUBMODULES[root] & banned


# --- plotnine and altair (step 1b of agentic/specs/261024-agent-all-libraries.md) ------------------------------

PLOTNINE_HEADER = """import os

import pandas as pd
from plotnine import aes, geom_point, ggplot, labs, theme

THEME = os.getenv("ANYPLOT_THEME", "light")
df = pd.DataFrame({"a": [1, 2, 3]})
"""
PLOTNINE_SAVE = 'plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)'
PLOTNINE_FOOTER = (
    '\nplot = ggplot(df, aes(x="a", y="a")) + geom_point() + labs(title="") + theme(figure_size=(8, 4.5))\n'
    + PLOTNINE_SAVE
    + "\n"
)
ALTAIR_HEADER = """import os

import altair as alt
import pandas as pd
from PIL import Image

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
df = pd.DataFrame({"a": [1, 2, 3]})
"""
ALTAIR_CHART = 'chart = alt.Chart(df).mark_circle().encode(x="a:Q", y="a:Q").properties(width=620, height=320)\n'
ALTAIR_PNG_SAVE = 'chart.save(f"plot-{THEME}.png", scale_factor=4.0)'
ALTAIR_HTML_SAVE = 'chart.save(f"plot-{THEME}.html")'
# The catalogue's padding block: vl-convert writes the PNG, PIL reopens it and centres it on the 3200 x 1800 canvas.
ALTAIR_PADDING = """TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(f"altair produced {_w}x{_h}, more than {TW}x{TH}")
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
"""
ALTAIR_FOOTER = "\n" + ALTAIR_CHART + ALTAIR_PNG_SAVE + "\n" + ALTAIR_PADDING + ALTAIR_HTML_SAVE + "\n"
NO_PNG_SAVE = 'no save of f"plot-{THEME}.png" found'


def plotnine_plot(body: str = "") -> str:
    """A minimal valid plotnine file in the catalogue's shape, with `body` between the THEME block and the plot."""
    return PLOTNINE_HEADER + body + PLOTNINE_FOOTER


def altair_plot(body: str = "") -> str:
    """A minimal valid altair file in the catalogue's shape, padding block included, with `body` before the chart."""
    return ALTAIR_HEADER + body + ALTAIR_FOOTER


def library_plot(library: str, body: str = "") -> str:
    """The minimal valid file of a library with a profile, with `body` before its plot."""
    if library == "plotnine":
        return plotnine_plot(body)
    if library == "altair":
        return altair_plot(body)
    if library == "pygal":
        return pygal_plot(body)
    if library == "letsplot":
        return letsplot_plot(body)
    return plot(("import seaborn as sns\n" if library == "seaborn" else "") + body)


def rules_of(code: str, library: str) -> set[str]:
    return {finding.rule for finding in validate_security(code, library=library)}


def swapped(code: str, old: str, new: str) -> str:
    """`code` with its one `old` replaced: an anchor that drifted fails here instead of testing the unchanged file."""
    assert code.count(old) == 1, old
    return code.replace(old, new)


EXPRESSION_IMPORTS = "import numpy as np\nfrom plotnine import after_stat, facet_grid, facet_wrap, label_value\n"
PLOTNINE_EXPRESSIONS = [
    pytest.param('aes(x="factor(cyl)")', id="a call on a column"),
    pytest.param('aes(y=after_stat("count"))', id="after_stat"),
    pytest.param('aes(y="after_stat(count)")', id="after_stat inside the string"),
    pytest.param('aes(x="day - 0.42")', id="arithmetic"),
    pytest.param('aes(x="importance + std")', id="a sum, not a formula"),
    pytest.param('facet_wrap("~panel")', id="one-sided formula"),
    pytest.param('facet_grid("var_y ~ var_x")', id="two-sided formula"),
    pytest.param('facet_grid("pane ~ .")', id="formula with a dot"),
    pytest.param('aes(x="True Label")', id="column with a space"),
    pytest.param('aes(x="x")', id="bare column"),
    pytest.param('aes(x="np.log10(x)")', id="numpy function"),
]
PLOTNINE_EXPRESSION_ESCAPES = [
    pytest.param("aes(x='open(\"/etc/passwd\").read()')", "aes", "banned-name", id="open"),
    pytest.param("aes(x='os.getenv(\"X\")')", "aes", "os-use", id="os beyond THEME"),
    pytest.param("aes(y=\"df.to_csv('x')\")", "aes", "banned-call", id="writer"),
    pytest.param('aes(x="x.__class__")', "aes", "dunder", id="dunder"),
    pytest.param("facet_wrap(\"~ open('x')\")", "facet_wrap", "banned-name", id="facet formula"),
    pytest.param("facet_grid(\"a ~ open('x')\")", "facet_grid", "banned-name", id="right side of a facet formula"),
    pytest.param("aes(x=\"np.testing.measure('1')\")", "aes", "banned-attribute", id="exec route"),
    pytest.param("aes(**{'x': 'open(\"x\")'})", "aes", "banned-name", id="unpacked dict literal"),
    pytest.param("aes(x=COLUMN)", "aes", "banned-name", id="a module-level name bound to the string"),
]
# Arguments plotnine would evaluate that the walk cannot read: a variable, a concatenation, an unpacked name.
PLOTNINE_OPAQUE_ARGUMENTS = [
    pytest.param("aes(x=columns[0])", id="subscript"),
    pytest.param("aes(x='op' + 'en(\"x\")')", id="concatenation"),
    pytest.param("aes(**mapping)", id="unpacked name"),
    pytest.param("aes(x=f\"{'op'}en('x')\")", id="f-string"),
    pytest.param("aes(x=LATER)", id="a name bound twice"),
    pytest.param("facet_wrap(facets=columns)", id="facet name"),
]
EXPRESSION_BINDINGS = (
    'COLUMN = \'open("/etc/passwd").read()\'\ncolumns = ["a"]\nmapping = {"x": "a"}\nLATER = "a"\nLATER = "b"\n'
)


class TestPlotnineProfile:
    """plotnine: the matplotlib stack plus plotnine and mizani, three save calls and the expression strings."""

    def test_minimal_file_has_no_findings(self) -> None:
        assert validate_security(plotnine_plot(), library="plotnine") == []

    @pytest.mark.parametrize(
        "body",
        [
            "import plotnine\n",
            "import mizani.formatters\n",
            "from mizani.formatters import percent_format\n",
            "from mizani.breaks import breaks_extended\n",
            "import matplotlib.pyplot as plt\n",
            "from plotnine import ggsave, theme_matplotlib\n",
            "from scipy import stats\n",
        ],
    )
    def test_allowed_import(self, body: str) -> None:
        assert rules_of(plotnine_plot(body), "plotnine") == set()

    @pytest.mark.parametrize(
        "body",
        [
            "import plotnine.data\n",
            "from plotnine.data import mtcars\n",
            "from plotnine import data\n",
            "import plotnine.watermark\n",
            "from plotnine import watermark\n",
            "import plotnine.animation\n",
            "from plotnine.animation import PlotnineAnimation\n",
            "import vl_convert\n",
            "from PIL import Image\n",
            "import altair as alt\n",
        ],
    )
    def test_banned_import(self, body: str) -> None:
        assert "banned-import" in rules_of(plotnine_plot(body), "plotnine")

    @pytest.mark.parametrize(
        "body", ["import plotnine\nd = plotnine.data.mtcars\n", "import plotnine as p9\nd = p9.data\n"]
    )
    def test_bundled_data_is_refused_by_its_path(self, body: str) -> None:
        """`data` is listed in REVIEWED_SUBMODULES; the module is refused by path, not by name."""
        assert rules_of(plotnine_plot(body), "plotnine") == {"banned-attribute"}

    @pytest.mark.parametrize(
        "save",
        [
            pytest.param('ggsave(plot, f"plot-{THEME}.png", dpi=300)', id="ggsave, file second"),
            pytest.param('ggsave(plot, filename=f"plot-{THEME}.png", dpi=400)', id="ggsave filename="),
            pytest.param('fig = plot.draw()\nfig.savefig(f"plot-{THEME}.png", dpi=300)', id="savefig after draw"),
            pytest.param('plot.save(filename=f"plot-{THEME}.png", dpi=400)', id="save filename="),
            pytest.param('plot.save(f"plot-{THEME}.png", format="png", limitsize=False)', id="format png"),
        ],
    )
    def test_save_passes(self, save: str) -> None:
        code = swapped(plotnine_plot("from plotnine import ggsave\n"), PLOTNINE_SAVE, save)
        assert validate_security(code, library="plotnine") == []

    @pytest.mark.parametrize(
        "save",
        [
            pytest.param('plot.save("plot.png")', id="other file"),
            pytest.param('plot.save(f"plot-{THEME}.png", path="out")', id="path joins a directory"),
            pytest.param('plot.save(f"plot-{THEME}.png", format="svg")', id="format"),
            pytest.param('kw = {}\nplot.save(f"plot-{THEME}.png", **kw)', id="unpacked keywords"),
            pytest.param('plot.save(f"plot-{THEME}.png", dpi=400, facecolor="#fff")', id="savefig keyword via save"),
            pytest.param('plot.save(f"plot-{THEME}.html")', id="the HTML is altair's"),
            pytest.param('ggsave(plot, "plot.png")', id="ggsave other file"),
            pytest.param('ggsave(f"plot-{THEME}.png", plot)', id="ggsave file first"),
            pytest.param('fig = plot.draw()\nfig.savefig("plot.png")', id="savefig other file"),
        ],
    )
    def test_other_save_is_a_finding(self, save: str) -> None:
        code = swapped(plotnine_plot("from plotnine import ggsave\n"), PLOTNINE_SAVE, save)
        assert rules_of(code, "plotnine") == {"savefig-target"}

    def test_a_file_that_saves_no_png_is_a_finding(self) -> None:
        code = swapped(plotnine_plot(), PLOTNINE_SAVE, 'plot.save(f"plot-{THEME}.html")')
        assert [f.message for f in validate_security(code, library="plotnine") if f.line is None] == [NO_PNG_SAVE]

    def test_a_save_bound_to_a_name_is_refused(self) -> None:
        code = swapped(plotnine_plot(), PLOTNINE_SAVE, 'f = plot.save\nf(f"plot-{THEME}.png")')
        assert {(f.rule, f.message) for f in validate_security(code, library="plotnine")} == {
            ("banned-attribute", "'.save' may only be called directly"),
            ("savefig-target", NO_PNG_SAVE),
        }

    def test_reopening_the_png_is_altairs_rule_only(self) -> None:
        assert rules_of(plotnine_plot("img = Image.open(f'plot-{THEME}.png')\n"), "plotnine") == {"banned-call"}

    @pytest.mark.parametrize(
        "save",
        [
            pytest.param('plot.save(f"plot-{THEME}.png", None, "/tmp")', id="path as the third positional"),
            pytest.param('plot.save(f"plot-{THEME}.png", "pgf")', id="format as the second positional"),
            pytest.param('ggsave(plot, f"plot-{THEME}.png", "png", "/tmp")', id="ggsave path positional"),
        ],
    )
    def test_path_and_format_as_positionals_are_findings(self, save: str) -> None:
        """`save(filename, format, path, ...)`: the keyword allowlist does not see the same arguments by position."""
        code = swapped(plotnine_plot("from plotnine import ggsave\n"), PLOTNINE_SAVE, save)
        assert "savefig-target" in rules_of(code, "plotnine")

    @pytest.mark.parametrize("expression", PLOTNINE_EXPRESSIONS)
    def test_expression_string_passes(self, expression: str) -> None:
        assert rules_of(plotnine_plot(EXPRESSION_IMPORTS + f"m = {expression}\n"), "plotnine") == set()

    @pytest.mark.parametrize(("expression", "call", "rule"), PLOTNINE_EXPRESSION_ESCAPES)
    def test_expression_string_is_walked_as_code(self, expression: str, call: str, rule: str) -> None:
        body = EXPRESSION_IMPORTS + EXPRESSION_BINDINGS + f"m = {expression}\n"
        findings = validate_security(plotnine_plot(body), library="plotnine")
        assert any(f.rule == rule and f.message.startswith(f"in the {call} expression: ") for f in findings)

    @pytest.mark.parametrize("expression", PLOTNINE_OPAQUE_ARGUMENTS)
    def test_an_argument_the_walk_cannot_read_is_refused(self, expression: str) -> None:
        body = EXPRESSION_IMPORTS + EXPRESSION_BINDINGS + f"m = {expression}\n"
        findings = validate_security(plotnine_plot(body), library="plotnine")
        opaque = ("as string literals, not as an expression", "takes ** only from a dict literal")
        assert any(f.rule == "banned-call" and f.message.endswith(opaque) for f in findings), findings

    @pytest.mark.parametrize(
        "rebinding",
        [
            pytest.param("match 'open(\"x\").read()':\n    case COLUMN:\n        pass\n", id="match capture"),
            pytest.param("for COLUMN in ['open(\"x\").read()']:\n    pass\n", id="loop target"),
            pytest.param("from textwrap import dedent as COLUMN\n", id="import"),
            pytest.param("def COLUMN():\n    return 1\n", id="function name"),
        ],
    )
    def test_a_name_bound_twice_is_not_read_as_its_literal(self, rebinding: str) -> None:
        """`COLUMN = "a"` and then `case COLUMN:` would hand plotnine the subject string, which the walk never saw
        (the validator pass of 2026-10-26: the 1b rule counted only assignments and passed the match capture)."""
        body = EXPRESSION_IMPORTS + 'COLUMN = "a"\n' + rebinding + "m = aes(x=COLUMN)\n"
        findings = validate_security(plotnine_plot(body), library="plotnine")
        assert any(f.message == "aes takes its column names as string literals, not as an expression" for f in findings)

    def test_literal_arguments_the_walk_can_read_pass(self) -> None:
        body = EXPRESSION_IMPORTS + (
            'COLUMN = "a"\n'
            'm = aes(x=COLUMN, y=after_stat("count"), size=3, alpha=None)\n'
            'f = facet_wrap(["a", "b"], ncol=2, scales="free_y", labeller=label_value)\n'
            'g = facet_grid(rows="a", cols="b", labeller=label_value)\n'
            'h = aes(**{"x": "a", "y": "b"})\n'
        )
        assert rules_of(plotnine_plot(body), "plotnine") == set()

    def test_qplot_is_banned_by_name(self) -> None:
        body = "from plotnine import qplot\nm = qplot(x=\"eval('1')\", data=df)\n"
        assert rules_of(plotnine_plot(body), "plotnine") == {"banned-attribute"}

    @pytest.mark.parametrize(
        "expression",
        [
            pytest.param("aes(x='np.save(\"x\", x)')", id="np.save"),
            pytest.param("aes(x='plt.savefig(\"x.svg\")')", id="savefig"),
            pytest.param("aes(x='df.info(buf=\"x\")')", id="buffer writer"),
        ],
    )
    def test_expression_string_that_writes_is_refused(self, expression: str) -> None:
        """plotnine evaluates the string at draw time; the walk runs no save or buffer-writer check inside it."""
        body = EXPRESSION_IMPORTS + "import matplotlib.pyplot as plt\n" + f"m = {expression}\n"
        findings = validate_security(plotnine_plot(body), library="plotnine")
        assert any(f.message.startswith("in the aes expression: ") for f in findings)

    @pytest.mark.parametrize(
        ("library", "body"),
        [
            pytest.param(
                "plotnine",
                'from plotnine import geom_smooth\nm = geom_smooth(method="lm", formula="y ~ x")\n',
                id="plotnine geom_smooth",
            ),
            pytest.param(
                "plotnine", 'from plotnine import stat_quantile\nm = stat_quantile(formula="y ~ x")\n', id="stat"
            ),
            pytest.param("matplotlib", 'm = geom_smooth(method="lm", formula="y ~ x")\n', id="any call, any profile"),
            pytest.param(
                "matplotlib",
                'import statsmodels.api as sm\nm = sm.OLS.from_formula(formula="y ~ x", data=df)\n',
                id="statsmodels from_formula",
            ),
        ],
    )
    def test_formula_keyword_is_refused(self, library: str, body: str) -> None:
        assert "banned-keyword" in rules_of(library_plot(library, body), library)

    def test_formula_as_a_positional_is_refused(self) -> None:
        """`from_formula(formula, data)`: patsy gets the same string by position, so the name is banned."""
        body = 'import statsmodels.api as sm\nm = sm.OLS.from_formula("y ~ x", df)\n'
        assert rules_of(library_plot("matplotlib", body), "matplotlib") == {"banned-attribute"}

    def test_smooth_without_a_formula_passes(self) -> None:
        body = 'from plotnine import geom_smooth\nm = geom_smooth(method="lm", se=True)\n'
        assert rules_of(plotnine_plot(body), "plotnine") == set()

    @pytest.mark.parametrize(
        ("call", "expected"),
        [
            pytest.param('theme_matplotlib(fname="x")', {"rc-key"}, id="settings file"),
            pytest.param('theme_matplotlib({"axes.grid": False}, "x.rc")', {"rc-key"}, id="settings file positional"),
            pytest.param('theme_matplotlib({"text.usetex": True})', {"rc-key"}, id="LaTeX setting"),
            pytest.param("theme_matplotlib(rc=settings)", {"rc-key"}, id="settings in a variable"),
            pytest.param('theme_matplotlib(rc={"axes.grid": False})', set(), id="literal safe settings"),
            pytest.param("theme_matplotlib()", set(), id="no settings"),
        ],
    )
    def test_theme_matplotlib_is_a_settings_consumer(self, call: str, expected: set[str]) -> None:
        body = f"from plotnine import theme_matplotlib\nsettings = {{}}\nt = {call}\n"
        assert rules_of(plotnine_plot(body), "plotnine") == expected

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            pytest.param(
                'from mizani.palettes import brewer_pal\np = brewer_pal(palette="Blues")\nb = p.bpal\n',
                {"banned-attribute"},
                id="brewer_pal's stored getattr",
            ),
            pytest.param(
                'from mizani.palettes import brewer_pal\np = brewer_pal(palette="Blues")\n', set(), id="brewer_pal"
            ),
            pytest.param('import mizani\nv = mizani.version("numpy")\n', {"banned-attribute"}, id="mizani.version"),
            pytest.param("from mizani import version\n", {"banned-attribute"}, id="from mizani import version"),
            pytest.param(
                "from mizani.formatters import percent_format\nf = percent_format()\n", set(), id="a formatter"
            ),
        ],
    )
    def test_mizani(self, body: str, expected: set[str]) -> None:
        assert rules_of(plotnine_plot(body), "plotnine") == expected


ALTAIR_ROUTES = [
    pytest.param('t = alt.topo_feature("https://x", "y")\n', {"banned-attribute", "url-literal"}, id="topo_feature"),
    pytest.param('alt.renderers.enable("browser")\n', {"banned-attribute"}, id="browser renderer"),
    pytest.param("alt.Chart(df).serve()\n", {"banned-attribute"}, id="serve opens a port"),
    pytest.param("alt.Chart(df).open_editor()\n", {"banned-attribute"}, id="open_editor starts a browser"),
    pytest.param("j = alt.utils.jsonschema\n", {"banned-attribute"}, id="re-exported jsonschema"),
    pytest.param('d = alt.UrlData("x.csv")\n', {"banned-attribute"}, id="UrlData"),
    pytest.param("v = alt.version\n", {"banned-attribute"}, id="importlib version bound on the package"),
    pytest.param("p = alt.utils.data.Path\n", {"banned-attribute"}, id="re-exported Path"),
    pytest.param('alt.vegalite_compilers.enable("x")\n', {"banned-attribute"}, id="compiler plugin by name"),
    pytest.param('alt.theme.enable("dark")\n', {"banned-attribute"}, id="a registry switch, altair's ban"),
    pytest.param('alt.theme.register("x", lambda: {})\n', {"banned-attribute"}, id="a registry hook"),
]
ALTAIR_NEAR_ROUTES = [
    pytest.param("alt.data_transformers.disable_max_rows()\n", id="disable_max_rows"),
    # `to_url` encodes the spec into a Vega editor link in process (vl-convert): no network, no file, so not banned.
    pytest.param("u = alt.Chart(df).to_url()\n", id="to_url"),
    pytest.param("s = alt.Chart(df).to_dict()\n", id="to_dict"),
]


class TestAltairProfile:
    """altair: altair and `PIL.Image` only, a PNG and an HTML save, and the PIL block that reopens the PNG."""

    def test_minimal_file_has_no_findings(self) -> None:
        assert validate_security(altair_plot(), library="altair") == []

    @pytest.mark.parametrize(
        "body", ["import altair\n", "import PIL.Image\n", "from altair import expr\n", "import numpy as np\n"]
    )
    def test_allowed_import(self, body: str) -> None:
        assert rules_of(altair_plot(body), "altair") == set()

    @pytest.mark.parametrize(
        "body",
        [
            "from PIL import ImageDraw\n",
            "import PIL.ImageDraw\n",
            "import PIL\n",
            "import vl_convert\n",
            "import vl_convert as vlc\n",
            "import altair.datasets\n",
            "import altair.datasets as d\n",
            "from altair import datasets\n",
            "import altair.jupyter\n",
            "import altair.utils.execeval\n",
            "from altair.utils import execeval\n",
            "import matplotlib.pyplot as plt\n",
            "from plotnine import ggplot\n",
        ],
    )
    def test_banned_import(self, body: str) -> None:
        assert "banned-import" in rules_of(altair_plot(body), "altair")

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            pytest.param(ALTAIR_PNG_SAVE, 'chart.save(fp=f"plot-{THEME}.png", ppi=200)', id="fp= and ppi="),
            pytest.param(ALTAIR_PNG_SAVE, 'chart.save(f"plot-{THEME}.png", format="png")', id="format png"),
            pytest.param(ALTAIR_HTML_SAVE, 'chart.save(f"plot-{THEME}.html", format="html")', id="format html"),
            pytest.param(
                ALTAIR_HTML_SAVE,
                'chart.save(f"plot-{THEME}.html", inline=True, embed_options={"actions": False})',
                id="HTML embedding",
            ),
        ],
    )
    def test_save_passes(self, old: str, new: str) -> None:
        assert validate_security(swapped(altair_plot(), old, new), library="altair") == []

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            pytest.param(ALTAIR_PNG_SAVE, 'chart.save("plot.png", scale_factor=4.0)', id="other file"),
            pytest.param(ALTAIR_PNG_SAVE, 'chart.save(f"plot-{THEME}.svg")', id="other type"),
            pytest.param(ALTAIR_HTML_SAVE, 'chart.save(f"plot-{THEME}.html", format="png")', id="format of the other"),
            pytest.param(ALTAIR_PNG_SAVE, 'chart.save(f"plot-{THEME}.png", webdriver="chrome")', id="webdriver"),
            pytest.param(ALTAIR_PNG_SAVE, 'chart.save(f"plot-{THEME}.png", engine="vl-convert")', id="engine"),
            pytest.param('Image.open(f"plot-{THEME}.png")', 'Image.open("/etc/passwd")', id="reopen another file"),
            pytest.param('Image.open(f"plot-{THEME}.png")', 'Image.open(f"plot-{THEME}.png", mode="r")', id="mode="),
            pytest.param('_canvas.save(f"plot-{THEME}.png")', '_canvas.save("x.png")', id="PIL save elsewhere"),
            pytest.param('_canvas.save(f"plot-{THEME}.png")', '_canvas.save(f"plot-{THEME}.png", **{})', id="PIL **"),
        ],
    )
    def test_other_save_or_reopen_is_a_finding(self, old: str, new: str) -> None:
        assert rules_of(swapped(altair_plot(), old, new), "altair") == {"savefig-target"}

    def test_a_file_whose_only_save_is_the_html_saves_no_png(self) -> None:
        findings = validate_security(ALTAIR_HEADER + ALTAIR_CHART + ALTAIR_HTML_SAVE + "\n", library="altair")
        assert [(f.rule, f.message, f.line) for f in findings] == [("savefig-target", NO_PNG_SAVE, None)]

    @pytest.mark.parametrize(("body", "name"), [("f = Image.open\n", "open"), ("s = alt.Chart(df).save\n", "save")])
    def test_reopen_and_save_may_only_be_called_directly(self, body: str, name: str) -> None:
        findings = validate_security(altair_plot(body), library="altair")
        assert [(f.rule, f.message) for f in findings] == [
            ("banned-attribute", f"'.{name}' may only be called directly")
        ]

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("import matplotlib.pyplot as plt\nplt.savefig(f'plot-{THEME}.png')\n", {"banned-import", "banned-call"}),
            ("fig.savefig(f'plot-{THEME}.png')\n", {"banned-call"}),
        ],
    )
    def test_matplotlib_save_is_not_altairs(self, body: str, expected: set[str]) -> None:
        findings = validate_security(altair_plot(body), library="altair")
        assert {f.rule for f in findings} == expected
        assert any(f.message.endswith("; the plot is saved with save") for f in findings if f.rule == "banned-call")

    @pytest.mark.parametrize(("body", "expected"), ALTAIR_ROUTES)
    def test_route_is_refused(self, body: str, expected: set[str]) -> None:
        assert rules_of(altair_plot(body), "altair") == expected

    @pytest.mark.parametrize("body", ALTAIR_NEAR_ROUTES)
    def test_nearest_allowed_sibling_passes(self, body: str) -> None:
        assert rules_of(altair_plot(body), "altair") == set()

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param('alt.data_transformers.enable("json")\n', id="json transformer"),
            pytest.param('alt.data_transformers.enable("csv", filename="x.csv")\n', id="csv transformer, file named"),
        ],
    )
    def test_data_transformer_that_writes_a_file_is_refused(self, body: str) -> None:
        """The `json` and `csv` transformers write the chart data to a file (`filename=` names it) on every save."""
        assert rules_of(altair_plot(body), "altair") != set()


# --- pygal and lets-plot (step 1c of agentic/specs/261024-agent-all-libraries.md) ------------------------------

PYGAL_HEADER = """import os

import pygal
from pygal.style import Style

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]
"""
# The catalogue's chart: pygal's own stylesheets before an inline rule (14 files), no tooltip script (30 files).
PYGAL_CSS = 'css=("file://style.css", "file://graph.css", "inline:.axis .line { stroke-opacity: .25; }")'
PYGAL_CHART = (
    "style = Style(background=PAGE_BG, plot_background=PAGE_BG, foreground=INK, colors=IMPRINT)\n"
    'chart = pygal.XY(width=3200, height=1800, style=style, title="", js=[], '
    + PYGAL_CSS
    + ', value_formatter=lambda v: f"{v:.0f}%")\n'
    'chart.add("a", [(1, 2), (3, 4)])\n'
)
PYGAL_PNG_SAVE = 'chart.render_to_png(f"plot-{THEME}.png")'
PYGAL_HTML_SAVE = 'chart.render_to_file(f"plot-{THEME}.html")'
PYGAL_FOOTER = "\n" + PYGAL_CHART + PYGAL_PNG_SAVE + "\n" + PYGAL_HTML_SAVE + "\n"
SVG2PNG = 'cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png")'
LETSPLOT_HEADER = """import os

import pandas as pd
from lets_plot import LetsPlot, aes, geom_point, ggplot, ggsize, labs, layer_tooltips
from lets_plot.export import ggsave

LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
df = pd.DataFrame({"a": [1, 2, 3]})
"""
LETSPLOT_PLOT = (
    'plot = ggplot(df, aes(x="a", y="a")) + geom_point(tooltips=layer_tooltips().line("@a").format("@a", ".1f"))'
    ' + labs(title="") + ggsize(1600, 900)\n'
)
LETSPLOT_PNG_SAVE = 'ggsave(plot, f"plot-{THEME}.png", path=".", scale=2)'
LETSPLOT_HTML_SAVE = 'ggsave(plot, f"plot-{THEME}.html", path=".")'
LETSPLOT_FOOTER = "\n" + LETSPLOT_PLOT + LETSPLOT_PNG_SAVE + "\n" + LETSPLOT_HTML_SAVE + "\n"


def pygal_plot(body: str = "") -> str:
    """A minimal valid pygal file in the catalogue's shape, PNG and HTML saves included, with `body` before the chart."""
    return PYGAL_HEADER + body + PYGAL_FOOTER


def letsplot_plot(body: str = "") -> str:
    """A minimal valid lets-plot file in the catalogue's normalised shape, with `body` before the plot."""
    return LETSPLOT_HEADER + body + LETSPLOT_FOOTER


PYGAL_ROUTES = [
    pytest.param("t = chart.render_tree()\n", {"banned-attribute"}, id="render_tree hands out the live tree"),
    pytest.param("chart.render_in_browser()\n", {"banned-attribute"}, id="render_in_browser"),
    pytest.param("t = chart.render_table()\n", {"banned-attribute"}, id="render_table"),
    pytest.param("r = chart.render_response()\n", {"banned-attribute"}, id="render_response"),
    pytest.param("chart.add_xml_filter(lambda tree: tree)\n", {"banned-attribute"}, id="add_xml_filter"),
    pytest.param('x = pygal.util.cut([IMPRINT], "copy")\n', {"banned-attribute"}, id="cut, a getattr by string"),
    pytest.param("from pygal.util import template\n", {"banned-attribute"}, id="template, a str.format"),
    pytest.param("e = pygal.entry_points\n", {"banned-attribute"}, id="plugin entry points"),
    pytest.param("e = pygal.etree\n", {"banned-attribute"}, id="ElementTree proxy"),
    pytest.param("e = pygal.svg.etree\n", {"banned-attribute"}, id="ElementTree proxy re-exported"),
    pytest.param("from pygal.etree import etree\n", {"banned-import", "banned-attribute"}, id="from pygal.etree"),
    pytest.param('chart.config._update({"js": ["x.js"]})\n', {"banned-attribute"}, id="config merge"),
    pytest.param("import cairosvg\ns = cairosvg.SURFACES\n", {"banned-attribute"}, id="SURFACES"),
    pytest.param(
        'import cairosvg\ncairosvg.svg2pdf(bytestring=b"", write_to="x.pdf")\n', {"banned-attribute"}, id="svg2pdf"
    ),
    pytest.param("import cairosvg\nc = cairosvg.surface.cairo\n", {"banned-attribute"}, id="cairocffi in surface"),
    pytest.param("import cairosvg\nf = cairosvg.helpers.cairo.ffi\n", {"banned-attribute"}, id="cairocffi in helpers"),
    pytest.param("from cairosvg.surface import PNGSurface\n", {"banned-import", "banned-attribute"}, id="a surface"),
    pytest.param("import cairosvg.parser\n", {"banned-import"}, id="parser import"),
    pytest.param('import cairosvg\nb = cairosvg.url.fetch("x")\n', {"banned-attribute"}, id="url fetch"),
    pytest.param('import cairosvg\np = cairosvg.Path("x")\n', {"banned-attribute"}, id="re-exported Path"),
    pytest.param("import cairosvg\np = cairosvg.ROOT.parent\n", {"banned-attribute"}, id="ROOT, a Path instance"),
    pytest.param("import cairosvg\ni = cairosvg.image.Image\n", {"banned-attribute"}, id="PIL in image"),
    pytest.param("import cairosvg\nc = cairosvg.css.cssselect2\n", {"banned-attribute"}, id="cssselect2 in css"),
    pytest.param("import cairosvg\nc = [cairosvg.colors][0].tinycss2\n", {"banned-attribute"}, id="tinycss2 by name"),
    pytest.param("import cairosvg\nt = cairosvg.test_api\n", {"banned-attribute"}, id="test_api"),
]
# Each pygal save name writes one kind of file (`SaveRule.writes`; the correctness review of 2026-10-26): the name in
# its own save's place passes, and the same name in the HTML save's place writing the other file is a finding.
PYGAL_FILE_TYPES = [
    pytest.param(
        PYGAL_PNG_SAVE,
        PYGAL_PNG_SAVE,
        'chart.render_to_png(f"plot-{THEME}.html")',
        'render_to_png writes only f"plot-{THEME}.png"',
        id="render_to_png",
    ),
    pytest.param(
        PYGAL_PNG_SAVE,
        "import cairosvg\n" + SVG2PNG,
        'cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.html")',
        'svg2png writes only f"plot-{THEME}.png"',
        id="svg2png",
    ),
    pytest.param(
        PYGAL_HTML_SAVE,
        PYGAL_HTML_SAVE,
        'chart.render_to_file(f"plot-{THEME}.png")',
        'render_to_file writes only f"plot-{THEME}.html"',
        id="render_to_file",
    ),
]
PYGAL_NEAR_ROUTES = [
    pytest.param("svg = chart.render()\n", id="render"),
    pytest.param("svg = chart.render(is_unicode=True)\n", id="render as text"),
    pytest.param("uri = chart.render_data_uri()\n", id="render_data_uri"),
    pytest.param('chart.x_labels = ["a", "b"]\n', id="labels"),
    pytest.param('style2 = Style(font_family="DejaVu Sans, sans-serif")\n', id="a local font"),
    pytest.param("from pygal.formatters import Significant\nf = Significant()\n", id="a formatter"),
    pytest.param("import cairosvg\nv = cairosvg.VERSION\n", id="cairosvg's version string"),
]
PYGAL_CONFIG_ROUTES = [
    pytest.param('c2 = pygal.Bar(js=["//cdn.example/x.js"])\n', {"banned-keyword"}, id="a script fetched"),
    pytest.param('c2 = pygal.Bar(js=["file:///etc/passwd"])\n', {"banned-keyword", "url-literal"}, id="a script read"),
    pytest.param('c2 = pygal.Bar(css=["file:///etc/passwd"])\n', {"banned-keyword", "url-literal"}, id="a file read"),
    pytest.param('c2 = pygal.Bar(css=["fi" + "le:///etc/passwd"])\n', {"banned-keyword"}, id="a built entry"),
    pytest.param('p = "x"\nc2 = pygal.Bar(css=[f"{p}inline:a"])\n', {"banned-keyword"}, id="f-string head"),
    pytest.param('c2 = pygal.Bar(css="inline:a")\n', {"banned-keyword"}, id="not a list"),
    pytest.param('C = ["inline:a"]\nC = ["x"]\nc2 = pygal.Bar(css=C)\n', {"banned-keyword"}, id="name bound twice"),
    pytest.param(
        'C = ["inline:a"]\nC.append("fi" + "le:///x")\nc2 = pygal.Bar(css=C)\n', {"banned-keyword"}, id="list mutated"
    ),
    pytest.param('c2 = pygal.Bar(defs=["<x/>"])\n', {"banned-keyword"}, id="defs"),
    pytest.param('chart.defs = ["<x/>"]\n', {"banned-attribute"}, id="defs attribute"),
    pytest.param('chart.css = ["fi" + "le:///x"]\n', {"banned-keyword"}, id="attribute with a built entry"),
    pytest.param('chart.css += ["fi" + "le:///x"]\n', {"banned-attribute"}, id="augmented"),
    pytest.param('chart.css.append("inline:a")\n', {"banned-attribute"}, id="mutator"),
    pytest.param('chart.css[0] = "inline:a"\n', {"banned-attribute"}, id="item store"),
    pytest.param("c = chart.css\n", {"banned-attribute"}, id="read"),
    pytest.param("del chart.js\n", {"banned-attribute"}, id="delete"),
    pytest.param("chart.js, n = [], 1\n", {"banned-attribute"}, id="unpacked target"),
    pytest.param('o = {}\no["c" + "ss"] = ["x"]\nc2 = pygal.Bar(**o)\n', {"banned-keyword"}, id="** built"),
    pytest.param('c2 = pygal.Bar(**{"css": ["fi" + "le:///x"]})\n', {"banned-keyword"}, id="** literal, bad css"),
    pytest.param('c2 = pygal.Bar(**{"c" + "ss": ["x"]})\n', {"banned-keyword"}, id="** built key"),
    pytest.param('O = {"width": 800}\nO["js"] = ["x"]\nc2 = pygal.Bar(**O)\n', {"banned-keyword"}, id="** mutated"),
    pytest.param('c2 = pygal.Bar(**{**{"js": []}})\n', {"banned-keyword"}, id="** nested unpacking"),
    pytest.param('cfg = pygal.Config(js=["x.js"])\n', {"banned-keyword"}, id="Config"),
    pytest.param('c2 = chart(css=["x.css"])\n', {"banned-keyword"}, id="a chart called with options"),
    pytest.param('s = Style(font_family="googlefont:Roboto")\n', {"url-literal"}, id="Google font"),
    pytest.param('f = "Roboto"\ns = Style(title_font_family=f"googlefont:{f}")\n', {"url-literal"}, id="font f-string"),
    pytest.param('s = "file://style.css"\n', {"url-literal"}, id="a package stylesheet outside a css list"),
]
PYGAL_CONFIG_SIBLINGS = [
    pytest.param("c2 = pygal.Bar(js=())\n", id="js empty tuple"),
    pytest.param('c2 = pygal.Bar(js=[], css=["inline:.a { fill: red; }"])\n', id="inline css"),
    pytest.param(
        'CSS = ("file://style.css", "file://graph.css", "inline:.a { fill: red; }")\n'
        "c2 = pygal.Bar(js=[], css=CSS)\nc3 = pygal.Line(css=CSS)\n",
        id="a css list bound once",
    ),
    pytest.param(
        'EXTRA = "inline:.b { opacity: .5; }"\nc2 = pygal.Bar(css=["file://base.css", EXTRA])\n',
        id="an entry bound once",
    ),
    pytest.param('x = 2\nc2 = pygal.Bar(css=[f"inline:.a {{ stroke-width: {x}; }}"])\n', id="inline f-string"),
    pytest.param('chart.css = ["file://style.css", "inline:.c { fill: none; }"]\n', id="css attribute"),
    pytest.param("chart.js = []\n", id="js attribute"),
    pytest.param(
        'OPTIONS = {"width": 3200, "height": 1800, "js": []}\nc2 = pygal.Bar(**OPTIONS, title="")\n'
        "c3 = pygal.Line(**OPTIONS)\n",
        id="** a dict bound once",
    ),
    pytest.param('c2 = pygal.Bar(**{"show_legend": False})\n', id="** a dict literal"),
]
SVG_NAMESPACE_LOOKALIKES = [
    pytest.param("http://www.w3.org/2000/svgevil.example/x", id="name continued"),
    pytest.param("http://www.w3.org/2000/svg/../x", id="path continued"),
    pytest.param("http://www.w3.org/2000/svg http://evil.example", id="a second URL"),
    pytest.param("https://www.w3.org/2000/svg", id="https"),
    pytest.param("HTTP://WWW.W3.ORG/2000/SVG", id="upper case"),
    pytest.param("{http://www.w3.org/2000/svg.x}a", id="Clark name continued"),
    pytest.param("http://www.w3.org/1999/xlinks", id="xlink continued"),
]


class TestPygalProfile:
    """pygal: pygal and cairosvg only, a PNG and an HTML save, pygal's config and its SVG namespaces."""

    def test_minimal_file_has_no_findings(self) -> None:
        assert validate_security(pygal_plot(), library="pygal") == []

    @pytest.mark.parametrize(
        "body",
        [
            "import cairosvg\n",
            "from cairosvg import svg2png\n",
            "import pygal.style\n",
            "from pygal import formatters\n",
            "import numpy as np\n",
            "from scipy import stats\n",
        ],
    )
    def test_allowed_import(self, body: str) -> None:
        assert rules_of(pygal_plot(body), "pygal") == set()

    @pytest.mark.parametrize(
        "body",
        [
            "import xml.etree.ElementTree as ET\n",
            "from xml.etree import ElementTree\n",
            "from PIL import Image\n",
            "import io\n",
            "import cairocffi\n",
            "import cssselect2\n",
            "import matplotlib.colors\n",
            "import pygal.etree\n",
            "import cairosvg.url as url\n",
            "from pygal_maps_world.maps import World\n",
            "import lets_plot\n",
        ],
    )
    def test_banned_import(self, body: str) -> None:
        assert "banned-import" in rules_of(pygal_plot(body), "pygal")

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            pytest.param(PYGAL_PNG_SAVE, 'chart.render_to_png(filename=f"plot-{THEME}.png", dpi=96)', id="filename="),
            pytest.param(PYGAL_PNG_SAVE, "import cairosvg\n" + SVG2PNG, id="svg2png"),
            pytest.param(
                PYGAL_PNG_SAVE,
                "import cairosvg\n"
                'cairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", output_width=3200, '
                "output_height=1800, dpi=96, scale=1, background_color=PAGE_BG)",
                id="svg2png sized",
            ),
            pytest.param(
                PYGAL_PNG_SAVE,
                'from cairosvg import svg2png\nsvg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png")',
                id="svg2png imported",
            ),
            pytest.param(PYGAL_HTML_SAVE, 'chart.render_to_file(filename=f"plot-{THEME}.html")', id="HTML filename="),
            pytest.param(PYGAL_HTML_SAVE, "", id="no HTML"),
        ],
    )
    def test_save_passes(self, old: str, new: str) -> None:
        assert validate_security(swapped(pygal_plot(), old, new), library="pygal") == []

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            pytest.param(PYGAL_PNG_SAVE, 'chart.render_to_png("plot.png")', id="other file"),
            pytest.param(PYGAL_PNG_SAVE, 'chart.render_to_png(f"plot-{THEME}.svg")', id="other type"),
            pytest.param(PYGAL_PNG_SAVE, 'chart.render_to_png(f"plot-{THEME}.png", 300)', id="dpi by position"),
            pytest.param(PYGAL_PNG_SAVE, 'chart.render_to_png(f"plot-{THEME}.png", width=800)', id="chart options"),
            pytest.param(PYGAL_PNG_SAVE, 'chart.render_to_png(f"plot-{THEME}.png", **{})', id="unpacked keywords"),
            pytest.param(PYGAL_PNG_SAVE, "data = chart.render_to_png()\n" + PYGAL_PNG_SAVE, id="bytes, no file"),
            pytest.param(PYGAL_HTML_SAVE, 'chart.render_to_file(f"plot-{THEME}.svg")', id="SVG file"),
            pytest.param(PYGAL_HTML_SAVE, 'chart.render_to_file(f"plot-{THEME}.html", pretty_print=True)', id="opts"),
            pytest.param(
                PYGAL_PNG_SAVE,
                'import cairosvg\ncairosvg.svg2png(chart.render(), write_to=f"plot-{THEME}.png")',
                id="svg2png by position",
            ),
            pytest.param(
                PYGAL_PNG_SAVE, "import cairosvg\ncairosvg.svg2png(bytestring=chart.render())", id="svg2png bytes"
            ),
            pytest.param(
                PYGAL_PNG_SAVE,
                "import cairosvg\ncairosvg.svg2png(bytestring=chart.render(), write_to=handle)",
                id="svg2png into a file object",
            ),
            pytest.param(
                PYGAL_PNG_SAVE,
                'import cairosvg\ncairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png", parent=1)',
                id="svg2png keyword it does not list",
            ),
        ],
    )
    def test_other_save_is_a_finding(self, old: str, new: str) -> None:
        assert rules_of(swapped(pygal_plot(), old, new), "pygal") == {"savefig-target"}

    def test_svg2png_takes_no_positional(self) -> None:
        new = 'import cairosvg\ncairosvg.svg2png(chart.render(), write_to=f"plot-{THEME}.png")'
        findings = validate_security(swapped(pygal_plot(), PYGAL_PNG_SAVE, new), library="pygal")
        assert [f.message for f in findings] == ["svg2png takes every argument by keyword"]

    @pytest.mark.parametrize("keyword", ['url="plot.svg"', "file_obj=handle", "unsafe=True", "url_fetcher=fetcher"])
    def test_svg2png_input_keywords_are_refused(self, keyword: str) -> None:
        """`url=` and `file_obj=` read the main input from any path or URL, `unsafe=` and `url_fetcher=` open hrefs."""
        new = f'import cairosvg\ncairosvg.svg2png(bytestring=chart.render(), write_to=f"plot-{{THEME}}.png", {keyword})'
        assert rules_of(swapped(pygal_plot(), PYGAL_PNG_SAVE, new), "pygal") == {"banned-keyword", "savefig-target"}

    def test_a_file_that_saves_no_png_is_a_finding(self) -> None:
        findings = validate_security(swapped(pygal_plot(), PYGAL_PNG_SAVE, ""), library="pygal")
        assert [(f.rule, f.message, f.line) for f in findings] == [("savefig-target", NO_PNG_SAVE, None)]

    @pytest.mark.parametrize(("place", "right", "wrong", "message"), PYGAL_FILE_TYPES)
    def test_a_save_name_writes_only_its_own_file_type(self, place: str, right: str, wrong: str, message: str) -> None:
        code = swapped(pygal_plot(), place, right)
        assert validate_security(code, library="pygal") == []
        wrong_code = swapped(code, PYGAL_HTML_SAVE, wrong)
        findings = validate_security(wrong_code, library="pygal")
        line = wrong_code.splitlines().index(wrong) + 1
        assert [(f.rule, f.message, f.line) for f in findings] == [("savefig-target", message, line)]

    def test_svg_text_in_the_png_is_no_png_save(self) -> None:
        """`render_to_file` writes SVG text, so a file whose one PNG save is `render_to_file` writes no PNG."""
        new = 'chart.render_to_file(f"plot-{THEME}.png")'
        findings = validate_security(swapped(pygal_plot(), PYGAL_PNG_SAVE, new), library="pygal")
        assert [(f.rule, f.message) for f in findings] == [
            ("savefig-target", 'render_to_file writes only f"plot-{THEME}.html"'),
            ("savefig-target", NO_PNG_SAVE),
        ]

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("import matplotlib.pyplot as plt\nplt.savefig(f'plot-{THEME}.png')\n", {"banned-import", "banned-call"}),
            ("canvas.save(f'plot-{THEME}.png')\n", {"banned-call"}),
        ],
    )
    def test_other_libraries_saves_are_banned_calls(self, body: str, expected: set[str]) -> None:
        """PIL's `.save` pads the PNG in 13 catalogue files; with pygal it is no save of the plot."""
        findings = validate_security(pygal_plot(body), library="pygal")
        assert {f.rule for f in findings} == expected
        assert any(f.message.endswith("; the plot is saved with save") for f in findings if f.rule == "banned-call")

    @pytest.mark.parametrize(("body", "expected"), PYGAL_ROUTES)
    def test_route_is_refused(self, body: str, expected: set[str]) -> None:
        assert rules_of(pygal_plot(body), "pygal") == expected

    @pytest.mark.parametrize("body", PYGAL_NEAR_ROUTES)
    def test_nearest_allowed_sibling_passes(self, body: str) -> None:
        assert rules_of(pygal_plot(body), "pygal") == set()

    @pytest.mark.parametrize(("body", "expected"), PYGAL_CONFIG_ROUTES)
    def test_config_that_reads_fetches_or_changes_later_is_refused(self, body: str, expected: set[str]) -> None:
        assert rules_of(pygal_plot(body), "pygal") == expected

    @pytest.mark.parametrize("body", PYGAL_CONFIG_SIBLINGS)
    def test_config_the_rule_can_read_passes(self, body: str) -> None:
        assert rules_of(pygal_plot(body), "pygal") == set()

    def test_svg_namespaces_pass_in_pygal_only(self) -> None:
        body = (
            'NS = {"svg": "http://www.w3.org/2000/svg", "xlink": "http://www.w3.org/1999/xlink"}\n'
            'TAG = "{http://www.w3.org/2000/svg}rect"\n'
            "MARKUP = '<svg xmlns=\"http://www.w3.org/2000/svg\"/>'\n"
        )
        assert rules_of(pygal_plot(body), "pygal") == set()
        assert rules_of(library_plot("matplotlib", body), "matplotlib") == {"url-literal"}

    @pytest.mark.parametrize("text", SVG_NAMESPACE_LOOKALIKES)
    def test_a_namespace_lookalike_is_a_url(self, text: str) -> None:
        assert rules_of(pygal_plot(f"u = {text!r}\n"), "pygal") == {"url-literal"}

    def test_cut_is_pandas_with_the_other_libraries(self) -> None:
        """`cut` is banned in pygal's profile only: `pygal.util.cut` is a getattr by string, `pd.cut` bins values."""
        body = 'bins = pd.cut(df["a"], 3)\n'
        assert rules_of(library_plot("matplotlib", body), "matplotlib") == set()
        assert rules_of(pygal_plot("import pandas as pd\n" + body), "pygal") == {"banned-attribute"}


LETSPLOT_ROUTES = [
    pytest.param('plot.to_png("x.png")\n', {"banned-attribute"}, id="to_png"),
    pytest.param('plot.to_svg("x.svg")\n', {"banned-attribute"}, id="to_svg"),
    pytest.param('plot.to_pdf("x.pdf")\n', {"banned-attribute"}, id="to_pdf"),
    pytest.param('plot.to_html("x.html")\n', {"banned-call"}, id="to_html"),
    pytest.param("plot.show()\n", {"banned-attribute"}, id="show"),
    pytest.param("p = geom_point().props()\n", {"banned-attribute"}, id="props hands out the spec dict"),
    pytest.param('LetsPlot.setup_show_ext(exec="sh -c id")\n', {"banned-attribute", "banned-call"}, id="browser"),
    pytest.param('LetsPlot.set({"js_url_manual": "x"})\n', {"banned-attribute", "banned-call"}, id="LetsPlot.set"),
    pytest.param("LetsPlot.set_theme(None)\n", {"banned-call"}, id="another LetsPlot method"),
    pytest.param("LetsPlot.setup_html(offline=True)\n", {"banned-call"}, id="setup_html with arguments"),
    pytest.param("lp = LetsPlot\n", {"banned-call"}, id="LetsPlot as a value"),
    pytest.param("import lets_plot\n[lets_plot.LetsPlot][0].set({})\n", {"banned-call"}, id="LetsPlot in a list"),
    pytest.param("import lets_plot\nc = lets_plot.cfg\n", {"banned-attribute"}, id="cfg"),
    pytest.param("from lets_plot import cfg\n", {"banned-attribute"}, id="from lets_plot import cfg"),
    pytest.param(
        'import lets_plot.plot.core as core\nm = core.LazyModule("subprocess")\n', {"banned-attribute"}, id="LazyModule"
    ),
    pytest.param(
        'import lets_plot.plot.geom_imshow_ as gi\nr = gi.png.Reader(filename="x")\n',
        {"banned-attribute"},
        id="png proxy",
    ),
    pytest.param(
        "import lets_plot.plot.geom_imshow_ as gi\np = gi.palettable\n", {"banned-attribute"}, id="palettable"
    ),
    pytest.param("import lets_plot.plot.geom as g\np = g.geopandas\n", {"banned-attribute"}, id="geopandas proxy"),
    pytest.param("import lets_plot\np = lets_plot.extend_path\n", {"banned-attribute"}, id="pkgutil.extend_path"),
    pytest.param("from lets_plot import geom_livemap\n", {"banned-attribute"}, id="livemap"),
    pytest.param("from lets_plot import maptiles_zxy\n", {"banned-attribute"}, id="map tiles"),
    pytest.param("import lets_plot\ng = lets_plot.geo_data\n", {"banned-attribute"}, id="geo_data by attribute"),
]
LETSPLOT_NEAR_ROUTES = [
    pytest.param('from lets_plot import scale_y_continuous\ns = scale_y_continuous(format="{.0f} %")\n', id="format="),
    pytest.param(
        'from lets_plot import layer_labels\nl = layer_labels().line("@a").format("@a", "d").size(10)\n', id="labels"
    ),
    pytest.param(
        'from lets_plot import smooth_labels\nl = smooth_labels().eq(lhs="y").format("^R2", ".2f").label_x("left")\n',
        id="smooth labels",
    ),
    pytest.param(
        't = layer_tooltips(["a"]).format(field="@a", format=".0f").title("x").anchor("top_right").min_width(50)\n',
        id="tooltips by keyword",
    ),
    pytest.param("d = layer_tooltips().as_dict()\n", id="as_dict"),
    pytest.param('from lets_plot.mapping import as_discrete\nm = as_discrete("a")\n', id="mapping"),
    pytest.param("from lets_plot import gggrid\ng = gggrid([ggplot(df)])\n", id="gggrid"),
]
LETSPLOT_FORMAT_ROUTES = [
    pytest.param('t = "{0}".format(1)\n', id="a string's format"),
    pytest.param('tt = layer_tooltips()\nt = tt.format("@a", ".1f")\n', id="a builder bound to a name"),
    pytest.param('layer_tooltips = str\nt = layer_tooltips("{0}").format("@a")\n', id="the builder name rebound"),
    pytest.param(
        'match str:\n    case layer_tooltips:\n        pass\nt = layer_tooltips("{0}").format("@a")\n',
        id="match capture",
    ),
    pytest.param('def f(layer_tooltips):\n    return layer_tooltips("{0}").format("@a")\n', id="parameter"),
    pytest.param(
        'import lets_plot\nlets_plot.layer_tooltips = str\nt = layer_tooltips("{0}").format("@a")\n',
        id="the library's attribute replaced",
    ),
    pytest.param('v = "@a"\nt = layer_tooltips().format(v, ".1f")\n', id="a non-literal argument"),
    pytest.param('t = layer_tooltips().format(*["@a"])\n', id="starred"),
    pytest.param('t = layer_tooltips().format("@a", spec=".1f")\n', id="another keyword"),
    pytest.param('t = layer_tooltips().as_dict().format("a")\n', id="as_dict in the chain"),
    pytest.param('t = layer_tooltips().line("@a").upper().format("a")\n', id="a method outside the builder's"),
    pytest.param('import lets_plot as lp\nt = lp.layer_tooltips().format("@a")\n', id="through the module"),
    pytest.param(
        'from lets_plot.plot.tooltip import layer_tooltips as lt\nt = lt().format("@a")\n', id="another import path"
    ),
    pytest.param('f = layer_tooltips().format\nt = f("@a")\n', id="not called"),
]


class TestLetsplotProfile:
    """lets-plot: lets_plot only, `ggsave` into `.`, `LetsPlot.setup_html()`, the builders' `.format`."""

    def test_minimal_file_has_no_findings(self) -> None:
        assert validate_security(letsplot_plot(), library="letsplot") == []

    @pytest.mark.parametrize(
        "body",
        [
            "import lets_plot\n",
            "from lets_plot import ggsave\n",
            "from lets_plot.mapping import as_discrete\n",
            "from lets_plot.bistro.corr import corr_plot\n",
            "import numpy as np\n",
            "from scipy import stats\n",
        ],
    )
    def test_allowed_import(self, body: str) -> None:
        assert rules_of(letsplot_plot(body), "letsplot") == set()

    @pytest.mark.parametrize(
        "body",
        [
            "from lets_plot.geo_data import geocode_countries\n",
            "import lets_plot.geo_data\n",
            "from lets_plot import tilesets\n",
            "import lets_plot.settings_utils\n",
            "import lets_plot.frontend_context\n",
            "from lets_plot.plot.geom_livemap_ import geom_livemap\n",
            "import matplotlib.pyplot as plt\n",
            "from PIL import Image\n",
            "import shutil\n",
            "import pygal\n",
        ],
    )
    def test_banned_import(self, body: str) -> None:
        assert "banned-import" in rules_of(letsplot_plot(body), "letsplot")

    def test_star_import_is_refused(self) -> None:
        """The normaliser expands `from lets_plot import *` (151 catalogue files); left in, it is a finding."""
        assert rules_of(letsplot_plot("from lets_plot import *\n"), "letsplot") == {"star-import"}

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            pytest.param(
                LETSPLOT_PNG_SAVE, 'ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)', id="file="
            ),
            pytest.param(
                LETSPLOT_PNG_SAVE,
                'ggsave(plot, f"plot-{THEME}.png", path=".", w=3200, h=1800, unit="px", dpi=96)',
                id="pixel size",
            ),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", path=".")', id="no scale"),
            pytest.param(LETSPLOT_HTML_SAVE, 'ggsave(plot, filename=f"plot-{THEME}.html", path=".")', id="HTML file="),
            pytest.param(LETSPLOT_HTML_SAVE, "", id="no HTML"),
        ],
    )
    def test_save_passes(self, old: str, new: str) -> None:
        assert validate_security(swapped(letsplot_plot(), old, new), library="letsplot") == []

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", scale=2)', id="no path"),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", path="/tmp")', id="another path"),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", path=str(d))', id="computed path"),
            pytest.param(LETSPLOT_HTML_SAVE, 'ggsave(plot, f"plot-{THEME}.html")', id="HTML without a path"),
            pytest.param(LETSPLOT_HTML_SAVE, 'ggsave(plot, f"plot-{THEME}.svg", path=".")', id="SVG"),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, "plot.png", path=".")', id="old-form file"),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", ".")', id="path by position"),
            pytest.param(LETSPLOT_HTML_SAVE, 'ggsave(plot, f"plot-{THEME}.html", path=".", iframe=False)', id="if"),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", **{"path": "."})', id="unpacked"),
            pytest.param(LETSPLOT_PNG_SAVE, 'ggsave(plot=plot, filename=f"plot-{THEME}.png", path=".")', id="plot="),
        ],
    )
    def test_other_save_is_a_finding(self, old: str, new: str) -> None:
        assert rules_of(swapped(letsplot_plot(), old, new), "letsplot") == {"savefig-target"}

    def test_a_save_without_the_directory_names_it(self) -> None:
        """Without `path=`, lets-plot creates `./lets-plot-images` and writes there (the render guard refuses it)."""
        code = swapped(letsplot_plot(), LETSPLOT_PNG_SAVE, 'ggsave(plot, f"plot-{THEME}.png", scale=2)')
        assert [f.message for f in validate_security(code, library="letsplot")] == ['ggsave must save with path="."']

    def test_a_file_that_saves_no_png_is_a_finding(self) -> None:
        findings = validate_security(swapped(letsplot_plot(), LETSPLOT_PNG_SAVE, ""), library="letsplot")
        assert [(f.rule, f.message, f.line) for f in findings] == [("savefig-target", NO_PNG_SAVE, None)]

    @pytest.mark.parametrize(("body", "expected"), LETSPLOT_ROUTES)
    def test_route_is_refused(self, body: str, expected: set[str]) -> None:
        assert rules_of(letsplot_plot(body), "letsplot") == expected

    @pytest.mark.parametrize("body", LETSPLOT_NEAR_ROUTES)
    def test_nearest_allowed_sibling_passes(self, body: str) -> None:
        assert rules_of(letsplot_plot(body), "letsplot") == set()

    @pytest.mark.parametrize("body", LETSPLOT_FORMAT_ROUTES)
    def test_format_outside_a_builder_chain_is_refused(self, body: str) -> None:
        findings = validate_security(letsplot_plot(body), library="letsplot")
        assert ("banned-attribute", "attribute '.format' is not allowed") in {(f.rule, f.message) for f in findings}

    def test_a_dunder_in_a_builder_format_still_fails(self) -> None:
        body = 't = layer_tooltips().format("@a", "{0.__class__}")\n'
        assert rules_of(letsplot_plot(body), "letsplot") == {"dunder"}

    def test_the_builder_exemption_is_lets_plots(self) -> None:
        """In another profile the same chain is an ordinary `.format`."""
        body = 'from plotnine import labs as layer_tooltips\nt = layer_tooltips().format("@a", ".1f")\n'
        assert "banned-attribute" in rules_of(plotnine_plot(body), "plotnine")


# The save rule finds a save by its callee's name, so a save reached under another name escapes it: open in the 1b
# plotnine profile (the lets-plot draft of 2026-10-26, alias_probe.py). One save name per profile, its import and
# a call that writes elsewhere.
SAVE_NAME_CASES = [
    pytest.param("plotnine", "from plotnine import ggsave\n", "ggsave", 'plot, "/tmp/x.pdf"', id="plotnine"),
    pytest.param(
        "pygal", "from cairosvg import svg2png\n", "svg2png", 'bytestring=b"", write_to="/tmp/x.png"', id="pygal"
    ),
    pytest.param("letsplot", "", "ggsave", 'plot, "/tmp/x.pdf", path="/tmp"', id="letsplot"),
]
SAVE_NAME_ROUTES = [
    pytest.param("from {module} import {name} as keep\nkeep({args})\n", {"banned-call"}, id="imported as"),
    pytest.param("from textwrap import dedent as {name}\n", {"banned-call"}, id="imported under a save name"),
    pytest.param("g = {name}\ng({args})\n", {"banned-call"}, id="assigned"),
    pytest.param("[{name}][0]({args})\n", {"banned-call"}, id="in a list"),
    pytest.param("import functools\nfunctools.partial({name})({args})\n", {"banned-call"}, id="partial"),
    # The wrapper calls the save where it is named, so the save rule sees its starred target (pygal's profile also
    # refuses a `**k` it cannot read, so the wrapper forwards positionals only).
    pytest.param("w = lambda *a: {name}(*a)\nw({args})\n", {"savefig-target"}, id="lambda wrapper"),
    pytest.param("g = getattr(df, '{name}')\n", {"banned-name"}, id="getattr"),
]


@pytest.mark.parametrize(("library", "imports", "name", "args"), SAVE_NAME_CASES)
@pytest.mark.parametrize(("template", "expected"), SAVE_NAME_ROUTES)
def test_a_save_reached_under_another_name_is_refused(
    library: str, imports: str, name: str, args: str, template: str, expected: set[str]
) -> None:
    module = {"plotnine": "plotnine", "pygal": "cairosvg", "letsplot": "lets_plot.export"}[library]
    body = imports + template.format(module=module, name=name, args=args)
    assert rules_of(library_plot(library, body), library) == expected


@pytest.mark.parametrize(
    ("library", "body"),
    [
        pytest.param("plotnine", "from plotnine import ggsave as ggsave\n", id="plotnine, imported as itself"),
        pytest.param(
            "pygal",
            'from cairosvg import svg2png\nsvg2png(bytestring=chart.render(), write_to=f"plot-{THEME}.png")\n',
            id="pygal, called where named",
        ),
        pytest.param("letsplot", "from lets_plot import ggsave\n", id="letsplot, imported twice under its name"),
    ],
)
def test_a_save_name_under_its_own_name_passes(library: str, body: str) -> None:
    assert rules_of(library_plot(library, body), library) == set()


def test_a_save_name_in_a_plotnine_expression_is_refused() -> None:
    """plotnine evaluates the string in the plot's namespace, where `ggsave` is bound."""
    body = "from plotnine import ggsave\nm = aes(x=\"(lambda g: g(df, '/tmp/x.pdf'))(ggsave)\")\n"
    findings = validate_security(plotnine_plot(body), library="plotnine")
    assert [(f.rule, f.message) for f in findings] == [
        ("banned-call", "in the aes expression: 'ggsave' may only be called directly")
    ]


LIBRARY_ROOTS = {"altair": "altair", "pygal": "pygal", "letsplot": "lets_plot"}


@pytest.mark.parametrize(
    ("library", "name"), [(library, name) for library, names in sorted(LIBRARY_BANS.items()) for name in sorted(names)]
)
def test_a_library_ban_is_refused_on_any_receiver_and_as_an_import(library: str, name: str) -> None:
    for body in (f"x = obj.{name}\n", f"from {LIBRARY_ROOTS[library]} import {name}\n"):
        assert rules_of(library_plot(library, body), library) == {"banned-attribute"}, body


LETSPLOT_HELPERS = (
    "to_png to_svg to_pdf setup_show_ext WebBrHtmlPageContext LazyModule geom_livemap maptiles_zxy maptiles_lets_plot "
    "maptiles_solid maptiles_chessboard geocoding_service geocode geocode_cities geocode_counties geocode_states "
    "geocode_countries reverse_geocode get_geocodes get_centroids get_boundaries get_limits extend_path".split()
)


@pytest.mark.parametrize("library", ["letsplot", "matplotlib"])
@pytest.mark.parametrize("name", LETSPLOT_HELPERS)
def test_a_lets_plot_helper_is_refused_in_every_profile(library: str, name: str) -> None:
    """No catalogue file of another library uses these names, so they are banned everywhere (`UNSAFE_HELPERS`)."""
    assert rules_of(library_plot(library, f"x = obj.{name}\n"), library) == {"banned-attribute"}


def test_a_save_name_as_a_value_is_refused_in_plot_and_data_code() -> None:
    findings = validate_security(plot("s = savefig\n"), library="matplotlib")
    assert [(f.rule, f.message) for f in findings] == [("banned-call", "'savefig' may only be called directly")]
    assert ("banned-call", "'savefig' may only be called directly") in {
        (f.rule, f.message) for f in validate_data_code("import pandas as pd\ns = savefig\ndf = pd.DataFrame()\n")
    }


# `np.save` shares its name with the `save` of plotnine and altair: the save rule resolves the receiver, and a
# module outside the plotting library is never the plot's save (finding of the 1b review, 2026-10-25).
@pytest.mark.parametrize("library", CODE_LIBRARIES)
@pytest.mark.parametrize(
    "body",
    [
        pytest.param("import numpy as np\nnp.save('x.npy', df)\n", id="np.save"),
        pytest.param("import numpy as np\nnp.save(f'plot-{THEME}.png', df)\n", id="np.save on the plot's file"),
        pytest.param("from numpy import save\n", id="from numpy import save"),
    ],
)
def test_numpy_save_is_a_banned_call_in_every_profile(library: str, body: str) -> None:
    assert "banned-call" in rules_of(library_plot(library, body), library)


# THEME names every save's file, and libcairo writes pygal's PNG where the render guard never looks, so in every
# profile the name keeps the theme block's value (the security review of 2026-10-26): a body that binds THEME, the
# 1-based line of the binding in it, and the other rules the body breaks.
THEME_BINDINGS = [
    pytest.param('THEME = "../x"\n', 1, set(), id="a second assignment"),
    pytest.param('THEME = os.getenv("ANYPLOT_THEME", "dark")\n', 1, set(), id="the theme block twice"),
    pytest.param('THEME += "x"\n', 1, set(), id="augmented"),
    pytest.param('THEME: str = "x"\n', 1, set(), id="annotated"),
    pytest.param('THEME, n = "x", 1\n', 1, set(), id="unpacked"),
    pytest.param('for THEME in ["x"]:\n    pass\n', 1, set(), id="for"),
    pytest.param("import warnings\nwith warnings.catch_warnings() as THEME:\n    pass\n", 2, set(), id="with"),
    pytest.param("try:\n    pass\nexcept ValueError as THEME:\n    pass\n", 3, set(), id="except"),
    pytest.param('match "x":\n    case THEME:\n        pass\n', 2, set(), id="match capture"),
    pytest.param('match ["x"]:\n    case [*THEME]:\n        pass\n', 2, set(), id="match star"),
    pytest.param("match {}:\n    case {**THEME}:\n        pass\n", 2, set(), id="match rest"),
    pytest.param('n = (THEME := "x")\n', 1, set(), id="walrus"),
    pytest.param('names = [THEME for THEME in ["x"]]\n', 1, set(), id="comprehension"),
    pytest.param("from textwrap import dedent as THEME\n", 1, set(), id="from import"),
    pytest.param("import textwrap as THEME\n", 1, {"module-value"}, id="import"),
    pytest.param('def THEME():\n    return "x"\n', 1, set(), id="def"),
    pytest.param('def f(THEME="x"):\n    return THEME\n', 1, set(), id="parameter"),
    pytest.param("f = lambda THEME: THEME\n", 1, set(), id="lambda parameter"),
    pytest.param('def f():\n    THEME = "x"\n    return THEME\n', 2, set(), id="a local"),
    pytest.param("def f():\n    global THEME\n", 2, {"banned-statement"}, id="global"),
    pytest.param(
        'def f():\n    THEME = "x"\n\n    def g():\n        nonlocal THEME\n', 5, {"banned-statement"}, id="nonlocal"
    ),
    pytest.param("del THEME\n", 1, set(), id="del"),
    pytest.param("type THEME = str\n", 1, set(), id="type alias"),
    pytest.param("def f[THEME]():\n    pass\n", 1, set(), id="type parameter"),
]
THEME_READS = [
    pytest.param("upper = THEME.upper()\n", id="a read"),
    pytest.param("def f(theme=THEME):\n    return theme\n", id="a default"),
    pytest.param('d = dict(THEME="x")\n', id="a keyword"),
    pytest.param('labels = {"THEME": THEME}\n', id="a dict key"),
    pytest.param('THEME_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"\n', id="another name"),
]
# With `import os`, the name is bound by nothing else: each of these hands the theme block another object's `getenv`.
OS_BINDINGS = [
    pytest.param(
        'import functools\n\n\ndef g():\n    pass\n\n\ng.getenv = lambda *a: "../x"\n\n\n'
        '@functools.wraps(g, assigned=("getenv",), updated=())\ndef os():\n    pass\n',
        12,
        id="def under wraps",
    ),
    pytest.param("from textwrap import dedent as os\n", 1, id="from import"),
    pytest.param("import textwrap as os\n", 1, id="import"),
    pytest.param("try:\n    pass\nexcept ValueError as os:\n    pass\n", 3, id="except"),
    pytest.param("def f(os):\n    return 1\n", 1, id="parameter"),
    pytest.param('match "x":\n    case os:\n        pass\n', 2, id="match capture"),
]


def body_line(code: str, body: str, line: int) -> int:
    """The line of `code` that is line `line` of `body`, which `code` holds once."""
    assert code.count(body) == 1, body
    return code.count("\n", 0, code.index(body)) + line


@pytest.mark.parametrize("library", CODE_LIBRARIES)
@pytest.mark.parametrize(("body", "line", "others"), THEME_BINDINGS)
def test_a_binding_of_theme_is_refused_in_every_profile(library: str, body: str, line: int, others: set[str]) -> None:
    code = library_plot(library, body)
    findings = validate_security(code, library=library)
    assert {f.rule for f in findings} == {"savefig-target"} | others
    assert ("savefig-target", THEME_BINDING_MESSAGE, body_line(code, body, line)) in {
        (f.rule, f.message, f.line) for f in findings
    }


@pytest.mark.parametrize("library", CODE_LIBRARIES)
@pytest.mark.parametrize("body", THEME_READS)
def test_a_read_of_theme_passes_in_every_profile(library: str, body: str) -> None:
    assert rules_of(library_plot(library, body), library) == set()


@pytest.mark.parametrize("library", CODE_LIBRARIES)
@pytest.mark.parametrize(
    "block",
    [
        pytest.param('THEME = os.environ.get("ANYPLOT_THEME", "light")', id="os.environ.get"),
        pytest.param('THEME = os.getenv("ANYPLOT_THEME", "light").lower()', id="a call on the lookup"),
        pytest.param('THEME = T = os.getenv("ANYPLOT_THEME", "light")', id="two targets"),
    ],
)
def test_a_theme_block_of_another_shape_is_a_finding(library: str, block: str) -> None:
    """The theme block is the shape `regions.is_theme_assignment` accepts, which readiness looks for too."""
    code = swapped(library_plot(library), THEME_LINE, block)
    findings = validate_security(code, library=library)
    assert [(f.rule, f.message, f.line) for f in findings] == [
        ("savefig-target", THEME_BINDING_MESSAGE, code.splitlines().index(block) + 1)
    ]


@pytest.mark.parametrize("library", CODE_LIBRARIES)
@pytest.mark.parametrize(
    "block",
    [
        pytest.param('THEME: str = os.getenv("ANYPLOT_THEME", "light")', id="annotated"),
        pytest.param('THEME = os.getenv("ANYPLOT_THEME")', id="no default"),
        pytest.param('THEME = os.getenv("ANYPLOT_THEME", default="light")', id="default by keyword"),
    ],
)
def test_a_theme_block_regions_accepts_passes(library: str, block: str) -> None:
    assert rules_of(swapped(library_plot(library), THEME_LINE, block), library) == set()


@pytest.mark.parametrize("library", CODE_LIBRARIES)
def test_the_theme_block_reads_the_imported_os(library: str) -> None:
    """Without `import os`, `os` is a name the file binds, and its `getenv` returns what the file says."""
    code = swapped(library_plot(library, "def os():\n    pass\n"), "import os\n", "")
    findings = validate_security(code, library=library)
    assert [(f.rule, f.message, f.line) for f in findings] == [
        ("savefig-target", THEME_BINDING_MESSAGE, code.splitlines().index(THEME_LINE) + 1)
    ]


@pytest.mark.parametrize("library", CODE_LIBRARIES)
@pytest.mark.parametrize(("body", "line"), OS_BINDINGS)
def test_a_binding_of_the_imported_os_is_refused(library: str, body: str, line: int) -> None:
    code = library_plot(library, body)
    findings = validate_security(code, library=library)
    assert [(f.rule, f.message, f.line) for f in findings] == [
        ("os-use", "'os' may only be bound by import os", body_line(code, body, line))
    ]


def test_data_code_may_bind_theme() -> None:
    """A data snippet saves nothing, so the THEME pin, a `savefig-target` rule, is no rule of the DATA profile."""
    assert validate_data_code('import pandas as pd\nTHEME = "x"\nTHEME = "y"\ndf = pd.DataFrame()\n') == []


# --- the catalogue corpus ----------------------------------------------------------------------


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is absent")
@pytest.mark.parametrize("path", CATALOGUE_FILES, ids=lambda p: f"{p.parts[-4]}/{p.stem}")
def test_catalogue_file_never_raises(path: Path) -> None:
    """The catalogue is not clean by design; the validator must still finish, fast, with sound findings.

    "Fast" is the process's CPU time, not the wall clock: a file takes under 10 ms, and a busy CI runner once
    stalled a worker for 1.2 s of wall time on one of them (#12456), while a pathological validator burns CPU.
    """
    started = time.process_time()
    findings = validate_security(path.read_text(encoding="utf-8"), library=path.stem)
    assert time.process_time() - started < 1.0
    for finding in findings:
        assert finding.rule and "\n" not in finding.message and len(finding.message) <= 300
        assert finding.line is None or finding.line >= 1


@pytest.mark.skipif(not CATALOGUE_FILES, reason="plots/ is absent")
def test_catalogue_summary() -> None:
    """Per-rule finding counts over the corpus, one block per library with a profile; visible with `pytest -s`.
    The bound is CPU time, as in `test_catalogue_file_never_raises`."""
    started = time.process_time()
    lines = []
    for library in CODE_LIBRARIES:
        files = [path for path in CATALOGUE_FILES if path.stem == library]
        findings_per_rule: Counter[str] = Counter()
        files_per_rule: Counter[str] = Counter()
        clean = 0
        for path in files:
            findings = validate_security(path.read_text(encoding="utf-8"), library=library)
            clean += not findings
            findings_per_rule.update(finding.rule for finding in findings)
            files_per_rule.update({finding.rule for finding in findings})
        lines.append(f"{library}: {len(files)} files, {clean} clean under SECURITY")
        for rule, count in findings_per_rule.most_common():
            lines.append(f"  {rule:<18} {count:>5} findings in {files_per_rule[rule]:>4} files")
    elapsed = time.process_time() - started
    print("\n" + "\n".join(lines) + f"\n({elapsed:.2f}s CPU)")
    assert elapsed < 20.0
