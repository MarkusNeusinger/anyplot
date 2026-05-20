#' anyplot.ai
#' histogram-returns-distribution: Returns Distribution Histogram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 92/100 | Created: 2026-05-20

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# Data - 2 years of daily returns for a diversified equity portfolio
n     <- 504
mu    <- 0.10 / 252        # 10% annual return (daily)
sigma <- 0.18 / sqrt(252)  # 18% annual volatility (daily)

base_returns          <- rnorm(n, mean = mu, sd = sigma)
fat_idx               <- sample(n, 14)
base_returns[fat_idx] <- base_returns[fat_idx] * 2.6
returns_pct           <- base_returns * 100

# Summary statistics
mean_ret <- mean(returns_pct)
sd_ret   <- sd(returns_pct)
skew_ret <- mean((returns_pct - mean_ret)^3) / sd_ret^3
kurt_ret <- mean((returns_pct - mean_ret)^4) / sd_ret^4 - 3

# Pre-compute histogram for per-bin tail coloring
h       <- hist(returns_pct, breaks = 40, plot = FALSE)
bin_w   <- diff(h$breaks)[1]
df_hist <- data.frame(
  mid     = h$mids,
  density = h$density,
  tail    = abs(h$mids - mean_ret) > 2 * sd_ret
)

# Normal distribution overlay
x_seq   <- seq(min(h$breaks), max(h$breaks), length.out = 500)
df_norm <- data.frame(x = x_seq, y = dnorm(x_seq, mean = mean_ret, sd = sd_ret))

# Statistics annotation (top-right, above the tail region)
stats_txt <- sprintf(
  "Mean:      %+.3f%%\nStd Dev:    %.3f%%\nSkewness: %+.2f\nEx. Kurt:  %+.2f",
  mean_ret, sd_ret, skew_ret, kurt_ret
)
ann_x <- max(h$mids)
ann_y <- max(h$density) * 0.93

# Plot
p <- ggplot(df_hist, aes(x = mid, y = density, fill = tail)) +
  geom_col(width = bin_w * 0.90, color = PAGE_BG, linewidth = 0.2, alpha = 0.85) +
  scale_fill_manual(
    values = c("FALSE" = OKABE_ITO[1], "TRUE" = OKABE_ITO[2]),
    labels = c("FALSE" = "Within ±2σ", "TRUE" = "Beyond ±2σ"),
    name   = NULL
  ) +
  geom_line(
    data = df_norm, aes(x = x, y = y), inherit.aes = FALSE,
    color = OKABE_ITO[3], linewidth = 1.2
  ) +
  geom_vline(
    xintercept = c(mean_ret - 2 * sd_ret, mean_ret + 2 * sd_ret),
    color      = OKABE_ITO[2], linewidth = 0.7, linetype = "dashed", alpha = 0.7
  ) +
  annotate("label",
    x = ann_x, y = ann_y,
    label         = stats_txt,
    hjust         = 1, vjust = 1,
    color         = INK,
    fill          = ELEVATED_BG,
    label.padding = unit(0.45, "lines"),
    label.size    = 0.3,
    size          = 3.9
  ) +
  scale_x_continuous(labels = function(x) paste0(x, "%")) +
  labs(
    title = "histogram-returns-distribution · r · ggplot2 · anyplot.ai",
    x     = "Daily Return (%)",
    y     = "Density"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK,      size = 12, hjust = 0),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA, linewidth = 0),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.position   = "bottom",
    legend.key.size   = unit(0.5, "cm"),
    plot.margin       = margin(0.5, 0.7, 0.3, 0.5, "cm")
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
