#' anyplot.ai
#' scatter-regression-polynomial: Scatter Plot with Polynomial Regression
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-08-11

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint categorical palette — 8 hues, theme-independent
IMPRINT_PALETTE <- c(
  "#009E73", # 1 — brand green (ALWAYS first series)
  "#C475FD", # 2 — lavender
  "#4467A3", # 3 — blue (used here for the fitted curve)
  "#BD8233", # 4 — ochre
  "#AE3030", # 5 — matte red
  "#2ABCCD", # 6 — cyan
  "#954477", # 7 — rose
  "#99B314"  # 8 — lime
)

# --- Data -----------------------------------------------------------------
# Nitrogen fertilizer applied to a corn field vs. resulting yield — a classic
# diminishing-returns relationship: yield climbs with more nitrogen, then
# plateaus and declines once over-fertilization sets in (quadratic pattern).
n <- 120
fertilizer_kg_ha <- runif(n, min = 0, max = 300)
noise <- rnorm(n, mean = 0, sd = 0.8)
corn_yield_t_ha <- -0.00018 * fertilizer_kg_ha^2 +
  0.075 * fertilizer_kg_ha +
  2.5 +
  noise

df <- tibble::tibble(
  fertilizer_kg_ha = fertilizer_kg_ha,
  corn_yield_t_ha   = corn_yield_t_ha
)

# Fit the degree-2 polynomial to report R² and the equation coefficients
poly_fit <- lm(corn_yield_t_ha ~ poly(fertilizer_kg_ha, 2, raw = TRUE), data = df)
r_squared <- summary(poly_fit)$r.squared
coefs <- coef(poly_fit)

annotation_label <- paste0(
  sprintf("y = %.5fx² + %.3fx + %.2f", coefs[3], coefs[2], coefs[1]),
  "\n",
  sprintf("R² = %.3f", r_squared)
)
ann_x <- min(df$fertilizer_kg_ha) + 0.03 * diff(range(df$fertilizer_kg_ha))
ann_y <- max(df$corn_yield_t_ha) - 0.02 * diff(range(df$corn_yield_t_ha))

# --- Plot -------------------------------------------------------------------
title_text <- "Corn Yield vs. Nitrogen Fertilizer · scatter-regression-polynomial · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = fertilizer_kg_ha, y = corn_yield_t_ha)) +
  geom_smooth(
    method = "lm",
    formula = y ~ poly(x, 2, raw = TRUE),
    se = TRUE,
    color = IMPRINT_PALETTE[3],
    fill = IMPRINT_PALETTE[3],
    alpha = 0.18,
    linewidth = 1.2
  ) +
  geom_point(color = IMPRINT_PALETTE[1], size = 2.5, alpha = 0.65) +
  annotate(
    "text",
    x = ann_x, y = ann_y,
    label = annotation_label,
    hjust = 0, vjust = 1,
    size = 3.2, lineheight = 1.15,
    color = INK
  ) +
  labs(
    title = title_text,
    x = "Nitrogen Fertilizer (kg/ha)",
    y = "Corn Yield (t/ha)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.15),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 9, face = "bold"),
    plot.margin       = margin(t = 12, r = 20, b = 10, l = 10)
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
