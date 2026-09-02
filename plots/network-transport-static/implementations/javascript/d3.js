// anyplot.ai
// network-transport-static: Static Transport Network Diagram
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 90, right: 50, bottom: 95, left: 50 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data: regional rail network (fixed layout, no force simulation) -------
const stations = [
  { id: "cen", label: "Central Station", x: 500, y: 330 },
  { id: "noj", label: "North Junction", x: 500, y: 90 },
  { id: "lak", label: "Lakeside", x: 220, y: 160 },
  { id: "riv", label: "Riverside", x: 830, y: 210 },
  { id: "egt", label: "Eastgate", x: 900, y: 330 },
  { id: "wfd", label: "Westfield", x: 130, y: 330 },
  { id: "spt", label: "Southport", x: 320, y: 520 },
  { id: "hbv", label: "Harborview", x: 680, y: 520 },
  { id: "mlb", label: "Millbrook", x: 500, y: 600 },
  { id: "apt", label: "Airport", x: 1040, y: 140 },
  { id: "olt", label: "Oldtown", x: 20, y: 560 },
  { id: "grw", label: "Greenwood", x: 760, y: 60 },
];

const routes = [
  { source: "cen", target: "noj", routeId: "RE1", dep: "08:00", arr: "08:20", type: "regional" },
  { source: "noj", target: "cen", routeId: "RE1", dep: "08:35", arr: "08:55", type: "regional" },
  { source: "cen", target: "lak", routeId: "RE2", dep: "08:05", arr: "08:32", type: "regional" },
  { source: "lak", target: "cen", routeId: "RE2", dep: "08:40", arr: "09:07", type: "regional" },
  { source: "cen", target: "riv", routeId: "RE3", dep: "08:10", arr: "08:38", type: "regional" },
  { source: "riv", target: "cen", routeId: "RE3", dep: "08:45", arr: "09:13", type: "regional" },
  { source: "cen", target: "egt", routeId: "IC10", dep: "08:00", arr: "08:22", type: "express" },
  { source: "egt", target: "cen", routeId: "IC10", dep: "08:30", arr: "08:52", type: "express" },
  { source: "cen", target: "egt", routeId: "RE6", dep: "08:15", arr: "08:45", type: "regional" },
  { source: "cen", target: "wfd", routeId: "S1", dep: "08:15", arr: "08:28", type: "local" },
  { source: "wfd", target: "cen", routeId: "S1", dep: "08:35", arr: "08:48", type: "local" },
  { source: "cen", target: "spt", routeId: "S2", dep: "08:20", arr: "08:42", type: "local" },
  { source: "spt", target: "cen", routeId: "S2", dep: "08:50", arr: "09:12", type: "local" },
  { source: "cen", target: "hbv", routeId: "RE4", dep: "08:25", arr: "08:53", type: "regional" },
  { source: "hbv", target: "cen", routeId: "RE4", dep: "09:00", arr: "09:28", type: "regional" },
  { source: "cen", target: "mlb", routeId: "S3", dep: "08:30", arr: "08:40", type: "local" },
  { source: "noj", target: "grw", routeId: "RE5", dep: "08:40", arr: "08:58", type: "regional" },
  { source: "grw", target: "apt", routeId: "IC11", dep: "09:05", arr: "09:22", type: "express" },
  { source: "noj", target: "lak", routeId: "S4", dep: "08:50", arr: "09:05", type: "local" },
  { source: "wfd", target: "olt", routeId: "S5", dep: "08:45", arr: "08:58", type: "local" },
  { source: "olt", target: "wfd", routeId: "S5", dep: "09:05", arr: "09:18", type: "local" },
];

const typeColor = { regional: t.palette[0], express: t.palette[1], local: t.palette[2] };
const typeLabel = { regional: "Regional", express: "Express", local: "Local" };
const nodeRadius = 32;

// --- Layout: map data coordinates into the drawing area, aspect preserved --
// (a single uniform `scale` keeps xScale/yScale slopes equal, so d3.scaleLinear
// can be used for both axes without distorting the network's shape)
const stationById = new Map(stations.map((s) => [s.id, s]));
const xExtent = d3.extent(stations, (d) => d.x);
const yExtent = d3.extent(stations, (d) => d.y);
const dataW = xExtent[1] - xExtent[0];
const dataH = yExtent[1] - yExtent[0];
const pad = nodeRadius + 45;
const scale = Math.min((iw - 2 * pad) / dataW, (ih - 2 * pad) / dataH);
const offsetX = (iw - dataW * scale) / 2;
const offsetY = (ih - dataH * scale) / 2;
const xScale = d3.scaleLinear().domain(xExtent).range([offsetX, offsetX + dataW * scale]);
const yScale = d3.scaleLinear().domain(yExtent).range([offsetY, offsetY + dataH * scale]);
for (const s of stations) {
  s.cx = xScale(s.x);
  s.cy = yScale(s.y);
}

// --- SVG mount --------------------------------------------------------------
const svg = d3
  .select("#container")
  .append("svg")
  .attr("width", width)
  .attr("height", height)
  .style("font-family", "'Inter', 'Helvetica Neue', Arial, sans-serif");
const defs = svg.append("defs");
const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// arrowhead markers, one per route type color
for (const [key, color] of Object.entries(typeColor)) {
  defs
    .append("marker")
    .attr("id", `arrow-${key}`)
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 9)
    .attr("refY", 0)
    .attr("markerWidth", 7)
    .attr("markerHeight", 7)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", color);
}

// --- Station nodes (drawn first so their footprint can repel edge labels;
// raised above the edges/labels layers at the very end for correct z-order) --
const nodeLayer = g.append("g").attr("class", "nodes");
const nodeObstacles = [];

const nodeCircles = nodeLayer
  .selectAll("circle.station")
  .data(stations)
  .join("circle")
  .attr("class", "station")
  .attr("cx", (d) => d.cx)
  .attr("cy", (d) => d.cy)
  .attr("r", nodeRadius)
  .attr("fill", t.elevatedBg)
  .attr("stroke", t.ink)
  .attr("stroke-width", 3);
nodeCircles.append("title").text((d) => d.label);
stations.forEach((s) => nodeObstacles.push({ x: s.cx, y: s.cy, hw: nodeRadius + 10, hh: nodeRadius + 10 }));

const nodeLabelGroups = nodeLayer
  .selectAll("g.station-label")
  .data(stations)
  .join("g")
  .attr("class", "station-label")
  .attr("transform", (d) => `translate(${d.cx},${d.cy + nodeRadius + 22})`);
nodeLabelGroups
  .append("text")
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .style("font-size", "15px")
  .style("font-weight", "600")
  .attr("fill", t.ink)
  .text((d) => d.label);
nodeLabelGroups.each(function (d) {
  const group = d3.select(this);
  const bbox = group.select("text").node().getBBox();
  group
    .insert("rect", "text")
    .attr("x", bbox.x - 6)
    .attr("y", bbox.y - 3)
    .attr("width", bbox.width + 12)
    .attr("height", bbox.height + 6)
    .attr("rx", 4)
    .attr("fill", t.pageBg)
    .attr("opacity", 0.85);
  nodeObstacles.push({ x: d.cx, y: d.cy + nodeRadius + 22, hw: bbox.width / 2 + 8, hh: bbox.height / 2 + 5 });
});

// --- Group routes by unordered station pair, so parallel routes fan out;
// trim endpoints so each path (and arrowhead) stops at the node's edge -----
const trim = (p, towards) => {
  const vx = towards.x - p.x;
  const vy = towards.y - p.y;
  const len = Math.sqrt(vx * vx + vy * vy) || 1;
  return { x: p.x + (vx / len) * nodeRadius, y: p.y + (vy / len) * nodeRadius };
};

const pairGroups = d3.group(routes, (r) => [r.source, r.target].sort().join("|"));
const routeGeometry = [];
for (const [key, group] of pairGroups) {
  const [aId, bId] = key.split("|");
  const a = stationById.get(aId);
  const b = stationById.get(bId);
  const dx = b.cx - a.cx;
  const dy = b.cy - a.cy;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const nx = -dy / dist;
  const ny = dx / dist;
  const step = 46;

  group.forEach((route, i) => {
    const offset = (i - (group.length - 1) / 2) * step;
    const src = stationById.get(route.source);
    const tgt = stationById.get(route.target);
    const mid = { x: (src.cx + tgt.cx) / 2 + nx * offset, y: (src.cy + tgt.cy) / 2 + ny * offset };
    const start = trim({ x: src.cx, y: src.cy }, mid);
    const end = trim({ x: tgt.cx, y: tgt.cy }, mid);
    // label anchored at the curve's midpoint (t=0.5 on the quadratic Bezier);
    // exact placement is resolved below by the collision-avoidance pass, since
    // labels from unrelated edges meeting at the same hub can also collide
    const labelPoint = { x: 0.25 * src.cx + 0.5 * mid.x + 0.25 * tgt.cx, y: 0.25 * src.cy + 0.5 * mid.y + 0.25 * tgt.cy };
    routeGeometry.push({ route, src, tgt, start, mid, end, labelPoint });
  });
}

const edgeLayer = g.append("g").attr("class", "edges");
const edgePaths = edgeLayer
  .selectAll("path.route")
  .data(routeGeometry)
  .join("path")
  .attr("class", "route")
  .attr("d", (d) => `M${d.start.x},${d.start.y} Q${d.mid.x},${d.mid.y} ${d.end.x},${d.end.y}`)
  .attr("fill", "none")
  .attr("stroke", (d) => typeColor[d.route.type])
  .attr("stroke-width", 3)
  .attr("stroke-linecap", "round")
  .attr("marker-end", (d) => `url(#arrow-${d.route.type})`);
edgePaths
  .append("title")
  .text((d) => `${d.route.routeId}: ${d.src.label} → ${d.tgt.label} (${d.route.dep} → ${d.route.arr})`);

const edgeLabelLayer = g.append("g").attr("class", "edge-labels");
const edgeLabelGroups = edgeLabelLayer
  .selectAll("g.edge-label")
  .data(routeGeometry)
  .join("g")
  .attr("class", "edge-label");
edgeLabelGroups
  .append("text")
  .attr("text-anchor", "middle")
  .attr("dominant-baseline", "middle")
  .style("font-size", "14px")
  .attr("fill", t.inkSoft)
  .text((d) => `${d.route.routeId} | ${d.route.dep} → ${d.route.arr}`);

const edgeLabels = [];
edgeLabelGroups.each(function (d) {
  const group = d3.select(this);
  const bbox = group.select("text").node().getBBox();
  group
    .insert("rect", "text")
    .attr("x", bbox.x - 5)
    .attr("y", bbox.y - 3)
    .attr("width", bbox.width + 10)
    .attr("height", bbox.height + 6)
    .attr("rx", 4)
    .attr("fill", t.elevatedBg)
    .attr("opacity", 0.92);
  edgeLabels.push({ el: group, x: d.labelPoint.x, y: d.labelPoint.y, hw: bbox.width / 2 + 6, hh: bbox.height / 2 + 4 });
});

// declutter: nudge apart any edge labels whose padded boxes still overlap —
// happens when several edges from the same hub meet at similar angles — and
// push edge labels away from the (fixed) station circles/labels they land on.
// Run as separate phases (not interleaved) so obstacle pushes can't undo a
// pairwise fix (or vice versa) before the system settles.
const declutterPairs = () => {
  for (let iter = 0; iter < 60; iter += 1) {
    for (let i = 0; i < edgeLabels.length; i += 1) {
      for (let j = i + 1; j < edgeLabels.length; j += 1) {
        const p = edgeLabels[i];
        const q = edgeLabels[j];
        const dx = q.x - p.x || 1;
        const dy = q.y - p.y || 1;
        const overlapX = p.hw + q.hw - Math.abs(dx);
        const overlapY = p.hh + q.hh - Math.abs(dy);
        if (overlapX > 0 && overlapY > 0) {
          if (overlapX < overlapY) {
            const shift = (overlapX / 2) * Math.sign(dx);
            p.x -= shift;
            q.x += shift;
          } else {
            const shift = (overlapY / 2) * Math.sign(dy);
            p.y -= shift;
            q.y += shift;
          }
        }
      }
    }
  }
};
const declutterObstacles = () => {
  for (let iter = 0; iter < 20; iter += 1) {
    for (const p of edgeLabels) {
      for (const obstacle of nodeObstacles) {
        const dx = p.x - obstacle.x || 1;
        const dy = p.y - obstacle.y || 1;
        const overlapX = p.hw + obstacle.hw - Math.abs(dx);
        const overlapY = p.hh + obstacle.hh - Math.abs(dy);
        if (overlapX > 0 && overlapY > 0) {
          if (overlapX < overlapY) {
            p.x += overlapX * Math.sign(dx);
          } else {
            p.y += overlapY * Math.sign(dy);
          }
        }
      }
    }
  }
};
for (let round = 0; round < 5; round += 1) {
  declutterPairs();
  declutterObstacles();
}

for (const label of edgeLabels) {
  label.el.attr("transform", `translate(${label.x},${label.y})`);
}
nodeLayer.raise();

// --- Legend: route type -> color, centered below the network ----------------
const legendItems = Object.keys(typeColor);
const legendGap = 220;
const legendStartX = width / 2 - ((legendItems.length - 1) * legendGap) / 2;
const legendY = height - 46;
const legend = svg.append("g").attr("class", "legend");
legendItems.forEach((key, i) => {
  const lx = legendStartX + i * legendGap;
  legend
    .append("line")
    .attr("x1", lx)
    .attr("x2", lx + 36)
    .attr("y1", legendY)
    .attr("y2", legendY)
    .attr("stroke", typeColor[key])
    .attr("stroke-width", 4)
    .attr("stroke-linecap", "round");
  legend
    .append("text")
    .attr("x", lx + 48)
    .attr("y", legendY)
    .attr("dominant-baseline", "middle")
    .style("font-size", "15px")
    .attr("fill", t.inkSoft)
    .text(typeLabel[key]);
});

// --- Title --------------------------------------------------------------------
svg
  .append("text")
  .attr("x", width / 2)
  .attr("y", 52)
  .attr("text-anchor", "middle")
  .style("font-size", "26px")
  .style("font-weight", "600")
  .attr("fill", t.ink)
  .text("network-transport-static · javascript · d3 · anyplot.ai");
