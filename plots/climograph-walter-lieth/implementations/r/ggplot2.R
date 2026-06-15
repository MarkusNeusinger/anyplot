#' anyplot.ai
#' climograph-walter-lieth: Walter-Lieth Climate Diagram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 83/100 | Created: 2026-06-15

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint categorical palette (hybrid-v3 sort order)
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first categorical series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Domain-convention colors (semantic exception: temperature→red, precipitation→blue/water)
COLOR_TEMP   <- IMPRINT_PALETTE[5]           # #AE3030 — temperature (hot/warm semantic)
COLOR_PRECIP <- IMPRINT_PALETTE[3]           # #4467A3 — precipitation (water semantic)
COLOR_FROST  <- IMPRINT_PALETTE[6]           # #2ABCCD — frost period (cold/ice semantic)
GRID_COLOR   <- adjustcolor(INK, alpha.f = 0.12)

# Station metadata — Ankara, Turkey (continental climate with summer arid period)
station_elev        <- 891
annual_mean_temp    <- 11.8
annual_precip_total <- 352

# Monthly climate normals (1991-2020 reference period)
climate_df <- data.frame(
  month_idx = 1:12,
  month_lbl = c("J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"),
  temp      = c(-0.5,  1.0,  6.0, 11.5, 16.5, 20.0, 23.5, 23.5, 18.5, 12.5,  6.0,  2.0),
  precip    = c( 38.0, 31.0, 29.0, 33.0, 43.0, 34.0, 16.0, 12.0, 17.0, 27.0, 31.0, 41.0)
)

# Walter-Lieth 1:2 scaling convention: 10°C aligns with 20 mm on the shared axis
climate_df$prec_scaled <- climate_df$precip / 2

# Smooth interpolation between months for continuous fill ribbons
n_interp <- 600
x_smooth <- seq(1, 12, length.out = n_interp)
t_smooth <- approx(climate_df$month_idx, climate_df$temp,        x_smooth)$y
p_smooth <- approx(climate_df$month_idx, climate_df$prec_scaled, x_smooth)$y
p_smooth <- pmin(p_smooth, 50)  # cap at 100 mm / 2 = 50 (standard WL scale maximum)

# Ribbon endpoints: pmax/pmin approach naturally zeroes ribbon area at curve crossings
fill_df <- data.frame(
  x          = x_smooth,
  temp       = t_smooth,
  prec_s     = p_smooth,
  humid_ymax = pmax(t_smooth, p_smooth),  # top of humid band (= prec_s where prec_s > temp)
  arid_ymin  = pmin(t_smooth, p_smooth)   # bottom of arid band (= prec_s where temp > prec_s)
)

# Frost-month rectangles (mean temperature below 0°C)
frost_months <- climate_df$month_idx[climate_df$temp < 0]
frost_df <- if (length(frost_months) > 0) {
  data.frame(
    xmin = frost_months - 0.45,
    xmax = frost_months + 0.45
  )
} else {
  NULL
}

# Plot title — mandatory anyplot format with descriptive station prefix
plot_title <- paste0(
  "Ankara, Turkey · climograph-walter-lieth · r · ggplot2 · anyplot.ai"
)
title_fontsize <- max(8L, round(12L * min(1.0, 67 / nchar(plot_title))))

# Subtitle carries the station header (Walter-Lieth convention)
plot_subtitle <- sprintf(
  "%d m a.s.l.  ·  T = %.1f°C  ·  ΣP = %d mm",
  station_elev, annual_mean_temp, as.integer(annual_precip_total)
)

# Build plot
p <- ggplot() +
  # Humid fill (blue) — where precipitation curve exceeds temperature curve
  geom_ribbon(
    data = fill_df,
    aes(x = x, ymin = temp, ymax = humid_ymax),
    fill = COLOR_PRECIP, alpha = 0.30, inherit.aes = FALSE
  ) +
  # Arid fill (red) — where temperature curve exceeds precipitation curve
  geom_ribbon(
    data = fill_df,
    aes(x = x, ymin = arid_ymin, ymax = temp),
    fill = COLOR_TEMP, alpha = 0.30, inherit.aes = FALSE
  ) +
  # Frost-month indicator bands below 0°C
  (if (!is.null(frost_df))
    geom_rect(
      data = frost_df,
      aes(xmin = xmin, xmax = xmax),
      ymin = -5, ymax = 0,
      fill = COLOR_FROST, alpha = 0.40, inherit.aes = FALSE
    )
  else NULL) +
  # Frost threshold reference line
  geom_hline(yintercept = 0, color = INK_SOFT, linewidth = 0.4, linetype = "dashed") +
  # Precipitation curve (plotted at precip/2 on temp axis; right axis shows actual mm)
  geom_line(
    data = climate_df,
    aes(x = month_idx, y = prec_scaled),
    color = COLOR_PRECIP, linewidth = 1.3, lineend = "round"
  ) +
  # Temperature curve
  geom_line(
    data = climate_df,
    aes(x = month_idx, y = temp),
    color = COLOR_TEMP, linewidth = 1.3, lineend = "round"
  ) +
  # X axis: month abbreviations
  scale_x_continuous(
    breaks = 1:12,
    labels = c("J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"),
    expand = c(0.025, 0)
  ) +
  # Dual y-axis: left = temperature (°C), right = precipitation (mm) at 2× scale
  scale_y_continuous(
    name   = "Temperature (°C)",
    limits = c(-5, 30),
    breaks = c(0, 10, 20, 30),
    sec.axis = sec_axis(
      ~ . * 2,
      name   = "Precipitation (mm)",
      breaks = c(0, 20, 40, 60),
      labels = c("0", "20", "40", "60")
    )
  ) +
  labs(
    title    = plot_title,
    subtitle = plot_subtitle,
    x        = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = GRID_COLOR, linewidth = 0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.border       = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.5),
    axis.title.y.left  = element_text(color = COLOR_TEMP,   size = 10),
    axis.title.y.right = element_text(color = COLOR_PRECIP, size = 10),
    axis.text.y.left   = element_text(color = INK_SOFT, size = 8),
    axis.text.y.right  = element_text(color = INK_SOFT, size = 8),
    axis.text.x        = element_text(color = INK_SOFT, size = 8),
    axis.line          = element_blank(),
    plot.title         = element_text(color = INK, size = title_fontsize, face = "bold"),
    plot.subtitle      = element_text(color = INK_SOFT, size = 9,
                                      margin = margin(t = 2, b = 6)),
    plot.margin        = margin(12, 16, 10, 12, "pt")
  )

# Save (landscape: 8 × 4.5 in @ 400 dpi → 3200 × 1800 px)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
