# anyplot.ai
# polar-bar: Polar Bar Chart (Wind Rose)
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-05

using CairoMakie
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
GRID = THEME == "light" ? RGBAf(0.102, 0.102, 0.090, 0.18) : RGBAf(0.941, 0.937, 0.910, 0.18)
IMPRINT_PALETTE = [colorant"#009E73", colorant"#C475FD", colorant"#4467A3"]

# --- Data -----------------------------------------------------------------
# Meteorological station: hours per year a wind was observed, split by
# compass direction and speed band. Prevailing wind blows from the SW-W
# quadrant, a common mid-latitude pattern.
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
n_directions = length(directions)
bearings_deg = collect(0:45:315)

speed_bins = ["Light (0-10 kn)", "Moderate (10-20 kn)", "Strong (20-30 kn)"]
n_bins = length(speed_bins)

prevailing_bearing = 247.5
base_hours = 60.0 .+ 40.0 .* cosd.(bearings_deg .- prevailing_bearing)
total_hours = round.(Int, base_hours .+ rand(n_directions) .* 15.0)

light_hours = round.(Int, total_hours .* (0.55 .+ 0.05 .* rand(n_directions)))
moderate_hours = round.(Int, total_hours .* (0.30 .+ 0.05 .* rand(n_directions)))
strong_hours = max.(total_hours .- light_hours .- moderate_hours, 3)

hours_by_bin = hcat(light_hours, moderate_hours, strong_hours)  # n_directions x n_bins

# --- Plot -------------------------------------------------------------------
fig = Figure(size = (1200, 1200), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title = "polar-bar · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    backgroundcolor = PAGE_BG,
    aspect = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)

sector_deg = 360.0 / n_directions
bar_half_width_deg = sector_deg * 0.34

row_totals = vec(sum(hours_by_bin, dims = 2))
r_grid_max = maximum(row_totals)
r_ticks = round.(Int, range(0, r_grid_max, length = 5))[2:end]
r_display_max = r_grid_max * 1.2

# Radial grid circles + compass spokes (background layer)
for rt in r_ticks
    circle_pts = Point2f[]
    for a in range(0, 360, length = 145)
        theta = deg2rad(a)
        push!(circle_pts, Point2f(rt * sin(theta), rt * cos(theta)))
    end
    lines!(ax, circle_pts; color = GRID, linewidth = 1.5)
end

for bearing in bearings_deg
    theta = deg2rad(bearing)
    spoke_end = Point2f(r_display_max * sin(theta), r_display_max * cos(theta))
    lines!(ax, [Point2f(0, 0), spoke_end]; color = GRID, linewidth = 1.0)
end

# Stacked wedges — each direction is n_bins wedges radiating from the center,
# sampled along an arc so the outer edge curves like a real wind-rose slice
n_arc = 24
for i in 1:n_directions
    center_deg = bearings_deg[i]
    r0 = 0.0
    for b in 1:n_bins
        r1 = r0 + hours_by_bin[i, b]
        arc_angles = range(center_deg - bar_half_width_deg, center_deg + bar_half_width_deg, length = n_arc)
        wedge_pts = Point2f[]
        for a in arc_angles
            theta = deg2rad(a)
            push!(wedge_pts, Point2f(r1 * sin(theta), r1 * cos(theta)))
        end
        if r0 <= 0
            push!(wedge_pts, Point2f(0, 0))
        else
            for a in reverse(arc_angles)
                theta = deg2rad(a)
                push!(wedge_pts, Point2f(r0 * sin(theta), r0 * cos(theta)))
            end
        end
        poly!(
            ax, wedge_pts;
            color = IMPRINT_PALETTE[b], strokecolor = PAGE_BG, strokewidth = 1.5,
            label = i == 1 ? speed_bins[b] : nothing,
        )
        r0 = r1
    end
end

# Radial tick labels sit in the gap between the N and NE bars, rotated to run
# along the spoke so their tangential footprint stays narrow at small radii
for rt in r_ticks
    theta = deg2rad(sector_deg / 2)
    label_pt = Point2f(rt * sin(theta), rt * cos(theta))
    text!(ax, label_pt; text = "$(rt)h", color = INK_SOFT, fontsize = 11,
          align = (:left, :center), rotation = pi / 2 - theta)
end

# Compass direction labels beyond the outer grid ring
label_r = r_display_max * 1.1
for (i, direction) in enumerate(directions)
    theta = deg2rad(bearings_deg[i])
    label_pt = Point2f(label_r * sin(theta), label_r * cos(theta))
    text!(ax, label_pt; text = direction, color = INK, fontsize = 16, align = (:center, :center))
end

axislegend(
    ax; position = :rb, framevisible = false, labelcolor = INK, labelsize = 13,
    backgroundcolor = (:transparent, 0.0),
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
