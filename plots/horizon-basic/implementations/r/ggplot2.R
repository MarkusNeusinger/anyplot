#' anyplot.ai
#' horizon-basic: Horizon Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-08-18

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME     <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG   <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK       <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT  <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint diverging endpoints (imprint_div) — folded bands climb toward these
NEG_HUE <- "#AE3030"  # matte red — below baseline
POS_HUE <- "#4467A3"  # blue — above baseline

# --- Data ---------------------------------------------------------------------
# 8 microservices reporting CPU-utilization deviation from their rolling
# baseline, sampled hourly over ~8 days. Each series is z-scored so all lanes
# share the same magnitude scale, which is what makes the folded bands
# comparable across the panel.
services <- c(
  "api-gateway", "auth-service", "payment-svc", "search-index",
  "user-profile", "notification", "cache-layer", "recommender"
)
n_series <- length(services)
n_time <- 200

start_time <- as.POSIXct("2024-06-01 00:00:00", tz = "UTC")
dates <- start_time + (0:(n_time - 1)) * 3600

t_idx  <- 0:(n_time - 1)
freqs  <- 0.02 + seq_len(n_series) * 0.005
phases <- seq_len(n_series) * 0.7
amps   <- 1 + seq_len(n_series) * 0.1

trend_matrix <- outer(t_idx, seq_len(n_series), function(t, i) {
  sin(t * freqs[i] + phases[i]) * amps[i]
})
noise_matrix <- matrix(rnorm(n_time * n_series, 0, 0.6), nrow = n_time)
spike_mask   <- matrix(runif(n_time * n_series) > 0.97, nrow = n_time)
spike_matrix <- matrix(rnorm(n_time * n_series, 0, 3), nrow = n_time) * spike_mask
z_matrix <- scale(trend_matrix + noise_matrix + spike_matrix)  # z-score per column

df <- tibble::tibble(
  date   = rep(dates, times = n_series),
  series = factor(rep(services, each = n_time), levels = services),
  value  = as.numeric(z_matrix)
)

# --- Fold into horizon bands ---------------------------------------------------
# 3 bands per polarity: band k covers the k-th slice of |value|, clipped and
# rescaled into the fixed lane height, so a deeper band = bigger deviation.
n_bands    <- 3
row_height <- 1
lane_gap   <- 0.88  # leaves a visible gap between stacked lanes
band_height <- max(abs(df$value)) / n_bands

df <- df %>%
  mutate(
    series_index = as.integer(series),
    lane_base    = (n_series - series_index) * row_height,
    pos_1 = pmin(pmax(value - 0 * band_height, 0), band_height) / band_height * row_height * lane_gap,
    pos_2 = pmin(pmax(value - 1 * band_height, 0), band_height) / band_height * row_height * lane_gap,
    pos_3 = pmin(pmax(value - 2 * band_height, 0), band_height) / band_height * row_height * lane_gap,
    neg_1 = pmin(pmax(-value - 0 * band_height, 0), band_height) / band_height * row_height * lane_gap,
    neg_2 = pmin(pmax(-value - 1 * band_height, 0), band_height) / band_height * row_height * lane_gap,
    neg_3 = pmin(pmax(-value - 2 * band_height, 0), band_height) / band_height * row_height * lane_gap
  )

lane_lookup <- df %>% distinct(series, lane_base)

# --- Plot -----------------------------------------------------------------
p <- ggplot(df, aes(x = date)) +
  geom_hline(
    data = lane_lookup, aes(yintercept = lane_base),
    color = scales::alpha(INK_MUTED, 0.35), linewidth = 0.3
  ) +
  geom_ribbon(aes(ymin = lane_base, ymax = lane_base + pos_1, group = series), fill = POS_HUE, alpha = 0.35) +
  geom_ribbon(aes(ymin = lane_base, ymax = lane_base + pos_2, group = series), fill = POS_HUE, alpha = 0.65) +
  geom_ribbon(aes(ymin = lane_base, ymax = lane_base + pos_3, group = series), fill = POS_HUE, alpha = 1.0) +
  geom_ribbon(aes(ymin = lane_base, ymax = lane_base + neg_1, group = series), fill = NEG_HUE, alpha = 0.35) +
  geom_ribbon(aes(ymin = lane_base, ymax = lane_base + neg_2, group = series), fill = NEG_HUE, alpha = 0.65) +
  geom_ribbon(aes(ymin = lane_base, ymax = lane_base + neg_3, group = series), fill = NEG_HUE, alpha = 1.0) +
  scale_x_datetime(date_labels = "%b %d", expand = expansion(mult = c(0.01, 0.01))) +
  scale_y_continuous(
    breaks = lane_lookup$lane_base + row_height / 2,
    labels = as.character(lane_lookup$series),
    expand = expansion(mult = c(0.03, 0.08))
  ) +
  labs(
    title = "horizon-basic · r · ggplot2 · anyplot.ai",
    subtitle = "CPU-utilization deviation (z-score) per microservice, folded into 3 bands",
    x = "Date",
    caption = "Blue = above baseline, red = below — deeper shade means a larger deviation",
    y = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title.x      = element_text(color = INK, size = 10),
    axis.text.x       = element_text(color = INK_SOFT, size = 8),
    axis.ticks.x      = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.line.x       = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.text.y       = element_text(color = INK_SOFT, size = 8, hjust = 1),
    axis.ticks.y      = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    plot.subtitle     = element_text(color = INK_SOFT, size = 8),
    plot.caption      = element_text(color = INK_MUTED, size = 7, hjust = 0),
    plot.margin       = margin(10, 16, 10, 10)
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
