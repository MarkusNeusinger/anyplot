#' anyplot.ai
#' spectrum-basic: Frequency Spectrum Plot
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-09-09

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

signal <- 1.00 * sin(2 * pi * 440  * t) +
          0.55 * sin(2 * pi * 880  * t) +
          0.30 * sin(2 * pi * 1320 * t) +
          0.15 * sin(2 * pi * 2150 * t) +
          rnorm(n, mean = 0, sd = 0.05)

spectrum <- fft(signal)
magnitude <- Mod(spectrum[1:(n / 2)]) * 2 / n
frequency <- (0:(n / 2 - 1)) * fs / n

df <- tibble::tibble(frequency = frequency, magnitude = magnitude) %>%
  filter(frequency > 0) %>%
  mutate(amplitude_db = 20 * log10(magnitude + 1e-6))

# --- Plot ---------------------------------------------------------------------
p <- ggplot(df, aes(x = frequency, y = amplitude_db)) +
  geom_area(fill = BRAND, alpha = 0.25) +
  geom_line(color = BRAND, linewidth = 0.7, alpha = 0.9) +
  scale_x_log10(
    breaks = c(20, 50, 100, 200, 500, 1000, 2000, 4000),
    labels = label_comma()
  ) +
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
