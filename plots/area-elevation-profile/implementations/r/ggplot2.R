#' anyplot.ai
#' area-elevation-profile: Terrain Elevation Profile Along Transect
#' Library: ggplot2 3.5.1 | R 4.4.1

library(ggplot2)
library(scales)
library(ragg)
library(grid)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data -------------------------------------------------------------------
# Alpine traverse: 120 km transect, sampled every 250 m (481 points)
ctrl_km  <- c(0,    8,    18,   25,   30,   38,   45,   52,   60,   70,   78,   90,  105, 120)
ctrl_elv <- c(820, 1100, 1870, 2420, 2650, 2000, 2120, 1750, 2470, 2200, 2980, 1950, 1300, 1080)

sfn      <- splinefun(ctrl_km, ctrl_elv, method = "natural")
distance <- seq(0, 120, by = 0.25)
noise    <- cumsum(rnorm(length(distance), 0, 3)) * 0.25
elevation <- pmax(sfn(distance) + noise, 750)

trail <- data.frame(distance = distance, elevation = elevation)

# Valley floor for ribbon base — matches the actual data minimum
elev_floor <- min(elevation)

# Key landmarks — elevation matched to the noisy profile
lm_dist <- c(0, 18, 30, 45, 60, 78, 120)
lm_name <- c("Valley Start", "Fontaine Col", "Aiguille Peak",
             "Lac Hut", "Grand Col", "High Summit", "Valley End")
lm_elev <- approx(trail$distance, trail$elevation, xout = lm_dist)$y

landmarks <- data.frame(
  name      = lm_name,
  distance  = lm_dist,
  elevation = lm_elev,
  lbl_hjust = c(0, 0, 0, 0, 0, 0, 1),
  label     = paste0(lm_name, " (", round(lm_elev), "m)")
)

# --- Title / sizing ---------------------------------------------------------
TITLE      <- "area-elevation-profile · r · ggplot2 · anyplot.ai"
title_size <- max(round(12 * min(1, 67 / nchar(TITLE))), 8)

# --- Gradient terrain fill (ggplot2 >= 3.5.0) --------------------------------
# Gradient from muted deep green at valley floor to bright brand green at peaks
terrain_fill <- linearGradient(
  colours = c(scales::alpha("#006B4F", 0.40), scales::alpha("#009E73", 0.65)),
  y1 = unit(0, "npc"), y2 = unit(1, "npc")
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(trail, aes(x = distance)) +
  # Terrain silhouette — gradient fill from valley floor to profile
  geom_ribbon(
    aes(ymin = elev_floor, ymax = elevation),
    fill = terrain_fill, color = NA
  ) +
  # Profile line
  geom_line(
    aes(y = elevation),
    color = IMPRINT_PALETTE[1], linewidth = 1.0
  ) +
  # Landmark dashed verticals
  geom_vline(
    data = landmarks, aes(xintercept = distance),
    color = INK_SOFT, linewidth = 0.4, linetype = "dashed"
  ) +
  # Landmark dots (open circle, page-bg fill for definition)
  geom_point(
    data = landmarks, aes(x = distance, y = elevation),
    shape = 21, size = 2.5,
    color = IMPRINT_PALETTE[1], fill = PAGE_BG, stroke = 1.2
  ) +
  # Landmark labels with name and elevation at 45° angle
  geom_text(
    data = landmarks,
    aes(x = distance, y = elevation + 160, label = label, hjust = lbl_hjust),
    color = INK, size = 3.0, vjust = 0, angle = 45
  ) +
  labs(
    title    = TITLE,
    subtitle = "Alpine Traverse · 120 km · ~10× vertical exaggeration",
    x        = "Distance (km)",
    y        = "Elevation (m)"
  ) +
  scale_x_continuous(
    breaks = seq(0, 120, 20),
    expand = expansion(mult = c(0.02, 0.04))
  ) +
  scale_y_continuous(
    breaks = seq(800, 3200, 200),
    labels = scales::comma
  ) +
  coord_cartesian(ylim = c(elev_floor, 3500)) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.2),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.border       = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.line.y        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks.x       = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.ticks.y       = element_blank(),
    plot.title         = element_text(color = INK, size = title_size, hjust = 0.5),
    plot.subtitle      = element_text(color = INK_SOFT, size = 8, hjust = 0.5),
    plot.margin        = margin(20, 30, 15, 15, "pt")
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
