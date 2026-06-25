#' anyplot.ai
#' scatter-basic: Basic Scatter Plot
#' Library: ggplot2 | R

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# Approximate RULE (15% opacity INK blended over PAGE_BG) — ggplot2 lacks rgba
GRID_LINE   <- if (THEME == "light") "#D8D7D0" else "#3A3A36"

# Imprint palette — canonical order
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — marketing spend vs quarterly revenue across 200 campaigns
n       <- 200
spend   <- runif(n, 5, 150)
revenue <- 3.5 * spend + 80 + rnorm(n, 0, 150)
revenue <- pmax(revenue, 10)

df <- data.frame(spend = spend, revenue = revenue)

# Pearson r for bottom-right annotation
r_val   <- cor(df$spend, df$revenue)
r_label <- sprintf("Pearson r = %.2f", round(r_val, 2))

# Plot
p <- ggplot(df, aes(x = spend, y = revenue)) +
  geom_smooth(
    method    = "lm",
    se        = TRUE,
    color     = IMPRINT_PALETTE[1],
    fill      = IMPRINT_PALETTE[1],
    alpha     = 0.15,
    linewidth = 1.0
  ) +
  geom_point(
    color = IMPRINT_PALETTE[1],
    size  = 2.5,
    alpha = 0.7,
    shape = 16
  ) +
  annotate(
    geom     = "text",
    x        = max(df$spend),
    y        = min(df$revenue) + 5,
    label    = r_label,
    color    = INK_SOFT,
    size     = 3,
    fontface = "italic",
    hjust    = 1
  ) +
  labs(
    title = "scatter-basic · r · ggplot2 · anyplot.ai",
    x     = "Marketing Spend ($K)",
    y     = "Quarterly Revenue ($K)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.border     = element_blank(),
    panel.grid.major = element_line(color = GRID_LINE, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK,      size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    axis.line        = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.ticks       = element_blank(),
    plot.title       = element_text(color = INK,      size = 12,
                                    face = "bold", margin = margin(b = 12)),
    plot.margin      = margin(20, 20, 20, 20)
  )

# Save — 3200×1800 px (landscape 16:9)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
