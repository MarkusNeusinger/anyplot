#' anyplot.ai
#' pie-basic: Basic Pie Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-28

library(ggplot2)
library(dplyr)
library(ragg)

THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

ANYPLOT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Annual budget allocation by department (millions USD)
budget <- tibble::tibble(
  department = c("R&D", "Marketing", "Operations", "Sales", "HR", "IT"),
  amount     = c(32, 22, 18, 14, 10, 4)
)

budget <- budget |>
  arrange(desc(amount)) |>
  mutate(
    department = factor(department, levels = department),
    pct        = amount / sum(amount) * 100,
    label      = if_else(pct >= 5, sprintf("%.0f%%", pct), "")
  )

# Pre-compute cumulative y positions (coord_polar stacks last-level-first).
budget <- budget |>
  mutate(
    ymax = rev(cumsum(rev(amount))),
    ymin = ymax - amount,
    ymid = (ymin + ymax) / 2
  )

# Explode largest slice (R&D 32%) outward by shifting its x range.
# Using geom_rect with explicit xmin/xmax avoids position_stack limitations.
EXPLODE_OFFSET <- 0.12
budget <- budget |>
  mutate(
    xmin = if_else(department == "R&D", 0.5 + EXPLODE_OFFSET, 0.5),
    xmax = if_else(department == "R&D", 1.5 + EXPLODE_OFFSET, 1.5),
    xmid = (xmin + xmax) / 2
  )

palette_named <- setNames(
  ANYPLOT_PALETTE[seq_len(nrow(budget))],
  levels(budget$department)
)

p <- ggplot(budget) +
  geom_rect(
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax, fill = department),
    color     = PAGE_BG,
    linewidth = 0.8
  ) +
  geom_text(
    aes(x = xmid, y = ymid, label = label),
    color    = "#FAF8F1",
    size     = 3.8,
    fontface = "bold"
  ) +
  scale_x_continuous(limits = c(0.5, 1.65), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 100), expand = c(0, 0)) +
  coord_polar(theta = "y", start = 0) +
  scale_fill_manual(values = palette_named) +
  labs(
    title = "pie-basic · r · ggplot2 · anyplot.ai",
    fill  = "Department"
  ) +
  theme_void() +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    plot.title          = element_text(
      color  = INK,
      size   = 12,
      hjust  = 0.5,
      face   = "bold",
      margin = margin(b = 10, t = 10)
    ),
    plot.title.position = "plot",
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title        = element_text(color = INK, size = 10),
    legend.background   = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.5),
    legend.key.size     = unit(0.5, "cm"),
    legend.margin       = margin(6, 6, 6, 6),
    plot.margin         = margin(30, 40, 30, 40)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
