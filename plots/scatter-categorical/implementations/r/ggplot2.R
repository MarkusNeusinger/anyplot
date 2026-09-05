#' anyplot.ai
#' scatter-categorical: Categorical Scatter Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 83/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)
library(palmerpenguins)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — first 3 categorical series (see prompts/default-style-guide.md)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3")

# --- Data ---------------------------------------------------------------
df <- penguins %>%
  filter(!is.na(bill_length_mm), !is.na(flipper_length_mm)) %>%
  mutate(species = as.character(species))

# --- Plot -----------------------------------------------------------------
title_text <- "scatter-categorical · r · ggplot2 · anyplot.ai"

# Grid lines blended toward the background instead of full-strength INK
# (ggplot2 does not expose grid alpha directly, so pre-mix the color).
GRID_COLOR <- grDevices::adjustcolor(INK, alpha.f = 0.2)

p <- ggplot(df, aes(x = bill_length_mm, y = flipper_length_mm, color = species, fill = species)) +
  stat_ellipse(linewidth = 0.6, alpha = 0.6, level = 0.68, show.legend = FALSE) +
  geom_point(shape = 21, color = "white", stroke = 0.3, size = 2.5, alpha = 0.85) +
  scale_color_manual(values = IMPRINT_PALETTE, guide = "none") +
  scale_fill_manual(values = IMPRINT_PALETTE, name = "Species") +
  labs(
    title = title_text,
    x = "Bill Length (mm)",
    y = "Flipper Length (mm)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "plain"),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.key        = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10)
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
