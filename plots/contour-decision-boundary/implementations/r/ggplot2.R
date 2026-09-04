#' anyplot.ai
#' contour-decision-boundary: Decision Boundary Classifier Visualization
#' Library: ggplot2 | R 4.4.1
#' Quality: pending | Created: 2026-09-04

library(ggplot2)
library(dplyr)
library(class)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — first 3 categorical slots (one per species)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3")

# --- Data ----------------------------------------------------------------
# Iris petal measurements: a real, well-separated 3-class dataset for a
# k-nearest-neighbors decision surface.
train_df <- tibble::tibble(
  petal_length = iris$Petal.Length,
  petal_width  = iris$Petal.Width,
  species      = iris$Species
)

# Dense mesh grid spanning the feature space, for the decision surface
grid_res <- 150
x_range  <- range(train_df$petal_length)
y_range  <- range(train_df$petal_width)
x_pad    <- diff(x_range) * 0.08
y_pad    <- diff(y_range) * 0.08

grid_df <- expand.grid(
  petal_length = seq(x_range[1] - x_pad, x_range[2] + x_pad, length.out = grid_res),
  petal_width  = seq(y_range[1] - y_pad, y_range[2] + y_pad, length.out = grid_res)
)

k_neighbors <- 9
grid_df$predicted <- class::knn(
  train = train_df[, c("petal_length", "petal_width")],
  test  = grid_df[, c("petal_length", "petal_width")],
  cl    = train_df$species,
  k     = k_neighbors
)

# Leave-one-out predictions on the training points flag misclassifications
train_df$predicted <- class::knn.cv(
  train = train_df[, c("petal_length", "petal_width")],
  cl    = train_df$species,
  k     = k_neighbors
)
train_df$status <- ifelse(
  train_df$predicted == train_df$species,
  "Correctly classified",
  "Misclassified"
)

# --- Plot ----------------------------------------------------------------
title_text <- "Iris Species by Petal Size · contour-decision-boundary · r · ggplot2 · anyplot.ai"

p <- ggplot() +
  geom_raster(
    data = grid_df,
    aes(x = petal_length, y = petal_width, fill = predicted),
    alpha = 0.32
  ) +
  geom_point(
    data = train_df,
    aes(x = petal_length, y = petal_width, color = species, shape = status),
    size = 2.5, stroke = 0.9
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE, guide = "none") +
  scale_color_manual(values = IMPRINT_PALETTE, name = "Species") +
  scale_shape_manual(
    values = c("Correctly classified" = 16, "Misclassified" = 4),
    name = "Prediction"
  ) +
  labs(
    title = title_text,
    x = "Petal Length (cm)",
    y = "Petal Width (cm)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 10, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.key        = element_rect(fill = PAGE_BG, color = NA)
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
