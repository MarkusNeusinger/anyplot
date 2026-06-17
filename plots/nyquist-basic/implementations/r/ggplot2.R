#' anyplot.ai
#' nyquist-basic: Nyquist Plot for Control Systems
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-17

library(ggplot2)
library(dplyr)
library(ragg)
library(grid)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette — brand green always first
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red (semantic anchor: critical/error)
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# Data: open-loop transfer function G(s) = 2 / (s*(s+1)*(s+2))
# Phase crossover at ω = sqrt(2) ≈ 1.414 rad/s, where G(jω) = -1/3 (stable)
# Gain crossover (|G| = 1) near ω ≈ 0.77 rad/s
set.seed(42)
n_pts <- 800
omega <- exp(seq(log(0.05), log(100), length.out = n_pts))

G_jw <- function(w) {
  s <- 1i * w
  2 / (s * (s + 1) * (s + 2))
}

Gjw     <- G_jw(omega)
re_vals <- Re(Gjw)
im_vals <- Im(Gjw)

df <- data.frame(re = re_vals, im = im_vals, omega = omega)

# Unit circle (reference: gain = 1 boundary)
theta       <- seq(0, 2 * pi, length.out = 300)
unit_circle <- data.frame(x = cos(theta), y = sin(theta))

# Frequency annotation points: key control-theory landmarks
# pc = phase crossover (Im = 0, curve crosses real axis at ω = sqrt(2))
label_omegas  <- c(0.3, 0.7, 1.0, sqrt(2), 2.5)
label_idx     <- sapply(label_omegas, function(w) which.min(abs(omega - w)))
label_df      <- data.frame(
  re    = re_vals[label_idx],
  im    = im_vals[label_idx],
  label = c("ω=0.3", "ω=0.7", "ω=1.0", "ω=√2 (pc)", "ω=2.5"),
  nx    = c( 0.10,    0.10,    0.10,    -0.28,         0.20),
  ny    = c( 0.13,    0.13,   -0.18,     0.20,          0.16)
)

# Directional arrows showing direction of increasing ω along the curve
arrow_steps <- c(185, 255, 330, 415, 515)
arrow_end   <- arrow_steps + 22
arrow_df    <- data.frame(
  x    = re_vals[arrow_steps],
  y    = im_vals[arrow_steps],
  xend = re_vals[arrow_end],
  yend = im_vals[arrow_end]
)
# Keep only arrows within the display window
visible  <- abs(arrow_df$x) < 3.2 & abs(arrow_df$y) < 3.2 &
            abs(arrow_df$xend) < 3.2 & abs(arrow_df$yend) < 3.2
arrow_df <- arrow_df[visible, ]

# Title
plot_title <- "nyquist-basic · r · ggplot2 · anyplot.ai"

# Plot
p <- ggplot() +
  # Unit circle: gain = 1 reference
  geom_path(
    data = unit_circle, aes(x = x, y = y),
    color = INK_MUTED, linewidth = 0.55, linetype = "dashed"
  ) +
  # Reference axes through origin
  geom_hline(yintercept = 0, color = INK_SOFT, linewidth = 0.35) +
  geom_vline(xintercept = 0, color = INK_SOFT, linewidth = 0.35) +
  # Nyquist curve (brand green — first series)
  geom_path(
    data = df, aes(x = re, y = im),
    color = IMPRINT_PALETTE[1], linewidth = 1.15
  ) +
  # Directional arrows showing increasing ω
  geom_segment(
    data  = arrow_df,
    aes(x = x, y = y, xend = xend, yend = yend),
    color = IMPRINT_PALETTE[1], linewidth = 1.15,
    arrow = arrow(length = unit(0.22, "cm"), type = "closed", angle = 22)
  ) +
  # Frequency annotation dots (blue — second categorical series)
  geom_point(
    data = label_df, aes(x = re, y = im),
    color = IMPRINT_PALETTE[3], size = 2.5, shape = 19
  ) +
  geom_text(
    data = label_df, aes(x = re, y = im, label = label),
    color = INK_SOFT, size = 2.7, nudge_x = label_df$nx, nudge_y = label_df$ny
  ) +
  # Critical point (-1, 0): matte red X (semantic anchor for instability boundary)
  annotate(
    "point", x = -1, y = 0,
    color = IMPRINT_PALETTE[5], size = 6, shape = 4, stroke = 2.8
  ) +
  annotate(
    "text", x = -1.0, y = -0.24, label = "(-1, 0)",
    color = IMPRINT_PALETTE[5], size = 3.0, hjust = 0.5
  ) +
  # Axis labels and title
  labs(x = "Real", y = "Imaginary", title = plot_title) +
  # 1:1 aspect ratio — required so unit circle appears circular
  coord_fixed(ratio = 1, xlim = c(-3, 1.5), ylim = c(-3, 1.5)) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK_MUTED, linewidth = 0.2),
    panel.grid.minor = element_blank(),
    panel.border     = element_rect(color = INK_MUTED, fill = NA, linewidth = 0.3),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12),
    plot.margin      = margin(20, 20, 20, 20, unit = "pt"),
    legend.position  = "none"
  )

# Save — square canvas (2400 × 2400 px: width=6, height=6 in, dpi=400)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
