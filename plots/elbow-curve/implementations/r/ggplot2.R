#' anyplot.ai
#' elbow-curve: Elbow Curve for K-Means Clustering
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-05

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data --------------------------------------------------------------------
# Customer segmentation: K-means fit on annual spending / visit-frequency
# features across k = 1..10, tracking within-cluster sum of squares (inertia).
k_values <- 1:10
inertia <- 5200 * exp(-0.55 * (k_values - 1)) + 180 + rnorm(10, mean = 0, sd = 15)

df <- tibble::tibble(k = k_values, inertia = inertia)

# Kneedle-style elbow detection: point of maximum perpendicular distance
# below the chord connecting the first and last (normalized) points.
norm_k <- (df$k - min(df$k)) / (max(df$k) - min(df$k))
norm_inertia <- (df$inertia - min(df$inertia)) / (max(df$inertia) - min(df$inertia))
chord_y <- 1 - norm_k
elbow_idx <- which.max(chord_y - norm_inertia)
elbow_k <- df$k[elbow_idx]
elbow_inertia <- df$inertia[elbow_idx]

# Post-elbow plateau, shaded to sharpen the "diminishing returns" story.
df_plateau <- df[elbow_idx:nrow(df), ]

# --- Plot ----------------------------------------------------------------
p <- ggplot(df, aes(x = k, y = inertia)) +
  geom_ribbon(
    data = df_plateau, aes(ymin = 0, ymax = inertia),
    fill = IMPRINT_PALETTE[1], alpha = 0.12, color = NA
  ) +
  geom_vline(
    xintercept = elbow_k, linetype = "dashed",
    color = INK_SOFT, linewidth = 0.5, alpha = 0.6
  ) +
  geom_line(color = IMPRINT_PALETTE[1], linewidth = 1.1) +
  geom_point(color = IMPRINT_PALETTE[1], size = 3.8) +
  geom_point(
    data = df[elbow_idx, ], shape = 21, size = 5.5,
    fill = IMPRINT_PALETTE[1], color = INK, stroke = 0.8
  ) +
  annotate(
    "text", x = elbow_k + 0.3, y = elbow_inertia + 380,
    label = sprintf("Elbow: k = %d", elbow_k),
    color = INK, size = 3.4, hjust = 0
  ) +
  scale_x_continuous(breaks = k_values) +
  scale_y_continuous(limits = c(0, NA)) +
  labs(
    title = "elbow-curve · r · ggplot2 · anyplot.ai",
    x = "Number of Clusters (k)",
    y = "Inertia (Within-Cluster Sum of Squares)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.25),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 14)
  )

# --- Save ----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
