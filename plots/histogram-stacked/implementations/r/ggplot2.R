#' anyplot.ai
#' histogram-stacked: Stacked Histogram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# ggplot2 exposes no per-element grid alpha, so blend INK to 15% opacity instead
GRID_COLOR  <- scales::alpha(INK, 0.15)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data --------------------------------------------------------------------
# Exam scores for three cohorts sitting the same test, stacked into shared bins
df <- bind_rows(
  tibble::tibble(score = rnorm(600, mean = 68, sd = 9),  cohort = "Freshman"),
  tibble::tibble(score = rnorm(500, mean = 76, sd = 8),  cohort = "Sophomore"),
  tibble::tibble(score = rnorm(400, mean = 83, sd = 7),  cohort = "Senior")
) %>%
  mutate(score = pmin(pmax(score, 0), 100),
         cohort = factor(cohort, levels = c("Freshman", "Sophomore", "Senior")))

cohort_levels <- levels(df$cohort)
shift_note <- sprintf(
  "Scores skew higher across cohorts (%s → %s)",
  cohort_levels[1], cohort_levels[length(cohort_levels)]
)

# --- Plot ---------------------------------------------------------------------
p <- ggplot(df, aes(x = score, fill = cohort)) +
  geom_histogram(binwidth = 4, boundary = 0, color = PAGE_BG, linewidth = 0.3) +
  # Distinctive touch: trace the combined total (stat recomputed across all
  # cohorts, ignoring the fill grouping) so the "total = combined frequency"
  # requirement is visible as a shape, not just implied by the stacking.
  stat_bin(
    data        = df,
    mapping     = aes(x = score, y = after_stat(count)),
    inherit.aes = FALSE,
    binwidth    = 4,
    boundary    = 0,
    geom        = "step",
    direction   = "mid",
    color       = INK,
    linewidth   = 0.5
  ) +
  annotate(
    "text",
    x        = -Inf,
    y        = Inf,
    label    = shift_note,
    hjust    = -0.02,
    vjust     = 1.6,
    size     = 2.8,
    fontface = "italic",
    color    = INK_SOFT
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:3]) +
  scale_x_continuous(expand = expansion(mult = c(0.01, 0.03))) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.1))) +
  labs(
    title = "Exam Scores by Cohort · histogram-stacked · r · ggplot2 · anyplot.ai",
    x = "Exam Score",
    y = "Number of Students",
    fill = "Cohort"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.y  = element_line(color = GRID_COLOR, linewidth = 0.3),
    axis.line           = element_line(color = INK_SOFT),
    axis.ticks          = element_blank(),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    plot.title          = element_text(color = INK, size = 12, face = "plain"),
    legend.position      = "top",
    legend.justification = "right",
    legend.background   = element_rect(fill = PAGE_BG, color = NA),
    legend.key           = element_rect(fill = PAGE_BG, color = NA),
    legend.text          = element_text(color = INK_SOFT, size = 8),
    legend.title         = element_text(color = INK, size = 10),
    plot.margin          = margin(t = 10, r = 22, b = 8, l = 8)
  )

# --- Save ---------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
