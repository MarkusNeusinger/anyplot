#' anyplot.ai
#' coefficient-confidence: Coefficient Plot with Confidence Intervals
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

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
             linewidth = 0.4, alpha = 0.7) +
  # Confidence interval error bars
  geom_errorbar(aes(xmin = ci_lower, xmax = ci_upper), orientation = "y",
                width = 0.3, linewidth = 0.7, alpha = 0.8) +
  # Coefficient points
  geom_point(size = 3, alpha = 0.9) +
  # Color scale: significant vs non-significant
  scale_color_manual(
    name = "Statistically Significant",
    values = c("TRUE" = IMPRINT[1], "FALSE" = INK_SOFT),
    labels = c("TRUE" = "Yes", "FALSE" = "No")
  ) +
  scale_fill_manual(
    name = "Statistically Significant",
    values = c("TRUE" = IMPRINT[1], "FALSE" = INK_SOFT),
    labels = c("TRUE" = "Yes", "FALSE" = "No")
  ) +
  labs(
    title = "coefficient-confidence · r · ggplot2 · anyplot.ai",
    x = "Coefficient Estimate",
    y = "Predictor Variable"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major = element_line(color = INK, linewidth = 0.1),
    panel.grid.minor = element_blank(),
    axis.title       = element_text(color = INK, size = 10),
    axis.text        = element_text(color = INK_SOFT, size = 8),
    axis.text.y      = element_text(color = INK_SOFT, size = 8),
    plot.title       = element_text(color = INK, size = 12, face = "plain"),
    legend.position  = "bottom",
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text      = element_text(color = INK_SOFT, size = 8),
    legend.title     = element_text(color = INK, size = 10)
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
