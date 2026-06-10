#' anyplot.ai
#' line-yield-curve: Yield Curve (Interest Rate Term Structure)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-06-10

library(ggplot2)
library(scales)
library(ragg)

# Theme tokens (Imprint palette + adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
GRID_COLOR  <- scales::alpha(INK, 0.15)

# Imprint categorical palette — positions 1, 2, 3 for three yield curves
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3")

# Data: U.S. Treasury yield curves on three historically significant dates
maturities     <- c("1M",  "3M",  "6M",  "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y")
maturity_years <- c(1/12, 0.25,  0.5,   1.0,  2.0,  3.0,  5.0,  7.0,  10.0,  20.0,  30.0)

# Jan 2021: Normal steep curve (near-zero short rates, post-pandemic QE)
yields_jan2021 <- c(0.05, 0.06, 0.08, 0.09, 0.12, 0.20, 0.45, 0.80, 1.08, 1.57, 1.83)
# Jul 2023: Deeply inverted (peak of Fed hiking cycle, 5.25-5.50% fed funds)
yields_jul2023 <- c(5.30, 5.43, 5.52, 5.44, 4.87, 4.55, 4.28, 4.18, 3.97, 4.11, 3.96)
# Jan 2024: Still inverted, beginning to normalize
yields_jan2024 <- c(5.52, 5.43, 5.36, 5.12, 4.43, 4.17, 4.00, 4.01, 3.97, 4.35, 4.22)

df <- data.frame(
  maturity       = rep(maturities, 3),
  maturity_years = rep(maturity_years, 3),
  yield_pct      = c(yields_jan2021, yields_jul2023, yields_jan2024),
  curve_date     = factor(
    rep(c("Jan 2021", "Jul 2023", "Jan 2024"), each = length(maturities)),
    levels = c("Jan 2021", "Jul 2023", "Jan 2024")
  )
)

y_top   <- max(df$yield_pct)
y_annot <- y_top + 0.30
plot_title <- "line-yield-curve · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = maturity_years, y = yield_pct, color = curve_date)) +
  # Shade the front-end region (3M–2Y) where 2023–2024 inversion is most prominent
  annotate("rect",
    xmin  = 0.25, xmax = 2.0,
    ymin  = -Inf, ymax = Inf,
    fill  = INK_MUTED, alpha = 0.07
  ) +
  geom_line(linewidth = 1.2, lineend = "round") +
  geom_point(size = 2.5) +
  annotate("text",
    x     = 0.7,   y     = y_annot,
    label = "Inversion zone",
    color = INK_MUTED, size = 2.8, hjust = 0.5, vjust = 0
  ) +
  scale_color_manual(values = IMPRINT_PALETTE, name = NULL) +
  scale_x_log10(
    breaks = maturity_years,
    labels = maturities
  ) +
  scale_y_continuous(
    labels = function(x) sprintf("%.1f%%", x),
    expand = expansion(mult = c(0.05, 0.22))
  ) +
  labs(
    title = plot_title,
    x     = "Maturity",
    y     = "Yield (%)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    panel.border      = element_blank(),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.ticks        = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK,      size = 12, margin = margin(b = 12)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 9),
    legend.title      = element_blank(),
    legend.key.width  = unit(1.5, "cm"),
    legend.position   = "right",
    plot.margin       = margin(20, 20, 20, 20, "pt")
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
