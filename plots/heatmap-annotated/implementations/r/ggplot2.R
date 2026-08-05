#' anyplot.ai
#' heatmap-annotated: Annotated Heatmap
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 82/100 | Created: 2026-08-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
LIGHT_TEXT  <- "#FFFDF6"  # near-white overlay text for saturated red/blue cells

# --- Data: correlation matrix of car performance metrics ----------------
metrics <- mtcars %>%
  rename(
    `MPG`      = mpg,
    `Cylinders` = cyl,
    `Displacement` = disp,
    `Horsepower`  = hp,
    `Rear Axle`   = drat,
    `Weight`      = wt,
    `Quarter Mile` = qsec
  )
corr_matrix <- cor(metrics[, c("MPG", "Cylinders", "Displacement", "Horsepower",
                                "Rear Axle", "Weight", "Quarter Mile")])

corr_df <- as.data.frame(as.table(corr_matrix)) %>%
  rename(x = Var1, y = Var2, value = Freq) %>%
  mutate(
    label      = sprintf("%.2f", value),
    text_color = ifelse(abs(value) > 0.35, LIGHT_TEXT, INK)
  )

# --- Plot -----------------------------------------------------------------
p <- ggplot(corr_df, aes(x = x, y = y, fill = value)) +
  geom_tile(color = PAGE_BG, linewidth = 2) +
  geom_text(aes(label = label, color = text_color), size = 3.4, fontface = "bold") +
  scale_fill_gradient2(
    low = "#AE3030", mid = PAGE_BG, high = "#4467A3",
    midpoint = 0, limits = c(-1, 1), name = "Correlation"
  ) +
  scale_color_identity() +
  coord_fixed() +
  scale_x_discrete(position = "top") +
  labs(
    title = "Car Performance Correlations · heatmap-annotated · r · ggplot2 · anyplot.ai",
    x = NULL, y = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.text.x       = element_text(color = INK_SOFT, size = 8, angle = 30, hjust = 0),
    axis.text.y       = element_text(color = INK_SOFT, size = 8),
    axis.title        = element_text(color = INK, size = 10),
    plot.title        = element_text(color = INK, size = 11, hjust = 0.5),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.position   = "right",
    plot.margin       = margin(10, 10, 10, 10)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
