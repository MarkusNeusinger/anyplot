# anyplot.ai: the drawn texts of a ggplot2 plot, for the agents' closing reply.
#
# The renderer's R row names this file as R's user profile (`R_PROFILE_USER`,
# agents/renderer/commands.py), so R reads it before `plot.R`. It only registers a hook:
# when ggplot2 loads, `ggsave` is wrapped, and each save that returned writes
# `texts-<theme>.json`, `{"entries": [[kind, text], ...]}`, the texts of the plot it saved,
# which the harness's exec mode turns into `probe-<theme>.json` under the probe's caps
# (`harness.collect_text_probe`). The texts come from the plot's grob tree (`ggplotGrob`,
# `patchworkGrob` for a patchwork), each named by the layout cell it sits in: the title,
# subtitle and caption, the axis titles (`xlab-*`, `ylab-*`), the axes' tick labels
# (`axis-b`, `axis-l`, ...), the legends (`guide-box-*`), a panel's texts (`geom_text`,
# `annotate`) as annotations, and a facet strip as another text.
#
# The probe runs after `ggsave` returned, the PNG drawn and closed: building the grob a second
# time draws random numbers (a jitter, a bootstrap) and may warn, and after the save neither
# can reach the saved PNG. A save that failed leaves no file. (Capturing the table `ggsave` built,
# at `ggplot_gtable`'s exit, would save the second build, about 0.3 s, but a patchwork
# assembles its table elsewhere, from one such table per plot.)
#
# Best-effort: any failure writes `{"error": "Error"}` instead and prints nothing (warnings and
# messages of the build are muffled, also under `options(warn = 2)`), so the plot's output and
# its exit code stay its own. The grob is built on a null PDF device, so no file is written,
# and the device that was current is current again. The plot code runs after this file and can
# change what it does; the harness and the agents read the result as untrusted data.
local({
  theme <- Sys.getenv("ANYPLOT_THEME", "light")
  limit <- 2000L
  # From the outermost cell in: a legend's own `title` cell sits inside `guide-box-*`, so the box names it first. A
  # patchwork numbers its plots' cells (`title-2`, `axis-l-2`), its own title is `title`.
  kind_of <- function(names) {
    for (name in names) {
      if (startsWith(name, "title")) return("title")
      if (startsWith(name, "subtitle")) return("subtitle")
      if (startsWith(name, "xlab")) return("x axis label")
      if (startsWith(name, "ylab")) return("y axis label")
      if (startsWith(name, "axis-b") || startsWith(name, "axis-t")) return("x tick label")
      if (startsWith(name, "axis-l") || startsWith(name, "axis-r")) return("y tick label")
      if (startsWith(name, "guide-box")) return("legend text")
      if (startsWith(name, "panel")) return("annotation")
      if (startsWith(name, "strip") || startsWith(name, "caption") || startsWith(name, "tag")) return("text")
    }
    "text"
  }
  texts_of <- function(plot) {
    grob <- if (inherits(plot, "patchwork")) patchwork::patchworkGrob(plot) else ggplot2::ggplotGrob(plot)
    found <- list()
    visit <- function(x, names) {
      if (length(found) >= limit || is.null(x) || inherits(x, "zeroGrob")) return(invisible())
      if (inherits(x, "text") && !is.null(x$label)) {
        labels <- x$label
        texts <- if (is.expression(labels) || is.list(labels)) {
          vapply(labels, function(item) paste(deparse(item), collapse = ""), "")
        } else {
          as.character(labels)
        }
        for (text in texts[!is.na(texts)]) found[[length(found) + 1L]] <<- c(kind_of(names), text)
        return(invisible())
      }
      if (inherits(x, "gtable")) {
        for (i in seq_along(x$grobs)) visit(x$grobs[[i]], c(names, x$layout$name[[i]]))
        return(invisible())
      }
      if (inherits(x, "gTree")) for (child in x$children) visit(child, names)
      invisible()
    }
    visit(grob, character())
    found
  }
  json_string <- function(s) {
    s <- enc2utf8(as.character(s))
    s <- gsub("\\", "\\\\", s, fixed = TRUE)
    s <- gsub("\"", "\\\"", s, fixed = TRUE)
    s <- gsub("[[:cntrl:]]", " ", s)
    paste0("\"", s, "\"")
  }
  write_report <- function(text) {
    con <- file(sprintf("texts-%s.json", theme), open = "w", encoding = "UTF-8")
    on.exit(close(con))
    writeLines(text, con, useBytes = TRUE)
  }
  probe <- function(plot) {
    previous <- grDevices::dev.cur()
    grDevices::pdf(NULL)
    on.exit({
      grDevices::dev.off()
      if (previous > 1L) grDevices::dev.set(previous)
    })
    found <- tryCatch(suppressWarnings(suppressMessages(texts_of(plot))), error = function(e) NULL)
    report <- if (is.null(found)) {
      "{\"error\":\"Error\"}"
    } else {
      entries <- vapply(found, function(e) paste0("[", json_string(e[[1]]), ",", json_string(e[[2]]), "]"), "")
      paste0("{\"entries\":[", paste(entries, collapse = ","), "]}")
    }
    tryCatch(write_report(report), error = function(e) NULL)
    invisible()
  }
  safe_probe <- function(plot) {
    tryCatch(probe(plot), error = function(e) NULL)
    invisible()
  }
  # `ggsave` in the namespace becomes a wrapper that saves first and probes after a save that returned. Not a `trace`
  # at its exit: `ggsave`'s own `on.exit()` (no `add = TRUE`) replaces the exit a trace registers. The wrapper takes
  # the plot once, as `ggsave` would (its default `get_last_plot()` resolves in the namespace), passes every other
  # argument on, and calls the function objects themselves, never a name the plot's code could shadow.
  setHook(packageEvent("ggplot2", "onLoad"), function(...) {
    tryCatch(
      {
        original <- get("ggsave", envir = asNamespace("ggplot2"))
        wrapper <- function(filename, plot = get_last_plot(), ...) NULL
        body(wrapper) <- bquote({
          value <- .(original)(filename, plot, ...)
          .(safe_probe)(plot)
          invisible(value)
        })
        environment(wrapper) <- asNamespace("ggplot2")
        utils::assignInNamespace("ggsave", wrapper, ns = "ggplot2")
      },
      error = function(e) NULL
    )
  })
})
