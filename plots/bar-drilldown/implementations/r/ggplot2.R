#' anyplot.ai
#' bar-drilldown: Column Chart with Hierarchical Drilling
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-05-20

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

# --- Theme tokens ---
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- if (THEME == "light") "#D0CFC8" else "#2C2C29"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data: company annual budget hierarchy (department -> expense category) ---
departments <- c("Engineering", "Sales", "Marketing", "Operations")

df <- tibble::tibble(
  department = rep(departments, each = 3),
  item = c(
    "Infrastructure", "R&D", "Tooling",
    "Headcount", "Travel", "CRM Software",
    "Advertising", "Events", "Content",
    "Facilities", "Equipment", "Logistics"
  ),
  budget_m = c(
    1.85, 1.62, 0.73,
    1.55, 0.92, 0.63,
    0.88, 0.61, 0.51,
    0.78, 0.62, 0.40
  )
)

# Compute department totals for strip labels and insight subtitle
dept_totals <- df %>%
  group_by(department) %>%
  summarize(total_m = sum(budget_m), .groups = "drop")

top_dept    <- dept_totals[which.max(dept_totals$total_m), ]
bottom_dept <- dept_totals[which.min(dept_totals$total_m), ]
ratio       <- top_dept$total_m / bottom_dept$total_m

# Strip labels embed each department's total — immediately reveals Engineering's lead
dept_strip_labels <- setNames(
  sprintf("%s  ·  $%.2fM total", dept_totals$department, dept_totals$total_m),
  dept_totals$department
)

# Insight subtitle makes the data story explicit
subtitle_text <- sprintf(
  "%s leads at $%.2fM · %.1f× %s ($%.2fM) · Annual budget by department",
  top_dept$department, top_dept$total_m, ratio,
  bottom_dept$department, bottom_dept$total_m
)

# Order items within each department by budget ascending (bottom-to-top after coord_flip)
df <- df %>%
  group_by(department) %>%
  arrange(budget_m, .by_group = TRUE) %>%
  mutate(bar_emphasis = if_else(budget_m == max(budget_m), "top", "other")) %>%
  ungroup() %>%
  mutate(
    department  = factor(department, levels = departments),
    unique_item = factor(
      paste(department, item, sep = "|"),
      levels = paste(department, item, sep = "|")
    )
  )

dept_colors <- setNames(OKABE_ITO[1:4], departments)

# --- Plot ---
p <- ggplot(df, aes(x = unique_item, y = budget_m, fill = department, alpha = bar_emphasis)) +
  geom_col(width = 0.65, show.legend = FALSE) +
  geom_text(
    aes(label = sprintf("$%.2fM", budget_m)),
    hjust   = -0.1,
    size    = 3.3,
    color   = INK_SOFT
  ) +
  facet_wrap(~department, scales = "free", ncol = 2,
             labeller = as_labeller(dept_strip_labels)) +
  scale_x_discrete(labels = function(x) sub(".*\\|", "", x)) +
  scale_y_continuous(
    labels = function(x) sprintf("$%.1fM", x),
    expand = expansion(mult = c(0, 0.48))
  ) +
  scale_fill_manual(values = dept_colors) +
  scale_alpha_manual(values = c("top" = 1.0, "other" = 0.72), guide = "none") +
  coord_flip() +
  labs(
    title    = "Department Budget Breakdown · bar-drilldown · r · ggplot2 · anyplot.ai",
    subtitle = subtitle_text,
    x        = NULL,
    y        = "Budget (USD millions)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(color = GRID_COLOR, linewidth = 0.15),
    panel.grid.minor   = element_blank(),
    axis.title.x       = element_text(color = INK, size = 10),
    axis.title.y       = element_blank(),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    strip.text         = element_text(color = INK, size = 10, face = "bold"),
    strip.background   = element_rect(fill = ELEVATED_BG, color = NA),
    plot.title         = element_text(color = INK, size = 11),
    plot.subtitle      = element_text(color = INK_SOFT, size = 8.5),
    panel.spacing.x    = unit(2, "lines"),
    panel.spacing.y    = unit(1.5, "lines"),
    plot.margin        = margin(15, 15, 10, 10)
  )

# --- Save ---
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
