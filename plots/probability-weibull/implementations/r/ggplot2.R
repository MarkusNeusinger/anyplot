#' anyplot.ai
#' probability-weibull: Weibull Probability Plot for Reliability Analysis
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-06-07

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
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (failures)
  "#AE3030",  # 5 — matte red (censored — semantic: suspended/lost)
  "#4467A3"   # 3 — blue (fitted line)
)

# Data: turbine blade fatigue-life data (hours to failure)
# Simulate Weibull(shape=2.3, scale=8000) with some right-censored observations
n_total <- 40
true_shape <- 2.3
true_scale <- 8000

# Generate failure times
all_times <- true_scale * (-log(runif(n_total)))^(1 / true_shape)
# Right-censor at 10000 hours
censor_time <- 10000
is_censored <- all_times > censor_time
time_to_failure <- pmin(all_times, censor_time)

# Sort by time for proper rank ordering
ord <- order(time_to_failure)
time_to_failure <- time_to_failure[ord]
is_censored <- is_censored[ord]

# Count actual failures for median rank calculation
n_fail <- sum(!is_censored)
failure_idx <- which(!is_censored)

# Median rank (Benard's approximation): (i - 0.3) / (n + 0.4)
# Only assign plotting positions to failures; censored are plotted separately
median_ranks <- (seq_along(failure_idx) - 0.3) / (n_total + 0.4)

# Weibull linearized y-axis: y = ln(-ln(1 - F))
weibull_y <- log(-log(1 - median_ranks))

# Data frame for failure points
df_fail <- data.frame(
  time  = time_to_failure[failure_idx],
  wb_y  = weibull_y,
  type  = "Failure"
)

# For censored points: use the last assigned median rank as a ceiling (right-censored)
# Place censored obs at a y that reflects "at least survived this long"
# — just plot them at the axis mid-level annotated as censored; no formal rank
censored_times <- time_to_failure[is_censored]
df_cens <- data.frame(
  time = censored_times,
  wb_y = rep(median(weibull_y), length(censored_times)),
  type = "Censored (suspended)"
)

# Fit line via OLS on linearised data (log(t) ~ wb_y)
log_times <- log(df_fail$time)
fit <- lm(weibull_y ~ log_times, data = df_fail)
beta_hat  <- coef(fit)[2]            # slope = shape parameter
eta_hat   <- exp(-coef(fit)[1] / coef(fit)[2])  # scale parameter (characteristic life)

# Fitted line over the data range
x_seq     <- seq(log(min(df_fail$time) * 0.7), log(max(df_fail$time) * 1.3), length.out = 200)
y_fit_seq <- coef(fit)[1] + coef(fit)[2] * x_seq
df_line   <- data.frame(time = exp(x_seq), wb_y = y_fit_seq)

# 63.2% reference line: wb_y at F=0.632 = ln(-ln(1-0.632)) ≈ 0
ref_y  <- log(-log(1 - 0.632))  # ≈ -0.0006 ≈ 0
ref_63 <- data.frame(
  x_start = min(df_line$time),
  x_end   = exp(-coef(fit)[1] / coef(fit)[2]),  # = eta_hat
  y_val   = ref_y
)

# Title
plot_title <- "probability-weibull · r · ggplot2 · anyplot.ai"
title_len  <- nchar(plot_title)
base_title_size <- 12
title_size <- max(8, round(base_title_size * 67 / title_len))

# Custom Weibull probability y-axis breaks and labels
# Convert F values to wb_y = ln(-ln(1-F))
f_breaks  <- c(0.01, 0.05, 0.10, 0.20, 0.30, 0.50, 0.632, 0.80, 0.90, 0.95, 0.99)
wb_breaks <- log(-log(1 - f_breaks))
f_labels  <- paste0(formatC(f_breaks * 100, format = "g", digits = 3), "%")

# Plot
p <- ggplot() +
  # Fitted Weibull line
  geom_line(
    data = df_line,
    aes(x = time, y = wb_y),
    color     = IMPRINT_PALETTE[3],
    linewidth = 1.0,
    linetype  = "solid"
  ) +
  # 63.2% horizontal reference line
  geom_segment(
    aes(x = ref_63$x_start, xend = ref_63$x_end,
        y = ref_63$y_val,   yend = ref_63$y_val),
    color     = INK_MUTED,
    linewidth = 0.5,
    linetype  = "dashed"
  ) +
  # Vertical drop to x-axis at eta
  geom_segment(
    aes(x = ref_63$x_end, xend = ref_63$x_end,
        y = ref_63$y_val, yend = min(wb_breaks) - 0.3),
    color     = INK_MUTED,
    linewidth = 0.5,
    linetype  = "dashed"
  ) +
  # Failure points (filled)
  geom_point(
    data = df_fail,
    aes(x = time, y = wb_y, shape = "Failure", color = "Failure"),
    size  = 2.8,
    alpha = 0.85,
    fill  = IMPRINT_PALETTE[1]
  ) +
  # Censored points (hollow)
  geom_point(
    data = df_cens,
    aes(x = time, y = wb_y, shape = "Censored (suspended)", color = "Censored (suspended)"),
    size   = 2.8,
    alpha  = 0.85,
    stroke = 1.2
  ) +
  # Parameter annotation
  annotate(
    "label",
    x     = min(df_fail$time) * 1.1,
    y     = max(wb_breaks) - 0.2,
    label = sprintf("β (shape) = %.2f\nη (scale) = %.0f h", beta_hat, eta_hat),
    hjust = 0,
    vjust = 1,
    size  = 3.5,
    color = INK_SOFT,
    fill  = ELEVATED_BG,
    label.size = 0.3
  ) +
  # 63.2% label
  annotate(
    "text",
    x     = ref_63$x_start * 1.05,
    y     = ref_63$y_val + 0.08,
    label = "63.2%",
    hjust = 0,
    size  = 2.5,
    color = INK_MUTED
  ) +
  scale_x_log10(
    labels = label_comma(),
    name   = "Time to Failure (hours)"
  ) +
  scale_y_continuous(
    breaks = wb_breaks,
    labels = f_labels,
    limits = c(min(wb_breaks) - 0.3, max(wb_breaks) + 0.1),
    name   = "Cumulative Failure Probability"
  ) +
  scale_color_manual(
    name   = NULL,
    values = c("Failure" = IMPRINT_PALETTE[1], "Censored (suspended)" = IMPRINT_PALETTE[2])
  ) +
  scale_shape_manual(
    name   = NULL,
    values = c("Failure" = 19, "Censored (suspended)" = 1)
  ) +
  labs(title = plot_title) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.4),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.x       = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK,      size = title_size, face = "bold",
                                     margin = margin(b = 8)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK,      size = 9),
    legend.position   = "bottom",
    legend.key        = element_rect(fill = NA, color = NA),
    plot.margin       = margin(12, 16, 12, 12)
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
