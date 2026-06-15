#' anyplot.ai
#' heatmap-periodic-table: Periodic Table Property Heatmap
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-15

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
TILE_EMPTY  <- if (THEME == "light") "#CCC9C1" else "#3A3A37"

# Imprint sequential colormap: low EN (alkali metals) → high EN (halogens/O)
COL_LOW  <- "#009E73"  # Imprint position 1 — brand green
COL_HIGH <- "#4467A3"  # Imprint position 3 — blue

# --- Element data -----------------------------------------------------------
# 118 elements: atomic number, symbol, period, group, Pauling electronegativity
# f-block (La-Lu, Ac-Lr) listed with period/group matching canonical placement;
# display coordinates will reposition them below the main grid.

elements <- data.frame(
  an = c(
    # Period 1
    1L, 2L,
    # Period 2
    3L, 4L, 5L, 6L, 7L, 8L, 9L, 10L,
    # Period 3
    11L, 12L, 13L, 14L, 15L, 16L, 17L, 18L,
    # Period 4
    19L, 20L, 21L, 22L, 23L, 24L, 25L, 26L, 27L, 28L, 29L, 30L,
    31L, 32L, 33L, 34L, 35L, 36L,
    # Period 5
    37L, 38L, 39L, 40L, 41L, 42L, 43L, 44L, 45L, 46L, 47L, 48L,
    49L, 50L, 51L, 52L, 53L, 54L,
    # Period 6 main — Cs,Ba then Hf-Rn (La pulled to f-block row)
    55L, 56L, 72L, 73L, 74L, 75L, 76L, 77L, 78L, 79L, 80L,
    81L, 82L, 83L, 84L, 85L, 86L,
    # Period 7 main — Fr,Ra then Rf-Og (Ac pulled to f-block row)
    87L, 88L, 104L, 105L, 106L, 107L, 108L, 109L, 110L, 111L, 112L,
    113L, 114L, 115L, 116L, 117L, 118L,
    # Lanthanides (La-Lu, 57-71)
    57L, 58L, 59L, 60L, 61L, 62L, 63L, 64L, 65L, 66L, 67L, 68L, 69L, 70L, 71L,
    # Actinides (Ac-Lr, 89-103)
    89L, 90L, 91L, 92L, 93L, 94L, 95L, 96L, 97L, 98L, 99L, 100L, 101L, 102L, 103L
  ),
  symbol = c(
    "H", "He",
    "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn",
    "Fr", "Ra", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn",
    "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
    "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"
  ),
  period = c(
    1L, 1L,
    2L, 2L, 2L, 2L, 2L, 2L, 2L, 2L,
    3L, 3L, 3L, 3L, 3L, 3L, 3L, 3L,
    4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L, 4L,
    5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L, 5L,
    6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L,
    7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L,
    6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L, 6L,
    7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L, 7L
  ),
  grp = c(
    1L, 18L,
    1L, 2L, 13L, 14L, 15L, 16L, 17L, 18L,
    1L, 2L, 13L, 14L, 15L, 16L, 17L, 18L,
    1L, 2L, 3L, 4L, 5L, 6L, 7L, 8L, 9L, 10L, 11L, 12L, 13L, 14L, 15L, 16L, 17L, 18L,
    1L, 2L, 3L, 4L, 5L, 6L, 7L, 8L, 9L, 10L, 11L, 12L, 13L, 14L, 15L, 16L, 17L, 18L,
    1L, 2L, 4L, 5L, 6L, 7L, 8L, 9L, 10L, 11L, 12L, 13L, 14L, 15L, 16L, 17L, 18L,
    1L, 2L, 4L, 5L, 6L, 7L, 8L, 9L, 10L, 11L, 12L, 13L, 14L, 15L, 16L, 17L, 18L,
    3L, 4L, 5L, 6L, 7L, 8L, 9L, 10L, 11L, 12L, 13L, 14L, 15L, 16L, 17L,
    3L, 4L, 5L, 6L, 7L, 8L, 9L, 10L, 11L, 12L, 13L, 14L, 15L, 16L, 17L
  ),
  en = c(
    # Period 1
    2.20, NA_real_,
    # Period 2
    0.98, 1.57, 2.04, 2.55, 3.04, 3.44, 3.98, NA_real_,
    # Period 3
    0.93, 1.31, 1.61, 1.90, 2.19, 2.58, 3.16, NA_real_,
    # Period 4
    0.82, 1.00, 1.36, 1.54, 1.63, 1.66, 1.55, 1.83, 1.88, 1.91, 1.90, 1.65,
    1.81, 2.01, 2.18, 2.55, 2.96, 3.00,
    # Period 5
    0.82, 0.95, 1.22, 1.33, 1.60, 2.16, 1.90, 2.20, 2.28, 2.20, 1.93, 1.69,
    1.78, 1.96, 2.05, 2.10, 2.66, 2.60,
    # Period 6 main (Cs,Ba,Hf-Rn)
    0.79, 0.89, 1.30, 1.50, 2.36, 1.90, 2.20, 2.20, 2.28, 2.54, 2.00,
    1.62, 2.33, 2.02, 2.00, 2.20, NA_real_,
    # Period 7 main (Fr,Ra,Rf-Og — most unknown)
    0.70, 0.90, NA_real_, NA_real_, NA_real_, NA_real_, NA_real_, NA_real_,
    NA_real_, NA_real_, NA_real_, NA_real_, NA_real_, NA_real_, NA_real_,
    NA_real_, NA_real_,
    # Lanthanides (La-Lu)
    1.10, 1.12, 1.13, 1.14, NA_real_, 1.17, NA_real_, 1.20, NA_real_,
    1.22, 1.23, 1.24, 1.25, NA_real_, 1.27,
    # Actinides (Ac-Lr)
    1.10, 1.30, 1.50, 1.38, 1.36, 1.28, 1.13, 1.28, 1.30, 1.30, 1.30,
    1.30, 1.30, 1.30, NA_real_
  ),
  stringsAsFactors = FALSE
)

# --- Display coordinates ----------------------------------------------------
# y = -period so period 1 appears at top; f-block rows pushed below with gap
elements$dx <- as.numeric(elements$grp)
elements$dy <- -as.numeric(elements$period)

# Reposition lanthanides (57-71) to y = -8.5
elements$dy[elements$an >= 57L & elements$an <= 71L] <- -8.5
# Reposition actinides (89-103) to y = -9.5
elements$dy[elements$an >= 89L & elements$an <= 103L] <- -9.5

# Placeholder tiles at (period 6, group 3) and (period 7, group 3) for La*/Ac*
placeholders <- data.frame(
  an = NA_integer_, symbol = c("†", "‡"),
  period = c(6L, 7L), grp = c(3L, 3L), en = NA_real_,
  dx = c(3, 3), dy = c(-6, -7),
  stringsAsFactors = FALSE
)
elements <- rbind(elements, placeholders)

# Text color: near-white on gradient tiles, muted on empty/unknown tiles
elements$txt_col <- ifelse(is.na(elements$en), INK_MUTED, "#F0EFE8")

# --- Plot -------------------------------------------------------------------
title_str <- "heatmap-periodic-table · r · ggplot2 · anyplot.ai"

p <- ggplot(elements, aes(x = dx, y = dy)) +

  # Base tiles (NA values get TILE_EMPTY fill via na.value)
  geom_tile(aes(fill = en), width = 0.90, height = 0.90,
            color = PAGE_BG, linewidth = 0.4) +

  # Element symbols — centered in tile
  geom_text(aes(label = symbol, color = txt_col),
            size = 2.2, fontface = "bold", vjust = 0.4) +

  # Atomic numbers — top-left corner of tile (skip placeholders with NA an)
  geom_text(
    data = subset(elements, !is.na(an)),
    aes(x = dx - 0.37, y = dy + 0.30, label = an, color = txt_col),
    size = 0.9, hjust = 0, vjust = 1
  ) +

  # EN value label — bottom of tile (only for elements with known values)
  geom_text(
    data = subset(elements, !is.na(en)),
    aes(x = dx, y = dy - 0.27, label = sprintf("%.2f", en)),
    color = "#F0EFE8", size = 0.75, vjust = 0
  ) +

  # Imprint sequential colormap for continuous EN data
  scale_fill_gradient(
    low      = COL_LOW,
    high     = COL_HIGH,
    na.value = TILE_EMPTY,
    name     = "Electronegativity (Pauling scale)",
    limits   = c(0.7, 4.0),
    breaks   = c(1, 2, 3, 4),
    labels   = c("1.0", "2.0", "3.0", "4.0"),
    guide    = guide_colorbar(
      title.position = "top",
      barwidth       = unit(10, "cm"),
      barheight      = unit(0.35, "cm"),
      label.theme    = element_text(size = 7, color = INK_SOFT),
      title.theme    = element_text(size = 8, color = INK)
    )
  ) +

  scale_color_identity() +

  scale_x_continuous(
    name   = "Group",
    breaks = 1:18,
    labels = as.character(1:18),
    expand = c(0.015, 0.015)
  ) +
  scale_y_continuous(
    name   = "Period",
    breaks = c(-1, -2, -3, -4, -5, -6, -7, -8.5, -9.5),
    labels = c("1", "2", "3", "4", "5", "6", "7", "Ln", "An"),
    expand = c(0.04, 0.04)
  ) +

  labs(title = title_str) +

  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title.x      = element_text(color = INK, size = 9),
    axis.title.y      = element_text(color = INK, size = 9),
    axis.text.x       = element_text(color = INK_SOFT, size = 7),
    axis.text.y       = element_text(color = INK_SOFT, size = 7),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "bold",
                                     margin = margin(b = 8)),
    plot.margin       = margin(t = 10, r = 10, b = 10, l = 10),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 7),
    legend.title      = element_text(color = INK, size = 8),
    legend.position   = "bottom",
    legend.direction  = "horizontal",
    legend.margin     = margin(t = 4)
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
