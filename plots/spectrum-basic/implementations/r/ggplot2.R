#' anyplot.ai
#' spectrum-basic: Frequency Spectrum Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]

# --- Data --------------------------------------------------------------------
# Synthetic audio signal: a fundamental tone at 440 Hz (concert A4) plus two
# decaying harmonics and a higher resonance, buried in noise. FFT recovers the
# frequency content, mirroring a real spectrum-analyzer workflow.
n  <- 4096   # FFT size (samples)
fs <- 8000   # sampling rate, Hz
t  <- (0:(n - 1)) / fs
peak_freqs <- c(440, 880, 1320, 2150)

signal <- 1.00 * sin(2 * pi * peak_freqs[1] * t) +
          0.55 * sin(2 * pi * peak_freqs[2] * t) +
          0.30 * sin(2 * pi * peak_freqs[3] * t) +
          0.15 * sin(2 * pi * peak_freqs[4] * t) +
          rnorm(n, mean = 0, sd = 0.05)

spectrum <- fft(signal)
magnitude <- Mod(spectrum[1:(n / 2)]) * 2 / n
frequency <- (0:(n / 2 - 1)) * fs / n

df <- tibble::tibble(frequency = frequency, magnitude = magnitude) %>%
  filter(frequency > 0) %>%
  mutate(amplitude_db = 20 * log10(magnitude + 1e-6))

# Noise floor: median amplitude across all bins. Used both as a reference
# line and as the ribbon baseline so the fill emphasizes height *above* the
# floor at each peak instead of washing every bin down to 0 dB.
noise_floor <- median(df$amplitude_db)

df <- df %>%
  mutate(fill_min = pmin(amplitude_db, noise_floor),
         fill_max = pmax(amplitude_db, noise_floor))

# Callout labels for the fundamental + harmonics, using the nearest FFT bin's
# actual recovered amplitude.
peak_labels <- lapply(peak_freqs, function(target) {
  idx <- which.min(abs(df$frequency - target))
  tibble::tibble(
    frequency    = df$frequency[idx],
    amplitude_db = df$amplitude_db[idx],
    label        = paste0(target, " Hz")
  )
}) %>% bind_rows()

# --- Plot ---------------------------------------------------------------------
p <- ggplot(df, aes(x = frequency, y = amplitude_db)) +
  geom_ribbon(aes(ymin = fill_min, ymax = fill_max), fill = BRAND, alpha = 0.25) +
  geom_hline(yintercept = noise_floor, color = INK_SOFT, linewidth = 0.4, linetype = "dashed") +
  geom_line(color = BRAND, linewidth = 0.7, alpha = 0.9) +
  geom_point(
    data = peak_labels, aes(x = frequency, y = amplitude_db),
    color = BRAND, size = 2.5, inherit.aes = FALSE
  ) +
  geom_text(
    data = peak_labels, aes(x = frequency, y = amplitude_db, label = label),
    color = INK, size = 3, vjust = -0.9, inherit.aes = FALSE
  ) +
  scale_x_log10(
    breaks = c(20, 50, 100, 200, 500, 1000, 2000, 4000),
    labels = label_comma()
  ) +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.12))) +
  labs(
    x     = "Frequency (Hz)",
    y     = "Amplitude (dB)",
    title = "spectrum-basic · r · ggplot2 · anyplot.ai"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT),
    axis.ticks        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12)
  )

# --- Save ----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
