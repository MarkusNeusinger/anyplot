// anyplot.ai
// gauge-activity-rings: Activity Rings Progress Chart
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-14
//# anyplot-orientation: square
// anyplot.ai
// gauge-activity-rings: Activity Rings Progress Chart
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-14

const t = window.ANYPLOT_TOKENS;

// --- Data (daily fitness goals) ---
const metrics = [
  { name: "Steps",      value: 7842, goal: 10000, display: "7,842 / 10,000 steps" },
  { name: "Active Min", value: 48,   goal: 60,    display: "48 / 60 min"           },
  { name: "Stand",      value: 10,   goal: 12,    display: "10 / 12 hr"            },
];
const colors = [t.palette[0], t.palette[1], t.palette[2]];

// Track colors: ring hue at ~15% opacity
const trackColors = [
  "rgba(0,158,115,0.15)",
  "rgba(196,117,253,0.15)",
  "rgba(68,103,163,0.15)",
];

// Percentage completion (clamped to 100)
const pcts = metrics.map(m =>
  parseFloat(Math.min(m.value / m.goal * 100, 100).toFixed(1))
);

// Ring geometry: outer → inner, concentric
const radii = ["66%", "48%", "30%"];
const ringW  = 34;  // CSS px (→ 68 physical px at DPR 2)

// --- Init ---
const chart = echarts.init(document.getElementById("container"));

// --- Option ---
chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: {
    text: "gauge-activity-rings · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "normal" },
  },

  // Center labels + bottom values row (1200×1200 CSS mount, center at 600,600)
  graphic: {
    elements: [
      // "Daily Goals" header above the per-ring labels
      {
        type: "text",
        style: {
          x: 600, y: 556,
          text: "Daily Goals",
          fill: t.inkSoft,
          fontSize: 14,
          textAlign: "center",
          fontStyle: "italic",
        },
      },
      // Per-ring: "Metric: XX.X%" in the ring's color
      ...metrics.map((m, i) => ({
        type: "text",
        style: {
          x: 600, y: 594 + i * 36,
          text: `${m.name}: ${pcts[i]}%`,
          fill: colors[i],
          fontSize: 17,
          fontWeight: "bold",
          textAlign: "center",
        },
      })),
      // Bottom row: raw values for each metric
      {
        type: "text",
        style: {
          x: 600, y: 1062,
          text: metrics.map(m => m.display).join("   ·   "),
          fill: t.inkSoft,
          fontSize: 14,
          textAlign: "center",
        },
      },
    ],
  },

  series: metrics.map((m, i) => ({
    type: "gauge",
    startAngle: 90,
    endAngle: -270,   // full circle clockwise from top
    min: 0,
    max: 100,
    radius: radii[i],
    center: ["50%", "50%"],
    progress: {
      show: true,
      roundCap: true,
      width: ringW,
      itemStyle: { color: colors[i] },
    },
    axisLine: {
      roundCap: true,
      lineStyle: { width: ringW, color: [[1, trackColors[i]]] },
    },
    pointer:   { show: false },
    axisTick:  { show: false },
    splitLine: { show: false },
    axisLabel: { show: false },
    detail:    { show: false },
    title:     { show: false },
    data: [{ value: pcts[i] }],
  })),
});
