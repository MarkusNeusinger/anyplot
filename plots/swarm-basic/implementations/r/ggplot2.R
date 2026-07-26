#' anyplot.ai
#' swarm-basic: Basic Swarm Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-07-26

library(ggplot2)
library(dplyr)
library(ragg)
library(scales)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ----------------------------------------------------------------
# Reaction times across a cognitive-load experiment (psychology research)
conditions <- c("Baseline", "Low Load", "High Load", "Time Pressure")
means <- c(420, 460, 540, 580)
sds   <- c(45, 50, 65, 70)
n_per_condition <- 45

reaction_df <- bind_rows(lapply(seq_along(conditions), function(i) {
  tibble::tibble(
    condition     = conditions[i],
    reaction_time = rnorm(n_per_condition, mean = means[i], sd = sds[i])
  )
})) %>%
  mutate(condition = factor(condition, levels = conditions))

# --- Swarm layout ----------------------------------------------------------
# Bin observations along the value axis, then rank within each bin so
# points that fall close in value are spread symmetrically around the
# category's center line - a lightweight beeswarm approximation built
# entirely from geom_point (ggplot2 has no native beeswarm geom).
bin_width     <- diff(range(reaction_df$reaction_time)) / 24
point_spacing <- 0.05
max_offset    <- 0.42

reaction_df <- reaction_df %>%
  mutate(value_bin = round(reaction_time / bin_width)) %>%
  group_by(condition, value_bin) %>%
  mutate(
    bin_rank = rank(reaction_time, ties.method = "first"),
    bin_n    = n(),
    x_offset = pmin(pmax((bin_rank - (bin_n + 1) / 2) * point_spacing, -max_offset), max_offset)
  ) %>%
  ungroup() %>%
  mutate(condition_x = as.numeric(condition) + x_offset)

condition_means <- reaction_df %>%
  group_by(condition) %>%
  summarise(mean_rt = mean(reaction_time), x_pos = as.numeric(condition[1]), .groups = "drop")

# --- Plot ------------------------------------------------------------------
p <- ggplot(reaction_df, aes(x = condition_x, y = reaction_time)) +
  geom_point(aes(color = condition), size = 2.6, alpha = 0.85) +
  geom_point(
    data = condition_means,
    aes(x = x_pos, y = mean_rt),
    shape = 18, size = 3.4, color = INK, alpha = 0.9
  ) +
  scale_color_manual(values = IMPRINT_PALETTE[seq_along(conditions)], guide = "none") +
  scale_x_continuous(
    breaks = seq_along(conditions),
    labels = conditions,
    expand = expansion(mult = c(0.1, 0.1))
  ) +
  labs(
    title = "swarm-basic · r · ggplot2 · anyplot.ai",
    x = "Experimental Condition",
    y = "Reaction Time (ms)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.y  = element_line(color = scales::alpha(INK, 0.15), linewidth = 0.3),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    axis.ticks          = element_blank(),
    axis.line           = element_line(color = INK_SOFT, linewidth = 0.3),
    plot.title          = element_text(color = INK, size = 12)
  )

# --- Save --------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
