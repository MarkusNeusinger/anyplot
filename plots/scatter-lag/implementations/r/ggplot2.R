#' anyplot.ai
#' scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-06-24

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- adjustcolor(INK, alpha.f = 0.15)

# Data — synthetic AR(1) hourly temperature residuals (phi = 0.72, n = 300)
n   <- 300
phi <- 0.72
eps <- rnorm(n, mean = 0, sd = 1)
ts_values <- numeric(n)
ts_values[1] <- eps[1]
for (i in 2:n) {
  ts_values[i] <- phi * ts_values[i - 1] + eps[i]
}

lag_k  <- 1
x_vals <- ts_values[seq_len(n - lag_k)]
y_vals <- ts_values[(lag_k + 1):n]
t_idx  <- seq_len(n - lag_k)

df <- data.frame(x = x_vals, y = y_vals, t = t_idx)

r_val   <- cor(df$x, df$y)
r_label <- sprintf("r = %.2f", r_val)

# Plot
title_str <- "scatter-lag · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = x, y = y, color = t)) +
  geom_abline(
    slope     = 1, intercept = 0,
    color     = INK_SOFT,
    linewidth = 0.8,
    linetype  = "dashed"
  ) +
  geom_point(size = 2.5, alpha = 0.65) +
  annotate(
    "label",
    x = -Inf, y = Inf,
    label         = r_label,
    hjust         = -0.2,  vjust = 1.4,
    size          = 3.5,
    color         = INK,
    fill          = ELEVATED_BG,
    label.size    = 0.3,
    label.padding = unit(0.35, "lines"),
    label.r       = unit(0.08, "lines")
  ) +
  scale_color_gradient(
    low   = "#009E73",
    high  = "#4467A3",
    name  = "Time\nindex",
    guide = guide_colorbar(
      barwidth       = 0.5,
      barheight      = 7,
      title.position = "top"
    )
  ) +
  labs(
    x     = "y(t)",
    y     = "y(t + 1)",
    title = title_str
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.5),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = 12, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 9),
    legend.position   = "right",
    legend.margin     = margin(5, 8, 5, 8)
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
