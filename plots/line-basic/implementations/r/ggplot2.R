#' anyplot.ai
#' line-basic: Basic Line Plot
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-08-24

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
BRAND    <- "#009E73" # Imprint palette position 1 — ALWAYS first series

# --- Data: daily temperature readings across a 90-day summer season --------
n_days <- 90
day_of_season <- 1:n_days
seasonal_curve <- 24 + 6 * sin(pi * day_of_season / n_days)
daily_temp_c <- seasonal_curve + rnorm(n_days, mean = 0, sd = 0.7)

df <- tibble::tibble(day = day_of_season, temperature = daily_temp_c)

# --- Plot --------------------------------------------------------------------
plot_title <- "line-basic · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = day, y = temperature)) +
  geom_line(color = BRAND, linewidth = 1.1) +
  labs(
    title = plot_title,
    x = "Day of Season",
    y = "Temperature (°C)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.2),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = 12),
    plot.margin        = margin(12, 16, 8, 8)
  )

# --- Save (PNG, both themes) -------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
