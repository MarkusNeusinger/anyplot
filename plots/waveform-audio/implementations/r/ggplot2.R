#' anyplot.ai
#' waveform-audio: Audio Waveform Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-06-03

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette — position 1 is always first series (brand green)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data: synthetic seismogram with P-wave and S-wave arrivals
n         <- 8000
time      <- seq(0, 2, length.out = n)

noise     <- rnorm(n, 0, 0.03)

p_arrival <- 0.4
p_env     <- ifelse(time >= p_arrival, exp(-3.0 * (time - p_arrival)), 0)
p_wave    <- 0.35 * p_env * sin(2 * pi * 8 * (time - p_arrival))

s_arrival <- 0.8
s_env     <- ifelse(time >= s_arrival, exp(-1.5 * (time - s_arrival)), 0)
s_wave    <- 0.90 * s_env * sin(2 * pi * 4 * (time - s_arrival) + 0.3)

coda_start <- 1.3
coda_env   <- ifelse(time >= coda_start, exp(-2.0 * (time - coda_start)), 0)
coda_wave  <- 0.20 * coda_env * sin(2 * pi * 2 * (time - coda_start) + 0.8)

raw       <- noise + p_wave + s_wave + coda_wave
amplitude <- raw / max(abs(raw)) * 0.92

df <- data.frame(time = time, amplitude = amplitude)

# Title length-based font size (baseline 67 chars → size 12)
plot_title <- paste0(
  "Seismic P-wave & S-wave Arrivals · ",
  "waveform-audio · r · ggplot2 · anyplot.ai"
)
title_size <- max(8L, round(12 * 67 / nchar(plot_title)))

# Plot
p <- ggplot(df, aes(x = time)) +
  geom_ribbon(
    aes(ymin = pmin(amplitude, 0), ymax = pmax(amplitude, 0)),
    fill  = IMPRINT_PALETTE[1],
    alpha = 0.78
  ) +
  geom_hline(yintercept = 0, color = INK_MUTED, linewidth = 0.4) +
  scale_x_continuous(
    breaks = seq(0, 2, by = 0.25),
    expand = expansion(mult = 0, add = 0.01)
  ) +
  scale_y_continuous(
    limits = c(-1.05, 1.05),
    breaks = c(-1, -0.5, 0, 0.5, 1)
  ) +
  labs(
    x     = "Time (s)",
    y     = "Normalized Amplitude",
    title = plot_title
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK_MUTED, linewidth = 0.2),
    panel.grid.minor = element_blank(),
    panel.border     = element_blank(),
    axis.line        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks       = element_blank(),
    axis.title       = element_text(color = INK,      size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK,      size = title_size,
                                    margin = margin(b = 10)),
    plot.margin      = margin(20, 24, 16, 16)
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
