#' anyplot.ai
#' coefficient-confidence: Coefficient Plot with Confidence Intervals
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 91/100 | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data -------------------------------------------------------------------
# Simulated housing price regression coefficients with confidence intervals
coefficients <- data.frame(
  variable = c("Square Footage", "Bedrooms", "Bathrooms", "Age",
               "Lot Size", "Garage Spaces", "Distance to School",
               "Property Tax Rate", "Basement Area", "Year Built"),
  coefficient = c(0.85, 0.42, -0.18, -0.15, 0.28, 0.35, -0.52, -0.08, 0.22, 0.12),
  ci_lower = c(0.72, 0.28, -0.35, -0.29, 0.15, 0.21, -0.68, -0.22, 0.08, -0.05),
  ci_upper = c(0.98, 0.56, -0.01, -0.01, 0.41, 0.49, -0.36, 0.06, 0.36, 0.29),
  significant = c(TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, TRUE, FALSE)
) %>%
  # Order by coefficient magnitude (descending)
  arrange(desc(abs(coefficient))) %>%
  mutate(variable = factor(variable, levels = variable))

# --- Plot -------------------------------------------------------------------
p <- ggplot(coefficients, aes(x = coefficient, y = variable,
                              color = significant, fill = significant)) +
  # Reference line at zero
  geom_vline(xintercept = 0, linetype = "solid", color = INK_SOFT,
             linewidth = 0.5, alpha = 0.5) +
  # Confidence interval error bars
  geom_errorbarh(aes(xmin = ci_lower, xmax = ci_upper),
                 height = 0.3, linewidth = 1.2, alpha = 0.8) +
  # Coefficient points
  geom_point(size = 5, alpha = 0.9) +
  # Color scale: significant vs non-significant
  scale_color_manual(
    name = "Statistically Significant",
    values = c("TRUE" = OKABE_ITO[1], "FALSE" = INK_SOFT),
    labels = c("TRUE" = "Yes", "FALSE" = "No")
  ) +
  scale_fill_manual(
    name = "Statistically Significant",
    values = c("TRUE" = OKABE_ITO[1], "FALSE" = INK_SOFT),
    labels = c("TRUE" = "Yes", "FALSE" = "No")
  ) +
  labs(
    title = "coefficient-confidence · r · ggplot2 · anyplot.ai",
    x = "Coefficient Estimate",
    y = "Predictor Variable"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 20),
    axis.text        = element_text(color = INK_SOFT, size = 16),
    axis.text.y      = element_text(color = INK_SOFT, size = 16),
    plot.title       = element_text(color = INK, size = 24, face = "plain"),
    legend.position  = "bottom",
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text      = element_text(color = INK_SOFT, size = 16),
    legend.title     = element_text(color = INK, size = 18)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
