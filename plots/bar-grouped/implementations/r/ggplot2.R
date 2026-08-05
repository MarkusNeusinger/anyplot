#' anyplot.ai
#' bar-grouped: Grouped Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-08-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
regions  <- c("North", "South", "East", "West", "Central")
products <- c("Software", "Hardware", "Services")

df <- expand.grid(region = regions, product = products) %>%
  mutate(
    region  = factor(region, levels = regions),
    product = factor(product, levels = products),
    revenue = case_when(
      product == "Software" ~ round(rnorm(n(), mean = 5.8, sd = 0.9), 1),
      product == "Hardware" ~ round(rnorm(n(), mean = 4.2, sd = 1.1), 1),
      TRUE                  ~ round(rnorm(n(), mean = 3.0, sd = 0.6), 1)
    )
  )

# --- Plot -----------------------------------------------------------------
p <- ggplot(df, aes(x = region, y = revenue, fill = product)) +
  geom_col(
    position = position_dodge(width = 0.75),
    width = 0.68,
    color = PAGE_BG,
    linewidth = 0.4
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:3], name = "Product Line") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(
    title = "Revenue by Product Line · bar-grouped · r · ggplot2 · anyplot.ai",
    x = "Region",
    y = "Revenue ($M)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor.x  = element_blank(),
    panel.grid.minor.y  = element_blank(),
    panel.grid.major.y  = element_line(color = INK, linewidth = 0.25),
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
