//# anyplot-orientation: square
// anyplot.ai
// heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

const margin = { top: 100, right: 40, bottom: 260, left: 175 };
const cellSize = Math.floor(
  Math.min(
    width - margin.left - margin.right,
    height - margin.top - margin.bottom
  ) / 5
);
const gridSide = cellSize * 5;

// Semantic risk zone colors — traffic-light domain convention
const ZONE = [
  { color: "#009E73", label: "Low (1–4)",         opacity: 0.32 },
  { color: "#DDCC77", label: "Medium (5–9)",      opacity: 0.62 },
  { color: "#BD8233", label: "High (10–16)",      opacity: 0.80 },
  { color: "#AE3030", label: "Critical (20–25)",  opacity: 0.90 },
];

function zoneIdx(l, i) {
  const s = l * i;
  return s <= 4 ? 0 : s <= 9 ? 1 : s <= 16 ? 2 : 3;
}

// Project management risk register (12 items, all in distinct cells)
const risks = [
  { name: "Budget Overrun",     l: 4, i: 4 },
  { name: "Scope Creep",        l: 5, i: 3 },
  { name: "Staff Turnover",     l: 2, i: 5 },
  { name: "Tech Failure",       l: 2, i: 4 },
  { name: "Regulatory Change",  l: 2, i: 3 },
  { name: "Vendor Delay",       l: 4, i: 2 },
  { name: "Data Breach",        l: 1, i: 5 },
  { name: "Market Shift",       l: 3, i: 3 },
  { name: "Integration Issues", l: 3, i: 2 },
  { name: "Comms Gap",          l: 5, i: 1 },
  { name: "Resource Shortage",  l: 3, i: 4 },
  { name: "Compliance Fail",    l: 1, i: 4 },
];

// SVG
const svg = d3.select("#container").append("svg")
  .attr("width", width).attr("height", height);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Heatmap cells
for (let l = 1; l <= 5; l++) {
  for (let i = 1; i <= 5; i++) {
    const zi = zoneIdx(l, i);
    const { color, opacity } = ZONE[zi];
    const cx = (l - 1) * cellSize;
    const cy = (5 - i) * cellSize; // impact 5 at top, 1 at bottom

    g.append("rect")
      .attr("x", cx).attr("y", cy)
      .attr("width", cellSize).attr("height", cellSize)
      .attr("fill", color).attr("fill-opacity", opacity)
      .attr("stroke", t.pageBg).attr("stroke-width", 3);

    // Score watermark (bottom-right of cell)
    g.append("text")
      .attr("x", cx + cellSize - 9).attr("y", cy + 20)
      .attr("text-anchor", "end")
      .attr("fill", t.ink).attr("fill-opacity", 0.28)
      .style("font-size", "13px")
      .text(l * i);
  }
}

// Grid border
g.append("rect")
  .attr("width", gridSide).attr("height", gridSide)
  .attr("fill", "none")
  .attr("stroke", t.inkSoft).attr("stroke-width", 2);

// Internal grid lines
for (let k = 1; k < 5; k++) {
  g.append("line")
    .attr("x1", k * cellSize).attr("y1", 0)
    .attr("x2", k * cellSize).attr("y2", gridSide)
    .attr("stroke", t.inkSoft).attr("stroke-opacity", 0.35).attr("stroke-width", 1);
  g.append("line")
    .attr("x1", 0).attr("y1", k * cellSize)
    .attr("x2", gridSide).attr("y2", k * cellSize)
    .attr("stroke", t.inkSoft).attr("stroke-opacity", 0.35).attr("stroke-width", 1);
}

// X-axis: Likelihood tick labels
const likelihoodLabels = ["Rare", "Unlikely", "Possible", "Likely", ["Almost", "Certain"]];
likelihoodLabels.forEach((label, idx) => {
  const x = (idx + 0.5) * cellSize;
  const lines = Array.isArray(label) ? label : [label];
  const txt = g.append("text")
    .attr("x", x).attr("y", gridSide + 26)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft).style("font-size", "14px");
  lines.forEach((line, li) =>
    txt.append("tspan").attr("x", x).attr("dy", li === 0 ? 0 : 18).text(line)
  );
});

g.append("text")
  .attr("x", gridSide / 2).attr("y", gridSide + 88)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "15px").style("font-weight", "600")
  .text("Likelihood →");

// Y-axis: Impact tick labels
["Negligible", "Minor", "Moderate", "Major", "Catastrophic"].forEach((label, idx) => {
  g.append("text")
    .attr("x", -14).attr("y", (4.5 - idx) * cellSize)
    .attr("text-anchor", "end").attr("dominant-baseline", "middle")
    .attr("fill", t.inkSoft).style("font-size", "14px")
    .text(label);
});

g.append("text")
  .attr("transform", `translate(${-148},${gridSide / 2}) rotate(-90)`)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "15px").style("font-weight", "600")
  .text("Impact →");

// Risk item markers (numbered circles)
risks.forEach((r, idx) => {
  const cx = (r.l - 0.5) * cellSize;
  const cy = (5.5 - r.i) * cellSize;

  g.append("circle")
    .attr("cx", cx).attr("cy", cy).attr("r", 14)
    .attr("fill", t.ink).attr("fill-opacity", 0.84)
    .attr("stroke", t.pageBg).attr("stroke-width", 2.5);

  g.append("text")
    .attr("x", cx).attr("y", cy)
    .attr("text-anchor", "middle").attr("dominant-baseline", "central")
    .attr("fill", t.pageBg)
    .style("font-size", "11px").style("font-weight", "700")
    .text(idx + 1);
});

// Zone legend strip
const zoneY = gridSide + 120;
const zoneBoxW = Math.floor((gridSide - 9) / 4);

g.append("text")
  .attr("x", 0).attr("y", zoneY - 9)
  .attr("fill", t.ink).style("font-size", "13px").style("font-weight", "600")
  .text("Risk Zones");

ZONE.forEach(({ color, label, opacity }, idx) => {
  const zx = idx * (zoneBoxW + 3);
  g.append("rect")
    .attr("x", zx).attr("y", zoneY)
    .attr("width", zoneBoxW).attr("height", 16)
    .attr("fill", color).attr("fill-opacity", opacity).attr("rx", 3);
  g.append("text")
    .attr("x", zx + zoneBoxW / 2).attr("y", zoneY + 31)
    .attr("text-anchor", "middle")
    .attr("fill", t.inkSoft).style("font-size", "12px")
    .text(label);
});

// Risk item index
const itemY = zoneY + 56;

g.append("text")
  .attr("x", 0).attr("y", itemY - 9)
  .attr("fill", t.ink).style("font-size", "13px").style("font-weight", "600")
  .text("Risk Items");

const cols = 3;
const colW = Math.floor(gridSide / cols);
risks.forEach((r, idx) => {
  const col = idx % cols;
  const row = Math.floor(idx / cols);
  g.append("text")
    .attr("x", col * colW).attr("y", itemY + row * 21)
    .attr("fill", t.inkSoft).style("font-size", "12px")
    .text(`${idx + 1}. ${r.name}`);
});

// Title
svg.append("text")
  .attr("x", margin.left + gridSide / 2).attr("y", 54)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px").style("font-weight", "600")
  .text("heatmap-risk-matrix · javascript · d3 · anyplot.ai");
