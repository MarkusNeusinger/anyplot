// anyplot.ai
// campbell-basic: Campbell Diagram
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-08-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 250, bottom: 90, left: 90 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
const maxSpeed = 6000; // RPM
const maxFreq = 180; // Hz — visible plot ceiling
const nPoints = 81;
const speeds = d3.range(nPoints).map((i) => (i * maxSpeed) / (nPoints - 1));

// Natural frequency modes: base value at zero speed + linear drift from
// gyroscopic stiffening/softening (some modes rise, some fall with speed).
const modes = [
  { label: "1st Bending", base: 25, delta: 10 },
  { label: "2nd Bending", base: 60, delta: -8 },
  { label: "1st Torsional", base: 110, delta: 12 },
  { label: "Axial", base: 155, delta: 5 },
];
const modeCurves = modes.map((m, i) => ({
  label: m.label,
  color: t.palette[i],
  points: speeds.map((s) => ({ speed: s, freq: m.base + (m.delta * s) / maxSpeed })),
}));

// Engine order excitation lines: frequency = order * (speed / 60 s/min).
const engineOrders = [1, 2, 3].map((order) => ({
  order,
  label: `${order}x`,
  points: speeds.map((s) => ({ speed: s, freq: (order * s) / 60 })),
}));

// Critical speeds: numeric root-finding for mode/order-line intersections.
function findIntersections(modeCurve, orderLine) {
  const hits = [];
  for (let i = 0; i < speeds.length - 1; i++) {
    const d0 = modeCurve.points[i].freq - orderLine.points[i].freq;
    const d1 = modeCurve.points[i + 1].freq - orderLine.points[i + 1].freq;
    if (d0 === 0 || d0 * d1 < 0) {
      const frac = d0 === 0 ? 0 : d0 / (d0 - d1);
      const speed = speeds[i] + frac * (speeds[i + 1] - speeds[i]);
      const freq = modeCurve.points[i].freq + frac * (modeCurve.points[i + 1].freq - modeCurve.points[i].freq);
      if (freq <= maxFreq) hits.push({ speed, freq });
    }
  }
  return hits;
}
const criticalSpeeds = modeCurves.flatMap((mc) =>
  engineOrders.flatMap((eo) => findIntersections(mc, eo).map((hit) => ({ ...hit, mode: mc.label, order: eo.label }))),
);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleLinear().domain([0, maxSpeed]).range([0, iw]);
const y = d3.scaleLinear().domain([0, maxFreq]).range([ih, 0]);
const line = d3.line().x((d) => x(d.speed)).y((d) => y(d.freq));

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

svg.append("clipPath").attr("id", "plot-area").append("rect").attr("width", iw).attr("height", ih);
const plot = g.append("g").attr("clip-path", "url(#plot-area)");

// --- Y grid (subtle, per style guide) --------------------------------------
plot
  .append("g")
  .selectAll("line")
  .data(y.ticks(6))
  .join("line")
  .attr("x1", 0)
  .attr("x2", iw)
  .attr("y1", (d) => y(d))
  .attr("y2", (d) => y(d))
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Engine order excitation lines (dashed, neutral reference lines) -------
plot
  .selectAll(".order-line")
  .data(engineOrders)
  .join("path")
  .attr("class", "order-line")
  .attr("d", (d) => line(d.points))
  .attr("fill", "none")
  .attr("stroke", t.inkSoft)
  .attr("stroke-width", 2)
  .attr("stroke-dasharray", "8,6");

// End labels for the engine order lines, placed where each line exits the
// visible frame (right edge if it stays under maxFreq, top edge otherwise).
const orderExits = engineOrders.map((eo) => {
  const freqAt6000 = (eo.order * maxSpeed) / 60;
  return freqAt6000 <= maxFreq
    ? { ...eo, speed: maxSpeed, freq: freqAt6000, anchor: "start", dx: 8, dy: 4 }
    : { ...eo, speed: (maxFreq * 60) / eo.order, freq: maxFreq, anchor: "middle", dx: 0, dy: -10 };
});
g.selectAll(".order-label")
  .data(orderExits)
  .join("text")
  .attr("class", "order-label")
  .attr("x", (d) => x(d.speed) + d.dx)
  .attr("y", (d) => y(d.freq) + d.dy)
  .attr("text-anchor", (d) => d.anchor)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .style("font-weight", "600")
  .text((d) => d.label);

// --- Natural frequency curves ------------------------------------------------
plot
  .selectAll(".mode-line")
  .data(modeCurves)
  .join("path")
  .attr("class", "mode-line")
  .attr("d", (d) => line(d.points))
  .attr("fill", "none")
  .attr("stroke", (d) => d.color)
  .attr("stroke-width", 3.5);

// --- Critical speed markers (deferred semantic-red anchor, per style guide) --
const diamond = d3.symbol().type(d3.symbolDiamond).size(260);
plot
  .selectAll(".critical-marker")
  .data(criticalSpeeds)
  .join("path")
  .attr("class", "critical-marker")
  .attr("d", diamond)
  .attr("transform", (d) => `translate(${x(d.speed)},${y(d.freq)})`)
  .attr("fill", t.palette[4])
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Axes -----------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6));
const yAxis = g.append("g").call(d3.axisLeft(y).ticks(6));
for (const axis of [xAxis, yAxis]) {
  axis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "14px");
  axis.selectAll("line").attr("stroke", t.inkSoft);
  axis.select(".domain").attr("stroke", t.inkSoft);
}

g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Rotational Speed (RPM)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "16px")
  .text("Natural Frequency (Hz)");

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("campbell-basic · javascript · d3 · anyplot.ai");

// --- Legend -----------------------------------------------------------------
const legendItems = [
  ...modeCurves.map((d) => ({ label: d.label, kind: "line", color: d.color, dash: null })),
  { label: "Engine order excitation", kind: "line", color: t.inkSoft, dash: "8,6" },
  { label: "Critical speed", kind: "marker", color: t.palette[4] },
];
const legend = g.append("g").attr("transform", `translate(${iw + 40}, 0)`);
const legendRows = legend
  .selectAll(".legend-row")
  .data(legendItems)
  .join("g")
  .attr("class", "legend-row")
  .attr("transform", (_, i) => `translate(0, ${i * 34})`);

legendRows
  .filter((d) => d.kind === "line")
  .append("line")
  .attr("x1", 0)
  .attr("x2", 28)
  .attr("y1", 0)
  .attr("y2", 0)
  .attr("stroke", (d) => d.color)
  .attr("stroke-width", 3.5)
  .attr("stroke-dasharray", (d) => d.dash);

legendRows
  .filter((d) => d.kind === "marker")
  .append("path")
  .attr("d", d3.symbol().type(d3.symbolDiamond).size(220))
  .attr("transform", "translate(14,0)")
  .attr("fill", (d) => d.color)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

legendRows
  .append("text")
  .attr("x", 38)
  .attr("y", 5)
  .attr("fill", t.inkSoft)
  .style("font-size", "14px")
  .text((d) => d.label);
