# anyplot.ai
# slope-basic: Basic Slope Chart (Slopegraph)
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Updated: 2026-07-26

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

IMPRINT_INCREASE = colorant"#009E73"  # brand green — gain (semantic exception: positive change)
IMPRINT_DECREASE = colorant"#AE3030"  # matte red — loss (semantic exception: negative change)

# --- Data ----------------------------------------------------------------
# Customer satisfaction score (0-100) for 10 product lines, comparing the
# 2023 and 2024 annual surveys.
products = [
    "Cloud Storage", "Mobile App", "Analytics Suite", "Payment Gateway",
    "Support Chat", "API Platform", "Video Conferencing", "Data Backup",
    "Email Client", "Customer Portal",
]
n = length(products)
score_2023 = round.(rand(n) .* 35 .+ 48, digits=1)
change = round.(randn(n) .* 8, digits=1)
score_2024 = round.(clamp.(score_2023 .+ change, 0, 100), digits=1)

order = sortperm(score_2023, rev=true)
products, score_2023, score_2024 = products[order], score_2023[order], score_2024[order]

y_min, y_max = minimum(vcat(score_2023, score_2024)), maximum(vcat(score_2023, score_2024))
y_pad = (y_max - y_min) * 0.12
ylim_lo, ylim_hi = y_min - y_pad, y_max + y_pad * 2.2

# Nudge label y-positions apart (independent of true marker/line position)
# so entity names don't overlap when two scores land close together.
min_gap = (ylim_hi - ylim_lo) * 0.052

label_y_left = copy(score_2023)
left_order = sortperm(label_y_left)
for _ in 1:200
    moved = false
    for k in 1:(n - 1)
        i, j = left_order[k], left_order[k + 1]
        if label_y_left[j] - label_y_left[i] < min_gap
            center = (label_y_left[i] + label_y_left[j]) / 2
            label_y_left[i] = center - min_gap / 2
            label_y_left[j] = center + min_gap / 2
            moved = true
        end
    end
    moved || break
end

label_y_right = copy(score_2024)
right_order = sortperm(label_y_right)
for _ in 1:200
    moved = false
    for k in 1:(n - 1)
        i, j = right_order[k], right_order[k + 1]
        if label_y_right[j] - label_y_right[i] < min_gap
            center = (label_y_right[i] + label_y_right[j]) / 2
            label_y_right[i] = center - min_gap / 2
            label_y_right[j] = center + min_gap / 2
            moved = true
        end
    end
    moved || break
end

# --- Plot ------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_text = "slope-basic · julia · makie · anyplot.ai"

ax = Axis(
    fig[1, 1];
    title           = title_text,
    titlesize       = 20,
    titlecolor      = INK,
    subtitle        = "Customer Satisfaction Score (0–100)",
    subtitlesize    = 14,
    subtitlecolor   = INK_SOFT,
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)
xlims!(ax, -0.85, 1.85)
ylims!(ax, ylim_lo, ylim_hi)

# The two vertical reference axes, one per survey year
vlines!(ax, [0, 1]; color=INK_SOFT, linewidth=1.5)

for i in 1:n
    rising = score_2024[i] >= score_2023[i]
    color = rising ? IMPRINT_INCREASE : IMPRINT_DECREASE
    label = rising ? "Increase" : "Decrease"
    arrow = rising ? "▲" : "▼"

    lines!(ax, [0, 1], [score_2023[i], score_2024[i]];
           color=color, linewidth=2.8, label=label)
    scatter!(ax, [0, 1], [score_2023[i], score_2024[i]];
             color=color, markersize=13, strokewidth=1.5, strokecolor=PAGE_BG)

    # Leader stubs: connect a nudged label back to its true marker position
    # whenever the anti-collision loop moved it, so the label-to-line link
    # stays traceable even when several labels cluster in a dense band.
    if abs(label_y_left[i] - score_2023[i]) > 1e-6
        lines!(ax, [-0.05, 0], [label_y_left[i], score_2023[i]];
               color=INK_SOFT, linewidth=0.75, linestyle=:dot)
    end
    if abs(label_y_right[i] - score_2024[i]) > 1e-6
        lines!(ax, [1, 1.05], [score_2024[i], label_y_right[i]];
               color=INK_SOFT, linewidth=0.75, linestyle=:dot)
    end

    text!(ax, -0.05, label_y_left[i]; text="$(products[i])  $(score_2023[i])",
          align=(:right, :center), color=INK, fontsize=15)
    text!(ax, 1.05, label_y_right[i]; text="$(arrow) $(score_2024[i])  $(products[i])",
          align=(:left, :center), color=INK, fontsize=15)
end

# Survey-year headers atop each vertical axis
text!(ax, 0, ylim_hi - y_pad * 0.5; text="2023 Survey", align=(:center, :bottom),
      color=INK_SOFT, fontsize=15, font=:bold)
text!(ax, 1, ylim_hi - y_pad * 0.5; text="2024 Survey", align=(:center, :bottom),
      color=INK_SOFT, fontsize=15, font=:bold)

Legend(fig[1, 2], ax; merge=true, unique=true, framevisible=false,
       labelcolor=INK, labelsize=13, patchsize=(22, 3), tellheight=false, valign=:center)
colsize!(fig.layout, 2, Fixed(105))

# --- Save --------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit=2)
