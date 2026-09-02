#' anyplot.ai
#' cat-box-strip: Box Plot with Strip Overlay
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-09-02

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
BRAND    <- "#009E73"  # Imprint palette position 1 — always first series

# --- Data -----------------------------------------------------------------
fertilizers <- c("Control", "Nitrogen", "Phosphorus", "Compost")
n_per_group <- 60

growth_df <- bind_rows(lapply(fertilizers, function(fertilizer) {
  base <- switch(fertilizer,
    Control    = 18,
    Nitrogen   = 27,
    Phosphorus = 22,
    Compost    = 25
  )
  spread <- switch(fertilizer,
    Control    = 3.5,
    Nitrogen   = 5.0,
    Phosphorus = 4.0,
    Compost    = 4.5
  )
  data.frame(
    fertilizer  = fertilizer,
    plant_height = rnorm(n_per_group, mean = base, sd = spread)
  )
}))

growth_df$fertilizer <- factor(growth_df$fertilizer, levels = fertilizers)

# --- Plot -------------------------------------------------------------------
title_text <- "cat-box-strip · r · ggplot2 · anyplot.ai"

p <- ggplot(growth_df, aes(x = fertilizer, y = plant_height)) +
  geom_boxplot(
    color = INK_SOFT,
    fill = NA,
    outlier.shape = NA,
    linewidth = 0.5,
    width = 0.5
  ) +
  geom_jitter(
    width = 0.15,
    height = 0,
    size = 2.2,
    alpha = 0.45,
    color = BRAND,
    stroke = 0
  ) +
  labs(
    title = title_text,
    x = "Fertilizer Treatment",
    y = "Plant Height (cm)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.2),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "plain"),
    legend.position   = "none"
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
