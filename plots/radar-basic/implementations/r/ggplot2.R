#' anyplot.ai
#' radar-basic: Basic Radar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-07-24
library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# coord_polar() curves straight edges into arcs; radar polygons need straight
# lines between vertices, so force linear interpolation via a custom coord.
coord_radar <- function(theta = "x", start = 0, direction = 1) {
  theta <- match.arg(theta, c("x", "y"))
  r <- if (theta == "x") "y" else "x"
  ggproto("CoordRadar", CoordPolar,
    theta = theta, r = r, start = start,
    direction = sign(direction),
    is_linear = function(coord) TRUE
  )
}

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- scales::alpha(INK, 0.15)

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data -----------------------------------------------------------------
competencies <- c("Communication", "Technical Skills", "Teamwork",
                   "Leadership", "Problem Solving", "Adaptability")
n_axes <- length(competencies)

reviews <- tibble::tibble(
  competency = rep(competencies, 2),
  employee   = factor(rep(c("Alice Chen", "Marcus Webb"), each = n_axes),
                       levels = c("Alice Chen", "Marcus Webb")),
  score      = c(85, 70, 90, 60, 80, 75,
                 60, 88, 68, 92, 74, 82)
) %>%
  mutate(axis_pos = rep(seq_len(n_axes), 2))

# Duplicate each series' first point at n_axes + 1 to close the polygon
closing_points <- reviews %>%
  filter(axis_pos == 1) %>%
  mutate(axis_pos = n_axes + 1)

radar_df <- bind_rows(reviews, closing_points)

# --- Plot -------------------------------------------------------------------
p <- ggplot(radar_df, aes(x = axis_pos, y = score, group = employee)) +
  geom_polygon(aes(fill = employee), color = NA, alpha = 0.25) +
  geom_line(aes(color = employee), linewidth = 1.1) +
  geom_point(aes(color = employee), size = 2.8) +
  coord_radar(theta = "x", start = 0) +
  scale_x_continuous(breaks = seq_len(n_axes), labels = competencies,
                      limits = c(1, n_axes + 1), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20),
                      expand = c(0, 0)) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:2], name = NULL) +
  scale_color_manual(values = IMPRINT_PALETTE[1:2], name = NULL) +
  labs(title = "radar-basic · r · ggplot2 · anyplot.ai") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.4),
    panel.grid.minor  = element_blank(),
    axis.title        = element_blank(),
    axis.text.x       = element_text(color = INK, size = 11),
    axis.text.y       = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, hjust = 0.5),
    legend.position    = "bottom",
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 9),
    legend.title       = element_blank()
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
