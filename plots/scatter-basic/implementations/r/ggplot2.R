#' anyplot.ai
#' scatter-basic: Basic Scatter Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-16

library(ggplot2)
library(gapminder)
library(scales)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COL    <- if (THEME == "light") "#E3E1DB" else "#2F2F2C"
BRAND       <- "#009E73"

# Data — 142 countries, year 2007
df <- gapminder[gapminder$year == 2007, ]

# Plot
p <- ggplot(df, aes(x = gdpPercap, y = lifeExp)) +
  geom_point(
    fill   = BRAND,
    color  = PAGE_BG,
    size   = 4,
    alpha  = 0.75,
    shape  = 21,
    stroke = 0.6
  ) +
  scale_x_log10(labels = label_dollar()) +
  labs(
    x     = "GDP per Capita (USD, log scale)",
    y     = "Life Expectancy (years)",
    title = "scatter-basic · ggplot2 · anyplot.ai"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = GRID_COL, linewidth = 0.4),
    panel.grid.minor = element_blank(),
    panel.border     = element_blank(),
    axis.line        = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.ticks       = element_blank(),
    axis.title       = element_text(color = INK,      size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK,      size = 24, face = "bold"),
    plot.margin      = margin(t = 24, r = 24, b = 16, l = 16, unit = "pt")
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
