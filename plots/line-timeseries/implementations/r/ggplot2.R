#' anyplot.ai
#' line-timeseries: Time Series Line Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 79/100 | Created: 2026-09-05

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID     <- scales::alpha(INK, 0.15)  # faint grid — element_line has no alpha arg
BRAND    <- "#009E73"  # Imprint palette position 1 — ALWAYS first series
MUTED    <- if (THEME == "light") "#6B6A63" else "#A8A79F"  # Imprint muted anchor — reference line

# --- Data ---------------------------------------------------------------
# Six months of daily outdoor temperature readings with a seasonal warm-up
# trend, weekly wobble, and day-to-day sensor noise.
n_days <- 182
dates <- seq(as.Date("2024-01-01"), by = "day", length.out = n_days)
day_idx <- seq_len(n_days)

seasonal_trend <- 4 + 14 * sin(2 * pi * (day_idx - 109) / 365)
weekly_wobble <- 1.2 * sin(2 * pi * day_idx / 7)
sensor_noise <- rnorm(n_days, mean = 0, sd = 1.6)
temperature_c <- seasonal_trend + weekly_wobble + sensor_noise

df <- tibble::tibble(date = dates, temperature_c = temperature_c)

title_text <- "line-timeseries · r · ggplot2 · anyplot.ai"

# --- Plot -----------------------------------------------------------------
p <- ggplot(df, aes(x = date, y = temperature_c)) +
  geom_smooth(
    method = "loess", span = 0.3, se = FALSE,
    color = MUTED, linewidth = 0.8, linetype = "dashed"
  ) +
  geom_line(color = BRAND, linewidth = 2) +
  scale_x_date(
    date_breaks = "1 month",
    labels = scales::label_date("%b")
  ) +
  scale_y_continuous(labels = scales::label_number(suffix = "°C")) +
  labs(
    title = title_text,
    x = "Date",
    y = "Outdoor Temperature (°C)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID, linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(angle = 30, hjust = 1),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    plot.margin       = margin(t = 14, r = 20, b = 10, l = 10)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
