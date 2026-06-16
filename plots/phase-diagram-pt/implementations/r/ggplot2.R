#' anyplot.ai
#' phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-06-08

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

# --- Theme tokens (Imprint palette, theme-adaptive chrome) ------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
GRID_COLOR  <- adjustcolor(INK, alpha.f = 0.12)

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first categorical)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

# --- Data: CO2 phase diagram (physically realistic approximations) -----------
T_tp <- 216.55  # triple point temperature (K)
P_tp <- 5.18    # triple point pressure (atm)
T_c  <- 304.13  # critical point temperature (K)
P_c  <- 72.8    # critical point pressure (atm)

# Liquid-gas: Clausius-Clapeyron fit anchored at both triple and critical points
T_lg <- seq(T_tp, T_c, length.out = 100)
P_lg <- exp(10.825 - 1988 / T_lg)

# Solid-gas: sublimation curve, L_sub/R = 25200/8.314 ≈ 3030 K
T_sg <- seq(140, T_tp, length.out = 100)
P_sg <- P_tp * exp(-3030.3 * (1 / T_sg - 1 / T_tp))

# Solid-liquid: near-vertical melting curve, dT/dP ≈ 0.015 K/atm for CO2
P_sl <- seq(P_tp, 2000, length.out = 100)
T_sl <- T_tp + 0.015 * (P_sl - P_tp)

df_boundaries <- bind_rows(
  tibble(temperature = T_lg, pressure = P_lg, boundary = "Liquid-Gas"),
  tibble(temperature = T_sg, pressure = P_sg, boundary = "Solid-Gas"),
  tibble(temperature = T_sl, pressure = P_sl,  boundary = "Solid-Liquid")
)
df_boundaries$boundary <- factor(
  df_boundaries$boundary,
  levels = c("Solid-Liquid", "Liquid-Gas", "Solid-Gas")
)

df_special <- tibble(
  temperature = c(T_tp, T_c),
  pressure    = c(P_tp, P_c)
)

# --- Plot -------------------------------------------------------------------
title_str <- "CO2 Phase Diagram · phase-diagram-pt · r · ggplot2 · anyplot.ai"

p <- ggplot() +
  # Phase region fills (semi-transparent, drawn first so lines appear on top)
  annotate("rect", xmin = 130, xmax = 219, ymin = 5,     ymax = 2000,
           fill = IMPRINT_PALETTE[3], alpha = 0.05) +
  annotate("rect", xmin = 215, xmax = 305, ymin = 5,     ymax = 75,
           fill = IMPRINT_PALETTE[2], alpha = 0.05) +
  annotate("rect", xmin = 140, xmax = 415, ymin = 0.001, ymax = 73,
           fill = IMPRINT_PALETTE[1], alpha = 0.05) +
  annotate("rect", xmin = 303, xmax = 415, ymin = 72,    ymax = 2000,
           fill = IMPRINT_PALETTE[4], alpha = 0.05) +
  geom_line(
    data = df_boundaries,
    aes(x = temperature, y = pressure, color = boundary, linetype = boundary),
    linewidth = 1.2
  ) +
  geom_point(
    data = df_special,
    aes(x = temperature, y = pressure),
    shape = 21, size = 4.5,
    fill = ELEVATED_BG, color = INK, stroke = 1.5
  ) +
  # Phase region labels
  annotate("text", x = 168, y = 80,   label = "SOLID",
           color = INK_MUTED, size = 4.0, fontface = "bold") +
  annotate("text", x = 268, y = 50,   label = "LIQUID",
           color = INK_MUTED, size = 4.0, fontface = "bold") +
  annotate("text", x = 300, y = 0.45, label = "GAS",
           color = INK_MUTED, size = 4.0, fontface = "bold") +
  annotate("text", x = 370, y = 600,  label = "SUPERCRITICAL\nFLUID",
           color = INK_MUTED, size = 3.5, fontface = "bold", lineheight = 0.9) +
  # Special point annotations
  annotate("text", x = 221, y = 12,
           label = "Triple Point\n(216.6 K, 5.2 atm)",
           color = INK_SOFT, size = 3.2, hjust = 0, lineheight = 0.9) +
  annotate("text", x = 308, y = 120,
           label = "Critical Point\n(304.1 K, 72.8 atm)",
           color = INK_SOFT, size = 3.2, hjust = 0, lineheight = 0.9) +
  scale_y_log10(
    name   = "Pressure (atm)",
    limits = c(0.001, 2000),
    breaks = c(0.001, 0.01, 0.1, 1, 10, 100, 1000),
    labels = c("0.001", "0.01", "0.1", "1", "10", "100", "1000")
  ) +
  scale_x_continuous(
    name   = "Temperature (K)",
    limits = c(130, 415),
    breaks = seq(150, 400, by = 50)
  ) +
  scale_color_manual(
    values = c(
      "Solid-Liquid" = IMPRINT_PALETTE[1],
      "Liquid-Gas"   = IMPRINT_PALETTE[2],
      "Solid-Gas"    = IMPRINT_PALETTE[3]
    ),
    name = "Phase Boundary"
  ) +
  scale_linetype_manual(
    values = c(
      "Solid-Liquid" = "solid",
      "Liquid-Gas"   = "solid",
      "Solid-Gas"    = "dashed"
    ),
    name = "Phase Boundary"
  ) +
  labs(title = title_str) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG,    color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG,    color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.4),
    panel.grid.minor  = element_line(color = GRID_COLOR, linewidth = 0.2),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT,  linewidth = 0.5),
    axis.title        = element_text(color = INK,       size = 10),
    axis.text         = element_text(color = INK_SOFT,  size = 8),
    plot.title        = element_text(color = INK,       size = 12, face = "bold",
                                     margin = margin(b = 8)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,  size = 8),
    legend.title      = element_text(color = INK,       size = 10),
    legend.position   = "right",
    legend.margin     = margin(6, 8, 6, 8),
    plot.margin       = margin(12, 15, 12, 10)
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
