#' anyplot.ai
#' bar-grouped: Grouped Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-08-05

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# element_line() has no `alpha` argument, so bake a ~20% opacity into the hex
# itself (0x33 = 51/255) to get the style guide's "subtle" gridline.
GRID_COLOR  <- paste0(INK, "33")
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
REGION  <- "Region"        # role: category
PRODUCT <- "Product Line"  # role: group
REVENUE <- "Revenue ($M)"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("revenue.csv", check.names = FALSE)
set.seed(42)
grid <- expand.grid(region = c("North", "South", "East", "West", "Central"),
                    product = c("Software", "Hardware", "Services"),
                    stringsAsFactors = FALSE)
df <- tibble::tibble(
  !!REGION  := grid$region,
  !!PRODUCT := grid$product,
  !!REVENUE := case_when(
    grid$product == "Software" ~ round(rnorm(nrow(grid), mean = 5.8, sd = 0.9), 1),
    grid$product == "Hardware" ~ round(rnorm(nrow(grid), mean = 4.2, sd = 1.1), 1),
    TRUE                       ~ round(rnorm(nrow(grid), mean = 3.0, sd = 0.6), 1)
  )
)

# Plot: reads only df and the constants above
# Order regions by total revenue (descending) so the chart reads as a ranking;
# products keep the data's order.
region_order <- df %>%
  group_by(.data[[REGION]]) %>%
  summarise(total = sum(.data[[REVENUE]], na.rm = TRUE), .groups = "drop") %>%
  arrange(desc(total)) %>%
  pull(1)
df <- df %>%
  mutate(
    !!REGION  := factor(.data[[REGION]], levels = region_order),
    !!PRODUCT := factor(.data[[PRODUCT]], levels = unique(.data[[PRODUCT]]))
  )

p <- ggplot(df, aes(x = .data[[REGION]], y = .data[[REVENUE]], fill = .data[[PRODUCT]])) +
  geom_col(
    position = position_dodge(width = 0.75),
    width = 0.68,
    color = PAGE_BG,
    linewidth = 0.4
  ) +
  geom_text(
    aes(label = sprintf("%.1f", .data[[REVENUE]])),
    position = position_dodge(width = 0.75),
    vjust = -0.5,
    size = 2.4,
    color = INK_SOFT
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.14))) +
  labs(
    title = "Revenue by Product Line · bar-grouped · r · ggplot2 · anyplot.ai",
    x = REGION,
    y = REVENUE,
    fill = PRODUCT
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor.x  = element_blank(),
    panel.grid.minor.y  = element_blank(),
    panel.grid.major.y  = element_line(color = GRID_COLOR, linewidth = 0.25),
    axis.line           = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks          = element_blank(),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    plot.title          = element_text(color = INK, size = 12, face = "bold"),
    legend.position     = "top",
    legend.justification = "left",
    legend.background   = element_blank(),
    legend.key          = element_blank(),
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title         = element_text(color = INK, size = 10),
    plot.margin         = margin(t = 10, r = 16, b = 8, l = 8)
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
