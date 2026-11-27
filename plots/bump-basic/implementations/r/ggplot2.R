#' anyplot.ai
#' bump-basic: Basic Bump Chart
#' Library: ggplot2 | R
#' Quality: 89/100 | Created: 2026-05-29

library(ggplot2)
library(ragg)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- alpha(INK, 0.15)

# Imprint palette (canonical order)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
RACE   <- "Race round"             # role: period
DRIVER <- "Driver"                 # role: entity
RANK   <- "Championship position"  # role: rank

# Data: F1 championship standings over 8 rounds; replace with your own table
set.seed(42)
drivers <- c("Hamilton", "Verstappen", "Leclerc", "Norris", "Russell", "Perez")
df <- tibble::tibble(
  !!RACE   := rep(1:8, each = 6),
  !!DRIVER := factor(rep(drivers, times = 8), levels = drivers),
  !!RANK   := c(
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

# Plot: reads only df and the constants above
n_races    <- max(df[[RACE]])
n_ranks    <- max(df[[RANK]])
labels_end <- df[df[[RACE]] == n_races, ]

p <- ggplot(df, aes(x = .data[[RACE]], y = .data[[RANK]],
                    color = .data[[DRIVER]], group = .data[[DRIVER]])) +
  geom_line(linewidth = 1.4, lineend = "round", linejoin = "round") +
  geom_point(size = 3.5) +
  geom_text(
    data     = labels_end,
    aes(x = .data[[RACE]] + 0.3, label = .data[[DRIVER]]),
    hjust    = 0,
    size     = 4.2,
    fontface = "bold"
  ) +
  scale_y_reverse(
    breaks = seq_len(n_ranks),
    labels = \(r) paste0(r, c("st", "nd", "rd", rep("th", 7))[r]),
    expand = expansion(add = 0.4)
  ) +
  scale_x_continuous(
    breaks = seq_len(n_races),
    labels = \(b) paste0("R", b),
    expand = expansion(mult = c(0.03, 0.22))
  ) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  labs(
    title = "bump-basic · r · ggplot2 · anyplot.ai",
    x     = RACE,
    y     = RANK
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = GRID, linewidth = 0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.3),
    plot.title         = element_text(color = INK, size = 12, face = "bold"),
    legend.position    = "none",
    plot.margin        = margin(t = 18, r = 24, b = 18, l = 12, unit = "pt")
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
