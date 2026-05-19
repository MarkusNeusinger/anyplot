#' anyplot.ai
#' mosaic-categorical: Mosaic Plot for Categorical Association Analysis
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-19

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# Data: product category vs customer satisfaction (retail survey, n = 500)
category_levels     <- c("Electronics", "Clothing", "Food", "Books")
satisfaction_levels <- c("Satisfied", "Neutral", "Unsatisfied")

freq_data <- data.frame(
  category     = factor(rep(category_levels, each = 3), levels = category_levels),
  satisfaction = factor(rep(satisfaction_levels, times = 4), levels = satisfaction_levels),
  freq         = c(
    80, 50, 20,  # Electronics: n = 150
    60, 55, 25,  # Clothing:    n = 140
    65, 35, 20,  # Food:        n = 120
    70, 15,  5   # Books:       n = 90
  )
)

# Marginal totals per category — determines column widths
category_totals <- freq_data %>%
  group_by(category) %>%
  summarize(total = sum(freq), .groups = "drop") %>%
  arrange(category) %>%
  mutate(
    width_prop = total / sum(total),
    xmax       = cumsum(width_prop),
    xmin       = lag(xmax, default = 0),
    xmin_plot  = xmin + 0.005,
    xmax_plot  = xmax - 0.005,
    x_center   = (xmin_plot + xmax_plot) / 2
  )

# Conditional heights within each column
plot_data <- freq_data %>%
  left_join(category_totals, by = "category") %>%
  arrange(category, satisfaction) %>%
  group_by(category) %>%
  mutate(
    height_prop = freq / total,
    ymax        = cumsum(height_prop)
  ) %>%
  mutate(
    ymin      = lag(ymax, default = 0),
    ymin_plot = ymin + 0.003,
    ymax_plot = ymax - 0.003
  ) %>%
  ungroup()

# Plot
p <- ggplot(plot_data) +
  geom_rect(
    aes(
      xmin = xmin_plot, xmax = xmax_plot,
      ymin = ymin_plot, ymax = ymax_plot,
      fill = satisfaction
    ),
    color = PAGE_BG, linewidth = 0.6
  ) +
  scale_fill_manual(
    values = setNames(OKABE_ITO[1:3], satisfaction_levels),
    name   = "Customer\nSatisfaction"
  ) +
  scale_x_continuous(
    breaks = category_totals$x_center,
    labels = paste0(category_totals$category, "\n(n = ", category_totals$total, ")"),
    expand = c(0.01, 0.01)
  ) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = c(0.01, 0.01)
  ) +
  labs(
    title = "Customer Satisfaction by Product Category · mosaic-categorical · r · ggplot2 · anyplot.ai",
    x     = "Product Category  (column width proportional to group size)",
    y     = "Proportion of Respondents"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_text(color = INK,      size = 18),
    axis.text.x       = element_text(color = INK_SOFT, size = 14),
    axis.text.y       = element_text(color = INK_SOFT, size = 14),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK,      size = 18, hjust = 0.5),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text       = element_text(color = INK_SOFT, size = 14),
    legend.title      = element_text(color = INK,      size = 16),
    plot.margin       = margin(40, 60, 40, 40)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
