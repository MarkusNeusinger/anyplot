# anyplot.ai
# heatmap-basic: Basic Heatmap
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-05-28

using CairoMakie
using Colors
using DataFrames
using Random
using Printf

# Theme tokens
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential ramp for filled cells (single-signed data)
const ANYPLOT_SEQ_FIELDS = THEME == "light" ?
    cgrad([colorant"#66E2B2", colorant"#009E73", colorant"#024582", colorant"#351E45"], [0.0, 0.369, 0.803, 1.0]) :
    cgrad([colorant"#404C02", colorant"#009E73", colorant"#CDD9FF"], [0.0, 0.487, 1.0])

# Columns: set these to your table's column names
const PLAN     = "Subscription plan"         # role: row
const FEATURE  = "Product feature"           # role: column
const ADOPTION = "Adoption (% of accounts)"  # role: value

# Data: replace this block with your own table, for example df = CSV.read("adoption.csv", DataFrame)
# Product-usage metrics: share of accounts using each feature, by plan tier
Random.seed!(42)
plans    = ["Trial", "Free", "Starter", "Team", "Business", "Enterprise"]
features = ["Dashboards", "Reports", "Alerts", "Export", "API", "Integrations", "SSO", "Audit log"]
df = DataFrame(
    PLAN     => repeat(plans; inner = length(features)),
    FEATURE  => repeat(features; outer = length(plans)),
    ADOPTION => [
        clamp(100 / (1 + exp(0.9 * (f - 1.5 - 1.3 * p))) + 4 * randn(), 2, 98)
        for p in eachindex(plans) for f in eachindex(features)
    ],
)

# Plot: reads only df and the constants above
row_names = unique(df[!, PLAN])
col_names = unique(df[!, FEATURE])
nr, nc    = length(row_names), length(col_names)
grid      = permutedims(reshape(df[!, ADOPTION], nc, nr))   # rows = plans, columns = features
vmin, vmax = extrema(df[!, ADOPTION])

fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-basic · julia · makie · anyplot.ai",
    titlesize          = 22,
    titlecolor         = INK,
    xlabel             = FEATURE,
    ylabel             = PLAN,
    xlabelsize         = 18,
    ylabelsize         = 18,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xticklabelsize     = 16,
    yticklabelsize     = 16,
    xticksize          = 0,
    yticksize          = 0,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticks             = (1:nc, col_names),
    yticks             = (1:nr, row_names),
    yreversed          = true,
)

hm = heatmap!(ax, 1:nc, 1:nr, permutedims(grid);
    colormap   = ANYPLOT_SEQ_FIELDS,
    colorrange = (vmin, vmax),
)

# Thin page-colored separators between cells
vlines!(ax, [i + 0.5 for i in 0:nc]; color = PAGE_BG, linewidth = 3)
hlines!(ax, [i + 0.5 for i in 0:nr]; color = PAGE_BG, linewidth = 3)

# In-cell values: ink flips with the darkness of the cell underneath
positions   = Point2f[]
cell_labels = String[]
label_color = RGBAf[]
for r in 1:nr, c in 1:nc
    v   = grid[r, c]
    bg  = get(ANYPLOT_SEQ_FIELDS, (v - vmin) / (vmax - vmin))
    lin(x) = x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055)^2.4
    lum = 0.2126 * lin(red(bg)) + 0.7152 * lin(green(bg)) + 0.0722 * lin(blue(bg))
    push!(positions, Point2f(c, r))
    push!(cell_labels, @sprintf("%.0f", v))
    # WCAG contrast of the near-black ink (L ~ 0.01) vs the near-white ink (L ~ 0.94)
    push!(label_color, (lum + 0.05) / 0.06 > 0.99 / (lum + 0.05) ? RGBAf(0.102, 0.102, 0.090) : RGBAf(0.98, 0.973, 0.945))
end
text!(ax, positions; text = cell_labels, align = (:center, :center), color = label_color, fontsize = 18)

Colorbar(fig[1, 2], hm;
    label          = ADOPTION,
    labelcolor     = INK,
    tickcolor      = INK_SOFT,
    ticklabelcolor = INK_SOFT,
    ticklabelsize  = 16,
    labelsize      = 18,
    width          = 24,
)

colgap!(fig.layout, 1, 16)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
