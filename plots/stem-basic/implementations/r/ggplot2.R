library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
  "#009E73", # 1 - first categorical series (brand green)
  "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data --------------------------------------------------------------------
# Discrete-time impulse response of a damped, decaying oscillator - the
# canonical stem-plot use case in signal processing.
n <- 40
df <- tibble::tibble(
  n = 0:(n - 1),
  amplitude = exp(-0.09 * n) * cos(0.55 * n) + rnorm(n, sd = 0.015)
)

# --- Plot ----------------------------------------------------------------
title_txt <- "stem-basic · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = n, y = amplitude)) +
  geom_hline(yintercept = 0, color = INK_SOFT, linewidth = 0.4) +
  geom_segment(
    aes(x = n, xend = n, y = 0, yend = amplitude),
    color = IMPRINT_PALETTE[1], linewidth = 0.9
  ) +
  geom_point(
    fill = IMPRINT_PALETTE[1],
    color = if (THEME == "light") "#FFFDF6" else "#242420",
    shape = 21, size = 3.2, stroke = 0.9
  ) +
  scale_x_continuous(breaks = seq(0, n - 1, by = 5)) +
  labs(
    title = title_txt,
    x = "Sample index n",
    y = "Amplitude"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    plot.margin       = margin(t = 12, r = 16, b = 8, l = 8)
  )

# --- Save --------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
