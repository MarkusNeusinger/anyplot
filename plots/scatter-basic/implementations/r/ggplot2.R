#' anyplot.ai
#' scatter-basic: Basic Scatter Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-16

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# Data — marketing spend vs quarterly revenue across 200 campaigns
n       <- 200
spend   <- runif(n, 5, 150)
revenue <- 3.5 * spend + 80 + rnorm(n, 0, 30)
revenue <- pmax(revenue, 10)

df <- data.frame(spend = spend, revenue = revenue)

# Plot
p <- ggplot(df, aes(x = spend, y = revenue)) +
  geom_point(
    color = IMPRINT[1],
    size  = 4,
    alpha = 0.7,
    shape = 16
  ) +
  labs(
    title = "scatter-basic · ggplot2 · anyplot.ai",
    x     = "Marketing Spend ($K)",
    y     = "Quarterly Revenue ($K)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.border     = element_blank(),
    panel.grid.major = element_line(color = INK_SOFT, linewidth = 0.3),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK,      size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    axis.line        = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.ticks       = element_blank(),
    plot.title       = element_text(color = INK,      size = 24,
                                    face = "bold", margin = margin(b = 12)),
    plot.margin      = margin(20, 20, 20, 20)
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
