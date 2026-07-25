#' anyplot.ai
#' rose-basic: Basic Rose Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-07-25

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]

# --- Data --------------------------------------------------------------------
# Average monthly rainfall for a temperate maritime city — wet winters,
# dry summers, the seasonal cycle a coxcomb/rose chart is built to reveal.
months <- factor(month.abb, levels = month.abb)
seasonal_signal <- 95 + 55 * cos(2 * pi * (seq_along(months) - 1) / 12)
rainfall_mm <- pmax(15, seasonal_signal + rnorm(12, mean = 0, sd = 8))

df <- tibble::tibble(month = months, rainfall_mm = rainfall_mm)

# --- Plot ---------------------------------------------------------------------
# Half a bar-width rotation centers January at 12 o'clock instead of its edge.
start_offset <- -(2 * pi / 12) / 2

title_text <- "rose-basic · r · ggplot2 · anyplot.ai"
title_fontsize <- if (nchar(title_text) > 67) round(12 * 67 / nchar(title_text)) else 12

p <- ggplot(df, aes(x = month, y = rainfall_mm)) +
  geom_col(fill = BRAND, color = PAGE_BG, linewidth = 0.4, width = 1) +
  coord_polar(theta = "x", start = start_offset) +
  scale_y_continuous(
    limits = c(0, max(df$rainfall_mm) * 1.15),
    breaks = pretty(c(0, df$rainfall_mm), n = 4),
    expand = c(0, 0)
  ) +
  labs(title = title_text, x = NULL, y = "Rainfall (mm)") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major   = element_line(color = scales::alpha(INK, 0.15), linewidth = 0.3),
    panel.grid.minor   = element_blank(),
    axis.title.y       = element_text(color = INK_SOFT, size = 8),
    axis.title.x       = element_blank(),
    axis.text.x        = element_text(color = INK, size = 10, face = "bold"),
    axis.text.y        = element_text(color = INK_SOFT, size = 7),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = title_fontsize, hjust = 0.5, margin = margin(b = 12)),
    plot.margin        = margin(t = 20, r = 30, b = 10, l = 30)
  )

# --- Save ---------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
