# anyplot.ai
# heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 82/100 | Created: 2026-06-20

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Risk colormap: Imprint green (safe) → amber (caution) → matte red (critical)
const RISK_CMAP = cgrad(
    [colorant"#009E73", colorant"#DDCC77", colorant"#AE3030"],
    [0.0, 4.0 / 25.0, 1.0],
)

# 5×5 risk score matrix: score = likelihood × impact
risk_matrix = Float64[i * j for i in 1:5, j in 1:5]

likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost\nCertain"]
impact_labels     = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

# Risk register: (name, likelihood 1–5, impact 1–5)  — all unique cells
risks = [
    ("Data Breach",    2, 5),
    ("Budget Overrun", 4, 4),
    ("Scope Creep",    4, 3),
    ("Vendor Failure", 2, 4),
    ("System Outage",  3, 5),
    ("Staff Turnover", 4, 2),
    ("Compliance",     1, 5),
    ("HW Fault",       3, 3),
    ("Market Shift",   3, 4),
    ("Cyber Attack",   5, 5),
    ("Proc. Delay",    5, 3),
    ("Reg. Change",    2, 3),
]

risk_names = [r[1] for r in risks]
risk_x     = Float64[r[2] for r in risks]   # likelihood (x-axis)
risk_y     = Float64[r[3] for r in risks]   # impact (y-axis)

# Figure — square canvas → 2400×2400 final PNG
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-risk-matrix · julia · makie · anyplot.ai",
    titlesize          = 22,
    titlecolor         = INK,
    xlabel             = "Likelihood",
    ylabel             = "Consequence / Impact",
    xlabelsize         = 16,
    ylabelsize         = 16,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = true,
    rightspinevisible  = true,
    leftspinevisible   = true,
    bottomspinevisible = true,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    topspinecolor      = INK_SOFT,
    rightspinecolor    = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
    xticks             = (1:5, likelihood_labels),
    yticks             = (1:5, impact_labels),
)

# Background heatmap
hm = heatmap!(ax, 1:5, 1:5, risk_matrix;
    colormap   = RISK_CMAP,
    colorrange = (1.0, 25.0),
)

# Cell grid lines
for k in 0.5:1.0:5.5
    hlines!(ax, k; color = (INK_SOFT, 0.6), linewidth = 1.2)
    vlines!(ax, k; color = (INK_SOFT, 0.6), linewidth = 1.2)
end

# Risk item markers — elevated-background fill with ink border
scatter!(ax, risk_x, risk_y;
    color       = ELEVATED_BG,
    markersize  = 18,
    strokecolor = INK,
    strokewidth = 1.8,
)

# Risk item text labels (offset above marker)
for i in eachindex(risk_names)
    text!(ax, risk_x[i], risk_y[i] + 0.22;
          text     = risk_names[i],
          align    = (:center, :bottom),
          fontsize = 9,
          color    = INK,
    )
end

xlims!(ax, 0.5, 5.5)
ylims!(ax, 0.5, 5.5)

# Colorbar with zone labels at zone midpoints
Colorbar(fig[1, 2], hm;
    label          = "Risk Score  (Likelihood × Impact)",
    labelsize      = 14,
    labelcolor     = INK,
    ticklabelsize  = 11,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    ticks          = (
        [2.5, 7.0, 13.0, 22.5],
        ["Low (1–4)", "Medium (5–9)", "High (10–16)", "Critical (20–25)"],
    ),
    width          = 22,
)

save("plot-$(THEME).png", fig; px_per_unit = 2)
