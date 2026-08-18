#' anyplot.ai
#' histogram-overlapping: Overlapping Histograms
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 82/100 | Created: 2026-08-18

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data -----------------------------------------------------------------
n <- 200
completion_time <- c(
  rnorm(n, mean = 45, sd = 8),
  rnorm(n, mean = 39, sd = 7),
  rnorm(n, mean = 51, sd = 9)
)
design <- factor(
  rep(c("Design A", "Design B", "Design C"), each = n),
  levels = c("Design A", "Design B", "Design C")
)
df <- tibble::tibble(completion_time = completion_time, design = design)

binwidth <- diff(range(df$completion_time)) / 28

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = completion_time, fill = design)) +
  geom_histogram(
    position  = "identity",
    binwidth  = binwidth,
    alpha     = 0.55,
    color     = PAGE_BG,
    linewidth = 0.25
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:3], name = "UI design") +
  labs(
    title = "histogram-overlapping · r · ggplot2 · anyplot.ai",
    x     = "Task Completion Time (seconds)",
    y     = "Number of Users"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.15),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 12),
    legend.position   = "right",
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_blank(),
    legend.key        = element_blank()
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
