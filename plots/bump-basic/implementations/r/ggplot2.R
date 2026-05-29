#' anyplot.ai
#' bump-basic: Basic Bump Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-05-29

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette (canonical order, hybrid-v3)
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 brand green
  "#C475FD",  # 2 lavender
  "#4467A3",  # 3 blue
  "#BD8233",  # 4 ochre
  "#AE3030",  # 5 matte red
  "#2ABCCD"   # 6 cyan
)

# Data: F1 Championship Standings — Rounds 1-8
drivers <- c("Hamilton", "Verstappen", "Leclerc", "Norris", "Russell", "Perez")

standings <- data.frame(
  race   = rep(1:8, each = 6),
  driver = factor(rep(drivers, times = 8), levels = drivers),
  rank   = c(
    2, 1, 3, 5, 4, 6,
    1, 2, 3, 5, 4, 6,
    1, 2, 4, 3, 5, 6,
    2, 1, 4, 3, 5, 6,
    2, 1, 3, 4, 5, 6,
    2, 1, 3, 4, 6, 5,
    1, 2, 3, 4, 6, 5,
    1, 2, 3, 5, 6, 4
  )
)

driver_colors       <- setNames(IMPRINT_PALETTE, drivers)
labels_end          <- standings[standings$race == 8, ]
labels_end$x_label  <- 8.35

# Plot
p <- ggplot(standings, aes(x = race, y = rank, color = driver, group = driver)) +
  geom_line(linewidth = 1.4, lineend = "round", linejoin = "round") +
  geom_point(size = 3.5) +
  geom_text(
    data     = labels_end,
    aes(x = x_label, label = driver),
    hjust    = 0,
    size     = 3.0,
    fontface = "bold"
  ) +
  scale_y_reverse(
    breaks = 1:6,
    labels = c("1st", "2nd", "3rd", "4th", "5th", "6th"),
    expand = expansion(add = 0.4)
  ) +
  scale_x_continuous(
    breaks = 1:8,
    labels = paste0("R", 1:8),
    expand = expansion(mult = c(0.03, 0.20))
  ) +
  scale_color_manual(values = driver_colors) +
  labs(
    title = "bump-basic · r · ggplot2 · anyplot.ai",
    x     = "Race Round",
    y     = "Championship Position"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.15),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.3),
    plot.title         = element_text(color = INK, size = 12, face = "bold"),
    legend.position    = "none",
    plot.margin        = margin(t = 12, r = 48, b = 12, l = 12, unit = "pt")
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
