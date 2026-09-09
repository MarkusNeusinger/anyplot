#' anyplot.ai
#' spectrogram-basic: Spectrogram Time-Frequency Heatmap
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-09-09

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# --- Data: synthetic linear chirp signal ------------------------------------
sample_rate <- 4000
duration <- 4
n_samples <- sample_rate * duration
t <- seq_len(n_samples) / sample_rate

freq_start <- 100
freq_end <- 800
instantaneous_phase <- 2 * pi * (freq_start * t + (freq_end - freq_start) * t^2 / (2 * duration))
signal <- sin(instantaneous_phase) + 0.15 * rnorm(n_samples)

# --- Short-time Fourier transform (Hann window, 75% overlap) ---------------
window_size <- 512
hop <- 128
hann_window <- 0.5 - 0.5 * cos(2 * pi * (0:(window_size - 1)) / (window_size - 1))

n_windows <- floor((n_samples - window_size) / hop) + 1
n_freq_bins <- window_size %/% 2 + 1

freqs <- (0:(n_freq_bins - 1)) * sample_rate / window_size
times <- ((0:(n_windows - 1)) * hop + window_size / 2) / sample_rate

power_db <- matrix(0, nrow = n_windows, ncol = n_freq_bins)
for (i in seq_len(n_windows)) {
  start <- (i - 1) * hop + 1
  segment <- signal[start:(start + window_size - 1)] * hann_window
  spectrum <- fft(segment)[1:n_freq_bins]
  power_db[i, ] <- 20 * log10(Mod(spectrum) + 1e-6)
}
power_db <- pmax(power_db, max(power_db) - 60) # 60 dB dynamic range

spec_df <- data.frame(
  time = rep(times, times = n_freq_bins),
  frequency = rep(freqs, each = n_windows),
  power = as.vector(power_db)
)

max_freq_display <- 1000
spec_df <- spec_df[spec_df$frequency <= max_freq_display, ]

# --- Plot ---------------------------------------------------------------
title_str <- "spectrogram-basic · r · ggplot2 · anyplot.ai"
title_fontsize <- round(12 * min(1.0, 67 / nchar(title_str)))

p <- ggplot(spec_df, aes(x = time, y = frequency, fill = power)) +
  geom_raster() +
  scale_fill_gradient(
    low = "#009E73", high = "#4467A3",
    name = "Power (dB)",
    guide = guide_colorbar(barwidth = unit(0.35, "cm"), barheight = unit(6, "cm"))
  ) +
  scale_x_continuous(expand = c(0, 0), breaks = seq(0, duration, 1)) +
  scale_y_continuous(expand = c(0, 0), breaks = seq(0, max_freq_display, 200)) +
  labs(x = "Time (s)", y = "Frequency (Hz)", title = title_str) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = title_fontsize),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    plot.margin       = margin(10, 10, 10, 10)
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
