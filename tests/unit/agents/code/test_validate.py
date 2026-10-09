"""Tests for agents/anyplot/code/validate.py.

Three corpora: every rule with a failing snippet and its nearest allowed sibling, every
bypass the design doc names, and the catalogue (never raises, runs under a time budget,
and prints a per-rule summary under `-s`; the catalogue is not clean by design).
"""

import time
from collections import Counter
from pathlib import Path
from typing import get_args

import pytest

from agents.anyplot.code.validate import (
    MAX_LITERAL_NUMBERS,
    MAX_STRING_CHARS,
    PLACEHOLDER,
    Finding,
    Profile,
    validate_adaptation,
    validate_security,
)
from agents.anyplot.schemas import MAX_CODE_CHARS
from core.palette import IMPRINT


REPO_ROOT = Path(__file__).resolve().parents[4]
PLOTS = REPO_ROOT / "plots"
CATALOGUE = sorted(PLOTS.glob("*/implementations/python/matplotlib.py")) + sorted(
    PLOTS.glob("*/implementations/python/seaborn.py")
)

HEADER = """import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

THEME = os.getenv("ANYPLOT_THEME", "light")
df = pd.DataFrame({"a": [1, 2, 3]})
"""
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
        assert get_args(Profile) == ("security", "adaptation")

    def test_finding_is_frozen_and_hashable(self) -> None:
        finding = Finding("banned-name", "'open' is not allowed", 3)
        assert hash(finding) == hash(Finding("banned-name", "'open' is not allowed", 3))
        with pytest.raises(AttributeError):
            finding.rule = "other"  # type: ignore[misc]

    def test_valid_file_has_no_findings_in_either_profile(self) -> None:
        assert validate_security(plot(), library="matplotlib") == []
        assert validate_security(plot("import seaborn as sns\n"), library="seaborn") == []
        assert validate_adaptation(ADAPTED, original_palette=ORIGINAL) == []

    @pytest.mark.parametrize("library", ["plotly", "altair", "ggplot2", "d3"])
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
    "from numpy import random\n",
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
    "import scipy.optimize\n",
    "from scipy import io\n",
    "from scipy import ndimage\n",
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
        assert security_rules("def f():\n    import subprocess\n    return subprocess\n") == {"banned-import"}

    def test_from_import_of_a_banned_function(self) -> None:
        assert security_rules("from numpy import load\n") == {"banned-call"}
        assert security_rules("from pandas import read_csv\n") == {"banned-call"}
        assert security_rules("from matplotlib.pyplot import show\n") == {"banned-attribute"}
        assert security_rules("from numpy import memmap\n") == {"banned-attribute"}
        assert security_rules("from numpy import linspace\n") == set()


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
        code = plot("os = np.ones(3)\ntotal = os.sum()\n").replace("import os\n", "import os as _o\n")
        code = code.replace(
            'THEME = os.getenv("ANYPLOT_THEME", "light")', 'THEME = _o.getenv("ANYPLOT_THEME", "light")'
        )
        assert validate_security(code, library="matplotlib") == []


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


# --- the catalogue corpus ----------------------------------------------------------------------


@pytest.mark.skipif(not CATALOGUE, reason="plots/ is absent")
@pytest.mark.parametrize("path", CATALOGUE, ids=lambda p: f"{p.parts[-4]}/{p.stem}")
def test_catalogue_file_never_raises(path: Path) -> None:
    """The catalogue is not clean by design; the validator must still finish, fast, with sound findings."""
    started = time.perf_counter()
    findings = validate_security(path.read_text(encoding="utf-8"), library=path.stem)
    assert time.perf_counter() - started < 1.0
    for finding in findings:
        assert finding.rule and "\n" not in finding.message and len(finding.message) <= 300
        assert finding.line is None or finding.line >= 1


@pytest.mark.skipif(not CATALOGUE, reason="plots/ is absent")
def test_catalogue_summary() -> None:
    """Per-rule finding counts over the corpus; visible with `pytest -s`."""
    started = time.perf_counter()
    lines = []
    for library in ("matplotlib", "seaborn"):
        files = [path for path in CATALOGUE if path.stem == library]
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
    elapsed = time.perf_counter() - started
    print("\n" + "\n".join(lines) + f"\n({elapsed:.2f}s)")
    assert elapsed < 20.0
