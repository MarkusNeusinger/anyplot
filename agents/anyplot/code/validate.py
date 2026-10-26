"""Two-profile AST validator of the plot pipeline (docs/concepts/agent-network.md, "Adapt and validate").

The SECURITY profile runs on the normalised catalogue original (eligibility) and on every
adapted working form; the ADAPTATION profile runs on adapted code only. Both functions
return an empty list for valid code and never raise on invalid code: a syntax error (also
one only the compiler reports, such as a module-level `return`), an oversize file or a
string that is not UTF-8 text is itself a `Finding`. Only `library` makes
`validate_security` raise `ValueError`: an id outside the catalogue, or a catalogue
library without a profile yet (`LIBRARY_IMPORTS`: matplotlib, seaborn, plotnine, altair,
pygal and letsplot), because that is a caller bug, not a property of the code.

The validator is one guardrail layer, not the boundary: the sandbox (no egress, read-only
root, no environment) and the loader substitution are the others. Its job is to make the
adapter's output boring: a fixed import surface, no reflection, no I/O, one data source.

Decisions this module takes where the design leaves room:

* **Import surface.** COMMON plus the science stack (`scipy.{stats, interpolate, signal,
  cluster.hierarchy, spatial, optimize, special, integrate, ndimage, fft, linalg,
  constants}`, `sklearn` without `datasets`, `statsmodels.{api, nonparametric, tsa,
  graphics}`) plus, for matplotlib and seaborn, `matplotlib`, `seaborn` and the bundled
  `mpl_toolkits.{mplot3d, axes_grid1, axisartist}`; for plotnine that matplotlib stack,
  `plotnine` and `mizani` (its scales and formatters, which 6 catalogue files import);
  for altair `altair` and `PIL.Image`, which 184 catalogue files use to pad the PNG
  vl-convert wrote (the import surfaces were walked on 2026-10-24 and the walk was
  adversarially checked on 2026-10-25, `agentic/specs/261024-agent-all-libraries.md`;
  `vl_convert` itself stays out: altair reaches it internally, and its own functions read
  files and open sockets for `<image>` hrefs). The checks' routes are closed by name: an
  image mark (`mark_image`, `Url*`, the `url=` keyword, `Chart.from_dict` and `from_json`
  in altair's profile, `LIBRARY_BANS`), whose `file://` href vl_convert's SVG renderer
  reads from disk in native code the audit hook never sees; the narwhals frame
  `alt.limit_rows` hands out, whose `.implementation.to_native_namespace()` is the pyarrow
  module; VegaFusion's `transformed_data`; and plotnine's `.environment`, the captured
  namespace every plot carries, whose `.namespace["os"]` is the `os` module as a value.
  pygal gets `pygal` and `cairosvg` (its PNG writer, which 98 catalogue files import
  directly), lets-plot gets `lets_plot` (surveys of 2026-10-24, drafts and spikes of
  2026-10-26, `agentic/specs/261024-agent-all-libraries.md`, step 1c); `xml.etree`, PIL
  and cairocffi stay out of pygal's surface and PIL out of lets-plot's, so the catalogue
  files that post-process the SVG or composite the PNG stay blocked. libcairo writes
  pygal's PNG with its own `fopen`, which the render guard never sees, so the closures
  matter more there: cairosvg's modules that read any path or URL or write any file
  (`parser`, `surface`, `url`, `image`, `css`, `features`, `test_api`, the re-exported
  `Path` and the `ROOT` instance, banned on their module in `MODULE_ESCAPES`), cairocffi
  reached as `.cairo` with its `ffi`, `dlopen` and file surfaces, cairosvg's other
  writers (`svg2pdf`, `svg2ps`, `svg2eps`, `svg2svg`, `SURFACES`) and fetchers, and
  pygal's renderers that open a browser or hand out the live tree, its `getattr` by
  string (`cut`), its `str.format` (`template`) and its config merge (`_update`), all in
  pygal's `LIBRARY_BANS`; `etree`, pygal's ElementTree proxy, is banned on every
  receiver (`UNSAFE_SUBMODULES`), and so are `cssselect2`, `tinycss2`, `webencodings` and
  `cairocffi` (`ESCAPE_ATTRIBUTES`): cssselect2 `eval`s the selectors it compiles, and a
  forged token object handed to its compiler reaches an unquoted slot of that code (the
  pygal spike of 2026-10-26). lets-plot's geocoding, map tiles, settings and browser
  launcher are denied imports and banned submodules, its writers (`to_png`, `to_svg`,
  `to_pdf`), browser hook (`setup_show_ext`), import-by-name proxy (`LazyModule`) and
  geocoders are `UNSAFE_HELPERS`, the proxies it hands out (`png`, `palettable`,
  `geopandas`) `ESCAPE_ATTRIBUTES`, and `LetsPlot.set`, `LetsPlot.setup_show_ext` and
  `lets_plot.cfg` `MODULE_ESCAPES`. The four extra scipy modules,
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
  `.update`d with a dict literal of literal keys, and is never a value; `rc_context` and
  every `rc=` take such a dict and no settings file (`fname`); `style.context` takes such a
  dict or a style name, never a path to a style sheet; `rc(group, **kw)` takes a
  literal group and checks each `group.keyword`. The keywords `usetex=` and `backend=` are
  banned on every call (`banned-keyword`), and so are the cache and spill directories of
  scikit-learn and joblib (`memory=`, `temp_folder=`, `cachedir=`), which write to a path
  on the machine that runs the exported code; the value "TeX" (`ismath="TeX"`) is a finding,
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
  numpy, matplotlib and pandas; the design's list names none of them. The one exception
  is lets-plot's spec builders ("lets-plot" below).
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
  and `file:///etc/passwd` do not. pygal's profile lets two kinds pass: the SVG and XLink
  namespace names, exactly `http://www.w3.org/2000/svg` and
  `http://www.w3.org/1999/xlink`, also in Clark notation (`{...}rect`), followed by a
  quote, `}`, whitespace or the end of the string (an XML parser compares them and never
  fetches them; 31 catalogue files write or match SVG markup), and pygal's own
  stylesheets in a `css=` list ("pygal's config" below).
* **The save (`savefig-target`).** Every call of a save name (`regions.SAVE_NAMES`:
  `savefig`, `save`, `ggsave`, `render_to_png`, `render_to_file`, `svg2png`), not only the
  last, is checked against the library's save rule (`regions.SAVE_RULES`). A name the rule
  does not list is a `banned-call` (`np.save` with matplotlib, `fig.savefig` with altair,
  PIL's `.save` with pygal). The file argument (the rule's positional, `fname=`,
  `filename=`, `fp=` or `write_to=`; `ggsave` takes the plot first and the file second,
  `cairosvg.svg2png` takes every argument by keyword) must be exactly the f-string
  `f"plot-{THEME}.png"`, for altair, pygal and lets-plot also `f"plot-{THEME}.html"`,
  the second file their catalogues write; `format=` is absent or the file's own type;
  there are no `**arguments`; and the saves of plotnine, altair, pygal and lets-plot take
  only the keywords the rule lists (the size, the dpi, altair's `scale_factor`, svg2png's
  input and output size), so `path=` with plotnine, which joins a directory, `webdriver=`
  and `engine=`, which choose how altair makes the PNG, a pygal save's chart options and
  svg2png's `url=`, `file_obj=` and `unsafe=`, which read any path or URL, are findings.
  lets-plot's `ggsave` passes exactly `path="."` (`SaveRule.directory`): without it,
  lets-plot writes into a `lets-plot-images` directory it creates. A file without a save
  of the PNG is a finding too, and so is a save without a file (pygal's
  `render_to_png()` returns bytes) or with a file object; a second save writing
  elsewhere is never wanted. A save name may only be called where it is named
  (`f = plot.save; f("x")` would hide the target), and so may `.open`, which only altair's
  rule admits, on the PNG (the PIL block reopens it: `Image.open(f"plot-{THEME}.png")`).
  A save name is never imported under another name (`from plotnine import ggsave as
  keep`), nothing is imported under a save name, and a bare save name is only ever the
  callee of a call (`g = ggsave`, `[ggsave][0](...)` and `partial(ggsave, plot)` are
  `banned-call` findings in every profile): the rule matches calls by their callee's
  name, so a save reached under another name would write anywhere (the lets-plot draft
  of 2026-10-26 showed it in the plotnine profile).
* **Expression strings (plotnine).** plotnine compiles and evaluates a string that is not
  a column name wherever it takes an aesthetic or a facet (`aes`, `after_stat`,
  `after_scale`, `stage`, `facet_wrap`, `facet_grid`, `qplot`), with real builtins and the
  plot's namespace, so `aes(x='open("/etc/passwd").read()')` is code (survey of
  2026-10-24). Every string literal passed to one of those calls (`EXPRESSION_CALLS`) is
  parsed as a Python expression, each side of a facet formula (`~`, `+`) on its own, and
  walked with the name, attribute, call, save and buffer-writer rules of this profile; a
  finding keeps its rule id and names the call. A bare identifier (a column) and a text
  that does not parse (a column such as "True Label", which plotnine can only look up)
  pass; a text that parses may be a column too ("Revenue (kCHF)"), so it is walked, not
  refused, and the render decides. The call's arguments are literals the walk can read:
  strings, numbers, lists of them, a call of another expression function, a name bound
  once at module level to a string literal, and `**` from a dict literal; a variable, a
  concatenation or `aes(**mapping)` is a finding, because plotnine would evaluate a string
  the walk never saw. `qplot`, which evaluates its aesthetics next to `data=` and labels,
  is banned by name. A `formula=` keyword (`stat_smooth`, `stat_quantile`) is a
  `banned-keyword` everywhere, and `from_formula` a banned name: statsmodels hands the
  string to patsy, which `exec`s Python while it parses, and the render guard refuses
  that. The guard lets plotnine's `Environment.eval` run the walked strings
  (`harness.CODE_BUILDERS`); what they reach stays under the guard.
* **pygal's config.** A `css` or `js` entry that starts with `file://` is read from any
  path and inlined into the SVG, any other entry but `inline:...` becomes a stylesheet or
  script the HTML fetches, `defs` is raw SVG markup, and a `googlefont:` font makes the
  SVG load Google Fonts (pygal 3.1.3, surveyed 2026-10-24). So `js=` takes only an empty
  list or tuple (30 catalogue files pass `js=[]`), `css=` takes a list or tuple of
  `inline:` texts (a string or an f-string whose text starts with it) and pygal's own
  `file://style.css`, `file://graph.css` and `file://base.css`, `defs` is refused, all
  three as keywords on any call and as `.css = [...]` and `.js = [...]` assignments; a
  list or a text may be a name bound once at module level, used nowhere but where the
  rule reads it. The attributes are never read, augmented, subscripted or deleted, so a
  list cannot change after the check (`chart.css += [...]`, `chart.css.append(...)`), and
  every `**` argument is a dict literal with string keys, or a name bound once at module
  level to one and used only as `**name` (3 catalogue files share their chart options
  that way), whose `css`, `js` and `defs` keys are checked the same way. A string that
  contains `googlefont:` is a `url-literal`. Findings are `banned-keyword` for a value and
  `banned-attribute` for an attribute.
* **lets-plot.** `LetsPlot` is used only as `LetsPlot.setup_html()` without arguments
  (every one of the 325 catalogue files; `set` points the HTML's script at any URL and
  `setup_show_ext` starts a browser), and `.props`, which hands out a layer's spec dict
  for rewriting after the check (an image layer's `href` included), is banned in its
  profile (`LIBRARY_BANS`; the spike of 2026-10-26). The `.format` ban has one exception
  here: lets-plot's tooltip and label builders set a field's format with `.format(field,
  format)` (128 uses in 59 catalogue files), so `.format` passes when its receiver is a
  chain of builder method calls (`LETSPLOT_BUILDER_METHODS`, each of which returns the
  builder) rooted in a call of `layer_tooltips`, `layer_labels` or `smooth_labels`
  imported with `from lets_plot import ...`, bound nowhere else and never assigned as an
  attribute (`lets_plot.layer_tooltips = str` before the import), and when it takes only
  string literals (positional, or `field=` and `format=`). `"{0}".format(...)`, a builder
  bound to a name (`tt = layer_tooltips(); tt.format(...)`) and a builder name bound
  twice stay findings. The `format=` keyword (`scale_y_continuous(format=...)`) is
  no attribute and passes everywhere.
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
(SECURITY; DATA without `savefig-target`; a plotnine expression string's finding keeps the id of the rule it broke;
pygal's config and lets-plot's rules use the ids above);
`placeholder-count`, `placeholder-use`, `rng`, `literal-data`, `palette-prefix`
(ADAPTATION); `data-frame` (DATA). Findings are sorted by line; messages never echo
more than about 60 characters of code and never echo string literal contents.
"""

from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from collections.abc import Callable, Container, Iterable
from dataclasses import dataclass
from typing import Literal, TypeVar

from core.constants import SUPPORTED_LIBRARIES
from core.palette import IMPRINT

from ..schemas import MAX_CODE_CHARS
from .regions import HTML_SUFFIX, SAVE_NAMES, SaveRule, is_theme_target, save_rule, save_target


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
# for the modules it re-exports (Python 3.13.12; walked again on 3.14.9, whose additions
# are noted per module and in the last item):
# * warnings: `formatwarning`, `showwarning` and `warn_explicit` read a line of any file
#   through `linecache` (the first returns it as text) or write to a file object, so
#   they are in `BANNED_IO`; re-exports `sys`.
# * typing: `get_type_hints` and `ForwardRef` evaluate annotation strings, which is
#   `eval`; re-exports `sys` and `types` (whose `CodeType` and `FunctionType` build
#   code): all in `ESCAPE_ATTRIBUTES`. 3.14 adds `evaluate_forward_ref`, which evaluates a
#   `ForwardRef`: in `ESCAPE_ATTRIBUTES`.
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
#   `_FuncBuilder` runs `exec` on text, which the private-name rule covers. 3.14 also
#   re-exports `annotationlib`, whose `get_annotations(..., eval_str=True)`,
#   `call_evaluate_function`, `call_annotate_function` and `ForwardRef.evaluate` evaluate
#   code (`from dataclasses import annotationlib` passed the walk of 3.13): the module and
#   those names are in `ESCAPE_ATTRIBUTES`.
# * operator: `attrgetter` and `methodcaller` look attributes up by string, which is
#   `getattr`: in `ESCAPE_ATTRIBUTES`.
# * decimal, fractions, numbers, cmath, bisect, heapq: nothing (fractions re-exports
#   `sys`, `re`, `math`, `operator`, `numbers` and `functools`).
# * 3.14.9, the rest: `decimal.IEEEContext`, `operator.is_none` and `is_not_none`, the
#   `heapq` `*_max` functions, `functools.Placeholder`, the types `functools` now
#   re-exports (`MethodType`, `MappingProxyType`, `UnionType`) and `collections.heapq`
#   compute only; `statistics` swaps its `math.erf` re-export for `erfc`, `fractions`
#   drops `Decimal` and `enum` drops `partial`. The walk of `random` below is unchanged.
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
DENIED_IMPORTS: frozenset[str] = frozenset(
    {
        "sklearn.datasets",
        "statsmodels.formula",
        "scipy.io",
        "scipy.datasets",
        # plotnine (survey of 2026-10-24): `data` reads 18 bundled CSVs and hands out `pathlib.Path`,
        # `watermark` draws any image file, `animation` starts ffmpeg.
        "plotnine.data",
        "plotnine.watermark",
        "plotnine.animation",
        # altair: `datasets` fetches over the network and caches under `~/.cache`, `jupyter` re-exports
        # `find_spec`, `execeval` execs text, `server` opens a port, `html` holds the Jinja templates.
        "altair.datasets",
        "altair.jupyter",
        "altair.utils.execeval",
        "altair.utils.server",
        "altair.utils.html",
        # lets-plot (survey of 2026-10-24): `geo_data` geocodes over urllib, `tilesets`, `settings_utils` and the
        # livemap geom put tile and geocoder URLs into the spec, `frontend_context` writes a temporary HTML file and
        # starts a browser.
        "lets_plot.geo_data",
        "lets_plot.tilesets",
        "lets_plot.settings_utils",
        "lets_plot.frontend_context",
        "lets_plot.plot.geom_livemap_",
    }
)
# The three toolkits ship with matplotlib and do no I/O. Third-party plotting helpers
# (cartopy, qrcode, wordcloud, matplotlib_venn, squarify, adjustText) stay banned: they
# are not installed in the agents image, and admitting one is an owner decision.
_MATPLOTLIB_STACK: frozenset[str] = frozenset(
    {"matplotlib", "mpl_toolkits.mplot3d", "mpl_toolkits.axes_grid1", "mpl_toolkits.axisartist"}
)
# One profile per Python library with a save rule (`regions.SAVE_RULES`): plotnine draws
# with matplotlib (5 catalogue files import it directly) and scales with mizani; altair's
# catalogue pads the PNG with `PIL.Image` (the module, not the package: `ImageDraw`,
# `ImageFont` and the rest stay out); pygal renders its PNG through cairosvg, which 98
# catalogue files also import directly (`cairocffi`, `PIL`, `xml.etree` and matplotlib stay
# out, and so do the 23 catalogue files that subclass pygal's `Graph`: a class definition
# is refused in every profile); lets-plot needs nothing else (no catalogue file imports
# matplotlib with it; the 4 that draw on the PNG with PIL stay out). The other Python
# libraries (plotly, bokeh) have no profile yet and raise `ValueError`.
LIBRARY_IMPORTS: dict[str, frozenset[str]] = {
    "matplotlib": _MATPLOTLIB_STACK,
    "seaborn": _MATPLOTLIB_STACK | {"seaborn"},
    "plotnine": _MATPLOTLIB_STACK | {"plotnine", "mizani"},
    "altair": frozenset({"altair", "PIL.Image"}),
    "pygal": frozenset({"pygal", "cairosvg"}),
    "letsplot": frozenset({"lets_plot"}),
}
# The DATA profile: no plotting stack, no sklearn (its `datasets` fetch over the network) and
# no statsmodels (`statsmodels.api.datasets` and `webuse` read files and URLs). The standard
# `random` was walked (Python 3.13.12, unchanged on 3.14.9): its public names compute; `main` parses `sys.argv`
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
    {
        "format",
        "format_map",
        "eval",
        "query",
        "memmap",
        "ctypeslib",
        "f2py",
        "use",
        "show",
        "io",
        # Callbacks the interpreter hands real frames (Fable review of #12181): `sys.settrace`, `sys.setprofile`,
        # `threading`'s forms of both and `sys.monitoring`. The render guard refuses their audit events as well.
        "settrace",
        "setprofile",
        "settrace_all_threads",
        "setprofile_all_threads",
        "monitoring",
    }
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
        # `save` is not here: it is a save name (`regions.SAVE_NAMES`), checked by the library's save rule
        # (`_check_save`), which refuses it where the rule does not list it (`np.save` with matplotlib).
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
        # `pathlib.Path` methods, reached through a module that re-exports `Path` (plotnine's `data` and
        # `ggplot`, altair's `utils.data`), and polars' writers, which altair's narwhals layer could reach.
        "write_text",
        "write_bytes",
        "write_csv",
        "write_parquet",
        "write_ipc",
        "write_json",
        "write_ndjson",
        "scan_csv",
        "scan_parquet",
        "sink_parquet",
        "sink_csv",
        "sink_ipc",
        "sink_ndjson",
        "write_database",
        "write_excel",
        "write_delta",
        "mkdir",
        "touch",
        "unlink",
        "rmdir",
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
        # Python 3.14: `dataclasses.annotationlib` and `typing.evaluate_forward_ref` evaluate annotation strings.
        "annotationlib",
        "get_annotations",
        "call_evaluate_function",
        "call_annotate_function",
        "evaluate_forward_ref",
        # Python 3.14 (PEP 734): code run in a subinterpreter is outside the render harness's audit hook.
        "concurrent",
        "interpreters",
        "InterpreterPoolExecutor",
        "_interpreters",
        "_interpqueues",
        "_interpchannels",
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
        # Modules plotnine and altair re-export as attributes (survey of 2026-10-24): plotnine's
        # `options.quarto` binds `os` and `sys` and reads the file an environment variable names; altair's
        # `utils` and `vegalite.v6.api` hand out jsonschema, referencing, narwhals (`nw`), jinja2, uuid,
        # vl_convert, pyarrow and polars.
        "quarto",
        "jsonschema",
        "referencing",
        "nw",
        "narwhals",
        "jinja2",
        "uuid",
        "vl_convert",
        "pyarrow",
        "polars",
        # cairosvg's `css` and `parser` hand out cssselect2, whose selector compiler `eval`s the code it builds: a
        # forged token object reaches an unquoted slot of it (the pygal spike of 2026-10-26); tinycss2 and
        # webencodings are its parser, cairocffi the C binding behind `.cairo` (survey of 2026-10-24).
        "cssselect2",
        "tinycss2",
        "webencodings",
        "cairocffi",
        # lets-plot's `LazyModule` proxies import their module by name on the first attribute access:
        # `geom_imshow_.png.Reader(filename=...)` reads any file (survey of 2026-10-24, its refute pass).
        "geopandas",
        "png",
        "palettable",
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
        "execeval",  # altair.utils.execeval compiles and execs text
        "server",  # altair.utils.server opens a port and a browser; the attribute is the stdlib http.server
        "html",  # altair.utils.html: Jinja templates built from text (`environment.from_string`)
        "jupyter",  # altair.jupyter re-exports importlib's `find_spec`
        # pygal and cairosvg (surveys of 2026-10-24): pygal's ElementTree proxy, re-exported as `pygal.svg.etree` and
        # `pygal.graph.map.etree` (`parse`, `ElementTree(root).write(path)`); cairosvg's pytest module.
        "etree",
        "test_api",
        # lets-plot (survey of 2026-10-24): the browser launcher, geocoding, tile and geocoder URLs, the livemap geom.
        "frontend_context",
        "geo_data",
        "settings_utils",
        "tilesets",
        "geom_livemap_",
    }
)
"""Submodules of the allowed packages that test, build, start processes, run LaTeX or import by name (validator
review of 2026-10-14: `np.testing.measure` compiles and execs its string). Banned like `ESCAPE_ATTRIBUTES`: as an
attribute on any object, as a `from` import and as an import path component below its root. A test pins that every
public first-level submodule of numpy, pandas, matplotlib, seaborn, scikit-learn and the plotting libraries is
either reviewed as safe or banned by name (here, or on its own module in `MODULE_ESCAPES`), so a library upgrade
that adds one fails until someone looks at it."""
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
        "Memory",  # joblib's disk cache, `Memory(location)`; sklearn.datasets._lfw re-exports it
        "check_memory",  # sklearn.utils.validation turns a path into that cache: `check_memory("dir")`
        "Parallel",  # sklearn.utils.parallel: `temp_folder` is its eighth positional parameter
        # plotnine (survey of 2026-10-24)
        "save_as_pdf_pages",  # writes a multipage PDF to any path
        "watermark",  # draws any image file the caller names (`matplotlib.image.imread`)
        "PlotnineAnimation",  # an ArtistAnimation whose `save` starts ffmpeg
        "Environment",  # plotnine.mapping.Environment: `eval` of text in a captured namespace
        "bpal",  # mizani's brewer_pal stores an unchecked `getattr(module, name)`: the builtins dict by name
        # altair (survey of 2026-10-24): exec, server, browser, plugin and import-by-name routes
        "eval_block",
        "serve",
        "find_open_port",
        "generate_handler",
        "open_html_in_browser",
        "browser_renderer",
        "jupyter_renderer",
        "open_editor",
        "entry_points",  # importlib.metadata.entry_points: every installed entry point's `.load()`
        "importlib_metadata_get",
        "PluginRegistry",  # `.enable(<unregistered name>)` loads an entry point
        "renderers",
        "vegalite_compilers",
        "find_spec",
        "exec_module",
        "import_vl_convert",
        "import_vegafusion",
        "import_pyarrow_interchange",
        "register_font_directory",  # vl_convert reads every font file under a directory
        "javascript_bundle",  # embeds caller JavaScript in the HTML artifact
        "UrlData",  # a data URL the renderer fetches
        "topo_feature",
        # The adversarial pass over the surveys (2026-10-25): an image mark's `file://` href is read from disk by
        # vl_convert's SVG renderer and drawn into the PNG, past the audit hook (native code) and the no-egress
        # sandbox; `alt.limit_rows(df)` hands out a narwhals frame whose `.implementation.to_native_namespace()`
        # is the pyarrow module (file reads and writes with no audit event); `transformed_data` evaluates the
        # chart's datasets in VegaFusion, which loads `url` data from files.
        "mark_image",
        "Url",
        "UrlValue",
        "UrlDatum",
        "limit_rows",
        "to_eager_narwhals_dataframe",
        "arrow_table_from_dfi_dataframe",
        "to_native_namespace",
        "transformed_data",
        "JupyterChart",
        "display",
        # Every plotnine plot carries `.environment`, the Environment captured from the plot's frame, whose
        # `.namespace["os"]` is the `os` module as a value (the same pass); banning the class name alone leaves
        # the instance route open. `qplot` evaluates its aesthetics like `aes` and takes `data=` and labels
        # next to them, so the expression rule cannot tell its arguments apart; `from_formula` hands its first
        # positional to patsy like the banned `formula=` keyword (the validator-tests pass of 2026-10-25).
        "environment",
        "namespace",
        "namespaces",
        "qplot",
        "from_formula",
        # lets-plot (survey of 2026-10-24): the writers next to `ggsave` (`to_html` is in `BANNED_IO`, `show` in
        # `BANNED_ATTRIBUTES`), the browser hook and its page context, import by name (`LazyModule("subprocess")`),
        # the livemap geom and its tile configs, the geocoders and the requests they send, and `pkgutil.extend_path`
        # left on the package root. No catalogue file of another library uses any of these names.
        "to_png",
        "to_svg",
        "to_pdf",
        "setup_show_ext",
        "WebBrHtmlPageContext",
        "LazyModule",
        "geom_livemap",
        "maptiles_zxy",
        "maptiles_lets_plot",
        "maptiles_solid",
        "maptiles_chessboard",
        "geocoding_service",
        "geocode",
        "geocode_cities",
        "geocode_counties",
        "geocode_states",
        "geocode_countries",
        "reverse_geocode",
        "get_geocodes",
        "get_centroids",
        "get_boundaries",
        "get_limits",
        "extend_path",
    }
)
"""Public functions and classes of the allowed modules that exec, start a process, import by name, fetch or write
files (survey of 2026-10-14). Banned as attributes on any object and as `from` imports, like `BANNED_ATTRIBUTES`;
`_UNSAFE_HELPER_PATTERN` adds the families `print_*` (a canvas writing any format to any path, past the savefig
rule) and `x13_*` (statsmodels' X-13 runners)."""
MODULE_ESCAPES: frozenset[str] = frozenset(
    {
        "calendar.main",
        "random.main",
        # `pathlib.Path` re-exported (plotnine's `data` and `ggplot` modules, altair's `utils.data` and
        # `display`), a `Path` instance into the package, and `importlib.metadata.version` bound on the
        # package (reads any installed distribution's metadata); `Path` and `version` are plausible names
        # elsewhere (`matplotlib.path.Path`, `numpy.version`).
        "plotnine.data.Path",
        "plotnine.data.DATA_DIR",
        "plotnine.ggplot.Path",
        "altair.utils.data.Path",
        "altair.vegalite.v6.display.Path",
        "altair.version",
        "mizani.version",
        # cairosvg (surveys of 2026-10-24): `parser` reads the main input from any path or URL with an unrestricted
        # fetcher, `surface` writes any path through libcairo and hands out cairocffi, `url` is urlopen, `image`
        # hands out PIL's `Image` and `ImageOps`, `css` cssselect2, `features` the locale module, `test_api` runs
        # pytest; `Path` is pathlib's class and `ROOT` a `Path` instance (the package directory). Each name is
        # plausible elsewhere (`matplotlib.image`, `matplotlib.path.Path`, a `url` column).
        "cairosvg.Path",
        "cairosvg.ROOT",
        "cairosvg.parser",
        "cairosvg.surface",
        "cairosvg.url",
        "cairosvg.image",
        "cairosvg.css",
        "cairosvg.features",
        "cairosvg.test_api",
        # lets-plot: `LetsPlot.set` points the HTML's script and the geocoder at any URL, `setup_show_ext` installs
        # the browser launcher, `cfg` is the private configuration module under a public name (the survey's refute
        # pass: banned by path, because `cfg` is a common name).
        "lets_plot.LetsPlot.set",
        "lets_plot.LetsPlot.setup_show_ext",
        "lets_plot.cfg",
    }
)
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
    "vl_convert": "altair writes the PNG itself through chart.save(); import nothing from vl_convert",
    "plotnine.data": _DATA_FROM_DF,
    "altair.datasets": _DATA_FROM_DF,
    "lets_plot.geo_data": _DATA_FROM_DF,
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
        "pygal_maps_world",
        "cairocffi",
        "cssselect2",
        "tinycss2",
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
_RC_CONSUMERS = frozenset({"rc_context", "context", "theme_matplotlib"})
"""Calls that take settings as a dict (`mpl.rc_context({...})`, `plt.style.context({...})`, plotnine's
`theme_matplotlib(rc={...})`): literal keys only."""
_RC_FILE_READERS = frozenset({"rc_context", "theme_matplotlib"})
"""`rc_context(rc, fname)` and plotnine's `theme_matplotlib(rc, fname)` load every setting from the file `fname`
names (`rc_params_from_file`), whose keys the string rule never sees: no second positional, no `fname=`."""
BANNED_KEYWORDS = frozenset(
    {"usetex", "backend", "memory", "temp_folder", "cachedir", "formula", "url", "file_obj", "unsafe", "url_fetcher"}
)
"""Keyword arguments banned on any call: `usetex=True` sends a text through LaTeX (`ax.text`, `TextPath`, `plt.rc`),
`backend=` imports a backend module by name (`savefig(backend="module://...")`). `memory=` is a joblib cache
directory that scikit-learn writes fitted steps to (`Pipeline`, `make_pipeline`, `AgglomerativeClustering`,
`FeatureAgglomeration`, `OPTICS`, all keyword-only), `temp_folder=` the directory joblib's `Parallel` spills arrays to,
and `cachedir=` joblib's older name for a cache directory. The render guard refuses those writes in the sandbox; the
keywords are banned so the exported code makes none on the machine that runs it (survey of the admitted libraries'
public signatures, 2026-10-14: `location=` names joblib's cache directory too, but matplotlib's colorbar and secondary
axes take it as a side, so joblib's `Memory` is banned by name instead, in `UNSAFE_HELPERS`). `formula=` (plotnine's
`stat_smooth`, `stat_quantile` and `geom_smooth`, statsmodels' `from_formula`) hands a string to patsy, which
`exec`s Python while it parses it; the render guard refuses that `exec`, so the keyword is refused first (no
matplotlib or seaborn catalogue file uses it). `url=` names an image mark's href in altair (`encode(url=...)`,
`MarkDef(url=...)`), which vl_convert reads from disk for a `file://` value, and matplotlib artists' SVG hyperlink,
which a PNG never carries (one catalogue file, altair's image mark, uses it); cairosvg's `svg2png` reads its main
input from any path or URL with `url=` (2 pygal catalogue files) and from a file object with `file_obj=`,
`unsafe=True` lets the SVG's entities and hrefs read files and fetch, and `url_fetcher=` replaces the fetcher that
keeps hrefs to `data:` URLs (survey of 2026-10-24; no catalogue file passes any of the three)."""
LIBRARY_BANS: dict[str, frozenset[str]] = {
    # `Chart.from_dict` and `from_json` build a chart from a spec the string rules cannot read (an image mark with
    # a `file://` href); pandas' `DataFrame.from_dict` is ordinary with the other libraries, so the ban is altair's.
    # `data_transformers.enable("json")` and `enable("csv", filename=...)` make every save write the chart's data
    # to a file, and `.register(name, fn)` with `.enable(name)` is the plugin hook of every altair registry
    # (renderers, themes, compilers); the catalogue only calls `data_transformers.disable_max_rows()`.
    "altair": frozenset({"from_dict", "from_json", "enable", "register"}),
    # pygal and cairosvg (surveys of 2026-10-24, the pygal draft of 2026-10-26): pygal's renderers that open a
    # browser or import pyquery, lxml, flask or django, and the live ElementTree (`render_tree`, `add_xml_filter`,
    # `xml_filters`); `pygal.util.cut`, an unchecked `getattr` by string (`cut([obj], "ctypes")`), and `template`,
    # `str.format` on a caller string; the plugin entry points and their import hook; `Config._update`, which merges
    # any dict into a chart's options past the `css`/`js` rule. cairosvg's other writers and its surfaces, which
    # libcairo opens natively, its parser and fetchers; cairocffi as `.cairo`, its `ffi`, `dlopen` and
    # `find_library` (which runs ldconfig and gcc), the pycairo shim and the file readers and writers of its
    # surfaces. `cut` is pandas' binning function with the other libraries, the rest are plausible names there.
    "pygal": frozenset(
        {
            "render_in_browser",
            "render_pyquery",
            "render_table",
            "render_response",
            "render_django_response",
            "render_tree",
            "add_xml_filter",
            "xml_filters",
            "cut",
            "template",
            "entry_points",
            "PluginImportFixer",
            "_update",
            "svg2pdf",
            "svg2ps",
            "svg2eps",
            "svg2svg",
            "SURFACES",
            "Tree",
            "fetch",
            "safe_fetch",
            "read_url",
            "fetch_url",
            "cairo",
            "ffi",
            "dlopen",
            "find_library",
            "install_as_pycairo",
            "write_to_png",
            "create_from_png",
            "PDFSurface",
            "PSSurface",
            "SVGSurface",
            "PNGSurface",
            "EPSSurface",
        }
    ),
    # `LayerSpec.props()` hands out the spec's own dict, so code could rewrite a field the native bridge reads (an
    # image layer's `href`) after the check (the lets-plot spike of 2026-10-26); `props` is a plausible name elsewhere.
    "letsplot": frozenset({"props"}),
}
"""Names banned as attributes and `from` imports in one library's profile only, like `UNSAFE_HELPERS` there."""
_STRING_DISPATCH_METHODS = frozenset({"agg", "aggregate", "apply", "transform", "applymap"})
EXPRESSION_CALLS = frozenset({"aes", "after_stat", "after_scale", "stage", "facet_wrap", "facet_grid"})
"""plotnine calls whose string arguments it compiles and evaluates when they are not column names (module
docstring, "Expression strings"); `qplot`, which evaluates its aesthetics the same way, is banned by name."""
FACET_CALLS = frozenset({"facet_wrap", "facet_grid"})
FACET_KEYWORDS = frozenset({"facets", "rows", "cols"})
"""The facet calls' formula arguments; their other keywords (`ncol`, `scales`, `labeller`) are no expressions."""
EXPRESSION_LIBRARIES = frozenset({"plotnine"})
"""The profiles that check `EXPRESSION_CALLS`."""
_FORMULA_SPLIT = re.compile(r"[~+]")
"""A facet formula's sides and terms (`"pane ~ ."`, `"a + b ~ c"`), which plotnine evaluates one by one."""
PYGAL_CONFIG_KEYS = frozenset({"css", "js", "defs"})
"""pygal's chart options that read files or embed markup (module docstring, "pygal's config")."""
PYGAL_PACKAGE_CSS = frozenset({"file://style.css", "file://graph.css", "file://base.css"})
"""pygal's own stylesheets (`Config.css` defaults and `base.css`), which a `css=` list repeats before its `inline:`
rules (14 catalogue files); pygal reads them from its package's `css` directory."""
_INLINE_CSS = "inline:"
_GOOGLE_FONT = "googlefont:"
_SVG_NAMESPACE = re.compile(r"\{?http://www\.w3\.org/(?:2000/svg|1999/xlink)(?=[\"'}\s]|$)")
"""The SVG and XLink namespace names, also in Clark notation (`{...}rect`), followed by a quote, `}`, whitespace or the
end; an XML parser compares them and never fetches them, so pygal's URL rule drops them before it looks."""
LETSPLOT_BUILDERS = frozenset({"lets_plot.layer_tooltips", "lets_plot.layer_labels", "lets_plot.smooth_labels"})
"""lets-plot's tooltip and label builders, whose `.format(field, format)` sets a spec field (module docstring)."""
LETSPLOT_BUILDER_METHODS = frozenset(
    {
        "line",
        "format",
        "title",
        "anchor",
        "min_width",
        "disable_splitting",
        "color",
        "size",
        "inherit_color",
        "eq",
        "label_x",
        "label_y",
    }
)
"""The builders' methods, each of which returns the builder itself (lets-plot 4.11.0, `plot/tooltip.py` and
`plot/annotation.py`), so a chain of them never reaches a string's `format`."""
_LETSPLOT_OBJECT = "lets_plot.LetsPlot"
_DIRECT_CALL_ONLY = SAVE_NAMES | {"open"}
"""Attributes that may only be called where they are named, so the save rule sees their target."""
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
    scan.security(library, COMMON_IMPORTS | SHARED_SCIENCE_IMPORTS | library_imports, save_rule(library))
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


def _is_text(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _is_inline_css(node: ast.expr) -> bool:
    """A pygal `css` entry that pygal inlines as CSS text: a string or an f-string whose literal start is `inline:`."""
    head = node.values[0] if isinstance(node, ast.JoinedStr) and node.values else node
    return isinstance(head, ast.Constant) and isinstance(head.value, str) and head.value.startswith(_INLINE_CSS)


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


_STYLE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
"""A matplotlib style name (`ggplot`, `seaborn-v0_8-whitegrid`): no dot and no separator, so not a file path, which
`style.context` would read as a style sheet of settings the key rules never see (#12177 review)."""


def _is_literal_settings(node: ast.AST | None, *, style_names: bool = False) -> bool:
    """A settings argument whose keys can be checked: `None`, a dict literal whose every key is a string literal (no
    `**` unpacking) and, with `style_names` (`style.context`), a string literal that is a style name, never a path."""
    if node is None or (isinstance(node, ast.Constant) and node.value is None):
        return True
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return style_names and _STYLE_NAME.match(node.value) is not None
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
        self.library = ""
        """The profile's library id; empty in the DATA profile."""
        self.url_exempt: set[ast.AST] = set()
        """String literals the URL rule lets pass: pygal's own stylesheets in a `css=` list (`_check_pygal_config`)."""
        self.allowed_imports: frozenset[str] = frozenset()
        self.library_bans: frozenset[str] = frozenset()
        """`LIBRARY_BANS` of the profile's library: banned as attributes and `from` imports in this scan."""
        self.library_imports: frozenset[str] = frozenset()
        """`LIBRARY_IMPORTS` of the profile's library: the modules whose save calls the save rule accepts."""
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

    def security(self, library: str, allowed_imports: frozenset[str], rule: SaveRule) -> None:
        self.library = library
        self.library_bans = LIBRARY_BANS.get(library, frozenset())
        self.library_imports = LIBRARY_IMPORTS.get(library, frozenset())
        self._check_imports(library, allowed_imports, rule)
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
        if library == "pygal":
            self._check_pygal_config()  # before the strings: it marks pygal's own stylesheets for the URL rule
        if library == "letsplot":
            self._check_letsplot_object()
        self._check_strings()
        self._check_save(rule)
        self._check_save_names()
        if library in EXPRESSION_LIBRARIES:
            self._check_expression_strings()

    # -- DATA ----------------------------------------------------------------------------

    def data(self, allowed_imports: frozenset[str]) -> None:
        """Every SECURITY check but the save target, then `df` at the top and no rows written out (module docstring).

        A data snippet saves nothing: every save name and `.open` is a `banned-call` (`_check_save` without a rule).
        """
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
        self._check_save(None)
        self._check_save_names()
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

    def _check_imports(self, library: str, allowed: frozenset[str], rule: SaveRule | None = None) -> None:
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
                self._check_function_name(alias.name, alias, rule, from_node.module)
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
        if _module_allowed(path, DENIED_IMPORTS):
            return False  # the allowlist reports a denied path with its own message (`sklearn.datasets`)
        escape = next((name for name in MODULE_ESCAPES if _module_allowed(path, [name])), None)
        if escape is not None:
            self.ban_import(path, f"reaches the banned name '{escape}'", node)
            return True
        for position, part in enumerate(path.split(".")):
            if part in BANNED_ATTRIBUTES or part in BANNED_IO or _BANNED_IO_PATTERN.match(part):
                self.ban_import(path, f"reaches the banned name '{part}'", node)
                return True
            # `import statsmodels.api.datasets as d` would spell no banned name afterwards (review of 2026-10-25).
            if position and (part in _ANY_RECEIVER_ESCAPES or _is_unsafe_helper(part)):
                self.ban_import(path, f"reaches the banned name '{part}'", node)
                return True
            if position and part.startswith("_"):
                self.ban_import(path, f"reaches the private module '{part}'", node)
                return True
        return False

    def _check_function_name(self, name: str, node: ast.AST, rule: SaveRule | None, module: str = "") -> None:
        """A name reached by a `from` import: the attribute, escape and I/O sets apply, and no private name.

        A save name is refused here unless the library's rule lists it and `module` is the plotting library's own
        (`from plotnine import ggsave`, 16 catalogue files); `from numpy import save` is refused in every profile,
        because its call would reach the save rule under the library's name.
        """
        foreign_save = name in SAVE_NAMES and (
            rule is None or name not in rule.names or not _module_allowed(module, self.library_imports)
        )
        if (
            name in BANNED_ATTRIBUTES
            or name in _ANY_RECEIVER_ESCAPES
            or name in self.library_bans
            or _is_unsafe_helper(name)
        ):
            self.add("banned-attribute", f"'{name}' is not allowed", node)
        elif name in BANNED_IO or foreign_save or _BANNED_IO_PATTERN.match(name):
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
            elif attribute.attr == "format" and self.library == "letsplot" and self._is_builder_format(attribute):
                continue  # lets-plot's tooltip and label builders (module docstring, "lets-plot")
            elif (
                attribute.attr in BANNED_ATTRIBUTES
                or attribute.attr in _ANY_RECEIVER_ESCAPES
                or attribute.attr in self.library_bans
                or _is_unsafe_helper(attribute.attr)
            ):
                self.add("banned-attribute", f"attribute '.{attribute.attr}' is not allowed", attribute)
            elif attribute.attr in _DIRECT_CALL_ONLY and not self._is_called(attribute):
                # `f = plot.save; f("x")` would hide the target from the save rule (`_check_save`).
                self.add("banned-attribute", f"'.{attribute.attr}' may only be called directly", attribute)
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
        """`BANNED_KEYWORDS` as a keyword, or as a string key of a dict literal unpacked into a call (`**{"memory":
        "dir"}`). A dict built elsewhere and unpacked (`**options`) is not followed; the render guard refuses the
        write such a keyword would make in the sandbox."""
        for keyword in self.of(ast.keyword):
            if keyword.arg in BANNED_KEYWORDS:
                self.add("banned-keyword", f"the keyword '{keyword.arg}=' is not allowed", keyword)
            elif keyword.arg is None and isinstance(keyword.value, ast.Dict):
                pending = [keyword.value]
                while pending:  # `**{**{"memory": ...}}`: an unpacked entry has the key None and a dict value
                    literal = pending.pop()
                    for key, value in zip(literal.keys, literal.values, strict=True):
                        if key is None and isinstance(value, ast.Dict):
                            pending.append(value)
                        elif isinstance(key, ast.Constant) and key.value in BANNED_KEYWORDS:
                            self.add("banned-keyword", f"the keyword '{key.value}=' is not allowed", key)

    def _check_settings(self) -> None:
        """matplotlib settings are written only with keys the string rule can read (`rc-key`).

        `rcParams` (and its two default copies) may be subscripted, with a string literal
        when the item is written or deleted, or be the receiver of a called `.update`, `.get`
        or `.copy`, whose `.update` arguments are dict literals with string-literal keys; it
        is never a value (`r = mpl.rcParams`) or a target. `rc_context(...)` and every `rc=`
        argument take such a dict and no file (`fname`, a second argument); `style.context(...)`
        takes such a dict or a style name, never a path; `rc(group, **settings)` takes a
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
            # `rc_context(rc, fname)` and `theme_matplotlib(rc, fname)` load every setting from the file `fname`
            # names (#12177 review; plotnine survey of 2026-10-24).
            reads_file = name in _RC_FILE_READERS and (
                len(call.args) > 1 or any(keyword.arg == "fname" for keyword in call.keywords)
            )
            style = name == "context"
            if (
                (name in _RC_CONSUMERS and unpacked)
                or reads_file
                or not all(_is_literal_settings(value, style_names=style) for value in settings)
            ):
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
        if (
            name in BANNED_NAMES
            or name in BANNED_ATTRIBUTES
            or name in BANNED_IO
            or name in _BUFFER_WRITERS
            or name in SAVE_NAMES
        ):
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
            pygal = self.library == "pygal"
            if pygal and isinstance(constant.value, str) and _GOOGLE_FONT in text:
                self.add("url-literal", "string literal names a Google font, which the chart fetches", constant)
            urls = _SVG_NAMESPACE.sub("", text) if pygal else text
            if _URL_IN_TEXT.search(urls) and constant not in self.url_exempt:
                hint = f" → {DATA_IO_MESSAGE}" if self.data_profile else ""
                self.add("url-literal", f"string literal contains a URL or a file:/data: scheme{hint}", constant)
            if isinstance(constant.value, str) and _is_unsafe_setting(text):
                self.add("rc-key", f"string literal names a setting: {RC_KEY_MESSAGE}", constant)

    def _is_called(self, attribute: ast.Attribute) -> bool:
        call = self.parents.get(attribute)
        return isinstance(call, ast.Call) and call.func is attribute

    def _check_save(self, rule: SaveRule | None) -> None:
        """Every call of a save name against the library's save rule (module docstring, "The save").

        Without a rule (the DATA profile) every save name and `.open` is a `banned-call`.
        """
        wrote_png = False
        for call in self.of(ast.Call):
            func = call.func
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                continue
            if name == "open" and isinstance(func, ast.Attribute):
                if rule is None or not rule.reopens:
                    self.add("banned-call", f"'{_snippet(func)}' is not allowed{self.io_hint('open')}", call)
                elif not call.args or not _is_theme_target(call.args[0]) or call.keywords or len(call.args) > 1:
                    self.add("savefig-target", 'open may only reopen f"plot-{THEME}.png", with no other argument', call)
                continue
            if name not in SAVE_NAMES:
                continue
            # `np.save` under a rule that lists `save`: the receiver resolves to a module outside the plotting
            # library, so it is not the library's save (the validator-tests pass of 2026-10-25).
            path = self.resolve(func) if isinstance(func, ast.Attribute) else None
            foreign = path is not None and not _module_allowed(path, self.library_imports)
            if rule is None or name not in rule.names or foreign:
                hint = self.io_hint(name) if rule is None else f"; the plot is saved with {rule.verb}"
                self.add("banned-call", f"'{_snippet(func)}' is not allowed{hint}", call)
                continue
            wrote_png |= self._check_save_call(call, rule, name)
        if rule is not None and not wrote_png:
            self.add("savefig-target", f'no {rule.verb} of f"plot-{{THEME}}.png" found', None)

    def _check_save_call(self, call: ast.Call, rule: SaveRule, name: str) -> bool:
        """The file, the format and the keywords of one save call; whether it writes the PNG."""
        target = save_target(call, rule, name)
        png = target is not None and _is_theme_target(target)
        html = rule.html and target is not None and is_theme_target(target, HTML_SUFFIX)
        if not (png or html):
            files = 'f"plot-{THEME}.png"' + (' or f"plot-{THEME}.html"' if rule.html else "")
            self.add("savefig-target", f"{name} target must be exactly {files}", call)
        position = rule.target_position(name)
        if position < 0 and call.args:
            # `svg2png(bytestring, ...)`: the keyword-only save names its file with `write_to=` alone.
            self.add("savefig-target", f"{name} takes every argument by keyword", call)
        elif len(call.args) > position + 1:
            # `plot.save(f, None, "/tmp")` is `path=`, `plot.save(f, "pgf")` is `format=`, by position.
            self.add("savefig-target", f"{name} takes only the file by position; the rest go by keyword", call)
        if rule.directory is not None:
            # lets-plot's `ggsave` writes into `./lets-plot-images`, which it creates, unless `path=` names a directory.
            directory = next((keyword.value for keyword in call.keywords if keyword.arg == "path"), None)
            if not (isinstance(directory, ast.Constant) and directory.value == rule.directory):
                self.add("savefig-target", f'{name} must save with path="{rule.directory}"', call)
        allowed = rule.allowed_keywords(name)
        for keyword in call.keywords:
            # `format="ps"` with a distiller or `format="pgf"` would start Ghostscript or LaTeX, whatever the name.
            fmt = keyword.value
            expected = "html" if html else "png"
            if keyword.arg == "format" and not (isinstance(fmt, ast.Constant) and fmt.value == expected):
                self.add("savefig-target", f'{name} format must be "{expected}" or left out', keyword)
            elif keyword.arg is None:
                self.add("savefig-target", f"{name} takes no **arguments", keyword)
            elif allowed is not None and keyword.arg not in allowed:
                self.add("savefig-target", f"{name} does not take '{keyword.arg}=' here", keyword)
        if any(isinstance(arg, ast.Starred) for arg in call.args):
            self.add("savefig-target", f"{name} takes no *arguments", call)
        return png

    def _check_save_names(self) -> None:
        """A save name keeps its own name and is reached only by calling it (module docstring, "The save").

        The save rule finds a save by its callee's name, so `from plotnine import ggsave as keep`, `g = ggsave`,
        `[ggsave][0](...)` and `partial(ggsave, plot)` would each write wherever their arguments say; `.save` and the
        other save attributes have the same rule in `_check_attributes`.
        """
        for from_node in self.of(ast.ImportFrom):
            for alias in from_node.names:
                bound = alias.asname or alias.name
                if bound == alias.name:
                    continue
                if alias.name in SAVE_NAMES:
                    self.add("banned-call", f"'{alias.name}' may only be imported under its own name", alias)
                elif bound in SAVE_NAMES:
                    self.add("banned-call", f"nothing may be imported under the save name '{bound}'", alias)
        for name in self.of(ast.Name):
            if name.id in SAVE_NAMES and isinstance(name.ctx, ast.Load):
                parent = self.parents.get(name)
                if not (isinstance(parent, ast.Call) and parent.func is name):
                    self.add("banned-call", f"'{name.id}' may only be called directly", name)

    def _check_expression_strings(self) -> None:
        """plotnine's expression arguments: literals the walk can read, each string walked as code (module docstring,
        "Expression strings")."""
        for call in self.of(ast.Call):
            func = call.func
            name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
            if name not in EXPRESSION_CALLS:
                continue
            facets = name in FACET_CALLS
            arguments: list[ast.expr] = []
            for position, argument in enumerate(call.args):
                if isinstance(argument, ast.Starred):
                    self.add("banned-call", f"{name} takes no *arguments", argument)
                elif not facets or position == 0:
                    arguments.append(argument)
            for keyword in call.keywords:
                if keyword.arg is None:
                    # `aes(**mapping)` evaluates strings the walk cannot see (the adversarial pass of 2026-10-25).
                    if isinstance(keyword.value, ast.Dict) and all(key is not None for key in keyword.value.keys):
                        arguments.extend(keyword.value.values)
                    else:
                        self.add("banned-call", f"{name} takes ** only from a dict literal", keyword)
                elif not facets or keyword.arg in FACET_KEYWORDS:
                    arguments.append(keyword.value)
            for argument in arguments:
                self._check_expression_argument(argument, name)

    def _check_expression_argument(self, node: ast.expr, name: str) -> None:
        """One argument plotnine evaluates: a literal (a string walked as code, a number, None), a list or tuple of
        them (`facet_wrap(["a", "b"])`), a call of another expression function (`aes(y=after_stat("count"))`), or a
        name bound once at module level to a string literal (`col = "x"`, then `aes(x=col)`); anything else may
        carry a string the walk cannot read."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                self._check_expression(node.value, name, node)
            return
        if isinstance(node, ast.List | ast.Tuple):
            for item in node.elts:
                self._check_expression_argument(item, name)
            return
        if isinstance(node, ast.Call):
            callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if callee in EXPRESSION_CALLS:
                return  # checked as a call of its own
        if isinstance(node, ast.Name):
            literal = self._module_string(node.id)
            if literal is not None and isinstance(literal.value, str):
                self._check_expression(literal.value, name, literal)
                return
        self.add("banned-call", f"{name} takes its column names as string literals, not as an expression", node)

    def _module_string(self, variable: str) -> ast.Constant | None:
        """The string literal a module-level `variable = "..."` binds, when nothing else binds `variable`."""
        value = self._module_value(variable)
        return value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None

    def _module_value(self, variable: str, read: Callable[[ast.Name], bool] | None = None) -> ast.expr | None:
        """The value a module-level `variable = value` binds, when nothing else in the file binds `variable`; with
        `read`, only when every read of the name passes it too (a list or a dict nothing can change after the check).
        """
        if self._bindings(variable) != 1:
            return None
        for statement in self.tree.body:
            target = _single_name_target(statement)
            if not isinstance(statement, ast.Assign | ast.AnnAssign) or target is None or target.id != variable:
                continue
            reads = [name for name in self.of(ast.Name) if name.id == variable and isinstance(name.ctx, ast.Load)]
            if read is not None and not all(read(name) for name in reads):
                return None
            return statement.value
        return None

    def _bindings(self, variable: str) -> int:
        """How many places bind `variable`: a store or a deletion of the name, a parameter, an import, a function or
        class name, an exception or `match` capture, a type parameter. A `case x:` would rebind a name the walk
        checked as a literal (`match "open('x')": case COLUMN: ...`), so every kind counts."""
        count = sum(1 for name in self.of(ast.Name) if name.id == variable and not isinstance(name.ctx, ast.Load))
        count += sum(1 for parameter in self.of(ast.arg) if parameter.arg == variable)
        imports: list[ast.Import | ast.ImportFrom] = [*self.of(ast.Import), *self.of(ast.ImportFrom)]
        count += sum(
            1 for node in imports for alias in node.names if (alias.asname or alias.name.split(".")[0]) == variable
        )
        named: list[ast.AST] = [
            *self.of(ast.FunctionDef),
            *self.of(ast.AsyncFunctionDef),
            *self.of(ast.ClassDef),
            *self.of(ast.ExceptHandler),
            *self.of(ast.MatchAs),
            *self.of(ast.MatchStar),
            *self.of(ast.TypeVar),
            *self.of(ast.ParamSpec),
            *self.of(ast.TypeVarTuple),
        ]
        count += sum(1 for node in named if getattr(node, "name", None) == variable)
        count += sum(1 for node in self.of(ast.MatchMapping) if node.rest == variable)
        return count

    def _check_expression(self, text: str, call_name: str, node: ast.Constant) -> None:
        """One expression string: every parsable term walked with this profile's name, attribute, call, save and
        buffer-writer rules. A bare identifier and a text that does not parse are column names plotnine looks up."""
        for term in [text, *_FORMULA_SPLIT.split(text)]:
            term = term.strip()
            if not term or term == "." or term.isidentifier():
                continue
            try:
                expression = ast.parse(term, mode="eval").body
            except SyntaxError, ValueError:
                continue  # plotnine can only evaluate what compiles: this is a column name such as "True Label"
            inner = _Scan(ast.Module(body=[ast.Expr(expression)], type_ignores=[]))
            inner.aliases = self.aliases
            inner.import_bindings = self.import_bindings
            inner.allowed_imports = self.allowed_imports
            inner.library_imports = self.library_imports
            inner.library_bans = self.library_bans
            inner.os_names = self.os_names
            inner._check_os_use()
            inner._check_names()
            inner._check_attributes()
            inner._check_attribute_surface()
            inner._check_calls()
            inner._check_keywords()
            inner._check_buffer_writers()
            inner._check_statements()
            inner._check_strings()
            inner._check_save(None)
            inner._check_save_names()  # `aes(x="(lambda g: g(p, 'x.pdf'))(ggsave)")` reaches the plot's namespace
            for finding in inner.findings:
                self.add(finding.rule, f"in the {call_name} expression: {finding.message}", node)
            if term == text:
                break  # the whole string parsed: its terms are already in it

    # -- pygal and lets-plot -------------------------------------------------------------

    def _check_pygal_config(self) -> None:
        """pygal's `css`, `js` and `defs` options as keywords, `**` arguments and attributes (module docstring,
        "pygal's config")."""
        for keyword in self.of(ast.keyword):
            if keyword.arg in PYGAL_CONFIG_KEYS:
                self._check_pygal_option(keyword.arg, keyword.value, keyword)
            elif keyword.arg is None:
                self._check_pygal_options(keyword)
        for attribute in self.of(ast.Attribute):
            if attribute.attr not in PYGAL_CONFIG_KEYS:
                continue
            parent = self.parents.get(attribute)
            if attribute.attr == "defs":
                self.add("banned-attribute", "'.defs' is not allowed: it is raw SVG markup", attribute)
            elif (
                isinstance(attribute.ctx, ast.Store)
                and isinstance(parent, ast.Assign)
                and len(parent.targets) == 1
                and parent.targets[0] is attribute
            ):
                self._check_pygal_option(attribute.attr, parent.value, parent)
            else:
                # `chart.css += [...]`, `chart.css.append(...)`, `chart.css[0] = ...` or `x = chart.css`: the list
                # would change after the check.
                message = f"'.{attribute.attr}' may only be assigned a whole list, as in .{attribute.attr} = [...]"
                self.add("banned-attribute", message, attribute)

    def _check_pygal_option(self, key: str, value: ast.expr, node: ast.AST) -> None:
        """One `css`, `js` or `defs` value: `defs` never, `js` an empty list, `css` a list of `inline:` texts and
        pygal's own stylesheets, which the URL rule then lets pass."""
        if key == "defs":
            self.add("banned-keyword", "the keyword 'defs=' is not allowed: it is raw SVG markup", node)
            return
        if isinstance(value, ast.Name):
            value = self._module_value(value.id, self._is_option_read) or value
        if not isinstance(value, ast.List | ast.Tuple):
            self.add("banned-keyword", f"{key}= takes a list literal, or a name bound once to one", node)
            return
        if key == "js":
            if value.elts:
                self.add("banned-keyword", "js= takes only [] (an entry is a script file read or fetched)", node)
            return
        for item in value.elts:
            if isinstance(item, ast.Name):
                item = self._module_value(item.id) or item
            if isinstance(item, ast.Constant) and item.value in PYGAL_PACKAGE_CSS:
                self.url_exempt.add(item)
            elif not _is_inline_css(item):
                message = "css= takes only 'inline:...' texts and pygal's own file://style.css, graph.css and base.css"
                self.add("banned-keyword", message, node)

    def _is_option_read(self, name: ast.Name) -> bool:
        """`name` is read only where the config rule checks it: as a `css=` or `js=` value, or assigned to `.css` or
        `.js`."""
        parent = self.parents.get(name)
        if isinstance(parent, ast.keyword):
            return parent.arg in ("css", "js")
        return (
            isinstance(parent, ast.Assign)
            and parent.value is name
            and len(parent.targets) == 1
            and isinstance(parent.targets[0], ast.Attribute)
            and parent.targets[0].attr in ("css", "js")
        )

    def _check_pygal_options(self, keyword: ast.keyword) -> None:
        """A `**` argument: a dict literal with string keys, or a name bound once at module level to one and used only
        as `**name`, whose `css`, `js` and `defs` keys are checked like keywords."""
        value: ast.expr | None = keyword.value
        if isinstance(value, ast.Name):
            value = self._module_value(value.id, self._is_unpacked)
        if not (
            isinstance(value, ast.Dict)
            and all(isinstance(key, ast.Constant) and isinstance(key.value, str) for key in value.keys)
        ):
            message = "** takes only a dict literal with string keys, or a name bound once to one and only unpacked"
            self.add("banned-keyword", message, keyword)
            return
        for key, item in zip(value.keys, value.values, strict=True):
            if isinstance(key, ast.Constant) and key.value in PYGAL_CONFIG_KEYS:
                self._check_pygal_option(key.value, item, key)

    def _is_unpacked(self, name: ast.Name) -> bool:
        parent = self.parents.get(name)
        return isinstance(parent, ast.keyword) and parent.arg is None

    def _check_letsplot_object(self) -> None:
        """`LetsPlot` only as `LetsPlot.setup_html()` without arguments (module docstring, "lets-plot")."""
        nodes: list[ast.Name | ast.Attribute] = [*self.of(ast.Name), *self.of(ast.Attribute)]
        for node in nodes:
            if not isinstance(node.ctx, ast.Load) or self.resolve(node) != _LETSPLOT_OBJECT:
                continue
            attribute = self.parents.get(node)
            call = self.parents.get(attribute) if attribute is not None else None
            if not (
                isinstance(attribute, ast.Attribute)
                and attribute.value is node
                and attribute.attr == "setup_html"
                and isinstance(call, ast.Call)
                and call.func is attribute
                and not call.args
                and not call.keywords
            ):
                self.add("banned-call", "LetsPlot may only be used as LetsPlot.setup_html(), without arguments", node)

    def _is_builder_format(self, attribute: ast.Attribute) -> bool:
        """`layer_tooltips().line("@x").format("@x", ".1f")`: `.format` called with string literals on a chain of
        builder methods rooted in a call of a lets-plot builder bound only by its `from` import."""
        call = self.parents.get(attribute)
        if not (isinstance(call, ast.Call) and call.func is attribute):
            return False
        if not all(_is_text(argument) for argument in call.args):
            return False
        if not all(keyword.arg in ("field", "format") and _is_text(keyword.value) for keyword in call.keywords):
            return False
        node = attribute.value
        while isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in LETSPLOT_BUILDER_METHODS:
                node = func.value
                continue
            return isinstance(func, ast.Name) and self._is_builder_name(func.id)
        return False

    def _is_builder_name(self, variable: str) -> bool:
        """`variable` is bound once, by `from lets_plot import layer_tooltips [as variable]` or another builder, and
        no attribute of that name is ever assigned: `lets_plot.layer_tooltips = str` before the import would hand the
        import another callable."""
        if self._bindings(variable) != 1:
            return False
        for node in self.of(ast.ImportFrom):
            for alias in node.names if node.module and not node.level else []:
                if f"{node.module}.{alias.name}" in LETSPLOT_BUILDERS and (alias.asname or alias.name) == variable:
                    stores = self.of(ast.Attribute)
                    return not any(store.attr == alias.name and not isinstance(store.ctx, ast.Load) for store in stores)
        return False

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
