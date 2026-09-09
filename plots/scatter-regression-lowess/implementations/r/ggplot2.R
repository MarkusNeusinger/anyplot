#' anyplot.ai
#' scatter-regression-lowess: Scatter Plot with LOWESS Regression
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)
BRAND <- IMPRINT_PALETTE[1]

# --- Data ----------------------------------------------------------------
# Enzyme activity across a temperature range: activity rises as the enzyme
# warms toward its optimum, then collapses once heat denatures the protein.
# This non-monotonic dose-response curve is exactly the case LOWESS is built
# for, since a single polynomial or linear fit cannot follow the rise-then-
# fall shape.
n <- 220
temperature_c <- runif(n, 10, 70)
optimum <- 42
true_activity <- 100 * exp(-((temperature_c - optimum)^2) / (2 * 11^2))
enzyme_activity <- pmax(0, true_activity + rnorm(n, mean = 0, sd = 9))

df <- tibble::tibble(
  temperature_c   = temperature_c,
  enzyme_activity = enzyme_activity
)

# --- Plot ------------------------------------------------------------------
p <- ggplot(df, aes(x = temperature_c, y = enzyme_activity)) +
  geom_point(color = BRAND, size = 2.5, alpha = 0.55) +
  geom_smooth(
    method = "loess", span = 0.4, se = TRUE,
    color = IMPRINT_PALETTE[2], fill = IMPRINT_PALETTE[2],
    linewidth = 1.1, alpha = 0.18
  ) +
  labs(
    title = "scatter-regression-lowess · r · ggplot2 · anyplot.ai",
    x = "Incubation Temperature (°C)",
    y = "Enzyme Activity (% of maximum)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_line(color = INK, linewidth = 0.2),
    axis.line         = element_line(color = INK_SOFT),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12)
  )

# --- Save --------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
