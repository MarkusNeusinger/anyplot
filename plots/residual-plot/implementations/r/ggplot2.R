#' anyplot.ai
#' residual-plot: Residual Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data --------------------------------------------------------------------
# House price prediction: a simple linear model fit to a mildly non-linear,
# heteroscedastic relationship between square footage and sale price. The
# residual plot exposes both the curvature the linear fit misses and the
# fanning variance that grows with home size.
n <- 220
square_footage <- runif(n, 800, 4200)
noise_scale <- 6000 + square_footage * 12
sale_price <- 45000 + 95 * square_footage + 0.018 * square_footage^2 +
  rnorm(n, mean = 0, sd = noise_scale)

homes <- tibble::tibble(square_footage, sale_price)
model <- lm(sale_price ~ square_footage, data = homes)

homes <- homes %>%
  mutate(
    fitted    = fitted(model),
    residual  = resid(model),
    band      = 2 * sd(residual),
    is_outlier = abs(residual) > band,
    status    = factor(if_else(is_outlier, "Outlier (>2σ)", "Normal"),
                        levels = c("Normal", "Outlier (>2σ)"))
  )

band_width <- unique(homes$band)

# --- Plot ---------------------------------------------------------------
p <- ggplot(homes, aes(x = fitted, y = residual)) +
  geom_hline(yintercept = c(-band_width, band_width),
             linetype = "dashed", linewidth = 0.5, color = INK_SOFT) +
  geom_hline(yintercept = 0, linewidth = 0.8, color = INK) +
  geom_smooth(method = "loess", formula = y ~ x, se = FALSE,
              color = IMPRINT_PALETTE[3], linewidth = 1.0) +
  geom_point(aes(color = status), size = 2.5, alpha = 0.75) +
  scale_color_manual(values = c("Normal" = IMPRINT_PALETTE[1],
                                "Outlier (>2σ)" = IMPRINT_PALETTE[5])) +
  labs(
    title  = "residual-plot · r · ggplot2 · anyplot.ai",
    x      = "Fitted Sale Price ($)",
    y      = "Residual ($)",
    color  = NULL
  ) +
  scale_x_continuous(labels = scales::dollar_format(scale = 1e-3, suffix = "k")) +
  scale_y_continuous(labels = scales::dollar_format(scale = 1e-3, suffix = "k")) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 12),
    legend.position   = "top",
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.key        = element_blank()
  )

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
