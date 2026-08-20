#' anyplot.ai
#' heatmap-correlation: Correlation Matrix Heatmap
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-08-20

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME        <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG      <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK          <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT     <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
MIDPOINT     <- PAGE_BG
# Fill colors (imprint_div extremes) are theme-independent, so the label
# color that reads on top of them must be fixed rather than theme-adaptive.
TEXT_ON_FILL <- "#F0EFE8"

# --- Data --------------------------------------------------------------
# Feature correlations among car design/performance attributes (mtcars) -
# a classic multicollinearity-detection scenario before regression modeling.
vars <- c("mpg", "disp", "hp", "drat", "wt", "qsec", "gear", "carb")
display_labels <- c(
  mpg  = "MPG", disp = "Displacement", hp   = "Horsepower", drat = "Axle Ratio",
  wt   = "Weight", qsec = "1/4 Mile Time", gear = "Gears", carb = "Carburetors"
)

cor_matrix <- cor(mtcars[, vars])
cor_matrix[upper.tri(cor_matrix)] <- NA  # mask redundant upper triangle

df <- as.data.frame(cor_matrix) %>%
  mutate(row_var = factor(vars, levels = rev(vars))) %>%
  pivot_longer(cols = -row_var, names_to = "col_var", values_to = "correlation") %>%
  mutate(col_var = factor(col_var, levels = vars)) %>%
  filter(!is.na(correlation))

# --- Plot ----------------------------------------------------------------
title_text <- "heatmap-correlation · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = col_var, y = row_var, fill = correlation)) +
  geom_tile(color = PAGE_BG, linewidth = 3) +
  geom_text(
    aes(label = sprintf("%.2f", correlation), color = abs(correlation) > 0.55),
    size = 3.3, show.legend = FALSE
  ) +
  scale_color_manual(values = c(`TRUE` = TEXT_ON_FILL, `FALSE` = INK), guide = "none") +
  scale_fill_gradient2(
    low = "#AE3030", mid = MIDPOINT, high = "#4467A3",
    midpoint = 0, limits = c(-1, 1), breaks = c(-1, -0.5, 0, 0.5, 1),
    name = "Correlation"
  ) +
  scale_x_discrete(labels = display_labels, expand = c(0, 0)) +
  scale_y_discrete(labels = display_labels, expand = c(0, 0)) +
  coord_fixed() +
  labs(title = title_text, x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid         = element_blank(),
    axis.title         = element_blank(),
    axis.text.x        = element_text(color = INK_SOFT, size = 9, angle = 35, hjust = 1),
    axis.text.y        = element_text(color = INK_SOFT, size = 9),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = 12, margin = margin(b = 14)),
    legend.background  = element_rect(fill = PAGE_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.key.height  = unit(1.6, "cm"),
    plot.margin        = margin(t = 20, r = 20, b = 20, l = 20)
  )

# --- Save ------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
