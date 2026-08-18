// anyplot.ai
// horizon-basic: Horizon Chart
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-08-18
//# anyplot-orientation: landscape
// anyplot.ai
// horizon-basic: Horizon Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Reproducible PRNG (LCG, no seeded RNG exists in the browser) ----------
function makeRng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

// --- Data: hourly temperature deviation from baseline, 8 facility sensors --
const STATIONS = [
  "Greenhouse North",
  "Greenhouse South",
  "Warehouse A",
  "Warehouse B",
  "Rooftop Array",
  "Basement Vault",
  "Loading Dock",
  "Server Room",
];
const HOURS = 200;
const startDate = new Date("2026-01-01T00:00:00Z");

const series = STATIONS.map((name, i) => {
  const rng = makeRng(1000 + i * 37);
  const phase = rng() * Math.PI * 2;
  const amplitude = 1.8 + rng() * 1.6;
  let walk = 0;
  const values = [];
  for (let h = 0; h < HOURS; h++) {
    walk += (rng() - 0.5) * 0.5;
    walk = Math.max(-2, Math.min(2, walk));
    const diurnal = amplitude * Math.sin((2 * Math.PI * h) / 24 + phase);
    values.push({ date: new Date(startDate.getTime() + h * 3600 * 1000), value: diurnal + walk });
  }
  return { name, values };
});

const allValues = series.flatMap((s) => s.values.map((d) => d.value));
const maxAbs = Math.ceil(d3.max(allValues, (d) => Math.abs(d)));
const NUM_BANDS = 3;
const bandSize = maxAbs / NUM_BANDS;

// --- Layout ------------------------------------------------------------------
const margin = { top: 150, right: 50, bottom: 60, left: 200 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;
const gap = 4;
const stripHeight = (ih - gap * (series.length - 1)) / series.length;

// --- Scales --------------------------------------------------------------
const x = d3
  .scaleTime()
  .domain(d3.extent(series[0].values, (d) => d.date))
  .range([0, iw]);

// Band color ramps — blue for above-baseline, red for below (Imprint div stops).
// The midpoint stop is the theme-adaptive page background, so shading from it
// toward the full hue reproduces the classic horizon "darker = larger" effect.
const midpoint = t.div[1];
const shade = (i) => 0.35 + 0.65 * (i / (NUM_BANDS - 1));
const posColors = d3.range(NUM_BANDS).map((i) => d3.interpolateRgb(midpoint, t.div[2])(shade(i)));
const negColors = d3.range(NUM_BANDS).map((i) => d3.interpolateRgb(midpoint, t.div[0])(shade(i)));

function bandScale(i) {
  const lower = i * bandSize;
  const upper = (i + 1) * bandSize;
  return d3.scaleLinear().domain([lower, upper]).range([stripHeight, 0]).clamp(true);
}

function bandPath(values, yScale, sign) {
  return d3
    .area()
    .x((d) => x(d.date))
    .y0(stripHeight)
    .y1((d) => yScale(Math.max(sign * d.value, 0)))
    .curve(d3.curveMonotoneX)(values);
}

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

// --- Title (fontsize scales down for long titles, see plot-generator.md) -----
const title = "Facility Temperature Deviation · horizon-basic · javascript · d3 · anyplot.ai";
const titleDefault = 26;
const titleSize = title.length > 67 ? Math.round(titleDefault * (67 / title.length)) : titleDefault;
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 46)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", `${titleSize}px`)
  .style("font-weight", "600")
  .text(title);

// --- Legend: band-color scale (value -> shade) --------------------------------
const legendSwatchW = 42;
const legendSwatchH = 20;
const legendColors = [...negColors.slice().reverse(), ...posColors];
const legendW = legendColors.length * legendSwatchW;
const legendX = width - margin.right - legendW;
const legendY = 76;

svg
  .append("text")
  .attr("x", legendX + legendW)
  .attr("y", legendY - 10)
  .attr("text-anchor", "end")
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text("Deviation from baseline (°C)");

svg
  .selectAll(".legend-swatch")
  .data(legendColors)
  .join("rect")
  .attr("class", "legend-swatch")
  .attr("x", (d, i) => legendX + i * legendSwatchW)
  .attr("y", legendY)
  .attr("width", legendSwatchW)
  .attr("height", legendSwatchH)
  .attr("fill", (d) => d);

const legendTicks = [
  { x: legendX, label: `-${maxAbs}°C` },
  { x: legendX + legendW / 2, label: "0°C" },
  { x: legendX + legendW, label: `+${maxAbs}°C` },
];
svg
  .selectAll(".legend-tick")
  .data(legendTicks)
  .join("text")
  .attr("class", "legend-tick")
  .attr("x", (d) => d.x)
  .attr("y", legendY + legendSwatchH + 16)
  .attr("text-anchor", (d, i) => (i === 0 ? "start" : i === 2 ? "end" : "middle"))
  .attr("fill", t.inkSoft)
  .style("font-size", "13px")
  .text((d) => d.label);

// --- Horizon strips ------------------------------------------------------------
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

g.append("rect")
  .attr("width", iw)
  .attr("height", ih)
  .attr("fill", "none")
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

series.forEach((s, si) => {
  const strip = g.append("g").attr("transform", `translate(0, ${si * (stripHeight + gap)})`);

  const clipId = `horizon-clip-${si}`;
  strip.append("clipPath").attr("id", clipId).append("rect").attr("width", iw).attr("height", stripHeight);

  const layers = strip.append("g").attr("clip-path", `url(#${clipId})`);
  for (let i = 0; i < NUM_BANDS; i++) {
    const yScale = bandScale(i);
    layers.append("path").attr("d", bandPath(s.values, yScale, 1)).attr("fill", posColors[i]);
    layers.append("path").attr("d", bandPath(s.values, yScale, -1)).attr("fill", negColors[i]);
  }

  strip
    .append("line")
    .attr("x1", 0)
    .attr("x2", iw)
    .attr("y1", stripHeight)
    .attr("y2", stripHeight)
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);

  strip
    .append("text")
    .attr("x", -12)
    .attr("y", stripHeight / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "end")
    .attr("fill", t.inkSoft)
    .style("font-size", "15px")
    .text(s.name);
});

// --- Shared time axis (bottom only) -------------------------------------------
const xAxis = g
  .append("g")
  .attr("transform", `translate(0, ${ih})`)
  .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat("%b %d")));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
xAxis.selectAll("line").attr("stroke", t.grid);
xAxis.select(".domain").attr("stroke", t.inkSoft);
