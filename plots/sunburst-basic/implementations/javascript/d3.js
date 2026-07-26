// anyplot.ai
// sunburst-basic: Basic Sunburst Chart
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-07-26

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// --- Data (in-memory, deterministic) ----------------------------------------
// Cloud infrastructure spend, thousands USD/month, by business unit -> service -> workload.
const data = {
  name: "Cloud Spend",
  children: [
    {
      name: "Engineering",
      children: [
        {
          name: "Compute",
          children: [
            { name: "Production", value: 42 },
            { name: "Staging", value: 18 },
            { name: "ML Training", value: 26 },
          ],
        },
        {
          name: "Storage",
          children: [
            { name: "Object Storage", value: 21 },
            { name: "Block Storage", value: 14 },
          ],
        },
        { name: "Networking", value: 19 },
      ],
    },
    {
      name: "Data & Analytics",
      children: [
        { name: "Data Warehouse", value: 24 },
        { name: "Streaming Pipeline", value: 16 },
        {
          name: "BI Tools",
          children: [
            { name: "Dashboards", value: 9 },
            { name: "Ad-hoc Queries", value: 7 },
          ],
        },
      ],
    },
    {
      name: "Operations",
      children: [
        { name: "Monitoring", value: 15 },
        { name: "Security", value: 12 },
        { name: "Backup & DR", value: 11 },
      ],
    },
  ],
};

// --- Layout -------------------------------------------------------------
const margin = { top: 130, right: 20, bottom: 20, left: 20 };
const size = Math.min(width - margin.left - margin.right, height - margin.top - margin.bottom);
const radius = size / 2;

const root = d3
  .hierarchy(data)
  .sum((d) => d.value)
  .sort((a, b) => b.value - a.value);
d3.partition().size([2 * Math.PI, radius])(root);

// --- Color: one hue per top-level branch, lightened per depth -----------
const branchNames = root.children.map((d) => d.data.name);
const branchColor = d3.scaleOrdinal().domain(branchNames).range(t.palette);

function colorFor(d) {
  let branchNode = d;
  while (branchNode.depth > 1) branchNode = branchNode.parent;
  const base = d3.hsl(branchColor(branchNode.data.name));
  base.l = Math.min(0.82, base.l + (d.depth - 1) * 0.14);
  return base.toString();
}

// --- SVG mount ------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);
const g = svg.append("g").attr("transform", `translate(${width / 2},${margin.top + radius})`);

const arc = d3
  .arc()
  .startAngle((d) => d.x0)
  .endAngle((d) => d.x1)
  .padAngle((d) => Math.min((d.x1 - d.x0) / 2, 0.004))
  .padRadius(radius / 2)
  .innerRadius((d) => d.y0)
  .outerRadius((d) => d.y1 - 1);

// --- Segments (skip the invisible root) ------------------------------------
g.selectAll("path")
  .data(root.descendants().filter((d) => d.depth > 0))
  .join("path")
  .attr("d", arc)
  .attr("fill", colorFor)
  .attr("stroke", t.pageBg)
  .attr("stroke-width", 1.5);

// --- Labels: only where the angular span leaves room to read ---------------
function labelTransform(d) {
  const midAngle = ((d.x0 + d.x1) / 2) * (180 / Math.PI);
  const labelRadius = (d.y0 + d.y1) / 2;
  const rotate = midAngle - 90;
  const flip = midAngle < 180 ? 0 : 180;
  return `rotate(${rotate}) translate(${labelRadius},0) rotate(${flip})`;
}

g.selectAll("text")
  .data(root.descendants().filter((d) => d.depth > 0 && d.x1 - d.x0 > 0.11))
  .join("text")
  .attr("transform", labelTransform)
  .attr("dy", "0.32em")
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", (d) => (d.depth === 1 ? "16px" : "13px"))
  .style("font-weight", (d) => (d.depth === 1 ? "600" : "400"))
  .style("pointer-events", "none")
  .text((d) => d.data.name);

// --- Title ------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("sunburst-basic · javascript · d3 · anyplot.ai");
