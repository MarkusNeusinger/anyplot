#' anyplot.ai
#' pyramid-basic: Basic Pyramid Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_MALE   <- "#4467A3"  # Imprint palette position 3 — blue (sky/male convention)
IMPRINT_FEMALE <- "#954477"  # Imprint palette position 7 — rose (wellness/female convention)

# --- Data --------------------------------------------------------------------
age_groups <- c(
  "0-9", "10-19", "20-29", "30-39", "40-49",
  "50-59", "60-69", "70-79", "80+"
)

df <- tibble::tibble(
  category    = factor(age_groups, levels = age_groups),
  value_left  = c(4.8, 5.1, 4.6, 4.2, 4.4, 4.0, 3.1, 1.9, 0.9),
  value_right = c(4.6, 4.9, 4.5, 4.3, 4.6, 4.3, 3.4, 2.3, 1.3)
) %>%
  mutate(value_left = -value_left)

plot_df <- df %>%
  pivot_longer(
    cols = c(value_left, value_right),
    names_to = "side",
    values_to = "population"
  ) %>%
  mutate(
    side = factor(side,
      levels = c("value_left", "value_right"),
      labels = c("Male", "Female")
    )
  )

axis_limit <- max(abs(df$value_left), df$value_right) * 1.15

# --- Plot ---------------------------------------------------------------------
p <- ggplot(plot_df, aes(x = category, y = population, fill = side)) +
  geom_col(width = 0.75) +
  geom_text(
    aes(
      label = sprintf("%.1f", abs(population)),
      hjust = ifelse(population < 0, 1.15, -0.15)
    ),
    size = 2.6, color = INK_SOFT, show.legend = FALSE
  ) +
  coord_flip() +
  scale_y_continuous(
    limits = c(-axis_limit, axis_limit),
    labels = function(x) label_number(accuracy = 1)(abs(x))
  ) +
  scale_fill_manual(values = c("Male" = IMPRINT_MALE, "Female" = IMPRINT_FEMALE)) +
  labs(
    title = "pyramid-basic · r · ggplot2 · anyplot.ai",
    x     = "Age Group",
    y     = "Population (millions)",
    fill  = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_line(color = INK, linewidth = 0.3),
    panel.grid.major.y = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line.x.bottom = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.line.x.top    = element_blank(),
    axis.line.y.left   = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.line.y.right  = element_blank(),
    plot.title         = element_text(color = INK, size = 12),
    legend.position     = "top",
    legend.background   = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title        = element_text(color = INK)
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
