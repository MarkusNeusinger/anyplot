#' anyplot.ai
#' scatter-marginal: Scatter Plot with Marginal Distributions
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-09

library(ggplot2)
library(gridExtra)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]

# --- Data ----------------------------------------------------------------
# Annual rainfall vs. crop yield across 400 farm plots, moderately correlated.
n <- 400
rainfall_mm <- rnorm(n, mean = 800, sd = 150)
crop_yield_t_ha <- 1.5 + 0.0035 * rainfall_mm + rnorm(n, mean = 0, sd = 0.55)
df <- tibble::tibble(rainfall_mm = rainfall_mm, crop_yield_t_ha = crop_yield_t_ha)

x_range <- range(df$rainfall_mm)
y_range <- range(df$crop_yield_t_ha)

# --- Shared chrome ---------------------------------------------------------
anyplot_theme <- theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid       = element_blank(),
    axis.ticks       = element_blank()
  )

# --- Main scatter -----------------------------------------------------------
p_main <- ggplot(df, aes(rainfall_mm, crop_yield_t_ha)) +
  geom_point(color = BRAND, size = 2.4, alpha = 0.6, stroke = 0) +
  coord_cartesian(xlim = x_range, ylim = y_range) +
  labs(x = "Annual Rainfall (mm)", y = "Crop Yield (t/ha)") +
  anyplot_theme +
  theme(
    axis.line   = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.title  = element_text(color = INK, size = 11),
    axis.text   = element_text(color = INK_SOFT, size = 9),
    plot.margin = margin(t = 4, r = 4, b = 10, l = 10)
  )

# --- Top marginal: rainfall distribution ------------------------------------
p_top <- ggplot(df, aes(rainfall_mm)) +
  geom_histogram(aes(y = after_stat(density)), bins = 30,
                  fill = BRAND, color = NA, alpha = 0.3) +
  geom_density(color = BRAND, linewidth = 0.9) +
  coord_cartesian(xlim = x_range) +
  anyplot_theme +
  theme(
    axis.title  = element_blank(),
    axis.text   = element_blank(),
    plot.margin = margin(t = 10, r = 4, b = 2, l = 10)
  )

# --- Right marginal: crop yield distribution, flipped ------------------------
p_right <- ggplot(df, aes(crop_yield_t_ha)) +
  geom_histogram(aes(y = after_stat(density)), bins = 30,
                  fill = BRAND, color = NA, alpha = 0.3) +
  geom_density(color = BRAND, linewidth = 0.9) +
  coord_flip(xlim = y_range) +
  anyplot_theme +
  theme(
    axis.title  = element_blank(),
    axis.text   = element_blank(),
    plot.margin = margin(t = 4, r = 10, b = 10, l = 2)
  )

# --- Align marginal panels to the main scatter's panel geometry -------------
g_main  <- ggplotGrob(p_main)
g_top   <- ggplotGrob(p_top)
g_right <- ggplotGrob(p_right)
g_top$widths    <- g_main$widths
g_right$heights <- g_main$heights

title_grob <- grid::textGrob(
  "scatter-marginal · r · ggplot2 · anyplot.ai",
  x = 0, hjust = 0,
  gp = grid::gpar(col = INK, fontsize = 12, fontface = "plain")
)

composite <- arrangeGrob(
  grobs = list(title_grob, g_top, g_main, g_right),
  layout_matrix = rbind(
    c(1, 1),
    c(2, NA),
    c(3, 4)
  ),
  widths  = c(4, 1),
  heights = c(0.5, 1, 4)
)

# --- Save --------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = composite,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400,
  bg       = PAGE_BG
)
