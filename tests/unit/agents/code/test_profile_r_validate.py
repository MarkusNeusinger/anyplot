"""Tests for agents/anyplot/code/profiles/r/validate.py: the SECURITY and ADAPTATION profiles for R."""

from collections import Counter

import pytest

from agents.anyplot.code.profiles.r.normalise import normalise
from agents.anyplot.code.profiles.r.validate import LIBRARY_ALLOWLIST, denied, validate_adaptation, validate_security
from agents.anyplot.code.validate import Finding

from .conftest import R_CATALOGUE_FILES, R_CATALOGUE_NORMALISED, source


SAVE = (
    'ggsave(filename = sprintf("plot-%s.png", THEME), plot = p, device = ragg::agg_png, '
    'width = 8, height = 4.5, units = "in", dpi = 400)\n'
)


def program(body: str) -> str:
    """A minimal valid R plot around `body`: the theme statement first, the protected save last."""
    return f'library(ggplot2)\nTHEME <- Sys.getenv("ANYPLOT_THEME", "light")\n{body}\n{SAVE}'


def rules(findings: list[Finding]) -> set[str]:
    return {finding.rule for finding in findings}


def test_the_normalised_catalogue_file_in_miniature_passes() -> None:
    assert validate_security(R_CATALOGUE_NORMALISED) == []


def test_a_minimal_program_passes() -> None:
    assert validate_security(program("p <- ggplot(df, aes(x, y)) + geom_point()")) == []


@pytest.mark.parametrize(
    ("body", "rule"),
    [
        # the named bypasses of the design pass (2026-10-29)
        ('x <- get("system")("id")', "banned-name"),
        ('x <- "system"("id")', "banned-call"),
        ('x <- base::system("id")', "banned-import"),
        ('x <- lapply(1, paste0("sys", "tem"))', "banned-call"),
        ('THEME <<- "dark"', "banned-statement"),
        ('sprintf <- function(...) "x.png"', "savefig-target"),
        ('p <- p + facet_wrap("~system()")', "banned-name"),
        ('d <- dplyr::mutate(d, dplyr::across(x, mean, .names = "{system()}"))', "banned-keyword"),
        ("d <- tibble::tibble(!!call2(sym) := 1)", "banned-call"),
        # more routes to a function from a string or a value
        ('x <- match.fun("system")', "banned-name"),
        ('x <- .env[["system"]]', "banned-name"),
        ('x <- `system`("id")', "banned-name"),
        ('x <- (paste0("sys", "tem"))("id")', "banned-call"),
        ('x <- do.call("merge", parts)', "banned-call"),
        ('x <- do.call(paste0("rb", "ind"), parts)', "banned-call"),
        ("f <- function(g) lapply(1, g)", "banned-call"),
        ('h <- paste0("sys", "tem")\nx <- sapply(1, h)', "banned-call"),
        ('x <- Reduce(paste0("su", "m"), 1:3)', "banned-call"),
        ('p <- p + stat_summary(fun = paste0("me", "an"))', "banned-call"),
        ('x <- eval(parse(text = "1"))', "banned-name"),
        ("x <- evalq(1)", "banned-name"),
        ("x <- grDevices:::png", "banned-import"),
        ('x <- utils::read.csv("x.csv")', "banned-import"),
        ('x <- tools::file_ext("x")', "banned-import"),
        ("x <- gridExtra::grid.arrange(p)", "banned-import"),
        ('x <- stats::as.formula("y ~ x")', "banned-name"),
        # facets and formulas that are strings
        ('GROUP <- "system()"\np <- p + facet_wrap(GROUP)', "banned-name"),
        ('p <- p + facet_grid(rows = "system()")', "banned-name"),
        ('p <- p + facet_wrap(paste0("~", "x"))', "banned-call"),
        ('m <- lm("y ~ system(1)", data = d)', "banned-name"),
        ('p <- p + geom_smooth(formula = paste0("y", "~x"))', "banned-call"),
        # tidy evaluation
        ("d <- dplyr::mutate(d, !!computed := 1)", "banned-call"),
        ('d <- dplyr::mutate(d, "{system()}" := 1)', "banned-call"),
        ('d <- tidyr::pivot_wider(d, names_glue = "{.value}_{system()}")', "banned-keyword"),
        ('d <- dplyr::across(x, mean, .names = paste0("{.col}"))', "banned-keyword"),
        # files, devices, processes
        ('cat("x", file = "out.txt")', "banned-keyword"),
        ('png("x.png")', "banned-name"),
        ('ragg::agg_png("x.png")', "savefig-target"),
        ('x <- system2("id")', "banned-name"),
        ('x <- readLines("/etc/passwd")', "banned-name"),
        ('write.csv(d, "x.csv")', "banned-name"),
        ('writeLines("x", "y")', "banned-name"),
        ('x <- file.exists("x")', "banned-name"),
        ('x <- Sys.getenv("HOME")', "banned-name"),
        ('x <- Sys.which("sh")', "banned-name"),
        ("x <- sys.function()", "banned-name"),
        ('source("x.R")', "banned-name"),
        ("options(warn = 2)", "banned-name"),
        ('x <- "https://example.com"', "url-literal"),
        ('x <- "//cdn.example.com/x.png"', "url-literal"),
        ('x <- "' + "a" * 201 + '"', "string-length"),
        # packages
        ("library(readr)", "banned-import"),
        ('library("httr")', "banned-import"),
        ("library(ggplot2, character.only = TRUE)", "banned-import"),
        ("require(curl)", "banned-import"),
        # the save and its names
        ('ggsave("other.png", p)', "savefig-target"),
        ("f <- ggsave", "savefig-target"),
        ('ggplot2::ggsave("x.png", p)', "savefig-target"),
        ('THEME <- "dark"', "savefig-target"),
        ("f <- function(THEME) THEME", "savefig-target"),
        ("for (THEME in 1:2) 1", "savefig-target"),
        ('Sys.getenv <- function(...) "x"', "savefig-target"),
        ("x <- 1 ->> y", "banned-statement"),
    ],
)
def test_refused(body: str, rule: str) -> None:
    findings = validate_security(program(body))

    assert rule in rules(findings), findings


@pytest.mark.parametrize(
    "body",
    [
        "x <- do.call(rbind, parts)",
        "x <- lapply(parts, function(part) part + 1)",
        "x <- sapply(parts, \\(part) part * 2)",
        "x <- sapply(parts, mean)",
        "x <- vapply(parts, nchar, integer(1))",
        'x <- outer(a, b, "-")',
        'x <- Reduce("+", parts)',
        "x <- Filter(Negate(is.null), parts)",
        "d <- dplyr::mutate(d, dplyr::across(c(a, b), list(min = min, max = max)))",
        "d <- dplyr::mutate(d, dplyr::across(c(a, b), ~ .x * 2))",
        'p <- p + geom_smooth(method = "lm", formula = y ~ x)',
        "p <- p + stat_summary(fun = mean)",
        "p <- p + facet_wrap(~ group)",
        "p <- p + facet_grid(rows = vars(a), cols = vars(b))",
        'p <- p + facet_wrap("group")',
        "p <- p + facet_wrap(labeller = label_wrap_gen(width = 11), ~ g)",
        "y <- lowess(x, f = 0.3)",
        'SPEND <- "Spend"\nd <- tibble::tibble(!!SPEND := 1:3)',
        'COLS <- c("a", "b")\nd <- dplyr::select(d, !!!COLS)',
        'd <- dplyr::mutate(d, dplyr::across(x, mean, .names = "{.col}_{.fn}"))',
        "x <- pdf(NULL)",
        "x <- grDevices::pdf(NULL)",
        "x <- scales::label_comma()(1234)",
        'x <- grDevices::colorRampPalette(c("#000000", "#FFFFFF"))(10)',
        "x <- utils::head(d, 3)",
        'x <- tools::toTitleCase("a title")',
        "g <- gridExtra::arrangeGrob(p, q)",
        "x <- Sys.time()",
        'x <- format(Sys.Date(), "%Y")',
        "x <- !TRUE",
        'x <- c(writer = "a", evaluation = 1)',
        "x <- d$source",
        "f <- function(n) n + 1\nx <- sapply(1:3, f)",
        'label <- "Week 1 cliff: ~5 pp drop"',
    ],
)
def test_allowed(body: str) -> None:
    assert validate_security(program(body)) == []


@pytest.mark.parametrize(
    "body",
    [
        # a user's column named like a denied function is data (owner decision of 2026-10-29)
        'SOURCE <- "source"  # role: source\nd <- dplyr::filter(d, .data[[SOURCE]] == "A")',
        'cols <- c("file", "load", "options", "body")',
        'd <- tibble::tribble(~source, ~target, ~value, "A", "B", 3)',
        "d <- dplyr::mutate(d, origin = source, n = dplyr::n())",
        "d <- dplyr::group_by(d, source)",
        "d <- dplyr::arrange(d, match(source, order))",
        "p <- ggplot(d, aes(x = file, y = load, fill = body))",
        "p <- p + facet_wrap(vars(source))",
        'p <- p + facet_wrap("source")',
        "d <- tidyr::pivot_longer(d, -source)",
        "m <- lm(value ~ source, data = d)",
        'm <- lm("value ~ load", data = d)',
        "x <- d$source",
        'x <- list(source = 1, options = "a")',
        'by <- c("source" = "node")',
        "s <- subset(d, source == 'A')",
    ],
)
def test_denied_words_as_data_pass(body: str) -> None:
    assert validate_security(program(body)) == []


@pytest.mark.parametrize(
    ("body", "message"),
    [
        # a denied name as a callee or a function-valued argument, also inside a data mask
        ("d <- dplyr::mutate(d, x = source(1))", "'source' is not allowed"),
        ("d <- dplyr::mutate(d, x = sapply(y, source))", "'source' is not allowed"),
        ("p <- ggplot(d, aes(x = system('id')))", "'system' is not allowed"),
        ('d <- dplyr::summarise(d, x = lapply(y, "system"))', "names the denied function 'system'"),
        # a denied name as a value outside a data mask
        ("x <- source", "'source' is not allowed"),
        ("x <- list(load)", "'load' is not allowed"),
        ("x <- c(get)", "'get' is not allowed"),
        ("f <- function() return(file)", "'file' is not allowed"),
        ("x <- identity(parse)", "'parse' is not allowed"),
        ("source <- 1", "'source' is not allowed"),
        # strings that become functions
        ('x <- outer(1, 2, "system")', "names the denied function 'system'"),
        ('x <- Map("source", 1)', "names the denied function 'source'"),
        ('p <- p + stat_summary(fun = "load")', "names the denied function 'load'"),
        ('x <- purrr_like <- lapply(1, list("get"))', "names the denied function 'get'"),
        ('p <- p + facet_wrap("~system()")', "in a code string: 'system' is not allowed"),
    ],
)
def test_denied_words_as_functions_are_refused(body: str, message: str) -> None:
    findings = validate_security(program(body))

    assert any(message in finding.message for finding in findings), findings


@pytest.mark.parametrize(
    ("body", "allowed"),
    [
        ("m <- lm(y ~ x, data = d)", True),
        ('m <- lm("y ~ x", data = d)', True),
        ("fml <- y ~ x\nm <- glm(fml, data = d)", True),
        ('fml <- "y ~ x"\nm <- nls(fml, data = d)', True),
        ("p <- p + geom_smooth(method = 'lm', formula = y ~ poly(x, 2))", True),
        ("a <- aggregate(d$v, by = list(d$g), FUN = sum)", True),
        ("a <- aggregate(v ~ g, data = d, FUN = mean)", True),
        ("p <- prcomp(X, scale. = TRUE)", True),
        ("t <- t.test(d$a, d$b)", True),
        ('m <- lm(paste0("y ~ ", x), data = d)', False),
        ('m <- lm(sprintf("%s ~ x", y), data = d)', False),
        ('fml <- paste("y", "~ x")\nm <- glm(fml, data = d)', False),
        ("m <- lm(f, data = d)", False),
        ("fml <- y ~ x\nfml <- y ~ z\nm <- lm(fml, data = d)", False),
        ('a <- aggregate(paste("v ~", g), data = d, FUN = sum)', False),
        ('fml <- format("v ~ g")\nt <- t.test(fml, data = d)', False),
        ('p <- p + geom_smooth(formula = paste0("y", "~x"))', False),
        ("p <- p + geom_smooth(formula = make_formula())", False),
    ],
)
def test_formula_positions(body: str, allowed: bool) -> None:
    findings = validate_security(program(body))

    assert (findings == []) is allowed, findings
    assert allowed or {finding.rule for finding in findings} == {"banned-call"}


THEME_LINE = 'THEME <- Sys.getenv("ANYPLOT_THEME", "light")'
TOKEN_LINE = 'INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"'


@pytest.mark.parametrize(
    ("code", "rule", "message"),
    [
        # review of 2026-10-29: a binding on the protected line passed the line comparison
        (f'{THEME_LINE}; THEME <- "dark"\n{SAVE}', "savefig-target", "THEME is bound only by"),
        (f'{THEME_LINE}\n{TOKEN_LINE}; INK <- "#FF00FF"\n{SAVE}', "banned-statement", "INK is bound only by its own"),
        (f"{THEME_LINE}\ndf <- load_user_data(); df <- iris\n{SAVE}", "banned-statement", "the placeholder shares"),
        (f"{THEME_LINE}\n{SAVE.rstrip()}; x <- 1\n", "savefig-target", "the final ggsave shares"),
        (f"{THEME_LINE}; x <- 1\n{SAVE}", "savefig-target", "the THEME statement shares"),
        (f'{THEME_LINE}\nIMPRINT_PALETTE <- c("#009E73", "#C475FD"); y <- 2\n{SAVE}', "banned-statement", "palette"),
    ],
)
def test_protected_statements_are_bound_once_and_alone_on_their_lines(code: str, rule: str, message: str) -> None:
    findings = validate_security(code)

    assert any(finding.rule == rule and message in finding.message for finding in findings), findings


def test_a_trailing_comment_and_a_placeholder_in_a_function_body_are_fine() -> None:
    code = f"{THEME_LINE}  # the theme\nf <- function() {{\n  df <- load_user_data()\n  df\n}}\n{SAVE}"

    assert validate_security(code) == []


@pytest.mark.parametrize(
    ("body", "message"),
    [
        # the two routes of the security review of 2026-10-29
        ('x <- with(d, (function(f) f("id"))(system))', "called where it is written"),
        ('d <- dplyr::mutate(d, g = list(system), out = g[[1]]("id"))', "taken out of a value"),
        # the shapes behind them
        ('x <- (\\(f) f("id"))(1)', "called where it is written"),
        ('y <- x$f("id")', "taken out of a value"),
        ('y <- x[1]("id")', "taken out of a value"),
        ('h <- function(g) g("x")', "'g' is a parameter"),
        ("h <- \\(g) g(1)", "'g' is a parameter"),
        ('d <- dplyr::mutate(d, x = identity(system)("id"))', "called at once"),
        ('d <- dplyr::summarise(d, x = dplyr::first(fns)("id"))', "called at once"),
        ('d <- dplyr::mutate(d, r = lapply(list(system), do.call, list("id")))', "do.call is only ever called"),
        ('d <- dplyr::mutate(d, r = .mapply(system, list("id"), NULL))', "'system' is not allowed"),
        ('x <- with(d, system("id"))', "'system' is not allowed"),
        ("x <- with(d, list(source))", "'source' is not allowed"),
    ],
)
def test_calls_that_would_run_a_held_function_are_refused(body: str, message: str) -> None:
    findings = validate_security(program(body))

    assert any(finding.rule in ("banned-call", "banned-name") and message in finding.message for finding in findings)


@pytest.mark.parametrize(
    "body",
    [
        'x <- colorRampPalette(c("#000000", "#FFFFFF"))(5)',
        "y <- scales::label_percent()(0.5)",
        "z <- scales::hue_pal()(3)",
        "w <- ecdf(v)(2)",
        "p <- p + labs(y = expression(-log[10](italic(p))))",
        "p <- p + scale_y_continuous(transform = scales::transform_log())",
        "p <- p + scale_x_continuous(transform = log10_trans())",
        "p <- p + scale_y_continuous(transform = scales::trans_new('sq', function(x) x^2, function(x) sqrt(x)))",
        'a <- do.call("rbind", parts)',
        'b <- do.call("cbind", parts)',
        "c2 <- do.call(paste0, parts)",
        "c3 <- do.call(paste, parts)",
        "f <- function(x) round(x, 2)\ny <- f(1.234)",
    ],
)
def test_builders_and_named_calls_stay_allowed(body: str) -> None:
    assert validate_security(program(body)) == []


@pytest.mark.parametrize(
    "body", ['x <- textConnection("a")', "x <- rawConnection(raw(0))", 'x <- do.call("system", l)']
)
def test_connections_and_other_do_call_targets_are_refused(body: str) -> None:
    assert validate_security(program(body)) != []


def test_dataset_packages_are_adaptation_findings_not_security() -> None:
    """gapminder and palmerpenguins are in the toolchain image: their sample data is for the adapter to replace
    (owner decision of 2026-10-29), so SECURITY passes them and ADAPTATION names them (`dataset-package`)."""
    code = program("library(palmerpenguins)\nd <- penguins\ng <- gapminder::gapminder")

    assert validate_security(code) == []
    findings = validate_adaptation(code, original_palette=[])
    assert {finding.rule for finding in findings} >= {"dataset-package", "literal-data"}
    assert [finding.line for finding in findings if finding.rule == "dataset-package"] == [3, 5]


def test_the_protected_save_is_pinned() -> None:
    bad = SAVE.replace("dpi = 400)", "dpi = 400, limitsize = FALSE)")
    findings = validate_security(f'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n{bad}')

    assert [finding.rule for finding in findings] == ["savefig-target"]
    assert "limitsize" in findings[0].message


@pytest.mark.parametrize(
    ("save", "message"),
    [
        (SAVE.replace("ragg::agg_png", "grDevices::png"), "device = ragg::agg_png"),
        (SAVE.replace('sprintf("plot-%s.png", THEME)', '"plot.png"'), "filename ="),
        (SAVE.replace("filename = ", ""), "by name"),
        ("", "no final top-level ggsave"),
    ],
)
def test_the_protected_save_findings(save: str, message: str) -> None:
    findings = validate_security(f'THEME <- Sys.getenv("ANYPLOT_THEME", "light")\n{save}')

    assert any(finding.rule == "savefig-target" and message in finding.message for finding in findings), findings


def test_without_the_theme_statement() -> None:
    findings = validate_security(SAVE)

    assert any("no THEME" in finding.message for finding in findings)


def test_a_theme_token_is_bound_only_by_its_line() -> None:
    code = program('INK <- if (THEME == "light") "#000000" else "#FFFFFF"\nINK <- "#FF00FF"')

    assert rules(validate_security(code)) == {"banned-statement"}


def test_findings_name_lines_and_never_echo_strings() -> None:
    code = program('x <- 1\ny <- lapply(1, paste0("secret", "value"))')
    findings = validate_security(code)

    assert [finding.line for finding in findings] == [4]
    assert "secret" not in findings[0].message


@pytest.mark.parametrize(("code", "rule"), [("x <- (\n", "syntax"), ('x <- "\\q"\n', "syntax"), ("x" * 50_000, "size")])
def test_unreadable_code_is_a_finding(code: str, rule: str) -> None:
    assert [finding.rule for finding in validate_security(code)] == [rule]


@pytest.mark.parametrize(
    ("name", "is_denied"),
    [
        ("system", True),
        ("eval", True),
        ("eval_tidy", True),
        ("evaluation", False),
        ("write.csv", True),
        ("writeLines", True),
        ("writer", False),
        ("read.table", True),
        ("readings", False),
        ("Sys.time", False),
        ("Sys.setenv", True),
        ("socketConnection", True),
        ("file.path", True),
        ("filename", False),
        ("dir", False),
    ],
)
def test_denied_names_and_families(name: str, is_denied: bool) -> None:
    assert denied(name) is is_denied


def test_the_library_allowlist_is_the_owners() -> None:
    assert LIBRARY_ALLOWLIST == {
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


# --- ADAPTATION ---------------------------------------------------------------------------

ADAPTED = (
    source("""
    library(ggplot2)
    THEME <- Sys.getenv("ANYPLOT_THEME", "light")
    IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3")
    SPEND <- "Spend"  # role: x
    df <- load_user_data()
    p <- ggplot(df, aes(x = .data[[SPEND]])) + geom_histogram(fill = IMPRINT_PALETTE[1])
""")
    + SAVE
)
PALETTE = ["#009E73", "#C475FD", "#4467A3"]


def test_an_adapted_working_form_passes_both_profiles() -> None:
    assert validate_security(ADAPTED) == []
    assert validate_adaptation(ADAPTED, original_palette=PALETTE) == []


@pytest.mark.parametrize(
    ("change", "rule"),
    [
        (("df <- load_user_data()\n", ""), "placeholder-count"),
        (("df <- load_user_data()\n", "df <- load_user_data()\ndf <- load_user_data()\n"), "placeholder-count"),
        (("p <- ggplot", "f <- load_user_data\np <- ggplot"), "placeholder-use"),
        (("p <- ggplot", "noise <- rnorm(10)\np <- ggplot"), "rng"),
        (("p <- ggplot", "draws <- MASS::mvrnorm(10, 0, 1)\np <- ggplot"), "rng"),
        (("p <- ggplot", "v <- c(" + ", ".join(str(n) for n in range(21)) + ")\np <- ggplot"), "literal-data"),
        (("p <- ggplot", "v <- c(1, c(" + ", ".join(str(n) for n in range(20)) + "))\np <- ggplot"), "literal-data"),
        (("p <- ggplot", "data(iris)\np <- ggplot"), "literal-data"),
        (("p <- ggplot", "d2 <- mtcars\np <- ggplot"), "literal-data"),
        (('c("#009E73", "#C475FD", "#4467A3")', 'c("#C475FD", "#009E73", "#4467A3")'), "palette-prefix"),
        (('"#4467A3")', '"#4467A3", "#FF00FF")'), "palette-prefix"),
        (("p <- ggplot", 'IMPRINT_PALETTE[4] <- "#FF00FF"\np <- ggplot'), "palette-prefix"),
        (("p <- ggplot", 'IMPRINT_PALETTE <- c("#009E73")\np <- ggplot'), "palette-prefix"),
    ],
)
def test_adaptation_findings(change: tuple[str, str], rule: str) -> None:
    code = ADAPTED.replace(*change)

    assert rule in rules(validate_adaptation(code, original_palette=PALETTE))


@pytest.mark.parametrize(
    "line",
    [
        "set.seed(1)",
        "jitter_x <- jitter(df[[SPEND]])",
        "pick <- sample(seq_len(nrow(df)), 10)",
        "u <- runif(nrow(df))",
        'IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233")',
        "v <- c(1, 2, 3)",
        "trees <- 3\nn <- trees + 1",
    ],
)
def test_adaptation_allows(line: str) -> None:
    code = ADAPTED.replace("p <- ggplot", f"{line}\np <- ggplot")
    if line.startswith("IMPRINT_PALETTE"):
        code = ADAPTED.replace('IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3")', line)

    assert validate_adaptation(code, original_palette=PALETTE) == []


def test_catalogue_corpus() -> None:
    """SECURITY over the 325 normalised catalogue files (2026-10-29, after the owner's narrowing of the denied-name
    rule): 6 files have findings. The 4 map specs that install or load geodata packages
    (flowmap-origin-destination, heatmap-geographic, map-connection-lines, map-projections; the other 9 map specs
    pass SECURITY and are blocked by name), qrcode-basic (a URL and the qrcode package) and maze-circular's `<<-`.
    The 7 flow files that name a column `source` and the 2 dataset-package files pass SECURITY now."""
    flagged: dict[str, Counter[str]] = {}
    for path in R_CATALOGUE_FILES:
        findings = validate_security(normalise(path.read_text(encoding="utf-8")))
        if findings:
            flagged[path.parts[-4]] = Counter(finding.rule for finding in findings)

    assert sorted(flagged) == [
        "flowmap-origin-destination",
        "heatmap-geographic",
        "map-connection-lines",
        "map-projections",
        "maze-circular",
        "qrcode-basic",
    ]
    assert set(flagged["maze-circular"]) == {"banned-statement"}
    assert set(flagged["qrcode-basic"]) == {"banned-import", "url-literal"}
