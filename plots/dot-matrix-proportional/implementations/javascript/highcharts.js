// anyplot.ai
// dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
// ANYPLOT_TOKENS has no "muted" field — derive the theme-adaptive muted-ink
// anchor locally (see prompts/default-style-guide.md "Theme-adaptive Chrome").
const inkMuted = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ---------------------------------------
const total = 100;
const gridCols = 10;
const gridRows = 10;

// Sentiment/polarity semantic exception: satisfied -> green, dissatisfied ->
// red, neutral -> the theme-adaptive muted anchor (default-style-guide.md
// "Color Philosophy" -> "Semantic exception").
const categories = [
  { name: "Satisfied", count: 47, color: t.palette[0] },
  { name: "Neutral", count: 31, color: inkMuted },
  { name: "Dissatisfied", count: 22, color: t.palette[4] },
];

// Fill dots left-to-right, top-to-bottom, sequentially across categories.
let cursor = 0;
const series = categories.map((cat) => {
  const data = [];
  for (let i = 0; i < cat.count; i += 1, cursor += 1) {
    data.push([cursor % gridCols, Math.floor(cursor / gridCols)]);
  }
  const pct = Math.round((cat.count / total) * 100);
  return {
    name: `${cat.name}: ${cat.count} (${pct}%)`,
    color: cat.color,
    data,
  };
});

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "dot-matrix-proportional · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Customer satisfaction survey · 100 respondents, one dot each",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -0.6,
    max: gridCols - 0.4,
    visible: false,
  },
  yAxis: {
    min: -0.6,
    max: gridRows - 0.4,
    reversed: true,
    title: { text: null },
    visible: false,
  },
  legend: {
    align: "center",
    verticalAlign: "bottom",
    symbolRadius: 6,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: "13px" },
    headerFormat: "",
    pointFormat: "{series.name}",
  },
  plotOptions: {
    series: {
      animation: false,
      marker: {
        radius: 38,
        symbol: "circle",
        lineWidth: 2,
        lineColor: t.pageBg,
      },
      states: { hover: { halo: { size: 0 } } },
    },
  },
  series,
});
