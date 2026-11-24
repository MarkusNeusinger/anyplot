#' anyplot.ai
#' violin-swarm: Violin Plot with Overlaid Swarm Points
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Columns ----------------------------------------------------------------
CONDITION     <- "Experimental condition"  # role: category
REACTION_TIME <- "Reaction time (ms)"      # role: value

# --- Data -------------------------------------------------------------------
set.seed(42)
df <- tibble::tibble(
  !!CONDITION := rep(c("Control", "Treatment A", "Treatment B", "Treatment C"),
                     each = 60),
  !!REACTION_TIME := c(
    rnorm(60, mean = 350, sd = 50),
    rnorm(60, mean = 320, sd = 45),
    rnorm(60, mean = 300, sd = 55),
    rnorm(60, mean = 310, sd = 48)
  )
)

# --- Plot -------------------------------------------------------------------
df <- df |> mutate(across(all_of(CONDITION), \(v) factor(v, levels = unique(v))))

# Swarm layout: each point sits at its value; only its sideways offset is
# computed, centred on the violin axis and capped by the violin's half-width.
VIOLIN_WIDTH <- 0.8
swarm_offsets <- function(y, half_width_at, spacing_x = 0.05, spacing_y = diff(range(y)) / 28) {
  ord <- order(y)
  x_off <- numeric(length(y))
  placed <- integer(0)
  for (i in ord) {
    limit <- half_width_at(y[i])
    candidates <- c(0, as.vector(rbind(1, -1)) * rep(seq_len(40), each = 2) * spacing_x * 0.5)
    candidates <- candidates[abs(candidates) <= limit]
    for (cand in candidates) {
      dist <- sqrt(((x_off[placed] - cand) / spacing_x)^2 + ((y[placed] - y[i]) / spacing_y)^2)
      if (length(placed) == 0 || all(dist >= 1)) { x_off[i] <- cand; break }
      x_off[i] <- cand
    }
    placed <- c(placed, i)
  }
  x_off
}

df$swarm_x <- NA_real_
for (lv in levels(df[[CONDITION]])) {
  idx <- which(df[[CONDITION]] == lv)
  y <- df[[REACTION_TIME]][idx]
  dens <- density(y)  # same default bandwidth as geom_violin
  half_width_at <- function(v) {
    VIOLIN_WIDTH / 2 * approx(dens$x, dens$y, xout = v, rule = 2)$y / max(dens$y) * 0.92
  }
  df$swarm_x[idx] <- as.integer(factor(lv, levels = levels(df[[CONDITION]]))) +
    swarm_offsets(y, half_width_at)
}

p <- ggplot(df, aes(x = .data[[CONDITION]], y = .data[[REACTION_TIME]])) +
  geom_violin(
    fill = IMPRINT_PALETTE[1],
    alpha = 0.35,
    color = INK_SOFT,
    linewidth = 0.4,
    width = VIOLIN_WIDTH,
    scale = "width"
  ) +
  geom_point(
    aes(x = swarm_x),
    color = IMPRINT_PALETTE[1],
    size = 1.6,
    alpha = 0.9
  ) +
  labs(
    title = "violin-swarm · r · ggplot2 · anyplot.ai",
    x = CONDITION,
    y = REACTION_TIME
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12)
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
