#' anyplot.ai
#' heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-24

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Data: synthetic chroma features for a I-vi-IV-V chord progression in C major
n_frames    <- 80
time_sec    <- seq(0, 8, length.out = n_frames)
pitch_names <- c("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Chord pitch-class indices (1-based): C=1, C#=2, D=3, ..., B=12
chords <- list(
  c(1, 5, 8),   # C major: C, E, G
  c(10, 1, 5),  # A minor: A, C, E
  c(6, 10, 1),  # F major: F, A, C
  c(8, 12, 3)   # G major: G, B, D
)
chord_seq <- c(rep(1, 20), rep(2, 20), rep(3, 20), rep(4, 20))

# Build 12 x n_frames energy matrix: background noise + chord energy peaks
energy_mat <- matrix(pmax(0, rnorm(12 * n_frames, mean = 0.05, sd = 0.04)), nrow = 12)
for (f in seq_len(n_frames)) {
  active <- chords[[chord_seq[f]]]
  energy_mat[active, f] <- pmin(1, pmax(0, rnorm(length(active), mean = 0.78, sd = 0.07)))
}

# Long-format data frame using integer frame indices for clean tile placement
df <- data.frame(
  frame       = rep(seq_len(n_frames), each = 12),
  pitch_class = factor(rep(pitch_names, times = n_frames), levels = pitch_names),
  energy      = as.vector(energy_mat)
)

# X-axis labels at approximate 2-second intervals
label_frames <- c(1, 21, 41, 61, 80)
label_times  <- round(time_sec[label_frames])

# Plot
plot_title <- "heatmap-chromagram · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = frame, y = pitch_class, fill = energy)) +
  geom_tile() +
  scale_fill_gradient(
    low    = "#009E73",
    high   = "#4467A3",
    name   = "Energy",
    limits = c(0, 1),
    breaks = c(0, 0.25, 0.5, 0.75, 1.0)
  ) +
  scale_x_continuous(
    breaks = label_frames,
    labels = paste0(label_times, "s"),
    expand = c(0, 0)
  ) +
  scale_y_discrete(expand = c(0, 0)) +
  labs(
    title = plot_title,
    x     = "Time (seconds)",
    y     = "Pitch Class"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.border      = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.5),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_line(color = INK_SOFT, linewidth = 0.3),
    plot.title        = element_text(color = INK, size = 12),
    plot.margin       = margin(12, 12, 12, 12, "pt"),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.position   = "right",
    legend.key.height = unit(1.5, "in"),
    legend.key.width  = unit(0.25, "in")
  )

# Save — square canvas: 6 x 6 in at 400 dpi = 2400 x 2400 px
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
