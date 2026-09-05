#' anyplot.ai
#' line-timeseries-rolling: Time Series with Rolling Average Overlay
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID     <- if (THEME == "light") "#CBC9BE" else "#454540"  # INK blended ~25% into PAGE_BG

IMPRINT_PALETTE <- c(
  "#009E73", # 1 - brand green, always first series (raw data)
  "#C475FD"  # 2 - lavender (rolling average)
)

# --- Data ----------------------------------------------------------------
window_size <- 14
n_days <- 180

dates <- seq(as.Date("2025-01-01"), by = "day", length.out = n_days)
seasonal <- 8 * sin(seq(0, 4 * pi, length.out = n_days))
trend <- seq(0, 12, length.out = n_days)
noise <- rnorm(n_days, mean = 0, sd = 4)
engagement_score <- 62 + trend + seasonal + noise

df <- tibble::tibble(date = dates, value = engagement_score) %>%
  mutate(rolling_avg = as.numeric(stats::filter(value, rep(1 / window_size, window_size), sides = 1)))

peak_row <- df %>% filter(!is.na(rolling_avg)) %>% slice_max(rolling_avg, n = 1)

# --- Plot ------------------------------------------------------------------
title_text <- sprintf(
  "%d-Day Rolling Average · line-timeseries-rolling · r · ggplot2 · anyplot.ai",
  window_size
)
title_fontsize <- round(12 * min(1.0, 67 / nchar(title_text)))

p <- ggplot(df, aes(x = date)) +
  geom_line(aes(y = value, color = "Raw Data"), linewidth = 0.5, alpha = 0.4) +
  geom_line(
    data = df %>% filter(!is.na(rolling_avg)),
    aes(y = rolling_avg, color = sprintf("Rolling Average (%d-day)", window_size)),
    linewidth = 1.4
  ) +
  geom_point(data = peak_row, aes(y = rolling_avg), color = IMPRINT_PALETTE[2], size = 2.2) +
  annotate(
    "text",
    x = peak_row$date, y = peak_row$rolling_avg,
    label = sprintf("Peak: %.1f", peak_row$rolling_avg),
    color = INK, size = 3, vjust = -1.2, fontface = "bold"
  ) +
  scale_color_manual(
    values = setNames(
      IMPRINT_PALETTE,
      c("Raw Data", sprintf("Rolling Average (%d-day)", window_size))
    ),
    name = NULL
  ) +
  scale_x_date(date_labels = "%b %Y", date_breaks = "1 month") +
  labs(
    title = title_text,
    x = "Date",
    y = "Engagement Score"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID, linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(angle = 30, hjust = 1),
    axis.line         = element_blank(),
    axis.ticks        = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = title_fontsize),
    legend.position   = "top",
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.key        = element_rect(fill = PAGE_BG, color = NA)
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
