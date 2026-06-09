#' anyplot.ai
#' pp-basic: Probability-Probability (P-P) Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-06-09

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette (canonical order)
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Data: reaction time measurements (ms) for a quality control process
# 200 observations with a slight right tail — compared against a fitted normal
n_obs        <- 200
base_times   <- rnorm(160, mean = 145, sd = 12)
delayed_obs  <- rnorm(40,  mean = 162, sd = 8)
observed     <- c(base_times, delayed_obs)

# Fit normal distribution parameters (MLE)
fit_mean <- mean(observed)
fit_sd   <- sd(observed)

# Empirical CDF via Hazen plotting positions: (i - 0.5) / n
sorted_obs      <- sort(observed)
empirical_cdf   <- (seq_len(n_obs) - 0.5) / n_obs
theoretical_cdf <- pnorm(sorted_obs, fit_mean, fit_sd)

df <- data.frame(
  theoretical = theoretical_cdf,
  empirical   = empirical_cdf
)

# Build plot
plot_title <- "pp-basic · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = theoretical, y = empirical)) +
  geom_abline(
    slope     = 1,
    intercept = 0,
    color     = INK_SOFT,
    linewidth = 0.8,
    linetype  = "dashed"
  ) +
  geom_point(
    color = IMPRINT_PALETTE[1],
    size  = 2.5,
    alpha = 0.75
  ) +
  scale_x_continuous(
    limits = c(0, 1),
    breaks = seq(0, 1, 0.2),
    expand = c(0.02, 0)
  ) +
  scale_y_continuous(
    limits = c(0, 1),
    breaks = seq(0, 1, 0.2),
    expand = c(0.02, 0)
  ) +
  coord_equal() +
  labs(
    x        = "Theoretical Cumulative Probability",
    y        = "Empirical Cumulative Probability",
    title    = plot_title,
    subtitle = "Fitted normal — right-tail deviation visible above 0.6"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG,  color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG,  color = NA),
    panel.grid.major = element_line(
      color     = scales::alpha(INK, 0.15),
      linewidth = 0.5
    ),
    panel.grid.minor = element_blank(),
    panel.border     = element_blank(),
    axis.line        = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.title       = element_text(color = INK,      size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK,      size = 12),
    plot.subtitle    = element_text(color = INK_SOFT, size = 9),
    plot.margin      = margin(20, 20, 20, 20)
  )

# Save — square canvas: 6×6 in @ 400 dpi = 2400×2400 px
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
