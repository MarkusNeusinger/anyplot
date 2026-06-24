#' anyplot.ai
#' line-stress-strain: Engineering Stress-Strain Curve
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-06-21

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

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green (first series)
  "#C475FD",  # 2 — lavender
  "#4467A3",  # 3 — blue
  "#BD8233",  # 4 — ochre
  "#AE3030",  # 5 — matte red
  "#2ABCCD",  # 6 — cyan
  "#954477",  # 7 — rose
  "#99B314"   # 8 — lime
)

GRID_COLOR <- adjustcolor(INK, alpha.f = 0.12)

# --- Mild Steel (AISI 1020): elastic + Luders plateau + hardening + necking ---
E_steel        <- 200000  # Young's modulus (MPa)
eps_y_steel    <- 0.00125  # upper yield strain
sig_y_upper    <- 250      # upper yield strength (MPa)
sig_y_lower    <- 228      # lower yield / Luders plateau (MPa)
eps_plateau    <- 0.016    # end of Luders plateau
sig_uts_steel  <- 410      # ultimate tensile strength (MPa)
eps_uts_steel  <- 0.200    # strain at UTS
sig_frac_steel <- 355      # engineering stress at fracture (MPa)
eps_frac_steel <- 0.350    # fracture strain

t_e   <- seq(0, 1, length.out = 40)
eps_e1 <- t_e * eps_y_steel
sig_e1 <- E_steel * eps_e1

t_p   <- seq(0, 1, length.out = 70)
eps_p1 <- eps_y_steel + t_p * (eps_plateau - eps_y_steel)
sig_p1 <- sig_y_upper + (sig_y_lower - sig_y_upper) * (1 - exp(-12 * t_p)) / (1 - exp(-12))

t_h   <- seq(0, 1, length.out = 130)
eps_h1 <- eps_plateau + t_h * (eps_uts_steel - eps_plateau)
sig_h1 <- sig_y_lower + (sig_uts_steel - sig_y_lower) * t_h^0.40

t_n   <- seq(0, 1, length.out = 80)
eps_n1 <- eps_uts_steel + t_n * (eps_frac_steel - eps_uts_steel)
sig_n1 <- sig_uts_steel - (sig_uts_steel - sig_frac_steel) * t_n^0.35

steel <- data.frame(
  strain     = c(eps_e1, eps_p1, eps_h1, eps_n1),
  stress_mpa = c(sig_e1, sig_p1, sig_h1, sig_n1),
  material   = "Mild Steel (AISI 1020)"
)

# --- Aluminum 6061-T6: smooth curve, 0.2% offset yield ---
E_al       <- 69000   # Young's modulus (MPa)
sig_02     <- 276     # 0.2% offset yield strength (MPa)
eps_el_al  <- sig_02 / E_al        # elastic limit strain ~0.004
eps_02_al  <- eps_el_al + 0.002    # yield strain via 0.2% offset ~0.006
sig_uts_al  <- 310
eps_uts_al  <- 0.12
sig_frac_al <- 285
eps_frac_al <- 0.17

eps_al <- seq(0, eps_frac_al, length.out = 250)
sig_al <- ifelse(
  eps_al <= eps_el_al,
  E_al * eps_al,
  pmin(
    sig_02 + (sig_uts_al - sig_02) *
      ((eps_al - eps_el_al) / (eps_uts_al - eps_el_al))^0.38,
    sig_uts_al
  )
)
is_neck_al <- eps_al > eps_uts_al
sig_al[is_neck_al] <- sig_uts_al - (sig_uts_al - sig_frac_al) *
  ((eps_al[is_neck_al] - eps_uts_al) / (eps_frac_al - eps_uts_al))^0.55

alum <- data.frame(
  strain     = eps_al,
  stress_mpa = pmax(0, sig_al),
  material   = "Aluminum 6061-T6"
)

# Combined
df <- rbind(steel, alum)
df$material <- factor(df$material,
                      levels = c("Mild Steel (AISI 1020)", "Aluminum 6061-T6"))

# --- 0.2% offset line for aluminum ---
offset_df <- data.frame(
  strain     = c(0.002, eps_02_al),
  stress_mpa = E_al * c(0.002 - 0.002, eps_02_al - 0.002)
)

# --- Critical points (yield, UTS, fracture for both materials) ---
crit <- data.frame(
  strain = c(
    eps_y_steel,   eps_uts_steel,   eps_frac_steel,
    eps_02_al,     eps_uts_al,      eps_frac_al
  ),
  stress_mpa = c(
    sig_y_upper,   sig_uts_steel,   sig_frac_steel,
    sig_02,        sig_uts_al,      sig_frac_al
  ),
  material = factor(
    c(
      "Mild Steel (AISI 1020)", "Mild Steel (AISI 1020)", "Mild Steel (AISI 1020)",
      "Aluminum 6061-T6",       "Aluminum 6061-T6",       "Aluminum 6061-T6"
    ),
    levels = c("Mild Steel (AISI 1020)", "Aluminum 6061-T6")
  )
)

plot_title <- "line-stress-strain · r · ggplot2 · anyplot.ai"

# --- Plot ---
p <- ggplot(df, aes(x = strain, y = stress_mpa, color = material)) +
  geom_line(linewidth = 1.2) +
  # 0.2% offset dashed line (aluminum)
  geom_line(
    data        = offset_df,
    aes(x = strain, y = stress_mpa),
    color       = INK_SOFT,
    linetype    = "dashed",
    linewidth   = 0.8,
    inherit.aes = FALSE
  ) +
  # Critical points
  geom_point(
    data        = crit,
    aes(x = strain, y = stress_mpa, color = material),
    size        = 3.5,
    shape       = 21,
    fill        = PAGE_BG,
    stroke      = 1.5,
    inherit.aes = FALSE
  ) +
  scale_color_manual(
    values = c(
      "Mild Steel (AISI 1020)" = IMPRINT_PALETTE[1],
      "Aluminum 6061-T6"       = IMPRINT_PALETTE[2]
    )
  ) +
  # Region boundary vertical guidelines
  annotate("segment",
    x = eps_plateau, xend = eps_plateau, y = 0, yend = 440,
    color = INK_MUTED, linetype = "dotted", linewidth = 0.5
  ) +
  annotate("segment",
    x = eps_uts_steel, xend = eps_uts_steel, y = 0, yend = 440,
    color = INK_MUTED, linetype = "dotted", linewidth = 0.5
  ) +
  # Region labels
  annotate("text",
    x = (0 + eps_plateau) / 2, y = 448,
    label = "Elastic",
    color = INK_MUTED, size = 3.2, fontface = "italic", hjust = 0.5
  ) +
  annotate("text",
    x = (eps_plateau + eps_uts_steel) / 2, y = 448,
    label = "Strain Hardening",
    color = INK_MUTED, size = 3.2, fontface = "italic", hjust = 0.5
  ) +
  annotate("text",
    x = (eps_uts_steel + eps_frac_steel) / 2, y = 448,
    label = "Necking",
    color = INK_MUTED, size = 3.2, fontface = "italic", hjust = 0.5
  ) +
  # Young's modulus slope indicator (steel, elastic region)
  annotate("segment",
    x = 0, xend = 0.00100, y = 0, yend = 200,
    color = INK_MUTED, linewidth = 1.6
  ) +
  annotate("text",
    x = 0.00110, y = 108,
    label = "E = 200 GPa", color = INK_MUTED,
    size = 2.9, fontface = "italic", hjust = 0
  ) +
  # Steel critical point labels
  annotate("text",
    x = eps_y_steel + 0.004, y = sig_y_upper + 16,
    label = "YS = 250 MPa", color = IMPRINT_PALETTE[1],
    size = 3.0, hjust = 0
  ) +
  annotate("text",
    x = eps_uts_steel - 0.002, y = sig_uts_steel + 16,
    label = "UTS = 410 MPa", color = IMPRINT_PALETTE[1],
    size = 3.0, hjust = 1
  ) +
  annotate("text",
    x = eps_frac_steel - 0.002, y = sig_frac_steel - 26,
    label = "Fracture", color = IMPRINT_PALETTE[1],
    size = 3.0, hjust = 1
  ) +
  # Aluminum: 0.2% offset label + critical point labels
  annotate("text",
    x = 0.0030, y = 16,
    label = "0.2% offset line", color = INK_SOFT,
    size = 2.8, fontface = "italic", hjust = 0
  ) +
  annotate("text",
    x = eps_02_al + 0.004, y = sig_02 - 22,
    label = "0.2% YS = 276 MPa", color = IMPRINT_PALETTE[2],
    size = 3.0, hjust = 0
  ) +
  annotate("text",
    x = eps_uts_al + 0.003, y = sig_uts_al + 16,
    label = "UTS = 310 MPa", color = IMPRINT_PALETTE[2],
    size = 3.0, hjust = 0
  ) +
  annotate("text",
    x = eps_frac_al - 0.002, y = sig_frac_al - 26,
    label = "Fracture", color = IMPRINT_PALETTE[2],
    size = 3.0, hjust = 1
  ) +
  labs(
    title = plot_title,
    x     = "Engineering Strain (mm/mm)",
    y     = "Engineering Stress (MPa)",
    color = "Material"
  ) +
  scale_x_continuous(
    limits = c(0, 0.37),
    expand = expansion(mult = c(0.01, 0.02))
  ) +
  scale_y_continuous(
    limits = c(0, 460),
    expand = expansion(mult = c(0.01, 0.02))
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.ticks        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12, face = "bold",
                                     margin = margin(b = 8)),
    plot.margin       = margin(t = 12, r = 16, b = 10, l = 10),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                     linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 9),
    legend.position        = "inside",
    legend.position.inside = c(0.80, 0.22),
    legend.key.height      = unit(1.0, "lines"),
    legend.margin          = margin(4, 8, 4, 8)
  )

# --- Save ---
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
