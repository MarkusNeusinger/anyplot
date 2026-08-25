// anyplot.ai
// gantt-dependencies: Gantt Chart with Dependencies
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 94/100 | Updated: 2026-08-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Software delivery sprint: four phases, each with its own tasks. start/end
// are day offsets from PROJECT_START. A dependent task's start never precedes
// the latest end of its predecessors.
const PROJECT_START = new Date(2026, 1, 2); // Mon Feb 2, 2026

const GROUPS = ["Requirements", "Design", "Development", "Testing"];

const tasks = [
  { task: "Stakeholder Interviews", group: "Requirements", start: 0, end: 4, dependsOn: [] },
  { task: "Gather Requirements", group: "Requirements", start: 0, end: 5, dependsOn: [] },
  { task: "Requirements Sign-off", group: "Requirements", start: 5, end: 8, dependsOn: ["Stakeholder Interviews", "Gather Requirements"] },
  { task: "System Architecture", group: "Design", start: 8, end: 14, dependsOn: ["Requirements Sign-off"] },
  { task: "UI/UX Design", group: "Design", start: 8, end: 16, dependsOn: ["Requirements Sign-off"] },
  { task: "Database Schema", group: "Design", start: 14, end: 18, dependsOn: ["System Architecture"] },
  { task: "API Development", group: "Development", start: 18, end: 29, dependsOn: ["Database Schema"] },
  { task: "Frontend Build", group: "Development", start: 16, end: 30, dependsOn: ["UI/UX Design"] },
  { task: "Data Pipeline", group: "Development", start: 18, end: 27, dependsOn: ["Database Schema"] },
  { task: "Auth Integration", group: "Development", start: 29, end: 33, dependsOn: ["API Development"] },
  { task: "Unit Testing", group: "Testing", start: 27, end: 32, dependsOn: ["Data Pipeline"] },
  { task: "Integration Testing", group: "Testing", start: 33, end: 38, dependsOn: ["Auth Integration", "Frontend Build"] },
  { task: "User Acceptance Testing", group: "Testing", start: 38, end: 43, dependsOn: ["Integration Testing", "Unit Testing"] },
];

const groupColor = Object.fromEntries(GROUPS.map((g, i) => [g, t.palette[i]]));

// --- Rows: a header row per group (aggregate span) above its indented tasks -
const rows = [];
const taskRowIndex = new Map();
for (const group of GROUPS) {
  const members = tasks.filter((task) => task.group === group);
  const groupStart = Math.min(...members.map((task) => task.start));
  const groupEnd = Math.max(...members.map((task) => task.end));
  rows.push({ label: group.toUpperCase(), isHeader: true, color: groupColor[group], start: groupStart, end: groupEnd });
  for (const task of members) {
    taskRowIndex.set(task.task, rows.length);
    rows.push({ label: `  ${task.task}`, isHeader: false, color: groupColor[group], start: task.start, end: task.end });
  }
}

// --- Critical path: the chain of tasks binding the project finish date -----
// Walk back from the last-finishing task, at each step following whichever
// predecessor finishes latest (the one actually constraining the successor's
// start). Rendered with heavier emphasis so the driving chain stands out.
const tasksByName = new Map(tasks.map((task) => [task.task, task]));
const criticalEdges = new Set();
{
  let current = tasks.reduce((latest, task) => (task.end > latest.end ? task : latest), tasks[0]);
  while (current.dependsOn.length) {
    let predName = current.dependsOn[0];
    let pred = tasksByName.get(predName);
    for (const depName of current.dependsOn) {
      const dep = tasksByName.get(depName);
      if (dep.end > pred.end) {
        pred = dep;
        predName = depName;
      }
    }
    criticalEdges.add(`${predName}=>${current.task}`);
    current = pred;
  }
}

const labels = rows.map((row) => row.label);
const barData = rows.map((row) => [row.start, row.end]);
const barBackground = rows.map((row) => (row.isHeader ? "transparent" : row.color));
const barBorder = rows.map((row) => row.color);
const barBorderWidth = rows.map((row) => (row.isHeader ? 3 : 0));

function formatDay(offset) {
  const date = new Date(PROJECT_START.getTime() + offset * 86400000);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Find a day offset in [loX, hiX] for the elbow's vertical segment that
// avoids passing through any of the given task bars (each a [start, end]
// range), preferring the value closest to the midpoint.
function freeElbowX(loX, hiX, blockingRanges) {
  const mid = (loX + hiX) / 2;
  const isBlocked = (x) => blockingRanges.some(([s, e]) => x > s && x < e);
  if (!isBlocked(mid)) return mid;
  const step = 0.1;
  for (let d = step; d <= (hiX - loX) / 2 + step; d += step) {
    const right = mid + d;
    if (right <= hiX && !isBlocked(right)) return right;
    const left = mid - d;
    if (left >= loX && !isBlocked(left)) return left;
  }
  return mid;
}

// --- Dependency-arrow plugin (finish-to-start connectors) --------------------
const dependencyArrows = {
  id: "dependencyArrows",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    const arrowSize = 11;
    for (const task of tasks) {
      if (!task.dependsOn.length) continue;
      const toRow = taskRowIndex.get(task.task);
      const toY = scales.y.getPixelForValue(toRow);
      const toX = scales.x.getPixelForValue(task.start);
      for (const depName of task.dependsOn) {
        const pred = tasks.find((candidate) => candidate.task === depName);
        if (!pred) continue;
        const fromRow = taskRowIndex.get(pred.task);
        const fromY = scales.y.getPixelForValue(fromRow);
        const fromX = scales.x.getPixelForValue(pred.end);

        // Route the elbow's vertical segment through a day offset not
        // covered by any task bar strictly between the two rows, so the
        // connector doesn't cut across unrelated tasks.
        const rowLo = Math.min(fromRow, toRow);
        const rowHi = Math.max(fromRow, toRow);
        const blockingRanges = rows
          .slice(rowLo + 1, rowHi)
          .filter((row) => !row.isHeader)
          .map((row) => [row.start, row.end]);
        const midDay = freeElbowX(pred.end, task.start, blockingRanges);
        const midX = scales.x.getPixelForValue(midDay);

        const isCritical = criticalEdges.has(`${depName}=>${task.task}`);
        ctx.strokeStyle = isCritical ? t.ink : t.inkSoft;
        ctx.fillStyle = isCritical ? t.ink : t.inkSoft;
        ctx.lineWidth = isCritical ? 3 : 2;

        ctx.beginPath();
        ctx.moveTo(fromX, fromY);
        ctx.lineTo(midX, fromY);
        ctx.lineTo(midX, toY);
        ctx.lineTo(toX - arrowSize, toY);
        ctx.stroke();

        // Arrowhead pointing into the successor bar's start edge.
        ctx.beginPath();
        ctx.moveTo(toX, toY);
        ctx.lineTo(toX - arrowSize, toY - arrowSize / 2);
        ctx.lineTo(toX - arrowSize, toY + arrowSize / 2);
        ctx.closePath();
        ctx.fill();
      }
    }
    ctx.restore();
  },
};

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "Timeline",
        data: barData,
        backgroundColor: barBackground,
        borderColor: barBorder,
        borderWidth: barBorderWidth,
        borderSkipped: false,
        barPercentage: 0.7,
        categoryPercentage: 0.8,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { right: 24 } },
    plugins: {
      title: {
        display: true,
        text: "Software Delivery Plan · gantt-dependencies · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 19 }, // 67/79 chars × 22px default title size, rounded
        padding: { bottom: 20 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        min: 0,
        max: 45,
        title: { display: true, text: "Project Timeline (2026)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 15 }, stepSize: 5, callback: (value) => formatDay(value) },
        grid: { color: t.grid },
      },
      y: {
        reverse: false,
        ticks: {
          color: (ctx) => (rows[ctx.index] && rows[ctx.index].isHeader ? t.ink : t.inkSoft),
          font: (ctx) => (rows[ctx.index] && rows[ctx.index].isHeader ? { size: 16, weight: "bold" } : { size: 15 }),
        },
        grid: { display: false },
      },
    },
  },
  plugins: [dependencyArrows],
});
