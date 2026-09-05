#' anyplot.ai
#' gantt-basic: Basic Gantt Chart
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
# Product launch project plan: phases grouped by workstream.
tasks <- tibble::tribble(
  ~task,                     ~start,       ~end,         ~workstream,
  "Market research",         "2026-01-05", "2026-01-23", "Discovery",
  "Stakeholder interviews",  "2026-01-12", "2026-01-30", "Discovery",
  "Requirements spec",       "2026-01-26", "2026-02-13", "Discovery",
  "UX wireframes",           "2026-02-09", "2026-03-06", "Design",
  "Visual design system",    "2026-02-23", "2026-03-20", "Design",
  "Usability testing",       "2026-03-16", "2026-03-27", "Design",
  "Backend architecture",    "2026-03-02", "2026-03-27", "Engineering",
  "API development",         "2026-03-16", "2026-04-24", "Engineering",
  "Frontend build",          "2026-03-30", "2026-05-08", "Engineering",
  "Integration testing",     "2026-05-04", "2026-05-22", "Engineering",
  "Beta rollout",            "2026-05-18", "2026-06-05", "Launch",
  "Marketing campaign",      "2026-05-25", "2026-06-19", "Launch",
  "General availability",    "2026-06-08", "2026-06-19", "Launch"
) %>%
  mutate(
    start = as.Date(start),
    end   = as.Date(end),
    task  = factor(task, levels = rev(task))
  )

today <- as.Date("2026-04-10")

# --- Plot -----------------------------------------------------------------
n_tasks <- length(levels(tasks$task))

p <- ggplot(tasks, aes(y = task, x = start, xend = end, color = workstream)) +
  geom_segment(aes(xend = end, yend = task), linewidth = 7, lineend = "round") +
  geom_vline(xintercept = today, color = INK_SOFT,
             linewidth = 0.6, linetype = "dashed") +
  annotate("text", x = today, y = n_tasks + 0.9,
           label = "Today", color = INK_SOFT, size = 3, hjust = -0.15) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_x_date(date_labels = "%b %Y", date_breaks = "1 month",
               expand = expansion(mult = c(0.02, 0.08))) +
  scale_y_discrete(expand = expansion(add = c(0.6, 1.3))) +
  guides(color = guide_legend(override.aes = list(linewidth = 5))) +
  labs(
    title = "Product Launch Plan · gantt-basic · r · ggplot2 · anyplot.ai",
    x = "Timeline", y = NULL, color = "Workstream"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_line(color = INK, linewidth = 0.25),
    panel.grid.major.y = element_blank(),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text.x       = element_text(color = INK_SOFT, size = 8),
    axis.text.y       = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, face = "plain"),
    legend.position     = "top",
    legend.background   = element_rect(fill = PAGE_BG, color = NA),
    legend.text         = element_text(color = INK_SOFT, size = 8, margin = margin(r = 14)),
    legend.title        = element_text(color = INK, size = 10, margin = margin(r = 10)),
    legend.key          = element_rect(fill = PAGE_BG, color = NA),
    legend.key.spacing.x = unit(0.4, "cm"),
    legend.margin       = margin(b = 6),
    plot.margin         = margin(12, 20, 8, 8)
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
