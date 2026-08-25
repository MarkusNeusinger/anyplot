// anyplot.ai
// gantt-dependencies: Gantt Chart with Dependencies
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-25
//# anyplot-orientation: landscape
// anyplot.ai
// gantt-dependencies: Gantt Chart with Dependencies
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Software release plan: four sequential phases, each a group of dependent tasks.
const day = (year, month, date) => Date.UTC(year, month - 1, date);

const rows = [
  { name: "Requirements", isGroup: true },
  { name: "Gather Requirements", group: "Requirements", start: day(2026, 1, 5), end: day(2026, 1, 9), deps: [] },
  { name: "Stakeholder Review", group: "Requirements", start: day(2026, 1, 9), end: day(2026, 1, 12), deps: ["Gather Requirements"] },
  { name: "Design", isGroup: true },
  { name: "System Architecture", group: "Design", start: day(2026, 1, 12), end: day(2026, 1, 19), deps: ["Stakeholder Review"] },
  { name: "UI/UX Design", group: "Design", start: day(2026, 1, 12), end: day(2026, 1, 21), deps: ["Stakeholder Review"] },
  { name: "Development", isGroup: true },
  { name: "Backend API", group: "Development", start: day(2026, 1, 19), end: day(2026, 2, 2), deps: ["System Architecture"] },
  { name: "Database Setup", group: "Development", start: day(2026, 1, 19), end: day(2026, 1, 26), deps: ["System Architecture"] },
  { name: "Frontend Implementation", group: "Development", start: day(2026, 1, 21), end: day(2026, 2, 4), deps: ["UI/UX Design"] },
  { name: "Testing", isGroup: true },
  { name: "Integration Testing", group: "Testing", start: day(2026, 2, 4), end: day(2026, 2, 9), deps: ["Backend API", "Database Setup", "Frontend Implementation"] },
  { name: "QA Review", group: "Testing", start: day(2026, 2, 9), end: day(2026, 2, 12), deps: ["Integration Testing"] },
  { name: "Deployment", group: "Testing", start: day(2026, 2, 12), end: day(2026, 2, 13), deps: ["QA Review"] },
];

// Group headers show the aggregate span of their child tasks.
rows.forEach((row) => {
  if (!row.isGroup) return;
  const children = rows.filter((r) => r.group === row.name);
  row.start = Math.min(...children.map((r) => r.start));
  row.end = Math.max(...children.map((r) => r.end));
});

const rowIndex = new Map(rows.map((row, i) => [row.name, i]));
const groupColor = {
  Requirements: t.palette[0],
  Design: t.palette[1],
  Development: t.palette[2],
  Testing: t.palette[3],
};

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// One bar per row — group headers render as thin outlined spans, tasks as solid bars.
const barData = rows.map((row, i) => {
  const color = groupColor[row.group || row.name];
  return {
    value: [i, row.start, row.end, row.isGroup ? 1 : 0],
    itemStyle: row.isGroup
      ? { color: hexToRgba(color, 0.28), borderColor: color, borderWidth: 2 }
      : { color },
  };
});

// Dependency edges: predecessor's end (finish) -> successor's start.
const depData = [];
rows.forEach((row) => {
  if (!row.deps) return;
  row.deps.forEach((predName) => {
    const pred = rows[rowIndex.get(predName)];
    depData.push({ value: [rowIndex.get(predName), pred.end, rowIndex.get(row.name), row.start] });
  });
});

function renderTask(params, api) {
  const idx = api.value(0);
  const isGroup = api.value(3) === 1;
  const start = api.coord([api.value(1), idx]);
  const end = api.coord([api.value(2), idx]);
  const rowHeight = api.size([0, 1])[1];
  const barHeight = isGroup ? rowHeight * 0.32 : rowHeight * 0.56;
  const shape = echarts.graphic.clipRectByRect(
    { x: start[0], y: start[1] - barHeight / 2, width: Math.max(end[0] - start[0], 2), height: barHeight },
    { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height }
  );
  return shape && { type: "rect", shape, style: api.style() };
}

// Elbow connector (horizontal-vertical-horizontal) with an arrowhead landing on
// the successor's left edge — keeps the line out of the row band between the
// two tasks rather than cutting diagonally across intermediate bars.
function renderDependency(params, api) {
  const p1 = api.coord([api.value(1), api.value(0)]);
  const p2 = api.coord([api.value(3), api.value(2)]);
  const arrow = 9;
  const gap = Math.min(28, Math.max((p2[0] - p1[0]) / 2, 10));
  const midX = p1[0] + gap;
  return {
    type: "group",
    children: [
      {
        type: "polyline",
        shape: {
          points: [
            [p1[0], p1[1]],
            [midX, p1[1]],
            [midX, p2[1]],
            [p2[0] - arrow, p2[1]],
          ],
        },
        style: { stroke: t.inkSoft, lineWidth: 2, fill: "none" },
      },
      {
        type: "polygon",
        shape: {
          points: [
            [p2[0], p2[1]],
            [p2[0] - arrow, p2[1] - arrow / 2],
            [p2[0] - arrow, p2[1] + arrow / 2],
          ],
        },
        style: { fill: t.inkSoft },
      },
    ],
  };
}

function formatDate(ts) {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dt = new Date(ts);
  return `${months[dt.getUTCMonth()]} ${dt.getUTCDate()}`;
}

function formatRowLabel(name, index) {
  return rows[index].isGroup ? `{group|${name}}` : `{task|${name}}`;
}

const title = "Software Release Plan · gantt-dependencies · javascript · echarts · anyplot.ai";
const titleFontSize = title.length > 67 ? Math.round(22 * (67 / title.length)) : 22;

const minStart = Math.min(...rows.map((r) => r.start));
const maxEnd = Math.max(...rows.map((r) => r.end));
const pad = 2 * 24 * 60 * 60 * 1000; // 2-day breathing room on each side

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  grid: { left: 300, right: 70, top: 90, bottom: 70 },
  xAxis: {
    // A plain value axis (timestamps in ms) rather than type "time" — the
    // "time" axis's automatic "nice" tick picker always adds a tick at each
    // month boundary in addition to its regular interval, which can land the
    // two ticks a single day apart and overlap. A value axis honors a fixed
    // "interval" exactly, so a 4-day cadence is guaranteed to space out labels.
    type: "value",
    min: minStart - pad,
    max: maxEnd + pad,
    interval: 4 * 24 * 60 * 60 * 1000,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: formatDate },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "category",
    inverse: true,
    data: rows.map((r) => r.name),
    axisLabel: {
      fontSize: 15,
      formatter: formatRowLabel,
      rich: {
        group: { color: t.ink, fontWeight: 700, fontSize: 16 },
        task: { color: t.inkSoft, fontSize: 14, padding: [0, 0, 0, 22] },
      },
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    { type: "custom", name: "Tasks", renderItem: renderTask, encode: { x: [1, 2], y: 0 }, data: barData, z: 2 },
    { type: "custom", name: "Dependencies", renderItem: renderDependency, data: depData, silent: true, z: 3 },
  ],
});
chart.on("finished", () => {
  window.__anyplotReady = true;
});
