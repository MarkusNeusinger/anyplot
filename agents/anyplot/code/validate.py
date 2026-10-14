"""Two-profile AST validator of the plot pipeline (docs/concepts/agent-network.md, "Adapt and validate").

The SECURITY profile runs on the normalised catalogue original (eligibility) and on every
adapted working form; the ADAPTATION profile runs on adapted code only. Both functions
return an empty list for valid code and never raise on invalid code: a syntax error (also
one only the compiler reports, such as a module-level `return`), an oversize file or a
string that is not UTF-8 text is itself a `Finding`. Only `library` makes
`validate_security` raise `ValueError`: an id outside the catalogue, or a catalogue
library without a profile yet (phase 1 profiles matplotlib and seaborn), because that is
a caller bug, not a property of the code.

The validator is one guardrail layer, not the boundary: the sandbox (no egress, read-only
root, no environment) and the loader substitution are the others. Its job is to make the
adapter's output boring: a fixed import surface, no reflection, no I/O, one data source.

Decisions this module takes where the design leaves room:

* **Import surface.** COMMON plus the science stack (`scipy.{stats, interpolate, signal,
  cluster.hierarchy, spatial, optimize, special, integrate, ndimage, fft, linalg,
  constants}`, `sklearn` without `datasets`, `statsmodels.{api, nonparametric, tsa,
  graphics}`) plus, for matplotlib and seaborn, `matplotlib`, `seaborn` and the bundled
  `mpl_toolkits.{mplot3d, axes_grid1, axisartist}`. The four extra scipy modules,
  `statsmodels.graphics` and the toolkits were admitted after the readiness sweep showed
  them behind most of the catalogue's benign import blocks; each was walked for file or
  network helpers and has none. The pure computing modules of the standard library
  (`warnings`, `typing`, `calendar`, `decimal`, `fractions`, `zoneinfo`, `enum`,
  `dataclasses`, `operator`, `bisect`, `heapq`, `numbers`, `cmath`) and
  `scipy.{fft, linalg, constants}` were admitted by the owner (2026-10-10) for FFTs and
  similar work; the walk behind them is at `COMMON_IMPORTS`, and the names it found are
  banned below. Third-party plotting helpers (cartopy, qrcode, wordcloud,
  matplotlib_venn, squarify, adjustText) stay banned: they are not in the agents image,
  and admitting one is an owner decision, not a validator default. A `banned-import`
  message names the module and what to use instead (`IMPORT_ALTERNATIVES`), and the
  finding carries a label of the path for the attribution log (`Finding.module`): its
  longest prefix in the closed vocabulary `LOGGED_MODULES`, else `?`. An import path
  is code the model wrote, so a path outside the vocabulary (a word from the data
  written as a module name) never reaches the log.
* **Re-exports and private names.** An allowed module can hand out a module the import
  rules keep out (`statistics.sys`, `enum.bltns`, which is `builtins`,
  `dataclasses.inspect`) or a private helper that runs `exec` (`dataclasses._FuncBuilder`).
  So the names in `ESCAPE_ATTRIBUTES` are banned as attributes on any object and as
  `from` imports, and a private name (one leading underscore) is banned on anything an
  import bound, and as a `from` import. Both are banned as a component of an import
  path below its root too, where an alias would hide them from the attribute check
  (`import scipy.fft._backend as backend`). No catalogue file uses either.
* **Exec, process and import-by-name routes through allowed modules** (review of
  2026-10-14: `np.testing.measure("...")` compiled and ran any string). A survey of every
  public function of the allowed packages for `exec`, `eval`, `compile`, `subprocess`,
  sockets, `urlopen`, `import_module` and pickle, and of every module they hand out as an
  attribute, found three kinds of route, each closed structurally. Whole submodules that
  test, build, start programs or import by name (`UNSAFE_SUBMODULES`: `testing`, `tests`,
  `distutils`, `backends`, `animation`, `texmanager`, `sphinxext`, pandas' `computation`,
  statsmodels' `x13` and `iolib`, ...) are banned like `ESCAPE_ATTRIBUTES`, and a test pins
  that every public first-level submodule of numpy, pandas, matplotlib, seaborn,
  scikit-learn, the toolkits and the admitted statsmodels packages is reviewed as safe or
  banned, so an upgrade that adds one fails until someone looks. Single helpers elsewhere
  (`UNSAFE_HELPERS`: `test()`, which runs pytest, `add_newdoc` and `import_module`, which
  import by name, `switch_backend`, `TexManager`, the seaborn and statsmodels fetchers,
  `print_*` canvas writers, `x13_*` runners) are banned like `BANNED_ATTRIBUTES`. Modules
  re-exported as attributes (`mpl.tempfile`, `mpl.logging`, pickle, pkgutil, pydoc,
  `sklearn.<module>.scipy`, ...) joined `ESCAPE_ATTRIBUTES`. And an attribute path resolved
  through an import must stay inside the import surface: `import scipy.stats` binds `scipy`,
  so `scipy.datasets.face()` is a finding (`_check_attribute_surface`).
* **Settings that start programs** (`rc-key`). matplotlib starts LaTeX for `text.usetex`
  and the `pgf.*` settings, ffmpeg or ImageMagick for `animation.*`, Ghostscript for
  `ps.usedistiller`, and imports the module `backend` names, as pandas does for
  `plotting.backend`. A string literal shaped like a dotted settings key that names one is a
  finding anywhere; in a settings position (an `rcParams` subscript, a key of a settings
  dict, a `**{...}` keyword) a bare `backend` or `usetex` is too, while the word "backend"
  in a list of labels passes. Settings are written only with keys the rule can read:
  `rcParams` (and its two default copies) is subscripted with a literal when written, or
  `.update`d with a dict literal of literal keys, and is never a value; `rc_context`,
  `style.context` and every `rc=` take a string or such a dict; `rc(group, **kw)` takes a
  literal group and checks each `group.keyword`. The keywords `usetex=` and `backend=` are
  banned on every call (`banned-keyword`), the value "TeX" (`ismath="TeX"`) is a finding,
  and a savefig `format=` other than "png" is a `savefig-target` finding. A key built at
  run time still passes; the render harness's audit hook refuses the process it would start.
* **A module is never a value.** A name bound by `import X [as Y]` may only be the
  receiver of an attribute (`calendar.month_abbr`); as a value (`[calendar][0]`,
  `f(dataclasses)`, `c = collections`) it would reach the attribute checks through an
  expression the resolver cannot follow, so `c._locale` would pass the private-name
  rule. No catalogue file uses a module as a value. A module reached through an
  attribute chain (`[np.lib][0]`) or a `from` import cannot be told from a plain value
  without importing it, so the dangerous private names the walk found are in
  `ESCAPE_ATTRIBUTES` as well.
* **Attribute names are banned outright, on any object.** `.format`, `.eval`, `.query`,
  `.show`, `.use`, `.load`, `.read_*`, `.to_csv` and the rest are findings wherever they
  appear, called or not, because the receiver's type is not knowable without executing
  (`f = pd.read_csv; f(path)` and `x = df; x.eval(...)` have to fail too). The price is
  a false positive on a column accessed as an attribute (`df.load`, `df.read_count`):
  the message says to subscript instead, and the single repair does. `.use` is wider
  than the design's `matplotlib.use` because `matplotlib.style.use` accepts paths and
  URLs; `.io` and `ExcelWriter` are added for `pandas.io.common.get_handle` and the
  Excel writer, and `open_memmap`, `imsave`, `to_filehandle`, `open_file_cm`,
  `rc_params_from_file` and the rarer pandas writers for the remaining file paths of
  numpy, matplotlib and pandas; the design's list names none of them.
* **Import paths are checked component by component** against the same name sets, so
  an alias cannot drop a banned component: `import pandas.io.common as common` and
  `import numpy.lib.format as fmt` are findings although `common.get_handle` and
  `fmt.open_memmap` no longer spell `.io` or `.format`.
* **Module paths are resolved through import aliases** (`import numpy as np`,
  `import matplotlib.pyplot as plt`, `from numpy import random`, plus one level of
  `name = <module chain>` assignment). The resolver drives the RNG rule and the
  messages; the security bans do not depend on it.
* **`os` is allowed only as the THEME block uses it.** Every occurrence of a name bound
  by `import os [as X]` must be the receiver of `X.getenv("ANYPLOT_THEME", ...)` or
  `X.environ.get("ANYPLOT_THEME", ...)` with the literal first argument, at most two
  positional arguments and no keyword other than `default`. `from os import ...` is a
  banned import. Note `__file__` is a dunder, so the catalogue's `sys.path` guard fails
  twice (`sys` and `__file__`); the normaliser strips that guard before eligibility.
* **Dunders and strings.** Every identifier matching `^__\\w+__$` (names, attributes,
  keywords, parameters, function names) and every string or bytes literal containing a
  dunder identifier is a finding; `__name__ == "__main__"` guards therefore fail, which
  is intended (no catalogue file uses one). Strings built at runtime (`"__cla" + "ss__"`)
  pass this check but have no consumer: `getattr`, `eval`, `exec`, `vars`, `__import__`
  and `.format` are all banned.
* **URL literals** match `http://`, `https://`, `ftp://`, and `file:`/`data:` followed
  by a non-space character, case-insensitively and at a word boundary, so a subtitle
  "Source data: 2024 survey" or the word "profile:" passes while `data:image/png;...`
  and `file:///etc/passwd` do not.
* **savefig.** Every `savefig` call (not only the last) must target exactly the f-string
  `f"plot-{THEME}.png"`, as the first positional argument or `fname=`; a file without a
  savefig call is a finding too. A second savefig writing elsewhere is never wanted.
* **`type()`** is allowed with exactly one plain positional argument; anything else
  (three arguments, starred arguments, keywords) is the class-creating form.
* **String method names.** pandas resolves `df.agg("to_csv")`, `df.apply("eval")` and
  `df.transform(...)` by `getattr` on the frame (falling back to numpy), so a string
  argument of `agg`, `aggregate`, `apply`, `transform` or `applymap` that names a banned
  attribute or function is a finding.
* **RNG allowance (ADAPTATION).** Exactly `np.random.default_rng(<int literal>)` (positional
  or `seed=`), either bound once by a plain `name = ...` assignment whose every use is a
  `name.choice(...)`, `name.permutation(...)` or `name.uniform(...)` call, or used inline
  as `np.random.default_rng(7).uniform(...)`. Everything else under `numpy.random.*`,
  the stdlib `random` module and scipy's `.rvs` samplers are findings.
* **Literal data (ADAPTATION).** A list, tuple or set literal is flattened through nested
  containers and its numeric leaves counted (`int`, `float`, `complex` and their signed
  forms; not `bool`); more than 20 at the outermost container is a finding.
* **Palette (ADAPTATION).** `IMPRINT` and `IMPRINT_PALETTE` (the two names the catalogue
  uses) must be lists or tuples of string literals that keep `original_palette` as their
  prefix in order (hex compared case-insensitively); the entries after the prefix must be
  the canonical `core.palette.IMPRINT` positions not already in the original, in
  canonical order, which for a canonical original is exactly "the next positions";
  a list longer than the original plus those positions is a finding of its own,
  because no literal list can give more groups distinct palette colours.
  The list is not changed afterwards either: a palette name, or a name bound to one by
  a plain `colors = IMPRINT`, may not be the target of anything but a plain assignment
  (no `+=`, unpacking, loop or `del` target), may not have items assigned or deleted,
  and may not reach a list mutator (`.append`, `.extend`, `.insert`, `.remove`, `.pop`,
  `.clear`, `.reverse`, `.sort`). A palette passed into a function is not followed; the
  reviewer sees the render.
* **Placeholder (ADAPTATION).** Exactly one `df = load_user_data()` statement, anywhere;
  any other use of the name `load_user_data` is a separate finding.

**The DATA profile** (`validate_data_code`, owner decision of 2026-10-14) checks a snippet
that generates the data for a plot, which the root translated to Python from what the
user pasted or typed (Python, JavaScript, R, a textbook formula) and the renderer runs in
the same sandbox as a plot (`agents/anyplot/tools/session.py`, `run_data_code`). It is
every SECURITY rule except `savefig-target`, with its own import surface and three rules
of its own:

* **Imports.** `COMMON_IMPORTS`, the standard `random` module and the scipy submodules of
  `SHARED_SCIENCE_IMPORTS` (`DATA_IMPORTS`): no plotting library, no sklearn and no
  statsmodels (`statsmodels.api.datasets` has network and file helpers). `os` is a banned
  import here, without the THEME exception: a data snippet reads no environment.
* **No private attribute at all.** A name with a leading underscore is banned as an
  attribute on any receiver, not only on an imported name: a snippet never needs one, and
  `random._inst`, `rng._bit_generator` or `x._mgr` would otherwise reach internals the
  resolver cannot see behind an expression.
* **`df` at the top.** A module-level assignment to the name `df` (`data-frame`); the
  harness takes it from the run's globals (`render/harness.py`, data mode).
* **No rows from memory.** `literal-data` counts the numbers and the strings of every
  outermost literal container (a list, tuple, set or dict, `pd.DataFrame({"x": [...]})`
  being one table), a repetition by an int literal as its copies (`[1, 2, 3] * 10` holds
  30 numbers, `["North", "South"] * 25` 50 strings), strings only as elements and dict
  values, never as dict keys (column names): more than `MAX_LITERAL_NUMBERS` (20) of
  either in one container, or more than `MAX_DATA_LITERAL_NUMBERS` (40) of either in the
  file, numbers outside containers included, is a finding (Fable review of 2026-10-14). A
  snippet computes values; values written out belong in the data panel as a table, where
  the dataset judge reads them. `np.repeat` and `np.tile` of a short literal list stay
  allowed: they repeat values the snippet chose, within the caps.

Its messages never mention `load_user_data()`: a file, URL or network finding carries the
fixed `DATA_IO_MESSAGE` ("paste the file's contents in the data panel instead"), and a
banned import names the data surface instead (`DATA_IMPORT_ALTERNATIVE`). An
`if __name__ == "__main__":` guard fails the dunder rule; `code/data_code.py` strips it
before validation.

Rule ids: `size`, `encoding`, `syntax`, `banned-import` (with `Finding.module`), `star-import`,
`relative-import`, `os-use`, `module-value`, `banned-name`, `banned-call`, `banned-attribute`,
`banned-keyword`, `rc-key`, `dunder`, `banned-statement`, `url-literal`, `string-length`, `savefig-target`
(SECURITY; DATA without `savefig-target`);
`placeholder-count`, `placeholder-use`, `rng`, `literal-data`, `palette-prefix`
(ADAPTATION); `data-frame` (DATA). Findings are sorted by line; messages never echo
more than about 60 characters of code and never echo string literal contents.
"""

from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from collections.abc import Container, Iterable
from dataclasses import dataclass
from typing import Literal, TypeVar

from core.constants import SUPPORTED_LIBRARIES
from core.palette import IMPRINT

from ..schemas import MAX_CODE_CHARS


Profile = Literal["security", "adaptation", "data"]

MAX_STRING_CHARS = 200
MAX_LITERAL_NUMBERS = 20
MAX_DATA_LITERAL_NUMBERS = 40
"""Numeric literals a data snippet may hold in all: a formula with its constants, ranges and seeds needs
far fewer (a random walk about 5, a textbook formula about 10); a table written out needs more."""
MAX_MESSAGE_CHARS = 300
MAX_SNIPPET_CHARS = 60
PLACEHOLDER = "df = load_user_data()"
THEME_VARIABLE = "ANYPLOT_THEME"

# The pure standard modules from `warnings` on were admitted by the owner (2026-10-10).
# Each was walked for public names that read, load, save, open, fetch or evaluate, and
# for the modules it re-exports (Python 3.13.12):
# * warnings: `formatwarning`, `showwarning` and `warn_explicit` read a line of any file
#   through `linecache` (the first returns it as text) or write to a file object, so
#   they are in `BANNED_IO`; re-exports `sys`.
# * typing: `get_type_hints` and `ForwardRef` evaluate annotation strings, which is
#   `eval`; re-exports `sys` and `types` (whose `CodeType` and `FunctionType` build
#   code): all in `ESCAPE_ATTRIBUTES`.
# * calendar: `LocaleTextCalendar`, `LocaleHTMLCalendar` and `different_locale` set the
#   process locale through `_locale.setlocale`, which the `locale` ban keeps out: in
#   `ESCAPE_ATTRIBUTES`. `main` reaches them through its `-L` option, but a column may be
#   called `main`, so it is banned on the calendar module only: in `MODULE_ESCAPES`. The
#   rest prints to standard output only; re-exports `sys`, `datetime`, `_locale`.
# * zoneinfo: `reset_tzpath` points the time zone search at any directory,
#   `available_timezones` lists it, `ZoneInfo.from_file` reads a file object: in
#   `BANNED_IO`. `ZoneInfo(key)` reads the time zone database only and refuses keys
#   that leave it.
# * enum: `bltns` is the `builtins` module and `global_enum` writes into a module's
#   namespace: in `ESCAPE_ATTRIBUTES`; re-exports `sys`.
# * dataclasses: re-exports `inspect` (source reads) and `sys`; the private
#   `_FuncBuilder` runs `exec` on text, which the private-name rule covers.
# * operator: `attrgetter` and `methodcaller` look attributes up by string, which is
#   `getattr`: in `ESCAPE_ATTRIBUTES`.
# * decimal, fractions, numbers, cmath, bisect, heapq: nothing (fractions re-exports
#   `sys`, `re`, `math`, `operator`, `numbers` and `functools`).
COMMON_IMPORTS: frozenset[str] = frozenset(
    {
        "numpy",
        "pandas",
        "math",
        "statistics",
        "datetime",
        "collections",
        "itertools",
        "functools",
        "textwrap",
        "colorsys",
        "re",
        "warnings",
        "typing",
        "calendar",
        "decimal",
        "fractions",
        "zoneinfo",
        "enum",
        "dataclasses",
        "operator",
        "bisect",
        "heapq",
        "numbers",
        "cmath",
    }
)
# Shared by every Python plotting library: the science stack minus its data loaders.
# Every package here was walked for public names that read, load, save, open or fetch
# (2026-10-09, scipy 1.18, statsmodels 0.14): none exist; `scipy.ndimage.imread` is
# long gone. `scipy.io` and `scipy.datasets` stay out. `scipy.fft`, `scipy.linalg` and
# `scipy.constants` were walked on 2026-10-10 (scipy 1.18.1): computation only, the
# CODATA table of `scipy.constants` is parsed from a string inside the module, and the
# private submodules they re-export fall under the private-name rule.
SHARED_SCIENCE_IMPORTS: frozenset[str] = frozenset(
    {
        "scipy.stats",
        "scipy.interpolate",
        "scipy.signal",
        "scipy.cluster.hierarchy",
        "scipy.spatial",
        "scipy.optimize",
        "scipy.special",
        "scipy.integrate",
        "scipy.ndimage",
        "scipy.fft",
        "scipy.linalg",
        "scipy.constants",
        "sklearn",
        "statsmodels.api",
        "statsmodels.nonparametric",
        "statsmodels.tsa",
        "statsmodels.graphics",
    }
)
DENIED_IMPORTS: frozenset[str] = frozenset({"sklearn.datasets", "statsmodels.formula", "scipy.io", "scipy.datasets"})
# The three toolkits ship with matplotlib and do no I/O. Third-party plotting helpers
# (cartopy, qrcode, wordcloud, matplotlib_venn, squarify, adjustText) stay banned: they
# are not installed in the agents image, and admitting one is an owner decision.
_MATPLOTLIB_STACK: frozenset[str] = frozenset(
    {"matplotlib", "mpl_toolkits.mplot3d", "mpl_toolkits.axes_grid1", "mpl_toolkits.axisartist"}
)
# Phase 1 enables matplotlib and seaborn. The other Python libraries save through
# different calls (`write_image`, `ggsave`, `render_to_png`), so their profile needs
# more than an import allowlist; until then they raise `ValueError`.
LIBRARY_IMPORTS: dict[str, frozenset[str]] = {
    "matplotlib": _MATPLOTLIB_STACK,
    "seaborn": _MATPLOTLIB_STACK | {"seaborn"},
}
# The DATA profile: no plotting stack, no sklearn (its `datasets` fetch over the network) and
# no statsmodels (`statsmodels.api.datasets` and `webuse` read files and URLs). The standard
# `random` was walked (Python 3.13.12): its public names compute; `main` parses `sys.argv`
# and prints, so it is banned on its module (`MODULE_ESCAPES`), and its private names
# (`_os`, `_urandom`, `_inst`) fall under the DATA profile's private-attribute rule.
DATA_IMPORTS: frozenset[str] = (
    COMMON_IMPORTS | {"random"} | frozenset(module for module in SHARED_SCIENCE_IMPORTS if module.startswith("scipy."))
)
DATA_IO_MESSAGE = "paste the file's contents in the data panel instead"
"""The one message of every file, URL or network finding of the DATA profile."""
DATA_IMPORT_ALTERNATIVE = (
    "compute the data with numpy, pandas, math, random, statistics or scipy.stats; plotting happens later in the chat"
)
"""What a DATA-profile `banned-import` suggests for a module that is no file or network module."""
DATA_IO_MODULES: frozenset[str] = frozenset(
    {
        "io",
        "csv",
        "json",
        "pickle",
        "shelve",
        "sqlite3",
        "urllib",
        "requests",
        "httpx",
        "http",
        "socket",
        "ssl",
        "ftplib",
        "pathlib",
        "shutil",
        "glob",
        "os",
        "tempfile",
        "zipfile",
        "tarfile",
        "gzip",
        "bz2",
        "lzma",
        "fileinput",
        "PIL",
        "imageio",
        "openpyxl",
        "pyarrow",
        "sklearn.datasets",
        "statsmodels",
        "scipy.io",
        "scipy.datasets",
        "pandas.io",
        "numpy.lib.format",
    }
)
"""Modules a DATA-profile `banned-import` answers with `DATA_IO_MESSAGE`: the snippet wanted a file or the network."""

BANNED_NAMES: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "input",
        "breakpoint",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "memoryview",
        "exit",
        "quit",
    }
)
BANNED_ATTRIBUTES: frozenset[str] = frozenset(
    {"format", "format_map", "eval", "query", "memmap", "ctypeslib", "f2py", "use", "show", "io"}
)
BANNED_IO: frozenset[str] = frozenset(
    {
        "ExcelFile",
        "ExcelWriter",
        "HDFStore",
        "to_csv",
        "to_pickle",
        "to_parquet",
        "to_excel",
        "to_sql",
        "to_hdf",
        "to_feather",
        "to_json",
        "to_html",
        "to_clipboard",
        "to_latex",
        "to_markdown",
        "to_xml",
        "to_stata",
        "to_orc",
        "save",
        "savez",
        "savez_compressed",
        "savetxt",
        "genfromtxt",
        "fromfile",
        "fromregex",
        "DataSource",
        "tofile",
        "open_memmap",
        "imread",
        "imsave",
        "get_sample_data",
        "to_filehandle",
        "open_file_cm",
        "rc_file",
        "rc_params_from_file",
        "urlopen",
        "formatwarning",
        "showwarning",
        "warn_explicit",
        "reset_tzpath",
        "available_timezones",
        "from_file",
    }
)
# Banned as attributes on any object, as `from` imports and as an import path's component
# below its root: modules an allowed module re-exports that the import rules keep out
# (`statistics.sys.modules`, `enum.bltns`, `dataclasses.inspect`), and the reflection and
# the locale setters the stdlib walk found (see COMMON_IMPORTS). The private-name rule
# needs the import resolver, which an expression defeats (`[np.lib][0]`), so the private
# helpers a walk of the allowed modules found dangerous are banned here by name as well:
# the re-exported `sys` (collections) and `_locale` (calendar), the stdlib RNG
# (`statistics._random`), the time zone path and file readers (`zoneinfo._tzpath`,
# `_common`), import by name (`warnings._getcategory`), `exec` on text
# (`dataclasses._FuncBuilder`), and numpy's file opener (`numpy.lib._datasource.open`).
ESCAPE_ATTRIBUTES: frozenset[str] = frozenset(
    {
        # Frame, generator, coroutine, traceback and code-object introspection (security review of
        # 2026-10-14): a generator's frame reaches the interpreter's builtins without a dunder name.
        "gi_frame",
        "gi_code",
        "gi_yieldfrom",
        "cr_frame",
        "cr_code",
        "cr_await",
        "cr_origin",
        "ag_frame",
        "ag_code",
        "ag_await",
        "f_back",
        "f_builtins",
        "f_globals",
        "f_locals",
        "f_code",
        "f_trace",
        "f_generator",  # Python 3.14: the generator or coroutine that owns a frame
        "tb_frame",
        "tb_next",
        "co_code",
        "co_consts",
        "co_names",
        # Native code and raw memory through a value, not an import (second opinion of 2026-10-14):
        # `np.zeros(1).ctypes._ctypes.CDLL(None)` reaches libc, `from_address` reads and writes any
        # address, `as_strided` views memory outside an array, `.dump` pickles an array to a file;
        # `extbuild` compiles C, and `get_rdataset` / `webuse` fetch over the network.
        "ctypes",
        "_ctypes",
        "cffi",
        "data_as",
        "from_address",
        "from_buffer",
        "from_buffer_copy",
        "as_strided",
        "dump",
        "dumps",
        "extbuild",
        "get_rdataset",
        "webuse",
        "sys",
        "os",
        "builtins",
        "bltns",
        "modules",
        "inspect",
        "subprocess",
        "importlib",
        "pathlib",
        "shutil",
        "socket",
        "linecache",
        "get_type_hints",
        "ForwardRef",
        "CodeType",
        "FunctionType",
        "attrgetter",
        "methodcaller",
        "global_enum",
        "different_locale",
        "LocaleTextCalendar",
        "LocaleHTMLCalendar",
        "_sys",
        "_locale",
        "_random",
        "_tzpath",
        "_common",
        "_getcategory",
        "_FuncBuilder",
        "_datasource",
        # Modules the allowed packages hand out as attributes outside the import surface (re-export survey of
        # 2026-10-14, numpy 2.5, pandas 3.0, matplotlib 3.11, seaborn 0.13, scipy 1.18, scikit-learn 1.9,
        # statsmodels 0.15): `mpl.tempfile`, `mpl.logging` (`FileHandler`, `config.dictConfig` imports by name),
        # pickle (`loads` runs code), pkgutil and pydoc (`resolve_name`, `locate`: import by name), the file,
        # archive and network modules, `sklearn.<module>.scipy` and `seaborn.regression.statsmodels` (the whole
        # package past the allowed submodules).
        "tempfile",
        "logging",
        "pickle",
        "pkgutil",
        "pydoc",
        "runpy",
        "webbrowser",
        "urllib",
        "codecs",
        "gzip",
        "zipfile",
        "tarfile",
        "mmap",
        "fileinput",
        "traceback",
        "platform",
        "threading",
        "multiprocessing",
        "atexit",
        "asyncio",
        "joblib",
        "pytest",
        "PIL",
        "locale",
        "scipy",
        "statsmodels",
    }
)
UNSAFE_SUBMODULES: frozenset[str] = frozenset(
    {
        "testing",  # numpy.testing.measure / runstring exec any string, tempdir; pandas.testing; matplotlib.testing
        "testutils",  # numpy.ma.testutils
        "tests",
        "conftest",
        "distutils",
        "sphinxext",  # matplotlib's plot directive runs code
        "backends",  # backend_pgf and backend_ps start LaTeX and Ghostscript, PdfPages writes files
        "backend_bases",  # register_backend: a backend imported by name; TexManager
        "backend_managers",
        "backend_tools",
        "animation",  # the movie writers start ffmpeg and ImageMagick
        "texmanager",  # starts LaTeX
        "dviread",  # starts kpsewhich
        "pylab",
        "computation",  # pandas' eval engine
        "compat",  # pandas.compat.pickle_compat, statsmodels.compat
        "external",  # seaborn.external (appdirs, docscrape → pydoc)
        "externals",  # sklearn.externals (array_api_extra.testing)
        "x13",  # statsmodels runs the X-13 binary from a path it is given
        "discovery",  # sklearn.utils.discovery imports by name
        "estimator_checks",
        "iolib",  # statsmodels' pickle save and load
        "smpickle",
    }
)
"""Submodules of the allowed packages that test, build, start processes, run LaTeX or import by name (validator
review of 2026-10-14: `np.testing.measure` compiles and execs its string). Banned like `ESCAPE_ATTRIBUTES`: as an
attribute on any object, as a `from` import and as an import path component below its root. A test pins that every
public first-level submodule of numpy, pandas, matplotlib, seaborn and scikit-learn is either reviewed as safe or
in this set, so a library upgrade that adds one fails until someone looks at it."""
UNSAFE_HELPERS: frozenset[str] = frozenset(
    {
        "test",  # np.test, pd.test, mpl.test, scipy's and statsmodels' `test()` run pytest
        "add_newdoc",  # numpy.lib.add_newdoc imports a module by name
        "import_module",  # sklearn.utils.discovery re-exports importlib.import_module
        "import_optional_dependency",  # pandas.core.apply re-exports it: import by name
        "register_backend",
        "switch_backend",  # imports a backend module by name (module://...)
        "backend",  # pd.options.plotting.backend: df.plot() imports the module it names
        "get_registered_canvas_class",
        "math_to_image",  # matplotlib.mathtext writes an image to any path
        "TexManager",
        "usetex",
        "set_usetex",
        "dogplot",  # seaborn fetches an image over the network
        "get_dataset_names",
        "get_data_home",
        "clear_data_home",  # statsmodels deletes its data directory
        "check_internet",
        "urlretrieve",
        "datasets",  # scipy.datasets downloads and caches, statsmodels.api.datasets fetches and deletes
        "webdoc",  # statsmodels opens a browser
        "run_spec",
        "all_estimators",
        "all_displays",
        "all_functions",
        "thumbnail",  # matplotlib.image.thumbnail reads and writes files by path
        "json_dump",  # matplotlib.font_manager writes JSON to any path
        "json_load",
        "save_pickle",
        "parse_lutkepohl_data",
        "make_pdf_to_png_converter",
        "gs_distill",
        "xpdf_distill",
    }
)
"""Public functions and classes of the allowed modules that exec, start a process, import by name, fetch or write
files (survey of 2026-10-14). Banned as attributes on any object and as `from` imports, like `BANNED_ATTRIBUTES`;
`_UNSAFE_HELPER_PATTERN` adds the families `print_*` (a canvas writing any format to any path, past the savefig
rule) and `x13_*` (statsmodels' X-13 runners)."""
MODULE_ESCAPES: frozenset[str] = frozenset({"calendar.main", "random.main"})
"""Escapes banned only on their own module, because the bare name is plausible data: `calendar.main`
sets the process locale through its `-L` option, while `df.main` is a column. Checked against the
resolved attribute path, `from` imports and import paths; the `module-value` rule keeps the module
from reaching it through an expression the resolver cannot follow."""
_DATA_FROM_DF = "the data comes only from df = load_user_data(), and the plot reads and writes no files"
IMPORT_ALTERNATIVES: dict[str, str] = {
    **dict.fromkeys(
        ("io", "csv", "json", "pickle", "sqlite3", "urllib", "requests", "http", "pathlib", "shutil", "glob"),
        _DATA_FROM_DF,
    ),
    **dict.fromkeys(("tempfile", "zipfile", "tarfile", "PIL", "imageio", "sklearn.datasets"), _DATA_FROM_DF),
    **dict.fromkeys(("scipy.io", "scipy.datasets", "pandas.io", "numpy.lib.format"), _DATA_FROM_DF),
    "os": 'os only as THEME = os.getenv("ANYPLOT_THEME", ...) after a plain import os',
    "sys": "a plot needs nothing from the interpreter: remove the import",
    "random": "values come from df; a seeded np.random.default_rng(<int>) is only for jitter or subsampling",
    "secrets": "values come from df; a seeded np.random.default_rng(<int>) is only for jitter or subsampling",
    "locale": "format numbers with f-strings or matplotlib.ticker.FuncFormatter, which need no locale",
    "string": "use str methods, f-strings and literals",
    "dateutil": "parse dates with pandas.to_datetime or datetime, time zones with zoneinfo",
    "pytz": "use zoneinfo for time zones",
    "statsmodels.formula": "fit with statsmodels.api on arrays taken from df",
    "scipy": "import the scipy submodule itself, such as scipy.stats or scipy.fft",
}
"""What a `banned-import` repair line suggests instead, by module path or its longest known prefix."""
DEFAULT_IMPORT_ALTERNATIVE = (
    "use numpy, pandas, scipy's computing modules, sklearn, statsmodels.api, the plotting library, or pure "
    "standard modules such as math, datetime, collections, re, warnings or zoneinfo"
)
# Third-party roots a banned import is logged under: the catalogue's banned plotting
# helpers, the catalogue's other plotting libraries, and data and science packages a
# model may reach for. A root missing here is logged as `?`; add it when a run shows one.
THIRD_PARTY_MODULES: frozenset[str] = frozenset(
    {
        "adjustText",
        "cartopy",
        "matplotlib_venn",
        "qrcode",
        "squarify",
        "wordcloud",
        "altair",
        "bokeh",
        "highcharts_core",
        "lets_plot",
        "plotly",
        "plotnine",
        "pygal",
        "IPython",
        "geopandas",
        "networkx",
        "openpyxl",
        "polars",
        "pyarrow",
        "shapely",
        "skimage",
        "sympy",
        "xarray",
        "yaml",
    }
)
LOGGED_MODULES: frozenset[str] = frozenset(
    {
        *sys.stdlib_module_names,
        *COMMON_IMPORTS,
        *SHARED_SCIENCE_IMPORTS,
        *DENIED_IMPORTS,
        *(module for modules in LIBRARY_IMPORTS.values() for module in modules),
        *IMPORT_ALTERNATIVES,
        *THIRD_PARTY_MODULES,
        *DATA_IO_MODULES,
    }
)
"""The closed vocabulary of `Finding.module`: no word in it comes from a model or a user."""
UNKNOWN_MODULE = "?"
"""The label of a banned import with no prefix in `LOGGED_MODULES`."""
# `read_*` (pandas readers), `fetch_*` (sklearn downloaders), `load*` (`np.load`,
# `np.loadtxt`, `sns.load_dataset`, sklearn's `load_*`).
_BANNED_IO_PATTERN = re.compile(r"^(?:read_\w+|fetch_\w+|load\w*)$")
_UNSAFE_HELPER_PATTERN = re.compile(r"^(?:print_\w+|x13_\w+)$")
_ANY_RECEIVER_ESCAPES = ESCAPE_ATTRIBUTES | UNSAFE_SUBMODULES
"""Banned as an attribute on any object, as a `from` import and as an import path component below its root."""
# matplotlib settings that start a program (LaTeX, ffmpeg, ImageMagick, Ghostscript), import a module by name (a
# backend, pandas' plotting backend) or open a server, matched against every string literal shaped like a setting
# key (lower-case dotted words), wherever it appears: a dict key, a subscript, `rc_context`, `set_theme(rc=...)`,
# `pd.set_option`. "TeX" is the `ismath` value that sends a text through LaTeX (`TextPath`, `text2path`).
_RC_KEY_SHAPE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")
_UNSAFE_RC_KEY = re.compile(
    r"^(?:animation|pgf|webagg)\.|(?:^|\.)(?:backend|backend_fallback|usetex)$|_path$|latex|ffmpeg|imagemagick|"
    r"distiller|convert_"
)
UNSAFE_TEXT_VALUES = frozenset({"TeX"})
RC_NAMES = frozenset({"rcParams", "rcParamsDefault", "rcParamsOrig"})
"""matplotlib's settings dicts: written only through a literal key or `.update` with a dict literal (`_check_rc`)."""
_RC_READERS = frozenset({"update", "get", "copy"})
_RC_CONSUMERS = frozenset({"rc_context", "context"})
"""Calls that take settings as a dict (`mpl.rc_context({...})`, `plt.style.context({...})`): literal keys only."""
BANNED_KEYWORDS = frozenset({"usetex", "backend"})
"""Keyword arguments banned on any call: `usetex=True` sends a text through LaTeX (`ax.text`, `TextPath`, `plt.rc`),
`backend=` imports a backend module by name (`savefig(backend="module://...")`)."""
_STRING_DISPATCH_METHODS = frozenset({"agg", "aggregate", "apply", "transform", "applymap"})
# Methods that return text without a target and write to one given as `buf`, with the position of
# `buf` among their positional parameters (`DataFrame.info(verbose, buf, …)`).
_BUFFER_WRITERS: dict[str, int] = {"to_string": 0, "info": 1}

_DUNDER_NAME = re.compile(r"^__\w+__$")
_DUNDER_IN_TEXT = re.compile(r"__\w+__")
_URL_IN_TEXT = re.compile(r"(?i)(?:https?|ftp)://|\b(?:file|data):\S")

_BANNED_STATEMENTS: dict[type[ast.AST], str] = {
    ast.ClassDef: "class definition",
    ast.AsyncFunctionDef: "async def",
    ast.AsyncFor: "async for",
    ast.AsyncWith: "async with",
    ast.Await: "await",
    ast.Yield: "yield",
    ast.YieldFrom: "yield from",
    ast.Global: "global",
    ast.Nonlocal: "nonlocal",
}

_RNG_FACTORY = "numpy.random.default_rng"
_RNG_ALLOWED_METHODS = frozenset({"choice", "permutation", "uniform"})
_RNG_ALLOWED_TEXT = "/".join(f".{method}" for method in sorted(_RNG_ALLOWED_METHODS))
_PALETTE_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})
_LIST_MUTATORS = frozenset({"append", "extend", "insert", "remove", "pop", "clear", "reverse", "sort"})

_Node = TypeVar("_Node", bound=ast.AST)


@dataclass(frozen=True, slots=True)
class Finding:
    """One validator result: a short kebab-case rule id, one message line, a 1-based line.

    A `banned-import` finding also carries the label of the module path it refused
    (`module_label`, a word of a closed vocabulary) for the attribution log; every other
    finding has None.
    """

    rule: str
    message: str
    line: int | None
    module: str | None = None


def _longest_prefix(path: str, known: Container[str]) -> str | None:
    """The longest dotted prefix of `path` that is in `known` (`scipy.io.matlab` → `scipy.io`), else None."""
    parts = path.split(".")
    for length in range(len(parts), 0, -1):
        prefix = ".".join(parts[:length])
        if prefix in known:
            return prefix
    return None


def module_label(path: str) -> str:
    """The label of a module path for the attribution log: its longest prefix in `LOGGED_MODULES`, else `?`.

    The path is code the model wrote, so only a word of the closed vocabulary is logged:
    `os.path` is `os`, `pandas.io.common` is `pandas.io`, and `patient_records` is `?`.
    The function is idempotent, so a reader re-checks a logged label with it.
    """
    return _longest_prefix(path, LOGGED_MODULES) or UNKNOWN_MODULE


def import_alternative(path: str) -> str:
    """What to use instead of the module `path`: the entry of its longest known prefix, else the default."""
    prefix = _longest_prefix(path, IMPORT_ALTERNATIVES)
    return IMPORT_ALTERNATIVES[prefix] if prefix is not None else DEFAULT_IMPORT_ALTERNATIVE


def data_import_alternative(path: str) -> str:
    """What a DATA-profile snippet uses instead of the module `path`: the fixed file message, else the data surface."""
    return DATA_IO_MESSAGE if _longest_prefix(path, DATA_IO_MODULES) is not None else DATA_IMPORT_ALTERNATIVE


def validate_data_code(code: str) -> list[Finding]:
    """The DATA profile (module docstring): SECURITY without savefig, the data import surface, `df`, no rows.

    Never raises; the caller strips an `if __name__ == "__main__":` guard first
    (`code/data_code.py`).
    """
    tree, findings = _parse(code)
    if tree is None:
        return findings
    scan = _Scan(tree, data=True)
    scan.data(DATA_IMPORTS)
    return scan.result()


def validate_security(code: str, *, library: str) -> list[Finding]:
    """The SECURITY profile: import surface, reflection, I/O, statements, literals, savefig.

    Raises `ValueError` for a library id that is not in the catalogue or has no profile
    yet; never raises for the code itself.
    """
    if library not in SUPPORTED_LIBRARIES:
        raise ValueError(f"unknown library {library!r}")
    library_imports = LIBRARY_IMPORTS.get(library)
    if library_imports is None:
        raise ValueError(f"no validator profile for {library!r} yet; enabled: {', '.join(sorted(LIBRARY_IMPORTS))}")
    tree, findings = _parse(code)
    if tree is None:
        return findings
    scan = _Scan(tree)
    scan.security(library, COMMON_IMPORTS | SHARED_SCIENCE_IMPORTS | library_imports)
    return scan.result()


def validate_adaptation(code: str, *, original_palette: list[str]) -> list[Finding]:
    """The ADAPTATION profile: one placeholder, no fabricated data, the palette prefix kept."""
    tree, findings = _parse(code)
    if tree is None:
        return findings
    scan = _Scan(tree)
    scan.adaptation(original_palette)
    return scan.result()


def _parse(code: str) -> tuple[ast.Module | None, list[Finding]]:
    """Size, encoding and syntax: the checks that run before any rule can.

    `ast.parse` alone accepts what only the compiler rejects (a module-level `return` or
    `break`, a repeated keyword argument), so the tree is also compiled, never executed.
    """
    if len(code) > MAX_CODE_CHARS:
        return None, [Finding("size", f"code is {len(code):,} characters; the limit is {MAX_CODE_CHARS:,}", None)]
    try:
        code.encode("utf-8")
    except UnicodeEncodeError:
        return None, [Finding("encoding", "code is not valid UTF-8 text", None)]
    try:
        tree = ast.parse(code, feature_version=(3, 13))
        compile(tree, "<plot>", "exec", dont_inherit=True)
    except SyntaxError as exc:
        return None, [Finding("syntax", f"syntax error: {exc.msg}", exc.lineno)]
    except (ValueError, RecursionError) as exc:  # null bytes, expression nesting
        return None, [Finding("syntax", f"cannot parse: {exc}", None)]
    return tree, []


def _is_numeric(node: ast.AST) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        node = node.operand
    return isinstance(node, ast.Constant) and type(node.value) in (int, float, complex)


def _numeric_leaves(node: ast.AST) -> int:
    """Numeric literal leaves of a (nested) list, tuple or set literal."""
    if not isinstance(node, ast.List | ast.Tuple | ast.Set):
        return 0
    return sum(1 if _is_numeric(elt) else _numeric_leaves(elt) for elt in node.elts)


MAX_REPEAT = 10**6
"""The largest repetition the literal counts multiply by; a larger literal count is an absurd table anyway."""


def _repeat_count(node: ast.BinOp) -> tuple[ast.AST, int] | None:
    """`[...] * n` or `n * [...]` with an int literal `n`: the repeated operand and `n`; None for anything else."""
    if not isinstance(node.op, ast.Mult):
        return None
    for operand, other in ((node.left, node.right), (node.right, node.left)):
        if isinstance(other, ast.Constant) and type(other.value) is int and _is_repeatable(operand):
            return operand, max(0, min(other.value, MAX_REPEAT))
    return None


def _is_repeatable(node: ast.AST) -> bool:
    if isinstance(node, ast.List | ast.Tuple):
        return True
    return isinstance(node, ast.BinOp) and _repeat_count(node) is not None


def _is_literal_container(node: ast.AST | None, parent: ast.AST | None = None) -> bool:
    """A list, tuple, set or dict literal (not an assignment target), or one repeated by an int literal."""
    if isinstance(node, ast.List | ast.Tuple):
        return isinstance(node.ctx, ast.Load)
    if isinstance(node, ast.Set | ast.Dict):
        return True
    return isinstance(node, ast.BinOp) and _repeat_count(node) is not None


def _counts_child(parent: ast.AST, child: ast.AST) -> bool:
    """Whether a literal container counts `child` among its leaves: a repetition never counts its multiplier."""
    if isinstance(parent, ast.BinOp):
        repeat = _repeat_count(parent)
        return repeat is not None and repeat[0] is child
    return True


def _literal_leaves(node: ast.AST) -> tuple[int, int]:
    """Numeric and text leaves of a literal container, a repetition multiplied; dict keys add numbers, not text."""
    if isinstance(node, ast.BinOp):
        repeat = _repeat_count(node)
        if repeat is None:
            return 0, 0
        numbers, strings = _literal_leaves(repeat[0])
        return numbers * repeat[1], strings * repeat[1]
    if isinstance(node, ast.Dict):
        key_numbers = sum(1 for key in node.keys if key is not None and _is_numeric(key))
        numbers, strings = _sum_leaves(node.values)
        return numbers + key_numbers, strings
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        return _sum_leaves(node.elts)
    return 0, 0


def _sum_leaves(items: Iterable[ast.AST]) -> tuple[int, int]:
    numbers = strings = 0
    for item in items:
        if _is_numeric(item):
            numbers += 1
        elif isinstance(item, ast.Constant) and isinstance(item.value, str):
            strings += 1
        else:
            inner = _literal_leaves(item)
            numbers += inner[0]
            strings += inner[1]
    return numbers, strings


def _hex(value: str) -> str:
    return value.strip().upper()


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _text(node: ast.Constant) -> str | None:
    """The textual content of a string or bytes literal, or None for other constants."""
    if isinstance(node.value, str):
        return node.value
    if isinstance(node.value, bytes):
        return node.value.decode("latin-1")
    return None


def _snippet(node: ast.AST) -> str:
    """The dotted name a message shows, built without recursion and without echoing literals.

    `np.random.normal` stays as written; any other receiver (a call, a subscript, a literal)
    becomes `(...)`, so `df["secret"].read_count` reads `(...).read_count`. A long chain
    keeps its tail, which is where the offending attribute sits.
    """
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    parts.append(node.id if isinstance(node, ast.Name) else "(...)")
    text = ".".join(reversed(parts))
    if len(text) > MAX_SNIPPET_CHARS:
        text = "..." + text[-(MAX_SNIPPET_CHARS - 3) :]
    return text


def _io_hint(name: str) -> str:
    """For a reader or loader (`read_*`, `load*`, `fetch_*`): where the data comes from instead."""
    return f" → {_DATA_FROM_DF}" if _BANNED_IO_PATTERN.match(name) else ""


def _is_unsafe_helper(name: str) -> bool:
    return name in UNSAFE_HELPERS or _UNSAFE_HELPER_PATTERN.match(name) is not None


RC_KEY_MESSAGE = "this setting starts a program or loads a module (LaTeX, ffmpeg, a backend or a tool path)"


def _is_unsafe_setting(text: str, *, setting: bool = False) -> bool:
    """A string literal that names a setting `_UNSAFE_RC_KEY` matches, or the `ismath="TeX"` value.

    Anywhere in the code only a dotted key counts (`"text.usetex"`, `"plotting.backend"`), so a
    word such as "backend" in a list of labels passes; where the string is a settings key
    (`setting`: an `rcParams` subscript, a key of a settings dict, a `**{...}` keyword) a bare
    `"backend"` or `"usetex"` counts too.
    """
    if text in UNSAFE_TEXT_VALUES:
        return True
    if _RC_KEY_SHAPE.match(text) is None or ("." not in text and not setting):
        return False
    return _UNSAFE_RC_KEY.search(text) is not None


def _is_literal_settings(node: ast.AST | None) -> bool:
    """A settings argument whose keys can be checked: `None`, a string literal (a style or group name) or a dict
    literal whose every key is a string literal (no `**` unpacking)."""
    if node is None or (isinstance(node, ast.Constant) and (node.value is None or isinstance(node.value, str))):
        return True
    return isinstance(node, ast.Dict) and all(
        isinstance(key, ast.Constant) and isinstance(key.value, str) for key in node.keys
    )


def _module_allowed(path: str, allowed: Iterable[str]) -> bool:
    return any(path == prefix or path.startswith(prefix + ".") for prefix in allowed)


def _is_placeholder(node: ast.AST | None) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "df"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "load_user_data"
        and not node.value.args
        and not node.value.keywords
    )


def _is_theme_target(node: ast.AST) -> bool:
    """Exactly `f"plot-{THEME}.png"`: three parts, the middle a bare `THEME` with no spec."""
    if not isinstance(node, ast.JoinedStr) or len(node.values) != 3:
        return False
    head, middle, tail = node.values
    return (
        isinstance(head, ast.Constant)
        and head.value == "plot-"
        and isinstance(middle, ast.FormattedValue)
        and isinstance(middle.value, ast.Name)
        and middle.value.id == "THEME"
        and middle.conversion == -1
        and middle.format_spec is None
        and isinstance(tail, ast.Constant)
        and tail.value == ".png"
    )


def _single_name_target(node: ast.AST) -> ast.Name | None:
    """The `name` of a plain `name = ...` or `name: T = ...` statement, else None."""
    if isinstance(node, ast.Assign):
        targets: list[ast.expr] = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = [node.target]
    else:
        return None
    if len(targets) == 1 and isinstance(targets[0], ast.Name):
        return targets[0]
    return None


class _Scan:
    """One parsed module, indexed by node type, with parent links and import aliases."""

    def __init__(self, tree: ast.Module, *, data: bool = False) -> None:
        self.tree = tree
        self.data_profile = data
        """The DATA profile: its own messages (no `load_user_data()`), no `os` exception, no private attribute."""
        self.by_type: defaultdict[type[ast.AST], list[ast.AST]] = defaultdict(list)
        self.parents: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            self.by_type[type(node)].append(node)
            for child in ast.iter_child_nodes(node):
                self.parents[child] = node
        self.findings: list[Finding] = []
        self.os_names: set[str] = set()
        self.allowed_imports: frozenset[str] = frozenset()
        self.import_bindings: dict[str, bool] = {}
        """Name bound by an import the rules permitted (`import scipy.stats` binds `scipy`) → True."""
        self.aliases: dict[str, str] = {}
        self._collect_aliases()

    # -- shared --------------------------------------------------------------------------

    def add(self, rule: str, message: str, node: ast.AST | None, *, module: str | None = None) -> None:
        label = module_label(module) if module is not None else None
        self.findings.append(Finding(rule, message[:MAX_MESSAGE_CHARS], self._line(node), label))

    def ban_import(self, path: str, reason: str, node: ast.AST) -> None:
        """A `banned-import` finding whose message names the module and what to use instead."""
        alternative = data_import_alternative(path) if self.data_profile else import_alternative(path)
        self.add("banned-import", f"import of '{path}' {reason} → {alternative}", node, module=path)

    def io_hint(self, name: str) -> str:
        """Where the data comes from instead: for a reader or loader (`read_*`, `load*`, `fetch_*`) in a plot, for any
        file or network name in a data snippet."""
        if self.data_profile:
            return f" → {DATA_IO_MESSAGE}" if name in BANNED_IO or _BANNED_IO_PATTERN.match(name) else ""
        return _io_hint(name)

    def result(self) -> list[Finding]:
        unique = dict.fromkeys(self.findings)
        return sorted(unique, key=lambda f: (f.line is None, f.line or 0, f.rule, f.message))

    def of(self, node_type: type[_Node]) -> list[_Node]:
        return [node for node in self.by_type[node_type] if isinstance(node, node_type)]

    def _line(self, node: ast.AST | None) -> int | None:
        while node is not None:
            line = getattr(node, "lineno", None)
            if isinstance(line, int):
                return line
            node = self.parents.get(node)
        return None

    def _collect_aliases(self) -> None:
        """Name bound by an import (or a one-level module assignment) → dotted module path."""
        for import_node in self.of(ast.Import):
            for alias in import_node.names:
                if alias.asname:
                    self.aliases[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    self.aliases[root] = root
        for from_node in self.of(ast.ImportFrom):
            if from_node.level or not from_node.module:
                continue
            for alias in from_node.names:
                if alias.name != "*":
                    self.aliases[alias.asname or alias.name] = f"{from_node.module}.{alias.name}"
        for assign in sorted(self.of(ast.Assign), key=lambda n: n.lineno):
            target = _single_name_target(assign)
            path = self.resolve(assign.value) if target is not None else None
            if target is not None and path is not None:
                self.aliases[target.id] = path

    def resolve(self, node: ast.AST) -> str | None:
        """`np.random.normal` → `numpy.random.normal`; None when the root is not a module."""
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        root = self.aliases.get(node.id)
        if root is None:
            return None
        return ".".join([root, *reversed(parts)])

    def _is_call_receiver(self, node: ast.AST, methods: frozenset[str]) -> bool:
        """`node` is the value of an attribute in `methods` that is itself called."""
        attribute = self.parents.get(node)
        if not isinstance(attribute, ast.Attribute) or attribute.value is not node or attribute.attr not in methods:
            return False
        call = self.parents.get(attribute)
        return isinstance(call, ast.Call) and call.func is attribute

    # -- SECURITY ------------------------------------------------------------------------

    def security(self, library: str, allowed_imports: frozenset[str]) -> None:
        self._check_imports(library, allowed_imports)
        self._check_os_use()
        self._check_module_values()
        self._check_names()
        self._check_attributes()
        self._check_attribute_surface()
        self._check_calls()
        self._check_keywords()
        self._check_settings()
        self._check_buffer_writers()
        self._check_statements()
        self._check_strings()
        self._check_savefig()

    # -- DATA ----------------------------------------------------------------------------

    def data(self, allowed_imports: frozenset[str]) -> None:
        """Every SECURITY check but savefig, then `df` at the top and no rows written out (module docstring)."""
        self._check_imports("data", allowed_imports)
        self._check_module_values()
        self._check_names()
        self._check_attributes()
        self._check_attribute_surface()
        self._check_calls()
        self._check_keywords()
        self._check_settings()
        self._check_buffer_writers()
        self._check_statements()
        self._check_strings()
        self._check_data_frame()
        self._check_data_literals()

    def _check_data_frame(self) -> None:
        """A module-level `df = ...` (or `df: T = ...`): the table the harness takes from the run's globals."""
        for statement in self.tree.body:
            target = _single_name_target(statement)
            if target is not None and target.id == "df":
                return
            if isinstance(statement, ast.Assign) and any(
                isinstance(element, ast.Name) and element.id == "df"
                for target_node in statement.targets
                if isinstance(target_node, ast.Tuple | ast.List)
                for element in target_node.elts
            ):
                return
        self.add("data-frame", "assign the table to df at the top level, such as df = pd.DataFrame({...})", None)

    def _check_data_literals(self) -> None:
        """No rows written out: numbers and strings in literal containers, a repetition counted as its copies.

        A container is a list, tuple, set or dict literal, or one repeated by an int
        literal (`[1, 2, 3] * 10` holds 30 numbers, `10 * ["a"]` 10 strings), counted at
        the outermost one. Strings count as list, tuple and set elements and dict values,
        never as dict keys (column names). Numbers outside any container count toward the
        file's total too.
        """
        source = "values written out belong in the data panel as a table"
        total_numbers = total_strings = 0
        for node in ast.walk(self.tree):
            parent = self.parents.get(node)
            grandparent = self.parents.get(parent) if parent is not None else None
            if not _is_literal_container(node, parent) or _is_literal_container(parent, grandparent):
                continue
            numbers, strings = _literal_leaves(node)
            total_numbers += numbers
            total_strings += strings
            if numbers > MAX_LITERAL_NUMBERS:
                message = f"literal with {numbers} numeric values; the limit is {MAX_LITERAL_NUMBERS}, {source}"
                self.add("literal-data", message, node)
            if strings > MAX_LITERAL_NUMBERS:
                message = f"literal with {strings} text values; the limit is {MAX_LITERAL_NUMBERS}, {source}"
                self.add("literal-data", message, node)
        total_numbers += sum(
            1 for constant in self.of(ast.Constant) if _is_numeric(constant) and not self._inside_literal(constant)
        )
        if total_numbers > MAX_DATA_LITERAL_NUMBERS:
            message = f"{total_numbers} numeric literals; the limit is {MAX_DATA_LITERAL_NUMBERS}: code computes the data, {source}"
            self.add("literal-data", message, None)
        if total_strings > MAX_DATA_LITERAL_NUMBERS:
            message = f"{total_strings} text values in literals; the limit is {MAX_DATA_LITERAL_NUMBERS}, {source}"
            self.add("literal-data", message, None)

    def _inside_literal(self, node: ast.AST) -> bool:
        """Whether `node` sits inside a literal container (`_is_literal_container`), which counts it already."""
        child, parent = node, self.parents.get(node)
        while parent is not None:
            if _is_literal_container(parent, self.parents.get(parent)) and _counts_child(parent, child):
                return True
            child, parent = parent, self.parents.get(parent)
        return False

    def _check_imports(self, library: str, allowed: frozenset[str]) -> None:
        def denied(path: str) -> bool:
            return _module_allowed(path, DENIED_IMPORTS)

        def permitted(path: str) -> bool:
            return _module_allowed(path, allowed) and not denied(path)

        self.allowed_imports = allowed
        where = "in data code" if self.data_profile else f"with {library}"
        for import_node in self.of(ast.Import):
            for alias in import_node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if alias.name == "os" and not self.data_profile:
                    self.os_names.add(alias.asname or "os")
                elif not permitted(alias.name):
                    self.ban_import(alias.name, f"is not allowed {where}", alias)
                else:
                    self.import_bindings[bound] = not self._check_module_path(alias.name, alias)
        for from_node in self.of(ast.ImportFrom):
            if from_node.level or not from_node.module:
                self.add("relative-import", "relative imports are not allowed", from_node)
                continue
            module_banned = self._check_module_path(from_node.module, from_node)
            for alias in from_node.names:
                if alias.name == "*":
                    self.add("star-import", f"star import from '{from_node.module}' is not allowed", alias)
                    continue
                path = f"{from_node.module}.{alias.name}"
                if not module_banned and (denied(path) or not (permitted(from_node.module) or permitted(path))):
                    self.ban_import(path, f"is not allowed {where}", alias)
                elif not module_banned:
                    self.import_bindings[alias.asname or alias.name] = True
                self._check_function_name(alias.name, alias)
                if path in MODULE_ESCAPES:
                    self.add("banned-attribute", f"'{path}' is not allowed", alias)

    def _check_module_path(self, path: str, node: ast.AST) -> bool:
        """An import path whose component is a banned name (`pandas.io`, `numpy.lib.format`), or
        below its root an escape name or a private module (`scipy.fft._backend`).

        The alias would hide the component from the attribute check: `common.get_handle`
        after `import pandas.io.common as common` spells no `.io`, and `backend.set_backend`
        after `import scipy.fft._backend as backend` no `._backend`. The root itself is
        left to the allowlist, which keeps its message.
        """
        escape = next((name for name in MODULE_ESCAPES if _module_allowed(path, [name])), None)
        if escape is not None:
            self.ban_import(path, f"reaches the banned name '{escape}'", node)
            return True
        for position, part in enumerate(path.split(".")):
            if part in BANNED_ATTRIBUTES or part in BANNED_IO or _BANNED_IO_PATTERN.match(part):
                self.ban_import(path, f"reaches the banned name '{part}'", node)
                return True
            if position and part in _ANY_RECEIVER_ESCAPES:
                self.ban_import(path, f"reaches the banned name '{part}'", node)
                return True
            if position and part.startswith("_"):
                self.ban_import(path, f"reaches the private module '{part}'", node)
                return True
        return False

    def _check_function_name(self, name: str, node: ast.AST) -> None:
        """A name reached by a `from` import: the attribute, escape and I/O sets apply, and no private name."""
        if name in BANNED_ATTRIBUTES or name in _ANY_RECEIVER_ESCAPES or _is_unsafe_helper(name):
            self.add("banned-attribute", f"'{name}' is not allowed", node)
        elif name in BANNED_IO or _BANNED_IO_PATTERN.match(name):
            self.add("banned-call", f"'{name}' is not allowed{self.io_hint(name)}", node)
        elif name.startswith("_") and not _DUNDER_NAME.match(name):
            self.add("banned-attribute", f"the private name '{name}' is not allowed", node)

    def _check_os_use(self) -> None:
        for name in self.of(ast.Name):
            if name.id in self.os_names and not self._is_theme_lookup(name):
                self.add("os-use", f"'{name.id}' may only be used as {name.id}.getenv('{THEME_VARIABLE}', ...)", name)

    def _check_module_values(self) -> None:
        """A name bound by `import X [as Y]` only as the receiver of an attribute (module docstring).

        `os` has its own, stricter rule (`os-use`).
        """
        modules = {
            alias.asname or alias.name.split(".")[0]
            for import_node in self.of(ast.Import)
            for alias in import_node.names
            if alias.name != "os"
        }
        for name in self.of(ast.Name):
            if name.id not in modules or not isinstance(name.ctx, ast.Load):
                continue
            parent = self.parents.get(name)
            if not (isinstance(parent, ast.Attribute) and parent.value is name):
                self.add(
                    "module-value",
                    f"the module '{name.id}' may only be used as {name.id}.<name>, never as a value",
                    name,
                )

    def _is_theme_lookup(self, name: ast.Name) -> bool:
        """`os.getenv("ANYPLOT_THEME", ...)` or `os.environ.get("ANYPLOT_THEME", ...)` around `name`."""
        node: ast.AST = name
        attribute = self.parents.get(node)
        expected = "getenv"
        if isinstance(attribute, ast.Attribute) and attribute.value is node and attribute.attr == "environ":
            node = attribute
            attribute = self.parents.get(node)
            expected = "get"
        if not isinstance(attribute, ast.Attribute) or attribute.value is not node or attribute.attr != expected:
            return False
        call = self.parents.get(attribute)
        if not isinstance(call, ast.Call) or call.func is not attribute:
            return False
        # At most one default, positional or keyword: `getenv(KEY, "light", default="dark")` is a TypeError.
        if not 1 <= len(call.args) <= 2 or len(call.args) + len(call.keywords) > 2:
            return False
        if any(keyword.arg != "default" for keyword in call.keywords):
            return False
        key = call.args[0]
        return isinstance(key, ast.Constant) and key.value == THEME_VARIABLE

    def _check_names(self) -> None:
        for name in self.of(ast.Name):
            if name.id in BANNED_NAMES:
                hint = f" → {DATA_IO_MESSAGE}" if self.data_profile and name.id in ("open", "input") else ""
                self.add("banned-name", f"'{name.id}' is not allowed{hint}", name)
            if _DUNDER_NAME.match(name.id):
                self.add("dunder", f"dunder name '{name.id}' is not allowed", name)
        for parameter in self.of(ast.arg):
            if parameter.arg in BANNED_NAMES:
                self.add("banned-name", f"parameter '{parameter.arg}' is not allowed", parameter)
            if _DUNDER_NAME.match(parameter.arg):
                self.add("dunder", f"dunder parameter '{parameter.arg}' is not allowed", parameter)
        for function in self.of(ast.FunctionDef):
            if _DUNDER_NAME.match(function.name):
                self.add("dunder", f"dunder function name '{function.name}' is not allowed", function)
        for keyword in self.of(ast.keyword):
            if keyword.arg is not None and _DUNDER_NAME.match(keyword.arg):
                self.add("dunder", f"dunder keyword '{keyword.arg}' is not allowed", keyword)

    def _check_attributes(self) -> None:
        for attribute in self.of(ast.Attribute):
            if _DUNDER_NAME.match(attribute.attr):
                self.add("dunder", f"dunder attribute '.{attribute.attr}' is not allowed", attribute)
            elif (
                attribute.attr in BANNED_ATTRIBUTES
                or attribute.attr in _ANY_RECEIVER_ESCAPES
                or _is_unsafe_helper(attribute.attr)
            ):
                self.add("banned-attribute", f"attribute '.{attribute.attr}' is not allowed", attribute)
            elif attribute.attr in BANNED_IO or _BANNED_IO_PATTERN.match(attribute.attr):
                # `df.load` / `df.read_count`: a column reached as an attribute, not a module function.
                column_like = self.resolve(attribute.value) is None and attribute.attr.startswith(("read_", "load"))
                hint = (
                    "; a column of that name must be subscripted"
                    if column_like and not self.data_profile
                    else self.io_hint(attribute.attr)
                )
                self.add("banned-call", f"'{_snippet(attribute)}' is not allowed{hint}", attribute)
            elif self.resolve(attribute) in MODULE_ESCAPES:
                self.add("banned-attribute", f"attribute '{_snippet(attribute)}' is not allowed", attribute)
            elif attribute.attr.startswith("_") and self.data_profile:
                # `random._inst`, `rng._bit_generator`, `x._mgr`: a data snippet needs no private name on anything.
                self.add("banned-attribute", f"the private attribute '{_snippet(attribute)}' is not allowed", attribute)
            elif attribute.attr.startswith("_") and self.resolve(attribute.value) is not None:
                # `collections._sys`, `dataclasses._FuncBuilder`: private helpers of an imported name.
                self.add("banned-attribute", f"the private attribute '{_snippet(attribute)}' is not allowed", attribute)

    def _in_surface(self, path: str) -> bool:
        return _module_allowed(path, self.allowed_imports) and not _module_allowed(path, DENIED_IMPORTS)

    def _check_attribute_surface(self) -> None:
        """An attribute path resolved through an import stays inside the import surface.

        `import scipy.stats` binds `scipy`, so `scipy.datasets.face()` would reach a module the
        import rules keep out (it downloads); `import statsmodels.tsa` binds `statsmodels`, and
        `statsmodels.iolib` loads pickles. The path is reported once, at its shortest prefix
        outside the surface; a name bound by a refused import is left to that finding.
        """
        for attribute in self.of(ast.Attribute):
            root: ast.AST = attribute
            while isinstance(root, ast.Attribute):
                root = root.value
            if not isinstance(root, ast.Name) or not self.import_bindings.get(root.id, False):
                continue
            path = self.resolve(attribute)
            if path is None or self._in_surface(path):
                continue
            inner = self.resolve(attribute.value) if isinstance(attribute.value, ast.Attribute) else None
            if inner is not None and not self._in_surface(inner):
                continue
            message = f"'{_snippet(attribute)}' reaches a module outside the allowed imports"
            self.add("banned-attribute", message, attribute)

    def _check_keywords(self) -> None:
        for keyword in self.of(ast.keyword):
            if keyword.arg in BANNED_KEYWORDS:
                self.add("banned-keyword", f"the keyword '{keyword.arg}=' is not allowed", keyword)

    def _check_settings(self) -> None:
        """matplotlib settings are written only with keys the string rule can read (`rc-key`).

        `rcParams` (and its two default copies) may be subscripted, with a string literal
        when the item is written or deleted, or be the receiver of a called `.update`, `.get`
        or `.copy`, whose `.update` arguments are dict literals with string-literal keys; it
        is never a value (`r = mpl.rcParams`) or a target. `rc_context(...)`, `style.context(...)`
        and every `rc=` argument take a string or such a dict; `rc(group, **settings)` takes a
        literal group, and each `group.keyword` key is checked like a string literal. A key built
        at run time would pass the string rule; the render guard refuses what such a setting starts.
        """
        message = "matplotlib settings must be written with literal keys (a string or a dict literal)"
        for node in [*self.of(ast.Attribute), *self.of(ast.Name)]:
            name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else ""
            if name not in RC_NAMES:
                continue
            if not self._is_settings_use(node):
                self.add("rc-key", message, node)
                continue
            parent = self.parents.get(node)
            if isinstance(parent, ast.Subscript):
                self._check_setting_keys(parent.slice)
            elif isinstance(parent, ast.Attribute) and parent.attr == "update":
                call = self.parents.get(parent)
                for argument in call.args if isinstance(call, ast.Call) else []:
                    self._check_setting_keys(argument)
        for call in self.of(ast.Call):
            func = call.func
            name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
            unpacked = any(isinstance(arg, ast.Starred) for arg in call.args) or any(
                keyword.arg is None for keyword in call.keywords
            )
            settings = [keyword.value for keyword in call.keywords if keyword.arg == "rc"]
            if name in _RC_CONSUMERS:
                settings.extend(call.args)
            if (name in _RC_CONSUMERS and unpacked) or not all(_is_literal_settings(value) for value in settings):
                self.add("rc-key", message, call)
            for value in [*settings, *(keyword.value for keyword in call.keywords if keyword.arg is None)]:
                self._check_setting_keys(value)  # `**{"usetex": True}` too
            if name == "rc":
                self._check_rc_call(call, unpacked)

    def _check_setting_keys(self, node: ast.AST) -> None:
        """The string keys of a settings dict, or a settings subscript's key, checked as settings (bare words too)."""
        keys = node.keys if isinstance(node, ast.Dict) else [node]
        for key in keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                if _is_unsafe_setting(key.value, setting=True):
                    self.add("rc-key", f"string literal names a setting: {RC_KEY_MESSAGE}", key)

    def _is_settings_use(self, node: ast.AST) -> bool:
        parent = self.parents.get(node)
        if isinstance(parent, ast.Subscript) and parent.value is node:
            key = parent.slice
            return isinstance(parent.ctx, ast.Load) or (isinstance(key, ast.Constant) and isinstance(key.value, str))
        if not (
            isinstance(parent, ast.Attribute)
            and parent.value is node
            and parent.attr in _RC_READERS
            and isinstance(getattr(node, "ctx", ast.Load()), ast.Load)
        ):
            return False
        call = self.parents.get(parent)
        if not (isinstance(call, ast.Call) and call.func is parent):
            return False
        if parent.attr != "update":
            return True
        return all(_is_literal_settings(arg) and not isinstance(arg, ast.Constant) for arg in call.args) and all(
            keyword.arg is not None for keyword in call.keywords
        )

    def _check_rc_call(self, call: ast.Call, unpacked: bool) -> None:
        """`plt.rc("text", usetex=True)` sets `text.usetex`: a literal group, and each `group.keyword` checked."""
        group = call.args[0] if len(call.args) == 1 else None
        if unpacked or not (isinstance(group, ast.Constant) and isinstance(group.value, str)):
            self.add("rc-key", "rc() takes one literal group name and keyword settings", call)
            return
        for keyword in call.keywords:
            if keyword.arg is not None and _is_unsafe_setting(f"{group.value}.{keyword.arg}"):
                self.add("rc-key", RC_KEY_MESSAGE, keyword)

    def _check_calls(self) -> None:
        for call in self.of(ast.Call):
            func = call.func
            if isinstance(func, ast.Name) and func.id == "type":
                plain = len(call.args) == 1 and not call.keywords and not isinstance(call.args[0], ast.Starred)
                if not plain:
                    self.add("banned-call", "type() is only allowed with one argument", call)
            if isinstance(func, ast.Attribute) and func.attr in _STRING_DISPATCH_METHODS:
                for argument in [*call.args, *[keyword.value for keyword in call.keywords]]:
                    for constant in ast.walk(argument):
                        if isinstance(constant, ast.Constant) and isinstance(constant.value, str):
                            self._check_dispatch_name(constant.value, func.attr, constant)

    def _check_buffer_writers(self) -> None:
        """`df.to_string("f")` and `df.info(buf=f)` write to a path; with no target they return text.

        Such a method may only be called where it is named (`w = df.to_string; w("f")` would hide
        the target), and a call is refused when its `buf` argument, by position or by keyword, is
        anything but `None`, or when a starred argument could carry it.
        """
        for attribute in self.of(ast.Attribute):
            position = _BUFFER_WRITERS.get(attribute.attr)
            if position is None:
                continue
            call = self.parents.get(attribute)
            if not (isinstance(call, ast.Call) and call.func is attribute):
                self.add("banned-attribute", f"'.{attribute.attr}' may only be called directly", attribute)
                continue
            targets = [
                *(call.args[position : position + 1]),
                *(keyword.value for keyword in call.keywords if keyword.arg == "buf"),
            ]
            starred = any(isinstance(argument, ast.Starred) for argument in call.args[: position + 1])
            unpacked = any(keyword.arg is None for keyword in call.keywords)
            if starred or unpacked or any(not _is_none(target) for target in targets):
                self.add("banned-call", f"'.{attribute.attr}()' with a target is not allowed", call)

    def _check_dispatch_name(self, name: str, method: str, node: ast.AST) -> None:
        """`df.agg("to_csv")` reaches the method by `getattr`: the name is checked as if written."""
        # A buffer writer counts too: `df.agg("to_string", buf="f")` forwards the target (#12167 review).
        if name in BANNED_NAMES or name in BANNED_ATTRIBUTES or name in BANNED_IO or name in _BUFFER_WRITERS:
            self.add("banned-call", f"'{name}' is not allowed as a method name in .{method}()", node)
        elif match := _BANNED_IO_PATTERN.match(name):
            # The string is a literal, and the pattern takes any word after `read_`: only its family is named.
            family = next(prefix for prefix in ("read_", "fetch_", "load") if match.group(0).startswith(prefix))
            self.add("banned-call", f"'{family}...' is not allowed as a method name in .{method}()", node)

    def _check_statements(self) -> None:
        for node_type, label in _BANNED_STATEMENTS.items():
            for node in self.by_type[node_type]:
                self.add("banned-statement", f"{label} is not allowed", node)
        for comprehension in self.of(ast.comprehension):
            if comprehension.is_async:
                self.add("banned-statement", "async comprehension is not allowed", comprehension)

    def _check_strings(self) -> None:
        for constant in self.of(ast.Constant):
            text = _text(constant)
            if text is None:
                continue
            if len(text) > MAX_STRING_CHARS:
                message = f"string literal is {len(text):,} characters; the limit is {MAX_STRING_CHARS}"
                self.add("string-length", message, constant)
            if _DUNDER_IN_TEXT.search(text):
                self.add("dunder", "string literal contains a dunder identifier", constant)
            if _URL_IN_TEXT.search(text):
                hint = f" → {DATA_IO_MESSAGE}" if self.data_profile else ""
                self.add("url-literal", f"string literal contains a URL or a file:/data: scheme{hint}", constant)
            if isinstance(constant.value, str) and _is_unsafe_setting(text):
                self.add("rc-key", f"string literal names a setting: {RC_KEY_MESSAGE}", constant)

    def _check_savefig(self) -> None:
        found = False
        for call in self.of(ast.Call):
            func = call.func
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                continue
            if name != "savefig":
                continue
            found = True
            target = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg == "fname"), None)
            if target is None or not _is_theme_target(target):
                self.add("savefig-target", 'savefig target must be exactly f"plot-{THEME}.png"', call)
            for keyword in call.keywords:
                # `format="ps"` with a distiller or `format="pgf"` would start Ghostscript or LaTeX, whatever the name.
                fmt = keyword.value
                if keyword.arg == "format" and not (isinstance(fmt, ast.Constant) and fmt.value == "png"):
                    self.add("savefig-target", 'savefig format must be "png" or left out', keyword)
                elif keyword.arg is None:
                    self.add("savefig-target", "savefig takes no **arguments", keyword)
        if not found:
            self.add("savefig-target", "no savefig call found", None)

    # -- ADAPTATION ----------------------------------------------------------------------

    def adaptation(self, original_palette: list[str]) -> None:
        self._check_placeholder()
        self._check_rng()
        self._check_literal_data()
        self._check_palette(original_palette)
        self._check_palette_writes()

    def _check_placeholder(self) -> None:
        count = sum(1 for assign in self.of(ast.Assign) if _is_placeholder(assign))
        if count != 1:
            self.add("placeholder-count", f"expected exactly one '{PLACEHOLDER}' statement, found {count}", None)
        for name in self.of(ast.Name):
            if name.id != "load_user_data":
                continue
            call = self.parents.get(name)
            if not (isinstance(call, ast.Call) and call.func is name and _is_placeholder(self.parents.get(call))):
                self.add("placeholder-use", f"'load_user_data' is only allowed in the statement '{PLACEHOLDER}'", name)

    def _check_rng(self) -> None:
        for call in self.of(ast.Call):
            path = self.resolve(call.func)
            if path == _RNG_FACTORY:
                self._check_default_rng(call)
            elif path is not None and (
                path.startswith("numpy.random.") or path == "random" or path.startswith("random.")
            ):
                self.add("rng", f"random data generation '{_snippet(call.func)}' is not allowed", call)
        for attribute in self.of(ast.Attribute):
            if attribute.attr == "rvs":
                self.add("rng", f"random sampling '{_snippet(attribute)}' is not allowed", attribute)

    def _check_default_rng(self, call: ast.Call) -> None:
        """The one allowance: a seeded generator used for jitter and subsampling only."""
        seed = call.args[0] if len(call.args) == 1 and not call.keywords else None
        if not call.args and len(call.keywords) == 1 and call.keywords[0].arg == "seed":
            seed = call.keywords[0].value
        if not (isinstance(seed, ast.Constant) and type(seed.value) is int):
            self.add("rng", "np.random.default_rng must be seeded with an int literal", call)
            return
        if self._is_call_receiver(call, _RNG_ALLOWED_METHODS):
            return
        parent = self.parents.get(call)
        target = _single_name_target(parent) if parent is not None else None
        if target is None:
            message = f"the seeded generator may only be bound to a name or used inline for {_RNG_ALLOWED_TEXT}(...)"
            self.add("rng", message, call)
            return
        name = target.id
        uses = [node for node in self.of(ast.Name) if node.id == name]
        stores = sum(1 for node in uses if not isinstance(node.ctx, ast.Load))
        stores += sum(1 for parameter in self.of(ast.arg) if parameter.arg == name)
        if stores != 1:
            self.add("rng", f"'{name}' must be bound exactly once, to the seeded generator", call)
        for use in uses:
            if isinstance(use.ctx, ast.Load) and not self._is_call_receiver(use, _RNG_ALLOWED_METHODS):
                self.add("rng", f"'{name}' may only be used as {name}{_RNG_ALLOWED_TEXT}(...)", use)

    def _check_literal_data(self) -> None:
        """The ADAPTATION rule; the DATA profile has its own, stricter one (`_check_data_literals`)."""
        for node_type in (ast.List, ast.Tuple, ast.Set):
            for literal in self.by_type[node_type]:
                if isinstance(self.parents.get(literal), ast.List | ast.Tuple | ast.Set):
                    continue  # counted at the outermost container
                count = _numeric_leaves(literal)
                if count > MAX_LITERAL_NUMBERS:
                    message = (
                        f"literal with {count} numeric values; the limit is {MAX_LITERAL_NUMBERS}, data comes from df"
                    )
                    self.add("literal-data", message, literal)

    def _check_palette(self, original_palette: list[str]) -> None:
        original = [_hex(colour) for colour in original_palette]
        extension = [colour for colour in IMPRINT if _hex(colour) not in set(original)]
        statements: list[ast.Assign | ast.AnnAssign] = [*self.of(ast.Assign), *self.of(ast.AnnAssign)]
        statements.sort(key=lambda statement: (statement.lineno, statement.col_offset))
        assigned = 0
        for statement in statements:
            target = _single_name_target(statement)
            if target is None or target.id not in _PALETTE_NAMES:
                continue
            assigned += 1
            if assigned > 1:  # the palette is one literal list, assigned once; a later one would replace it
                self.add("palette-prefix", f"{target.id} is assigned again; keep one literal palette list", statement)
                continue
            value = statement.value
            if not isinstance(value, ast.List | ast.Tuple) or not all(
                isinstance(element, ast.Constant) and isinstance(element.value, str) for element in value.elts
            ):
                self.add("palette-prefix", f"{target.id} must be a list of colour string literals", statement)
                continue
            entries = [
                _hex(element.value)
                for element in value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            ]
            if entries[: len(original)] != original:
                message = f"{target.id} must keep the {len(original)} original palette entries in order"
                self.add("palette-prefix", message, statement)
            elif len(entries) > len(original) + len(extension):
                limit = len(original) + len(extension)
                message = f"{target.id} has {len(entries)} entries, more than the {limit} colours the palette has"
                self.add("palette-prefix", message, statement)
            elif entries[len(original) :] != extension[: len(entries) - len(original)]:
                next_positions = ", ".join(extension[:3]) or "none left"
                message = f"{target.id} may only be extended with the next Imprint positions ({next_positions})"
                self.add("palette-prefix", message, statement)

    def _check_palette_writes(self) -> None:
        """The checked literal stays the palette: no later rebinding, item write or list mutator."""
        names = set(_PALETTE_NAMES)
        for assign in self.of(ast.Assign):
            target = _single_name_target(assign)
            if target is not None and isinstance(assign.value, ast.Name) and assign.value.id in _PALETTE_NAMES:
                names.add(target.id)  # `colors = IMPRINT` shares the list
        for name in self.of(ast.Name):
            if name.id not in names:
                continue
            parent = self.parents.get(name)
            if isinstance(name.ctx, ast.Store | ast.Del):
                if isinstance(name.ctx, ast.Store) and parent is not None and _single_name_target(parent) is name:
                    continue  # a plain assignment: `_check_palette` checks its value, or it binds an alias
                self.add("palette-prefix", f"'{name.id}' holds the palette and may only be assigned plainly", name)
            elif isinstance(parent, ast.Subscript) and parent.value is name and not isinstance(parent.ctx, ast.Load):
                self.add("palette-prefix", f"items of '{name.id}' may not be assigned or deleted", name)
            elif isinstance(parent, ast.Attribute) and parent.value is name and parent.attr in _LIST_MUTATORS:
                self.add("palette-prefix", f"'{name.id}.{parent.attr}' would change the palette", name)
