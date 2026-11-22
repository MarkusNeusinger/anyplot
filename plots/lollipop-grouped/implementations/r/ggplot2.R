#' anyplot.ai
#' lollipop-grouped: Grouped Lollipop Chart
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")  # Imprint palette

# Columns: set these to your table's column names
REGION  <- "Region"               # role: category
PRODUCT <- "Product"              # role: group
REVENUE <- "Revenue ($ millions)" # role: value

# Data: replace this block with your own table, for example df <- read.csv("sales.csv", check.names = FALSE)
set.seed(42)
df <- tibble::tibble(
  !!REGION  := rep(c("North", "South", "East", "West"), each = 3),
  !!PRODUCT := rep(c("Product A", "Product B", "Product C"), times = 4),
  !!REVENUE := c(2.8, 2.2, 1.9,
                 3.2, 2.7, 2.4,
                 2.6, 2.0, 1.7,
                 3.0, 2.4, 2.1)
)

# Plot: reads only df and the constants above
# Regions sorted by total revenue (descending); products keep their data order
region_order <- df |>
  group_by(.data[[REGION]]) |>
  summarise(total = sum(.data[[REVENUE]]), .groups = "drop") |>
  arrange(desc(total)) |>
  pull(1)
df[[REGION]]  <- factor(df[[REGION]], levels = region_order)
df[[PRODUCT]] <- factor(df[[PRODUCT]], levels = unique(df[[PRODUCT]]))

dodge <- position_dodge(width = 0.6)

p <- ggplot(df, aes(x = .data[[REGION]], y = .data[[REVENUE]], color = .data[[PRODUCT]])) +
  geom_linerange(
    aes(ymin = 0, ymax = .data[[REVENUE]]),
    position = dodge,
    linewidth = 0.9
  ) +
  geom_point(position = dodge, size = 5.5) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(limits = c(0, max(df[[REVENUE]], na.rm = TRUE) * 1.1),
                     expand = expansion(mult = c(0, 0.02))) +
  labs(
    title = "lollipop-grouped · r · ggplot2 · anyplot.ai",
    x = REGION,
    y = REVENUE,
    color = PRODUCT
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.2),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12),
    legend.background  = element_rect(fill = PAGE_BG, color = NA),
    legend.key         = element_rect(fill = PAGE_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.position    = "right"
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
