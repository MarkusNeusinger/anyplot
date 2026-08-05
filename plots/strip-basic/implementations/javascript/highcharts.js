// anyplot.ai
// strip-basic: Basic Strip Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 86/100 | Created: 2026-08-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) -----------------------------------
let seed = 42;
function nextUniform() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function nextGaussian() {
  const u1 = Math.max(nextUniform(), 1e-9);
  const u2 = nextUniform();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const groups = [
  { name: "Placebo", mean: 62, sd: 11 },
  { name: "Low Dose", mean: 48, sd: 10 },
  { name: "Standard Dose", mean: 35, sd: 9 },
  { name: "High Dose", mean: 26, sd: 8 },
];
const pointsPerGroup = 45;

const groupData = groups.map((group) => {
  const values = Array.from({ length: pointsPerGroup }, () => {
    const responseMinutes = Math.max(5, group.mean + nextGaussian() * group.sd);
    return Math.round(responseMinutes * 10) / 10;
  });
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  return { name: group.name, values, mean };
});

const series = groupData.map((group, groupIndex) => ({
  name: group.name,
  color: t.palette[groupIndex],
  showInLegend: false,
  marker: {
    fillColor: hexToRgba(t.palette[groupIndex], 0.6),
    lineWidth: 1,
    lineColor: t.pageBg,
  },
  data: group.values.map((value) => [groupIndex, value]),
}));

const meanSeries = {
  name: "Group Mean",
  showInLegend: true,
  color: t.ink,
  jitter: { x: 0, y: 0 },
  marker: {
    symbol: "diamond",
    radius: 8,
    fillColor: t.ink,
    lineWidth: 2,
    lineColor: t.pageBg,
  },
  dataLabels: {
    enabled: true,
    format: "{y:.1f} min",
    y: -14,
    style: { color: t.ink, fontSize: "12px", fontWeight: "600", textOutline: "none" },
  },
  data: groupData.map((group, groupIndex) => [
    groupIndex,
    Math.round(group.mean * 10) / 10,
  ]),
};

// --- Chart -----------------------------------------------------------------
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
    text: "strip-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: groups.map((group) => group.name),
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: {
      text: "Time to Symptom Relief (minutes)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      jitter: { x: 0.3, y: 0 },
      marker: { radius: 6, symbol: "circle" },
    },
  },
  series: [...series, meanSeries],
});
