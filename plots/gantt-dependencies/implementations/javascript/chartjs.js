// anyplot.ai
// gantt-dependencies: Gantt Chart with Dependencies
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 89/100 | Updated: 2026-08-25

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

// --- Dependency-arrow plugin (finish-to-start connectors) --------------------
const dependencyArrows = {
  id: "dependencyArrows",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.strokeStyle = t.inkSoft;
    ctx.fillStyle = t.inkSoft;
    ctx.lineWidth = 2;
    for (const task of tasks) {
      if (!task.dependsOn.length) continue;
      const toY = scales.y.getPixelForValue(taskRowIndex.get(task.task));
      const toX = scales.x.getPixelForValue(task.start);
      for (const depName of task.dependsOn) {
        const pred = tasks.find((candidate) => candidate.task === depName);
        if (!pred) continue;
        const fromY = scales.y.getPixelForValue(taskRowIndex.get(pred.task));
        const fromX = scales.x.getPixelForValue(pred.end);
        const midX = (fromX + toX) / 2;

        ctx.beginPath();
        ctx.moveTo(fromX, fromY);
        ctx.lineTo(midX, fromY);
        ctx.lineTo(midX, toY);
        ctx.lineTo(toX - 8, toY);
        ctx.stroke();

        // Arrowhead pointing into the successor bar's start edge.
        ctx.beginPath();
        ctx.moveTo(toX, toY);
        ctx.lineTo(toX - 8, toY - 4);
        ctx.lineTo(toX - 8, toY + 4);
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
        title: { display: true, text: "Project Timeline (2026)", color: t.ink, font: { size: 15 } },
        ticks: { color: t.inkSoft, font: { size: 13 }, stepSize: 5, callback: (value) => formatDay(value) },
        grid: { color: t.grid },
      },
      y: {
        reverse: false,
        ticks: {
          color: (ctx) => (rows[ctx.index] && rows[ctx.index].isHeader ? t.ink : t.inkSoft),
          font: (ctx) => (rows[ctx.index] && rows[ctx.index].isHeader ? { size: 14, weight: "bold" } : { size: 13 }),
        },
        grid: { display: false },
      },
    },
  },
  plugins: [dependencyArrows],
});
