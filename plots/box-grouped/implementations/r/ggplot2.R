#' anyplot.ai
#' box-grouped: Grouped Box Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-08-18

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data -----------------------------------------------------------------
departments <- c("Engineering", "Sales", "Marketing", "Support")
levels_exp  <- c("Junior", "Mid", "Senior")

dept_baseline <- c(Engineering = 62, Sales = 58, Marketing = 55, Support = 60)
level_shift   <- c(Junior = -8, Mid = 0, Senior = 9)
level_spread  <- c(Junior = 9, Mid = 8, Senior = 7)
n_per_group   <- 70

df <- expand.grid(
  department = departments,
  experience = levels_exp,
  stringsAsFactors = FALSE
) %>%
  mutate(
    mean_score = dept_baseline[department] + level_shift[experience],
    sd_score   = level_spread[experience]
  ) %>%
  rowwise() %>%
  mutate(score = list(rnorm(n_per_group, mean = mean_score, sd = sd_score))) %>%
  ungroup() %>%
  unnest(score) %>%
  transmute(
    department = factor(department, levels = departments),
    experience = factor(experience, levels = levels_exp),
    score
  )

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = department, y = score, fill = experience)) +
  geom_boxplot(
    position    = position_dodge(width = 0.75),
    width       = 0.65,
    linewidth   = 0.5,
    color       = INK_SOFT,
    outlier.size  = 1.8,
    outlier.alpha = 0.7
  ) +
  stat_summary(
    mapping     = aes(x = department, y = score, group = experience, shape = "Mean"),
    fun         = mean,
    geom        = "point",
    position    = position_dodge(width = 0.75),
    size        = 2.2,
    stroke      = 0.6,
    color       = INK,
    fill        = PAGE_BG,
    inherit.aes = FALSE
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:3], name = "Experience Level") +
  scale_shape_manual(values = c("Mean" = 23), name = NULL) +
  labs(
    title = "box-grouped · r · ggplot2 · anyplot.ai",
    x     = "Department",
    y     = "Productivity Score"
  ) +
  guides(
    fill  = guide_legend(order = 1),
    shape = guide_legend(order = 2)
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.y  = element_line(color = INK_SOFT, linewidth = 0.15),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    axis.ticks          = element_blank(),
    plot.title          = element_text(color = INK, size = 12, face = "bold"),
    legend.position       = "top",
    legend.justification  = "right",
    legend.background    = element_rect(fill = PAGE_BG, color = NA),
    legend.key           = element_rect(fill = PAGE_BG, color = NA),
    legend.text          = element_text(color = INK_SOFT, size = 8),
    legend.title         = element_text(color = INK, size = 9)
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
