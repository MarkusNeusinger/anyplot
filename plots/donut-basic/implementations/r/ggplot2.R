#' anyplot.ai
#' donut-basic: Basic Donut Chart
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-25

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
  "#009E73",  # 1 — brand green
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD"   # 6 — cyan
)

# Data — annual budget allocation by department (millions USD)
departments <- c("Technology", "Operations", "Marketing", "Finance", "HR", "R&D")
budgets     <- c(2.8, 2.2, 1.9, 1.3, 1.1, 0.7)

df <- data.frame(
  category = factor(departments, levels = departments),
  value    = budgets
) |>
  mutate(
    pct   = value / sum(value),
    label = paste0(sprintf("%.0f", pct * 100), "%")
  )

# geom_col stacks in reverse factor level order (last level first at y=0).
# Compute midpoints in the same reverse order so labels land in their segments.
df_label <- df |>
  arrange(desc(as.integer(category))) |>
  mutate(
    ymax = cumsum(pct),
    ymin = lag(ymax, default = 0),
    ymid = (ymax + ymin) / 2
  )

total_label <- paste0("$", sprintf("%.1f", sum(budgets)), "M\nTotal Budget")

# Plot
p <- ggplot(df) +
  geom_col(
    aes(x = 2, y = pct, fill = category),
    width     = 1,
    color     = PAGE_BG,
    linewidth = 0.6
  ) +
  geom_text(
    data     = df_label,
    aes(x = 2, y = ymid, label = label),
    color    = "#FFFFFF",
    size     = 3.5,
    fontface = "bold"
  ) +
  annotate(
    "text",
    x          = 0,
    y          = 0,
    label      = total_label,
    color      = INK,
    size       = 5,
    fontface   = "bold",
    hjust      = 0.5,
    vjust      = 0.5,
    lineheight = 1.3
  ) +
  coord_polar(theta = "y", start = 0) +
  scale_x_continuous(limits = c(-0.5, 2.5), expand = c(0, 0)) +
  scale_fill_manual(
    values = setNames(IMPRINT_PALETTE, departments)
  ) +
  labs(
    title = "donut-basic · r · ggplot2 · anyplot.ai",
    fill  = "Department"
  ) +
  theme_void() +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(
      color  = INK,
      size   = 12,
      hjust  = 0.5,
      margin = margin(b = 10)
    ),
    legend.position   = "right",
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.key.size   = unit(14, "pt"),
    plot.margin       = margin(20, 20, 20, 20)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
