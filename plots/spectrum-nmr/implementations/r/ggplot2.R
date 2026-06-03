#' anyplot.ai
#' spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-06-03

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Simulated 1H NMR spectrum of ethanol (CH3CH2OH) at 400 MHz
lorentz <- function(x, x0, hw, h) {
  h * (hw / 2)^2 / ((x - x0)^2 + (hw / 2)^2)
}

ppm <- seq(5.2, -0.5, length.out = 7000)

# J-coupling constant: 7 Hz at 400 MHz = 0.0175 ppm
J        <- 0.0175
hw_sharp <- 0.004   # sharp peak half-width (ppm)
hw_broad <- 0.030   # broad OH singlet half-width (ppm)

# CH3 triplet at 1.17 ppm (3H): 1:2:1 intensity ratio
ch3_ppm <- c(1.17 - J, 1.17, 1.17 + J)
ch3_h   <- c(0.55, 1.10, 0.55)

# CH2 quartet at 3.69 ppm (2H): 1:3:3:1 intensity ratio
ch2_ppm <- c(3.69 - 1.5 * J, 3.69 - 0.5 * J, 3.69 + 0.5 * J, 3.69 + 1.5 * J)
ch2_h   <- c(0.22, 0.65, 0.65, 0.22)

# OH singlet at 2.60 ppm (1H, broad due to fast proton exchange)
# TMS reference at 0.00 ppm (internal chemical shift standard)
intensity <- numeric(length(ppm))
for (i in seq_along(ch3_ppm)) intensity <- intensity + lorentz(ppm, ch3_ppm[i], hw_sharp, ch3_h[i])
for (i in seq_along(ch2_ppm)) intensity <- intensity + lorentz(ppm, ch2_ppm[i], hw_sharp, ch2_h[i])
intensity <- intensity + lorentz(ppm, 2.60, hw_broad, 0.35)
intensity <- intensity + lorentz(ppm, 0.00, hw_sharp, 0.40)
intensity <- intensity + rnorm(length(ppm), 0, 0.003)
intensity <- pmax(intensity, 0)

df <- data.frame(ppm = ppm, intensity = intensity)

# Peak annotation labels
label_df <- data.frame(
  ppm   = c(1.17,    3.69,     2.60,     0.00),
  y     = c(1.33,    0.87,     0.59,     0.64),
  label = c("CH₃  1.17 ppm\ntriplet  (3H)",
            "CH₂  3.69 ppm\nquartet  (2H)",
            "OH  2.60 ppm\nsinglet  (1H)",
            "TMS  0.00 ppm\n(reference)")
)

# Title length check — only shrink when > 67 chars baseline
plot_title <- "Ethanol ¹H NMR · spectrum-nmr · r · ggplot2 · anyplot.ai"
title_n    <- nchar(plot_title)
title_size <- max(8, round(12 * min(1.0, 67 / title_n)))

p <- ggplot(df, aes(x = ppm, y = intensity)) +
  geom_hline(yintercept = 0, color = INK_SOFT, linewidth = 0.35) +
  geom_line(color = IMPRINT_PALETTE[1], linewidth = 0.65) +
  geom_text(
    data       = label_df,
    aes(x = ppm, y = y, label = label),
    color      = INK_MUTED,
    size       = 2.5,
    hjust      = 0.5,
    lineheight = 0.9
  ) +
  scale_x_reverse(breaks = seq(5, 0, by = -1)) +
  scale_y_continuous(
    limits = c(-0.05, 1.75),
    breaks = c(0, 0.5, 1.0),
    expand = c(0, 0)
  ) +
  labs(
    title = plot_title,
    x     = "Chemical Shift (δ, ppm)",
    y     = "Intensity (a.u.)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,   color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,   color = NA),
    panel.grid.major  = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line.x       = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.line.y       = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.text.y       = element_text(color = INK_MUTED, size = 7),
    plot.title        = element_text(color = INK,      size = title_size, face = "bold"),
    plot.margin       = margin(20, 30, 15, 20, unit = "pt")
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
