// anyplot.ai
// gantt-dependencies: Gantt Chart with Dependencies
// Library: d3 7.9.0 | JavaScript 22.23.2
// Quality: 79/100 | Updated: 2026-08-25

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const margin = { top: 110, right: 60, bottom: 60, left: 230 };
const iw = width - margin.left - margin.right;
const ih = height - margin.top - margin.bottom;

// --- Data (in-memory, deterministic) ----------------------------------------
// Offsets are workdays from the project kickoff date.
const PROJECT_START = new Date(2026, 0, 5);
const dayToDate = (d) => new Date(PROJECT_START.getTime() + d * 86400000);

const GROUPS = [
  {
    name: "Requirements",
    tasks: [
      { task: "Gather Requirements", start: 0, end: 5 },
      { task: "Stakeholder Review", start: 5, end: 8, dependsOn: ["Gather Requirements"] },
    ],
  },
  {
    name: "Design",
    tasks: [
      { task: "System Architecture", start: 8, end: 14, dependsOn: ["Stakeholder Review"] },
      { task: "UI/UX Design", start: 8, end: 16, dependsOn: ["Stakeholder Review"] },
      { task: "Database Schema", start: 14, end: 18, dependsOn: ["System Architecture"] },
    ],
  },
  {
    name: "Development",
    tasks: [
      { task: "Backend API", start: 18, end: 32, dependsOn: ["Database Schema"] },
      { task: "Frontend Components", start: 16, end: 30, dependsOn: ["UI/UX Design"] },
      { task: "Auth Module", start: 18, end: 26, dependsOn: ["Database Schema"] },
      { task: "Integration", start: 32, end: 36, dependsOn: ["Backend API", "Frontend Components"] },
    ],
  },
  {
    name: "Testing",
    tasks: [
      { task: "Unit Testing", start: 26, end: 34, dependsOn: ["Auth Module"] },
      { task: "Integration Testing", start: 36, end: 42, dependsOn: ["Integration"] },
      { task: "User Acceptance Testing", start: 42, end: 46, dependsOn: ["Integration Testing"] },
    ],
  },
  {
    name: "Deployment",
    tasks: [
      { task: "Staging Deployment", start: 46, end: 49, dependsOn: ["User Acceptance Testing"] },
      { task: "Production Release", start: 49, end: 52, dependsOn: ["Staging Deployment"] },
    ],
  },
];

// --- Flatten into rows (group header row, then its indented task rows) ------
const rows = [];
GROUPS.forEach((group, groupIndex) => {
  const groupStart = d3.min(group.tasks, (d) => d.start);
  const groupEnd = d3.max(group.tasks, (d) => d.end);
  rows.push({ kind: "group", name: group.name, start: groupStart, end: groupEnd, groupIndex });
  group.tasks.forEach((d) => rows.push({ kind: "task", ...d, groupIndex }));
});

const allStart = d3.min(rows, (d) => d.start);
const allEnd = d3.max(rows, (d) => d.end);

// --- Scales -------------------------------------------------------------------
const x = d3.scaleTime()
  .domain([dayToDate(allStart), dayToDate(allEnd)])
  .nice(d3.timeWeek)
  .range([0, iw]);

const rowHeight = ih / rows.length;
const y = (i) => i * rowHeight + rowHeight / 2;

// --- SVG mount ----------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

svg.append("defs").append("marker")
  .attr("id", "arrowhead")
  .attr("viewBox", "0 0 10 10")
  .attr("refX", 9)
  .attr("refY", 5)
  .attr("markerWidth", 7)
  .attr("markerHeight", 7)
  .attr("orient", "auto-start-reverse")
  .append("path")
  .attr("d", "M0,0 L10,5 L0,10 Z")
  .attr("fill", t.inkSoft);

const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

// --- Axes -----------------------------------------------------------------
const xAxis = g.append("g")
  .attr("transform", `translate(0,${ih})`)
  .call(d3.axisBottom(x).ticks(d3.timeWeek.every(1)).tickFormat(d3.timeFormat("%b %d")));
xAxis.selectAll("text").attr("fill", t.inkSoft).style("font-size", "13px");
xAxis.selectAll("line").attr("stroke", t.grid);
xAxis.select(".domain").attr("stroke", t.inkSoft);

g.append("g")
  .attr("class", "grid")
  .selectAll("line")
  .data(x.ticks(d3.timeWeek.every(1)))
  .join("line")
  .attr("x1", (d) => x(d))
  .attr("x2", (d) => x(d))
  .attr("y1", 0)
  .attr("y2", ih)
  .attr("stroke", t.grid)
  .attr("stroke-width", 1);

// --- Row labels (group names bold, task names indented) -----------------------
rows.forEach((row, i) => {
  g.append("text")
    .attr("x", row.kind === "group" ? -30 : -14)
    .attr("y", y(i))
    .attr("dy", "0.32em")
    .attr("text-anchor", "end")
    .style("font-size", row.kind === "group" ? "14px" : "13px")
    .style("font-weight", row.kind === "group" ? "600" : "400")
    .attr("fill", row.kind === "group" ? t.ink : t.inkSoft)
    .text(row.name || row.task);
});

// --- Group aggregate span bars (thin bracket behind the group's tasks) --------
rows.forEach((row, i) => {
  if (row.kind !== "group") return;
  g.append("rect")
    .attr("x", x(dayToDate(row.start)))
    .attr("y", y(i) - rowHeight * 0.16)
    .attr("width", x(dayToDate(row.end)) - x(dayToDate(row.start)))
    .attr("height", rowHeight * 0.32)
    .attr("rx", 3)
    .attr("fill", t.palette[row.groupIndex % t.palette.length])
    .attr("fill-opacity", 0.35);
});

// --- Task bars ------------------------------------------------------------
const barHeight = rowHeight * 0.6;
const taskLayout = new Map();
rows.forEach((row, i) => {
  if (row.kind !== "task") return;
  const xStart = x(dayToDate(row.start));
  const xEnd = x(dayToDate(row.end));
  g.append("rect")
    .attr("x", xStart)
    .attr("y", y(i) - barHeight / 2)
    .attr("width", Math.max(xEnd - xStart, 2))
    .attr("height", barHeight)
    .attr("rx", 4)
    .attr("fill", t.palette[row.groupIndex % t.palette.length]);
  taskLayout.set(row.task, { xStart, xEnd, yMid: y(i) });
});

// --- Dependency arrows: predecessor's right edge -> successor's left edge ----
rows.forEach((row) => {
  if (row.kind !== "task" || !row.dependsOn) return;
  const to = taskLayout.get(row.task);
  row.dependsOn.forEach((depName) => {
    const from = taskLayout.get(depName);
    if (!from) return;
    const midX = from.xEnd + Math.max((to.xStart - from.xEnd) / 2, 10);
    const path = [
      [from.xEnd, from.yMid],
      [midX, from.yMid],
      [midX, to.yMid],
      [to.xStart - 6, to.yMid],
    ];
    g.append("path")
      .attr("d", d3.line()(path))
      .attr("fill", "none")
      .attr("stroke", t.inkSoft)
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#arrowhead)");
  });
});

// --- Legend: group colors ------------------------------------------------
const legend = svg.append("g").attr("transform", `translate(${margin.left},${margin.top - 46})`);
let legendX = 0;
GROUPS.forEach((group, i) => {
  const item = legend.append("g").attr("transform", `translate(${legendX},0)`);
  item.append("rect")
    .attr("width", 14)
    .attr("height", 14)
    .attr("rx", 3)
    .attr("fill", t.palette[i % t.palette.length]);
  const label = item.append("text")
    .attr("x", 20)
    .attr("y", 11)
    .style("font-size", "13px")
    .attr("fill", t.inkSoft)
    .text(group.name);
  legendX += 20 + label.node().getComputedTextLength() + 28;
});

// --- Title ------------------------------------------------------------------
svg.append("text")
  .attr("x", width / 2)
  .attr("y", 44)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px")
  .style("font-weight", "600")
  .text("gantt-dependencies · javascript · d3 · anyplot.ai");
