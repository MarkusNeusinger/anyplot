#' anyplot.ai
#' heatmap-basic: Basic Heatmap
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-05-28

library(ggplot2)
library(tidyr)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# Imprint diverging midpoint is theme-adaptive (matches surface for zero-value cells)
DIV_MID     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"

# Data: pairwise correlations across mtcars vehicle performance metrics
data(mtcars)
selected_vars <- c("mpg", "cyl", "disp", "hp", "drat", "wt", "qsec", "gear")
var_labels    <- c("MPG", "Cylinders", "Displacement", "Horsepower",
                   "Rear Axle", "Weight", "1/4 Mile", "Gears")

cor_mat           <- cor(mtcars[, selected_vars])
rownames(cor_mat) <- var_labels
colnames(cor_mat) <- var_labels

cor_df       <- as.data.frame(cor_mat)
cor_df$y_var <- rownames(cor_df)
cor_long     <- pivot_longer(cor_df,
                             cols      = -y_var,
                             names_to  = "x_var",
                             values_to = "correlation")

# Reverse y levels so matrix reads top-left → bottom-right along diagonal
cor_long$x_var <- factor(cor_long$x_var, levels = var_labels)
cor_long$y_var <- factor(cor_long$y_var, levels = rev(var_labels))

plot_title <- "heatmap-basic · r · ggplot2 · anyplot.ai"

# Plot
p <- ggplot(cor_long, aes(x = x_var, y = y_var, fill = correlation)) +
  geom_tile(color = PAGE_BG, linewidth = 0.8) +
  geom_text(aes(label = sprintf("%.2f", correlation)),
            color = INK, size = 3.5) +
  scale_fill_gradient2(
    low      = "#AE3030",
    mid      = DIV_MID,
    high     = "#4467A3",
    midpoint = 0,
    limits   = c(-1, 1),
    name     = "r"
  ) +
  coord_fixed() +
  labs(title = plot_title, x = NULL, y = NULL) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.border      = element_rect(color = INK_SOFT, fill = NA, linewidth = 0.5),
    panel.grid        = element_blank(),
    axis.text.x       = element_text(color = INK_SOFT, size = 9,
                                     angle = 35, hjust = 1),
    axis.text.y       = element_text(color = INK_SOFT, size = 9),
    plot.title        = element_text(color = INK, size = 12, face = "bold",
                                     margin = margin(b = 10)),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                     linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    plot.margin       = margin(20, 20, 20, 20)
  )

# Save — square canvas (2400×2400 px = 6in × 6in @ 400 dpi)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
