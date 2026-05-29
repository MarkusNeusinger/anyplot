#' anyplot.ai
#' line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-05-29

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data -------------------------------------------------------------------
# 300-sample × 15-feature sensor dataset driven by 3 latent factors,
# giving a realistic PCA scree with a clear elbow around components 5-7
n_obs      <- 300
n_features <- 15

f1 <- rnorm(n_obs)
f2 <- rnorm(n_obs)
f3 <- rnorm(n_obs)

X <- matrix(0, nrow = n_obs, ncol = n_features)
for (i in 1:5)   X[, i] <- f1 * (1.8 - 0.25 * i) + rnorm(n_obs, 0, 0.3)
for (i in 6:10)  X[, i] <- f2 * (1.3 - 0.12 * (i - 5)) + rnorm(n_obs, 0, 0.4)
for (i in 11:15) X[, i] <- f3 * (0.9 - 0.08 * (i - 10)) + rnorm(n_obs, 0, 0.5)

pca      <- prcomp(X, center = TRUE, scale. = TRUE)
var_ind  <- pca$sdev^2 / sum(pca$sdev^2) * 100
var_cum  <- cumsum(var_ind)

df <- data.frame(
  component      = seq_len(n_features),
  individual_pct = var_ind,
  cumulative_pct = var_cum
)

thr90 <- min(which(var_cum >= 90))
thr95 <- min(which(var_cum >= 95))

# Elbow detection: point of maximum perpendicular distance from line
# connecting first and last cumulative-variance values
a_coef <- var_cum[n_features] - var_cum[1]
b_coef <- -(n_features - 1)
c_coef <- (n_features - 1) * var_cum[1] - (var_cum[n_features] - var_cum[1]) * 1
knee_dist <- abs(a_coef * seq_len(n_features) + b_coef * var_cum + c_coef) /
  sqrt(a_coef^2 + b_coef^2)
elbow_pc <- which.max(knee_dist)

# --- Plot -------------------------------------------------------------------
title_str <- "line-pca-variance-cumulative · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = component)) +
  geom_col(aes(y = individual_pct),
           fill = IMPRINT_PALETTE[1], alpha = 0.13, width = 0.65) +
  geom_hline(yintercept = 90, linetype = "dashed",
             color = INK_SOFT, linewidth = 0.55) +
  geom_hline(yintercept = 95, linetype = "dashed",
             color = INK_SOFT, linewidth = 0.55) +
  geom_vline(xintercept = elbow_pc, linetype = "dotted",
             color = IMPRINT_PALETTE[1], linewidth = 0.65, alpha = 0.55) +
  geom_line(aes(y = cumulative_pct),
            color = IMPRINT_PALETTE[1], linewidth = 1.2) +
  geom_point(aes(y = cumulative_pct),
             color = IMPRINT_PALETTE[1], size = 2.8) +
  annotate("text", x = 1.2, y = 91.8,
           label = "90%", color = INK_MUTED, size = 3.3, hjust = 0) +
  annotate("text", x = 1.2, y = 96.8,
           label = "95%", color = INK_MUTED, size = 3.3, hjust = 0) +
  annotate("text", x = thr90 + 0.3, y = 85,
           label = sprintf("PC%d\n90%%", thr90),
           color = INK_MUTED, size = 3.0, hjust = 0, lineheight = 0.9) +
  annotate("text", x = elbow_pc + 0.35, y = 5,
           label = sprintf("PC%d\nelbow", elbow_pc),
           color = IMPRINT_PALETTE[1], size = 3.3, hjust = 0, lineheight = 0.9) +
  scale_x_continuous(breaks = seq_len(n_features)) +
  scale_y_continuous(
    limits = c(0, 105),
    breaks = seq(0, 100, 20),
    labels = function(x) paste0(x, "%")
  ) +
  labs(
    x     = "Number of Principal Components",
    y     = "Cumulative Explained Variance",
    title = title_str
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.18),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.border       = element_blank(),
    axis.line          = element_line(color = INK_SOFT, linewidth = 0.45),
    axis.ticks         = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12, face = "bold",
                                      margin = margin(b = 14)),
    plot.margin        = margin(22, 24, 18, 18)
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
