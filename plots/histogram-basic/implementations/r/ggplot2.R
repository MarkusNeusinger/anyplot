#' anyplot.ai
#' histogram-basic: Basic Histogram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-05-28

library(ggplot2)
library(scales)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
SALARY <- "Annual Salary"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("salaries.csv", check.names = FALSE)
set.seed(42)
n <- 400
salaries <- c(
  rnorm(round(n * 0.70), mean = 65000,  sd = 15000),
  rnorm(round(n * 0.20), mean = 105000, sd = 20000),
  rnorm(round(n * 0.10), mean = 175000, sd = 30000)
)
df <- tibble::tibble(!!SALARY := pmax(salaries, 28000))

# Plot: reads only df and the constants above
p <- ggplot(df, aes(x = .data[[SALARY]])) +
  geom_histogram(
    bins      = 35,
    fill      = IMPRINT_PALETTE[1],
    color     = alpha(INK, 0.55),
    linewidth = 0.25
  ) +
  scale_x_continuous(
    labels = label_dollar(scale = 1e-3, suffix = "k"),
    expand = expansion(mult = c(0.01, 0.02))
  ) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
  labs(
    title = "histogram-basic · r · ggplot2 · anyplot.ai",
    x     = SALARY,
    y     = "Number of Employees"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(color = alpha(INK_SOFT, 0.35), linewidth = 0.2),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK,      size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line          = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = 12, face = "bold",
                                      margin = margin(b = 10)),
    plot.margin        = margin(20, 25, 15, 15)
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
