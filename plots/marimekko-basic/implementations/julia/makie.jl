# anyplot.ai
# marimekko-basic: Basic Marimekko Chart
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-07-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const WHITE_TEXT = colorant"#FFFDF6"
const DARK_TEXT  = colorant"#1A1A17"

# --- Data: digital ad spend ($K) by channel (width) and objective (stack) --
x_categories = ["Social", "Search", "Video", "Display", "Audio"]
y_categories = ["Brand Awareness", "Performance", "Retention"]

# rows = y_categories (stack order, bottom to top), cols = x_categories
values = [
    150  40 190  70 30
    220 260  90  50 15
    80   60  30  20  5
]

n_x = length(x_categories)
n_y = length(y_categories)
col_totals = vec(sum(values; dims = 1))
grand_total = sum(col_totals)

# Bar widths proportional to column totals, with a thin gap between bars.
gap = 0.015
usable_width = 1.0 - gap * (n_x - 1)
widths = col_totals ./ grand_total .* usable_width

x_starts = zeros(n_x)
for i in 2:n_x
    x_starts[i] = x_starts[i - 1] + widths[i - 1] + gap
end

# Segment fill colors: green first, then canonical order.
SEGMENT_COLORS = IMPRINT_PALETTE[1:n_y]
TEXT_ON_FILL = [WHITE_TEXT, DARK_TEXT, WHITE_TEXT]  # contrast per SEGMENT_COLORS entry

# --- Figure -------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "marimekko-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Channel  (bar width ∝ total ad spend)",
    ylabel             = "Share of Channel Spend",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 13,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xticksvisible      = false,
    ygridvisible       = true,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

ax.xticks = (x_starts .+ widths ./ 2, x_categories)
ax.yticks = (0:0.25:1, ["0%", "25%", "50%", "75%", "100%"])

xlims!(ax, -0.02, 1.02)
ylims!(ax, 0, 1.06)

# Label threshold: only annotate segments that are large enough to hold text.
label_threshold = 0.04 * grand_total

for i in 1:n_x
    y0 = 0.0
    for j in 1:n_y
        value = values[j, i]
        frac = value / col_totals[i]
        poly!(
            ax,
            Rect2f(x_starts[i], y0, widths[i], frac);
            color = SEGMENT_COLORS[j],
            strokecolor = PAGE_BG,
            strokewidth = 3,
        )
        if value >= label_threshold
            text!(
                ax,
                x_starts[i] + widths[i] / 2,
                y0 + frac / 2;
                text = "\$$(value)K",
                color = TEXT_ON_FILL[j],
                fontsize = 15,
                align = (:center, :center),
            )
        end
        y0 += frac
    end
    # Column-total annotation above each bar, reinforcing "width = total".
    text!(
        ax,
        x_starts[i] + widths[i] / 2,
        1.03;
        text = "\$$(col_totals[i])K",
        color = INK_SOFT,
        fontsize = 13,
        align = (:center, :center),
    )
end

Legend(
    fig[1, 2],
    [PolyElement(color = c) for c in SEGMENT_COLORS],
    y_categories,
    "Objective";
    framevisible = false,
    backgroundcolor = :transparent,
    labelcolor = INK,
    titlecolor = INK,
)

colsize!(fig.layout, 1, Relative(0.82))

# --- Save ---------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
