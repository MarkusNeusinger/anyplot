// anyplot.ai
// line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-26

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Simulated eigenvalues from PCA on a 15-sensor manufacturing quality-control
// dataset (temperature, pressure, vibration, etc. readings on a production line).
const rawEigenvalues = [
  312, 198, 137, 94, 71, 54, 42, 33, 27, 22, 18, 15, 12, 10, 8,
];
const totalVariance = rawEigenvalues.reduce((sum, v) => sum + v, 0);
const individualRatio = rawEigenvalues.map((v) => v / totalVariance);
const cumulativeRatio = individualRatio.reduce((acc, v, i) => {
  acc.push((i > 0 ? acc[i - 1] : 0) + v);
  return acc;
}, []);
const nComponents = rawEigenvalues.map((_, i) => i + 1);

// Elbow detection: point of max perpendicular distance from the chord
// connecting the first and last cumulative points (standard elbow heuristic).
const x1 = 0;
const y1 = cumulativeRatio[0];
const x2 = cumulativeRatio.length - 1;
const y2 = cumulativeRatio[cumulativeRatio.length - 1];
const chordLength = Math.hypot(x2 - x1, y2 - y1);
const distances = cumulativeRatio.map((y, i) => {
  const x = i;
  return Math.abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / chordLength;
});
const elbowIndex = distances.indexOf(Math.max(...distances));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "line-pca-variance-cumulative · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    categories: nComponents.map(String),
    title: { text: "Number of Components", style: { color: t.inkSoft, fontSize: "16px" } },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: [
    {
      title: { text: "Individual Variance Ratio", style: { color: t.inkSoft, fontSize: "16px" } },
      labels: {
        style: { color: t.inkSoft, fontSize: "14px" },
        formatter() {
          return Math.round(this.value * 100) + "%";
        },
      },
      gridLineColor: t.grid,
      max: Math.max(...individualRatio) * 1.6,
    },
    {
      title: { text: "Cumulative Explained Variance", style: { color: t.inkSoft, fontSize: "16px" } },
      labels: {
        style: { color: t.inkSoft, fontSize: "14px" },
        formatter() {
          return Math.round(this.value * 100) + "%";
        },
      },
      gridLineColor: t.grid,
      min: 0,
      max: 1,
      opposite: true,
      plotLines: [
        {
          value: 0.9,
          color: t.amber,
          dashStyle: "Dash",
          width: 1.5,
          label: { text: "90%", style: { color: t.inkSoft, fontSize: "13px" }, align: "left", x: 4 },
        },
        {
          value: 0.95,
          color: t.amber,
          dashStyle: "Dash",
          width: 1.5,
          label: { text: "95%", style: { color: t.inkSoft, fontSize: "13px" }, align: "left", x: 4 },
        },
      ],
    },
  ],
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false },
    column: { borderWidth: 0, opacity: 0.55 },
  },
  series: [
    {
      type: "column",
      name: "Individual variance",
      data: individualRatio,
      yAxis: 0,
      color: t.palette[1],
    },
    {
      type: "line",
      name: "Cumulative variance",
      data: cumulativeRatio.map((v, i) =>
        i === elbowIndex
          ? { y: v, marker: { radius: 8, symbol: "diamond", fillColor: t.palette[0], lineColor: t.ink, lineWidth: 1.5 } }
          : v
      ),
      yAxis: 1,
      color: t.palette[0],
      lineWidth: 2.5,
      marker: { radius: 5, fillColor: t.palette[0], lineColor: t.pageBg, lineWidth: 1 },
      dataLabels: {
        enabled: true,
        formatter() {
          return this.point.index === elbowIndex ? "Elbow" : null;
        },
        style: { color: t.ink, fontSize: "13px", fontWeight: "600", textOutline: "none" },
        y: -16,
      },
    },
  ],
});
