// anyplot.ai
// bar-grouped: Grouped Bar Chart
// Library: d3 7.9.0 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 130, right: 260, bottom: 100, left: 130 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Quarterly revenue (in $M) for three product lines across four fiscal quarters.
const categories = ["Q1", "Q2", "Q3", "Q4"];
const groups = ["Hardware", "Software", "Services"];
const data = [
  { category: "Q1", group: "Hardware", value: 4.2 },
  { category: "Q1", group: "Software", value: 6.1 },
  { category: "Q1", group: "Services", value: 3.0 },
  { category: "Q2", group: "Hardware", value: 4.6 },
  { category: "Q2", group: "Software", value: 6.8 },
  { category: "Q2", group: "Services", value: 3.4 },
  { category: "Q3", group: "Hardware", value: 4.1 },
  { category: "Q3", group: "Software", value: 7.9 },
  { category: "Q3", group: "Services", value: 3.9 },
  { category: "Q4", group: "Hardware", value: 5.3 },
  { category: "Q4", group: "Software", value: 9.2 },
  { category: "Q4", group: "Services", value: 4.5 },
];

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Scales ---------------------------------------------------------------
const x0 = d3.scaleBand().domain(categories).range([0, iw]).paddingInner(0.3);
const x1 = d3.scaleBand().domain(groups).range([0, x0.bandwidth()]).padding(0.12);
const y = d3
  .scaleLinear()
  .domain([0, d3.max(data, (d) => d.value)])
  .nice()
  .range([ih, 0]);
const color = d3.scaleOrdinal().domain(groups).range(t.palette);

// --- Defs: per-series sheen gradients + growth-arrow marker ------------------
// A hand-built path generator + gradient/marker defs is a low-level SVG
// capability that a high-level charting library would not expose directly.
const defs = svg.append("defs");
groups.forEach((group, i) => {
  const base = d3.color(color(group));
  const grad = defs
    .append("linearGradient")
    .attr("id", `bar-sheen-${i}`)
    .attr("x1", "0%")
    .attr("y1", "0%")
    .attr("x2", "0%")
    .attr("y2", "100%");
  grad.append("stop").attr("offset", "0%").attr("stop-color", base.brighter(0.7));
  grad.append("stop").attr("offset", "35%").attr("stop-color", base);
  grad.append("stop").attr("offset", "100%").attr("stop-color", base.darker(0.15));
});

defs
  .append("marker")
  .attr("id", "growth-arrow")
  .attr("viewBox", "0 0 10 10")
  .attr("refX", 8)
  .attr("refY", 5)
  .attr("markerWidth", 7)
  .attr("markerHeight", 7)
  .attr("orient", "auto-start-reverse")
  .append("path")
  .attr("d", "M0,0 L10,5 L0,10 Z")
  .attr("fill", t.ink);

// --- Rounded-top bar path generator ------------------------------------------
function topRoundedRectPath(x, y, w, h, radius) {
  const r = Math.min(radius, w / 2, h);
  return `M${x},${y + r}
    A${r},${r} 0 0 1 ${x + r},${y}
    H${x + w - r}
    A${r},${r} 0 0 1 ${x + w},${y + r}
    V${y + h}
    H${x}
    Z`;
}

// --- Gridlines (y-axis only) ------------------------------------------------
g.append("g")
  .attr("class", "grid")
  .call(d3.axisLeft(y).tickSize(-iw).tickFormat(""))
  .selectAll("line")
  .attr("stroke", t.grid);
g.select(".grid .domain").remove();

// --- Bars -------------------------------------------------------------------
const categoryGroups = g
  .selectAll(".category-group")
  .data(categories)
  .join("g")
  .attr("class", "category-group")
  .attr("transform", (d) => `translate(${x0(d)},0)`);

categoryGroups
  .selectAll("path")
  .data((cat) => data.filter((d) => d.category === cat))
  .join("path")
  .attr("d", (d) =>
    topRoundedRectPath(x1(d.group), y(d.value), x1.bandwidth(), ih - y(d.value), 5)
  )
  .attr("fill", (d) => `url(#bar-sheen-${groups.indexOf(d.group)})`)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Value labels -------------------------------------------------------------
categoryGroups
  .selectAll("text")
  .data((cat) => data.filter((d) => d.category === cat))
  .join("text")
  .attr("x", (d) => x1(d.group) + x1.bandwidth() / 2)
  .attr("y", (d) => y(d.value) - 12)
  .attr("text-anchor", "middle")
  .style("font-size", "13px")
  .attr("fill", t.inkSoft)
  .text((d) => d.value.toFixed(1));

// --- Axes -----------------------------------------------------------------
const xAxis = g.append("g").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x0));
const yAxis = g
  .append("g")
  .call(d3.axisLeft(y).tickFormat((d) => `$${d}M`));

for (const ax of [xAxis, yAxis]) {
  ax.selectAll("text").attr("fill", t.inkSoft).style("font-size", "16px");
  ax.selectAll("line").attr("stroke", t.inkSoft);
  ax.select(".domain").attr("stroke", t.inkSoft);
}
xAxis.selectAll("line").remove();

// --- Axis labels ------------------------------------------------------------
g.append("text")
  .attr("x", iw / 2)
  .attr("y", ih + 66)
  .attr("text-anchor", "middle")
  .style("font-size", "18px")
  .attr("fill", t.ink)
  .text("Fiscal Quarter (2025)");

g.append("text")
  .attr("transform", "rotate(-90)")
  .attr("x", -ih / 2)
  .attr("y", -96)
  .attr("text-anchor", "middle")
  .style("font-size", "18px")
  .attr("fill", t.ink)
  .text("Revenue ($M)");

// --- Growth annotation (Software Q1 -> Q4) ------------------------------------
// Data storytelling: Software is the standout trend (6.1 -> 9.2). A bracket
// spanning the empty headroom above the tallest bars calls it out without
// touching any bar, value label, or gridline.
const softwareQ1 = data.find((d) => d.category === "Q1" && d.group === "Software");
const softwareQ4 = data.find((d) => d.category === "Q4" && d.group === "Software");
const growthPct = Math.round(((softwareQ4.value - softwareQ1.value) / softwareQ1.value) * 100);
const bracketY = 22;
const qx1 = x0("Q1") + x1("Software") + x1.bandwidth() / 2;
const qx4 = x0("Q4") + x1("Software") + x1.bandwidth() / 2;

const annotation = g.append("g").attr("class", "growth-annotation");

annotation
  .append("path")
  .attr(
    "d",
    `M${qx1},${bracketY + 8} V${bracketY} H${qx4}`
  )
  .attr("fill", "none")
  .attr("stroke", t.ink)
  .attr("stroke-width", 2)
  .attr("stroke-dasharray", "5,4")
  .attr("opacity", 0.75)
  .attr("marker-end", "url(#growth-arrow)");

annotation
  .append("text")
  .attr("x", (qx1 + qx4) / 2)
  .attr("y", bracketY - 10)
  .attr("text-anchor", "middle")
  .style("font-size", "15px")
  .style("font-weight", "700")
  .attr("fill", t.ink)
  .text(`Software +${growthPct}% (Q1→Q4)`);

// --- Legend -------------------------------------------------------------------
const legend = svg
  .append("g")
  .attr("transform", `translate(${width - margin.right + 60},${margin.top + 20})`);

groups.forEach((group, i) => {
  const row = legend.append("g").attr("transform", `translate(0,${i * 40})`);
  row
    .append("rect")
    .attr("width", 24)
    .attr("height", 24)
    .attr("rx", 5)
    .attr("ry", 5)
    .attr("fill", `url(#bar-sheen-${i})`)
    .attr("stroke", t.grid)
    .attr("stroke-width", 1);
  row
    .append("text")
    .attr("x", 36)
    .attr("y", 18)
    .style("font-size", "16px")
    .attr("fill", t.ink)
    .text(group);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 60)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "19px")
  .style("font-weight", "600")
  .text("Product Line Revenue by Quarter · bar-grouped · javascript · d3 · anyplot.ai");
