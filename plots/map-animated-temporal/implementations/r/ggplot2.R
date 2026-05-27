#' anyplot.ai
#' map-animated-temporal: Animated Map over Time
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-05-27

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data -------------------------------------------------------------------
# Earthquake aftershock sequence - Tohoku region, Japan
# Temporal decay follows Omori law: N(t) ~ 1 / (t + c)^p
n_days  <- 9
lat_epi <- 38.3
lon_epi <- 142.4
events_per_day <- pmax(round(55 / (1:n_days + 0.3)^0.8), 4)

quakes <- do.call(rbind, lapply(seq_len(n_days), function(d) {
  n  <- events_per_day[d]
  sp <- 0.45 + 0.07 * d  # spatial spread grows as fault zone relaxes
  data.frame(
    day       = d,
    lat       = lat_epi + rnorm(n, 0, sp),
    lon       = lon_epi + rnorm(n, 0, sp * 1.2),
    magnitude = pmin(2.5 + rexp(n, rate = 1.4), 7.5)
  )
}))
quakes$day_label <- factor(
  paste0("Day ", quakes$day),
  levels = paste0("Day ", seq_len(n_days))
)

# Epicenter reference point
epicenter <- data.frame(lat = lat_epi, lon = lon_epi)

# Event counts per panel for strip labels
day_counts <- as.integer(table(quakes$day))
day_labels_full <- paste0("Day ", seq_len(n_days), " (n=", day_counts, ")")
levels(quakes$day_label) <- day_labels_full

# --- Plot -------------------------------------------------------------------
title_text <- "map-animated-temporal · r · ggplot2 · anyplot.ai"

p <- ggplot(quakes, aes(x = lon, y = lat)) +
  geom_point(
    aes(size = magnitude, color = magnitude),
    alpha = 0.75, stroke = 0
  ) +
  geom_point(
    data = epicenter,
    aes(x = lon, y = lat),
    shape = 3, size = 2.5, color = INK, stroke = 0.8
  ) +
  scale_color_gradient(
    low = "#009E73", high = "#4467A3",
    name = "Mag", limits = c(2.5, 7.5)
  ) +
  scale_size_continuous(range = c(0.5, 3.2), guide = "none") +
  scale_x_continuous(
    limits = c(139.5, 145.5),
    breaks = c(140, 142, 144),
    labels = c("140°E", "142°E", "144°E")
  ) +
  scale_y_continuous(
    limits = c(35.5, 41.5),
    breaks = c(36, 38, 40),
    labels = c("36°N", "38°N", "40°N")
  ) +
  facet_wrap(~ day_label, nrow = 3) +
  labs(
    title = title_text,
    x = "Longitude", y = "Latitude"
  ) +
  theme_minimal(base_size = 7) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,    color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,    color = NA),
    panel.grid.major  = element_line(color = INK_SOFT,  linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT,  fill = NA, linewidth = 0.25),
    axis.title        = element_text(color = INK,       size = 9),
    axis.text         = element_text(color = INK_SOFT,  size = 5),
    axis.text.x       = element_text(angle = 45,        hjust = 1),
    plot.title        = element_text(color = INK,       size = 12, hjust = 0.5,
                                     margin = margin(b = 6)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                     linewidth = 0.25),
    legend.text       = element_text(color = INK_SOFT,  size = 7),
    legend.title      = element_text(color = INK,       size = 9),
    legend.key.height = unit(0.5, "cm"),
    strip.background  = element_rect(fill = ELEVATED_BG, color = NA),
    strip.text        = element_text(color = INK,       size = 6.5, face = "bold"),
    plot.margin       = margin(8, 8, 8, 8)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8, height = 4.5,
  units    = "in", dpi = 400
)
