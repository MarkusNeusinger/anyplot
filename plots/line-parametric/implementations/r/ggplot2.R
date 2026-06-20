#' anyplot.ai
#' line-parametric: Parametric Curve Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-06-20

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Data
n <- 1200

# Lissajous figure: x = sin(3t), y = sin(2t) for t in [0, 2pi]
t_liss  <- seq(0, 2 * pi, length.out = n)
df_liss <- data.frame(
  t_norm = (t_liss - min(t_liss)) / diff(range(t_liss)),
  x      = sin(3 * t_liss),
  y      = sin(2 * t_liss),
  curve  = "Lissajous (3:2)"
)

# Archimedean spiral: x = t*cos(t), y = t*sin(t) for t in [0, 4pi]
t_sprl  <- seq(0, 4 * pi, length.out = n)
df_sprl <- data.frame(
  t_norm = (t_sprl - min(t_sprl)) / diff(range(t_sprl)),
  x      = t_sprl * cos(t_sprl),
  y      = t_sprl * sin(t_sprl),
  curve  = "Archimedean Spiral"
)

df <- rbind(df_liss, df_sprl)
df$curve <- factor(df$curve, levels = c("Lissajous (3:2)", "Archimedean Spiral"))

# Start and end markers per curve
start_pts <- df %>% group_by(curve) %>% slice(1)   %>% ungroup()
end_pts   <- df %>% group_by(curve) %>% slice(n()) %>% ungroup()

# Plot
p <- ggplot(df, aes(x = x, y = y, color = t_norm)) +
  geom_path(linewidth = 0.9) +
  geom_point(
    data = start_pts,
    aes(x = x, y = y),
    inherit.aes = FALSE,
    color = IMPRINT_PALETTE[1],
    size  = 3.5,
    shape = 19
  ) +
  geom_point(
    data = end_pts,
    aes(x = x, y = y),
    inherit.aes = FALSE,
    color = IMPRINT_PALETTE[3],
    size  = 3.5,
    shape = 15
  ) +
  scale_color_gradient(
    low  = "#009E73",
    high = "#4467A3",
    name = "t (0 to 1)"
  ) +
  facet_wrap(~curve, scales = "free") +
  labs(
    title   = "line-parametric · r · ggplot2 · anyplot.ai",
    x       = "x(t)",
    y       = "y(t)",
    caption = "● start (t = 0)    ■ end (t = max)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(
      color     = adjustcolor(INK, alpha.f = 0.12),
      linewidth = 0.3
    ),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    plot.title        = element_text(color = INK,      size = 12,
                                     margin = margin(b = 10)),
    plot.caption      = element_text(color = INK_SOFT, size = 8,
                                     hjust = 0, margin = margin(t = 8)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                      linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK,      size = 10),
    legend.key.width  = unit(1.2, "cm"),
    strip.text        = element_text(color = INK, size = 10, face = "bold",
                                     margin = margin(b = 6)),
    strip.background  = element_blank(),
    aspect.ratio      = 1
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
