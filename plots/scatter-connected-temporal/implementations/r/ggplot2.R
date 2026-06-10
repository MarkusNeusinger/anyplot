#' anyplot.ai
#' scatter-connected-temporal: Connected Scatter Plot with Temporal Path
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-06-09

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
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

# Data: unemployment vs inflation (Phillips curve dynamics), 1980-2019
years        <- 1980:2019
unemployment <- c(
  7.2, 7.6, 9.7, 9.6, 7.5, 7.2, 7.0, 6.2, 5.5, 5.3,
  5.6, 6.8, 7.5, 6.9, 6.1, 5.6, 5.4, 4.9, 4.5, 4.2,
  4.0, 4.7, 5.8, 6.0, 5.5, 5.1, 4.6, 4.6, 5.8, 9.3,
  9.6, 8.9, 8.1, 7.4, 6.2, 5.3, 4.9, 4.4, 3.9, 3.5
)
inflation <- c(
  13.5, 10.3, 6.2, 3.2, 4.3, 3.6, 1.9, 3.6, 4.1, 4.8,
   5.4,  4.2, 3.0, 3.0, 2.6, 2.8, 2.9, 2.3, 1.6, 2.2,
   3.4,  2.8, 1.6, 2.3, 2.7, 3.4, 3.2, 2.9, 3.8, -0.4,
   1.6,  3.2, 2.1, 1.5, 1.6, 0.1, 1.3, 2.1, 2.4,  2.3
)

df <- data.frame(
  year         = years,
  unemployment = unemployment,
  inflation    = inflation
)

key_years <- c(1980, 1990, 2000, 2010, 2019)
df_labels <- df[df$year %in% key_years, ]

# Per-label positions to avoid crowding (2000 nudged left, 2019 nudged higher)
df_labels$lbl_x <- df_labels$unemployment + c( 0.2,  0.2, -0.3,  0.2,  0.2)
df_labels$lbl_y <- df_labels$inflation    + c( 0.6,  0.5,  0.5,  0.5,  0.7)

# Arrow segment: from start point toward first step for temporal direction cue
arrow_start <- df[df$year == 1980, ]
arrow_end   <- df[df$year == 1981, ]

# Title: scale fontsize for long title (80 chars -> size 10)
plot_title <- "Phillips Curve Dynamics · scatter-connected-temporal · r · ggplot2 · anyplot.ai"
title_size <- max(8L, round(12 * 67 / nchar(plot_title)))

# Plot
p <- ggplot(df, aes(x = unemployment, y = inflation)) +
  geom_path(
    aes(color = year),
    linewidth = 1.0,
    alpha     = 0.85,
    lineend   = "round",
    linejoin  = "round"
  ) +
  # Start-of-path arrow to reinforce temporal direction
  geom_segment(
    data   = data.frame(
      x    = arrow_start$unemployment,
      y    = arrow_start$inflation,
      xend = arrow_end$unemployment,
      yend = arrow_end$inflation
    ),
    aes(x = x, y = y, xend = xend, yend = yend),
    color     = IMPRINT_PALETTE[1],
    linewidth = 1.2,
    arrow     = arrow(length = unit(0.18, "cm"), type = "closed")
  ) +
  geom_point(
    aes(color = year),
    size  = 3.5,
    alpha = 0.95
  ) +
  geom_text(
    data     = df_labels,
    aes(x = lbl_x, y = lbl_y, label = year),
    color    = INK,
    size     = 3.2,
    fontface = "bold"
  ) +
  scale_color_gradient(
    low   = IMPRINT_PALETTE[1],
    high  = IMPRINT_PALETTE[3],
    name  = "Year",
    guide = guide_colorbar(
      barwidth       = 8,
      barheight      = 0.5,
      title.position = "top",
      title.hjust    = 0.5
    )
  ) +
  scale_x_continuous(
    labels = label_number(suffix = "%"),
    expand = expansion(mult = c(0.05, 0.08))
  ) +
  scale_y_continuous(
    labels = label_number(suffix = "%"),
    expand = expansion(mult = c(0.05, 0.15))
  ) +
  labs(
    x     = "Unemployment Rate",
    y     = "Inflation Rate",
    title = plot_title
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major  = element_line(color = INK_MUTED,  linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT,   linewidth = 0.4),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = title_size, face = "bold"),
    legend.position   = "bottom",
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 9),
    plot.margin       = margin(20, 20, 10, 20)
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
