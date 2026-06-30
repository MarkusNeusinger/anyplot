#' anyplot.ai
#' area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-06-30

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Panorama-specific colors (not from categorical palette — atmospheric tones)
SKY_COLOR     <- if (THEME == "light") "#C8DCEC" else "#0B1828"
MOUNTAIN_FILL <- if (THEME == "light") "#2C2A28" else "#0D0C0A"
MOUNTAIN_FG   <- if (THEME == "light") "#1E1C1A" else "#080808"
RIDGE_COLOR   <- if (THEME == "light") "#4A4540" else "#2E2C2A"

# Peak data: Wallis panorama — 10 summits in a west-to-east sweep
peaks_df <- data.frame(
  name      = c("Weisshorn", "Dent Blanche", "Matterhorn", "Breithorn",
                "Liskamm", "Dufourspitze", "Strahlhorn", "Allalinhorn",
                "Alphubel", "Dom"),
  angle_deg = c(  8,  28,  47,  63,  76,  90,  98, 105, 112, 118),
  elev_m    = c(4506, 4358, 4478, 4164, 4527, 4634, 4190, 4027, 4206, 4545),
  stringsAsFactors = FALSE
)

# Label stagger heights — SPECIAL for focal peaks, alternating HIGH/LOW for rest
peaks_df$label_y <- c(
  5300,  # Weisshorn     HIGH
  5050,  # Dent Blanche  LOW
  5500,  # Matterhorn    SPECIAL (focal)
  5050,  # Breithorn     LOW
  5300,  # Liskamm       HIGH
  5500,  # Dufourspitze  SPECIAL (highest)
  5050,  # Strahlhorn    LOW
  5300,  # Allalinhorn   HIGH
  5050,  # Alphubel      LOW
  5300   # Dom           HIGH
)

# Derived label positions (elevation text above leader endpoint; name above elevation)
peaks_df$seg_y1 <- peaks_df$label_y
peaks_df$elev_y <- peaks_df$label_y + 30
peaks_df$name_y <- peaks_df$label_y + 30 + 80 + 30

# Skyline: sum of tent functions (asymmetric flanks) + smoothed noise
BASE_ELEV <- 2750
angles    <- seq(0, 124, by = 0.08)
n_pts     <- length(angles)

slp_left  <- c(290, 245, 370, 205, 295, 340, 230, 215, 245, 315)
slp_right <- c(215, 290, 260, 255, 245, 265, 250, 230, 220, 270)

skyline <- rep(BASE_ELEV, n_pts)
for (i in seq_len(nrow(peaks_df))) {
  pa   <- peaks_df$angle_deg[i]
  pe   <- peaks_df$elev_m[i]
  tent <- ifelse(angles <= pa,
                 pe - slp_left[i]  * (pa - angles),
                 pe - slp_right[i] * (angles - pa))
  skyline <- pmax(skyline, pmax(tent, BASE_ELEV))
}

# Ridge jaggedness: smoothed noise + micro-roughness
noise_sm <- as.numeric(stats::filter(rnorm(n_pts, 0, 28), rep(1 / 7, 7), sides = 2))
noise_sm[is.na(noise_sm)] <- 0
skyline <- skyline + noise_sm + rnorm(n_pts, 0, 9)

# Re-anchor named summits to exact elevations
for (i in seq_len(nrow(peaks_df))) {
  skyline[which.min(abs(angles - peaks_df$angle_deg[i]))] <- peaks_df$elev_m[i]
}

panorama_df <- data.frame(angle = angles, elev = skyline)

# Foreground ridge: closer terrain adding visual depth
fg_ridge <- BASE_ELEV + 80 +
  35 * sin(angles * 0.14 + 0.4) +
  18 * cos(angles * 0.07) +
  rnorm(n_pts, 0, 10)
fg_df <- data.frame(angle = angles, ridge = fg_ridge)

# Title — 67 chars → ratio = 1.0 → title_size = 12
title_str  <- "Wallis Panorama · area-mountain-panorama · r · ggplot2 · anyplot.ai"
title_n    <- nchar(title_str)
title_size <- max(8, round(12 * 67 / title_n))

p <- ggplot() +
  # Main mountain silhouette
  geom_ribbon(
    data  = panorama_df,
    aes(x = angle, ymin = BASE_ELEV, ymax = elev),
    fill  = MOUNTAIN_FILL,
    color = NA
  ) +
  # Foreground ridge (depth layer)
  geom_ribbon(
    data  = fg_df,
    aes(x = angle, ymin = BASE_ELEV, ymax = ridge),
    fill  = MOUNTAIN_FG,
    color = NA
  ) +
  # Ridgeline edge
  geom_line(
    data      = panorama_df,
    aes(x = angle, y = elev),
    color     = RIDGE_COLOR,
    linewidth = 0.35
  ) +
  # Leader lines: summit tip → label base
  geom_segment(
    data = peaks_df,
    aes(x = angle_deg, xend = angle_deg, y = elev_m + 20, yend = seg_y1),
    color     = INK_MUTED,
    linewidth = 0.4
  ) +
  # Elevation labels
  geom_text(
    data     = peaks_df,
    aes(x = angle_deg, y = elev_y, label = paste0(elev_m, " m")),
    color    = INK_SOFT,
    size     = 2.4,
    hjust    = 0.5,
    vjust    = 0
  ) +
  # Peak names (bold, above elevation)
  geom_text(
    data     = peaks_df,
    aes(x = angle_deg, y = name_y, label = name),
    color    = INK,
    size     = 3.0,
    hjust    = 0.5,
    vjust    = 0,
    fontface = "bold"
  ) +
  scale_x_continuous(limits = c(0, 124), expand = expansion(0)) +
  scale_y_continuous(
    limits = c(BASE_ELEV, 5850),
    breaks = c(3000, 3500, 4000, 4500, 5000),
    labels = function(x) paste0(x, " m"),
    expand = expansion(0)
  ) +
  labs(title = title_str, x = NULL, y = "Elevation") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG,   color = PAGE_BG),
    panel.background   = element_rect(fill = SKY_COLOR, color = NA),
    panel.grid.major.y = element_line(color = INK_MUTED, linewidth = 0.15,
                                      linetype = "dashed"),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.border       = element_blank(),
    axis.title.x       = element_blank(),
    axis.text.x        = element_blank(),
    axis.ticks.x       = element_blank(),
    axis.title.y       = element_text(color = INK_SOFT, size = 9),
    axis.text.y        = element_text(color = INK_SOFT, size = 8),
    axis.ticks.y       = element_blank(),
    plot.title         = element_text(color = INK, size = title_size,
                                      face = "bold",
                                      margin = margin(b = 8)),
    plot.margin        = margin(16, 16, 12, 16, unit = "pt")
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
