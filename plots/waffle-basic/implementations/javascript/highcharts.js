// anyplot.ai
// waffle-basic: Basic Waffle Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-09

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const departments = [
  { name: "Engineering", value: 34 },
  { name: "Marketing", value: 22 },
  { name: "Operations", value: 18 },
  { name: "Sales", value: 15 },
  { name: "Support", value: 11 },
];

const GRID_SIZE = 10;
let cellIndex = 0;
const series = departments.map((dept, i) => {
  const data = [];
  for (let n = 0; n < dept.value; n += 1) {
    const row = Math.floor(cellIndex / GRID_SIZE);
    const col = cellIndex % GRID_SIZE;
    data.push([col, row]);
    cellIndex += 1;
  }
  return {
    name: `${dept.name} — ${dept.value}%`,
    color: t.palette[i],
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
    marginTop: 100,
    marginBottom: 110,
    marginLeft: 105,
    marginRight: 105,
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "waffle-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Annual budget allocation by department — each square = 1%",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    min: -0.5,
    max: GRID_SIZE - 0.5,
    tickInterval: 1,
    gridLineWidth: 0,
    lineWidth: 0,
    tickWidth: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  yAxis: {
    min: -0.5,
    max: GRID_SIZE - 0.5,
    tickInterval: 1,
    reversed: true,
    gridLineWidth: 0,
    lineWidth: 0,
    tickWidth: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  legend: {
    layout: "horizontal",
    align: "center",
    verticalAlign: "bottom",
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
    symbolHeight: 14,
    symbolWidth: 14,
    symbolRadius: 0,
  },
  tooltip: {
    headerFormat: "",
    pointFormat: "<b>{series.name}</b>",
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: {
        symbol: "square",
        radius: 41,
        lineWidth: 2,
        lineColor: t.pageBg,
      },
      states: { hover: { halo: { size: 0 } } },
    },
  },
  series,
});
