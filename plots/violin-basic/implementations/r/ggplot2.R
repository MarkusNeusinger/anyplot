#' anyplot.ai
#' violin-basic: Basic Violin Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-29

library(ggplot2)
library(ragg)

# Theme tokens
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID     <- alpha(INK, 0.15)

# Imprint palette: all eight positions, one per class group in order
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
CLASS_GROUP <- "Class group"  # role: category
TEST_SCORE  <- "Test score"   # role: value

# Data: replace this block with your own table, for example df <- read.csv("scores.csv", check.names = FALSE)
set.seed(42)
class_a <- rnorm(120, mean = 72, sd = 10)                                  # average, symmetric
class_b <- c(rnorm(60, mean = 60, sd = 5), rnorm(60, mean = 86, sd = 5))  # bimodal
class_c <- rnorm(120, mean = 83, sd = 6)                                   # high-performing
class_d <- pmax(50, pmin(100, 58 + rexp(120, rate = 0.10)))                # low, right-skewed
df <- tibble::tibble(
  !!CLASS_GROUP := rep(c("Class A", "Class B", "Class C", "Class D"), each = 120),
  !!TEST_SCORE  := c(class_a, class_b, class_c, class_d)
)

# Plot: reads only df and the constants above
df[[CLASS_GROUP]] <- factor(df[[CLASS_GROUP]], levels = unique(df[[CLASS_GROUP]]))

p <- ggplot(df, aes(x = .data[[CLASS_GROUP]], y = .data[[TEST_SCORE]], fill = .data[[CLASS_GROUP]])) +
  geom_violin(
    trim              = TRUE,
    color             = INK_SOFT,
    linewidth         = 0.3,
    quantiles         = c(0.25, 0.5, 0.75),
    quantile.linetype = 1,
    quantile.colour   = INK,
    quantile.linewidth = 0.6
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE, guide = "none") +
  labs(
    title = "violin-basic · r · ggplot2 · anyplot.ai",
    x     = CLASS_GROUP,
    y     = TEST_SCORE
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = GRID, linewidth = 0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.border       = element_blank(),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.line.y        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12, margin = margin(b = 12)),
    plot.margin        = margin(t = 20, r = 20, b = 16, l = 16)
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
