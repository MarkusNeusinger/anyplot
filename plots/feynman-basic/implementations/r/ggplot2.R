#' anyplot.ai
#' feynman-basic: Feynman Diagram for Particle Interactions
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-06-03

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette — pos 1 for fermions, pos 3 (blue) for photons (semantic: EM radiation)
COL_FERMION <- "#009E73"  # Imprint pos 1 — fermion lines (e-)
COL_PHOTON  <- "#4467A3"  # Imprint pos 3 — photon lines (gamma), blue for EM radiation

# --- Helper: wavy photon line -----------------------------------------------
wavy_line <- function(x0, y0, x1, y1, n_waves = 3, amplitude = 0.35, n_pts = 300) {
  t   <- seq(0, 1, length.out = n_pts)
  dx  <- x1 - x0
  dy  <- y1 - y0
  len <- sqrt(dx^2 + dy^2)
  px  <- -dy / len  # unit perpendicular vector
  py  <-  dx / len
  wave <- amplitude * sin(n_waves * 2 * pi * t)
  tibble(
    x = x0 + t * dx + wave * px,
    y = y0 + t * dy + wave * py
  )
}

# --- Diagram: Compton Scattering (e- gamma -> e- gamma) --------------------
# Coordinate space: x in [0, 16], y in [0, 9] — matches 3200x1800 px aspect ratio
V1 <- c(5.0, 4.5)   # first vertex (photon absorbed by electron)
V2 <- c(11.0, 4.5)  # second vertex (new photon emitted by electron)

# Fermion (e-) segments: incoming, internal propagator, outgoing
fermion_segs <- tibble(
  x    = c(0.5,   V1[1], V2[1]),
  y    = c(7.0,   V1[2], V2[2]),
  xend = c(V1[1], V2[1], 15.5),
  yend = c(V1[2], V2[2], 7.0)
)

# Photon (gamma) wavy paths
photons <- bind_rows(
  wavy_line(0.5, 2.0, V1[1], V1[2], n_waves = 3) |> mutate(group = "photon_in"),
  wavy_line(V2[1], V2[2], 15.5, 2.0, n_waves = 3) |> mutate(group = "photon_out")
)

# Interaction vertices
vertices <- tibble(x = c(V1[1], V2[1]), y = c(V1[2], V2[2]))

# Particle labels at line endpoints and on internal propagator
labels_df <- tibble(
  x     = c(0.3,  0.3,  15.7, 15.7, 8.0),
  y     = c(7.4,  1.6,  7.4,  1.6,  5.2),
  label = c("e⁻", "γ", "e⁻", "γ", "e⁻"),
  hjust = c(1.0,  1.0,  0.0,  0.0,  0.5),
  col   = c(COL_FERMION, COL_PHOTON, COL_FERMION, COL_PHOTON, COL_FERMION)
)

# --- Title (length 39 chars < 67, no scaling needed) -----------------------
plot_title    <- "feynman-basic · r · ggplot2 · anyplot.ai"
plot_subtitle <- "Compton Scattering  —  e⁻γ → e⁻γ"

# --- Build plot -------------------------------------------------------------
p <- ggplot() +
  # Photon wavy lines
  geom_path(
    data      = photons,
    aes(x = x, y = y, group = group),
    color     = COL_PHOTON,
    linewidth = 1.1
  ) +
  # Fermion straight lines with directional arrows
  geom_segment(
    data      = fermion_segs,
    aes(x = x, y = y, xend = xend, yend = yend),
    color     = COL_FERMION,
    linewidth = 1.1,
    arrow     = arrow(length = unit(0.22, "cm"), type = "closed", ends = "last")
  ) +
  # Interaction vertex dots
  geom_point(
    data  = vertices,
    aes(x = x, y = y),
    color = INK,
    size  = 4.0,
    shape = 16
  ) +
  # Particle type labels (color mapped via scale_color_identity)
  geom_text(
    data     = labels_df,
    aes(x = x, y = y, label = label, hjust = hjust, color = col),
    size     = 5.5,
    fontface = "italic"
  ) +
  scale_color_identity() +
  # Time direction marker at bottom
  annotate("segment",
           x = 5.5, xend = 10.5, y = 0.4, yend = 0.4,
           color     = INK_MUTED,
           linewidth = 0.7,
           arrow     = arrow(length = unit(0.15, "cm"), type = "open")) +
  annotate("text",
           x     = 8.0,
           y     = 0.05,
           label = "time",
           color = INK_MUTED,
           size  = 3.5,
           hjust = 0.5) +
  coord_cartesian(xlim = c(-0.5, 16.5), ylim = c(-0.3, 9.3)) +
  labs(
    title    = plot_title,
    subtitle = plot_subtitle
  ) +
  theme_void() +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    plot.title      = element_text(color = INK,      size = 12, hjust = 0.5,
                                   margin = margin(t = 15, b = 5)),
    plot.subtitle   = element_text(color = INK_SOFT, size = 9,  hjust = 0.5,
                                   margin = margin(b = 10)),
    plot.margin     = margin(t = 10, r = 30, b = 20, l = 30)
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
