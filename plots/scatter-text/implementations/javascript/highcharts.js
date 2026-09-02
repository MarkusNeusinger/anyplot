// anyplot.ai
// scatter-text: Scatter Plot with Text Labels Instead of Points
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Synthetic 2D projection (e.g. a t-SNE/UMAP embedding) of programming
// language names, loosely clustered by language family. Every point is
// rendered as its own name instead of a marker glyph.
const clusters = [
  {
    name: "Data & scientific",
    points: [
      { name: "Python", x: 1.6, y: 4.8 },
      { name: "R", x: 2.6, y: 5.6 },
      { name: "Julia", x: 0.6, y: 5.4 },
      { name: "MATLAB", x: 3.2, y: 6.6 },
      { name: "SAS", x: 3.6, y: 4.4 },
    ],
  },
  {
    name: "Web & frontend",
    points: [
      { name: "JavaScript", x: 5.8, y: 1.4 },
      { name: "TypeScript", x: 6.6, y: 2.4 },
      { name: "PHP", x: 4.8, y: 0.6 },
      { name: "Ruby", x: 5.4, y: -0.6 },
      { name: "Dart", x: 7.2, y: 1.0 },
    ],
  },
  {
    name: "Systems programming",
    points: [
      { name: "C", x: -2.4, y: -0.4 },
      { name: "C++", x: -1.4, y: 0.6 },
      { name: "Rust", x: -3.2, y: 1.2 },
      { name: "Go", x: -2.0, y: 2.0 },
      { name: "Zig", x: -3.6, y: -0.8 },
    ],
  },
  {
    name: "JVM & enterprise",
    points: [
      { name: "Java", x: 3.4, y: -2.6 },
      { name: "Kotlin", x: 4.4, y: -1.8 },
      { name: "Scala", x: 2.6, y: -3.4 },
      { name: "C#", x: 5.2, y: -3.0 },
      { name: "VB.NET", x: 3.8, y: -4.2 },
    ],
  },
  {
    name: "Scripting & ops",
    points: [
      { name: "Bash", x: -4.6, y: 3.8 },
      { name: "Perl", x: -3.8, y: 4.8 },
      { name: "Lua", x: -5.4, y: 4.4 },
      { name: "PowerShell", x: -4.2, y: 5.6 },
      { name: "Groovy", x: -2.8, y: 4.2 },
    ],
  },
];

// --- Chart -------------------------------------------------------------------
const series = clusters.map((cluster, i) => ({
  type: "scatter",
  name: cluster.name,
  color: t.palette[i],
  data: cluster.points,
  marker: { enabled: false, states: { hover: { enabled: false } } },
  dataLabels: {
    enabled: true,
    format: "{point.name}",
    allowOverlap: false,
    crop: false,
    overflow: "allow",
    align: "center",
    verticalAlign: "middle",
    style: {
      color: t.palette[i],
      fontSize: "15px",
      fontWeight: "600",
      textOutline: `1px ${t.pageBg}`,
    },
  },
}));

Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    spacing: [24, 32, 24, 32],
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "scatter-text · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    title: {
      text: "t-SNE dimension 1",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: -6.6,
    max: 8.4,
    labels: { enabled: false },
    lineColor: t.inkSoft,
    tickLength: 0,
    gridLineWidth: 1,
    gridLineColor: t.grid,
  },
  yAxis: {
    title: {
      text: "t-SNE dimension 2",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: -5.5,
    max: 7.8,
    labels: { enabled: false },
    lineColor: t.inkSoft,
    tickLength: 0,
    gridLineWidth: 1,
    gridLineColor: t.grid,
  },
  legend: {
    title: {
      text: "Language family",
      style: { color: t.inkSoft, fontSize: "14px" },
    },
    // Marker-free scatter series draw no legend symbol, so the color key
    // lives in the legend text itself instead of a swatch.
    useHTML: true,
    labelFormatter: function () {
      return `<span style="color:${this.color}">${this.name}</span>`;
    },
    itemStyle: { fontSize: "14px", fontWeight: "600" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: { series: { animation: false } },
  series,
});
