#' anyplot.ai
#' errorbar-asymmetric: Asymmetric Error Bars Plot
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-09-05

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

# --- Data ---------------------------------------------------------------
# Annual rainfall is right-skewed (occasional very wet years pull the upper
# tail out further than the lower tail), so the 10th-90th percentile range
# around the median is naturally asymmetric.
stations <- c("Manaus", "Singapore", "Mumbai", "Miami", "Bangkok", "Lagos",
              "Jakarta", "Houston", "Tokyo", "Sydney", "Cairo", "Phoenix")
typical_mm <- c(2200, 2100, 1900, 1500, 1450, 1350,
                1750, 1200, 1500, 850, 30, 200)

station_quantiles <- lapply(seq_along(stations), function(i) {
  samples <- rlnorm(2000, meanlog = log(typical_mm[i]), sdlog = 0.28)
  quantile(samples, probs = c(0.10, 0.50, 0.90))
})

df <- tibble::tibble(
  station   = stations,
  p10       = vapply(station_quantiles, `[[`, numeric(1), 1),
  median_mm = vapply(station_quantiles, `[[`, numeric(1), 2),
  p90       = vapply(station_quantiles, `[[`, numeric(1), 3)
) %>%
  mutate(
    error_lower = median_mm - p10,
    error_upper = p90 - median_mm,
    station     = factor(station, levels = stations[order(median_mm)])
  )

# --- Plot -----------------------------------------------------------------
p <- ggplot(df, aes(x = station, y = median_mm)) +
  geom_errorbar(
    aes(ymin = median_mm - error_lower, ymax = median_mm + error_upper),
    color = BRAND, width = 0.3, linewidth = 0.8
  ) +
  geom_point(color = BRAND, size = 2.8) +
  coord_flip() +
  scale_y_continuous(labels = label_comma()) +
  labs(
    title    = "errorbar-asymmetric · r · ggplot2 · anyplot.ai",
    subtitle = "Median annual rainfall with 10th–90th percentile range",
    x        = NULL,
    y        = "Annual rainfall (mm)"
  ) +
  theme_minimal(base_size = 7) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = alpha(INK, 0.15), linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    panel.grid.major.y = element_blank(),
    axis.line.x       = element_line(color = INK_SOFT),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    plot.subtitle     = element_text(color = INK_SOFT, size = 9),
    plot.margin       = margin(12, 16, 12, 12)
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
