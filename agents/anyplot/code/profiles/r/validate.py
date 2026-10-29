"""Two-profile validator of the R (ggplot2) code profile, over tree-sitter.

The R counterpart of `code/validate.py`, with the same `Finding` and, where a rule has a
Python twin, the same rule id. `validate_security` runs on the normalised catalogue
original (eligibility) and on every adapted working form; `validate_adaptation` on adapted
code only. Both return an empty list for valid code and never raise: oversize code, text
that is not UTF-8, code tree-sitter cannot read and a string R would refuse are findings.

**Threat model.** The rules are hygiene, not the boundary (second opinion of 2026-10-24,
`agentic/specs/261024-agent-all-libraries.md`): the sandbox (gVisor, no egress, a
read-only root) and the exec filter (`agents/renderer/execdeny/`, which kills any process
start) protect the service; this list keeps the exported `plot.R`, which runs unguarded on
the user's machine, free of the model's accidental file, network and process access, and
makes the adapter's output boring. R can reach any function from a string in many ways;
each way the list knows is closed by name or by shape, and the named bypasses below are
tests.

SECURITY rules (rule ids in parentheses):

* **Denied names** (`banned-name`): `DENIED_NAMES` and the families of `DENIED_PATTERN`
  (`socket*`, `eval*`, `read.*`, `write*`, `file.*`, `dev.*`, `sys.*`, `Sys.*` except
  `Sys.time` and `Sys.Date`). The list holds process starts, connections, file and network
  I/O, sourcing and evaluation, every route from a string to a function (`get`,
  `match.fun`, `.env`, environments), attribute and binding tricks, the graphics devices
  other than the protected save (`png`, `svg`, ragg's `agg_*`; only `pdf(NULL)`, which 2
  catalogue files open for measuring grobs, is allowed), `aes_string`, glue and formula
  builders. `Sys.getenv` appears only in the theme statement. Beyond the design's list,
  names that read or write files, start an editor or reach environments joined it, but
  words common as variable names stay out (`dir`, `zip`, `browser`, `windows`, `debug`,
  `edit`). Where a denied name counts (owner decision of 2026-10-29, after the first pass
  refused every `source` column):
  - a bare name is refused as a callee and as a function-valued argument everywhere, and
    as any other value (an assignment's value or target, a return value, an element of
    `list()` or `c()`, an argument of an ordinary call) outside a data mask;
  - it is a column, and allowed, anywhere inside the arguments of a data-masking or
    tidy-select call (`DATA_MASK_CALLS`: `aes`, `vars`, the facets, the dplyr and tidyr
    verbs, base R's `subset` and `transform`; not the general evaluators `with`, `within`
    and `local`) and in the operands of `~` (formulas, a tribble's `~source` header,
    lambdas), and in the pure name positions: an argument's name and the field after `$`
    or `@`;
  - a string equal to a denied name is refused only where a string becomes a function: as
    a callee, as a function-valued argument, and inside a code string (below). Everywhere
    else a string is data, so a user's column called `source`, `file`, `load`, `options`
    or `body` passes.
  What still passes, honestly (review of 2026-10-29): inside a data mask a denied function
  can still be held as a value, as in `mutate(d, g = list(system))`, because a bare name
  there is read as a column. Every call shape the walk can see that would then run it is
  refused (next bullet): by its name, as a function literal called at once, through an
  index or a field (`g[[1]]("id")`, `x$f()`), through a parameter (`function(g) g("x")`),
  through `do.call` as a value, through a call that is no known builder
  (`identity(g)("id")`), or handed to a function-valued argument. What the walk cannot see
  is a function that calls a value it receives without naming it a function argument we
  list, such as a condition handler (`tryCatch(expr, error = g)`) or a package's internal
  callback; such a call gets that function's own arguments (a condition object, not a
  command), and the sandbox (no egress, a read-only root) and the exec filter (any
  process start kills the child) contain whatever it does. The check is hygiene for the
  exported `plot.R`, not the boundary.
* **Packages** (`banned-import`): `library()` and `require()` take one package of
  `LIBRARY_ALLOWLIST` or a dataset package (`DATASET_PACKAGES`, gapminder and
  palmerpenguins, which ADAPTATION refuses instead), by name or as a string, and no other
  argument (`character.only`).
  `pkg::name` takes a package of that list or `utils` and `tools`, with per-package rules
  (`NAMESPACE_FUNCTIONS`: `utils::head`, `tools::toTitleCase`,
  `gridExtra::arrangeGrob` only, owner decision of 2026-10-29; `ragg::agg_png` only as the
  protected save's device), and its name passes the denied-name rule; `:::` is refused.
* **Callees and functions** (`banned-call`): a call names its function. Refused callees
  (review of 2026-10-29, after measuring the catalogue): a string (`"system"("id")`, which
  R's parser turns into a call of `system`), a parenthesised value, a function literal
  called at once (`(function(f) f("id"))(x)`, `(\\(f) ...)(x)`; 0 catalogue calls), an
  index or a field (`f[[1]](...)`, `x$f(...)`, `x[i](...)`; 1 catalogue call, plotmath
  inside `expression()`, which `INERT_CALLS` exempts), a parameter of an enclosing
  function literal (`function(g) g("x")`; 0 catalogue calls), and a call's result unless
  the call is a builder of `CALLABLE_FACTORIES` (`colorRampPalette(...)(n)`,
  `scales::label_percent()(x)`, `hue_pal()(n)`; the catalogue's 12 such callees are all
  builders). `do.call` takes `rbind`, `cbind`, `c`, `paste` or `paste0` by name, or
  `"rbind"`, `"cbind"` or `"c"` as a string, and is never a value (`lapply(fns, do.call,
  args)` would call anything). A function-valued argument (`FUNCTION_ARGUMENTS`: `FUN`, `fun` and
  `fun.*` without `fun.args`, `.f`, `.fn`, `.fns`, `.funs`, `f`, `fn`, `method`,
  `labeller`, `transform`, `inverse`, and the positional function of the apply family,
  `FUNCTION_POSITIONS`) is a function literal, `\\(x)`, a `~` lambda, a literal (a
  method's name, a number for `lowess(f = )`), `pkg::name`, a name the file binds only to
  function literals or not at all, or a function factory (`FUNCTION_FACTORIES`: `list`,
  `c`, `Negate`, `Vectorize` over such values; ggplot2's labellers for `labeller =`, and
  scales' transformations, `transform_*()`, `*_trans()`, `trans_new()`, for `transform =`
  and `inverse =`): never a computed value such as `paste0("sys", "tem")`, which
  `match.fun` would resolve.
* **Tidy evaluation** (`banned-call`, `banned-keyword`): `!!` and `!!!` only on a column
  constant (a top-level name bound once to a string or a `c()` of strings); the left side
  of `:=` only `!!` of such a constant, a name, or a string without braces; `.names =`
  and `names_glue =` only a string whose braces are `{.col}` or `{.fn}`, because glue
  evaluates any other brace as code.
* **Code strings** (the rules above, inside the string): ggplot2 parses a string facet
  (`facet_wrap("~x")`, `facets`, `rows`, `cols`) and R a string formula as code, so every
  string literal in those positions, every string a facet argument names through a column
  constant, and every string that holds a `~` is parsed as R and walked with these rules
  as a data mask when it parses; a facet argument the walk cannot read (a call other than
  `vars()`, a computed name) is a `banned-call`. A formula position (`formula =` on any
  call, and the first positional of `FORMULA_FIRST`: `lm`, `glm`, `loess`, `nls`, `aov`,
  `model.frame`, `model.matrix`, `xtabs`, `formula` and the MASS and survival models)
  takes only a `~` literal, a string literal or a name bound once to one of them; the first
  positional of `FORMULA_OR_DATA_FIRST` (`aggregate`, the `*.test` functions, `boxplot`,
  `prcomp`, ...), whose data method takes a table, refuses only a string built at run
  time (`STRING_BUILDERS`: `paste0`, `sprintf`, `format`, `glue`, ..., or a name bound to
  one), because R parses a formula string and evaluates its names in the data.
* **Statements and keywords**: `<<-` and `->>` (`banned-statement`); the keyword `file =`
  on every call (`banned-keyword`; `cat(file =)`, `capture.output(file =)`), except
  `pdf(file = NULL)`.
* **The save and its names** (`savefig-target`): exactly one protected save
  (`regions.py`), whose arguments are all named and in `SAVE_KEYWORDS`, with
  `filename = sprintf("plot-%s.png", THEME)` and `device = ragg::agg_png`; any other
  `ggsave` call is refused. THEME is bound only by its theme statement, and `ggsave`,
  `sprintf` and `Sys.getenv` are never bound; a theme token is bound only by its own
  line (`banned-statement`).
* **Literals**: no URL (`url-literal`, the Python profile's pattern) and no string over
  `MAX_STRING_CHARS` characters (`string-length`).

ADAPTATION rules, with the Python profile's ids: exactly one `df <- load_user_data()`
(`placeholder-count`) and `load_user_data` nowhere else (`placeholder-use`); no random
draws (`rng`: `rnorm`, `rpois` and the other `r*` draws, `MASS::mvrnorm`; `set.seed`,
`sample`, `runif` and `jitter` stay allowed for jitter and subsampling); no data from
memory (`literal-data`: a `c(...)` with more than `MAX_LITERAL_NUMBERS` numbers, `data()`,
a built-in dataset of `DATASETS` read by name; `dataset-package`: `library()` or `pkg::` of
gapminder or palmerpenguins, owner decision of 2026-10-29); the palette prefix kept
(`palette-prefix`: `IMPRINT_PALETTE` or `IMPRINT` assigned once, as a `c()` of colour
strings that keeps the original entries in order and adds only the next Imprint
positions, and never written through a replacement form such as `IMPRINT_PALETTE[9] <-`).

Messages never echo string contents (a denied name a string equals is the list's word),
at most `MAX_SNIPPET_CHARS` of code. Findings are sorted by line.
"""

import re
from collections import Counter
from dataclasses import dataclass

from tree_sitter import Node

from core.palette import IMPRINT

from ....schemas import MAX_CODE_CHARS
from ...treesitter import (
    R_LITERALS,
    Argument,
    Source,
    Span,
    Visit,
    first_line,
    last_line,
    r_argument,
    r_arguments,
    r_assignment,
    r_bindings,
    r_callee,
    r_identifier,
    r_is_lookup,
    r_number,
    r_operator,
    r_string_value,
    r_unwrap,
    syntax_problems,
    visits,
)
from ...validate import MAX_LITERAL_NUMBERS, MAX_MESSAGE_CHARS, MAX_STRING_CHARS, Finding
from .coupling import DATASET_PACKAGES, LIBRARY_CALLS, is_package_argument
from .regions import (
    IMPRINT_NAMES,
    PLACEHOLDER,
    PLACEHOLDER_FUNC,
    SAVE_DEVICE,
    SAVE_KEYWORDS,
    SAVE_NAME,
    SAVE_NAMES,
    THEME_NAME,
    Regions,
    find_regions,
    is_placeholder,
)


MAX_SNIPPET_CHARS = 60
MAX_CODE_STRING_DEPTH = 2
"""Code strings inside code strings are walked this deep; deeper is a finding."""

LIBRARY_ALLOWLIST = frozenset(
    {
        "ggplot2",
        "ragg",
        "dplyr",
        "tidyr",
        "tibble",
        "scales",
        "patchwork",
        "viridis",
        "grid",
        "gridExtra",
        "stats",
        "grDevices",
        "graphics",
        "MASS",
        "cluster",
        "survival",
        "class",
        "splines",
    }
)
"""The packages `library()` may attach: the renderer image's set (`.github/actions/setup-r`) without readr, which
only the loader uses, and with R's base packages that plot code reads (stats, grDevices, graphics, grid, splines)."""
NAMESPACE_FUNCTIONS: dict[str, frozenset[str]] = {
    "utils": frozenset({"head"}),
    "tools": frozenset({"toTitleCase"}),
    "gridExtra": frozenset({"arrangeGrob"}),
    "ragg": frozenset({"agg_png"}),
}
"""`pkg::name` of these packages takes only these names; every other package of `NAMESPACES` takes any name that
the denied-name rule passes. `ragg::agg_png` only as the protected save's device."""
NAMESPACES = LIBRARY_ALLOWLIST | frozenset(NAMESPACE_FUNCTIONS)
LOGGED_PACKAGES = NAMESPACES | frozenset(
    {
        "base",
        "methods",
        "readr",
        "purrr",
        "stringr",
        "lubridate",
        "forcats",
        "glue",
        "rlang",
        "data.table",
        "jsonlite",
        "httr",
        "curl",
        "sf",
        "maps",
        "mapdata",
        "rnaturalearth",
        "ggrepel",
        "ggforce",
        "cowplot",
        "ggridges",
        "qrcode",
        "gapminder",
        "palmerpenguins",
        "processx",
        "callr",
    }
)
"""The closed vocabulary a `banned-import` finding's `module` label comes from (`?` for any other package), so the
attribution log never records a name the model made up."""
UNKNOWN_PACKAGE = "?"

DENIED_NAMES = frozenset(
    {
        # processes and the shell
        "system",
        "system2",
        "shell",
        "shell.exec",
        "pipe",
        "Rscript",
        # connections, files and the network
        "file",
        "url",
        "gzfile",
        "bzfile",
        "xzfile",
        "unz",
        "fifo",
        "gzcon",
        "textConnection",
        "rawConnection",
        "download.file",
        "browseURL",
        "nsl",
        "make.socket",
        "readLines",
        "readRDS",
        "readline",
        "readBin",
        "readChar",
        "readRenviron",
        "load",
        "scan",
        "dget",
        "dump",
        "saveRDS",
        "save",
        "save.image",
        "sink",
        "unlink",
        "dir.create",
        "list.files",
        "list.dirs",
        "tempfile",
        "unzip",
        "untar",
        "Rprof",
        "Rprofmem",
        # sourcing, parsing and evaluation
        "source",
        "parse",
        "str2lang",
        "str2expression",
        # reaching a function or a variable from a string or an environment
        "get",
        "get0",
        "mget",
        "exists",
        "assign",
        "dynGet",
        "match.fun",
        "getAnywhere",
        "getS3method",
        "getFunction",
        "getExportedValue",
        "getNamespace",
        "asNamespace",
        "loadNamespace",
        "requireNamespace",
        "attachNamespace",
        "getFromNamespace",
        "assignInNamespace",
        "fixInNamespace",
        "environment",
        "as.environment",
        "list2env",
        "baseenv",
        "globalenv",
        "emptyenv",
        "topenv",
        "parent.env",
        "parent.frame",
        "new.env",
        "pos.to.env",
        "attach",
        ".env",
        ".GlobalEnv",
        ".BaseNamespaceEnv",
        "::",
        ":::",
        # internals and native code
        ".Internal",
        ".Primitive",
        ".Call",
        ".External",
        ".External2",
        ".C",
        ".Fortran",
        ".Call.graphics",
        ".External.graphics",
        "dyn.load",
        "dyn.unload",
        "library.dynam",
        "getNativeSymbolInfo",
        ".libPaths",
        "install.packages",
        "remove.packages",
        "update.packages",
        # bindings, function internals, debugging, options
        "makeActiveBinding",
        "lockBinding",
        "unlockBinding",
        "lockEnvironment",
        "delayedAssign",
        "body",
        "formals",
        "trace",
        "options",
        # strings that become code: aesthetics, glue, formulas
        "aes_string",
        "aes_",
        "aes_q",
        "glue",
        "str_glue",
        "label_glue",
        "as.formula",
        "reformulate",
        # graphics devices: every plot leaves through the protected save
        "png",
        "svg",
        "jpeg",
        "bmp",
        "tiff",
        "pdf",
        "postscript",
        "cairo_pdf",
        "cairo_ps",
        "xfig",
        "pictex",
        "bitmap",
        "quartz",
        "x11",
        "X11",
        "savePlot",
        "agg_png",
        "agg_jpeg",
        "agg_tiff",
        "agg_ppm",
        "agg_supertransparent",
        "agg_capture",
        "agg_record",
        "agg_webp",
        "agg_webp_anim",
        "grid.arrange",
        "marrangeGrob",
    }
)
"""Names R code may not use (module docstring, "Denied names")."""
DENIED_PATTERN = re.compile(r"^(?:socket|eval(?:$|[._q])|read[.A-Z]|write(?:$|[._A-Z])|file\.|dev\.|sys\.|Sys\.)")
"""The denied families: `socket*`, `eval`, `evalq`, `eval.parent`, `eval_tidy`, `read.*` (and `readLines`-style
names), `write`, `write.*`, `writeLines`, `file.*`, `dev.*`, `sys.*` and `Sys.*`. `writer` or `evaluation` stay names."""
ALLOWED_SYS = frozenset({"Sys.time", "Sys.Date"})
SYS_GETENV = "Sys.getenv"

DO_CALL = "do.call"
DO_CALL_FUNCTIONS = frozenset({"rbind", "cbind", "c", "paste", "paste0"})
"""What `do.call` may call: one of these by name, or `"rbind"`, `"cbind"` or `"c"` as a string (`DO_CALL_STRINGS`)."""
DO_CALL_STRINGS = frozenset({"rbind", "cbind", "c"})
FUNCTION_ARGUMENTS = frozenset(
    {"FUN", "fun", ".f", ".fn", ".fns", ".funs", "f", "fn", "method", "labeller", "transform", "inverse"}
)
"""Arguments that take a function (and a string `match.fun` resolves); `fun.*` too, except `fun.args`."""
FUNCTION_POSITIONS: dict[str, tuple[int, ...]] = {
    "lapply": (1,),
    "sapply": (1,),
    "vapply": (1,),
    "rapply": (1,),
    "mapply": (0,),
    "Map": (0,),
    "Reduce": (0,),
    "Filter": (0,),
    "Find": (0,),
    "Position": (0,),
    "Negate": (0,),
    "Vectorize": (0,),
    "apply": (2,),
    "tapply": (2,),
    "outer": (2,),
    "kronecker": (2,),
    "sweep": (3,),
    "aggregate": (2,),
    "by": (2,),
    "integrate": (0,),
    "optimize": (0,),
    "optimise": (0,),
    "uniroot": (0,),
    "optim": (1,),
    "across": (1,),
    "if_any": (1,),
    "if_all": (1,),
    "rename_with": (1,),
    "group_map": (1,),
    "group_modify": (1,),
    "trans_new": (1, 2),
    "new_transform": (1, 2),
    ".mapply": (0,),
    "forceAndCall": (1,),
    "nlm": (0,),
    "nlminb": (1,),
    # purrr's map family: not attachable here (purrr is off the allowlist), but a function slot wherever it appears
    **dict.fromkeys(("map", "map_dbl", "map_chr", "map_int", "map_lgl", "map_dfr", "map_dfc", "map_vec"), (1,)),
    **dict.fromkeys(("imap", "pmap", "walk", "keep", "discard", "detect", "reduce", "accumulate", "modify"), (1,)),
    **dict.fromkeys(("map2", "map2_dbl", "map2_chr", "map2_int", "map2_lgl", "walk2"), (2,)),
}
"""The positional slots (counting positional arguments only) that take a function."""
FUNCTION_FACTORIES = frozenset({"list", "c", "Negate", "Vectorize"})
"""Calls whose arguments are function values, checked one by one."""
LABELLERS = frozenset(
    {"labeller", "as_labeller", "label_wrap_gen", "label_both", "label_value", "label_parsed", "label_context"}
)
"""ggplot2's labeller builders: a labeller value may be one of these calls (2 catalogue files)."""
TRANSFORM_ARGUMENTS = frozenset({"transform", "inverse"})
TRANSFORM_BUILDERS = re.compile(r"^(?:transform_\w+|\w+_trans|trans_new|new_transform)$")
"""scales' transformation objects, which `transform =` and `inverse =` also take (`scale_y_continuous(transform =
scales::transform_log())`); `trans_new` and `new_transform` have their own function slots (`FUNCTION_POSITIONS`)."""
CALLABLE_FACTORIES = re.compile(
    r"^(?:colorRampPalette|colorRamp|label_\w+|\w+_format|\w+_pal|breaks_\w+|pretty_breaks|extended_breaks"
    r"|col_numeric|col_factor|col_bin|col_quantile|rescale_\w+|ecdf|approxfun|splinefun|Vectorize|Negate)$"
)
"""Builders whose result a call may call at once: palettes, scales' labels and breaks, `ecdf` and the
interpolators (`colorRampPalette(...)(n)`, `scales::label_percent()(x)`, `hue_pal()(n)`; the catalogue uses
`colorRampPalette` 8 times and `label_comma` and `label_number` 4). Any other call as a callee is refused, because
`identity(fn)("id")` or `dplyr::first(fns)("id")` would call whatever function a value holds."""
INERT_CALLS = frozenset({"expression", "quote"})
"""Calls whose arguments R never evaluates: plotmath such as `expression(-log[10](p))` may index a callee there."""
FACET_CALLS: dict[str, tuple[tuple[int, ...], frozenset[str]]] = {
    "facet_wrap": ((0,), frozenset({"facets"})),
    "facet_grid": ((0, 1), frozenset({"rows", "cols", "facets"})),
}
"""Where ggplot2 reads a facet, which `parse_expr` turns into code when it is a string."""
DATA_MASK_CALLS = frozenset(
    {
        # ggplot2: aesthetics, facets and their helpers
        "aes",
        "vars",
        "facet_wrap",
        "facet_grid",
        "after_stat",
        "after_scale",
        "stage",
        # dplyr verbs, tidy selection and the helpers that evaluate inside them
        "mutate",
        "transmute",
        "summarise",
        "summarize",
        "reframe",
        "filter",
        "arrange",
        "select",
        "rename",
        "relocate",
        "group_by",
        "count",
        "add_count",
        "tally",
        "distinct",
        "pull",
        "slice_min",
        "slice_max",
        "across",
        "if_any",
        "if_all",
        "c_across",
        "pick",
        "case_when",
        "case_match",
        "join_by",
        # tidyr verbs
        "pivot_longer",
        "pivot_wider",
        "separate",
        "separate_wider_delim",
        "unite",
        "nest",
        "unnest",
        "complete",
        "expand",
        "fill",
        "drop_na",
        "uncount",
        "extract",
        "gather",
        "spread",
        # base R's data-masking verbs (the counterparts of filter and mutate)
        "subset",
        "transform",
    }
)
"""Calls whose arguments R evaluates in a data mask, where a bare name is a column: a denied name there is data
(a flow's `source` column), except as a callee or a function-valued argument. The operands of `~` are a mask too
(formulas, a tribble's `~source` header, lambdas). Fixed in code, owner decision of 2026-10-29. The general
evaluators `with`, `within` and `local`, whose argument is any expression rather than a column, are no mask
(review of 2026-10-29)."""
FORMULA_FIRST = frozenset(
    {
        "lm",
        "glm",
        "loess",
        "nls",
        "aov",
        "model.frame",
        "model.matrix",
        "xtabs",
        "formula",
        "survfit",
        "coxph",
        "survreg",
        "rlm",
        "lda",
        "qda",
        "glm.nb",
        "polr",
        "ppr",
        "lqs",
        "loglm",
    }
)
"""Modelling functions whose first positional argument is always a formula (stats, MASS, survival)."""
FORMULA_OR_DATA_FIRST = frozenset(
    {
        "aggregate",
        "t.test",
        "wilcox.test",
        "kruskal.test",
        "cor.test",
        "var.test",
        "bartlett.test",
        "fligner.test",
        "ansari.test",
        "mood.test",
        "friedman.test",
        "boxplot",
        "prcomp",
        "princomp",
        "ftable",
    }
)
"""Functions with a formula method and a data method: their first positional is checked only for a computed string."""
STRING_BUILDERS = frozenset(
    {
        "paste",
        "paste0",
        "sprintf",
        "gettextf",
        "format",
        "formatC",
        "prettyNum",
        "toString",
        "as.character",
        "deparse",
        "sub",
        "gsub",
        "trimws",
        "tolower",
        "toupper",
        "str_c",
        "str_glue",
        "glue",
    }
)
"""Calls that build a string at run time: never a formula, which R would parse and evaluate in the data."""
GLUE_KEYWORDS = frozenset({".names", "names_glue"})
GLUE_FIELDS = frozenset({".col", ".fn"})
BANNED_KEYWORDS = frozenset({"file"})
PROTECTED_NAMES = frozenset({SAVE_NAME, "sprintf", SYS_GETENV})
"""Names the save statement and the theme statement call: never bound by the code."""

RNG_DRAWS = re.compile(
    r"^(?:r(?:norm|pois|binom|exp|gamma|beta|t|chisq|f|lnorm|weibull|cauchy|geom|hyper|nbinom|logis|multinom"
    r"|signrank|wilcox|mvnorm)|mvrnorm)$"
)
"""Random draws that fabricate data; `runif`, `sample`, `set.seed` and `jitter` stay allowed (owner, 2026-10-29)."""
DATASETS = frozenset(
    {
        "iris",
        "mtcars",
        "airquality",
        "faithful",
        "faithfuld",
        "diamonds",
        "mpg",
        "economics",
        "economics_long",
        "txhousing",
        "midwest",
        "msleep",
        "presidential",
        "seals",
        "luv_colours",
        "ToothGrowth",
        "ChickWeight",
        "CO2",
        "PlantGrowth",
        "InsectSprays",
        "USArrests",
        "VADeaths",
        "WorldPhones",
        "AirPassengers",
        "EuStockMarkets",
        "JohnsonJohnson",
        "LifeCycleSavings",
        "Titanic",
        "UCBAdmissions",
        "HairEyeColor",
        "quakes",
        "airmiles",
        "nhtemp",
        "Nile",
        "LakeHuron",
        "lynx",
        "sunspots",
        "sunspot.month",
        "sunspot.year",
        "co2",
        "nottem",
        "ldeaths",
        "mdeaths",
        "fdeaths",
        "UKgas",
        "UKDriverDeaths",
        "USAccDeaths",
        "warpbreaks",
        "esoph",
        "infert",
        "longley",
        "morley",
        "chickwts",
        "state.x77",
        "state.name",
        "state.abb",
        "state.region",
        "state.area",
        "state.center",
        "state.division",
        "stackloss",
        "swiss",
        "volcano",
        "uspop",
        "WWWusage",
        "precip",
        "eurodist",
        "Puromycin",
        "Theoph",
        "Indometh",
        "Loblolly",
        "DNase",
        "BOD",
        "Formaldehyde",
        "OrchardSprays",
        "randu",
        "crimtab",
        "freeny",
        "treering",
        "austres",
        "BJsales",
        "Boston",
        "Cars93",
        "Animals",
        "geyser",
        "gapminder",
        "penguins",
        "penguins_raw",
    }
)
"""Built-in datasets of base R, ggplot2, MASS and the dataset packages read by name; ambiguous words (`cars`, `women`,
`pressure`, `trees`, `rock`, `sleep`) are left out, because a user's column may carry them."""

_URL_IN_TEXT = re.compile(r"(?i)(?:https?|ftp)://|\b(?:file|data):\S")
"""The Python profile's URL rule (`validate._URL_IN_TEXT`)."""
_GLUE_FIELD = re.compile(r"\{([^{}]*)\}")
_HEX = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")
_WHITESPACE = re.compile(r"\s+")


def denied(name: str) -> bool:
    """Whether R code may not use `name` (module docstring, "Denied names")."""
    if name in DENIED_NAMES:
        return True
    if name in ALLOWED_SYS:
        return False
    return DENIED_PATTERN.match(name) is not None


def validate_security(code: str) -> list[Finding]:
    """The SECURITY profile (module docstring); never raises."""
    source, findings = _parse(code)
    if source is None:
        return findings
    scan = _Scan(source)
    scan.security()
    return scan.result()


def validate_adaptation(code: str, *, original_palette: list[str]) -> list[Finding]:
    """The ADAPTATION profile: one placeholder, no fabricated data, the palette prefix kept."""
    source, findings = _parse(code)
    if source is None:
        return findings
    scan = _Scan(source)
    scan.adaptation(original_palette)
    return scan.result()


def _parse(code: str) -> tuple[Source | None, list[Finding]]:
    """Size, encoding and syntax: the checks that run before any rule can."""
    if len(code) > MAX_CODE_CHARS:
        return None, [Finding("size", f"code is {len(code):,} characters; the limit is {MAX_CODE_CHARS:,}", None)]
    try:
        code.encode("utf-8")
    except UnicodeEncodeError:
        return None, [Finding("encoding", "code is not valid UTF-8 text", None)]
    source = Source(code, "r")
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        return None, [Finding("syntax", f"syntax error: {problems[0].message()}", problems[0].line)]
    for visit in visits(source.root):
        node = visit.node
        if (node.type == "string" and r_string_value(source, node) is None) or (
            node.type == "identifier" and r_identifier(source, node) is None
        ):
            message = "syntax error: a string or backtick name R cannot read (an unknown escape or a nul character)"
            return None, [Finding("syntax", message, first_line(node))]
    return source, []


def _snippet(source: Source, node: Node) -> str:
    """At most `MAX_SNIPPET_CHARS` of a node's code on one line, its string literals shown as `"..."`."""
    data = source.data
    parts: list[str] = []
    cursor = node.start_byte
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "string":
            parts.append(data[cursor : current.start_byte].decode("utf-8", "replace") + '"..."')
            cursor = current.end_byte
            continue
        stack.extend(reversed(current.children))
    parts.append(data[cursor : node.end_byte].decode("utf-8", "replace"))
    text = _WHITESPACE.sub(" ", "".join(parts)).strip()
    return text if len(text) <= MAX_SNIPPET_CHARS else text[: MAX_SNIPPET_CHARS - 3] + "..."


@dataclass(frozen=True, slots=True)
class _Binding:
    """One place the file binds a name, and whether it binds a function literal there."""

    node: Node
    function: bool
    top_level: bool
    value: Node | None


class _Scan:
    """One validation pass over a parsed R source.

    A code string's scan (`depth` > 0) places its findings on the string's `line`, and
    with `masked` reads the whole string as a data mask, because ggplot2 evaluates a
    facet string and R a formula's variables in the data.
    """

    def __init__(self, source: Source, *, depth: int = 0, line: int | None = None, masked: bool = False) -> None:
        self.source = source
        self.depth = depth
        self.fixed_line = line
        self.findings: list[Finding] = []
        self.visits = list(visits(source.root))
        self.regions: Regions = find_regions(source)
        self.masks: list[tuple[int, int]] = [(source.root.start_byte, source.root.end_byte)] if masked else []
        self.inert: list[tuple[int, int]] = []
        self.parameters: list[tuple[int, int, frozenset[str]]] = []
        """Each function literal's byte range and the names of its parameters."""
        for visit in self.visits:
            node = visit.node
            if node.type == "call":
                base = (r_callee(source, node) or "").rsplit("::", 1)[-1]
                arguments = node.child_by_field_name("arguments")
                if arguments is not None and base in DATA_MASK_CALLS:
                    self.masks.append((arguments.start_byte, arguments.end_byte))
                elif arguments is not None and base in INERT_CALLS:
                    self.inert.append((arguments.start_byte, arguments.end_byte))
            elif node.type in ("unary_operator", "binary_operator") and r_operator(source, node) == "~":
                self.masks.append((node.start_byte, node.end_byte))
            elif node.type == "function_definition":
                parameters = node.child_by_field_name("parameters")
                names = frozenset(
                    name
                    for parameter in (parameters.named_children if parameters is not None else [])
                    if parameter.type == "parameter"
                    for name in [r_identifier(source, parameter.child_by_field_name("name") or parameter)]
                    if name is not None
                )
                if names:
                    self.parameters.append((node.start_byte, node.end_byte, names))
        self.bindings: dict[str, list[_Binding]] = {}
        for name, node in r_bindings(source, source.root):
            value = node.child_by_field_name("rhs") if node.type == "binary_operator" else None
            assignment = r_assignment(source, node) if node.type == "binary_operator" else None
            bound_value = assignment.value if assignment is not None else value
            self.bindings.setdefault(name, []).append(
                _Binding(
                    node=node,
                    function=bound_value is not None and r_unwrap(bound_value).type == "function_definition",
                    top_level=node.parent is not None and node.parent.type == "program",
                    value=bound_value if assignment is not None and assignment.target.type == "identifier" else None,
                )
            )
        theme = self.regions.theme
        self.theme_chars = (theme.statement.start, theme.statement.end) if theme and theme.statement else None

    # -- bookkeeping ---------------------------------------------------------------------

    def add(self, rule: str, message: str, node: Node | None, *, module: str | None = None) -> None:
        line = self.fixed_line if self.fixed_line is not None else (first_line(node) if node is not None else None)
        if self.depth:
            message = f"in a code string: {message}"
        self.findings.append(Finding(rule, message[:MAX_MESSAGE_CHARS], line, module))

    def result(self) -> list[Finding]:
        unique = dict.fromkeys(self.findings)
        return sorted(unique, key=lambda f: (f.line is None, f.line or 0, f.rule, f.message))

    def in_theme_statement(self, node: Node) -> bool:
        if self.theme_chars is None:
            return False
        return self.theme_chars[0] <= self.source.char(node.start_byte) < self.theme_chars[1]

    def starts_at(self, node: Node, span: Span | None) -> bool:
        """Whether `node` is the statement `span` holds: the same first character (identity, not the same line)."""
        return span is not None and self.source.char(node.start_byte) == span.start

    def in_inert(self, node: Node) -> bool:
        """Whether `node` lies in the arguments of a call R never evaluates (`INERT_CALLS`: plotmath)."""
        return any(start <= node.start_byte < end for start, end in self.inert)

    def is_parameter(self, node: Node, name: str) -> bool:
        """Whether `name` is a parameter of a function literal that encloses `node`."""
        return any(start <= node.start_byte < end and name in names for start, end, names in self.parameters)

    def in_mask(self, node: Node) -> bool:
        """Whether `node` lies in the arguments of a data-masking call (`DATA_MASK_CALLS`) or in a `~` operand."""
        return any(start <= node.start_byte < end for start, end in self.masks)

    def snippet(self, node: Node) -> str:
        return _snippet(self.source, node)

    def string_constant(self, name: str) -> tuple[str, ...] | None:
        """The strings a column constant holds: a top-level name bound exactly once to a string or `c()` of strings."""
        bound = self.bindings.get(name, [])
        if len(bound) != 1 or not bound[0].top_level or bound[0].value is None:
            return None
        value = r_unwrap(bound[0].value)
        single = r_string_value(self.source, value)
        if single is not None:
            return (single,)
        if value.type != "call" or r_callee(self.source, value) != "c":
            return None
        texts = [
            r_string_value(self.source, r_unwrap(argument.value)) if argument.value is not None else None
            for argument in r_arguments(self.source, value)
        ]
        if not texts or any(text is None for text in texts):
            return None
        return tuple(text for text in texts if text is not None)

    # -- SECURITY ------------------------------------------------------------------------

    def security(self) -> None:
        for visit in self.visits:
            node = visit.node
            if node.type == "identifier":
                self.check_identifier(visit)
            elif node.type == "string":
                self.check_string(visit)
            elif node.type == "namespace_operator":
                self.check_namespace(visit)
            elif node.type == "call":
                self.check_call(node)
            elif node.type == "binary_operator":
                self.check_binary(node)
            elif node.type == "unary_operator":
                self.check_injection(visit)
        if self.depth == 0:
            self.check_save()
            self.check_bindings()

    def check_identifier(self, visit: Visit) -> None:
        node, parent, field = visit.node, visit.parent, visit.field
        if parent is None or parent.type == "namespace_operator":
            return  # `pkg::name` has its own rule
        if parent.type == "argument" and field == "name":
            return  # an argument's name is no lookup
        if parent.type == "extract_operator" and field == "rhs":
            return  # the field after `$` or `@`
        name = r_identifier(self.source, node)
        if name is None:
            self.add("syntax", "a backtick name R cannot read", node)
            return
        callee = parent.type == "call" and field == "function"
        if name == SAVE_NAME and not callee and r_is_lookup(visit):
            self.add("savefig-target", "ggsave is only ever called where it is named, as the final save", node)
        if name == DO_CALL and not callee and r_is_lookup(visit):
            # `lapply(fns, do.call, args)` would call any function a value holds, past the do.call rule
            self.add("banned-call", "do.call is only ever called where it is named", node)
        if not denied(name):
            return
        if name == SYS_GETENV and self.in_theme_statement(node):
            return
        if name == "pdf" and self.is_null_device(visit):
            return
        if not callee and self.in_mask(node):
            return  # a column of the data: `aes(y = source)`, `group_by(source)`, `~source` (function slots: below)
        self.add("banned-name", f"'{name}' is not allowed: {self.reason(name)}", node)

    def is_null_device(self, callee: Visit) -> bool:
        """Whether `callee` (`pdf` or `grDevices::pdf`) is called as `pdf(NULL)` or `pdf(file = NULL)`: the null
        device two catalogue files open to measure grobs."""
        call = callee.parent
        if call is None or call.type != "call" or callee.field != "function":
            return False
        arguments = r_arguments(self.source, call)
        return (
            len(arguments) == 1
            and arguments[0].name in (None, "file")
            and arguments[0].value is not None
            and r_unwrap(arguments[0].value).type == "null"
        )

    def reason(self, name: str) -> str:
        if name == SYS_GETENV:
            return 'the environment is read only by THEME <- Sys.getenv("ANYPLOT_THEME", "light")'
        if name in ("pdf", "png", "svg", "jpeg") or name.startswith(("agg_", "dev.")):
            return "the plot is written only by the final ggsave"
        return "the plot reads only df and writes only through the final ggsave, without files, processes or eval"

    def check_string(self, visit: Visit) -> None:
        node = visit.node
        value = r_string_value(self.source, node)
        if value is None:
            self.add("syntax", "a string R cannot read (an unknown escape or a nul character)", node)
            return
        if self.in_theme_statement(node):
            return
        if len(value) > MAX_STRING_CHARS:
            self.add(
                "string-length", f"string literal of {len(value)} characters; the limit is {MAX_STRING_CHARS}", node
            )
        if _URL_IN_TEXT.search(value):
            self.add("url-literal", "URL or file literal; the plot reads only df", node)
        if "~" in value:
            self.walk_code_string(value, node)

    def walk_code_string(self, value: str, node: Node) -> None:
        """Parse a string R would read as code and walk it with these rules, as a data mask (a facet's or formula's
        names are columns); text that does not parse stays text."""
        if len(value) > MAX_CODE_CHARS:
            return
        inner = Source(value, "r")
        if syntax_problems(inner.tree, limit=1):
            return
        if self.depth >= MAX_CODE_STRING_DEPTH:
            self.add("banned-call", "code strings nested this deep are not allowed", node)
            return
        nested = _Scan(inner, depth=self.depth + 1, line=self.fixed_line or first_line(node), masked=True)
        nested.security()
        self.findings.extend(nested.findings)

    def check_namespace(self, visit: Visit) -> None:
        node = visit.node
        operator = node.child_by_field_name("operator")
        lhs, rhs = node.child_by_field_name("lhs"), node.child_by_field_name("rhs")
        if operator is None or lhs is None or rhs is None:
            return
        package = r_identifier(self.source, lhs) or r_string_value(self.source, lhs) or ""
        name = r_identifier(self.source, rhs) or r_string_value(self.source, rhs) or ""
        label = package if package in LOGGED_PACKAGES else UNKNOWN_PACKAGE
        if self.source.text(operator) == ":::":
            self.add(
                "banned-import", "':::' reaches a package's internals; use its exported functions", node, module=label
            )
            return
        if package not in NAMESPACES and package not in DATASET_PACKAGES:
            allowed = ", ".join(sorted(LIBRARY_ALLOWLIST))
            self.add("banned-import", f"package '{package}' is not available → use {allowed}", node, module=label)
            return
        allowed_names = NAMESPACE_FUNCTIONS.get(package)
        if allowed_names is not None and name not in allowed_names:
            shown = ", ".join(f"{package}::{allowed}" for allowed in sorted(allowed_names))
            self.add("banned-import", f"'{package}::{name}' is not allowed; only {shown}", node, module=label)
            return
        if package == "ragg":
            if not self.is_protected_device(node):
                self.add("savefig-target", f"{SAVE_DEVICE} is only the device of the final ggsave", node)
            return
        callee = visit.parent is not None and visit.parent.type == "call" and visit.field == "function"
        if name == SAVE_NAME and not callee:
            self.add("savefig-target", "ggsave is only ever called where it is named, as the final save", node)
        if denied(name) and not (name == "pdf" and self.is_null_device(visit)):
            self.add("banned-name", f"'{package}::{name}' is not allowed: {self.reason(name)}", node)

    def is_protected_device(self, node: Node) -> bool:
        save = self.regions.save
        if save is None or self.depth:
            return False
        device = save.argument("device")
        return (
            device is not None
            and device.value_span is not None
            and device.value_span.start == self.source.char(node.start_byte)
        )

    def check_call(self, node: Node) -> None:
        function = node.child_by_field_name("function")
        if function is None:
            return
        unwrapped = r_unwrap(function)
        if unwrapped.type == "string":
            self.add("banned-call", "a string as the function of a call; name the function", node)
        elif unwrapped.type == "function_definition":
            self.add("banned-call", "a function literal called where it is written; name it, then call it", node)
        elif function.type == "parenthesized_expression":
            self.add("banned-call", f"a computed function '{self.snippet(function)}'; name the function", node)
        elif unwrapped.type in ("subset", "subset2", "extract_operator") and not self.in_inert(node):
            self.add(
                "banned-call", f"a function taken out of a value '{self.snippet(function)}'; call it by name", node
            )
        elif unwrapped.type == "call" and not self.in_inert(node):
            factory = (r_callee(self.source, unwrapped) or "").rsplit("::", 1)[-1]
            if CALLABLE_FACTORIES.fullmatch(factory) is None:
                message = f"the result of '{self.snippet(unwrapped)}' called at once; call a named function"
                self.add("banned-call", message, node)
        elif unwrapped.type == "identifier":
            called = r_identifier(self.source, unwrapped) or ""
            if self.is_parameter(node, called):
                message = f"'{called}' is a parameter: a function never calls the function it is handed"
                self.add("banned-call", message, node)
        callee = r_callee(self.source, node)
        base = callee.rsplit("::", 1)[-1] if callee is not None else None
        arguments = r_arguments(self.source, node)
        if callee in LIBRARY_CALLS:
            self.check_library(node, callee, arguments)
        elif base == DO_CALL:
            self.check_do_call(node, arguments)
        elif callee in SAVE_NAMES and not self.is_protected_save(node):
            self.add("savefig-target", "the plot is saved only by the final ggsave", node)
        for argument in arguments:
            name = argument.name
            if name is None or argument.value is None:
                continue
            if name in BANNED_KEYWORDS and not (base == "pdf" and r_unwrap(argument.value).type == "null"):
                self.add(
                    "banned-keyword", f"the keyword '{name} =' writes a file; the plot writes only through ggsave", node
                )
            if name in FUNCTION_ARGUMENTS or (name.startswith("fun.") and name != "fun.args"):
                builders = (
                    LABELLERS if name == "labeller" else TRANSFORM_BUILDERS if name in TRANSFORM_ARGUMENTS else None
                )
                self.check_function_value(argument.value, f"{name} =", builders=builders or frozenset())
            if name in GLUE_KEYWORDS:
                self.check_glue(argument.value, name)
            if name == "formula":
                self.check_formula(argument.value, strict=True)
        if base in FORMULA_FIRST or base in FORMULA_OR_DATA_FIRST:
            first = r_argument(arguments, "\0", 0)
            if first is not None and first.value is not None and not any(arg.name == "formula" for arg in arguments):
                self.check_formula(first.value, strict=base in FORMULA_FIRST)
        if base in FUNCTION_POSITIONS:
            for position in FUNCTION_POSITIONS[base]:
                slot = r_argument(arguments, "\0", position)
                if slot is not None and slot.value is not None:
                    self.check_function_value(slot.value, f"the function argument of {base}()")
        if base in FACET_CALLS:
            positions, keywords = FACET_CALLS[base]
            slots = [argument for argument in arguments if argument.name in keywords]
            slots += [
                argument for argument in (r_argument(arguments, "\0", position) for position in positions) if argument
            ]
            for argument in slots:
                if argument.value is not None:
                    self.check_facet(argument.value, base)

    def check_library(self, node: Node, callee: str, arguments: list[Argument]) -> None:
        package = None
        if len(arguments) == 1 and arguments[0].name in (None, "package") and arguments[0].value is not None:
            value = r_unwrap(arguments[0].value)
            package = r_identifier(self.source, value) or r_string_value(self.source, value)
        if package is None:
            self.add("banned-import", f"{callee}() takes one package name and nothing else", node)
            return
        if package not in LIBRARY_ALLOWLIST and package not in DATASET_PACKAGES:
            label = package if package in LOGGED_PACKAGES else UNKNOWN_PACKAGE
            allowed = ", ".join(sorted(LIBRARY_ALLOWLIST))
            self.add("banned-import", f"package '{package}' is not available → use {allowed}", node, module=label)

    def check_do_call(self, node: Node, arguments: list[Argument]) -> None:
        what = r_argument(arguments, "what", 0)
        value = r_unwrap(what.value) if what is not None and what.value is not None else None
        name = r_identifier(self.source, value) if value is not None else None
        text = r_string_value(self.source, value) if value is not None else None
        if name not in DO_CALL_FUNCTIONS and text not in DO_CALL_STRINGS:
            self.add(
                "banned-call", 'do.call() takes only rbind, cbind, c, paste or paste0 (or "rbind", "cbind", "c")', node
            )

    def is_protected_save(self, node: Node) -> bool:
        save = self.regions.save
        return save is not None and self.depth == 0 and save.span.start == self.source.char(node.start_byte)

    def check_function_value(
        self, value: Node, where: str, *, builders: frozenset[str] | re.Pattern[str] = frozenset()
    ) -> None:
        """A function-valued argument: a function literal, a lambda, a literal, `pkg::name`, a name bound only to
        function literals, a factory over such values, or a call of one of `builders` (the argument's own object
        builders: ggplot2's labellers for `labeller =`, scales' transformations for `transform =`); never a computed
        value `match.fun` would resolve."""
        stack = [value]
        while stack:
            node = r_unwrap(stack.pop())
            kind = node.type
            if kind == "string":
                # A string here is a function's name for `match.fun`: one equal to a denied name is that function.
                text = r_string_value(self.source, node) or ""
                if denied(text):
                    self.add("banned-name", f"{where} names the denied function '{text}'", node)
                continue
            if kind in ("function_definition", "namespace_operator") or kind in R_LITERALS:
                continue
            if kind == "unary_operator" and (
                r_operator(self.source, node) == "~" or r_number(self.source, node) is not None
            ):
                continue  # a `~` lambda, or a negative number
            if kind == "identifier":
                name = r_identifier(self.source, node) or ""
                if denied(name):
                    self.add("banned-name", f"'{name}' is not allowed: {self.reason(name)}", node)
                    continue
                bound = self.bindings.get(name, [])
                if all(binding.function for binding in bound):
                    continue
                self.add(
                    "banned-call",
                    f"{where} takes a function; '{name}' is bound to something else here, so write the function",
                    node,
                )
                continue
            if kind == "call":
                callee = r_callee(self.source, node) or ""
                base = callee.rsplit("::", 1)[-1]
                if base in FUNCTION_FACTORIES:
                    stack.extend(argument.value for argument in r_arguments(self.source, node) if argument.value)
                    continue
                built = builders.fullmatch(base) is not None if isinstance(builders, re.Pattern) else base in builders
                if built:
                    continue
            self.add(
                "banned-call",
                f"{where} takes a function, a lambda or a function's name, not a computed value '{self.snippet(node)}'",
                node,
            )

    def check_glue(self, value: Node, keyword: str) -> None:
        """glue evaluates every `{...}` as code: only `{.col}` and `{.fn}`, and no other brace."""
        text = r_string_value(self.source, r_unwrap(value))
        fields_ok = text is not None and all(field in GLUE_FIELDS for field in _GLUE_FIELD.findall(text))
        rest = _GLUE_FIELD.sub("", text) if text is not None else ""
        if not fields_ok or "{" in rest or "}" in rest:
            self.add("banned-keyword", f"{keyword} takes a string whose braces are only {{.col}} and {{.fn}}", value)

    def check_formula(self, value: Node, *, strict: bool) -> None:
        """A formula position: a `~` literal, a string literal (parsed and walked) or a name bound once to one of them.

        R parses a string formula and evaluates its variables in the data, so a string built
        at run time (`STRING_BUILDERS`, or a name bound to one) is refused everywhere. With
        `strict` (`formula =`, `FORMULA_FIRST`) nothing else is a formula either; without it
        (`FORMULA_OR_DATA_FIRST`, whose data method takes a table) any other value passes.
        """
        node = r_unwrap(value)
        if self.is_formula_literal(node):
            if node.type == "string":
                self.walk_code_string(r_string_value(self.source, node) or "", node)
            return
        if node.type == "identifier":
            bound = self.bindings.get(r_identifier(self.source, node) or "", [])
            bound_value = r_unwrap(bound[0].value) if len(bound) == 1 and bound[0].value is not None else None
            if bound_value is not None and self.is_formula_literal(bound_value):
                if bound_value.type == "string":
                    self.walk_code_string(r_string_value(self.source, bound_value) or "", node)
                return
            built = any(binding.value is not None and self.builds_string(binding.value) for binding in bound)
            if not strict and not built:
                return
        elif not strict and not self.builds_string(node):
            return
        self.add(
            "banned-call",
            f"a formula is y ~ x, a string or a name bound once to one, never a computed value '{self.snippet(node)}'",
            value,
        )

    def is_formula_literal(self, node: Node) -> bool:
        if node.type == "string":
            return True
        return node.type in ("unary_operator", "binary_operator") and r_operator(self.source, node) == "~"

    def builds_string(self, value: Node) -> bool:
        """A call of `STRING_BUILDERS` (`paste0(...)`, `sprintf(...)`)."""
        node = r_unwrap(value)
        return node.type == "call" and (r_callee(self.source, node) or "").rsplit("::", 1)[-1] in STRING_BUILDERS

    def check_facet(self, value: Node, call: str) -> None:
        node = r_unwrap(value)
        kind = node.type
        if kind in ("unary_operator", "binary_operator") and r_operator(self.source, node) == "~":
            return
        if kind == "null" or (kind == "identifier" and r_identifier(self.source, node) == "."):
            return
        if kind == "call" and (r_callee(self.source, node) or "").rsplit("::", 1)[-1] == "vars":
            return
        if kind == "string":
            self.walk_code_string(r_string_value(self.source, node) or "", node)
            return
        texts: tuple[str, ...] | None = None
        if kind == "identifier":
            texts = self.string_constant(r_identifier(self.source, node) or "")
        elif kind == "call" and r_callee(self.source, node) == "c":
            items = [r_unwrap(argument.value) for argument in r_arguments(self.source, node) if argument.value]
            strings = [r_string_value(self.source, item) for item in items]
            texts = tuple(text for text in strings if text is not None) if all(strings) and strings else None
        if texts is None:
            self.add(
                "banned-call",
                f"{call}() reads a facet as code; pass a formula, vars(), strings or a column constant",
                node,
            )
            return
        for text in texts:
            self.walk_code_string(text, node)

    def check_binary(self, node: Node) -> None:
        operator = r_operator(self.source, node)
        if operator in ("<<-", "->>"):
            self.add("banned-statement", f"'{operator}' assigns outside the function; return the value instead", node)
        elif operator == ":=":
            lhs = node.child_by_field_name("lhs")
            if lhs is not None and not self.injection_target_ok(lhs):
                self.add("banned-call", "the left side of := is a name, a string or !! of a column constant", node)

    def injection_target_ok(self, lhs: Node) -> bool:
        node = r_unwrap(lhs)
        if node.type == "identifier":
            return True
        if node.type == "string":
            text = r_string_value(self.source, node) or ""
            return "{" not in text and "}" not in text
        return self.injected_constant(node) is not None

    def injected_constant(self, node: Node) -> str | None:
        """The column constant `!!X` or `!!!X` injects, else None."""
        bangs = 0
        while node.type == "unary_operator" and r_operator(self.source, node) == "!" and bangs < 3:
            inner = node.child_by_field_name("rhs")
            if inner is None:
                return None
            node = r_unwrap(inner)
            bangs += 1
        if bangs < 2 or node.type != "identifier":
            return None
        name = r_identifier(self.source, node)
        return name if name is not None and self.string_constant(name) is not None else None

    def check_injection(self, visit: Visit) -> None:
        node, parent = visit.node, visit.parent
        if r_operator(self.source, node) != "!":
            return
        if parent is not None and parent.type == "unary_operator" and r_operator(self.source, parent) == "!":
            return  # checked at the outermost `!`
        inner = node.child_by_field_name("rhs")
        inner = r_unwrap(inner) if inner is not None else None
        if inner is None or inner.type != "unary_operator" or r_operator(self.source, inner) != "!":
            return  # a plain negation
        if self.injected_constant(node) is None:
            self.add("banned-call", f"!! and !!! inject only a column constant, not '{self.snippet(node)}'", node)

    def check_save(self) -> None:
        save = self.regions.save
        if save is None:
            self.add("savefig-target", 'no final top-level ggsave(filename = sprintf("plot-%s.png", THEME), ...)', None)
            return
        names = [argument.name for argument in save.arguments]
        line_node = next(
            (visit.node for visit in self.visits if visit.node.type == "call" and self.is_protected_save(visit.node)),
            None,
        )
        if None in names:
            self.add("savefig-target", "the final ggsave passes every argument by name", line_node)
        unknown = sorted({name for name in names if name is not None and name not in SAVE_KEYWORDS})
        if unknown:
            allowed = ", ".join(SAVE_KEYWORDS)
            self.add("savefig-target", f"the final ggsave takes only {allowed}, not {', '.join(unknown)}", line_node)
        repeated = sorted(name for name, count in Counter(names).items() if name is not None and count > 1)
        if repeated:
            self.add("savefig-target", f"the final ggsave repeats {', '.join(repeated)}", line_node)
        if not save.standard_target:
            self.add("savefig-target", 'the final ggsave writes filename = sprintf("plot-%s.png", THEME)', line_node)
        if save.device != SAVE_DEVICE:
            self.add("savefig-target", f"the final ggsave renders through device = {SAVE_DEVICE}", line_node)

    def check_bindings(self) -> None:
        """THEME and each token bound by their own statement alone, the save's names never; by node, not by line.

        Until the review of 2026-10-29 a binding passed when it started on the protected
        line, so `THEME <- Sys.getenv("ANYPLOT_THEME", "light"); THEME <- "dark"` moved the
        save. Now only the protected statement itself counts, and every protected statement
        must also stand alone on its lines (`check_alone`).
        """
        theme = self.regions.theme
        if theme is None:
            self.add("savefig-target", 'no THEME <- Sys.getenv("ANYPLOT_THEME", "light") at the top level', None)
        for binding in self.bindings.get(THEME_NAME, []):
            if theme is None or not self.starts_at(binding.node, theme.statement):
                self.add(
                    "savefig-target",
                    'THEME is bound only by THEME <- Sys.getenv("ANYPLOT_THEME", "light"): the save writes '
                    'sprintf("plot-%s.png", THEME)',
                    binding.node,
                )
        for name in sorted(PROTECTED_NAMES):
            for binding in self.bindings.get(name, []):
                self.add("savefig-target", f"'{name}' may not be bound: the final save and THEME use it", binding.node)
        for token in self.regions.theme_tokens:
            for binding in self.bindings.get(token.name, []):
                if not self.starts_at(binding.node, token.statement):
                    message = f"the theme token {token.name} is bound only by its own statement"
                    self.add("banned-statement", message, binding.node)
        self.check_alone()

    def check_alone(self) -> None:
        """Every protected statement (theme, tokens, palette, placeholder, save) has its lines to itself.

        Another statement on the same line would ride inside the protected region: the edit
        applier protects whole lines, and the loader replaces only the placeholder statement,
        so `df <- load_user_data(); df <- iris` would keep the sample. A trailing comment is fine.
        """
        regions = self.regions
        protected: list[tuple[str, str, Span | None]] = []
        if regions.theme is not None:
            protected.append(("savefig-target", "the THEME statement", regions.theme.statement))
        protected += [
            ("banned-statement", f"the theme token {token.name}", token.statement) for token in regions.theme_tokens
        ]
        if regions.imprint is not None:
            protected.append(("banned-statement", f"the palette {regions.imprint.name}", regions.imprint.statement))
        protected += [("banned-statement", "the placeholder", region.statement) for region in regions.placeholders]
        if regions.save is not None and regions.save.statement is not None:
            protected.append(("savefig-target", "the final ggsave", regions.save.span))
        statements = [
            visit.node
            for visit in self.visits
            if visit.parent is not None
            and visit.parent.type in ("program", "braced_expression")
            and visit.node.is_named
            and visit.node.type != "comment"
        ]
        for rule, what, span in protected:
            if span is None:
                continue
            for node in statements:
                start, end = self.source.char(node.start_byte), self.source.char(node.end_byte)
                if start <= span.start < end or span.start <= start < span.end:
                    continue  # the statement itself, a statement around it (a function body) or one inside it
                if first_line(node) <= span.last_line and last_line(node) >= span.first_line:
                    self.add(rule, f"{what} shares its line with other code; give it lines of its own", node)
                    break

    # -- ADAPTATION ----------------------------------------------------------------------

    def adaptation(self, original_palette: list[str]) -> None:
        self.check_placeholder()
        self.check_rng()
        self.check_literal_data()
        self.check_dataset_packages()
        self.check_palette(original_palette)

    def check_dataset_packages(self) -> None:
        """`library(gapminder)` or `palmerpenguins::penguins`: the sample data of a package, never the user's."""
        for visit in self.visits:
            node = visit.node
            package: str | None = None
            if node.type == "call" and r_callee(self.source, node) in LIBRARY_CALLS:
                arguments = r_arguments(self.source, node)
                value = r_unwrap(arguments[0].value) if arguments and arguments[0].value is not None else None
                package = (r_identifier(self.source, value) or r_string_value(self.source, value)) if value else None
            elif node.type == "namespace_operator":
                lhs = node.child_by_field_name("lhs")
                package = r_identifier(self.source, lhs) if lhs is not None else None
            if package in DATASET_PACKAGES:
                message = f"'{package}' is a dataset package; the data comes from df <- load_user_data()"
                self.add("dataset-package", message, node)

    def check_placeholder(self) -> None:
        statements = [visit.node for visit in self.visits if is_placeholder(self.source, visit.node)]
        if len(statements) != 1:
            message = f"expected exactly one '{PLACEHOLDER}' statement, found {len(statements)}"
            self.add("placeholder-count", message, None)
        for visit in self.visits:
            node = visit.node
            if node.type != "identifier" or r_identifier(self.source, node) != PLACEHOLDER_FUNC:
                continue
            call = visit.parent
            statement = call.parent if call is not None else None
            if not (
                call is not None
                and call.type == "call"
                and visit.field == "function"
                and statement is not None
                and is_placeholder(self.source, statement)
            ):
                message = f"'{PLACEHOLDER_FUNC}' is only allowed in the statement '{PLACEHOLDER}'"
                self.add("placeholder-use", message, node)

    def check_rng(self) -> None:
        for visit in self.visits:
            node = visit.node
            if node.type != "call":
                continue
            callee = r_callee(self.source, node) or ""
            if RNG_DRAWS.match(callee.rsplit("::", 1)[-1]):
                self.add("rng", f"random data generation '{callee}' is not allowed; the data comes from df", node)

    def check_literal_data(self) -> None:
        for visit in self.visits:
            node = visit.node
            if node.type == "call":
                callee = r_callee(self.source, node) or ""
                base = callee.rsplit("::", 1)[-1]
                if base == "data":
                    self.add("literal-data", "data() loads a built-in dataset; the data comes from df", node)
                elif base == "c" and not self.inside_c(visit):
                    count = self.numbers_in(node)
                    if count > MAX_LITERAL_NUMBERS:
                        message = f"literal with {count} numeric values; the limit is {MAX_LITERAL_NUMBERS}, data comes from df"
                        self.add("literal-data", message, node)
            elif node.type == "identifier" and r_is_lookup(visit) and not is_package_argument(self.source, visit):
                name = r_identifier(self.source, node) or ""
                if name in DATASETS and name not in self.bindings:
                    self.add("literal-data", f"'{name}' is a built-in dataset; the data comes from df", node)

    def inside_c(self, visit: Visit) -> bool:
        """Whether a `c()` call is an argument of another `c()` (counted at the outermost one)."""
        argument = visit.parent
        arguments = argument.parent if argument is not None else None
        call = arguments.parent if arguments is not None else None
        return (
            argument is not None
            and argument.type == "argument"
            and call is not None
            and call.type == "call"
            and r_callee(self.source, call) == "c"
        )

    def numbers_in(self, call: Node) -> int:
        count = 0
        stack = [call]
        while stack:
            node = stack.pop()
            for argument in r_arguments(self.source, node):
                if argument.value is None:
                    continue
                value = r_unwrap(argument.value)
                if r_number(self.source, value) is not None:
                    count += 1
                elif value.type == "call" and r_callee(self.source, value) == "c":
                    stack.append(value)
        return count

    def check_palette(self, original_palette: list[str]) -> None:
        original = [colour.upper() for colour in original_palette]
        extension = [colour.upper() for colour in IMPRINT if colour.upper() not in set(original)]
        assigned = 0
        for name in sorted(IMPRINT_NAMES):
            for binding in self.bindings.get(name, []):
                assignment = r_assignment(self.source, binding.node) if binding.node.type == "binary_operator" else None
                if assignment is None or assignment.target.type != "identifier":
                    message = f"'{name}' holds the palette and may only be assigned plainly"
                    self.add("palette-prefix", message, binding.node)
                    continue
                assigned += 1
                if assigned > 1:
                    self.add("palette-prefix", f"{name} is assigned again; keep one literal palette", binding.node)
                    continue
                entries = self.palette_entries(assignment.value)
                if entries is None:
                    self.add("palette-prefix", f"{name} must be a c() of colour string literals", binding.node)
                elif entries[: len(original)] != original:
                    message = f"{name} must keep the {len(original)} original palette entries in order"
                    self.add("palette-prefix", message, binding.node)
                elif len(entries) > len(original) + len(extension):
                    limit = len(original) + len(extension)
                    message = f"{name} has {len(entries)} entries, more than the {limit} colours the palette has"
                    self.add("palette-prefix", message, binding.node)
                elif entries[len(original) :] != extension[: len(entries) - len(original)]:
                    next_positions = ", ".join(extension[:3]) or "none left"
                    message = f"{name} may only be extended with the next Imprint positions ({next_positions})"
                    self.add("palette-prefix", message, binding.node)

    def palette_entries(self, value: Node) -> list[str] | None:
        node = r_unwrap(value)
        if node.type != "call" or r_callee(self.source, node) != "c":
            return None
        entries: list[str] = []
        for argument in r_arguments(self.source, node):
            text = r_string_value(self.source, r_unwrap(argument.value)) if argument.value is not None else None
            if text is None or argument.name is not None or not _HEX.fullmatch(text):
                return None
            entries.append(text.upper())
        return entries
