// anyplot.ai
// pictogram-basic: Pictogram Chart (Isotype Visualization)
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-20

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
const UNIT = 5; // thousand tons represented by each icon
const rows = [
  { category: "Apples", value: 47 },
  { category: "Bananas", value: 38 },
  { category: "Oranges", value: 29 },
  { category: "Grapes", value: 21 },
  { category: "Strawberries", value: 14 },
];

function buildIcons(value) {
  const full = Math.floor(value / UNIT);
  const remainder = (value - full * UNIT) / UNIT;
  const icons = [];
  for (let i = 0; i < full; i++) icons.push(1);
  if (remainder > 0.02) icons.push(0.3 + 0.7 * remainder); // keep faint remainders legible
  return icons;
}

const iconCounts = rows.map((row) => buildIcons(row.value));
const maxIcons = Math.max(...iconCounts.map((icons) => icons.length));

const categories = rows.map((row) => `${row.category} — ${row.value}k t`);

const series = rows.map((row, i) => ({
  name: row.category,
  dataLabels: { style: { color: t.palette[i] } },
  data: iconCounts[i].map((opacity, x) => ({
    x,
    y: i,
    dataLabels: { style: { opacity } },
  })),
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "pictogram-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  caption: {
    text: `Each ● represents ${UNIT},000 tons of annual fruit production`,
    align: "left",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -0.5,
    max: maxIcons - 0.5,
    gridLineWidth: 0,
    lineWidth: 0,
    tickLength: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  yAxis: {
    categories,
    reversed: true,
    gridLineWidth: 0,
    lineWidth: 0,
    tickLength: 0,
    title: { text: null },
    labels: { style: { color: t.inkSoft, fontSize: "16px" } },
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    scatter: {
      animation: false,
      marker: { enabled: false },
      dataLabels: {
        enabled: true,
        format: "●",
        align: "center",
        verticalAlign: "middle",
        y: 0,
        style: { fontSize: "30px", fontWeight: "normal", textOutline: "none" },
      },
    },
  },
  series,
});
