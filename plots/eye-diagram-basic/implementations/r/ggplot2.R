#' anyplot.ai
#' eye-diagram-basic: Signal Integrity Eye Diagram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-06-18

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# NRZ simulation parameters
n_bits       <- 600
samp_per_ui  <- 100
noise_sigma  <- 0.05   # Gaussian noise (5% of amplitude)
jitter_sigma <- 0.03   # Timing jitter std dev (3% of UI)
sigmoid_k    <- 18     # Bandwidth-limiting sharpness

# Random bit stream and per-transition jitter
bits       <- sample(c(0L, 1L), n_bits, replace = TRUE)
jitter_raw <- rnorm(n_bits - 1L, 0.0, jitter_sigma)
j_arr      <- c(0.0, jitter_raw)  # j_arr[b]: jitter at start of bit b

# Vectorized waveform generation with sigmoid transitions and jitter
n_total   <- n_bits * samp_per_ui
t_all     <- (seq_len(n_total) - 0.5) / samp_per_ui
bit_idx   <- pmin(as.integer(floor(t_all)) + 1L, n_bits)
t_within  <- t_all - floor(t_all)
prev_bits <- c(bits[1L], bits[-n_bits])
prev_at_t <- prev_bits[bit_idx]
curr_at_t <- bits[bit_idx]
j_vals    <- j_arr[bit_idx]

dt    <- (t_within - j_vals) * sigmoid_k
sig_s <- 1.0 / (1.0 + exp(-dt))
same  <- (prev_at_t == curr_at_t)
rise  <- (!same & curr_at_t > prev_at_t)
v_sig <- ifelse(same, curr_at_t * 1.0, ifelse(rise, sig_s, 1.0 - sig_s))
v_sig <- v_sig + rnorm(n_total, 0.0, noise_sigma)

# Fold waveform into 2-UI eye traces (start at each bit boundary)
window_sz <- 2L * samp_per_ui
n_traces  <- n_bits - 2L
t_axis    <- seq(0.0, 2.0, length.out = window_sz + 1L)[-1L]
start_idx <- (seq_len(n_traces) - 1L) * samp_per_ui + 1L
samp_mat  <- outer(0L:(window_sz - 1L), start_idx, `+`)
eye_df    <- data.frame(
  time    = rep(t_axis, n_traces),
  voltage = v_sig[as.vector(samp_mat)]
)

# Plot: density heatmap — Imprint sequential colormap (green=low, blue=high density)
plot_title <- "eye-diagram-basic · r · ggplot2 · anyplot.ai"

p <- ggplot(eye_df, aes(x = time, y = voltage)) +
  geom_bin_2d(bins = 100) +
  scale_fill_gradient(
    name  = "Density",
    low   = "#009E73",  # Imprint seq — brand green
    high  = "#4467A3",  # Imprint seq — blue
    trans = "sqrt"
  ) +
  scale_x_continuous(
    name   = "Time (UI)",
    breaks = c(0.0, 0.5, 1.0, 1.5, 2.0),
    expand = c(0.01, 0.0)
  ) +
  scale_y_continuous(
    name   = "Voltage (V)",
    breaks = c(0.0, 0.25, 0.5, 0.75, 1.0),
    expand = c(0.06, 0.0)
  ) +
  labs(title = plot_title) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,     color = NA),
    panel.grid.major  = element_line(color = INK_MUTED,  linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(fill = NA,          color = INK_SOFT, linewidth = 0.4),
    axis.title        = element_text(color = INK,        size = 10),
    axis.text         = element_text(color = INK_SOFT,   size = 8),
    plot.title        = element_text(color = INK,        size = 12, hjust = 0.0),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,   size = 8),
    legend.title      = element_text(color = INK,        size = 9),
    legend.position   = "right",
    plot.margin       = margin(12, 12, 12, 12, "pt")
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
